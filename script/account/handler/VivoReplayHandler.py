"""Vivo 渠道回放"""

from __future__ import annotations
from typing import TYPE_CHECKING

from script.account.handler.ChannelReplayHandler import ChannelReplayHandler

if TYPE_CHECKING:
    from script.account.AccountProxy import AccountProxy


class VivoReplayHandler(ChannelReplayHandler):

    def _build_confirm_data(self, channel_auth: dict, short_game_id: str) -> dict | None:
        from script.account.channel.VivoChannel import build_replay_data
        return build_replay_data(channel_auth, short_game_id)
