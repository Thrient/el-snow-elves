import threading
from functools import wraps
from typing import Callable, Any, Optional


def thread(daemon: bool = False, name: Optional[str] = None):
    """
    装饰器工厂：使被装饰函数在新线程中执行，可选守护线程。

    Args:
        daemon (bool): 是否为守护线程，默认为False。
        name (str, optional): 线程名称。

    Returns:
        Callable: 包装后的函数，调用后返回线程对象。
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., threading.Thread]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> threading.Thread:
            obj = threading.Thread(
                target=func,
                args=args,
                kwargs=kwargs,
                daemon=daemon,
                name=name
            )
            obj.start()
            return obj

        return wrapper

    return decorator
