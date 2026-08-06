"""
Keno 采集：PlayNow primary / fallback + pc28.help，幂等写入 keno + number。
"""

import asyncio

from shared.logger import get_logger
from shared.event_bus import notify_new_draw
from modules.lottery.core.calculator import calculate_all
from modules.lottery.db.repository import NumberRepository
from modules.keno.config import (
    PLAYNOW_PRIMARY_URL, PLAYNOW_FALLBACK_URL, KENO_API_URL,
    PRIMARY_INTERVAL, FALLBACK_INTERVAL, BACKUP_INTERVAL, SOURCE_NAME,
)
from modules.keno.db.repository import KenoRepository
from modules.keno.sources import (
    PlayNowHttpSource, BusinessKenoSource,
    CompletedDraw, UpcomingDraw,
)
from modules.keno.transform import (
    transform_keno_to_pc28, parse_primary_time, parse_fallback_time,
    is_valid_keno_nums,
)

logger = get_logger("keno.collector")


def _build_number_record(
    draw_nbr: int, draw_date: str, draw_time: str,
    num1: int, num2: int, num3: int, draw_sum: int,
) -> dict:
    calc_fields = calculate_all(num1, num2, num3, draw_sum)
    return {
        "draw_nbr": draw_nbr,
        "draw_date": draw_date,
        "draw_time": draw_time,
        "draw_number": f"{num1}+{num2}+{num3}",
        "draw_num": draw_sum,
        "source": SOURCE_NAME,
        **calc_fields,
    }


def _log_record(record: dict, prefix: str = "入库") -> str:
    jz = f" {record['extreme_type']}" if record["extreme_type"] else ""
    return (
        f"[{prefix}] draw_nbr={record['draw_nbr']}, "
        f"{record['draw_date']} {record['draw_time']}, "
        f"PC28={record['draw_number']}={record['draw_num']}, "
        f"{record['combination_type']}{jz} "
        f"{record['pattern_type']} "
        f"{record['location_type']} "
        f"{record['dragon_tiger']}"
    )


def _parse_primary(raw: dict) -> tuple[CompletedDraw | None, UpcomingDraw | None]:
    draw_nbr = raw.get("draw")
    nums = raw.get("num")
    draw_date_iso = raw.get("drawDate")

    completed: CompletedDraw | None = None
    if isinstance(draw_nbr, int) and draw_date_iso:
        try:
            sorted_nums = sorted(int(n) for n in nums) if isinstance(nums, list) else []
        except (TypeError, ValueError):
            sorted_nums = []
        if is_valid_keno_nums(sorted_nums):
            draw_date, draw_time = parse_primary_time(draw_date_iso)
            bonus = raw.get("bonus")
            completed = CompletedDraw(
                draw_nbr=int(draw_nbr),
                draw_date=draw_date,
                draw_time=draw_time,
                draw_nbrs=sorted_nums,
                draw_bonus=int(bonus) if bonus is not None else None,
            )

    upcoming: UpcomingDraw | None = None
    countdown = raw.get("nextKenoDraw")
    if isinstance(draw_nbr, int) and isinstance(countdown, str) and countdown:
        upcoming = UpcomingDraw(draw_nbr=int(draw_nbr) + 1, countdown=countdown)

    return completed, upcoming


def _parse_fallback(raw) -> list[CompletedDraw]:
    if isinstance(raw, dict):
        items = [raw]
    elif isinstance(raw, list):
        items = raw
    else:
        return []

    out: list[CompletedDraw] = []
    for item in items:
        try:
            draw_nbr = int(item["drawNbr"])
            nums_raw = item["drawNbrs"]
            if not isinstance(nums_raw, list) or len(nums_raw) != 20:
                continue
            sorted_nums = sorted(int(n) for n in nums_raw)
            if not is_valid_keno_nums(sorted_nums):
                continue
            draw_date, draw_time = parse_fallback_time(item["drawDate"], item["drawTime"])
            bonus = item.get("drawBonus")
            out.append(CompletedDraw(
                draw_nbr=draw_nbr,
                draw_date=draw_date,
                draw_time=draw_time,
                draw_nbrs=sorted_nums,
                draw_bonus=int(bonus) if bonus is not None else None,
            ))
        except (KeyError, ValueError, TypeError):
            continue
    return out


class KenoCollector:

    def __init__(self):
        self.keno_repo = KenoRepository()
        self.number_repo = NumberRepository()
        self.primary = PlayNowHttpSource("playnow_primary", PLAYNOW_PRIMARY_URL)
        self.fallback = PlayNowHttpSource("playnow_fallback", PLAYNOW_FALLBACK_URL)
        self.backup = BusinessKenoSource("pc28_help", KENO_API_URL)
        self._running = False
        self._last_nbr: int = 0

    def _keno_to_record(self, draw: CompletedDraw) -> dict | None:
        num1, num2, num3, draw_sum = transform_keno_to_pc28(draw.draw_nbrs)
        if not (0 <= num1 <= 9 and 0 <= num2 <= 9 and 0 <= num3 <= 9):
            logger.warning(f"[keno] 转换越界 draw_nbr={draw.draw_nbr} ({num1},{num2},{num3})")
            return None
        return _build_number_record(
            draw.draw_nbr, draw.draw_date, draw.draw_time,
            num1, num2, num3, draw_sum,
        )

    async def _persist_completed(self, draw: CompletedDraw) -> bool:
        try:
            filled = await self.keno_repo.fill_completed(
                draw_nbr=draw.draw_nbr,
                draw_date=draw.draw_date,
                draw_time=draw.draw_time,
                draw_nbrs=draw.draw_nbrs,
                draw_bonus=draw.draw_bonus,
            )
        except Exception as e:
            logger.warning(f"[keno] 写入失败 draw_nbr={draw.draw_nbr}: {e}")
            return False

        if not filled:
            return False

        record = self._keno_to_record(draw)
        if record is None:
            return False

        try:
            inserted = await self.number_repo.insert_draw(record)
        except Exception as e:
            logger.warning(f"[keno→number] 写入失败 draw_nbr={draw.draw_nbr}: {e}")
            return False

        self._last_nbr = max(self._last_nbr, draw.draw_nbr)
        if not inserted:
            return False

        notify_new_draw(record)
        logger.info(_log_record(record))
        return True

    async def _persist_upcoming(self, up: UpcomingDraw) -> None:
        try:
            await self.keno_repo.upsert_upcoming(up.draw_nbr, up.countdown)
        except Exception as e:
            logger.warning(f"[keno-upcoming] 写入失败 draw_nbr={up.draw_nbr}: {e}")

    async def _tick_primary(self) -> bool:
        raw = await self.primary.fetch_json()
        if not isinstance(raw, dict):
            return False
        try:
            completed, upcoming = _parse_primary(raw)
        except Exception as e:
            logger.warning(f"[primary] 解析异常: {e}")
            return False

        found_new = False
        if completed is not None and completed.draw_nbr > self._last_nbr:
            try:
                found_new = await self._persist_completed(completed)
            except Exception as e:
                logger.warning(f"[primary] 写入异常: {e}")
        if upcoming is not None:
            await self._persist_upcoming(upcoming)
        return found_new

    async def _tick_fallback(self) -> bool:
        raw = await self.fallback.fetch_json()
        if raw is None:
            return False
        try:
            draws = _parse_fallback(raw)
        except Exception as e:
            logger.warning(f"[fallback] 解析异常: {e}")
            return False
        if not draws:
            return False

        results = await asyncio.gather(
            *(self._persist_completed(d) for d in sorted(draws, key=lambda x: x.draw_nbr)),
            return_exceptions=True,
        )
        return any(r is True for r in results)

    async def _tick_backup(self) -> bool:
        snapshot = await self.backup.fetch_snapshot()
        if snapshot is None:
            return False

        found_new = False
        for draw in sorted(snapshot.completed, key=lambda d: d.draw_nbr):
            if draw.draw_nbr < self._last_nbr:
                continue
            try:
                ok = await self._persist_completed(draw)
            except Exception as e:
                logger.warning(f"[pc28_help] 写入异常 draw_nbr={draw.draw_nbr}: {e}")
                continue
            self._last_nbr = max(self._last_nbr, draw.draw_nbr)
            if ok:
                found_new = True

        if snapshot.upcoming is not None:
            await self._persist_upcoming(snapshot.upcoming)
        return found_new

    async def _poll(self, tick_fn, interval: float, label: str) -> None:
        while self._running:
            loop = asyncio.get_running_loop()
            start = loop.time()
            try:
                found_new = await tick_fn()
            except Exception as e:
                logger.warning(f"[{label}] tick 异常: {e}")
                found_new = False

            target_interval = 0.05 if found_new else interval
            remaining = max(0.0, target_interval - (loop.time() - start))
            if remaining > 0:
                await asyncio.sleep(remaining)

    async def init(self) -> None:
        latest = await self.keno_repo.get_latest_filled_nbr()
        if latest:
            self._last_nbr = latest
        latest_info = f"最新期号: {latest}" if latest else "暂无数据"
        logger.info(
            f"采集初始化 (primary/fallback/backup={PRIMARY_INTERVAL}s), "
            f"keno 表{latest_info}"
        )
        await asyncio.gather(
            self.primary.warmup(),
            self.fallback.warmup(),
            self.backup.warmup(),
            self._tick_primary(),
            self._tick_fallback(),
            self._tick_backup(),
            return_exceptions=True,
        )

    async def start(self) -> None:
        self._running = True
        logger.info("采集进入并发轮询 (playnow_primary + playnow_fallback + pc28_help)")
        tasks = [
            asyncio.create_task(
                self._poll(self._tick_primary, PRIMARY_INTERVAL, "primary"),
                name="keno-primary",
            ),
            asyncio.create_task(
                self._poll(self._tick_fallback, FALLBACK_INTERVAL, "fallback"),
                name="keno-fallback",
            ),
            asyncio.create_task(
                self._poll(self._tick_backup, BACKUP_INTERVAL, "pc28_help"),
                name="keno-pc28-help",
            ),
        ]
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("采集收到停止信号")
        finally:
            self._running = False
            for t in tasks:
                if not t.done():
                    t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("采集已停止")

    def stop(self) -> None:
        self._running = False

    async def close(self) -> None:
        self.stop()
        await asyncio.gather(
            self.primary.close(),
            self.fallback.close(),
            self.backup.close(),
            return_exceptions=True,
        )
        logger.info("HTTP 客户端已关闭")
