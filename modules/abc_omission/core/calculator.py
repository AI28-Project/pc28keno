"""
ABC球遗漏计算器 - 命中归0，未命中+1

每期开出 a(num1)、b(num2)、c(num3)，各取值 0-9。
每球追踪 18 项: 10 数值 + 大小 + 单双 + 小单/小双/大单/大双。
规则: 0-4=小, 5-9=大; 奇=单, 偶=双
"""

from shared.constants import ABC_ALL_ITEMS


def _ball_attrs(n: int) -> list[str]:
    """单球数值 → 命中的属性列表"""
    size = "小" if n <= 4 else "大"
    parity = "单" if n % 2 else "双"
    return [size, parity, size + parity]


def get_abc_hit_items(draw_record: dict) -> set[str]:
    """从开奖记录提取本期命中的 ABC 球项（数值 + 属性）"""
    draw_number = draw_record.get("draw_number", "")
    parts = draw_number.split("+")
    if len(parts) != 3:
        return set()

    try:
        num1, num2, num3 = int(parts[0]), int(parts[1]), int(parts[2])
    except (ValueError, TypeError):
        return set()

    hits: set[str] = set()
    for prefix, n in (("a", num1), ("b", num2), ("c", num3)):
        hits.add(f"{prefix}{n}")
        for attr in _ball_attrs(n):
            hits.add(f"{prefix}{attr}")

    return hits


def calculate_abc_omission(
    draw_record: dict, current_omission: dict[str, int],
) -> list[dict]:
    """计算新的 54 项 ABC 球遗漏数据"""
    hits = get_abc_hit_items(draw_record)

    return [
        {
            "missing_content": item,
            "missing_data": 0 if item in hits else current_omission.get(item, 0) + 1,
        }
        for item in ABC_ALL_ITEMS
    ]
