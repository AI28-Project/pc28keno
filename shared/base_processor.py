"""
Processor 基类 - 事件驱动 + 轮询兜底

设计:
- 通过 Queue 接收 collector 推送的 draw_record，零延迟 + 携带数据
- 超时走轮询兜底（record=None 表示超时触发）
- 连续处理直到队列清空
"""

import asyncio
from abc import ABC, abstractmethod

from shared.event_bus import subscribe, unsubscribe
from shared.logger import get_logger


class BaseProcessor(ABC):

    def __init__(self, poll_interval: float):
        self._running = False
        self._poll_interval = poll_interval
        self._queue: asyncio.Queue | None = None
        self.logger = get_logger(self.processor_name)

    @property
    @abstractmethod
    def processor_name(self) -> str:
        ...

    @property
    def processor_display_name(self) -> str:
        return self.processor_name

    @abstractmethod
    async def _process_once(self, record: dict | None = None) -> bool:
        """
        处理一期数据。
        record: 从 event_bus 收到的 draw_record，None 表示轮询触发需自行查询。
        返回 True=处理了数据(可能还有后续)，False=无数据。
        """
        ...

    async def _on_start(self) -> None:
        pass

    async def _on_stop(self) -> None:
        pass

    async def start(self) -> None:
        self._running = True
        self._queue = subscribe()
        await self._on_start()
        self.logger.info(f"{self.processor_display_name}服务启动")

        while self._running:
            try:
                record = None
                try:
                    record = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=self._poll_interval,
                    )
                except asyncio.TimeoutError:
                    pass

                if not self._running:
                    break

                # 处理收到的记录（或轮询兜底）
                await self._process_once(record)

                # 排空队列中的积压
                while self._running and not self._queue.empty():
                    try:
                        record = self._queue.get_nowait()
                        await self._process_once(record)
                    except asyncio.QueueEmpty:
                        break

            except Exception as e:
                self.logger.error(f"{self.processor_display_name}异常: {e}")
                await asyncio.sleep(0.2)

    def stop(self) -> None:
        self._running = False
        if self._queue is not None:
            try:
                self._queue.put_nowait(None)
            except asyncio.QueueFull:
                pass

    async def close(self) -> None:
        self.stop()
        if self._queue is not None:
            unsubscribe(self._queue)
            self._queue = None
        await self._on_stop()
        self.logger.info(f"{self.processor_display_name}服务已停止")
