import threading

from functools import wraps


def run_async(func):
    @wraps(func)
    def async_func(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()

    return async_func
