"""任务存储源 — 代表一个任务根目录及其读写属性"""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TaskSource:
    root: Path        # 任务根目录 (e.g. resources/config/)
    writable: bool    # 是否允许写入
    priority: int     # 冲突时数值越大越优先
    name: str         # 日志标识 (e.g. "builtin", "user")
