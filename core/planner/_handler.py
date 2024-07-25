from abc import ABC, abstractmethod
from typing import Any, Dict


class MessageHandler(ABC):
    @abstractmethod
    async def handle_message(self, message: Dict[str, Any]):
        pass
