import logging
from colorlog import ColoredFormatter

def setup_logger():
    # 创建一个名为 "my_logger" 的 logger
    logger = logging.getLogger("my_logger")
    logger.setLevel(logging.DEBUG)

    # 创建一个控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # 创建一个彩色格式化器
    color_formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )

    # 设置控制台处理器的格式化器
    console_handler.setFormatter(color_formatter)

    # 将控制台处理器添加到 logger
    logger.addHandler(console_handler)

    return logger

# 使用示例
logger = setup_logger()