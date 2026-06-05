"""分片睡眠 — 消除超时检测盲区"""

import time


def safe_sleep(seconds: float, check_fn, tick: float = 0.1) -> bool:
    """分片睡眠，每 tick 秒调用 check_fn()。

    Args:
        seconds: 总睡眠时长（秒），<=0 时仅执行一次 check_fn
        check_fn: 无参函数，返回 True 表示应中断
        tick: 检查间隔（秒），默认 0.1

    Returns:
        True 表示被 check_fn 中断，False 表示正常睡完
    """
    if seconds <= 0:
        return check_fn()

    elapsed = 0.0
    while elapsed < seconds:
        remaining = min(tick, seconds - elapsed)
        time.sleep(remaining)
        elapsed += remaining
        if check_fn():
            return True
    return False
