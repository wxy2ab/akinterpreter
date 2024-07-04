import time
from functools import wraps

def retry(max_retries=3, delay=5):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        raise
                    print(f"Error occurred: {e}. Retrying in {delay} seconds... (Attempt {retries} of {max_retries})")
                    time.sleep(delay)
        return wrapper
    return decorator