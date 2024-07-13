from typing import Dict, Literal, Any, Generator
from dataclasses import dataclass

MessageType = Literal["message", "plan", "code","full_code", "progress", "result", "report" ,"error", "debug" ,"finish"]

@dataclass
class Message:
    content: Any
    type: MessageType = "message"

def send_message(content: Any, type: MessageType = "message") -> Dict[str, Any]:
    return {"type": type, "content": content}

def message_generator(messages: Generator[Message, None, None]) -> Generator[dict, None, None]:
    for message in messages:
        yield {"type": message.type, "content": message.content}