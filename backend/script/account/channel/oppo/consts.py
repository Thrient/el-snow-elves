"""OPPO 渠道常量 — 设备画像 + HTTP 头构建 + URL 编码工具"""
import base64
import json
import uuid
import os
from urllib.parse import quote
from script.config.Setting import APP_DATA

OPPO_WEBVIEW_UA = (
    "Mozilla/5.0 (Linux; Android 12.0.0; MI=8 Build/V417IR; wv) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/101.0.4951.61 "
    "Safari/537.36 DayNight/0 ColorOSVersion/ language/zh languageTag/zh-CN "
    "locale/zh_CN timeZone/Asia/Shanghai model/MI appPackageName/com.heytap.htms "
    "appVersion/2012701 foldMode/ largeScreen/false displayWidth/1600 displayHeight/864 "
    "realScreenWidth/1600 realScreenHeight/900 navHeight/72 isThird/1 X-BusinessSystem/other "
    "hardwareType/Mobile isMagicWindow/0 isTalkBackState/0 JSBridge/2 ClientType/UserCenter "
    "usercenter/2.1.27_efe796d_250819_outgoing_dom_f91d222_250808 WebFitMethod/1 switchHost/1 "
    "localstorageEncrypt/1 deepThemeColor/rgba(0,189,19,1.0) themeColor/rgba(0,189,19,1.0) "
    "isPanel/0 regionCode/CN Business/account"
)

OPPO_UC_CLIENT_DOMAIN = "https://muc.heytap.com/account-external-sdk/login"


def _get_or_create_oppo_guid_uuid() -> str:
    """持久化 GUID 的 uuid32 部分"""
    cache_path = os.path.join(APP_DATA, "oppo_guid_uuid.txt")
    try:
        if os.path.exists(cache_path):
            with open(cache_path) as f:
                v = f.read().strip()
                if v:
                    return v
    except Exception:
        pass
    new_uuid = uuid.uuid4().hex
    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w") as f:
            f.write(new_uuid)
    except Exception:
        pass
    return new_uuid


_GUID_UUID = _get_or_create_oppo_guid_uuid()
PKG_HOST = "com.heytap.htms"
GUID = f"{PKG_HOST}{_GUID_UUID}"


def _json_compact(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def url_encode_json(obj) -> str:
    return quote(_json_compact(obj), safe="")


def base64_encode_json(obj) -> str:
    return base64.b64encode(_json_compact(obj).encode()).decode()


def build_vip_header_json() -> dict:
    """复刻 OPPO Heytap 客户端的 HTTP 请求头"""
    raw_device = {"wd": 1600, "ht": 900, "devicetype": "Mobile"}
    raw_app = {
        "ucVersion": 0, "ucPackage": "", "acVersion": 200202,
        "acPackage": "com.oplus.account.open.sdk", "payVersion": 0,
        "appPackage": PKG_HOST, "deviceId": "", "appVersion": 2012701,
        "instantVersion": "", "hostPackage": PKG_HOST, "hostVersion": 2012701,
        "fromHT": "true", "overseaClient": "false", "foldMode": "",
    }
    raw_context = {"country": "CN", "maskRegion": "CN", "timeZone": "Asia/Shanghai", "locale": "zh_CN"}
    raw_sdk = {"sdkName": "UCBasic", "sdkBuildTime": "2024-01-16 14:58:22", "sdkVersionName": "2.0.8", "headerRevisedVersion": 1}
    raw_sys = {
        "romVersion": "0", "osVersion": "12.0.0", "androidVersion": "31",
        "osVersionCode": "31", "osBuildTime": 1752315442000, "uid": "0",
        "utype": "P", "betaEnv": False, "rpname": "dipper", "rotaver": "0",
        "guid": GUID,
    }
    raw_system = {"uid": "0", "usn": "", "utype": "P", "rpname": "dipper", "rotaver": "0"}
    raw_device_info = {"model": "MI", "ht": 900, "wd": 1600, "brand": "Xiaomi", "hardwareType": "Mobile", "nfc": False, "lsd": False}
    safety = {"imei": "", "imei1": "", "mac": "", "serialNum": "", "serial": "", "wifissid": "", "hasPermission": False, "deviceName": "", "marketName": ""}
    safety_json = _json_compact(safety)

    return {
        "Ext-App": f"/2012701/{PKG_HOST}",
        "Ext-Instant-Version": "",
        "Ext-Mobile": "///1/CN",
        "Ext-System": "MI/12.0.0/2/Xiaomi//CHINA+MOBILE/200202/",
        "X-APP": url_encode_json(raw_app),
        "X-BIZ-PACKAGE": PKG_HOST,
        "X-BIZ-VERSION": "2.1.27_efe796d_250819_outgoing_dom",
        "X-BusinessSystem": "other",
        "X-Client-Country": "CN",
        "X-Client-Device": "",
        "X-Client-GUID": GUID,
        "X-Client-HTOSVersion": "0",
        "X-Client-Locale": "zh_CN",
        "X-Client-Timezone": "Asia/Shanghai",
        "X-Client-package": "com.oplus.account.open.sdk",
        "X-Context": url_encode_json(raw_context),
        "X-Device": base64_encode_json(raw_device),
        "X-Device-Info": url_encode_json(raw_device_info),
        "X-From-HT": "true",
        "X-Op-Upgrade": "true",
        "X-SDK": url_encode_json(raw_sdk),
        "X-SDK-TYPE": "open",
        "X-SDK-VERSION": "2.2.2",
        "X-Safety": safety_json,
        "X-Security": safety_json,
        "X-Sys": url_encode_json(raw_sys),
        "X-Sys-TalkBackState": "false",
        "X-System": base64_encode_json(raw_system),
        "accept-language": "zh-CN",
    }
