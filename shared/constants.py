"""
公共常量 - 遗漏/统计内容列表
"""

# ── 和值 + 属性 + N余数（omission/statistics 共用 60 项） ──────

VALUE_ITEMS = [str(i).zfill(2) for i in range(28)]

ATTR_ITEMS = [
    "大", "小", "单", "双",
    "龙", "虎", "合",
    "小单", "小双", "大单", "大双",
    "小边", "中", "大边",
    "极大", "极小",
    "对子", "顺子", "豹子", "杂六",
]

REMAINDER_ITEMS = [
    f"{divisor}N余{remainder}"
    for divisor in (3, 4, 5)
    for remainder in range(divisor)
]

ALL_ITEMS = VALUE_ITEMS + ATTR_ITEMS + REMAINDER_ITEMS

# ── ABC 球遗漏（abc_omission 专用 54 项） ─────────────────────
#
# 每球 18 项 = 10 数值(0-9) + 2 大小 + 2 单双 + 4 组合(小单/小双/大单/大双)
# 规则: 0-4=小, 5-9=大; 奇=单, 偶=双
#   小单: 1,3   小双: 0,2,4   大单: 5,7,9   大双: 6,8

ABC_ATTR_ITEMS = ["大", "小", "单", "双", "小单", "小双", "大单", "大双"]

ABC_A_ITEMS = [f"a{i}" for i in range(10)] + [f"a{a}" for a in ABC_ATTR_ITEMS]
ABC_B_ITEMS = [f"b{i}" for i in range(10)] + [f"b{a}" for a in ABC_ATTR_ITEMS]
ABC_C_ITEMS = [f"c{i}" for i in range(10)] + [f"c{a}" for a in ABC_ATTR_ITEMS]
ABC_ALL_ITEMS = ABC_A_ITEMS + ABC_B_ITEMS + ABC_C_ITEMS
