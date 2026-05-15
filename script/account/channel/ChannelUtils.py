"""渠道服通用工具 — SAUTH 构造 + 签名发送"""

import base64
import json
import random
import string
import hmac
import hashlib
import logging

import requests

# 设备指纹 — 持久化避免每次变更
import os as _os

_DEVICE_FILE = _os.path.join(_os.path.dirname(__file__), "_fake_device.json")

def _load_device() -> dict:
    try:
        with open(_DEVICE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
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


FAKE_DEVICE = _load_device()

# 默认 log_key（一梦江湖 h42，来自 idv-login cloudRes）
DEFAULT_LOG_KEY = "yi8_cXKEm4Pe2XYL3E4GjjD9MVtYRuGy"


def get_sign_src(method: str, url: str, data: str) -> str:
    replaced = url.replace("://", "")
    path = ""
    idx = replaced.find("/")
    if idx != -1:
        path = replaced[idx:]
    return method.upper() + path + data


def calc_sign(url: str, method: str, data: str, key: str) -> str:
    src = get_sign_src(method, url, data)
    return hmac.new(key.encode(), src.encode(), hashlib.sha256).hexdigest()


def _get_my_ip() -> str:
    try:
        return requests.get("https://who.nie.netease.com/", verify=False, timeout=5).json().get("ip", "127.0.0.1")
    except Exception:
        return "127.0.0.1"


def build_sauth(
    login_channel: str,
    app_channel: str,
    uid: str,
    session: str,
    game_id: str,
    sdk_version: str = "6.1.0.301",
    custom_data: dict | None = None,
) -> dict:
    """构造 UniSDK SAUTH 数据"""
    device = dict(FAKE_DEVICE)
    ip = _get_my_ip()
    data = {
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
        "aim_info": f'{{"tz":"+0800","tzid":"Asia/Shanghai","aim":"{ip}","country":"CN"}}',
        "source_app_channel": app_channel,
        "source_platform": "ad",
        "client_login_sn": "".join(random.choices(string.hexdigits, k=16)),
        "step": "".join(random.choices(string.digits, k=10)),
        "step2": "".join(random.choices(string.digits, k=9)),
        "hostid": 0,
        "sdklog": json.dumps(device),
    }
    if custom_data:
        data.update(custom_data)
    return data


class _CustomEncoder(json.JSONEncoder):
    """idv-login 风格的 JSON 编码器：转义 / 为 \\/"""
    def encode(self, obj):
        return super().encode(obj).replace('/', '\\/')


def post_signed_data(data: dict, game_id: str, log_key: str = DEFAULT_LOG_KEY,
                     need_custom_encode: bool = False) -> dict:
    """签名并 POST 到网易 UniSDK 端点"""
    url = f"https://mgbsdk.matrix.netease.com/{game_id}/sdk/uni_sauth"
    if need_custom_encode:
        body = json.dumps(data, cls=_CustomEncoder)
    else:
        body = json.dumps(data)
    headers = {
        "X-Client-Sign": calc_sign(url, "POST", body, log_key),
        "Content-Type": "application/json",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; M2102K1AC Build/V417IR)",
    }
    r = requests.post(url, data=body, headers=headers, timeout=15)
    result = r.json()
    logging.info(f"[ChannelUtils] uni_sauth code={result.get('code')} msg={result.get('msg', result.get('reason', ''))}")
    logging.debug(f"[ChannelUtils] uni_sauth keys: {list(result.keys())} full={json.dumps(result, ensure_ascii=False)[:300]}")
    if result.get('code') != 0:
        logging.error(f"[ChannelUtils] uni_sauth failed code={result.get('code')} subcode={result.get('subcode', 'N/A')} status={result.get('status', 'N/A')}")
        logging.debug(f"[ChannelUtils] uni_sauth body login_channel={data.get('login_channel')} sdkuid={data.get('sdkuid')} sessionid={data.get('sessionid')[:20] if data.get('sessionid') else 'N/A'}...")
    return result


def confirm_login(game_id: str, process_id: str, uni_data: dict, channel_data: dict | None = None) -> bool:
    """调用网易 qrcode/confirm_login — 对齐 idv-login 格式"""
    # 用真实 IP 避免 hosts 劫持
    url = "https://42.186.193.21/mpay/api/qrcode/confirm_login"
    cd = channel_data or {}
    fd = dict(FAKE_DEVICE)

    # 构建 extra_unisdk_data（SAUTH_STR + SAUTH_JSON）
    unisdk_json = uni_data.get("unisdk_login_json", "")
    extra = {}
    if unisdk_json:
        try:
            unisdk_obj = json.loads(base64.b64decode(unisdk_json))
        except Exception:
            unisdk_obj = {}
        str_data = dict(unisdk_obj)
        str_data["username"] = cd.get("uname", "")
        sauth_str = base64.b64encode("&".join(f"{k}={v}" for k, v in str_data.items()).encode()).decode()
        sauth_json = base64.b64encode(json.dumps(unisdk_obj).encode()).decode()
        extra = {"SAUTH_STR": sauth_str, "SAUTH_JSON": sauth_json}

    body = {
        "game_id": game_id,
        "uuid": process_id,
        "user_id": cd.get("user_id", ""),
        "token": cd.get("token", ""),
        "login_channel": cd.get("login_channel", ""),
        "app_channel": cd.get("app_channel", ""),
        "pay_channel": cd.get("pay_channel", ""),
        "udid": fd["udid"],
        "sdk_version": "6.1.0.301",
        "jf_game_id": game_id.split("-")[-1] if "-" in game_id else game_id,
        "gv": "157",
        "gvn": "1.5.80",
        "cv": "a1.5.0",
        "extra_data": "",
        "extra_unisdk_data": json.dumps(extra) if extra else "",
    }
    body_str = "&".join(f"{k}={v}" for k, v in body.items())
    logging.debug(f"[ChannelUtils] confirm_login extra_unisdk_data={body.get('extra_unisdk_data', 'MISSING')[:120]}")
    logging.debug(f"[ChannelUtils] confirm_login body: {body_str[:500]}")
    try:
        r = requests.post(
            url, data=body_str,
            headers={"Content-Type": "application/x-www-form-urlencoded", "Host": "service.mkey.163.com"},
            timeout=15, verify=False,
        )
        result = r.json()
        code = result.get("code")
        ok = code is None or code == 0
        logging.info(f"[ChannelUtils] confirm_login: {'OK' if ok else 'FAIL'} code={code} status={r.status_code}")
        logging.debug(f"[ChannelUtils] confirm_login raw: {r.text[:300]}")
        return ok
    except Exception as e:
        logging.error(f"[ChannelUtils] confirm_login 失败: {e}")
        return False


def get_huawei_game_auth(access_token: str, app_id: str = "100112247") -> dict | None:
    """回放时刷新 gameAuthSign"""
    try:
        body = {
            "gamePopTime": 0, "idType": 2,
            "hmsSdkVersionCode": 60100302, "hmsSdkVersionName": "6.1.0.302",
            "hmsApkVersionName": "6.14.0.302", "hmsApkVersionCode": 61400302,
            "kitver": 61400300, "thirdAppVersion": "1.5.99",
            "clientPackage": "com.huawei.gamebox", "locale": "zh_CN",
            "timeZone": "Asia/Shanghai", "serviceType": 47, "odm": 0,
            "countryCode": "CN", "deviceIdType": 4,
            "method": "client.hms.gs.getGameAuthSign",
            "extraBody": f'json={{"appId":"{app_id}"}}',
            "accessToken": access_token,
        }
        resp = requests.post(
            "https://jgw-drcn.jos.dbankcloud.cn/gameservice/api/gbClientApi",
            headers={"User-Agent": "com.huawei.hms.game/6.14.0.300 (Linux; Android 12; M2102K1AC) RestClient/7.0.6.300", "Content-Type": "application/x-www-form-urlencoded"},
            data=body, timeout=15,
        )
        result = resp.json()
        gs = result.get("gameAuthSign")
        pid = result.get("playerId")
        if gs and pid:
            logging.info(f"[ChannelUtils] getGameAuthSign 刷新成功, playerId={pid}")
            return {"gameAuthSign": gs, "playerId": str(pid), "playerLevel": str(result.get("playerLevel", "")), "ts": str(result.get("ts", ""))}
        logging.error(f"[ChannelUtils] getGameAuthSign 失败: {result}")
    except Exception as e:
        logging.error(f"[ChannelUtils] getGameAuthSign 异常: {e}")
    return None
