"""计划执行领域 — IPC 注册"""
from script.api.Api import Api


def register(api: Api, app) -> None:
    """注册 plan 领域所有 IPC 事件处理器。"""
    from script.settings.AppConfig import load_plans, save_plans

    api.on("API:PLAN:LOAD", load_plans)
    api.on("API:PLAN:SAVE", save_plans)
    api.on("API:CRON:TRIGGER", app._on_cron_trigger)
