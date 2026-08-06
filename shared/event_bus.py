"""
事件总线 - 携带 draw_record 数据广播到所有订阅者

设计:
- notify_new_draw(record) 同步推送到所有订阅者队列（零延迟唤醒 Processor）
- 每个 Processor 通过 subscribe() 获得独立队列，不丢不竞争
"""

import asyncio

from shared.logger import get_logger

logger = get_logger("event_bus")

_subscribers: list[asyncio.Queue] = []
QUEUE_MAXSIZE = 16


def subscribe(maxsize: int = QUEUE_MAXSIZE) -> asyncio.Queue:
    """订阅，返回独立的 Queue"""
    q: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
    _subscribers.append(q)
    return q


def unsubscribe(q: asyncio.Queue) -> None:
    try:
        _subscribers.remove(q)
    except ValueError:
        pass


def notify_new_draw(record: dict | None = None) -> None:
    """同步广播: 把开奖记录推送到所有订阅者队列（不阻塞）"""
    for q in _subscribers:
        try:
            q.put_nowait(record)
        except asyncio.QueueFull:
            logger.warning("订阅队列已满，跳过一次开奖广播")


def reset_draw_event() -> None:
    """清空所有队列并移除订阅者（停机时调用）"""
    for q in _subscribers:
        while not q.empty():
            try:
                q.get_nowait()
            except asyncio.QueueEmpty:
                break
    _subscribers.clear()
