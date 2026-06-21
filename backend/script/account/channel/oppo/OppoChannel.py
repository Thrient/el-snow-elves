"""OPPO 渠道服登录 — WebView 注入 JSBridge mock 拦截原生调用"""

import json
import logging
import os
import shutil
import threading
import time
import uuid

import requests
import webview
import webview.platforms.winforms as _wf
from script.config.Setting import APP_DATA

from .consts import OPPO_UC_CLIENT_DOMAIN, OPPO_WEBVIEW_UA
from .jsbridge import build_mock_native_js
from .openaccount import OppoOpenAccountClient
from .gamesdk import OppoGameSdkClient


class OppoLogin:
    """OPPO 渠道登录 — 每次创建独立临时用户数据目录，注入 JSBridge mock"""

    def __init__(self):
        self._window: webview.Window | None = None
        self._result: dict | None = None
        self._done = threading.Event()
        self._temp_dir: str = ""
        self._original_cache_dir: str = ""

    def login(self) -> dict | None:
        """Open OPPO UC login page, inject JSBridge mock, poll for result."""
        self._done.clear()

        # ── 创建独立临时用户数据目录，确保无旧 Cookie ──
        self._temp_dir = os.path.normpath(
            os.path.join(APP_DATA, "oppo_sessions", uuid.uuid4().hex[:8])
        )
        os.makedirs(self._temp_dir, exist_ok=True)
        self._original_cache_dir = _wf.cache_dir
        _wf.cache_dir = self._temp_dir
        logging.debug(f"[OppoChannel] 临时缓存目录: {self._temp_dir}")

        # 提前下载图标
        try:
            icon_bytes = requests.get("https://www.oppo.com/favicon.ico", timeout=5).content
        except Exception:
            icon_bytes = None

        try:
            self._window = webview.create_window(
                "OPPO 账号登录", OPPO_UC_CLIENT_DOMAIN, width=420, height=680,
            )
            if icon_bytes:
                from script.account.channel.ChannelUtils import _apply_icon_bytes
                _apply_icon_bytes(self._window, icon_bytes)
        finally:
            _wf.cache_dir = self._original_cache_dir

        def _run():
            time.sleep(3)  # 等页面加载完成

            # 注入 JSBridge mock
            try:
                js_code = build_mock_native_js()
                self._window.evaluate_js(js_code)
                logging.debug("[OppoChannel] JSBridge mock 已注入")
            except Exception as e:
                logging.error(f"[OppoChannel] JSBridge 注入失败: {e}")

            # 轮询 window.__oppo_login_resp
            for _ in range(320):  # 160s / 0.5s
                if self._done.is_set():
                    return
                try:
                    raw = self._window.evaluate_js(
                        "window.__oppo_login_resp ? JSON.stringify(window.__oppo_login_resp) : null"
                    )
                    if raw and raw != "null":
                        self._result = json.loads(raw)
                        logging.info("[OppoChannel] 登录成功")
                        self._done.set()
                        return
                except Exception:
                    pass
                time.sleep(0.5)
            logging.warning("[OppoChannel] 登录超时")
            self._done.set()

        threading.Thread(target=_run, daemon=True).start()
        self._done.wait(timeout=160)

        # 关闭窗口
        try:
            from webview.platforms.winforms import BrowserView
            import clr
            clr.AddReference("System.Windows.Forms")
            from System.Windows.Forms import MethodInvoker
            form = BrowserView.instances.get(self._window.uid) if self._window else None
            if form:
                form.Invoke(MethodInvoker(lambda: form.Close()))
        except Exception:
            pass

        self._cleanup_temp_dir()
        return self._result

    def _cleanup_temp_dir(self):
        if not self._temp_dir:
            return
        try:
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            logging.debug(f"[OppoChannel] 临时目录已清理: {self._temp_dir}")
        except Exception as e:
            logging.warning(f"[OppoChannel] 清理临时目录失败: {e}")


def record() -> dict | None:
    """录制：打开 OPPO 登录窗口 → 获取 idToken → OPPO Open Account 授权"""
    login = OppoLogin()
    login_resp = login.login()
    if not login_resp:
        return None

    id_token = login_resp.get("accountToken", "")
    if not id_token:
        logging.error("[OppoChannel] record: accountToken 为空")
        return None

    client = OppoOpenAccountClient()
    oa_resp = client.authorize(id_token)

    return {
        "channel_type": "oppo",
        "login_resp": login_resp,
        "oppo_open_account": oa_resp,
    }


def build_replay_data(channel_auth: dict, short_game_id: str) -> dict | None:
    """渠道回放：token refresh → GameSDK → SAUTH → 构建 confirm 数据"""
    import json as _json
    import base64 as _b64
    from script.account.channel.ChannelUtils import build_sauth, post_signed_data, FAKE_DEVICE

    oa = channel_auth.get("oppo_open_account", {}) or {}

    ssoid = oa.get("ssoid", "")
    refresh_token = oa.get("refreshToken", "")
    primary_token = oa.get("primaryToken", "")
    refresh_ticket = oa.get("refreshTicket", "")
    access_token = oa.get("accessToken", "")
    secondary_token_map = oa.get("secondaryTokenMap", {}) or {}

    # token_refresh
    client = OppoOpenAccountClient()
    refresh_resp = client.token_refresh(
        refresh_token=refresh_token,
        ssoid=ssoid,
        primary_token=primary_token,
        refresh_ticket=refresh_ticket,
        access_token=access_token,
        secondary_token_map=secondary_token_map,
    )

    new_stm = refresh_resp.get("secondaryTokenMap", {}) or secondary_token_map
    secondary_token = new_stm.get("com.heytap.htms", "")
    if not secondary_token:
        logging.error("[OppoChannel] build_replay_data: secondary_token 为空")
        return None

    # GameSDK
    pkg = "com.netease.wyclx.nearme"
    gs = OppoGameSdkClient()
    login_result = gs.user_login(pkg_name=pkg, secondary_token=secondary_token)
    logging.debug(
        "[OppoChannel] user/login code=%s user_id=%s",
        login_result.code,
        login_result.user_dto.get("user_id", ""),
    )

    result, accounts = gs.account_latest_role(pkg_name=pkg, secondary_token=secondary_token)
    if not accounts:
        logging.error("[OppoChannel] build_replay_data: 无账号")
        return None

    # 选 login_time 最大的账号
    selected = max(accounts, key=lambda a: a.get("login_time", 0))
    account_id = selected.get("account_id", "")
    logging.debug(
        "[OppoChannel] 选中账号: account_id=%s role_name=%s login_time=%s",
        account_id,
        selected.get("role_name", "?"),
        selected.get("login_time", 0),
    )

    # SAUTH
    fd = dict(FAKE_DEVICE)
    sauth_body = build_sauth(
        login_channel="oppo",
        app_channel="oppo",
        uid=account_id,
        session=secondary_token,
        game_id=short_game_id,
        sdk_version="4.7.2.0",
        custom_data={
            "realname": _json.dumps({"realname_type": 0, "age": 22}),
        },
    )

    uni_data = post_signed_data(sauth_body, short_game_id)
    unisdk_json_b64 = uni_data.get("unisdk_login_json", "")
    if not unisdk_json_b64:
        logging.error("[OppoChannel] uni_sauth 缺少 unisdk_login_json")
        return None
    unisdk_login = _json.loads(_b64.b64decode(unisdk_json_b64).decode())

    extra_fields = {"realname": _json.dumps({"realname_type": 0, "age": 22})}
    extra_res = {"SAUTH_STR": "", "SAUTH_JSON": "", **extra_fields}
    json_data = {
        "extra_data": "",
        "get_access_token": "1",
        "sdk_udid": fd["udid"],
        "realname": extra_fields["realname"],
    }
    json_data.update(sauth_body)
    str_data = json_data.copy()
    str_data["username"] = unisdk_login.get("username", "")
    str_data_str = "&".join(f"{k}={v}" for k, v in str_data.items())
    extra_res["SAUTH_STR"] = _b64.b64encode(str_data_str.encode()).decode()
    extra_res["SAUTH_JSON"] = _b64.b64encode(_json.dumps(json_data).encode()).decode()

    return {
        "user_id": account_id,
        "token": _b64.b64encode(secondary_token.encode()).decode(),
        "login_channel": "oppo",
        "app_channel": "oppo",
        "pay_channel": "oppo",
        "udid": fd["udid"],
        "sdk_version": "4.7.2.0",
        "jf_game_id": short_game_id,
        "extra_data": "",
        "extra_unisdk_data": _json.dumps(extra_res),
        "gv": "157",
        "gvn": "1.5.80",
        "cv": "a1.5.0",
    }
