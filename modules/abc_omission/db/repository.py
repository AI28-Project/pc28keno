"""
abc_omission 表数据操作 - 固定 54 行，每次开奖只更新 missing_data 和 missed_time

54 项 = 3 球 × (10 数值 + 大/小 + 单/双 + 小单/小双/大单/大双)
"""

from shared.db.connection import execute, fetch_all
from modules.abc_omission.config import TABLE_NAME


class ABCOmissionRepository:

    async def get_current_omission(self, *, conn=None) -> dict[str, int]:
        sql = f"""
            SELECT missing_content, missing_data
            FROM {TABLE_NAME}
            ORDER BY sort_order ASC
        """
        rows = await fetch_all(sql, conn=conn)
        return {row["missing_content"]: row["missing_data"] for row in rows}

    async def rebuild_from_processed_numbers(self, *, conn=None) -> int:
        """
        从已完成 ABC 遗漏处理的 number 历史回推当前遗漏，返回被修正的项数。

        对每期 draw_number "n1+n2+n3" 展开为最多 12 个命中项（每球: 数值+大小+单双+组合），
        找每项最后一次命中的期号，再统计其后的已处理期数。
        """
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
                               n1::int AS a, n2::int AS b, n3::int AS c
                        FROM (
                            SELECT draw_nbr,
                                   SPLIT_PART(draw_number, '+', 1) AS n1,
                                   SPLIT_PART(draw_number, '+', 2) AS n2,
                                   SPLIT_PART(draw_number, '+', 3) AS n3
                            FROM number
                            WHERE abc_omission_done IS TRUE
                              AND draw_number LIKE '%+%+%'
                        ) AS sp
                    ) AS nums,
                    LATERAL (VALUES
                        ('a' || a),
                        ('a' || CASE WHEN a <= 4 THEN '小' ELSE '大' END),
                        ('a' || CASE WHEN a % 2 = 1 THEN '单' ELSE '双' END),
                        ('a' || CASE WHEN a <= 4 THEN '小' ELSE '大' END
                             || CASE WHEN a % 2 = 1 THEN '单' ELSE '双' END),
                        ('b' || b),
                        ('b' || CASE WHEN b <= 4 THEN '小' ELSE '大' END),
                        ('b' || CASE WHEN b % 2 = 1 THEN '单' ELSE '双' END),
                        ('b' || CASE WHEN b <= 4 THEN '小' ELSE '大' END
                             || CASE WHEN b % 2 = 1 THEN '单' ELSE '双' END),
                        ('c' || c),
                        ('c' || CASE WHEN c <= 4 THEN '小' ELSE '大' END),
                        ('c' || CASE WHEN c % 2 = 1 THEN '单' ELSE '双' END),
                        ('c' || CASE WHEN c <= 4 THEN '小' ELSE '大' END
                             || CASE WHEN c % 2 = 1 THEN '单' ELSE '双' END)
                    ) AS v(item)
                    GROUP BY item
                ) AS last_hits ON last_hits.item = base.missing_content
                LEFT JOIN number AS n
                  ON n.abc_omission_done IS TRUE
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
