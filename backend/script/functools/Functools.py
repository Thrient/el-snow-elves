import time

from script.engine.safe_sleep import safe_sleep


def delay(pre_delay=0, post_delay=0):
    """添加延迟"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            time.sleep(float(kwargs.get('pre_delay', pre_delay)) / 1000)
            result = func(*args, **kwargs)
            time.sleep(float(kwargs.get('post_delay', post_delay)) / 1000)
            return result

        return wrapper

    return decorator


def repeat(count=1):
    """重复执行"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(int(kwargs.get('count', count))):
                func(*args, **kwargs)

        return wrapper

    return decorator


def during(seconds=1800, dealy=0.5, is_valid=lambda x: bool(x), predicate=lambda: True):
    """持续运行（seconds 参数单位 ms）。seconds=null 时仅执行一次。"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            if kwargs.get('seconds', seconds) is None:
                return func(*args, **kwargs)
            end_time = time.time() + kwargs.get('seconds', seconds) / 1000
            while time.time() < end_time and kwargs.get("predicate", predicate)():
                result = func(*args, **kwargs)
                if kwargs.get("is_valid", is_valid)(result):
                    return result
                if safe_sleep(float(kwargs.get('dealy', dealy)), lambda: not kwargs.get("predicate", predicate)()):
                    break
            return None

        return wrapper

    return decorator


def wait_until(k=1, seconds=1000, dealy=0.5, is_valid=lambda x: bool(x), predicate=lambda: True):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if kwargs.get('seconds', seconds) is None:
                return func(*args, **kwargs)
            count = 0
            end_time = time.time() + kwargs.get('seconds', seconds) / 1000
            while time.time() < end_time and kwargs.get("predicate", predicate)():
                result = func(*args, **kwargs)

                if kwargs.get("is_valid", is_valid)(result):
                    count += 1
                    if count >= kwargs.get("k", k):
                        return result
                else:
                    count = 0
                if safe_sleep(float(kwargs.get('dealy', dealy)),
                              lambda: not kwargs.get("predicate", predicate)()):
                    break
            return None

        return wrapper

    return decorator
