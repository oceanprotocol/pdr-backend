from functools import wraps
import time

from enforce_typing import enforce_types


@enforce_types
def retry_function(times=5, delay=2, disallowed_exceptions=()):
    """
    Decorator for retrying a function unless a disallowed exception occurs or reaches max retries.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if isinstance(e, disallowed_exceptions):
                        raise e
                    if _ < times - 1:
                        print(
                            f" -- An error: {e} occured, trying again in {delay} seconds"
                        )
                        time.sleep(delay)
                        continue
                    raise e
            return None

        return wrapper

    return decorator
