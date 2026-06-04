"""任务编辑领域 — IPC 注册"""
from script.api.Api import Api


def register(api: Api, app) -> None:
    """注册 task-editor 领域所有 IPC 事件处理器。"""
    from script.task_editor.task_library import (
        get_full_task_config, save_full_task_config,
        create_task, delete_task, list_steps_for_task,
    )
    from script.task_editor.template_assets import (
        list_actions, list_template_images, list_global_common_steps,
        load_positions, save_positions,
    )
    from script.engine.flow_engine import clear_common_cache

    api.on("API:TASK:LOAD:FULL", get_full_task_config)
    api.on("API:TASK:SAVE:FULL", save_full_task_config)
    api.on("API:TASK:CREATE", create_task)
    api.on("API:TASK:DELETE", delete_task)
    api.on("API:AUTOCOMPLETE:ACTIONS", list_actions)
    api.on("API:AUTOCOMPLETE:TEMPLATES", list_template_images)
    api.on("API:AUTOCOMPLETE:STEPS", list_steps_for_task)
    api.on("API:AUTOCOMPLETE:COMMON:STEPS", list_global_common_steps)
    api.on("API:COMMON:CACHE:CLEAR", clear_common_cache)
    api.on("API:TASK:LOAD:POSITIONS", load_positions)
    api.on("API:TASK:SAVE:POSITIONS", save_positions)
    api.on("API:PREPROCESS:APPLY", app.preprocess_apply)
