"""Vivo 渠道服登录 — 独立临时用户数据目录，避免 Cookie 污染"""

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


VIVO_LOGIN_URL = (
    "https://passport.vivo.com.cn/#/login"
    "?client_id=67"
    "&redirect_uri=https%3A%2F%2Fjoint.vivo.com.cn%2Fgame-subaccount-login%3Ffrom%3Dlogin"
)

VIVO_UNION_GET = "https://joint.vivo.com.cn/h5/union/get?gamePackage={game_package}"

DEFAULT_GAME_PACKAGE = "com.netease.wyclx.vivo"


def _add_navigation_handler(window, login_container: dict):
    """给 WebView2 追加 NavigationStarting 事件。检测登录完成。"""
    try:
        from webview.platforms.winforms import BrowserView
        from Microsoft.Web.WebView2.Core import CoreWebView2NavigationStartingEventArgs
        from System import EventHandler

        form = BrowserView.instances.get(window.uid)
        if not form:
            logging.error("[VivoChannel] 找不到 BrowserForm 实例")
            return False
        wv2 = form.webview

        def handler(sender, args: CoreWebView2NavigationStartingEventArgs):
            uri = args.Uri or ""
            if "joint.vivo.com.cn" in uri and "from=login" in uri:
                logging.info(f"[VivoChannel] 拦截登录完成: {uri[:120]}")
                login_container["url"] = uri

        wv2.NavigationStarting += EventHandler[CoreWebView2NavigationStartingEventArgs](handler)
        logging.info("[VivoChannel] NavigationStarting 处理器已追加")
        return True
    except Exception as e:
        logging.error(f"[VivoChannel] 追加事件失败: {e}")
        return False


class VivoLogin:
    """Vivo 渠道登录 — 每次创建独立临时用户数据目录，天然隔离不同账号"""

    def __init__(self, game_package: str = DEFAULT_GAME_PACKAGE):
        self.game_package = game_package
        self._window: webview.Window | None = None
        self._result: dict | None = None
        self._cookies: dict[str, str] = {}
        self._done = threading.Event()
        self._temp_dir: str = ""
        self._original_cache_dir: str = ""

    def login(self) -> dict | None:
        self._done.clear()
        login_container: dict = {}

        # ── 创建独立临时用户数据目录，确保无旧 Cookie ──
        self._temp_dir = os.path.normpath(
            os.path.join(APP_DATA, "vivo_sessions", uuid.uuid4().hex[:8])
        )
        os.makedirs(self._temp_dir, exist_ok=True)
        self._original_cache_dir = _wf.cache_dir
        _wf.cache_dir = self._temp_dir
        logging.info(f"[VivoChannel] 临时缓存目录: {self._temp_dir}")

        try:
            self._window = webview.create_window(
                "Vivo 账号登录", VIVO_LOGIN_URL, width=420, height=680,
            )
        finally:
            _wf.cache_dir = self._original_cache_dir

        def _run():
            time.sleep(2)
            _add_navigation_handler(self._window, login_container)

            for _ in range(300):
                if self._done.is_set():
                    return
                if login_container.get("url"):
                    _process_login()
                    return
                time.sleep(0.5)
            logging.warning("[VivoChannel] 登录超时")
            self._done.set()

        def _process_login():
            self._window.evaluate_js(f"""
                window.__vivo_result = null;
                fetch("{VIVO_UNION_GET.format(game_package=self.game_package)}", {{credentials: "include"}})
                    .then(r => r.text())
                    .then(text => {{ window.__vivo_result = text; }})
                    .catch(e => {{ window.__vivo_result = JSON.stringify({{error: e.toString()}}); }});
            """)

            for _ in range(60):
                try:
                    raw = self._window.evaluate_js("window.__vivo_result")
                    if raw and raw != "null":
                        data = json.loads(raw)
                        if isinstance(data, dict) and data.get("code") == 0:
                            self._result = data.get("data", {})
                            logging.info(f"[VivoChannel] union/get 成功: {json.dumps(self._result, ensure_ascii=False)[:200]}")
                        elif isinstance(data, dict) and data.get("error"):
                            logging.error(f"[VivoChannel] fetch 错误: {data['error']}")
                        else:
                            logging.error(f"[VivoChannel] union/get 失败: {data}")
                        break
                except Exception:
                    pass
                time.sleep(0.2)
            else:
                logging.error("[VivoChannel] union/get 超时")

            # 通过 window.get_cookies() 获取包含 HttpOnly 的全部 Cookie
            self._cookies = _get_cookies_safe(self._window)

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

            self._done.set()

        threading.Thread(target=_run, daemon=True).start()
        self._done.wait(timeout=160)

        self._cleanup_temp_dir()
        return self._result

    def _cleanup_temp_dir(self):
        if not self._temp_dir:
            return
        try:
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            logging.info(f"[VivoChannel] 临时目录已清理: {self._temp_dir}")
        except Exception as e:
            logging.warning(f"[VivoChannel] 清理临时目录失败: {e}")

    @property
    def cookies(self) -> dict:
        return self._cookies


def _get_cookies_safe(window) -> dict[str, str]:
    """安全调用 window.get_cookies()，返回 {name: value} 字典"""
    try:
        raw = window.get_cookies()
        result: dict[str, str] = {}
        for cookie in raw:
            for name, morsel in cookie.items():
                if name and morsel.value:
                    result[name] = morsel.value
        logging.info(f"[VivoChannel] get_cookies 获取到 {len(result)} 个")
        return result
    except Exception as e:
        logging.warning(f"[VivoChannel] get_cookies 失败: {e}")
        return {}


def record() -> dict | None:
    """录制：打开 Vivo 登录窗口 → 返回 channel_auth"""
    login = VivoLogin()
    result = login.login()
    if not result:
        return None
    return {
        "channel_type": "nearme_vivo",
        "auth_data": result,
        "cookies": login.cookies,
    }


def build_replay_data(channel_auth: dict, short_game_id: str) -> dict | None:
    """渠道回放：cookies → union/get → 选子账号 → union/use → uni_sauth → 构建 confirm 数据"""
    import json as _json
    import base64 as _b64
    from script.account.channel.ChannelUtils import build_sauth, post_signed_data, FAKE_DEVICE

    cookies = channel_auth.get("cookies", {}) or {}
    if not cookies:
        logging.error("[VivoChannel] build_replay_data: cookies 为空")
        return None

    try:
        r = requests.get(VIVO_UNION_GET.format(game_package=DEFAULT_GAME_PACKAGE),
                          cookies=cookies, timeout=15)
        data = r.json()
        logging.info(f"[VivoChannel] union/get: code={data.get('code')}")
        if data.get("code") != 0:
            logging.error(f"[VivoChannel] union/get 失败: {data}")
            return None
        user_data = data.get("data", {})
    except Exception as e:
        logging.error(f"[VivoChannel] union/get 异常: {e}")
        return None

    sub_accounts = user_data.get("subAccounts", [])
    if not sub_accounts:
        logging.error("[VivoChannel] 无子账号")
        return None
    sub = sub_accounts[0]
    sub_open_id = sub.get("subOpenId", "")
    if not sub_open_id:
        logging.error("[VivoChannel] subOpenId 为空")
        return None

    try:
        r2 = requests.post("https://joint.vivo.com.cn/h5/union/use",
                           data={"noLoading": True, "subOpenId": sub_open_id,
                                 "gamePackage": DEFAULT_GAME_PACKAGE},
                           cookies=cookies, timeout=15)
        use_data = r2.json()
        logging.info(f"[VivoChannel] union/use: code={use_data.get('code')}")
        if use_data.get("code") != 0:
            logging.error(f"[VivoChannel] union/use 失败: {use_data}")
            return None
        open_token = use_data.get("data", "")
        if not open_token:
            logging.error("[VivoChannel] openToken 为空")
            return None
    except Exception as e:
        logging.error(f"[VivoChannel] union/use 异常: {e}")
        return None

    fd = dict(FAKE_DEVICE)
    sauth_body = build_sauth(
        login_channel="nearme_vivo", app_channel="nearme_vivo",
        uid=sub_open_id, session=open_token, game_id=short_game_id,
        sdk_version="4.7.2.0",
        custom_data={"realname": _json.dumps({"realname_type": 0, "age": 22})},
    )
    # Vivo 需要自定义 JSON 编码（/ → \/），对齐 idv-login 的签名
    uni_data = post_signed_data(sauth_body, short_game_id, need_custom_encode=True)
    unisdk_json_b64 = uni_data.get("unisdk_login_json", "")
    if not unisdk_json_b64:
        logging.error("[VivoChannel] uni_sauth 缺少 unisdk_login_json")
        return None
    unisdk_login = _json.loads(_b64.b64decode(unisdk_json_b64).decode())

    extra_fields = {"realname": _json.dumps({"realname_type": 0, "age": 22})}
    extra_res = {"SAUTH_STR": "", "SAUTH_JSON": "", **extra_fields}
    json_data = {"extra_data": "", "get_access_token": "1",
                 "sdk_udid": fd["udid"], "realname": extra_fields["realname"]}
    json_data.update(sauth_body)
    str_data = json_data.copy()
    str_data["username"] = unisdk_login.get("username", "")
    str_data_str = "&".join(f"{k}={v}" for k, v in str_data.items())
    extra_res["SAUTH_STR"] = _b64.b64encode(str_data_str.encode()).decode()
    extra_res["SAUTH_JSON"] = _b64.b64encode(_json.dumps(json_data).encode()).decode()

    return {
        "user_id": sub_open_id,
        "token": _b64.b64encode(open_token.encode()).decode(),
        "login_channel": "nearme_vivo", "app_channel": "nearme_vivo", "pay_channel": "nearme_vivo",
        "udid": fd["udid"], "sdk_version": "4.7.2.0", "jf_game_id": short_game_id,
        "extra_data": "", "extra_unisdk_data": _json.dumps(extra_res),
        "gv": "157", "gvn": "1.5.80", "cv": "a1.5.0",
    }
