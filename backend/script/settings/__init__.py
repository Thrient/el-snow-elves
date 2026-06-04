"""设置领域 — IPC 注册"""
from script.api.Api import Api


def register(api: Api) -> None:
    """注册 settings 领域所有 IPC 事件处理器。"""
    from script.settings.AppConfig import load_settings
    from script.settings.TaskConfig import (
        get_config_list, save_config, load_config, delete_config,
    )
    from script.util.StartupManager import get_autostart, set_autostart

    api.on("API:SETTINGS:LOAD", load_settings)
    api.on("API:SCRIPT:SAVE:CONFIG", save_config)
    api.on("API:SCRIPT:LOAD:CONFIG", load_config)
    api.on("API:SCRIPT:LOAD:CONFIG:LIST", get_config_list)
    api.on("API:SCRIPT:DELETE:CONFIG", delete_config)
    api.on("API:AUTOSTART:GET", lambda: get_autostart())
    api.on("API:AUTOSTART:SET", set_autostart)
