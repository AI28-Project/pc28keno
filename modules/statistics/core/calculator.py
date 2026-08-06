"""
统计增量计算器 - 命中项 +1，未命中不变

与 omission 使用相同的 ALL_ITEMS 和 get_hit_items，
区别: omission 是"未命中 +1, 命中归零"，statistics 是"命中 +1, 未命中不变"。
"""

from shared.constants import ALL_ITEMS
from shared.utils import get_hit_items


def calculate_statistics(draw_record: dict, current_stats: dict) -> list[dict]:
    """计算本期命中的统计项，返回需要更新的项（仅 hit 项）"""
    hits = get_hit_items(draw_record)

    return [
        {
            "statistics_content": item,
            "statistics_data": current_stats.get(item, 0) + 1,
        }
        for item in ALL_ITEMS
        if item in hits
    ]
