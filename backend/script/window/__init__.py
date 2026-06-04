"""窗口管理领域 — IPC 注册"""
from script.api.Api import Api


def register(api: Api, app) -> None:
    """注册 window 领域所有 IPC 事件处理器。"""
    api.on("API:SCRIPT:SEARCH", app.search)
    api.on("API:SCRIPT:BIND", app.bind)
    api.on("API:SCRIPT:UNBIND", app.unbind)
    api.on("API:SCRIPT:RESUME", app.resume)
    api.on("API:SCRIPT:PAUSE", app.pause)
    api.on("API:SCRIPT:STOP", app.stop_task)
    api.on("API:SCRIPT:LOCK", app.lock_window)
    api.on("API:SCRIPT:UNLOCK", app.unlock_window)
    api.on("API:SCRIPT:SET_OPACITY", app.set_window_opacity)
