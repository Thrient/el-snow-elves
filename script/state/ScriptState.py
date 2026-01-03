from enum import IntEnum


class ScriptState(IntEnum):
    """Script 进程的全局状态机"""
    INIT       = 0  # 初始化
    STOPPED    = 1  # 停止
    RUNNING    = 2  # 运行
    PAUSED     = 3  # 暂停
    FULLSCREEN = 4  # 全屏模式
    UNBINDING  = 5  # 解绑
    NOTASK     = 6  # 无任务

    def __str__(self):
        return self.name
