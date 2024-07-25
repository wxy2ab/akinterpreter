import time
from functools import wraps 

def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"函数 {func.__module__}.{func.__name__} 运行时间: {execution_time:.5f} 秒")
        return result
    return wrapper