"""
公共工具函数 - omission和statistics共用的命中项计算
"""


def get_hit_items(draw_record: dict) -> set:
    """根据开奖记录获取本期命中的项集合"""
    hits = set()

    draw_num = int(draw_record["draw_num"])
    hits.add(str(draw_num).zfill(2))
    for divisor in (3, 4, 5):
        hits.add(f"{divisor}N余{draw_num % divisor}")

    for field in (
        "size_type", "parity_type", "dragon_tiger", "location_type",
        "extreme_type", "pattern_type", "combination_type",
    ):
        value = draw_record.get(field)
        if value and str(value).strip():
            hits.add(str(value).strip())

    return hits
