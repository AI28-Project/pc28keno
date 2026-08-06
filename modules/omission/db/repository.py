"""
omission 表数据操作 - 固定 60 行，每次开奖只更新 missing_data 和 missed_time
"""

from shared.db.connection import execute, fetch_all
from modules.omission.config import TABLE_NAME


class OmissionRepository:

    async def get_current_omission(self, *, conn=None) -> dict[str, int]:
        sql = f"""
            SELECT missing_content, missing_data
            FROM {TABLE_NAME}
            ORDER BY sort_order ASC
        """
        rows = await fetch_all(sql, conn=conn)
        return {row["missing_content"]: row["missing_data"] for row in rows}

    async def rebuild_from_processed_numbers(self, *, conn=None) -> int:
        """从已完成遗漏处理的 number 历史回推当前遗漏，返回被修正的项数。"""
        sql = f"""
            UPDATE {TABLE_NAME} AS target
            SET missing_data = expected.missing_data,
                missed_time = CURRENT_TIMESTAMP
            FROM (
                SELECT base.missing_content,
                       COUNT(n.draw_nbr)::int AS missing_data
                FROM {TABLE_NAME} AS base
                LEFT JOIN (
                    SELECT item, MAX(draw_nbr) AS last_hit_draw_nbr
                    FROM (
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
                        WHERE omission_done IS TRUE
                    ) AS hit_rows
                    WHERE item IS NOT NULL
                    GROUP BY item
                ) AS last_hits ON last_hits.item = base.missing_content
                LEFT JOIN number AS n
                  ON n.omission_done IS TRUE
                 AND (
                     last_hits.last_hit_draw_nbr IS NULL
                     OR n.draw_nbr > last_hits.last_hit_draw_nbr
                 )
                GROUP BY base.missing_content
            ) AS expected
            WHERE target.missing_content = expected.missing_content
              AND target.missing_data IS DISTINCT FROM expected.missing_data
            RETURNING target.missing_content
        """
        changed_rows = await fetch_all(sql, conn=conn)
        return len(changed_rows)

    async def batch_update(self, items: list[dict], *, conn=None) -> None:
        if not items:
            return
        placeholders = ", ".join(["(%s, %s)"] * len(items))
        params: list = []
        for item in items:
            params.extend([item["missing_content"], item["missing_data"]])
        sql = f"""
            UPDATE {TABLE_NAME} AS t
            SET missing_data = v.data::int,
                missed_time = CURRENT_TIMESTAMP
            FROM (VALUES {placeholders}) AS v(content, data)
            WHERE t.missing_content = v.content
        """
        await execute(sql, tuple(params), conn=conn)
