"""
长龙模块配置 - 表名、轮询间隔、检测参数
"""

# dragon表名
TABLE_NAME = "dragon"

# 轮询间隔(秒) - 事件驱动为主，轮询仅作兜底
POLL_INTERVAL = 1.0

# 历史数据量(期数)，用于长龙检测
HISTORY_COUNT = 100

# 所有模式最小阈值(期数)
MIN_THRESHOLD = 4

# 复合周期检测最大周期长度(人类可感知的上限, 3~5为宜)
MAX_PATTERN_PERIOD = 5

# 检测维度
DETECT_ATTRS = ["size", "parity", "combo", "dragon_tiger", "location"]

# 维度对应的number表字段名
ATTR_FIELD_MAP = {
    "size": "size_type",
    "parity": "parity_type",
    "combo": "combination_type",
    "dragon_tiger": "dragon_tiger",
    "location": "location_type",
}

# 维度对应的中文名(用于dragon_content)
ATTR_NAME_MAP = {
    "size": "大小",
    "parity": "单双",
    "combo": "组合",
    "dragon_tiger": "龙虎",
    "location": "边中",
}

# 赔率分组
ODDS_HIGH = {"小单", "大双"}  # 高赔率 4.6倍
ODDS_LOW = {"小双", "大单"}   # 低赔率 4.2倍

# 固定行定义: (dragon_type, dragon_content)
DRAGON_ROWS = [
    ("循环", "大小"),
    ("循环", "单双"),
    ("循环", "组合"),
    ("循环", "龙虎"),
    ("循环", "边中"),
    ("交替", "大小"),
    ("交替", "单双"),
    ("交替", "组合"),
    ("交替", "龙虎"),
    ("交替", "边中"),
    ("abb循环", "大小"),
    ("abb循环", "单双"),
    ("abb循环", "组合"),
    ("abb循环", "龙虎"),
    ("abb循环", "边中"),
    ("赔率循环", "赔率"),
]
