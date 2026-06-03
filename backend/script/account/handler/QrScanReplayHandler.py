"""官服扫码回放：伪造 QR query 状态 + 注入存储的 exchange_token 响应"""

from __future__ import annotations
import json
import logging
from typing import TYPE_CHECKING

from script.account.handler.BaseHandler import BaseHandler
from script.account.HostsManager import HostsManager

if TYPE_CHECKING:
    from script.account.AccountProxy import AccountProxy


class QrScanReplayHandler(BaseHandler):

    def on_qrcode_query(self, flow) -> bool:
        self._fake_qrcode_query(flow, "INJ")
        return True

    def on_exchange_token(self, flow) -> bool:
        t = self.proxy.token_info or {}
        resp_data = t.get("response_data", {})
        if resp_data:
            flow.response.content = json.dumps(resp_data, ensure_ascii=False).encode()
            flow.response.status_code = 200
            for cookie_str in t.get("cookies", []):
                flow.response.headers.add("Set-Cookie", cookie_str)
            self.proxy.completed = True
            HostsManager.restore()
            logging.info("[Proxy INJ] 注入exchange_token响应，已还原hosts")
        return True
