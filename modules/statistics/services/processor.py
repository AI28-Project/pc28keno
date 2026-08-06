"""
统计处理：增量 + 启动全日 rebuild + 跨天 reset；advisory lock 幂等。
"""

from datetime import datetime, timezone, timedelta

from shared.base_processor import BaseProcessor
from shared.db.connection import transaction, fetch_one
from modules.statistics.config import POLL_INTERVAL
from modules.statistics.core.calculator import calculate_statistics
from modules.statistics.db.repository import StatisticsRepository
from modules.lottery.db.repository import NumberRepository

BJT = timezone(timedelta(hours=8))

STATS_LOCK_OFFSET = 2_000_000_000


def get_today_bjt() -> str:
    return datetime.now(BJT).strftime("%Y-%m-%d")


class StatisticsProcessor(BaseProcessor):

    def __init__(self):
        super().__init__(poll_interval=POLL_INTERVAL)
        self.stats_repo = StatisticsRepository()
        self.number_repo = NumberRepository()
        self._current_date: str = ""

    @property
    def processor_name(self) -> str:
        return "statistics"

    @property
    def processor_display_name(self) -> str:
        return "统计处理"

    async def _check_day_reset(self, draw_date: str) -> None:
        if self._current_date == draw_date:
            return

        self.logger.info(f"跨开奖日检测: {self._current_date} -> {draw_date}，重置统计数据")
        await self.stats_repo.reset_all()
        self._current_date = draw_date

    async def _on_start(self) -> None:
        today = get_today_bjt()

        marked = await self.number_repo.mark_done_not_on_date(today, "statistics_done")
        if marked > 0:
            self.logger.info(f"[启动] 跳过 {marked} 条非当天记录")

        latest_date = await self.stats_repo.get_latest_draw_date()
        if latest_date is None:
            self._current_date = today
            self.logger.info(f"当前开奖日: {self._current_date}，暂无开奖记录")
            return

        async with transaction() as conn:
            changed_count = await self.stats_repo.rebuild_for_date(latest_date, conn=conn)
            await self.number_repo.mark_done_by_date(latest_date, "statistics_done", conn=conn)

        self._current_date = latest_date
        self.logger.info(
            f"[启动回推] draw_date={self._current_date} 统计已按当天开奖重建，修正{changed_count}项"
        )

    async def _process_once(self, record: dict | None = None) -> bool:
        if record is None:
            records = await self.number_repo.get_unprocessed("statistics_done", limit=1)
            if not records:
                return False
            record = records[0]

        draw_nbr = record["draw_nbr"]
        draw_date = record.get("draw_date") or get_today_bjt()

        today = get_today_bjt()
        if draw_date != self._current_date and draw_date != today:
            await self.number_repo.mark_done(draw_nbr, "statistics_done")
            return True

        await self._check_day_reset(draw_date)

        try:
            async with transaction() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "SELECT pg_advisory_xact_lock(%s)",
                        (draw_nbr + STATS_LOCK_OFFSET,),
                    )

                done_row = await fetch_one(
                    "SELECT statistics_done FROM number WHERE draw_nbr = %s",
                    (draw_nbr,), conn=conn,
                )
                if done_row and done_row.get("statistics_done"):
                    return True

                current = await self.stats_repo.get_current_statistics(conn=conn)
                items = calculate_statistics(record, current)
                await self.stats_repo.batch_update(items, conn=conn)
                await self.number_repo.mark_done(draw_nbr, "statistics_done", conn=conn)

            self.logger.info(f"[完成] draw_nbr={draw_nbr} 统计已更新 ({len(items)}项命中)")
        except Exception as e:
            self.logger.error(f"draw_nbr={draw_nbr} 统计处理失败: {e}")
            return False

        return True
