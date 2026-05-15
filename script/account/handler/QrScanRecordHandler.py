"""官服扫码录制：捕获 exchange_token 响应 + cookies"""

from __future__ import annotations
import json
import logging
from typing import TYPE_CHECKING

from script.account.handler.BaseHandler import BaseHandler

if TYPE_CHECKING:
    from script.account.AccountProxy import AccountProxy


class QrScanRecordHandler(BaseHandler):

    def on_exchange_token(self, flow) -> bool:
        if self.proxy.completed:
            return True
        try:
            data = json.loads(flow.response.content)

            login_channel = (data.get("user", {})).get("login_channel", "")
            if login_channel and not login_channel.startswith("netease"):
                ext = data.get("ext_info")
                if isinstance(ext, dict):
                    ext["is_remember"] = True
                pc_ext = data.get("pc_ext") or data.get("pc_ext_info") or data.get("pcExtInfo")
                if isinstance(pc_ext, dict):
                    pc_ext["is_remember"] = True
            flow.response.content = json.dumps(data, ensure_ascii=False).encode()

            user = data.get("user", {})
            if user:
                self.router.schedule(lambda: self._finish_recording(data, user, login_channel))
        except Exception as e:
            logging.error(f"[Proxy REC] exchange_token解析失败: {e}")
        return True

    def _finish_recording(self, data, user, login_channel):
        is_channel = bool(login_channel and not login_channel.startswith("netease"))

        captured: dict = {"source": "exchange_token", "response_data": data}
        if self.router.cookies:
            captured["cookies"] = self.router.cookies

        self.router.captured = captured
        self.proxy.completed = True

        name = user.get("client_username", user.get("name", ""))
        parts = [f"[Proxy REC] 捕获登录信息: {name}"]
        if is_channel:
            parts.append("(is_remember)")
        if self.router.cookies:
            parts.append(f"(cookies: {len(self.router.cookies)}个)")
        logging.info(" ".join(parts))
