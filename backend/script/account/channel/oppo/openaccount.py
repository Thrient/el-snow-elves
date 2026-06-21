"""OPPO Open Account — encrypted API client.

Merged from idv-login/src/channelHandler/oppoOpenAccount/:
  crypto.py (AES-CTR, RSA, SecurityKey)
  sign.py   (MD5-based request signing)
  envinfo.py (environment info builders)
  client.py (OppoSecureSession, OppoOpenAccountClient)
  models.py (AuthorizeRequest, RefreshRequest — inlined)

Exports: SecurityKey, OppoSecureSession, OppoOpenAccountClient, sign_request
"""
# ============================================================================
# SECTION 1: crypto — AES-CTR + RSA encryption
# ============================================================================
import base64
import hashlib
import json
import logging
import time
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

import requests
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.Hash import MD5, SHA1, SHA256
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Signature import pkcs1_15

from .consts import GUID, build_vip_header_json

_log = logging.getLogger(__name__)

OPPO_PROTOCOL_VERSION = "3.0"

OPPO_RSA_PUBLIC_KEY_B64 = (
    "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDpgSW5VkZ6/xvh+wMXezrOokNdiupu"
    "vuMj4RVJy44byWDupl4H37z907A26RVdFzMeyLUQB4rsDIaXdxCODlljWW+/K96uF5"
    "MsDtOFUBw7VlOclIjcYTv/YDQEul8JoXoOuy1Yf3b5sbTpTuVTcl97tAuLJ8PoGe2K"
    "7N3B1eUQqQIDAQAB"
)


def _pem_from_spki_b64(spki_b64: str) -> bytes:
    der = base64.b64decode(spki_b64)
    b64 = base64.encodebytes(der).replace(b"\n", b"")
    lines = [b64[i : i + 64] for i in range(0, len(b64), 64)]
    return b"-----BEGIN PUBLIC KEY-----\n" + b"\n".join(lines) + b"\n-----END PUBLIC KEY-----\n"


_RSA_PUB = RSA.import_key(_pem_from_spki_b64(OPPO_RSA_PUBLIC_KEY_B64))


def b64_urlsafe_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii")


def b64_urlsafe_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s.encode("ascii"))


def b64_std_encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64_std_decode(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))


def aes_ctr_encrypt_to_b64(plaintext: str, aes_key_b64_urlsafe: str, iv: bytes) -> str:
    """AES-CTR encrypt, Java-compatible: key is the raw bytes of the base64 string."""
    key = aes_key_b64_urlsafe.encode("ascii")
    initial_value = int.from_bytes(iv, byteorder="big", signed=False)
    cipher = AES.new(key, AES.MODE_CTR, nonce=b"", initial_value=initial_value)
    ct = cipher.encrypt(plaintext.encode("utf-8"))
    return b64_std_encode(ct)


def aes_ctr_decrypt_from_b64(ciphertext_b64_std: str, aes_key_b64_urlsafe: str, iv: bytes) -> str:
    key = aes_key_b64_urlsafe.encode("ascii")
    initial_value = int.from_bytes(iv, byteorder="big", signed=False)
    cipher = AES.new(key, AES.MODE_CTR, nonce=b"", initial_value=initial_value)
    pt = cipher.decrypt(b64_std_decode(ciphertext_b64_std))
    return pt.decode("utf-8", errors="replace")


def rsa_encrypt_b64(plaintext: str, pubkey: RSA.RsaKey = _RSA_PUB) -> str:
    cipher = PKCS1_v1_5.new(pubkey)
    ct = cipher.encrypt(plaintext.encode("utf-8"))
    return b64_std_encode(ct)


def verify_rsa_signature_of_text(text: str, signature_b64: str, pubkey: RSA.RsaKey = _RSA_PUB) -> bool:
    """RsaCoder.doCheck compatible: tries MD5/SHA1/SHA256."""
    sig = b64_std_decode(signature_b64)
    data = text.encode("utf-8")
    for h in (MD5.new(data), SHA1.new(data), SHA256.new(data)):
        try:
            pkcs1_15.new(pubkey).verify(h, sig)
            return True
        except Exception:
            pass
    return False


@dataclass
class SecurityKey:
    """Per-request AES key + IV, RSA-encrypted for OPPO servers."""

    aes_key_b64_urlsafe: str
    iv: bytes
    iv_b64_urlsafe: str
    rsa_b64_std: str
    session_ticket: str = ""
    header_signature_v1: str = ""  # raw X-Security
    header_signature_v2: str = ""  # url-encoded X-Security

    @staticmethod
    def generate(pubkey: RSA.RsaKey = _RSA_PUB) -> "SecurityKey":
        iv = get_random_bytes(16)
        iv_str = b64_urlsafe_encode(iv)
        aes_key_raw = get_random_bytes(16)
        aes_key_str = b64_urlsafe_encode(aes_key_raw)
        rsa_str = rsa_encrypt_b64(aes_key_str, pubkey)
        return SecurityKey(
            aes_key_b64_urlsafe=aes_key_str,
            iv=iv,
            iv_b64_urlsafe=iv_str,
            rsa_b64_std=rsa_str,
        )

    def encrypt(self, plaintext: str) -> str:
        return aes_ctr_encrypt_to_b64(plaintext, self.aes_key_b64_urlsafe, self.iv)

    def decrypt(self, ciphertext_b64_std: str) -> str:
        return aes_ctr_decrypt_from_b64(ciphertext_b64_std, self.aes_key_b64_urlsafe, self.iv)


def build_security_headers(
    security_key: SecurityKey,
    device_security_header_plain: str,
    xor_key_name: str = "key",
) -> Dict[str, str]:
    """Replicate SecurityRequestInterceptor.Header.newHeader."""
    x_security = security_key.encrypt(device_security_header_plain)
    security_key.header_signature_v1 = x_security

    headers: Dict[str, str] = {
        "X-Protocol-Version": OPPO_PROTOCOL_VERSION,
        "X-Protocol-Ver": OPPO_PROTOCOL_VERSION,
        "Accept": "application/encrypted-json",
        "X-Security": x_security,
        "X-Key": security_key.rsa_b64_std,
        "X-I-V": security_key.iv_b64_urlsafe,
    }
    if security_key.session_ticket:
        headers["X-Session-Ticket"] = security_key.session_ticket

    protocol_obj = {
        xor_key_name: security_key.rsa_b64_std,
        "iv": security_key.iv_b64_urlsafe,
        "sessionTicket": security_key.session_ticket,
    }
    protocol_json = json.dumps(protocol_obj, ensure_ascii=False, separators=(",", ":"))
    headers["X-Protocol"] = urllib.parse.quote(protocol_json, safe="")

    x_safety = urllib.parse.quote(x_security, safe="")
    security_key.header_signature_v2 = x_safety
    headers["X-Safety"] = x_safety

    return headers


# ============================================================================
# SECTION 2: sign — MD5-based request signing
# ============================================================================

BIZK_SECRET_KEY = "6CyfIPKEDKF0RIR3fdtFsQ=="


def _iter_fields(obj: Any):
    """Iterate (name, value) from dataclass, dict, or __dict__."""
    from dataclasses import asdict, is_dataclass

    if is_dataclass(obj):
        yield from asdict(obj).items()
    elif isinstance(obj, dict):
        yield from obj.items()
    elif hasattr(obj, "__dict__"):
        yield from vars(obj).items()


def _java_value_to_string(value: Any) -> str:
    """Java Object.toString() semantics for sign source building."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, dict):
        items = []
        for k in sorted(value.keys(), key=lambda x: str(x)):
            items.append(f"{_java_value_to_string(k)}={_java_value_to_string(value[k])}")
        return "{" + ", ".join(items) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_java_value_to_string(v) for v in value) + "]"
    return str(value)


def _build_sign_source(obj: Any, exclude_field: Optional[str] = None) -> Optional[str]:
    """Replicate AcSignHelper.signWithAnnotation."""
    parts = []
    for name, value in _iter_fields(obj):
        if name in {"sign", exclude_field}:
            continue
        if value is None:
            continue
        if isinstance(value, str) and (value == "" or value.strip() == ""):
            continue
        if isinstance(value, (list, tuple)) and len(value) == 0:
            continue
        if isinstance(value, dict) and len(value) == 0:
            continue
        parts.append(f"{name}={_java_value_to_string(value)}&")
    if not parts:
        return None
    parts.sort(key=lambda s: s.lower())
    return "".join(parts)


def _md5_hex(s: str) -> str:
    return hashlib.md5((s or "").encode("utf-8")).hexdigest()


def _sign_add_key(source: str) -> str:
    if source and not source.endswith("&"):
        source = source + "&"
    return source + f"key={BIZK_SECRET_KEY}"


def sign_request(obj: Any, exclude_field: Optional[str] = None) -> str:
    """MD5 sign a dataclass/dict payload with BIZK_SECRET_KEY."""
    src = _build_sign_source(obj, exclude_field=exclude_field) or ""
    return _md5_hex(_sign_add_key(src))


# ============================================================================
# SECTION 3: envinfo — environment info builders
# ============================================================================

# Hardcoded device defaults (matching consts.py + idv-login OppoDeviceProfile defaults)
_DEVICE_DEFAULTS = {
    "sys_os_version": "V10.0.11.0",
    "rom_build_display": "V417IR release-keys",
    "android_version": "31",
    "sec_version": "2018-10-01",
    "bootloader_version": "unknown",
    "build_id": "1.0.0.0",
    "model": "MI",
    "rpname": "dipper",
    "brand": "Xiaomi",
    "hw_name": "Xiaomi",
    "screen_wd": 1600,
    "screen_ht": 900,
    "screen_dpi": 240,
    "cpu_id": (
        "fp asimd aes pmull sha1 sha2 crc32 atomics,"
        "ARMv8 processor rev 1 (aarch64),"
        "8,placeholder,null"
    ),
    "cpu_type": "arm64-v8a,armeabi-v7a,armeabi",
    "bt_name": "NOP",
    "battery_status": "charging",
    "battery_present": True,
    "battery_health": 2,
    "other_sdk_version": "1.1.0",
}

DEVICE_SECURITY_HEADER_OBJ: Dict[str, Any] = {
    "imei": "",
    "imei1": "",
    "mac": "",
    "serialNum": "",
    "serial": "",
    "wifissid": "",
    "hasPermission": False,
    "deviceName": "",
    "marketName": "",
}


def build_device_security_header_plain() -> str:
    """DeviceSecurityHeader.getDeviceSecurityHeader plaintext (mockNative.js — all empty)."""
    return json.dumps(DEVICE_SECURITY_HEADER_OBJ, ensure_ascii=False, separators=(",", ":"))


def build_env_param_minimal() -> str:
    """Build envParam (percent-encoded JSON) with hardcoded device defaults."""
    now_ms = int(time.time() * 1000)
    uptime_ms = int(time.monotonic() * 1000)

    payload: Dict[str, Any] = {
        "SysInfo": {
            "osVersion": _DEVICE_DEFAULTS["sys_os_version"],
            "romVersion": _DEVICE_DEFAULTS["rom_build_display"],
            "apiVersion": int(_DEVICE_DEFAULTS["android_version"]),
            "secVersion": _DEVICE_DEFAULTS["sec_version"],
            "bootloaderVersion": _DEVICE_DEFAULTS["bootloader_version"],
            "usbStatus": False,
            "curTime": now_ms,
            "upTime": uptime_ms,
            "activeTime": uptime_ms,
        },
        "DevInfo": {
            "buildID": _DEVICE_DEFAULTS["build_id"],
            "model": _DEVICE_DEFAULTS["model"],
            "product": _DEVICE_DEFAULTS["rpname"],
            "brand": _DEVICE_DEFAULTS["brand"],
            "hwName": _DEVICE_DEFAULTS["hw_name"],
            "platform": "phone",
        },
        "NetInfo": {
            "networkType": "",
            "cellIP": "",
            "isVpn": False,
            "vpnIP": "",
        },
        "EnvInfo": {
            "isRoot": False,
            "isVirtual": False,
            "vmApp": "",
            "hookFrame": False,
            "hookMethods": False,
            "isFileExist": False,
            "OSisDebuggable": False,
            "roSecure": 1,
        },
        "HardInfo": {
            "screenSize": f"{_DEVICE_DEFAULTS['screen_wd']},{_DEVICE_DEFAULTS['screen_ht']}",
            "screenDpi": _DEVICE_DEFAULTS["screen_dpi"],
            "cpuID": _DEVICE_DEFAULTS["cpu_id"],
            "cpuType": _DEVICE_DEFAULTS["cpu_type"],
            "btName": _DEVICE_DEFAULTS["bt_name"],
            "btMac": None,
        },
        "OtherInfo": {
            "batteryStatus": _DEVICE_DEFAULTS["battery_status"],
            "batteryPresent": _DEVICE_DEFAULTS["battery_present"],
            "batteryHealth": _DEVICE_DEFAULTS["battery_health"],
            "sdkVersion": _DEVICE_DEFAULTS["other_sdk_version"],
        },
    }

    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return urllib.parse.quote(raw, safe="")


def build_env_info_pkg(
    app_id: str,
    device_id: str,
    pkg_name: str,
    pkg_name_sign: str,
    env_param: Optional[str] = None,
) -> str:
    obj = {
        "appId": app_id,
        "deviceId": device_id or "",
        "envParam": env_param or "",
        "pkgName": pkg_name,
        "pkgNameSign": pkg_name_sign,
    }
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


# ============================================================================
# SECTION 4: models — inlined AuthorizeRequest / RefreshRequest helpers
# ============================================================================

ACCOUNT_BIZK = "3cd48b0c781835478b0a1783a9eff0c9"


def _build_authorize_payload(account_id_token: str, env_info: str, biz_app_key: str) -> Dict[str, Any]:
    """Inline AuthorizeRequest with MD5 sign."""
    timestamp = int(time.time() * 1000)
    d = {
        "bizk": ACCOUNT_BIZK,
        "timestamp": timestamp,
        "envInfo": env_info,
        "accountIdToken": account_id_token,
        "bizAppKey": biz_app_key,
        "sign": "",
    }
    d["sign"] = sign_request(d)
    return d


def _build_refresh_payload(
    refresh_token: str,
    ssoid: str,
    primary_token: str,
    refresh_ticket: str,
    access_token: str,
    env_info: str,
    package_sign_map: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Inline RefreshRequest with MD5 sign."""
    timestamp = int(time.time() * 1000)
    d = {
        "bizk": ACCOUNT_BIZK,
        "timestamp": timestamp,
        "refreshToken": refresh_token,
        "ssoid": ssoid,
        "primaryToken": primary_token,
        "packageSignMap": package_sign_map,
        "refreshTicket": refresh_ticket,
        "envInfo": env_info,
        "accessToken": access_token,
        "sign": "",
    }
    d["sign"] = sign_request(d)
    return d


# ============================================================================
# SECTION 5: OppoSecureSession + OppoOpenAccountClient
# ============================================================================

DEFAULT_BASE_URL = "https://uc-client-cn.heytapmobi.com/"

# Default constants matching the device profile in consts.py
DEFAULT_DEVICE_ID = ""
DEFAULT_APP_ID = "31288517"
DEFAULT_PKG_NAME = "com.oplus.account.open.sdk"
DEFAULT_PKG_NAME_SIGN = "00e7ec6745698936072925f64fc2a3e8"
DEFAULT_BIZ_APP_KEY = "cd73441423364d90a6ac6fe2bc727542"


class OppoSecureSession:
    """Encrypted HTTP session for OPPO Heytap account API (SecurityRequestInterceptor equivalent)."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        session_ticket: str = "",
        device_security_header_plain: str = "",
    ):
        self.base_url = base_url
        self.session_ticket = session_ticket
        self.http = requests.Session()
        self.http.trust_env = False
        if device_security_header_plain:
            self._device_security_header_plain = device_security_header_plain
        else:
            self._device_security_header_plain = build_device_security_header_plain()

    def _build_common_headers(self) -> Dict[str, str]:
        h = build_vip_header_json()
        h["is_open_account"] = "true"
        return h

    def _build_plain_headers(self) -> Dict[str, str]:
        h = self._build_common_headers()
        h["Accept"] = "application/json"
        h["X-Protocol-Ver"] = OPPO_PROTOCOL_VERSION
        h["X-Protocol-Version"] = OPPO_PROTOCOL_VERSION
        h["Content-Type"] = "application/json; charset=UTF-8"
        for k in ("X-Key", "X-I-V", "X-Security", "X-Safety", "X-Protocol", "X-Session-Ticket"):
            h.pop(k, None)
        return h

    def post_plain_json(self, path: str, payload_obj: Dict[str, Any]) -> Dict[str, Any]:
        url = self.base_url.rstrip("/") + "/" + path.lstrip("/")
        body_json = json.dumps(payload_obj, ensure_ascii=False, separators=(",", ":"))
        headers = self._build_plain_headers()
        r = self.http.post(url, data=body_json, headers=headers, verify=True)
        try:
            return r.json()
        except Exception:
            return {"success": False, "http": r.status_code, "raw": r.text}

    def post_json(
        self,
        path: str,
        payload_obj: Dict[str, Any],
        *,
        allow_plain_fallback: bool = True,
    ) -> Dict[str, Any]:
        """Send encrypted JSON POST. On 222 (downgrade) retries plaintext if allowed."""
        url = self.base_url.rstrip("/") + "/" + path.lstrip("/")

        security_key = SecurityKey.generate()
        security_key.session_ticket = self.session_ticket

        sec_headers = build_security_headers(security_key, self._device_security_header_plain, xor_key_name="key")

        body_json = json.dumps(payload_obj, ensure_ascii=False, separators=(",", ":"))
        enc_body = security_key.encrypt(body_json)

        headers = self._build_common_headers()
        headers.update(sec_headers)
        headers["Content-Type"] = "application/encrypted-json; charset=UTF-8"

        r = self.http.post(url, data=enc_body, headers=headers, verify=True)
        text = r.text

        new_ticket = r.headers.get("X-Session-Ticket")
        if isinstance(new_ticket, str) and new_ticket:
            self.session_ticket = new_ticket

        # Success: AES-decrypt body
        if r.status_code != 222 and r.ok:
            try:
                dec = security_key.decrypt(text)
                return json.loads(dec)
            except Exception as e:
                raise RuntimeError(f"Decrypt/parse failed: {e}; raw={text[:200]}")

        # Downgrade/signature check: status=222
        if r.status_code == 222:
            sig = r.headers.get("X-Signature", "")
            if not sig:
                raise RuntimeError("Server returned 222 without X-Signature")

            md5_v1 = _md5_hex(security_key.header_signature_v1)
            md5_v2 = _md5_hex(security_key.header_signature_v2)
            if not (
                verify_rsa_signature_of_text(md5_v1, sig)
                or verify_rsa_signature_of_text(md5_v2, sig)
            ):
                raise RuntimeError("222 response signature verification failed")

            if allow_plain_fallback:
                _log.info("Received 222 (downgrade), retrying with plaintext")
                return self.post_plain_json(path, payload_obj)

            return {"success": False, "code": 222, "message": "response decrypt downgrade", "raw": text}

        # Other HTTP errors
        try:
            return r.json()
        except Exception:
            return {"success": False, "http": r.status_code, "raw": text}


class OppoOpenAccountClient:
    """OPPO Heytap account API client with encrypted transport."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        session_ticket: str = "",
        device_id: str = DEFAULT_DEVICE_ID,
    ):
        self.device_id = device_id
        self.session = OppoSecureSession(base_url=base_url, session_ticket=session_ticket)

    def authorize(
        self,
        account_id_token: str,
        biz_app_key: str = DEFAULT_BIZ_APP_KEY,
        app_id: str = DEFAULT_APP_ID,
        device_id: str = "",
        pkg_name: str = DEFAULT_PKG_NAME,
        pkg_name_sign: str = DEFAULT_PKG_NAME_SIGN,
    ) -> Dict[str, Any]:
        if not device_id:
            device_id = self.device_id
        env_param = build_env_param_minimal()
        env_info = build_env_info_pkg(app_id, device_id, pkg_name, pkg_name_sign, env_param)
        payload = _build_authorize_payload(account_id_token, env_info, biz_app_key)
        return self.session.post_json("api/authorize", payload)

    def token_refresh(
        self,
        refresh_token: str,
        ssoid: str,
        primary_token: str,
        refresh_ticket: str,
        access_token: str,
        secondary_token_map: Optional[Dict[str, str]] = None,
        app_id: str = DEFAULT_APP_ID,
        device_id: str = "",
        pkg_name: str = DEFAULT_PKG_NAME,
        pkg_name_sign: str = DEFAULT_PKG_NAME_SIGN,
        host_package: str = "com.heytap.htms",
    ) -> Dict[str, Any]:
        if not device_id:
            device_id = self.device_id
        env_param = build_env_param_minimal()
        env_info = build_env_info_pkg(app_id, device_id, pkg_name, pkg_name_sign, env_param)

        package_sign_map = None
        if secondary_token_map and host_package in secondary_token_map:
            package_sign_map = {host_package: secondary_token_map[host_package]}

        payload = _build_refresh_payload(
            refresh_token=refresh_token,
            ssoid=ssoid,
            primary_token=primary_token,
            refresh_ticket=refresh_ticket,
            access_token=access_token,
            env_info=env_info,
            package_sign_map=package_sign_map,
        )
        return self.session.post_json("api/token/refresh", payload)
