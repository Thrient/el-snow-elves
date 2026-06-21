"""OPPO 渠道回放 Handler"""
from script.account.handler.ChannelReplayHandler import ChannelReplayHandler


class OppoReplayHandler(ChannelReplayHandler):
    def _build_confirm_data(self, channel_auth: dict, short_game_id: str) -> dict | None:
        from script.account.channel.oppo import build_replay_data
        return build_replay_data(channel_auth, short_game_id)
