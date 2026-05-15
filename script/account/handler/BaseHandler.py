"""回放/录制处理器抽象基类"""

from __future__ import annotations
from abc import ABC
import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from script.account.AccountProxy import AccountProxy


class BaseHandler(ABC):
    """每个具体 handler 只覆写需要的方法。返回 bool: True=已处理。"""

    def __init__(self, proxy: AccountProxy, router):
        self.proxy = proxy
        self.router = router

    def on_create_login_request(self, flow) -> bool:
        return False

    def on_create_login_response(self, flow) -> bool:
        return False

    def on_qrcode_query(self, flow) -> bool:
        return False

    def on_exchange_token(self, flow) -> bool:
        return False

    @staticmethod
    def _fake_qrcode_query(flow, tag: str = ""):
        try:
            data = json.loads(flow.response.content)
            data.setdefault("qrcode", {})["status"] = 2
            flow.response.content = json.dumps(data, ensure_ascii=False).encode()
            logging.info(f"[Proxy {tag}] 伪造扫码状态")
        except Exception:
            pass
