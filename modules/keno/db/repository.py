"""
keno 表数据操作

表结构:
    draw_nbr    bigint PK
    draw_date   varchar     -- CN 日期 (YYYY-MM-DD)
    draw_time   varchar     -- CN 时间 (HH:MM:SS)
    draw_nbrs   int[]       -- 20 个球（升序）
    draw_bonus  int
    countdown   varchar     -- 距下一期的倒计时（仅下一期行有值）
    created_at  timestamptz -- 首次见到该期的时刻（不论是 "next" 占位还是已完成）
    updated_at  timestamptz -- 首次补齐完整开奖号码时的时刻

两类写入:
    1) countdown → upcoming 骨架行（仅 draw_nbr / countdown）
    2) 完整开奖 → 仅在 draw_nbrs IS NULL 时填充；True 表示本次首次填入
"""

from shared.db.connection import execute, execute_returning, fetch_one
from modules.keno.config import KENO_TABLE


class KenoRepository:

    async def get_latest_filled_nbr(self) -> int | None:
        """查最新一期已有完整开奖号码的 draw_nbr，用于启动时初始化 _last_nbr。"""
        sql = f"""
            SELECT draw_nbr FROM {KENO_TABLE}
            WHERE draw_nbrs IS NOT NULL
            ORDER BY draw_nbr DESC LIMIT 1
        """
        row = await fetch_one(sql)
        return int(row["draw_nbr"]) if row else None

    async def upsert_upcoming(self, draw_nbr: int, countdown: str | None) -> None:
        """
        Upcoming 期号（含倒计时）。
        - 不存在 → 插入骨架行
        - 已存在 → 只刷 countdown（不动其它字段，避免覆盖已完成状态）
        """
        sql = f"""
            INSERT INTO {KENO_TABLE} (draw_nbr, countdown, created_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (draw_nbr) DO UPDATE
            SET countdown = EXCLUDED.countdown
            WHERE {KENO_TABLE}.draw_nbrs IS NULL
        """
        await execute(sql, (draw_nbr, countdown))

    async def fill_completed(
        self,
        draw_nbr: int,
        draw_date: str,
        draw_time: str,
        draw_nbrs: list[int],
        draw_bonus: int | None,
    ) -> bool:
        """
        补齐一期开奖号码。
        使用 UPSERT + WHERE draw_nbrs IS NULL 的防重条件更新，返回 True 当且仅当
        "本次调用真正把 draw_nbrs 从 NULL 填上"（RETURNING 产出一行）。
        并发多源同时写时，只有第一个返回 True，后续返回 False。
        """
        sql = f"""
            INSERT INTO {KENO_TABLE}
                (draw_nbr, draw_date, draw_time, draw_nbrs, draw_bonus,
                 countdown, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, NULL, NOW(), NOW())
            ON CONFLICT (draw_nbr) DO UPDATE
            SET draw_date  = EXCLUDED.draw_date,
                draw_time  = EXCLUDED.draw_time,
                draw_nbrs  = EXCLUDED.draw_nbrs,
                draw_bonus = EXCLUDED.draw_bonus,
                countdown  = NULL,
                updated_at = NOW()
            WHERE {KENO_TABLE}.draw_nbrs IS NULL
            RETURNING draw_nbr
        """
        row = await execute_returning(
            sql, (draw_nbr, draw_date, draw_time, draw_nbrs, draw_bonus)
        )
        return row is not None
