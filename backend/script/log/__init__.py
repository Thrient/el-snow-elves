"""日志领域 — IPC 注册"""
from script.api.Api import Api


def register(api: Api) -> None:
    """注册 log 领域所有 IPC 事件处理器。"""
    from script.util.LogManager import read_logs, get_log_files

    api.on("API:LOG:READ", read_logs)
    api.on("API:LOG:FILES", get_log_files)
