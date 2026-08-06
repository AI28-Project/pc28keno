"""
入口：Keno 采集 + 遗漏 + ABC 遗漏 + 统计 + 长龙
用法: python main.py
"""

import asyncio
import selectors

from shared.logger import get_logger
from shared.db.connection import init_pool, close_pool
from shared.event_bus import reset_draw_event
from modules.keno.services.collector import KenoCollector
from modules.omission.services.processor import OmissionProcessor
from modules.abc_omission.services.processor import ABCOmissionProcessor
from modules.statistics.services.processor import StatisticsProcessor
from modules.dragon.services.processor import DragonProcessor

logger = get_logger("main")


async def run() -> None:
    await init_pool()

    keno_collector = KenoCollector()
    processors = [
        OmissionProcessor(),
        ABCOmissionProcessor(),
        StatisticsProcessor(),
        DragonProcessor(),
    ]

    logger.info("系统启动: Keno 采集 + 遗漏 + ABC球遗漏 + 统计 + 长龙")
    await keno_collector.init()

    tasks = [asyncio.create_task(keno_collector.start(), name="keno")]
    for p in processors:
        tasks.append(asyncio.create_task(p.start(), name=p.processor_name))

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.info("收到停止信号，开始优雅停机...")
    finally:
        await keno_collector.close()
        for p in processors:
            await p.close()

        reset_draw_event()

        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

        await close_pool()
        logger.info("系统退出")


def main() -> None:
    selector = selectors.SelectSelector()
    loop_factory = lambda: asyncio.SelectorEventLoop(selector)
    try:
        asyncio.run(run(), loop_factory=loop_factory)
    except KeyboardInterrupt:
        logger.info("用户中断，系统退出")


if __name__ == "__main__":
    main()
