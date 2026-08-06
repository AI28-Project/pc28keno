"""
长龙处理服务 - 事件驱动，并发查询 + 一次连接批量写入
"""

import asyncio

from shared.base_processor import BaseProcessor
from shared.db.connection import transaction
from modules.dragon.config import POLL_INTERVAL, HISTORY_COUNT, ATTR_FIELD_MAP
from modules.dragon.core.detector import detect_all, DetectResult
from modules.dragon.core.predictor import calculate_expected
from modules.dragon.db.repository import DragonRepository
from modules.lottery.db.repository import NumberRepository


class DragonProcessor(BaseProcessor):

    def __init__(self):
        super().__init__(poll_interval=POLL_INTERVAL)
        self.dragon_repo = DragonRepository()
        self.number_repo = NumberRepository()

    @property
    def processor_name(self) -> str:
        return "dragon"

    @property
    def processor_display_name(self) -> str:
        return "长龙检测"

    _DRAGON_COLUMNS = ["draw_nbr"] + list(dict.fromkeys(ATTR_FIELD_MAP.values()))

    async def _process_record(self, draw_nbr: int) -> None:
        records, all_dragons = await asyncio.gather(
            self.number_repo.get_recent_records(HISTORY_COUNT, columns=self._DRAGON_COLUMNS),
            self.dragon_repo.get_all_dragons(),
        )

        if not records:
            await self.number_repo.mark_done_batch(draw_nbr, "dragon_done")
            return

        detected = detect_all(records)

        detected_map: dict[tuple[str, str], DetectResult] = {}
        for r in detected:
            detected_map[(r.dragon_type, r.dragon_content)] = r

        activate_items: list[tuple] = []
        deactivate_keys: list[tuple] = []

        for dragon in all_dragons:
            key = (dragon["dragon_type"], dragon["dragon_content"])
            old_status = dragon["dragon_status"]

            if key in detected_map:
                result = detected_map[key]
                expected = calculate_expected(result)

                activate_items.append((
                    result.dragon_count, result.start_nbr, result.current_nbr,
                    result.sequence, expected,
                    result.dragon_type, result.dragon_content,
                ))

                tag = "延续" if old_status == "进行中" else "新建"
                self.logger.info(
                    f"[{tag}] {key[0]}-{key[1]} "
                    f"{result.dragon_count}期 预期={expected}"
                )
            else:
                if old_status == "进行中":
                    deactivate_keys.append((key[0], key[1]))
                    self.logger.info(
                        f"[断开] {key[0]}-{key[1]} "
                        f"共{dragon['dragon_count']}期"
                    )

        async with transaction() as conn:
            await self.dragon_repo.batch_activate_dragons(activate_items, conn=conn)
            await self.dragon_repo.batch_deactivate_dragons(deactivate_keys, conn=conn)
            await self.number_repo.mark_done_batch(draw_nbr, "dragon_done", conn=conn)

    async def _process_once(self, record: dict | None = None) -> bool:
        if record is not None:
            await self._process_record(record["draw_nbr"])
            self.logger.info(f"[完成] draw_nbr={record['draw_nbr']} 长龙已更新")
            return True

        unprocessed = await self.number_repo.get_latest_unprocessed("dragon_done")
        if not unprocessed:
            return False

        await self._process_record(unprocessed["draw_nbr"])
        self.logger.info(f"[完成] draw_nbr={unprocessed['draw_nbr']} 长龙已更新")
        return True
