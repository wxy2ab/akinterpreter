import asyncio
from asyncio import Queue
from typing import Any, AsyncGenerator, Dict, Union
from ..utils.single_ton import Singleton

class AsyncSingletonReplayGenerator(metaclass=Singleton):
    def __init__(self):
        self.queue = Queue()

    async def __aiter__(self)->AsyncGenerator[Union[Dict[str,Any],str],None]:
        while True:
            item = await self.queue.get()
            if item is None:  # 使用 None 作为结束信号
                break
            yield item

    async def put(self, item):
        await self.queue.put(item)

    async def close(self):
        await self.queue.put(None)
