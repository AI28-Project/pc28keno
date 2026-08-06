"""
下期预期值推算 - 根据长龙模式和序列推算下期应开内容(纯函数)

仅供参考，不做对错判断。
"""

from modules.dragon.core.detector import DetectResult


def _extract_period(detail: str) -> int:
    """从 detail 字段提取周期数, 格式: 'P4:大大小小' -> 4"""
    if not detail or not detail.startswith("P"):
        return 0
    colon = detail.find(":")
    if colon < 0:
        return 0
    try:
        return int(detail[1:colon])
    except ValueError:
        return 0


def calculate_expected(result: DetectResult) -> str:
    """
    根据检测结果推算下期应开内容

    返回: 单值如 "大"，或逗号分隔多值如 "小单,大双"
    """
    parts = result.sequence.split()
    if not parts:
        return ""

    if result.dragon_type == "循环":
        # 下期继续同值
        return parts[-1]

    elif result.dragon_type == "交替":
        # 下期是另一个值(倒数第二个)
        if len(parts) >= 2:
            return parts[-2]
        return parts[-1]

    elif result.dragon_type == "abb循环":
        # 通用周期模式: 从 detail 提取周期, 按模板推算下期
        period = _extract_period(result.detail)
        if period > 0 and len(parts) >= period:
            pos = result.dragon_count % period
            return parts[pos]
        # 兜底: 序列中往前一个周期对应位置的值
        return parts[-1]

    elif result.dragon_type == "赔率循环":
        # 从 detail 推断赔率组，返回该组所有可能值
        if result.detail == "高赔率":
            return "小单,大双"
        elif result.detail == "低赔率":
            return "小双,大单"
        # 兜底: 从 sequence 推断
        if "小单" in parts or "大双" in parts:
            return "小单,大双"
        if "小双" in parts or "大单" in parts:
            return "小双,大单"

    return parts[-1]
