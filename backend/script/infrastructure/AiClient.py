"""AI Vision 客户端 — 截图 → Hub AI → 返回结果"""
import logging
import re

import requests

_log = logging.getLogger("Elves.AiClient")

HUB_URL = "https://elves.elarion.cn/api/v1"


class AiClient:
    _session: requests.Session | None = None

    @classmethod
    def _get_session(cls) -> requests.Session:
        if cls._session is None:
            cls._session = requests.Session()
            cls._session.headers["Connection"] = "keep-alive"
        return cls._session

    @staticmethod
    def vision(image_data_uri: str, prompt: str) -> str:
        """POST /ai/vision → 返回 reply 文本，失败返回 "" """
        try:
            resp = AiClient._get_session().post(
                f"{HUB_URL}/ai/vision",
                json={"image": image_data_uri, "prompt": prompt},
                timeout=300,
            )
            resp.raise_for_status()
            body = resp.json()
            if body.get("code") == 0:
                reply = body.get("data", {}).get("reply", {})
                m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", reply, re.DOTALL)
                reply = m.group(1).strip() if m else reply.strip()
                _log.info(f"ai_vision: {reply}")
                return reply
            _log.error(f"ai_vision: {body.get('message')}")
            return {}
        except Exception as e:
            _log.error(f"ai_vision: {e}")
            return {}
