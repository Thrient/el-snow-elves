import time
from typing import Union


def delay(pre_delay: Union[int, float] = 0, post_delay: Union[int, float] = 0):
    """添加延迟"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            time.sleep(kwargs.get('pre_delay', pre_delay) / 1000)
            result = func(*args, **kwargs)
            time.sleep(kwargs.get('post_delay', post_delay) / 1000)
            return result

        return wrapper

    return decorator


def repeat(count: Union[int] = 1):
    """重复执行"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(kwargs.get('count', count)):
                func(*args, **kwargs)

        return wrapper

    return decorator

