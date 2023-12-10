"""
Taken from: https://github.com/zauberzeug/nicegui/issues/1956
Discussed at: https://github.com/encode/uvicorn/discussions/1103
"""

import asyncio
import threading
import uvicorn
from uvicorn.config import Config

class ThreadedUvicorn:
    def __init__(self, config: Config):
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(daemon=True, target=self.server.run)

    def start(self):
        self.thread.start()
        asyncio.run(self.wait_for_started())

    async def wait_for_started(self):
        while not self.server.started:
            await asyncio.sleep(0.1)

    def stop(self):
        if self.thread.is_alive():
            self.server.should_exit = True
            while self.thread.is_alive():
                continue

