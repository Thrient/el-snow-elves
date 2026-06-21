"""360 渠道服登录 — OAuth2 webview 授权 (display=desktop)

360 OAuth endpoint: openapi.360.cn/oauth2/authorize
client_id = appkey (e7e8d257...), 不是 appid (203810216)
"""

import base64 as _b64
import json as _json
import logging
import os as _os
import shutil as _shutil
import threading
import time
import uuid as _uuid
from urllib.parse import urlparse, parse_qs

import requests
import webview
import webview.platforms.winforms as _wf

from script.config.Setting import APP_DATA

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("Microsoft.Web.WebView2.WinForms")

APPID = "203810216"
APPKEY = "e7e8d257f9a8ac6c9dd53b2005046d33"
CHANNEL_TYPE = "360_assistant"

_AUTH_URL = (
    "https://openapi.360.cn/oauth2/authorize?"
    f"client_id={APPKEY}&"
    "response_type=code&"
    "redirect_uri=oob&"
    "scope=basic&"
    "display=desktop&"
    "force_login=0&"
    "oauth_version=1.0"
)

_TOKEN_URL = "https://openapi.360.cn/oauth2/access_token"
_ME_URL = "https://openapi.360.cn/user/me.json"


def _add_navigation_handler(window, login_container: dict) -> bool:
    """NavigationStarting 检测 OAuth redirect / code"""
    try:
        from webview.platforms.winforms import BrowserView
        from Microsoft.Web.WebView2.Core import CoreWebView2NavigationStartingEventArgs
        from System import EventHandler

        form = BrowserView.instances.get(window.uid)
        if not form:
            logging.error("[Qihu360Channel] 找不到 BrowserForm 实例")
            return False
        wv2 = form.webview

        def handler(sender, args: CoreWebView2NavigationStartingEventArgs):
            uri = args.Uri or ""
            if "code=" in uri or "access_token=" in uri:
                logging.debug(f"[Qihu360Channel] OAuth 重定向: {uri[:200]}")
                login_container["redirect"] = uri

        wv2.NavigationStarting += EventHandler[CoreWebView2NavigationStartingEventArgs](handler)
        logging.debug("[Qihu360Channel] NavigationStarting 已追加")
        return True
    except Exception as e:
        logging.error(f"[Qihu360Channel] NavigationStarting 失败: {e}")
        return False


def _exchange_code(code: str) -> dict:
    """用 code 换 access_token + refresh_token + expires_in"""
    for i, use_basic_auth in enumerate([True, False]):
        try:
            data_payload = {"grant_type": "authorization_code", "code": code,
                          "redirect_uri": "https://openapi.360.cn/page/oauth2_succeed",
                          "scope": "basic"}
            kw = {"data": data_payload, "timeout": 15}
            if use_basic_auth:
                kw["auth"] = (APPKEY, APPKEY)
                data_payload["client_id"] = APPKEY
            else:
                data_payload["client_id"] = APPKEY
                data_payload["client_secret"] = APPKEY
            r = requests.post(_TOKEN_URL, **kw)
            data = r.json()
            auth_mode = "BasicAuth" if use_basic_auth else "body"
            logging.debug(f"[Qihu360Channel] token 响应 ({auth_mode}): status={r.status_code}, keys={list(data.keys())}, error={data.get('error', 'N/A')}")
            at = data.get("access_token", "")
            if at:
                rt = data.get("refresh_token", "")
                ei = data.get("expires_in", 0)
                logging.info(
                    f"[Qihu360Channel] access_token 获取成功 ({auth_mode}), "
                    f"expires_in={ei}, has_refresh_token={bool(rt)}"
                )
                return {"access_token": at, "refresh_token": rt, "expires_in": int(ei) if ei else 0}
        except Exception as e:
            logging.warning(f"[Qihu360Channel] token 异常: {e}")
    return {}


def _get_user_id(access_token: str) -> str:
    """获取 360 用户 ID"""
    try:
        r = requests.get(_ME_URL, params={"access_token": access_token}, timeout=15)
        data = r.json()
        uid = str(data.get("id", ""))
        if uid:
            logging.info(f"[Qihu360Channel] user_id={uid}, name={data.get('name', '')}")
        return uid
    except Exception as e:
        logging.error(f"[Qihu360Channel] user/me 异常: {e}")
    return ""


def _refresh_access_token(refresh_token: str) -> str | None:
    """用 refresh_token 刷新 access_token（360 OAuth2 刷新端点）"""
    if not refresh_token:
        return None
    try:
        r = requests.post(
            _TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": APPKEY,
                "client_secret": APPKEY,
                "scope": "basic",
            },
            timeout=15,
        )
        data = r.json()
        at = data.get("access_token", "")
        if at:
            logging.info(
                f"[Qihu360Channel] access_token 刷新成功, "
                f"expires_in={data.get('expires_in', 'N/A')}"
            )
            return at
        logging.error(f"[Qihu360Channel] token 刷新失败: {data}")
    except Exception as e:
        logging.error(f"[Qihu360Channel] token 刷新异常: {e}")
    return None


class Qihu360Login:
    """360 OAuth 登录 — webview（持久化 cookie 缓存，支持静默刷新）"""

    def __init__(self, cache_dir: str = ""):
        self._window: webview.Window | None = None
        self._access_token: str = ""
        self._refresh_token: str = ""
        self._expires_in: int = 0
        self._user_id: str = ""
        self._done = threading.Event()
        self._temp_dir: str = ""
        self._original_cache_dir: str = ""
        self._cache_dir: str = cache_dir  # 持久化缓存目录

    def login(self, silent: bool = False) -> dict | None:
        """silent=True 时隐藏窗口，依赖持久化 cookie 自动登录"""
        self._done.clear()
        login_container: dict = {}

        if self._cache_dir:
            self._temp_dir = self._cache_dir
        else:
            self._temp_dir = _os.path.normpath(
                _os.path.join(APP_DATA, "qihu360_sessions", _uuid.uuid4().hex[:8])
            )
        _os.makedirs(self._temp_dir, exist_ok=True)
        self._original_cache_dir = _wf.cache_dir
        _wf.cache_dir = self._temp_dir
        logging.debug(f"[Qihu360Channel] 缓存目录: {self._temp_dir}, silent={silent}")

        try:
            icon_bytes = requests.get("https://www.360.cn/favicon.ico", timeout=5).content
        except Exception:
            icon_bytes = None

        try:
            self._window = webview.create_window(
                "360 账号登录",
                _AUTH_URL,
                width=1 if silent else 480,
                height=1 if silent else 720,
                hidden=silent,
            )
            if not silent and icon_bytes:
                from script.account.channel.ChannelUtils import _apply_icon_bytes
                _apply_icon_bytes(self._window, icon_bytes)
        finally:
            _wf.cache_dir = self._original_cache_dir

        def _run():
            time.sleep(2)
            _add_navigation_handler(self._window, login_container)

            for _ in range(240 if silent else 480):
                if self._done.is_set():
                    return

                redirect = login_container.get("redirect", "")
                if redirect:
                    if "code=" in redirect:
                        parsed = urlparse(redirect)
                        code = parse_qs(parsed.query).get("code", [""])[0]
                        if code:
                            exchange_result = _exchange_code(code)
                            if exchange_result:
                                self._access_token = exchange_result.get("access_token", "")
                                self._refresh_token = exchange_result.get("refresh_token", "")
                                self._expires_in = exchange_result.get("expires_in", 0)
                    elif "#" in redirect and "access_token=" in redirect.split("#")[1]:
                        self._access_token = parse_qs(redirect.split("#")[1]).get("access_token", [""])[0]
                        ei_str = parse_qs(redirect.split("#")[1]).get("expires_in", ["0"])[0]
                        self._expires_in = int(ei_str) if ei_str else 0
                    if self._access_token:
                        break

                # JS 提取页面上的 token（适用于 oob / 页面展示场景）
                try:
                    raw = self._window.evaluate_js(
                        "(function(){var b=document.body?document.body.innerText:'';"
                        "var m=b.match(/[a-f0-9]{32,64}/i);return m?m[0]:null;})()"
                    )
                    if raw and raw != "null":
                        code = str(raw).strip()
                        exchange_result = _exchange_code(code)
                        if exchange_result:
                            self._access_token = exchange_result.get("access_token", "")
                            self._refresh_token = exchange_result.get("refresh_token", "")
                            self._expires_in = exchange_result.get("expires_in", 0)
                            logging.info(f"[Qihu360Channel] JS 提取 code 并交换成功: {code[:8]}...")
                            break
                except Exception:
                    pass

                time.sleep(0.5)

            if self._access_token:
                self._user_id = self._access_token[:10]
                logging.debug(f"[Qihu360Channel] access_token, user_id={self._user_id}")

            if not self._done.is_set():
                self._done.set()
            _close_window_safe(self._window)

        threading.Thread(target=_run, daemon=True).start()
        self._done.wait(timeout=120 if silent else 260)

        # 录制模式保留缓存目录（持久化 cookie），refresh 模式也保留
        if not self._cache_dir:
            self._cleanup_temp_dir()

        if self._user_id and self._access_token:
            return {"user_id": self._user_id, "access_token": self._access_token,
                    "refresh_token": self._refresh_token, "expires_in": self._expires_in}
        if self._access_token:
            return {"user_id": "", "access_token": self._access_token,
                    "refresh_token": self._refresh_token, "expires_in": self._expires_in}
        return None

    def _cleanup_temp_dir(self):
        if not self._temp_dir:
            return
        try:
            _shutil.rmtree(self._temp_dir, ignore_errors=True)
            logging.debug(f"[Qihu360Channel] 临时目录已清理: {self._temp_dir}")
        except Exception as e:
            logging.warning(f"[Qihu360Channel] 清理临时目录失败: {e}")


def _close_window_safe(window):
    try:
        from webview.platforms.winforms import BrowserView
        from System.Windows.Forms import MethodInvoker
        form = BrowserView.instances.get(window.uid) if window else None
        if form:
            form.Invoke(MethodInvoker(lambda: form.Close()))
    except Exception:
        pass


def record() -> dict | None:
    cache_dir = _os.path.normpath(
        _os.path.join(APP_DATA, "qihu360_sessions", f"persist_{_uuid.uuid4().hex[:8]}")
    )
    login = Qihu360Login(cache_dir=cache_dir)
    result = login.login()
    if not result:
        return None
    return {
        "channel_type": CHANNEL_TYPE,
        "access_token": result.get("access_token", ""),
        "refresh_token": result.get("refresh_token", ""),
        "expires_in": result.get("expires_in", 0),
        "user_id": result.get("user_id", ""),
        "appid": APPID,
        "appkey": APPKEY,
        "cache_dir": cache_dir,
    }


def refresh_token_silent(channel_auth: dict) -> dict | None:
    """静默刷新：用持久化 cookie 重新授权，无需用户操作。
    返回更新后的 channel_auth 或 None。"""
    cache_dir = channel_auth.get("cache_dir", "")
    if not cache_dir or not _os.path.isdir(cache_dir):
        logging.warning("[Qihu360Channel] 无持久化缓存目录，无法静默刷新")
        return None
    login = Qihu360Login(cache_dir=cache_dir)
    result = login.login(silent=True)
    if result and result.get("access_token"):
        channel_auth["access_token"] = result["access_token"]
        channel_auth["refresh_token"] = result.get("refresh_token", "")
        channel_auth["expires_in"] = result.get("expires_in", 0)
        logging.info("[Qihu360Channel] 静默刷新成功")
        return channel_auth
    return None


def build_replay_data(channel_auth: dict, short_game_id: str) -> dict | None:
    """渠道回放：构造 SAUTH body（对齐真实 360 SDK 格式）→ uni_sauth → 构建 confirm 数据"""
    from script.account.channel.ChannelUtils import post_signed_data, FAKE_DEVICE

    access_token = str(channel_auth.get("access_token", ""))
    user_id = str(channel_auth.get("user_id", ""))

    if not access_token:
        logging.error("[Qihu360Channel] build_replay_data: 缺少 access_token")
        return None

    fd = dict(FAKE_DEVICE)
    udid = fd["udid"]

    # SAUTH body — 对齐真实 360 SDK 格式（sdkuid=0, sdk_version=2.3.4_794, 无 ip 字段）
    sauth_body = {
        "gameid": short_game_id,
        "login_channel": CHANNEL_TYPE,
        "app_channel": CHANNEL_TYPE,
        "platform": "ad",
        "sdkuid": "0",
        "udid": udid,
        "sessionid": access_token,
        "sdk_version": "2.3.4_794",
        "is_unisdk_guest": 0,
        "aim_info": _json.dumps({
            "country": "CN", "tz": "+0800", "tzid": "Asia/Shanghai",
            "celluar_ip": "", "operator": "460000", "is_vpn_enabled": False,
        }),
        "source_app_channel": CHANNEL_TYPE,
        "source_platform": "ad",
        "get_access_token": "1",
        "client_login_sn": "".join(__import__("random").choices("0123456789abcdef", k=32)),
        "step": "".join(__import__("random").choices("0123456789", k=10)),
        "step2": "".join(__import__("random").choices("0123456789", k=9)),
        "hostid": 0,
        "sdklog": _json.dumps({
            "device_model": fd.get("device_model", "M2102K1AC"),
            "os_name": "android", "os_ver": "12",
            "udid": udid, "app_ver": "136",
            "imei": "", "area_code": fd.get("country_code", "CN"),
            "is_emulator": 1, "is_root": 0, "oaid": "",
        }),
    }

    uni_data = post_signed_data(sauth_body, short_game_id)
    unisdk_json_b64 = uni_data.get("unisdk_login_json", "")
    if not unisdk_json_b64:
        # Step 1: 用 refresh_token 刷新 access_token
        refresh_token = str(channel_auth.get("refresh_token", ""))
        if refresh_token:
            logging.info("[Qihu360Channel] uni_sauth 失败，尝试 refresh_token...")
            new_at = _refresh_access_token(refresh_token)
            if new_at:
                channel_auth["access_token"] = new_at
                sauth_body["sessionid"] = new_at
                uni_data = post_signed_data(sauth_body, short_game_id)
                unisdk_json_b64 = uni_data.get("unisdk_login_json", "")
                if unisdk_json_b64:
                    logging.info("[Qihu360Channel] refresh_token 刷新成功")
        # Step 2: refresh_token 也失败，尝试 cookie 静默刷新
        if not unisdk_json_b64:
            logging.info("[Qihu360Channel] 尝试 cookie 静默刷新...")
            refreshed = refresh_token_silent(channel_auth)
            if refreshed:
                sauth_body["sessionid"] = refreshed["access_token"]
                uni_data = post_signed_data(sauth_body, short_game_id)
                unisdk_json_b64 = uni_data.get("unisdk_login_json", "")
                if unisdk_json_b64:
                    logging.info("[Qihu360Channel] cookie 静默刷新成功")
    if not unisdk_json_b64:
        logging.error(f"[Qihu360Channel] uni_sauth 失败: {uni_data}")
        return None
    unisdk_login = _json.loads(_b64.b64decode(unisdk_json_b64).decode())

    # 从响应获取真实 sdkuid
    real_sdkuid = uni_data.get("sdkuid", "") or unisdk_login.get("sdkuid", "")
    if not real_sdkuid:
        real_sdkuid = user_id or "3184868108"
    logging.info(f"[Qihu360Channel] uni_sauth OK, sdkuid={real_sdkuid}")

    # 构建 extra_unisdk_data
    extra_fields = {"realname": _json.dumps({"realname_type": 0, "age": 22})}
    extra_res = {"SAUTH_STR": "", "SAUTH_JSON": "", **extra_fields}

    json_data = {
        "extra_data": "", "get_access_token": "1",
        "sdk_udid": udid, "realname": extra_fields["realname"],
    }
    json_data.update({k: v for k, v in sauth_body.items() if k != "sdklog"})

    str_data = json_data.copy()
    str_data["username"] = unisdk_login.get("username", "")
    str_data_str = "&".join(f"{k}={v}" for k, v in str_data.items())

    extra_res["SAUTH_STR"] = _b64.b64encode(str_data_str.encode()).decode()
    extra_res["SAUTH_JSON"] = _b64.b64encode(_json.dumps(json_data).encode()).decode()

    return {
        "user_id": str(real_sdkuid),
        "token": _b64.b64encode(str(channel_auth.get("access_token", "")).encode()).decode(),
        "login_channel": CHANNEL_TYPE, "app_channel": CHANNEL_TYPE, "pay_channel": CHANNEL_TYPE,
        "udid": udid, "sdk_version": "2.3.4_794", "jf_game_id": short_game_id,
        "extra_data": "", "extra_unisdk_data": _json.dumps(extra_res),
        "gv": "157", "gvn": "1.5.80", "cv": "a1.5.0",
    }
