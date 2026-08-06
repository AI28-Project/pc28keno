"""
dragon 表数据操作
"""

from shared.db.connection import execute_many, fetch_all
from modules.dragon.config import TABLE_NAME


class DragonRepository:

    async def get_all_dragons(self) -> list[dict]:
        sql = f"""
            SELECT * FROM {TABLE_NAME}
            ORDER BY status_order ASC, sort_order ASC
        """
        return await fetch_all(sql)

    async def batch_activate_dragons(self, items: list[tuple], *, conn=None) -> None:
        if not items:
            return
        sql = f"""
            UPDATE {TABLE_NAME}
            SET dragon_count = %s,
                dragon_start = %s,
                dragon_current = %s,
                dragon_sequence = %s,
                dragon_expected = %s,
                dragon_status = '进行中',
                status_order = 0,
                dragon_time = CURRENT_TIMESTAMP
            WHERE dragon_type = %s AND dragon_content = %s
        """
        await execute_many(sql, items, conn=conn)

    async def batch_deactivate_dragons(self, keys: list[tuple], *, conn=None) -> None:
        if not keys:
            return
        sql = f"""
            UPDATE {TABLE_NAME}
            SET dragon_status = '已断开',
                status_order = 1,
                dragon_time = CURRENT_TIMESTAMP
            WHERE dragon_type = %s AND dragon_content = %s AND dragon_status = '进行中'
        """
        await execute_many(sql, keys, conn=conn)
