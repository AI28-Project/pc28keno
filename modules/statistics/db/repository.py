"""
statistics 表数据操作 - 固定 60 行，只统计当天数据，跨天重置
"""

from shared.db.connection import execute, fetch_all, fetch_one
from modules.statistics.config import TABLE_NAME


class StatisticsRepository:

    async def get_latest_draw_date(self, *, conn=None) -> str | None:
        sql = """
            SELECT draw_date
            FROM number
            ORDER BY draw_nbr DESC
            LIMIT 1
        """
        row = await fetch_one(sql, conn=conn)
        return row["draw_date"] if row and row["draw_date"] else None

    async def get_current_statistics(self, *, conn=None) -> dict[str, int]:
        sql = f"""
            SELECT statistics_content, statistics_data
            FROM {TABLE_NAME}
            ORDER BY sort_order ASC
        """
        rows = await fetch_all(sql, conn=conn)
        return {row["statistics_content"]: row["statistics_data"] for row in rows}

    async def batch_update(self, items: list[dict], *, conn=None) -> None:
        if not items:
            return
        placeholders = ", ".join(["(%s, %s)"] * len(items))
        params: list = []
        for item in items:
            params.extend([item["statistics_content"], item["statistics_data"]])
        sql = f"""
            UPDATE {TABLE_NAME} AS t
            SET statistics_data = v.data::int,
                statistics_time = CURRENT_TIMESTAMP
            FROM (VALUES {placeholders}) AS v(content, data)
            WHERE t.statistics_content = v.content
        """
        await execute(sql, tuple(params), conn=conn)

    async def rebuild_for_date(self, draw_date: str, *, conn=None) -> int:
        """
        从指定开奖日的全部 number 记录回推当日统计，返回被修正的项数。
        仅在启动时调用，运行时使用增量模式。
        """
        sql = f"""
            UPDATE {TABLE_NAME} AS target
            SET statistics_data = expected.statistics_data,
                statistics_time = CURRENT_TIMESTAMP
            FROM (
                SELECT base.statistics_content,
                       COUNT(hit_rows.draw_nbr)::int AS statistics_data
                FROM {TABLE_NAME} AS base
                LEFT JOIN (
                    SELECT draw_nbr,
                           UNNEST(ARRAY[
                               LPAD(draw_num::text, 2, '0'),
                               NULLIF(BTRIM(size_type), ''),
                               NULLIF(BTRIM(parity_type), ''),
                               NULLIF(BTRIM(dragon_tiger), ''),
                               NULLIF(BTRIM(location_type), ''),
                               NULLIF(BTRIM(extreme_type), ''),
                               NULLIF(BTRIM(pattern_type), ''),
                               NULLIF(BTRIM(combination_type), ''),
                               '3N余' || MOD(draw_num, 3),
                               '4N余' || MOD(draw_num, 4),
                               '5N余' || MOD(draw_num, 5)
                           ]) AS item
                    FROM number
                    WHERE draw_date = %s
                ) AS hit_rows ON hit_rows.item = base.statistics_content
                GROUP BY base.statistics_content
            ) AS expected
            WHERE target.statistics_content = expected.statistics_content
              AND target.statistics_data IS DISTINCT FROM expected.statistics_data
            RETURNING target.statistics_content
        """
        changed_rows = await fetch_all(sql, (draw_date,), conn=conn)
        return len(changed_rows)

    async def reset_all(self) -> None:
        sql = f"""
            UPDATE {TABLE_NAME}
            SET statistics_data = 0,
                statistics_time = CURRENT_TIMESTAMP
        """
        await execute(sql)
