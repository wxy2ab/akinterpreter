import platform
import socket
import pandas as pd
from functools import wraps
import inspect

def tsdata(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        limit = kwargs.pop('limit', None)
        offset = kwargs.pop('offset', None)
        if limit is None:
            limit = 2000

        all_data = []
        while True:
            kwargs['limit'] = limit
            kwargs['offset'] = offset
            df = func(*args, **kwargs)
            all_data.append(df)

            if len(df) < limit:
                break

            offset = offset + limit if offset else limit

        result_df = pd.concat(all_data, ignore_index=True)
        return result_df

    return wrapper

def is_wsl():
    # 检查操作系统平台
    if platform.system().lower() != 'linux':
        return False
    # 尝试读取/proc/version文件
    try:
        with open('/proc/version', 'r') as f:
            content = f.read().lower()
        # 检查文件内容中是否包含'microsoft'字样
        return 'microsoft' in content
    except FileNotFoundError:
        return False
    
def is_socket_connected(host, port):
    try:
        # 创建一个 socket 对象并尝试连接
        with socket.create_connection((host, port), timeout=5) as sock:
            return True
    except (socket.timeout, ConnectionRefusedError):
        return False


def check_proxy_running(host, port=10808,type="http"):
    # 要检查的地址和端口
    host_to_check = host

    from .config_setting import Config
    from .log import logger
    config = Config()
    if config.has_key("proxy_host"):
        host_to_check = config.get("proxy_host")

    port_to_check = port
    if config.has_key("proxy_port"):
        port_to_check = int(config.get("proxy_port"))
    
    try:
        if is_socket_connected(host_to_check, port_to_check):
            import os
            os.environ["http_proxy"]  = f"{type}://{host_to_check}:{port_to_check}"
            os.environ["https_proxy"] = f"{type}://{host_to_check}:{port_to_check}"
            logger.info("连接到代理")
        else:
            logger.warning("没有代理服务器")
    except Exception as e:
        host_to_check = "127.0.0.1"
        import os
        os.environ["http_proxy"]  = f"{type}://{host_to_check}:10808"
        os.environ["https_proxy"] = f"{type}://{host_to_check}:10808"
        logger.info("连接到代理")

def is_hugging_face_api_key_valid(api_key: str) -> bool:
    import requests
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    response = requests.get("https://huggingface.co/api/whoami-v2", headers=headers)
    return response.status_code == 200