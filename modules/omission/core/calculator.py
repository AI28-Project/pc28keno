"""
遗漏计算器 - 命中归0，未命中+1
"""

from shared.constants import ALL_ITEMS
from shared.utils import get_hit_items


def calculate_omission(draw_record: dict, current_omission: dict) -> list[dict]:
    """计算新的 60 项遗漏数据"""
    hits = get_hit_items(draw_record)

    return [
        {
            "missing_content": item,
            "missing_data": 0 if item in hits else current_omission.get(item, 0) + 1,
        }
        for item in ALL_ITEMS
    ]
