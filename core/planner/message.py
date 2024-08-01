from typing import Dict, Literal, Any, Generator
from dataclasses import dataclass

MessageType = Literal["message", "plan", "code","full_code", "code_review","progress", "result", "report" ,"info","warning","error", "debug" ,"finish"]

@dataclass
class Message:
    content: Any
    type: MessageType = "message"

def send_message(content: Any, type: str = "message", **kwargs) -> Dict[str, Any]:
    """
    创建一个包含消息内容、类型和任何额外参数的字典。

    参数:
    content (Any): 消息的内容
    type (str): 消息的类型，默认为 "message"
    **kwargs: 任何额外的关键字参数

    返回:
    Dict[str, Any]: 包含所有提供的信息的字典
    """
    message = {
        "type": type,
        "content": content
    }
    message.update(kwargs)
    return message

def message_generator(messages: Generator[Message, None, None]) -> Generator[dict, None, None]:
    for message in messages:
        yield {"type": message.type, "content": message.content}