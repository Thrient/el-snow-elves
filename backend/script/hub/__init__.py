"""Hub 同步模块 — IPC 注册"""
from script.api.Api import Api


def register(api: Api, app) -> None:
    """注册 hub 领域所有 IPC 事件处理器。"""
    from script.hub.HubSync import HubSync

    def handle_update_from_hub(name: str = "", author: str = ""):
        """处理前端发起的任务更新请求。"""
        if not name or not author:
            return {"error": "缺少 name 或 author 参数"}
        sync = HubSync()
        return sync.download_and_import(author, name)

    api.on("API:TASK:UPDATE_FROM_HUB", handle_update_from_hub)
