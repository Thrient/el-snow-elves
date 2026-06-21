from __future__ import annotations

import hashlib
import logging
import re
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, urlsplit, urlencode

import requests

from .proto.gamesdk_login_pb2 import GameAccountsDto
from .proto.gamesdk_latest_role_pb2 import LatestGameAccountsDto


BASE_URL = "https://isdk.heytapmobi.com"

RSA_BLOB_STORENEW = (
    "STORENEW"
    "MIICeAIBADANBgkqhkiG9w0BAQEFAASCAmIwggJeAgEAAoGBANYFY/UJGSzhIhpx6YM5KJ9yRHc7YeURxzb9tDvJvMfENHlnP3DtVkOIjERbpsSd76fjtZnMWY60TpGLGyrNkvuV40L15JQhHAo9yURpPQoI0eg3SLFmTEI/MUiPRCwfwYf2deqKKlsmMSysYYHX9JiGzQuWiYZaawxprSuiqDGvAgMBAAECgYEAtQ0QV00gGABISljNMy5aeDBBTSBWG2OjxJhxLRbndZM81OsMFysgC7dq+bUS6ke1YrDWgsoFhRxxTtx/2gDYciGp/c/h0Td5pGw7T9W6zo2xWI5oh1WyTnn0Xj17O9CmOk4fFDpJ6bapL+fyDy7gkEUChJ9+p66WSAlsfUhJ2TECQQD5sFWMGE2IiEuz4fIPaDrNSTHeFQQr/ZpZ7VzB2tcG7GyZRx5YORbZmX1jR7l3H4F98MgqCGs88w6FKnCpxDK3AkEA225CphAcfyiH0ShlZxEXBgIYt3V8nQuc/g2KJtiV6eeFkxmOMHbVTPGkARvt5VoPYEjwPTg43oqTDJVtlWagyQJBAOvEeJLno9aHNExvznyD4/pR4hec6qqLNgMyIYMfHCl6d3UodVvC1HO1/nMPl+4GvuRnxuoBtxj/PTe7AlUbYPMCQQDOkf4sVv58tqslO+I6JNyHy3F5RCELtuMUR6rG5x46FLqqwGQbO8ORq+m5IZHTV/Uhr4h6GXNwDQRh1EpVW0gBAkAp/v3tPI1riz6UuG0I6uf5er26yl5evPyPrjrD299L4Qy/1EIunayC7JYcSGlR01+EDYYgwUkec+QgrRC/NstV"
)


# ---------------------------------------------------------------------------
# sign2 helpers (merged from sign2.py)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Sign2Constants:
    oak: str = "a78b923440df20ce"
    salt: str = "a31cfccd172003e00f5ac59c95387a3b"
    rsa_blob: str = RSA_BLOB_STORENEW


def _md5_hex(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _split_path_query(url: str) -> Tuple[str, str]:
    parts = urlsplit(url)
    return parts.path or "", parts.query or ""


def _build_id_header_from_vaid(vaid: str) -> str:
    vaid = str(vaid or "").strip()
    return f"///{vaid}" if vaid else "///"


def build_sign(
    *,
    url: str,
    ocs: str,
    t_ms: int,
    device_id: str,
    constants: Sign2Constants = Sign2Constants(),
) -> str:
    path, query = _split_path_query(url)

    prefix = "".join(
        [
            constants.oak,
            constants.salt,
            ocs,
            str(t_ms),
            device_id,
            path,
            query,
        ]
    )

    prefix_with_len = prefix + str(len(prefix))
    final = prefix_with_len + constants.rsa_blob
    return _md5_hex(final)


def build_user_agent_encoded(
    *, brand: str, model: str, api: int, os_ver: str, sdkversion: int, ch: str
) -> str:
    raw = f"{brand}/{model}/{api}/{os_ver}/unknown/{sdkversion}/{ch}/{sdkversion}"
    return quote(raw, safe="")


def build_ocs_encoded(
    *, brand: str, model: str, api: int, os_ver: str, sdkversion: int, rom: str
) -> str:
    raw = f"{brand}/{model}/{api}/{os_ver}/unknown/{sdkversion}/{rom}/{sdkversion}"
    return quote(raw, safe="")


def build_headers(
    *,
    url: str,
    t_ms: int,
    user_agent: str,
    ocs: str,
    vaid: str,
    udid: str = "",
    oaid: str = "",
    mkmix_id: str = "",
    net: str = "wifi",
    country: str = "CN",
    sdkversion: int = 6070105,
    sdktype: str = "0",
    ch: str = "2401",
    oak: str = "a78b923440df20ce",
    locale: str = "-;cn",
    rom: str = "unknown",
    pid: str = "1001",
    appversion: str = "2.0.15",
    appid: str = "OPPO#1001#CN",
    client_time_ms: Optional[int] = None,
    h: Optional[str] = None,
    w: Optional[str] = None,
    rsq: Optional[int] = None,
    ext_original_url: bool = True,
) -> Dict[str, str]:
    device_id = _build_id_header_from_vaid(vaid)
    sign = build_sign(url=url, ocs=ocs, t_ms=t_ms, device_id=device_id)

    headers: Dict[str, str] = {
        "Accept": "application/x-protostuff; charset=UTF-8",
        "User-Agent": user_agent,
        "t": str(t_ms),
        "id": device_id,
        "udid": udid,
        "oaid": oaid,
        "vaid": vaid,
        "MkMixId": mkmix_id,
        "ocs": ocs,
        "ch": ch,
        "oak": oak,
        "locale": locale,
        "rom": rom,
        "pid": pid,
        "country": country,
        "sdkversion": str(sdkversion),
        "sdkType": sdktype,
        "net": net,
        "sign": sign,
        "appversion": appversion,
        "appid": appid,
        "ouidStatus": "false",
    }

    if client_time_ms is not None:
        headers["clientTime"] = str(client_time_ms)
        headers["ct"] = str(client_time_ms)

    if h is not None:
        headers["h"] = str(h)

    if w is not None:
        headers["w"] = str(w)

    if rsq is not None:
        headers["rsq"] = str(int(rsq))

    if ext_original_url:
        headers["extOriginalUrl"] = url

    return headers


# ---------------------------------------------------------------------------
# result DTOs
# ---------------------------------------------------------------------------

@dataclass
class GameSdkLoginResult:
    code: str = ""
    msg: str = ""
    ticket: str = ""
    trace_id: str = ""
    user_dto: Dict[str, Any] = None  # type: ignore[assignment]


@dataclass
class GameSdkResult:
    """Result for account-latest-role (formerly ResultDto)."""
    code: str = ""
    msg: str = ""


# ---------------------------------------------------------------------------
# Sign2Profile
# ---------------------------------------------------------------------------

_UUID_HEX_RE = re.compile(r"[0-9a-f]+")


def _normalize_uuid32(value: str) -> str:
    raw = (value or "").strip().lower()
    if not raw:
        return ""
    hex_only = "".join(_UUID_HEX_RE.findall(raw))
    if len(hex_only) < 32:
        return ""
    return hex_only[:32]


def _generate_vaid(device_uuid: str = "") -> str:
    prefix = time.strftime("%y%m%d%H", time.localtime())
    u32 = _normalize_uuid32(device_uuid)
    if not u32:
        u32 = uuid.uuid4().hex
    return prefix + u32


@dataclass
class Sign2Profile:
    brand: str = "Xiaomi"
    model: str = "M2102K1AC"
    api: int = 32
    os_ver: str = "12"
    rom: str = "unknown"

    sdkversion: int = 6070105
    ch: str = "2401"
    pid: str = "1001"
    locale: str = "-;cn"
    country: str = "CN"
    net: str = "wifi"
    sdktype: str = "0"

    appversion: str = "2.0.15"
    appid: str = "OPPO#1001#CN"

    udid: str = ""
    oaid: str = ""
    mkmix_id: str = ""
    vaid: str = ""

    screen_w: int = 1600
    screen_h: int = 900

    def user_agent(self) -> str:
        return build_user_agent_encoded(
            brand=self.brand,
            model=self.model,
            api=self.api,
            os_ver=self.os_ver,
            sdkversion=self.sdkversion,
            ch=self.ch,
        )

    def ocs(self) -> str:
        return build_ocs_encoded(
            brand=self.brand,
            model=self.model,
            api=self.api,
            os_ver=self.os_ver,
            sdkversion=self.sdkversion,
            rom=self.rom,
        )


# ---------------------------------------------------------------------------
# OppoGameSdkClient
# ---------------------------------------------------------------------------

class OppoGameSdkClient:
    """OPPO Game SDK client.

    GET /gamesdk/v2/user/login
    GET /gamesdk/v2/user/account-latest-role

    Returns protostuff (binary), decoded to only the needed fields.
    """

    def __init__(self, profile: Sign2Profile = Sign2Profile(), base_url: str = BASE_URL):
        self.logger = logging.getLogger(__name__)
        self.profile = profile
        if not (self.profile.vaid or "").strip():
            self.profile.vaid = _generate_vaid(self.profile.udid)
        self.base_url = base_url.rstrip("/")
        self.http = requests.Session()
        self.http.trust_env = False
        self._rsq = int(time.time()) % 100000

    @property
    def vaid(self) -> str:
        return self.profile.vaid

    def _next_rsq(self) -> int:
        self._rsq += 1
        return self._rsq

    def _get(
        self, path: str, params: Dict[str, Any]
    ) -> Tuple[int, Dict[str, str], bytes]:
        url = self.base_url + path
        r = self.http.get(
            url,
            params=params,
            headers=self._build_headers_for(url, params),
            verify=True,
        )
        return r.status_code, dict(r.headers), r.content

    def _build_headers_for(
        self, url: str, params: Dict[str, Any]
    ) -> Dict[str, str]:
        query = urlencode(params or {}, doseq=True)
        full_url = url if not query else f"{url}?{query}"

        t_ms = int(time.time() * 1000)
        return build_headers(
            url=full_url,
            t_ms=t_ms,
            user_agent=self.profile.user_agent(),
            ocs=self.profile.ocs(),
            vaid=self.profile.vaid,
            udid=self.profile.udid,
            oaid=self.profile.oaid,
            mkmix_id=self.profile.mkmix_id,
            net=self.profile.net,
            country=self.profile.country,
            sdkversion=self.profile.sdkversion,
            sdktype=self.profile.sdktype,
            ch=self.profile.ch,
            locale=self.profile.locale,
            rom=self.profile.rom,
            pid=self.profile.pid,
            appversion=self.profile.appversion,
            appid=self.profile.appid,
            client_time_ms=t_ms,
            h=str(self.profile.screen_h),
            w=str(self.profile.screen_w),
            rsq=self._next_rsq(),
            ext_original_url=True,
        )

    def user_login(
        self,
        *,
        pkg_name: str,
        secondary_token: str,
        ad_id: str = "",
    ) -> GameSdkLoginResult:
        status, headers, body = self._get(
            "/gamesdk/v2/user/login",
            {
                "adId": ad_id,
                "pkgName": pkg_name,
                "token": secondary_token,
            },
        )
        if status != 200:
            raise RuntimeError(f"user/login http={status} raw={body[:200]!r}")

        dto = GameAccountsDto()
        dto.ParseFromString(body)

        user_dto: Dict[str, Any] = {}
        if dto.HasField("user_dto"):
            u = dto.user_dto
            user_dto = {
                "user_id": str(u.user_id or ""),
                "user_name": str(u.user_name or ""),
                "email": str(u.email or ""),
                "mobile": str(u.mobile or ""),
                "create_time": str(u.create_time or ""),
                "user_status": str(u.user_status or ""),
                "real_name_status": str(u.real_name_status or ""),
                "age": int(u.age or 0),
                "twice_real_name_auth": bool(u.twice_real_name_auth),
            }
        return GameSdkLoginResult(
            code=str(dto.code or ""),
            msg=str(dto.msg or ""),
            ticket=str(dto.ticket or ""),
            trace_id=str(dto.trace_id or ""),
            user_dto=user_dto,
        )

    def account_latest_role(
        self,
        *,
        pkg_name: str,
        secondary_token: str,
    ) -> Tuple[GameSdkResult, List[Dict[str, Any]]]:
        status, headers, body = self._get(
            "/gamesdk/v2/user/account-latest-role",
            {
                "pkgName": pkg_name,
                "token": secondary_token,
            },
        )
        if status != 200:
            raise RuntimeError(
                f"account-latest-role http={status} raw={body[:200]!r}"
            )

        dto = LatestGameAccountsDto()
        dto.ParseFromString(body)
        result = GameSdkResult(code=str(dto.code or ""), msg=str(dto.msg or ""))

        out: List[Dict[str, Any]] = []
        for a in dto.accountMsgDtoList:
            out.append(
                {
                    "account_id": str(a.accountId or ""),
                    "user_id": str(a.userId or ""),
                    "role_id": str(a.roleId or ""),
                    "role_name": str(a.roleName or ""),
                    "realm_id": str(a.realmId or ""),
                    "realm_name": str(a.realmName or ""),
                    "login_time": int(a.loginTime or 0),
                    "role_level": int(a.roleLevel or 0),
                    "account_name": str(a.accountName or ""),
                }
            )

        return result, out
