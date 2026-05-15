"""渠道回放抽象基类：scan → _build_confirm_data() → confirm_login"""

from __future__ import annotations
import json
import logging
from abc import abstractmethod
from typing import TYPE_CHECKING

from script.account.handler.BaseHandler import BaseHandler
from script.account.HostsManager import HostsManager

if TYPE_CHECKING:
    from script.account.AccountProxy import AccountProxy


class ChannelReplayHandler(BaseHandler):
    """渠道回放基类。子类只需实现 _build_confirm_data()。"""

    def on_create_login_response(self, flow) -> bool:
        suid = self.proxy.scanner_uuid or self.proxy.process_id
        if self.proxy.channel_fake and self.proxy.token_info and suid:
            self.proxy.scanner_uuid = suid
            self._trigger_channel_confirm()
        return True

    def on_qrcode_query(self, flow) -> bool:
        # 确认完成前只返回"已扫码"，避免游戏客户端提前发 exchange_token 导致 1311
        if self.proxy.channel_done:
            self._fake_qrcode_query(flow, "CH")
        else:
            try:
                data = json.loads(flow.response.content)
                data.setdefault("qrcode", {})["status"] = 1
                flow.response.content = json.dumps(data, ensure_ascii=False).encode()
            except Exception:
                pass
        return True

    def on_exchange_token(self, flow) -> bool:
        try:
            body = json.loads(flow.response.content)
            user = body.get("user", {})
            logging.info(f"[Proxy] 渠道 exchange_token code={body.get('code')} user_id={user.get('id', 'N/A')} login_channel={user.get('login_channel', 'N/A')} keys={list(user.keys())}")
            if user:
                self.proxy.completed = True
                HostsManager.restore()
                logging.info("[Proxy] 渠道回放完成，已还原hosts")
        except Exception:
            logging.info(f"[Proxy] 渠道 exchange_token 透传, status={flow.response.status_code}")
        return True

    # ── channel confirm flow ──

    def _trigger_channel_confirm(self):
        import threading as _thr

        def _do():
            try:
                import requests as _requests

                ca = (self.proxy.token_info or {}).get("channel_auth", {})
                ct = ca.get("channel_type", "")
                gid = self.proxy.game_id
                pid = self.proxy.process_id
                short = gid.split("-")[-1] if "-" in gid else gid
                suid = self.proxy.scanner_uuid or pid

                # Step 1: /mpay/api/qrcode/scan
                scan_params = {
                    "uuid": suid,
                    "login_channel": ct,
                    "app_channel": ct,
                    "pay_channel": ct,
                    "game_id": gid,
                    "gv": "157",
                    "gvn": "1.5.80",
                    "cv": "a1.5.0",
                }
                scan_resp = _requests.get(
                    "https://42.186.193.21/mpay/api/qrcode/scan",
                    params=scan_params,
                    headers={"Host": "service.mkey.163.com"},
                    timeout=15, verify=False,
                )
                scan_json = scan_resp.json()
                logging.info(f"[Proxy] scan: code={scan_json.get('code')} status={scan_resp.status_code}")

                if scan_json.get("code") == 1424:
                    gid = scan_json.get("game", {}).get("id", gid)
                    short = gid.split("-")[-1] if "-" in gid else gid
                    scan_params["game_id"] = gid
                    scan_resp = _requests.get(
                        "https://42.186.193.21/mpay/api/qrcode/scan",
                        params=scan_params,
                        headers={"Host": "service.mkey.163.com"},
                        timeout=15, verify=False,
                    )

                if scan_resp.status_code != 200:
                    logging.error(f"[Proxy] scan 失败: {scan_resp.status_code}")
                    return

                # Step 2: 渠道构建 confirm 数据
                confirm_body = self._build_confirm_data(ca, short)
                if not confirm_body:
                    logging.error(f"[Proxy] 渠道 {ct} 构建确认数据失败")
                    return
                confirm_body["uuid"] = suid
                confirm_body["game_id"] = gid

                # Step 3: confirm_login
                body_str = "&".join(f"{k}={v}" for k, v in confirm_body.items())
                r = _requests.post(
                    "https://42.186.193.21/mpay/api/qrcode/confirm_login",
                    data=body_str,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Host": "service.mkey.163.com",
                    },
                    timeout=15, verify=False,
                )
                logging.info(f"[Proxy] confirm_login: status={r.status_code} body={r.text[:200]}")
                if r.status_code == 200:
                    self.proxy.channel_done = True
                    logging.info("[Proxy] channel confirm_login: OK")
                else:
                    logging.error("[Proxy] channel confirm_login FAIL")

            except Exception as e:
                logging.error(f"[Proxy] channel confirm_login 异常: {e}")

        _thr.Thread(target=_do, daemon=True).start()

    @abstractmethod
    def _build_confirm_data(self, channel_auth: dict, short_game_id: str) -> dict | None:
        """子类实现：构建 confirm_login POST body（不含 uuid / game_id）"""
        ...
