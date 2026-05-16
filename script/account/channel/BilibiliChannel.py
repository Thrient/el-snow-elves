"""Bilibili 渠道服登录 — pywebview 浏览器 + XHR 拦截"""

import hashlib
import json
import logging
import threading
import time

import requests
import webview
from urllib.parse import urlencode


# 默认参数（第五人格 B站服）
DEFAULT_GAME_ID = "301"
DEFAULT_APP_KEY = "h9Ejat5tFh81cq8"

_LOGIN_URL = (
    "https://sdk.biligame.com/login/"
    f"?cef=true&gameId={DEFAULT_GAME_ID}&appKey={DEFAULT_APP_KEY}&is_gov_ver=1"
)

# 注入到登录页的 XHR 拦截脚本
_INTERCEPT_JS = r"""
(function() {
  if (window.__bili_injected) return;
  window.__bili_injected = true;
  window.__bili_result = null;

  var origOpen = XMLHttpRequest.prototype.open;
  var origSend = XMLHttpRequest.prototype.send;

  XMLHttpRequest.prototype.open = function(method, url) {
    this.__url = (typeof url === 'string') ? url : String(url);
    this.__method = method;
    return origOpen.apply(this, arguments);
  };

  XMLHttpRequest.prototype.send = function(body) {
    var self = this;
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


class BilibiliLogin:
    """B站渠道登录 — 打开浏览器窗口，用户输入 B站 账号密码/OTP"""

    def __init__(self, game_id: str = DEFAULT_GAME_ID, app_key: str = DEFAULT_APP_KEY):
        self.game_id = game_id
        self.app_key = app_key
        self._window: webview.Window | None = None
        self._result: dict | None = None
        self._done = threading.Event()

    @property
    def login_url(self) -> str:
        return (
            "https://sdk.biligame.com/login/"
            f"?cef=true&gameId={self.game_id}&appKey={self.app_key}&is_gov_ver=1"
        )

    def login(self) -> dict | None:
        """阻塞：打开窗口 → 等待登录完成 → 返回结果"""
        self._done.clear()

        # 提前下载图标
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

        # 等页面加载后注入拦截脚本，然后轮询结果
        def _run():
            time.sleep(2)  # 等页面加载
            try:
                self._window.evaluate_js(_INTERCEPT_JS)
            except Exception:
                pass

            for _ in range(240):  # 最长 2 分钟
                if self._done.is_set():
                    return
                try:
                    raw = self._window.evaluate_js("JSON.stringify(window.__bili_result)")
                    if raw and raw != "null":
                        self._result = json.loads(raw)
                        logging.info(f"[BilibiliChannel] 登录成功: uid={self._result.get('uid')}, uname={self._result.get('uname')}")
                        self._done.set()
                        break
                except Exception:
                    pass
                time.sleep(0.5)
            if not self._done.is_set():
                logging.warning("[BilibiliChannel] 登录超时")
                self._done.set()

        threading.Thread(target=_run, daemon=True).start()
        self._done.wait(timeout=130)

        # 关闭窗口
        try:
            self._window.evaluate_js("window.close()")
        except Exception:
            pass
        return self._result


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
    }


def build_replay_data(channel_auth: dict, short_game_id: str) -> dict | None:
    """渠道回放：access_key → auto.login 验证 → uni_sauth → 构建 confirm 数据"""
    import json as _json
    import base64 as _b64
    from script.account.channel.ChannelUtils import build_sauth, post_signed_data, FAKE_DEVICE

    access_key = channel_auth.get("access_key", "")
    uid = channel_auth.get("uid", "")
    if not access_key or not uid:
        logging.error("[BilibiliChannel] build_replay_data: 缺少 access_key 或 uid")
        return None

    # Step 1: auto.login 验证 token 有效性
    try:
        sign_params = {"access_key": access_key, "game_id": str(DEFAULT_GAME_ID), "is_gov_ver": 1}
        raw_sign = "&".join(f"{k}={v}" for k, v in sorted(sign_params.items())) + "&appSecret=" + DEFAULT_APP_KEY
        sign_params["sign"] = hashlib.md5(raw_sign.encode()).hexdigest()
        al_url = "https://wpg-api.biligame.com/api/pcg/auto.login?" + urlencode(sign_params)
        resp = requests.post(al_url, timeout=15)
        al_data = resp.json()
        if al_data.get("code") != 0:
            logging.warning(f"[BilibiliChannel] auto.login 返回非零: {al_data.get('code')}，继续尝试")
    except Exception as e:
        logging.warning(f"[BilibiliChannel] auto.login 异常，继续尝试: {e}")

    fd = dict(FAKE_DEVICE)

    # Step 2: buildSAUTH
    sauth_body = build_sauth(
        login_channel="bilibili_sdk",
        app_channel="bilibili_sdk",
        uid=uid,
        session=access_key,
        game_id=short_game_id,
        sdk_version="5.9.6",
    )

    # Step 3: postSignedData
    uni_data = post_signed_data(sauth_body, short_game_id)
    unisdk_json_b64 = uni_data.get("unisdk_login_json", "")
    if not unisdk_json_b64:
        logging.error("[BilibiliChannel] uni_sauth 缺少 unisdk_login_json")
        return None
    unisdk_login = _json.loads(_b64.b64decode(unisdk_json_b64).decode())

    # Step 4: _build_extra_unisdk_data
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
