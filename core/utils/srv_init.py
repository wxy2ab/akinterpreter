from functools import wraps
import time
from core.utils.log import logger

class ServiceInitMeta(type):
    def __new__(cls, name, bases, dct):
        # Find all methods with @service_init decorator
        for attr_name, attr_value in dct.items():
            if callable(attr_value) and hasattr(attr_value, "_service_init"):
                # Execute the method during class initialization
                attr_value()
        return super().__new__(cls, name, bases, dct)
    
service_init_funs = []

def service_init(func):
    """
    Custom decorator to execute functions during APIService initialization.
    """
    service_init_funs.append(func)

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"函数 {func.__module__}.{func.__name__} 运行时间: {execution_time:.5f} 秒")
        return result
    return wrapper