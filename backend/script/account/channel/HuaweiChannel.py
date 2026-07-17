"""华为渠道服登录 — 给 WebView2 追加 NavigationStarting 事件处理器"""

import json
import logging
import os
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


# 一梦江湖华为服 OAuth 参数
HMS_CLIENT_ID = "100112247"
HMS_SCOPE = "openid"
HMS_TOKEN_URL = "https://oauth-login.cloud.huawei.com/oauth2/v3/token"
REDIRECT_URI = "hms://redirect_url"

# WebView2 持久化缓存目录（保留 OAuth cookie，跳过重复授权）
# 复用 pywebview 内部的 _wf.cache_dir 机制，与 Qihu360 模式一致
import webview.platforms.winforms as _wf
from script.config.Setting import APP_DATA

_HUAWEI_SESSIONS = os.path.join(APP_DATA, "huawei_sessions")
os.makedirs(_HUAWEI_SESSIONS, exist_ok=True)

# JS: 监听表单提交，捕获华为账号密码（存入 window.__huawei_creds）
_CAPTURE_CREDS_JS = """
(function() {
    if (window.__capture_installed) return;
    window.__capture_installed = true;
    document.addEventListener('submit', function() {
        try {
            var inputs = document.querySelectorAll('input');
            var accountInput = Array.prototype.find.call(inputs, function(i) {
                return i.getAttribute('ht') === 'input_pwdlogin_account';
            });
            var pwdInput = Array.prototype.find.call(inputs, function(i) {
                return i.getAttribute('ht') === 'input_pwdlogin_pwd';
            });
            if (accountInput && accountInput.value) {
                window.__huawei_creds = JSON.stringify({
                    account: accountInput.value,
                    pwd: pwdInput ? pwdInput.value : ''
                });
            }
        } catch(e) {}
    }, true);
})();
"""

# JS: 读取缓存的凭证（用于录制时在 hms:// 拦截后提取）
_READ_CREDS_JS = "(function() { return window.__huawei_creds || ''; })();"


def _autofill_js(account: str, pwd: str) -> str:
    """生成自动填充华为登录表单并提交的 JS（idv-login 同款技术）"""
    safe_account = json.dumps(account)
    safe_pwd = json.dumps(pwd)
    return (
        '(function(){'
        'if(window.__auto_filled)return"already_filled";'
        'var inputs=document.querySelectorAll("input");'
        'var a=Array.prototype.find.call(inputs,function(i){return i.getAttribute("ht")==="input_pwdlogin_account"});'
        'var p=Array.prototype.find.call(inputs,function(i){return i.getAttribute("ht")==="input_pwdlogin_pwd"});'
        'if(!a||!p)return"no_form";'
        'window.__auto_filled=true;'
        'function iv(t,v){var e=document.createEvent("HTMLEvents");e.initEvent("input",true,true);t.value=v;t.dispatchEvent(e);}'
        'a.focus();iv(a,' + safe_account + ');'
        'p.focus();iv(p,' + safe_pwd + ');'
        'setTimeout(function(){'
        'var b=document.querySelector(\'button[ht="input_pwdlogin_btn"]\')||document.querySelector("form button")||document.querySelector("input[type=\\"submit\\"]");'
        'if(b){b.focus();b.click();}'
        '},600);'
        'return"filled";'
        '})();'
    )


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


def _refresh_access_token(refresh_token: str) -> str | None:
    """用 refresh_token 刷新 access_token"""
    if not refresh_token:
        return None
    try:
        resp = requests.post(
            HMS_TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": HMS_CLIENT_ID,
                "redirect_uri": REDIRECT_URI,
            },
            timeout=15,
        )
        result = resp.json()
        at = result.get("access_token", "")
        if at:
            logging.info("[HuaweiChannel] access_token 刷新成功")
            return at
        logging.error(f"[HuaweiChannel] token 刷新失败: {result}")
    except Exception as e:
        logging.error(f"[HuaweiChannel] token 刷新异常: {e}")
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


def _auto_relogin(client_id: str, account: str, password: str, cache_dir: str = "") -> dict | None:
    """自动静默重登：后台打开华为 OAuth 窗口，自动填表提交，换新 token

    复用持久化 cache_dir 保留 cookie，跳过重复授权页。
    无验证码时窗口保持隐藏，用户无感。30s 仍未完成则显示窗口。

    Args:
        client_id: HMS 应用 ID
        account: 华为账号
        password: 华为密码
        cache_dir: 持久化 WebView2 缓存目录（保留 cookie）

    Returns:
        dict 或 None
    """
    if not account or not password:
        logging.warning("[HuaweiChannel] 缺少账号密码，无法自动重登")
        return None

    code_verifier = str(uuid.uuid4())
    code_challenge = _generate_code_challenge(code_verifier)
    auth_url = (
        "https://oauth-login.cloud.huawei.com/oauth2/v3/authorize?"
        "access_type=offline&response_type=code&"
        f"client_id={client_id}&redirect_uri={REDIRECT_URI}&"
        f"scope={HMS_SCOPE}&code_challenge={code_challenge}&"
        "code_challenge_method=S256"
    )

    logging.info("[HuaweiChannel] 开始自动重登...")
    code_container: dict = {}
    fill_success = False
    window_shown = False
    window: webview.Window | None = None

    # —— _wf.cache_dir 操作：使用持久化目录保留 cookie ——
    if cache_dir:
        temp_dir = cache_dir
    else:
        temp_dir = os.path.join(_HUAWEI_SESSIONS, f"relogin_{uuid.uuid4().hex[:8]}")
    os.makedirs(temp_dir, exist_ok=True)
    original_cache_dir = _wf.cache_dir
    _wf.cache_dir = temp_dir
    logging.debug("[HuaweiChannel] 重登缓存目录: %s", temp_dir)

    try:
        window = webview.create_window(
            "华为自动登录", auth_url, width=1, height=1, hidden=True
        )
    finally:
        _wf.cache_dir = original_cache_dir

    def _show():
        nonlocal window_shown
        if not window_shown and window:
            try:
                window.show()
                window.restore()
                window_shown = True
            except Exception as e:
                logging.debug("[HuaweiChannel] 显示窗口失败: %s", e)

    time.sleep(2.0)  # 等 WebView2 初始化
    _add_navigation_handler(window, code_container)

    for i in range(600):  # 最多等 5 分钟
        if code_container.get("code"):
            break

        # 尝试自动填表
        if not fill_success:
            try:
                from webview.platforms.winforms import BrowserView
                form = BrowserView.instances.get(window.uid) if window else None
                if form:
                    result = form.webview.CoreWebView2.ExecuteScriptAsync(_autofill_js(account, password))
                    result_str = str(result.Result) if result.Result else ""
                    if "filled" in result_str:
                        fill_success = True
                        logging.info("[HuaweiChannel] 自动填充成功")
                    elif "no_form" in result_str:
                        pass  # 登录页还没加载
                    elif "already_filled" in result_str:
                        fill_success = True
            except Exception as e:
                logging.debug("[HuaweiChannel] 自动填充尝试: %s", e)

        # 30 秒未完成 → 显示窗口（可能需验证码）
        if i > 60 and not window_shown and not code_container.get("code"):
            logging.info("[HuaweiChannel] 30s 未完成，显示窗口等待手动操作")
            _show()

        time.sleep(0.5)

    # 关闭窗口
    try:
        from webview.platforms.winforms import BrowserView
        import clr
        clr.AddReference("System.Windows.Forms")
        from System.Windows.Forms import MethodInvoker
        form = BrowserView.instances.get(window.uid) if window else None
        if form:
            form.Invoke(MethodInvoker(lambda: form.Close()))
    except Exception:
        pass

    code = code_container.get("code", "")
    if not code:
        logging.warning("[HuaweiChannel] 自动重登超时（未获取到授权码）")
        return None

    token = _exchange_code(code, code_verifier)
    if not token:
        logging.error("[HuaweiChannel] 自动重登换 token 失败")
        return None

    ga = _get_game_auth(token.get("access_token", ""))
    result = {
        "access_token": token.get("access_token", ""),
        "refresh_token": token.get("refresh_token", ""),
        "expires_in": token.get("expires_in", 0),
        "game_auth_sign": ga.get("gameAuthSign", "") if ga else "",
        "player_id": ga.get("playerId", "") if ga else "",
        "player_level": ga.get("playerLevel", "") if ga else "",
        "ts": ga.get("ts", "") if ga else "",
        "account": account,
        "password": password,
        "recorded_at": int(time.time()),
    }
    logging.info("[HuaweiChannel] 自动重登成功, player_id=%s", result["player_id"])
    return result


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
    def __init__(self, cache_dir: str = ""):
        self._window: webview.Window | None = None
        self._result: dict | None = None
        self._code_verifier: str = ""
        self._done = threading.Event()
        self._cache_dir: str = cache_dir  # 持久化缓存目录
        self._temp_dir: str = ""
        self._original_cache_dir: str = ""

    def login(self) -> dict | None:
        auth_url, self._code_verifier = _build_auth_url(HMS_CLIENT_ID, HMS_SCOPE)
        self._done.clear()
        code_container: dict = {}

        # —— _wf.cache_dir 操作：窗口使用持久化目录，cookie 跨会话保留 ——
        if self._cache_dir:
            self._temp_dir = self._cache_dir
        else:
            self._temp_dir = os.path.join(_HUAWEI_SESSIONS, f"rec_{uuid.uuid4().hex[:8]}")
        os.makedirs(self._temp_dir, exist_ok=True)
        self._original_cache_dir = _wf.cache_dir
        _wf.cache_dir = self._temp_dir
        logging.debug("[HuaweiChannel] 缓存目录: %s", self._temp_dir)

        # 提前下载图标，窗口创建后立即设置
        try:
            icon_bytes = requests.get("https://consumer.huawei.com/favicon.ico", timeout=5).content
        except Exception:
            icon_bytes = None

        try:
            self._window = webview.create_window("华为账号登录", auth_url, width=1050, height=810)
        finally:
            _wf.cache_dir = self._original_cache_dir

        if icon_bytes:
            from script.account.channel.ChannelUtils import _apply_icon_bytes
            _apply_icon_bytes(self._window, icon_bytes)

        def _run():
            time.sleep(1.5)  # 等 WebView2 初始化
            _add_navigation_handler(self._window, code_container)

            # 注入凭证捕获 JS，监听登录表单提交
            capture_injected = False

            for _ in range(300):
                if self._done.is_set():
                    return

                if not capture_injected:
                    try:
                        from webview.platforms.winforms import BrowserView
                        form = BrowserView.instances.get(self._window.uid) if self._window else None
                        if form:
                            form.webview.CoreWebView2.ExecuteScriptAsync(_CAPTURE_CREDS_JS)
                            capture_injected = True
                    except Exception:
                        pass

                if code_container.get("code"):
                    # 尝试读取捕获的华为账号密码
                    captured_account = ""
                    captured_pwd = ""
                    try:
                        from webview.platforms.winforms import BrowserView
                        form = BrowserView.instances.get(self._window.uid) if self._window else None
                        if form:
                            task = form.webview.CoreWebView2.ExecuteScriptAsync(_READ_CREDS_JS)
                            creds_json = str(task.Result) if task.Result else ""
                            if creds_json and creds_json.strip():
                                creds = json.loads(creds_json)
                                captured_account = creds.get("account", "")
                                captured_pwd = creds.get("pwd", "")
                                if captured_account:
                                    logging.info("[HuaweiChannel] 已捕获账号 %s", captured_account[:3] + "***")
                    except Exception as e:
                        logging.debug("[HuaweiChannel] 读取凭证失败: %s", e)

                    token = _exchange_code(code_container["code"], self._code_verifier)
                    if token:
                        # 调 getGameAuthSign 获取 gameAuthSign + playerId
                        ga = _get_game_auth(token.get("access_token", ""))
                        if ga:
                            token["_game_auth_sign"] = ga["gameAuthSign"]
                            token["_player_id"] = ga["playerId"]
                            token["_player_level"] = ga["playerLevel"]
                            token["_ts"] = ga["ts"]
                        token["_account"] = captured_account
                        token["_password"] = captured_pwd
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

    构建 SAUTH + extra_unisdk_data 用于 confirm_login。
    """
    import json as _json
    from script.account.channel.ChannelUtils import build_sauth, post_signed_data, FAKE_DEVICE

    ct = channel_auth.get("channel_type", "")
    access_token = channel_auth.get("access_token", "")
    refresh_token = channel_auth.get("refresh_token", "")

    # 获取 gameAuthSign（可能需要刷新或重新登录）
    ga = _get_game_auth(access_token) if access_token else None
    if not ga:
        logging.info("[HuaweiChannel] access_token 已过期，尝试自动重登...")
        account = channel_auth.get("account", "")
        password = channel_auth.get("password", "")
        cache_dir = channel_auth.get("cache_dir", "")
        relogin_result = _auto_relogin(HMS_CLIENT_ID, account, password, cache_dir)
        if relogin_result:
            # 将新 token 写回 channel_auth（下次 _persist_channel_auth 会持久化）
            for k in ("access_token", "refresh_token", "expires_in", "game_auth_sign",
                       "player_id", "player_level", "ts", "account", "password", "recorded_at"):
                if k in relogin_result:
                    channel_auth[k] = relogin_result[k]
            ga = _get_game_auth(relogin_result.get("access_token", ""))
        else:
            # 自动重登失败，尝试用 refresh_token 刷新（大概率也失败，没 client_secret）
            if refresh_token:
                new_at = _refresh_access_token(refresh_token)
                if new_at:
                    channel_auth["access_token"] = new_at
                    ga = _get_game_auth(new_at)

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
    """录制：打开华为 OAuth 窗口 → 返回 channel_auth（含持久化 cache_dir）"""
    cache_dir = os.path.join(_HUAWEI_SESSIONS, f"persist_{uuid.uuid4().hex[:8]}")
    login = HuaweiLogin(cache_dir=cache_dir)
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
        "account": result.get("_account", ""),
        "password": result.get("_password", ""),
        "recorded_at": int(time.time()),
        "cache_dir": cache_dir,
    }
