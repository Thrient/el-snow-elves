"""网易 UniSDK 渠道服通用工具 — SAUTH 构造 + 签名发送

实现网易 mgbsdk.matrix.netease.com 的 uni_sauth 协议：
  1. 构造 SAUTH JSON（设备指纹 + 登录凭证 + 随机字段）
  2. HMAC-SHA256 签名（METHOD + path + body）
  3. POST 到 uni_sauth 端点

协议参考：网易 UniSDK 公开 API 文档
"""

import hashlib
import hmac
import json
import logging
import os as _os
import random
import string

import requests

# ── 设备指纹（持久化，避免每次变更触发风控）──

_DEVICE_FILE = _os.path.join(_os.path.dirname(__file__), "_fake_device.json")


def _load_device() -> dict:
    """加载或生成持久化设备指纹"""
    try:
        with open(_DEVICE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        pass

    d = {
        "device_model": "M2102K1AC",
        "os_name": "android",
        "os_ver": "12",
        "udid": "".join(random.choices(string.hexdigits.lower(), k=16)),
        "app_ver": "157",
        "imei": "".join(random.choices(string.digits, k=15)),
        "country_code": "CN",
        "is_emulator": 0,
        "is_root": 0,
        "oaid": "",
    }
    try:
        with open(_DEVICE_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f)
    except Exception:
        pass
    return d


FAKE_DEVICE: dict = _load_device()

# 一梦江湖 (h42) 的 log_key，来自游戏资源文件
DEFAULT_LOG_KEY = "yi8_cXKEm4Pe2XYL3E4GjjD9MVtYRuGy"

# UniSDK SAUTH 端点
_UNI_SAUTH_URL = "https://mgbsdk.matrix.netease.com/{game_id}/sdk/uni_sauth"


# ── HMAC 签名 ──

def _hmac_sign(method: str, url: str, body: str, key: str) -> str:
    """计算 UniSDK 请求签名：HMAC-SHA256(METHOD + path + body, key)"""
    # 提取 path（去掉协议和 host）
    path = url[url.find("/", url.find("://") + 3):] if "://" in url else url
    src = method.upper() + path + body
    return hmac.new(key.encode(), src.encode(), hashlib.sha256).hexdigest()


def _get_my_ip() -> str:
    """获取本机出口 IP"""
    try:
        return requests.get(
            "https://who.nie.netease.com/", verify=False, timeout=5
        ).json().get("ip", "127.0.0.1")
    except Exception:
        return "127.0.0.1"


# ── 自定义 JSON 编码器（Vivo 等渠道需要 / 转义为 \/）──

class _CustomEncoder(json.JSONEncoder):
    r"""将 JSON 中的 / 转义为 \/，保证 HMAC 签名与服务端一致"""

    def encode(self, obj):
        return super().encode(obj).replace("/", "\\/")


# ── 公共 API ──

def build_sauth(
    login_channel: str,
    app_channel: str,
    uid: str,
    session: str,
    game_id: str,
    sdk_version: str = "6.1.0.301",
    custom_data: dict | None = None,
) -> dict:
    """构造 UniSDK SAUTH 请求体

    Args:
        login_channel: 登录渠道标识（如 nearme_vivo, huawei, bilibili_sdk）
        app_channel: 应用渠道标识
        uid: 渠道用户 ID（sdkuid）
        session: 登录凭证（sessionid / access_key / open_token）
        game_id: 游戏 ID（如 h42）
        sdk_version: UniSDK 版本号
        custom_data: 额外的顶层字段（如 realname）

    Returns:
        SAUTH JSON 字典，可直接传给 post_signed_data
    """
    device = dict(FAKE_DEVICE)
    ip = _get_my_ip()

    body = {
        "gameid": game_id,
        "login_channel": login_channel,
        "app_channel": app_channel,
        "platform": "ad",
        "sdkuid": uid,
        "udid": device["udid"],
        "sessionid": session,
        "sdk_version": sdk_version,
        "is_unisdk_guest": 0,
        "ip": ip,
        "aim_info": (
            '{"tz":"+0800","tzid":"Asia/Shanghai",'
            '"aim":"' + ip + '","country":"CN"}'
        ),
        "source_app_channel": app_channel,
        "source_platform": "ad",
        "client_login_sn": "".join(random.choices(string.hexdigits, k=16)),
        "step": "".join(random.choices(string.digits, k=10)),
        "step2": "".join(random.choices(string.digits, k=9)),
        "hostid": 0,
        "sdklog": json.dumps(device),
    }
    if custom_data:
        body.update(custom_data)
    return body


def post_signed_data(
    data: dict,
    game_id: str,
    log_key: str = DEFAULT_LOG_KEY,
    need_custom_encode: bool = False,
) -> dict:
    """对 SAUTH 数据签名并 POST 到网易 UniSDK 端点

    Args:
        data: build_sauth 返回的字典
        game_id: 游戏 ID
        log_key: HMAC 签名密钥
        need_custom_encode: 是否使用自定义编码器（Vivo 渠道需要）

    Returns:
        服务端响应的 JSON 字典，包含 unisdk_login_json 等字段
    """
    url = _UNI_SAUTH_URL.format(game_id=game_id)

    encoder = _CustomEncoder if need_custom_encode else None
    if encoder:
        body = json.dumps(data, cls=encoder)
    else:
        body = json.dumps(data)

    headers = {
        "X-Client-Sign": _hmac_sign("POST", url, body, log_key),
        "Content-Type": "application/json",
        "User-Agent": (
            "Dalvik/2.1.0 (Linux; U; Android 12; M2102K1AC Build/V417IR)"
        ),
    }
    r = requests.post(url, data=body, headers=headers, timeout=15)
    result = r.json()

    code = result.get("code")
    if code != 0:
        logging.error(
            "[ChannelUtils] uni_sauth failed code=%s subcode=%s",
            code, result.get("subcode", "N/A"),
        )
        logging.debug(
            "[ChannelUtils] uni_sauth req login_channel=%s sdkuid=%s",
            data.get("login_channel"), data.get("sdkuid"),
        )
        # 调试：打印请求体前 300 字符 + 签名
        logging.debug("[ChannelUtils] uni_sauth body[:300]=%s", body[:300])
        logging.debug("[ChannelUtils] uni_sauth sign=%s", headers.get("X-Client-Sign", "N/A"))
        logging.debug("[ChannelUtils] uni_sauth url=%s", url)
    else:
        logging.info("[ChannelUtils] uni_sauth OK")
    logging.debug(
        "[ChannelUtils] uni_sauth resp keys=%s",
        list(result.keys()),
    )
    return result


# ── 窗口图标 ──

# 各渠道官网 favicon
CHANNEL_ICONS: dict[str, str] = {
    "huawei": "https://consumer.huawei.com/favicon.ico",
    "vivo": "https://www.vivo.com/favicon.ico",
    "bilibili": "https://www.bilibili.com/favicon.ico",
    "nearme_vivo": "https://www.vivo.com/favicon.ico",
}


def set_window_icon(window, icon_url: str):
    """下载 favicon 并设置为 WebView2 窗口图标（需在窗口创建后调用）"""
    try:
        resp = requests.get(icon_url, timeout=10)
        resp.raise_for_status()
        _apply_icon_bytes(window, resp.content)
        logging.debug(f"[ChannelUtils] 窗口图标已设置: {icon_url}")
    except Exception as e:
        logging.warning(f"[ChannelUtils] 设置窗口图标失败: {e}")


def _apply_icon_bytes(window, icon_bytes: bytes):
    """将图标字节应用到窗口（内部方法，兼容 ico/png/jpg 等格式）"""
    import clr
    clr.AddReference("System.Drawing")
    clr.AddReference("System.Windows.Forms")
    from System.Drawing import Bitmap, Icon
    from System.Windows.Forms import MethodInvoker
    from System.IO import MemoryStream
    from webview.platforms.winforms import BrowserView

    stream = MemoryStream(icon_bytes)
    # 先用 Bitmap 加载（支持 png/jpg/bmp/ico），再转为 Icon
    bitmap = Bitmap(stream)
    icon = Icon.FromHandle(bitmap.GetHicon())
    stream.Close()

    form = BrowserView.instances.get(window.uid) if window else None
    if form:
        form.Invoke(MethodInvoker(lambda: setattr(form, "Icon", icon)))
