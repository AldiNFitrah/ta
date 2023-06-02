import threading
import pytz

from datetime import datetime
from functools import wraps


def run_async(func):
    @wraps(func)
    def async_func(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()

    return async_func

def get_current_utc_datetime():
    return datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
