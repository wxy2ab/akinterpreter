from asyncio import Queue
from ..utils.single_ton import Singleton


class SSEMessageQueue(metaclass=Singleton):
    def __init__(self):
        self.queues = {}

    def get_queue(self, session_id):
        if session_id not in self.queues:
            self.queues[session_id] = Queue()
        return self.queues[session_id]

    async def put(self, session_id, item):
        queue = self.get_queue(session_id)
        await queue.put(item)

    async def get(self, session_id):
        queue = self.get_queue(session_id)
        return await queue.get()

    def empty(self, session_id):
        queue = self.get_queue(session_id)
        return queue.empty()

