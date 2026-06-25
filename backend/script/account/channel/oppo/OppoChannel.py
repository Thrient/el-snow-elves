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
        """打开 OPPO 登录窗口，注入 JSBridge mock，轮询登录结果。"""
        self._done.clear()

        self._temp_dir = os.path.normpath(
            os.path.join(APP_DATA, "oppo_sessions", uuid.uuid4().hex[:8])
        )
        os.makedirs(self._temp_dir, exist_ok=True)
        self._original_cache_dir = _wf.cache_dir
        _wf.cache_dir = self._temp_dir

        try:
            icon_bytes = requests.get("https://www.oppo.com/favicon.ico", timeout=5).content
        except Exception:
            icon_bytes = None

        try:
            self._window = webview.create_window(
                "OPPO 账号登录", "about:blank", width=420, height=680,
            )
            if icon_bytes:
                from script.account.channel.ChannelUtils import _apply_icon_bytes
                _apply_icon_bytes(self._window, icon_bytes)
        finally:
            _wf.cache_dir = self._original_cache_dir

        # 后台线程：CoreWebView2 就绪 → 注入 mock → 导航到 OPPO
        def _setup():
            try:
                from webview.platforms.winforms import BrowserView
                import clr
                clr.AddReference("System.Windows.Forms")
                from System.Windows.Forms import MethodInvoker
                from System import EventHandler
                from Microsoft.Web.WebView2.Core import CoreWebView2InitializationCompletedEventArgs

                form = BrowserView.instances.get(self._window.uid)
                if not form:
                    return
                wv2 = form.webview
                js_code = build_mock_native_js()

                def _do_inject_and_nav(*args):
                    wv2.CoreWebView2.Settings.UserAgent = OPPO_WEBVIEW_UA
                    wv2.CoreWebView2.AddScriptToExecuteOnDocumentCreatedAsync(js_code)
                    time.sleep(0.3)
                    wv2.CoreWebView2.Navigate(OPPO_UC_CLIENT_DOMAIN)
                    logging.debug("[OppoChannel] UA + mock 已注入，已导航到 OPPO")

                def _on_ui():
                    if wv2.CoreWebView2 is not None:
                        _do_inject_and_nav()
                        return
                    self._init_handler = EventHandler[
                        CoreWebView2InitializationCompletedEventArgs
                    ](lambda s, a: _do_inject_and_nav())
                    wv2.CoreWebView2InitializationCompleted += self._init_handler

                form.BeginInvoke(MethodInvoker(_on_ui))
            except Exception as e:
                logging.error(f"[OppoChannel] 后台注入失败: {e}")

        threading.Thread(target=_setup, daemon=True).start()

        def _run():
            _cme_state = {"handled": False}
            for _ in range(320):
                if self._done.is_set():
                    return
                try:
                    # 处理 CallMethodExecutor（身份验证）
                    if not _cme_state["handled"]:
                        cme = self._window.evaluate_js(
                            "window.__oppo_last_call_executor ? JSON.stringify(window.__oppo_last_call_executor) : null"
                        )
                        if cme and cme != "null":
                            cme_raw = json.loads(cme)
                            if isinstance(cme_raw, str):
                                param = json.loads(cme_raw)
                            else:
                                param = cme_raw
                            _cme_state["handled"] = True
                            self._handle_call_method_executor(param, _cme_state)
                            continue

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

    def _handle_call_method_executor(self, param: dict, cme_state: dict):
        """处理 CallMethodExecutor：调用 OPPO 身份验证 → 打开验证弹窗 → 回调主页面。"""
        if not self._window:
            return
        try:
            from webview.platforms.winforms import BrowserView
            import clr
            clr.AddReference("System.Windows.Forms")
            from System.Windows.Forms import MethodInvoker
            from .consts import build_vip_header_json
            from .openaccount import sign_request
            import requests as _requests

            form = BrowserView.instances.get(self._window.uid)
            if not form:
                return

            base_url = "https://client-uc.heytapmobi.com"
            headers = build_vip_header_json()
            headers["X-Sys-TalkBackState"] = "false"
            headers["X-BusinessSystem"] = "other"
            headers["X-Client-package"] = "com.heytap.htms"
            headers["Ext-Mobile"] = "///1/CN"
            headers["Content-Type"] = "application/json; charset=UTF-8"
            headers["Accept"] = "application/json"

            payload = {
                "mspBizK": param.get("bizk") or "",
                "mspBizSec": param.get("bizs") or "",
                "appId": param.get("appId") or "3574817",
                "ssoId": "",
                "businessId": param.get("businessId") or "",
                "deviceId": "",
                "userToken": "",
                "processToken": param.get("processToken") or "",
                "captchaCode": "",
                "envParam": "",
                "isBiometricClear": True,
                "isLockScreenClear": False,
                "validateSdkVersion": "2.2.1",
                "source": "app",
                "bizk": "3cd48b0c781835478b0a1783a9eff0c9",
                "timestamp": int(time.time() * 1000),
            }
            payload["sign"] = sign_request(payload)

            r = _requests.post(
                f"{base_url}/api/v2/business/authentication/auth",
                json=payload, headers=headers, timeout=15,
            )
            resp = r.json()
            logging.debug(f"[OppoChannel] authentication/auth ok")
            data = resp.get("data") if isinstance(resp, dict) else resp
            if not isinstance(data, dict):
                data = resp.get("result") or {}
            verification_url = data.get("verificationUrl") or ""
            if not verification_url:
                logging.error(f"[OppoChannel] authentication/auth 未返回 verificationUrl")
                return

            try:
                callback_id = self._window.evaluate_js("window.__oppo_last_cme_callbackid || ''") or ""
            except Exception:
                callback_id = ""
            business_id = param.get("businessId") or ""

            verify_window = webview.create_window(
                "身份验证", verification_url, width=500, height=600,
            )
            vjs_code = build_mock_native_js()
            logging.debug(f"[OppoChannel] 验证弹窗已打开")

            verify_done = False
            for _i in range(60):
                if self._done.is_set():
                    try:
                        form2 = BrowserView.instances.get(verify_window.uid)
                        if form2:
                            form2.Invoke(MethodInvoker(lambda: form2.Close()))
                    except Exception:
                        pass
                    return
                if _i == 3:
                    try:
                        verify_window.evaluate_js(vjs_code)
                        logging.debug("[OppoChannel] 弹窗 mock 已注入")
                    except Exception as e:
                        logging.error(f"[OppoChannel] 弹窗 mock 注入失败: {e}")
                try:
                    result = verify_window.evaluate_js(
                        "window.__oppo_login_resp ? JSON.stringify(window.__oppo_login_resp) : null"
                    )
                    if result and result != "null":
                        resp_data = json.loads(result)
                        ticket = ""
                        if isinstance(resp_data, dict):
                            d = resp_data.get("data") or {}
                            if isinstance(d, dict):
                                ticket = d.get("ticket") or ""
                            if not ticket:
                                ticket = resp_data.get("ticket") or ""
                        if ticket and callback_id:
                            cb_payload = json.dumps({
                                "code": 0, "msg": "success!",
                                "data": {
                                    "businessId": business_id,
                                    "code": "VERIFY_RESULT_CODE_SUCCESS",
                                    "msg": "success", "requestCode": "",
                                    "ticket": ticket,
                                },
                            })
                            cb_js = (
                                "if(window.HeytapJsApi&&window.HeytapJsApi.callback){"
                                f"window.HeytapJsApi.callback('{callback_id}', JSON.stringify({cb_payload}));"
                                "}"
                            )
                            self._window.evaluate_js(cb_js)
                            logging.debug(f"[OppoChannel] 验证完成，已回调主页面")
                        verify_done = True
                        try:
                            form2 = BrowserView.instances.get(verify_window.uid)
                            if form2:
                                form2.Invoke(MethodInvoker(lambda: form2.Close()))
                        except Exception:
                            pass
                        break
                except Exception:
                    pass
                time.sleep(1)

            if not verify_done:
                logging.warning("[OppoChannel] 验证弹窗超时，重置状态等待页面重试")
                cme_state["handled"] = False
                try:
                    form2 = BrowserView.instances.get(verify_window.uid)
                    if form2:
                        form2.Invoke(MethodInvoker(lambda: form2.Close()))
                except Exception:
                    pass
        except Exception as e:
            logging.error(f"[OppoChannel] CallMethodExecutor 处理失败: {e}")

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

    logging.debug(f"[OppoChannel] login_resp keys: {list(login_resp.keys()) if isinstance(login_resp, dict) else type(login_resp)}")

    account_token = login_resp.get("accountToken") or {}
    if not isinstance(account_token, dict):
        logging.error(f"[OppoChannel] record: accountToken 不是 dict")
        return None
    id_token = str(account_token.get("idToken") or "").strip()
    if not id_token:
        logging.error("[OppoChannel] record: accountToken.idToken 为空")
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

    lr = channel_auth.get("login_resp", {}) or {}
    if not isinstance(lr, dict) or not lr:
        logging.error("[OppoChannel] login_resp 为空")
        return None

    at = lr.get("accountToken") or {}
    ssoid = str(lr.get("ssoid") or "").strip()
    refresh_token = str(at.get("refreshToken") or "").strip()
    primary_token = str(lr.get("primaryToken") or "").strip()
    refresh_ticket = str(lr.get("refreshTicket") or "").strip()
    access_token = str(at.get("accessToken") or "").strip()
    secondary_token_map = lr.get("secondaryTokenMap", {}) or {}

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
    pkg = "com.netease.wyclx.nearme.gamecenter"
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

    selected = max(accounts, key=lambda a: a.get("login_time", 0))
    account_id = selected.get("account_id", "")
    logging.debug(
        "[OppoChannel] 选中账号: account_id=%s role_name=%s",
        account_id,
        selected.get("role_name", "?"),
    )

    ticket = login_result.ticket
    fd = dict(FAKE_DEVICE)
    extra_unisdk = ""

    sauth_body = build_sauth(
        login_channel="oppo",
        app_channel="oppo",
        uid=account_id,
        session=ticket,
        game_id=short_game_id,
        sdk_version="6070105",
        custom_data={
            "realname": _json.dumps({"realname_type": 0, "age": 22}),
        },
    )
    uni_data = post_signed_data(sauth_body, short_game_id, need_custom_encode=True)
    unisdk_json_b64 = uni_data.get("unisdk_login_json", "")
    if unisdk_json_b64:
        unisdk_login = _json.loads(_b64.b64decode(unisdk_json_b64).decode())
        extra_fields = {"realname": _json.dumps({"realname_type": 0, "age": 22})}
        extra_res = {"SAUTH_STR": "", "SAUTH_JSON": "", **extra_fields}
        json_data = {
            "extra_data": "", "get_access_token": "1",
            "sdk_udid": fd["udid"], "realname": extra_fields["realname"],
        }
        json_data.update(sauth_body)
        str_data = json_data.copy()
        str_data["username"] = unisdk_login.get("username", "")
        str_data_str = "&".join(f"{k}={v}" for k, v in str_data.items())
        extra_res["SAUTH_STR"] = _b64.b64encode(str_data_str.encode()).decode()
        extra_res["SAUTH_JSON"] = _b64.b64encode(_json.dumps(json_data).encode()).decode()
        extra_unisdk = _json.dumps(extra_res)

    return {
        "user_id": account_id,
        "token": _b64.b64encode(ticket.encode()).decode(),
        "login_channel": "oppo",
        "app_channel": "oppo",
        "pay_channel": "oppo",
        "udid": fd["udid"],
        "sdk_version": "6070105",
        "jf_game_id": short_game_id,
        "extra_data": "",
        "extra_unisdk_data": extra_unisdk,
        "gv": "157",
        "gvn": "1.5.80",
        "cv": "a1.5.0",
    }
