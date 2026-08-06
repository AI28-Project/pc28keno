"""
预计算字段计算器 - 纯函数，根据开奖号码计算所有衍生字段
"""


def calc_size(draw_sum: int) -> str:
    return "大" if draw_sum >= 14 else "小"


def calc_parity(draw_sum: int) -> str:
    return "单" if draw_sum % 2 != 0 else "双"


def calc_extreme(draw_sum: int) -> str | None:
    if draw_sum >= 22:
        return "极大"
    elif draw_sum <= 5:
        return "极小"
    return None


def calc_combination(draw_sum: int) -> str:
    return calc_size(draw_sum) + calc_parity(draw_sum)


def calc_pattern(num1: int, num2: int, num3: int) -> str:
    if num1 == num2 == num3:
        return "豹子"
    if num1 == num2 or num2 == num3 or num1 == num3:
        return "对子"

    # 顺子: 支持0-9循环(如890/012/901)
    sorted_nums = sorted([num1, num2, num3])
    diff1 = sorted_nums[1] - sorted_nums[0]
    diff2 = sorted_nums[2] - sorted_nums[1]
    if (diff1 == 1 and diff2 == 1) or (diff1 == 1 and diff2 == 8) or (diff1 == 8 and diff2 == 1):
        return "顺子"

    return "杂六"


def calc_location(draw_sum: int) -> str:
    if draw_sum <= 9:
        return "小边"
    elif draw_sum <= 17:
        return "中"
    else:
        return "大边"


def calc_dragon_tiger(num1: int, num3: int) -> str:
    if num1 > num3:
        return "龙"
    elif num1 < num3:
        return "虎"
    else:
        return "合"


def calculate_all(num1: int, num2: int, num3: int, draw_sum: int) -> dict:
    return {
        "size_type": calc_size(draw_sum),
        "parity_type": calc_parity(draw_sum),
        "extreme_type": calc_extreme(draw_sum),
        "combination_type": calc_combination(draw_sum),
        "pattern_type": calc_pattern(num1, num2, num3),
        "location_type": calc_location(draw_sum),
        "dragon_tiger": calc_dragon_tiger(num1, num3),
    }
