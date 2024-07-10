from asyncio import Queue
from ..utils.single_ton import Singleton

class ReplayMessageQueue(metaclass=Singleton):
    def __init__(self):
        self.queue = Queue()

    async def put(self, item):
        await self.queue.put(item)

    async def get(self):
        return await self.queue.get()

    def empty(self):
        return self.queue.empty()