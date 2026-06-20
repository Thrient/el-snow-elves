"""任务编辑领域 — IPC 注册"""
from script.api.Api import Api


def register(api: Api, app) -> None:
    """注册 task-editor 领域所有 IPC 事件处理器。"""
    from script.task import get_repo
    from script.task_editor.TemplateAssets import (
        list_actions, list_template_images, list_global_common_steps,
        load_positions, save_positions,
    )
    from script.engine.FlowEngine import clear_common_cache

    repo = get_repo()

    api.on("API:TASK:LOAD:FULL", repo.get_full_config)
    api.on("API:TASK:SAVE:FULL", repo.save)
    api.on("API:TASK:CREATE", repo.create)
    api.on("API:TASK:DELETE", repo.delete)
    api.on("API:TASK:SAVE:AS:NEW", repo.save_as_new_version)
    api.on("API:AUTOCOMPLETE:ACTIONS", list_actions)
    api.on("API:AUTOCOMPLETE:TEMPLATES", list_template_images)
    api.on("API:AUTOCOMPLETE:STEPS", repo.list_steps_for_task)
    api.on("API:AUTOCOMPLETE:COMMON:STEPS", list_global_common_steps)
    api.on("API:COMMON:CACHE:CLEAR", clear_common_cache)
    api.on("API:TASK:LOAD:POSITIONS", load_positions)
    api.on("API:TASK:SAVE:POSITIONS", save_positions)
    api.on("API:PREPROCESS:APPLY", app.preprocess_apply)
