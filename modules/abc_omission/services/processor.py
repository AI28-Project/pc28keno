"""
ABC 球遗漏（54 项）：advisory lock + 二次校验 omission 同款幂等。
"""

from shared.base_processor import BaseProcessor
from shared.db.connection import transaction, fetch_one
from modules.abc_omission.config import POLL_INTERVAL
from modules.abc_omission.core.calculator import calculate_abc_omission
from modules.abc_omission.db.repository import ABCOmissionRepository
from modules.lottery.db.repository import NumberRepository

ABC_LOCK_OFFSET = 1_000_000_000


class ABCOmissionProcessor(BaseProcessor):

    def __init__(self):
        super().__init__(poll_interval=POLL_INTERVAL)
        self.abc_repo = ABCOmissionRepository()
        self.number_repo = NumberRepository()

    @property
    def processor_name(self) -> str:
        return "abc_omission"

    @property
    def processor_display_name(self) -> str:
        return "ABC球遗漏处理"

    async def _on_start(self) -> None:
        async with transaction() as conn:
            changed_count = await self.abc_repo.rebuild_from_processed_numbers(conn=conn)

        self.logger.info(f"[启动回推] ABC球遗漏已按已处理开奖重建，修正{changed_count}项")

    async def _process_once(self, record: dict | None = None) -> bool:
        if record is None:
            records = await self.number_repo.get_unprocessed("abc_omission_done", limit=1)
            if not records:
                return False
            record = records[0]

        draw_nbr = record["draw_nbr"]

        try:
            async with transaction() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "SELECT pg_advisory_xact_lock(%s)",
                        (draw_nbr + ABC_LOCK_OFFSET,),
                    )

                done_row = await fetch_one(
                    "SELECT abc_omission_done FROM number WHERE draw_nbr = %s",
                    (draw_nbr,), conn=conn,
                )
                if done_row and done_row.get("abc_omission_done"):
                    return True

                current = await self.abc_repo.get_current_omission(conn=conn)
                items = calculate_abc_omission(record, current)
                await self.abc_repo.batch_update(items, conn=conn)
                await self.number_repo.mark_done(draw_nbr, "abc_omission_done", conn=conn)

            self.logger.info(f"[完成] draw_nbr={draw_nbr} ABC球遗漏已更新")
        except Exception as e:
            self.logger.error(f"draw_nbr={draw_nbr} ABC球遗漏处理失败: {e}")
            return False

        return True
