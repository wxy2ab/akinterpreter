import sys
from typing import Any, Dict
from ._handler import MessageHandler
from .replay_event_bus import ReplayEventBus

class CliUIHandler(MessageHandler):
    def __init__(self, print_func):
        self.print_colored = print_func
        self.event_bus = ReplayEventBus()
        self.current_response_type = None

    def subscribe(self):
        self.event_bus.subscribe("message", self.handle_message)
        self.event_bus.subscribe("error", self.handle_error)

    def unsubscribe(self):
        self.event_bus.unsubscribe("message", self.handle_message)
        self.event_bus.unsubscribe("error", self.handle_error)

    async def handle_message(self, data: Dict[str, Any]):
        self._handle_response({"type": "message", "content": data['content']})

    async def handle_error(self, data: Dict[str, Any]):
        self._handle_response({"type": "error", "content": data['content']})

    def _handle_response(self, response: Dict[str, Any]):
        response_type = response.get('type', '')
        content = response.get('content', '')

        if response_type != self.current_response_type:
            if self.current_response_type is not None:
                print()  # 添加换行，为新类型做准备
            self.current_response_type = response_type
            if response_type == 'error':
                self.print_colored("[错误] ", 'red', end='')
            elif response_type == 'message':
                self.print_colored("[消息] ", 'green', end='')

        print(content, end='', flush=True)