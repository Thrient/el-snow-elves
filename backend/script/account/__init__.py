"""账号管理领域 — IPC 注册"""
from script.api.Api import Api


def register(api: Api, app) -> None:
    """注册 account 领域所有 IPC 事件处理器。"""
    from script.account.AccountManager import AccountManager
    from script.util.GamePathManager import get_game_path, set_game_path

    api.on("API:ACCOUNT:LIST", AccountManager.list_accounts)
    api.on("API:ACCOUNT:LIST:NAMES", AccountManager.list_account_names)
    api.on("API:ACCOUNT:SAVE", AccountManager.save_account)
    api.on("API:ACCOUNT:DELETE", AccountManager.delete_account)
    api.on("API:ACCOUNT:RENAME", AccountManager.rename_account)
    api.on("API:ACCOUNT:SAVE_ORDER", AccountManager.save_order)
    api.on("API:ACCOUNT:RECORD:START", app._session.start_qr_recording)
    api.on("API:ACCOUNT:RECORD:START:CHANNEL", app._session.start_channel_recording)
    api.on("API:ACCOUNT:RECORD:STOP", app._session.stop_recording)
    api.on("API:ACCOUNT:RECORD:STATUS", app._session.recording_status)
    api.on("API:ACCOUNT:REPLAY:START", app._session.start_replay)
    api.on("API:ACCOUNT:QUICK_START", app._qs.execute)
    api.on("API:ACCOUNT:REPLAY:STOP", app._session.stop_replay)
    api.on("API:GAME:GET_PATH", get_game_path)
    api.on("API:GAME:SET_PATH", lambda: set_game_path(app.window))
