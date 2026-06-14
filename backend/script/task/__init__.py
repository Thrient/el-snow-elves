"""任务管理领域 — IPC 注册"""
from script.api.Api import Api


def register(api: Api, app) -> None:
    """注册 task 领域所有 IPC 事件处理器。"""
    from script.task_editor.TaskLibrary import load_task_list, import_task, resolve_task_version, build_task_zip

    api.on("API:TASK:EXPORT", app.export_task)
    api.on("API:TASK:EXPORT:BATCH", app.export_tasks_batch)
    api.on("API:TASK:IMPORT", import_task)
    api.on("API:SCRIPT:LOAD:LIST", load_task_list)
