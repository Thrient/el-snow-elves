"""Bilibili 渠道服登录 — pywebview 浏览器 + XHR 拦截 + NavigationStarting 兜底

签名算法对齐 idv-login: sorted_values_joined + appKey → MD5
登录页 URL 不加 sign（和 idv-login 一致），API 调用才签名。
"""

import hashlib
import json
import logging
import threading
import time

import requests
import webview
from urllib.parse import urlencode

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("Microsoft.Web.WebView2.WinForms")


# 默认参数（第五人格 B站服，来自 idv-login cloudRes game_id=h42）
DEFAULT_GAME_ID = "301"
DEFAULT_APP_KEY = "h9Ejat5tFh81cq8"


# ── Bilibili Sign ────────────────────────────────────────────

def compute_sign(params: dict, app_key: str = DEFAULT_APP_KEY) -> str:
    """Bilibili Game SDK 签名：按 key 排序 → 拼接 value → 追加 appKey → MD5。
    对齐 idv-login bilibiliChannel.py compute_sign()。
    """
    sorted_items = sorted(params.items())
    plaintext = "".join(
        str(v) for k, v in sorted_items if k != "sign" and v is not None
    )
    plaintext += app_key
    return hashlib.md5(plaintext.encode("utf-8")).hexdigest()


# ── 登录页 URL（不加 sign，对齐 idv-login）──────────────────

_LOGIN_URL = (
    "https://sdk.biligame.com/login/"
    f"?cef=true&gameId={DEFAULT_GAME_ID}&appKey={DEFAULT_APP_KEY}&is_gov_ver=1"
)


# ── XHR 拦截脚本（参考 idv-login bilibiliChannel.py _build_intercept_js）──

_INTERCEPT_JS = r"""
(function() {
  if (window.__bili_injected) return;
  window.__bili_injected = true;
  window.__bili_result = null;

  var AGREEMENT_MOCK = JSON.stringify({
    request_id: "mock",
    timestamp: Date.now(),
    code: 0,
    message: "响应成功",
    data: { cooperation_mode: 0, agreement_switch: "OFF", privacy_tips_switch: "ON" },
    success: true
  });

  var origOpen = XMLHttpRequest.prototype.open;
  var origSend = XMLHttpRequest.prototype.send;
  var origSetHeader = XMLHttpRequest.prototype.setRequestHeader;

  XMLHttpRequest.prototype.open = function(method, url) {
    this.__url = (typeof url === 'string') ? url : String(url);
    this.__method = method;
    this.__mock = this.__url.indexOf('/api/agreement/config') !== -1;
    if (!this.__mock) return origOpen.apply(this, arguments);
  };

  XMLHttpRequest.prototype.setRequestHeader = function() {
    if (this.__mock) return;
    return origSetHeader.apply(this, arguments);
  };

  XMLHttpRequest.prototype.send = function(body) {
    var self = this;

    if (this.__mock) {
      setTimeout(function() {
        try {
          Object.defineProperty(self, 'readyState',   { value: 4,   configurable: true });
          Object.defineProperty(self, 'status',        { value: 200, configurable: true });
          Object.defineProperty(self, 'statusText',    { value: 'OK', configurable: true });
          Object.defineProperty(self, 'responseText',  { value: AGREEMENT_MOCK, configurable: true });
          Object.defineProperty(self, 'response',      { value: AGREEMENT_MOCK, configurable: true });
          self.getAllResponseHeaders = function() { return 'content-type: application/json\r\n'; };
          if (typeof self.onreadystatechange === 'function') self.onreadystatechange();
          self.dispatchEvent(new Event('load'));
          self.dispatchEvent(new Event('loadend'));
        } catch(e) {}
      }, 10);
      return;
    }

    this.addEventListener('load', function() {
      try {
        var u = self.__url || '';
        if (u.indexOf('/api/pcg/otp/login') !== -1 || u.indexOf('/api/pcg/login') !== -1) {
          var resp = JSON.parse(self.responseText);
          if (resp && resp.code === 0) {
            var ak = resp.access_key || (resp.data && resp.data.access_key);
            if (ak) {
              window.__bili_result = resp;
            }
          }
        }
      } catch(e) {}
    });

    return origSend.apply(this, arguments);
  };
})();
"""


def _add_navigation_handler(window, login_container: dict) -> bool:
    """给 WebView2 追加 NavigationStarting 事件处理器，兜底检测登录完成"""
    try:
        from webview.platforms.winforms import BrowserView
        from Microsoft.Web.WebView2.Core import CoreWebView2NavigationStartingEventArgs
        from System import EventHandler

        form = BrowserView.instances.get(window.uid)
        if not form:
            logging.error("[BilibiliChannel] 找不到 BrowserForm 实例")
            return False
        wv2 = form.webview

        def handler(sender, args: CoreWebView2NavigationStartingEventArgs):
            uri = args.Uri or ""
            if "biligame.com" in uri and ("/success" in uri or "/result" in uri):
                logging.debug(f"[BilibiliChannel] NavigationStarting 检测到登录完成: {uri[:120]}")
                login_container["url"] = uri

        wv2.NavigationStarting += EventHandler[CoreWebView2NavigationStartingEventArgs](handler)
        logging.debug("[BilibiliChannel] NavigationStarting 处理器已追加")
        return True
    except Exception as e:
        logging.error(f"[BilibiliChannel] 追加事件失败: {e}")
        return False


def _get_cookies_safe(window) -> dict[str, str]:
    """安全调用 window.get_cookies()，返回 {name: value} 字典"""
    try:
        raw = window.get_cookies()
        result: dict[str, str] = {}
        for cookie in raw:
            for name, morsel in cookie.items():
                if name and morsel.value:
                    result[name] = morsel.value
        logging.debug(f"[BilibiliChannel] get_cookies 获取到 {len(result)} 个")
        return result
    except Exception as e:
        logging.warning(f"[BilibiliChannel] get_cookies 失败: {e}")
        return {}


def _validate_access_key(access_key: str, uid: str) -> bool:
    """调用 auto.login 验证 access_key 是否仍然有效。
    签名算法对齐 idv-login: 只传 3 个核心参数 + compute_sign。
    """
    try:
        params = {
            "access_key": access_key,
            "game_id": str(DEFAULT_GAME_ID),
            "is_gov_ver": 1,
        }
        params["sign"] = compute_sign(params)
        al_url = "https://wpg-api.biligame.com/api/pcg/auto.login?" + urlencode(params)
        resp = requests.post(al_url, timeout=15)
        al_data = resp.json()
        if al_data.get("code") == 0:
            logging.info(f"[BilibiliChannel] access_key 验证成功, uid={uid}")
            return True
        logging.warning(
            f"[BilibiliChannel] access_key 验证失败: code={al_data.get('code')}, "
            f"msg={al_data.get('message', '')}"
        )
        return False
    except Exception as e:
        logging.warning(f"[BilibiliChannel] access_key 验证异常: {e}")
        return False


class BilibiliLogin:
    """B站渠道登录 — 打开浏览器窗口，用户输入 B站 账号密码/OTP"""

    def __init__(self, game_id: str = DEFAULT_GAME_ID, app_key: str = DEFAULT_APP_KEY):
        self.game_id = game_id
        self.app_key = app_key
        self._window: webview.Window | None = None
        self._result: dict | None = None
        self._cookies: dict[str, str] = {}
        self._done = threading.Event()

    @property
    def login_url(self) -> str:
        # 对齐 idv-login: 登录页不加 sign
        return (
            "https://sdk.biligame.com/login/"
            f"?cef=true&gameId={self.game_id}&appKey={self.app_key}&is_gov_ver=1"
        )

    def login(self) -> dict | None:
        """阻塞：打开窗口 → 注入拦截器 → 等待登录完成 → 返回结果"""
        self._done.clear()
        login_container: dict = {}

        try:
            icon_bytes = requests.get("https://www.bilibili.com/favicon.ico", timeout=5).content
        except Exception:
            icon_bytes = None

        self._window = webview.create_window(
            "Bilibili 账号登录",
            self.login_url,
            width=370,
            height=480,
        )

        if icon_bytes:
            from script.account.channel.ChannelUtils import _apply_icon_bytes
            _apply_icon_bytes(self._window, icon_bytes)

        def _run():
            time.sleep(2)  # 等 WebView2 初始化

            try:
                self._window.evaluate_js(_INTERCEPT_JS)
            except Exception:
                pass

            _add_navigation_handler(self._window, login_container)

            for _ in range(240):  # 最长 2 分钟
                if self._done.is_set():
                    return

                try:
                    raw = self._window.evaluate_js("JSON.stringify(window.__bili_result)")
                    if raw and raw != "null":
                        self._result = json.loads(raw)
                        logging.info(
                            f"[BilibiliChannel] 登录成功: uid={self._result.get('uid')}, "
                            f"uname={self._result.get('uname')}"
                        )
                        self._done.set()
                        break
                except Exception:
                    pass

                if login_container.get("url"):
                    logging.info("[BilibiliChannel] NavigationStarting 兜底触发，尝试获取已拦截数据")
                    time.sleep(1)
                    try:
                        raw2 = self._window.evaluate_js("JSON.stringify(window.__bili_result)")
                        if raw2 and raw2 != "null":
                            self._result = json.loads(raw2)
                    except Exception:
                        pass
                    self._done.set()
                    break

                time.sleep(0.5)

            if not self._done.is_set():
                logging.warning("[BilibiliChannel] 登录超时")
                self._done.set()

            self._cookies = _get_cookies_safe(self._window)
            _close_window_safe(self._window)

        threading.Thread(target=_run, daemon=True).start()
        self._done.wait(timeout=130)

        return self._result

    @property
    def cookies(self) -> dict:
        return self._cookies


def _close_window_safe(window):
    """通过 WinForms Invoke 安全关闭窗口"""
    try:
        from webview.platforms.winforms import BrowserView
        from System.Windows.Forms import MethodInvoker
        form = BrowserView.instances.get(window.uid) if window else None
        if form:
            form.Invoke(MethodInvoker(lambda: form.Close()))
    except Exception:
        pass


def record() -> dict | None:
    """录制：打开 B站 登录窗口 → 返回 channel_auth"""
    login = BilibiliLogin()
    result = login.login()
    if not result:
        return None
    data = result.get("data") if isinstance(result, dict) and "data" in result else result
    return {
        "channel_type": "bilibili",
        "access_key": data.get("access_key", ""),
        "uid": data.get("uid", ""),
        "uname": data.get("uname", ""),
        "cookies": login.cookies,
    }


def build_replay_data(channel_auth: dict, short_game_id: str) -> dict | None:
    """渠道回放：验证 access_key → uni_sauth → 构建 confirm 数据"""
    import json as _json
    import base64 as _b64
    from script.account.channel.ChannelUtils import build_sauth, post_signed_data, FAKE_DEVICE

    access_key = str(channel_auth.get("access_key", ""))
    uid = str(channel_auth.get("uid", ""))
    if not access_key or not uid:
        logging.error("[BilibiliChannel] build_replay_data: 缺少 access_key 或 uid")
        return None

    if not _validate_access_key(access_key, uid):
        logging.error("[BilibiliChannel] access_key 已失效，请重新录制账号")
        return None

    fd = dict(FAKE_DEVICE)

    sauth_body = build_sauth(
        login_channel="bilibili_sdk",
        app_channel="bilibili_sdk",
        uid=uid,
        session=access_key,
        game_id=short_game_id,
        sdk_version="5.9.6",
    )

    uni_data = post_signed_data(sauth_body, short_game_id, need_custom_encode=True)
    unisdk_json_b64 = uni_data.get("unisdk_login_json", "")
    if not unisdk_json_b64:
        logging.error("[BilibiliChannel] uni_sauth 缺少 unisdk_login_json")
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
        "user_id": uid,
        "token": _b64.b64encode(access_key.encode()).decode(),
        "login_channel": "bilibili_sdk",
        "udid": fd["udid"],
        "app_channel": "bilibili_sdk",
        "sdk_version": "5.9.6",
        "jf_game_id": short_game_id,
        "pay_channel": "bilibili_sdk",
        "extra_data": "",
        "extra_unisdk_data": _json.dumps(extra_res),
        "gv": "157",
        "gvn": "1.5.80",
        "cv": "a1.5.0",
    }
