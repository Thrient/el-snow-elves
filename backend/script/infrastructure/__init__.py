"""基础设施领域 — IPC 注册"""
from script.api.Api import Api


def register(api: Api, app) -> None:
    """注册 infrastructure 领域所有 IPC 事件处理器。"""
    from script.config.Setting import VERSION
    from script.infrastructure.UpdateEngine import UpdateEngine
    from script.infrastructure.UpdateWorker import UpdateWorker

    api.on("API:UPDATE:CHECK", UpdateEngine.check_version)
    api.on("API:APP:VERSION", lambda: VERSION)

    def _handle_update_diff(payload: dict):
        return UpdateEngine.diff_manifest(
            payload.get("current_version", "0.0.0"),
            payload.get("manifest", {}),
        )
    api.on("API:UPDATE:DIFF", _handle_update_diff)

    def _handle_update_download(payload: dict):
        return UpdateWorker.download_updates(payload.get("current_version", "0.0.0"))
    api.on("API:UPDATE:DOWNLOAD", _handle_update_download)

    def _handle_update_apply():
        UpdateWorker.apply_and_restart()
        import time
        time.sleep(0.3)
        app._do_exit()

    api.on("API:UPDATE:APPLY", lambda: _handle_update_apply())

    api.on("API:TEMPLATE:CAPTURE", app.capture_for_template)
    api.on("API:TEMPLATE:CAPTURE:PNG", app.capture_for_template_png)
    api.on("API:TEMPLATE:SAVE", app.save_template_image)

    def _handle_set_theme(payload: dict):
        theme = payload.get("theme", "light") if isinstance(payload, dict) else "light"
        app.set_titlebar_theme(theme == "dark")
    api.on("API:APP:SET_THEME", _handle_set_theme)
