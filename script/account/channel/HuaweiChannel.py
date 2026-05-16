"""华为渠道服登录 — 给 WebView2 追加 NavigationStarting 事件处理器"""

import logging
import threading
import time
import uuid
import base64
import hashlib
from urllib.parse import urlparse, parse_qs

import requests
import webview

import clr

clr.AddReference("System.Windows.Forms")
clr.AddReference("Microsoft.Web.WebView2.WinForms")


# 一梦江湖华为服 OAuth 参数（来自 idv-login cloudRes game_id=h42）
HMS_CLIENT_ID = "100112247"
HMS_SCOPE = "openid"
HMS_TOKEN_URL = "https://oauth-login.cloud.huawei.com/oauth2/v3/token"
REDIRECT_URI = "hms://redirect_url"


def _generate_code_challenge(code_verifier: str) -> str:
    sha256 = hashlib.sha256()
    sha256.update(code_verifier.encode("ascii"))
    return base64.urlsafe_b64encode(sha256.digest()).decode("ascii").rstrip("=")


def _build_auth_url(client_id: str, scope: str) -> tuple[str, str]:
    code_verifier = str(uuid.uuid4())
    code_challenge = _generate_code_challenge(code_verifier)
    url = (
        "https://oauth-login.cloud.huawei.com/oauth2/v3/authorize?"
        "access_type=offline&response_type=code&"
        f"client_id={client_id}&redirect_uri={REDIRECT_URI}&"
        f"scope={scope}&code_challenge={code_challenge}&"
        "code_challenge_method=S256"
    )
    return url, code_verifier


def _exchange_code(code: str, code_verifier: str) -> dict | None:
    try:
        resp = requests.post(
            HMS_TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": HMS_CLIENT_ID,
                "code_verifier": code_verifier,
                "redirect_uri": REDIRECT_URI,
            },
            timeout=15,
        )
        result = resp.json()
        if "access_token" in result:
            logging.info("[HuaweiChannel] token 获取成功")
            # 从 id_token 或 access_token JWT 中提取 uid
            for token_key in ("id_token", "access_token"):
                token = result.get(token_key, "")
                if token and "." in token:
                    try:
                        payload = token.split(".")[1]
                        payload += "=" * (-len(payload) % 4)
                        jwt_data = json.loads(base64.urlsafe_b64decode(payload))
                        uid = jwt_data.get("sub") or jwt_data.get("uid") or jwt_data.get("user_id")
                        if uid:
                            result["_uid"] = str(uid)
                            logging.info(f"[HuaweiChannel] 提取 uid: {uid}")
                            break
                    except Exception:
                        pass
            return result
        logging.error(f"[HuaweiChannel] token 交换失败: {result}")
    except Exception as e:
        logging.error(f"[HuaweiChannel] token 请求异常: {e}")
    return None


def _get_game_auth(access_token: str) -> dict | None:
    """调用华为 getGameAuthSign API，获取 gameAuthSign + playerId"""
    try:
        body = {
            "gamePopTime": 0,
            "idType": 2,
            "hmsSdkVersionCode": 60100302,
            "hmsSdkVersionName": "6.1.0.302",
            "hmsApkVersionName": "6.14.0.302",
            "hmsApkVersionCode": 61400302,
            "kitver": 61400300,
            "thirdAppVersion": "1.5.99",
            "clientPackage": "com.huawei.gamebox",
            "locale": "zh_CN",
            "timeZone": "Asia/Shanghai",
            "serviceType": 47,
            "odm": 0,
            "countryCode": "CN",
            "deviceIdType": 4,
            "method": "client.hms.gs.getGameAuthSign",
            "extraBody": f'json={{"appId":"{HMS_CLIENT_ID}"}}',
            "accessToken": access_token,
        }
        resp = requests.post(
            "https://jgw-drcn.jos.dbankcloud.cn/gameservice/api/gbClientApi",
            headers={
                "User-Agent": "com.huawei.hms.game/6.14.0.300 (Linux; Android 12; M2102K1AC) RestClient/7.0.6.300",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data=body,
            timeout=15,
        )
        result = resp.json()
        gs = result.get("gameAuthSign")
        pid = result.get("playerId")
        if gs and pid:
            logging.info(f"[HuaweiChannel] getGameAuthSign 成功, playerId={pid}")
            return {
                "gameAuthSign": gs,
                "playerId": str(pid),
                "playerLevel": str(result.get("playerLevel", "")),
                "ts": str(result.get("ts", "")),
                "raw": result,
            }
        logging.error(f"[HuaweiChannel] getGameAuthSign 失败: {result}")
    except Exception as e:
        logging.error(f"[HuaweiChannel] getGameAuthSign 异常: {e}")
    return None


def _add_navigation_handler(window, code_container: dict) -> bool:
    """给窗口的 WebView2 追加 NavigationStarting 事件处理器"""
    try:
        from webview.platforms.winforms import BrowserView

        form = BrowserView.instances.get(window.uid)
        if not form:
            logging.error("[HuaweiChannel] 找不到 BrowserForm 实例")
            return False
        wv2 = form.webview  # WebView2 WinForms 控件

        from Microsoft.Web.WebView2.Core import CoreWebView2NavigationStartingEventArgs
        from System import EventHandler

        def handler(sender, args: CoreWebView2NavigationStartingEventArgs):
            uri = args.Uri or ""
            if uri.startswith("hms://"):
                args.Cancel = True
                parsed = urlparse(uri)
                code = parse_qs(parsed.query).get("code", [""])[0]
                if code:
                    code_container["code"] = code
                    logging.info(f"[HuaweiChannel] 拦截 hms:// 成功")

        event_type = EventHandler[CoreWebView2NavigationStartingEventArgs]
        wv2.NavigationStarting += event_type(handler)
        logging.debug("[HuaweiChannel] NavigationStarting 处理器已追加")
        return True
    except Exception as e:
        logging.error(f"[HuaweiChannel] 追加事件失败: {e}")
        return False


class HuaweiLogin:
    def __init__(self):
        self._window: webview.Window | None = None
        self._result: dict | None = None
        self._code_verifier: str = ""
        self._done = threading.Event()

    def login(self) -> dict | None:
        auth_url, self._code_verifier = _build_auth_url(HMS_CLIENT_ID, HMS_SCOPE)
        self._done.clear()
        code_container: dict = {}

        # 提前下载图标，窗口创建后立即设置
        try:
            icon_bytes = requests.get("https://consumer.huawei.com/favicon.ico", timeout=5).content
        except Exception:
            icon_bytes = None

        self._window = webview.create_window("华为账号登录", auth_url, width=1050, height=810)

        if icon_bytes:
            from script.account.channel.ChannelUtils import _apply_icon_bytes
            _apply_icon_bytes(self._window, icon_bytes)

        def _run():
            time.sleep(1.5)  # 等 WebView2 初始化
            _add_navigation_handler(self._window, code_container)

            for _ in range(300):
                if self._done.is_set():
                    return
                if code_container.get("code"):
                    token = _exchange_code(code_container["code"], self._code_verifier)
                    if token:
                        # 调 getGameAuthSign 获取 gameAuthSign + playerId
                        ga = _get_game_auth(token.get("access_token", ""))
                        if ga:
                            token["_game_auth_sign"] = ga["gameAuthSign"]
                            token["_player_id"] = ga["playerId"]
                            token["_player_level"] = ga["playerLevel"]
                            token["_ts"] = ga["ts"]
                        self._result = token
                    self._done.set()
                    return
                time.sleep(0.5)
            logging.warning("[HuaweiChannel] 登录超时")
            self._done.set()

        threading.Thread(target=_run, daemon=True).start()
        self._done.wait(timeout=160)

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
        return self._result


def build_replay_data(channel_auth: dict, short_game_id: str) -> dict | None:
    """渠道回放：构建 confirm_login 所需的 body 数据（不含 uuid/game_id）

    对齐 idv-login huaChannelHandler.get_uniSdk_data + _build_extra_unisdk_data
    """
    import json as _json
    from script.account.channel.ChannelUtils import build_sauth, post_signed_data, FAKE_DEVICE

    ct = channel_auth.get("channel_type", "")
    access_token = channel_auth.get("access_token", "")

    # 刷新 gameAuthSign
    ga = _get_game_auth(access_token) if access_token else None
    if ga:
        player_id = ga.get("playerId", channel_auth.get("player_id", ""))
        game_auth = ga.get("gameAuthSign", channel_auth.get("game_auth_sign", ""))
        player_level = ga.get("playerLevel", channel_auth.get("player_level", ""))
        ts = ga.get("ts", channel_auth.get("ts", ""))
    else:
        player_id = channel_auth.get("player_id", "")
        game_auth = channel_auth.get("game_auth_sign", "")
        player_level = channel_auth.get("player_level", "")
        ts = channel_auth.get("ts", "")

    if not game_auth:
        logging.error("[HuaweiChannel] build_replay_data: game_auth 为空")
        return None

    fd = dict(FAKE_DEVICE)

    # buildSAUTH (uniBody)
    sauth_body = build_sauth(
        login_channel=ct,
        app_channel=ct,
        uid=player_id,
        session=game_auth,
        game_id=short_game_id,
        custom_data={
            "anonymous": "",
            "get_access_token": "0",
            "extra_data": str(player_level),
            "timestamp": ts,
            "realname": _json.dumps({"realname_type": 0, "duration": 0}),
        },
    )

    # postSignedData → 获取 unisdk_login_json
    uni_data = post_signed_data(sauth_body, short_game_id)
    unisdk_json_b64 = uni_data.get("unisdk_login_json", "")
    if not unisdk_json_b64:
        logging.error("[HuaweiChannel] uni_sauth 缺少 unisdk_login_json")
        return None
    unisdk_login = _json.loads(base64.b64decode(unisdk_json_b64).decode())

    # _build_extra_unisdk_data
    extra_res = {"SAUTH_STR": "", "SAUTH_JSON": ""}
    extra_fields = {
        "anonymous": "",
        "get_access_token": "0",
        "extra_data": str(player_level),
        "timestamp": ts,
        "realname": _json.dumps({"realname_type": 0, "duration": 0}),
    }
    extra_res.update(extra_fields)

    json_data = {
        "extra_data": str(player_level),
        "get_access_token": "0",
        "sdk_udid": fd["udid"],
        "realname": extra_fields["realname"],
    }
    json_data.update(sauth_body)

    str_data = json_data.copy()
    str_data["username"] = unisdk_login.get("username", "")
    str_data_str = "&".join(f"{k}={v}" for k, v in str_data.items())

    extra_res["SAUTH_STR"] = base64.b64encode(str_data_str.encode()).decode()
    extra_res["SAUTH_JSON"] = base64.b64encode(_json.dumps(json_data).encode()).decode()

    return {
        "user_id": player_id,
        "token": base64.b64encode(game_auth.encode()).decode(),
        "login_channel": ct,
        "udid": fd["udid"],
        "app_channel": ct,
        "sdk_version": "6.1.0.301",
        "jf_game_id": short_game_id,
        "pay_channel": ct,
        "extra_data": "",
        "extra_unisdk_data": _json.dumps(extra_res),
        "gv": "157",
        "gvn": "1.5.80",
        "cv": "a1.5.0",
    }


def record() -> dict | None:
    """录制：打开华为 OAuth 窗口 → 返回 channel_auth"""
    login = HuaweiLogin()
    result = login.login()
    if not result:
        return None
    return {
        "channel_type": "huawei",
        "access_token": result.get("access_token", ""),
        "refresh_token": result.get("refresh_token", ""),
        "expires_in": result.get("expires_in", 0),
        "game_auth_sign": result.get("_game_auth_sign", ""),
        "player_id": result.get("_player_id", ""),
        "player_level": result.get("_player_level", ""),
        "ts": result.get("_ts", ""),
    }
