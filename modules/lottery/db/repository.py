"""
number 表数据操作
"""

from shared.db.connection import execute, execute_returning, fetch_all, fetch_one
from modules.lottery.config import TABLE_NAME

ALLOWED_DONE_FIELDS = {
    "omission_done", "statistics_done",
    "dragon_done", "abc_omission_done",
}


def _check_field(field: str) -> None:
    if field not in ALLOWED_DONE_FIELDS:
        raise ValueError(f"非法字段: {field}")


class NumberRepository:

    async def insert_draw(self, data: dict) -> bool:
        """插入开奖记录；冲突跳过时返回 False。"""
        sql = f"""
            INSERT INTO {TABLE_NAME} (
                draw_nbr, draw_date, draw_time, draw_number, draw_num,
                source, size_type, parity_type, extreme_type, combination_type,
                pattern_type, location_type, dragon_tiger
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s
            )
            ON CONFLICT (draw_nbr) DO NOTHING
            RETURNING draw_nbr
        """
        params = (
            data["draw_nbr"],
            data["draw_date"],
            data["draw_time"],
            data["draw_number"],
            data["draw_num"],
            data["source"],
            data["size_type"],
            data["parity_type"],
            data["extreme_type"],
            data["combination_type"],
            data["pattern_type"],
            data["location_type"],
            data["dragon_tiger"],
        )
        row = await execute_returning(sql, params)
        return row is not None

    async def mark_done(self, draw_nbr: int, field: str, *, conn=None) -> None:
        _check_field(field)
        sql = f"UPDATE {TABLE_NAME} SET {field} = true WHERE draw_nbr = %s"
        await execute(sql, (draw_nbr,), conn=conn)

    async def mark_done_batch(self, max_draw_nbr: int, field: str, *, conn=None) -> None:
        _check_field(field)
        sql = f"""
            UPDATE {TABLE_NAME} SET {field} = true
            WHERE draw_nbr <= %s AND ({field} IS NULL OR {field} = false)
        """
        await execute(sql, (max_draw_nbr,), conn=conn)

    async def mark_done_by_date(self, date: str, field: str, *, conn=None) -> None:
        _check_field(field)
        sql = f"""
            UPDATE {TABLE_NAME} SET {field} = true
            WHERE draw_date = %s AND ({field} IS NULL OR {field} = false)
        """
        await execute(sql, (date,), conn=conn)

    async def mark_done_not_on_date(self, date: str, field: str, *, conn=None) -> int:
        """将不属于指定日期的未处理记录标记为 done，返回影响行数。"""
        _check_field(field)
        result = await fetch_all(
            f"""
            WITH updated AS (
                UPDATE {TABLE_NAME} SET {field} = true
                WHERE ({field} IS NULL OR {field} = false)
                  AND (draw_date IS NULL OR draw_date != %s)
                RETURNING 1
            ) SELECT COUNT(*) AS cnt FROM updated
            """,
            (date,), conn=conn,
        )
        return result[0]["cnt"] if result else 0

    async def get_unprocessed(self, field: str, limit: int = 1) -> list[dict]:
        _check_field(field)
        sql = f"""
            SELECT * FROM {TABLE_NAME}
            WHERE {field} IS NULL OR {field} = false
            ORDER BY draw_nbr ASC
            LIMIT %s
        """
        return await fetch_all(sql, (limit,))

    async def get_latest_unprocessed(self, field: str) -> dict | None:
        _check_field(field)
        sql = f"""
            SELECT * FROM {TABLE_NAME}
            WHERE {field} IS NULL OR {field} = false
            ORDER BY draw_nbr DESC
            LIMIT 1
        """
        return await fetch_one(sql)

    async def get_recent_records(
        self, count: int, *, columns: list[str] | None = None,
    ) -> list[dict]:
        """取最近 N 期，按 draw_nbr 旧→新返回。"""
        cols = ", ".join(columns) if columns else "*"
        sql = f"""
            SELECT {cols} FROM (
                SELECT {cols} FROM {TABLE_NAME}
                ORDER BY draw_nbr DESC LIMIT %s
            ) sub ORDER BY draw_nbr ASC
        """
        return await fetch_all(sql, (count,))
