"""华为渠道回放：_build_confirm_data 委托给 HuaweiChannel.build_replay_data"""

from __future__ import annotations
from typing import TYPE_CHECKING

from script.account.handler.ChannelReplayHandler import ChannelReplayHandler

if TYPE_CHECKING:
    from script.account.AccountProxy import AccountProxy


class HuaweiReplayHandler(ChannelReplayHandler):

    def _build_confirm_data(self, channel_auth: dict, short_game_id: str) -> dict | None:
        from script.account.channel.HuaweiChannel import build_replay_data
        return build_replay_data(channel_auth, short_game_id)
