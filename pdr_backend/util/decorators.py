import time

@enforce_types
def retry_function(times=5, delay=2, allowed_exceptions=()):
    """
    Decorator for retrying a function if exception occurs.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(times):
                try:
                    return func(*args, **kwargs)
                except allowed_exceptions as e:
                    if _ < times - 1:
                        print(f" -- An error: {e} occured, trying again in {delay} seconds")
                        time.sleep(delay)
                        continue
                    else:
                        raise e
        return wrapper
    return decorator