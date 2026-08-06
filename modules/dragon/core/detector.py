"""
长龙检测器 - 4种模式检测算法(纯函数)

检测维度: 大小(size)、单双(parity)、组合(combo)、龙虎(dragon_tiger)、边中(location)
检测方法: 从最新期(列表末尾)往前回溯，找到最长匹配序列

每行独立检测，每行独立判断是否>=阈值。

输入: records 列表，每条为 number 表 dict，按 draw_nbr 升序排列(旧->新)
输出: DetectResult 列表
"""

from dataclasses import dataclass

from modules.dragon.config import (
    MIN_THRESHOLD, DETECT_ATTRS, ATTR_FIELD_MAP, ATTR_NAME_MAP,
    ODDS_HIGH, ODDS_LOW, MAX_PATTERN_PERIOD,
)


@dataclass
class DetectResult:
    """检测结果"""
    dragon_type: str      # 循环/交替/abb循环/赔率循环
    dragon_content: str   # 大小/单双/组合/赔率
    dragon_count: int     # 连续期数
    start_nbr: int        # 起始期号
    current_nbr: int      # 当前期号
    sequence: str         # 序列详情: "大 大 大 大"
    detail: str = ""      # 附加信息(赔率循环用: "高赔率"/"低赔率")


def _get_attr_value(record: dict, attr: str) -> str:
    """从 number 记录中获取指定维度的值"""
    field_name = ATTR_FIELD_MAP[attr]
    return str(record.get(field_name, "")).strip()


# ----------------------------------------------------------
#  单类循环: 同一个值连续重复
# ----------------------------------------------------------
def _detect_repeat(records: list[dict], attr: str) -> DetectResult | None:
    """
    检测单类循环模式
    示例: 大 大 大 大 / 小单 小单 小单 小单
    """
    if len(records) < MIN_THRESHOLD:
        return None

    last_idx = len(records) - 1
    target = _get_attr_value(records[last_idx], attr)
    if not target:
        return None

    count = 1
    for i in range(last_idx - 1, -1, -1):
        if _get_attr_value(records[i], attr) == target:
            count += 1
        else:
            break

    if count < MIN_THRESHOLD:
        return None

    start_idx = last_idx - count + 1
    seq = " ".join(target for _ in range(count))
    return DetectResult(
        dragon_type="循环",
        dragon_content=ATTR_NAME_MAP[attr],
        dragon_count=count,
        start_nbr=records[start_idx]["draw_nbr"],
        current_nbr=records[last_idx]["draw_nbr"],
        sequence=seq,
    )


# ----------------------------------------------------------
#  单类交替: 两个值交替出现
# ----------------------------------------------------------
def _detect_alternate(records: list[dict], attr: str) -> DetectResult | None:
    """
    检测单类交替模式
    示例: 大 小 大 小 / 小单 小双 小单 小双
    """
    if len(records) < MIN_THRESHOLD:
        return None

    last_idx = len(records) - 1
    val_a = _get_attr_value(records[last_idx], attr)       # 最新期
    val_b = _get_attr_value(records[last_idx - 1], attr)   # 上一期

    if not val_a or not val_b or val_a == val_b:
        return None

    count = 2
    details = [val_b, val_a]

    for i in range(last_idx - 2, -1, -1):
        pos = last_idx - i
        expected = val_a if pos % 2 == 0 else val_b
        current = _get_attr_value(records[i], attr)

        if current == expected:
            count += 1
            details.insert(0, current)
        else:
            break

    if count < MIN_THRESHOLD:
        return None

    start_idx = last_idx - count + 1
    return DetectResult(
        dragon_type="交替",
        dragon_content=ATTR_NAME_MAP[attr],
        dragon_count=count,
        start_nbr=records[start_idx]["draw_nbr"],
        current_nbr=records[last_idx]["draw_nbr"],
        sequence=" ".join(details),
    )


# ----------------------------------------------------------
#  通用复合周期检测: 自动发现周期3~MAX的任意重复模式
#  覆盖: ABB, AABB, ABBA, AAABB 等所有复合规律
#
#  人类逻辑: 从末尾往前找龙起点, 从起点往末尾按固定步长切组
#    1. 尝试每个候选起点(从末尾往前推)
#    2. 从起点取P个值作为模板
#    3. 后续每P个一组必须和模板严格一致
#    4. 末尾残余必须和模板开头逐位对应
#    5. 不穷举偏移, 模板由起点决定, 唯一确定
# ----------------------------------------------------------
def _detect_pattern(records: list[dict], attr: str) -> DetectResult | None:
    """
    通用周期模式检测器

    对每个候选周期P(3~MAX):
      从末尾往前搜索龙起点, 从起点开始按P个一组切分:
        起点的前P个值 = 模板
        后续每组必须和模板严格一致
        末尾不足一组的残余必须和模板开头逐位对应
      模板只允许2种不同的值, 且须至少2个完整周期
      排除退化模式(全相同/纯交替)
    取匹配期数最长的(同长取短周期)。
    """
    n = len(records)
    if n < MIN_THRESHOLD:
        return None

    values = [_get_attr_value(records[i], attr) for i in range(n)]

    best_count = 0
    best_period = 0
    best_start = 0
    best_cycles = 0

    for period in range(3, MAX_PATTERN_PERIOD + 1):
        if n < period + 1:
            continue

        # 搜索龙起点: 从最远可能位置到末尾附近
        earliest = max(0, n - period * 6)
        for start in range(earliest, n - period):
            template = values[start:start + period]

            # 模板必须恰好包含2种值, 排除单值和3+值
            if len(set(template)) != 2 or _is_degenerate(template):
                continue

            # 从起点往末尾逐组验证
            full_cycles = 1
            pos = start + period
            while pos + period <= n:
                if values[pos:pos + period] == template:
                    full_cycles += 1
                    pos += period
                else:
                    break

            # 残余: pos 到末尾, 必须和模板开头逐位对应
            matched_tail = 0
            remaining = n - pos
            if remaining > 0:
                if values[pos:n] == template[:remaining]:
                    matched_tail = remaining
                else:
                    continue

            total = full_cycles * period + matched_tail

            # 龙必须延续到当前最新期
            if start + total != n:
                continue

            if total < period + 1:
                continue

            # 至少2个完整周期, 防止偶然匹配
            if full_cycles < 2:
                continue

            if (total > best_count
                    or (total == best_count and full_cycles > best_cycles)
                    or (total == best_count and full_cycles == best_cycles and period < best_period)):
                best_count = total
                best_period = period
                best_start = start
                best_cycles = full_cycles

    if best_count == 0:
        return None

    seq_values = values[best_start:]
    template = values[best_start:best_start + best_period]
    template_str = "".join(template)

    return DetectResult(
        dragon_type="abb循环",
        dragon_content=ATTR_NAME_MAP[attr],
        dragon_count=best_count,
        start_nbr=records[best_start]["draw_nbr"],
        current_nbr=records[n - 1]["draw_nbr"],
        sequence=" ".join(seq_values),
        detail=f"P{best_period}:{template_str}",
    )


def _is_degenerate(template: list[str]) -> bool:
    """
    检查模板是否是退化模式(已被循环/交替检测覆盖):
    - 可被更短周期完美整除表示: 如 ABAB(P4) 实为 AB(P2)
    - 是更短周期的前缀: 如 ABA(P3) 实为 AB交替
    """
    n = len(template)

    for p in range(1, n):
        if n % p != 0:
            continue
        if all(template[i] == template[i % p] for i in range(n)):
            return True

    # 周期2前缀: ABA, ABAB前缀等
    if n >= 3 and len(set(template)) == 2:
        a, b = template[0], template[1]
        if a != b and all(template[i] == (a if i % 2 == 0 else b) for i in range(n)):
            return True

    return False


# ----------------------------------------------------------
#  赔率循环: 按赔率分组连续出现
# ----------------------------------------------------------
def _detect_odds(records: list[dict]) -> DetectResult | None:
    """
    检测赔率循环模式
    高赔率组: 小单 + 大双 (4.6倍)
    低赔率组: 小双 + 大单 (4.2倍)

    dragon_content 统一为 "赔率"，具体高/低赔率记录在 detail 中。
    """
    if len(records) < MIN_THRESHOLD:
        return None

    last_idx = len(records) - 1
    last_combo = _get_attr_value(records[last_idx], "combo")

    if last_combo in ODDS_HIGH:
        group = ODDS_HIGH
        detail = "高赔率"
    elif last_combo in ODDS_LOW:
        group = ODDS_LOW
        detail = "低赔率"
    else:
        return None

    count = 1
    details = [last_combo]

    for i in range(last_idx - 1, -1, -1):
        combo = _get_attr_value(records[i], "combo")
        if combo in group:
            count += 1
            details.insert(0, combo)
        else:
            break

    if count < MIN_THRESHOLD:
        return None

    start_idx = last_idx - count + 1
    return DetectResult(
        dragon_type="赔率循环",
        dragon_content="赔率",
        dragon_count=count,
        start_nbr=records[start_idx]["draw_nbr"],
        current_nbr=records[last_idx]["draw_nbr"],
        sequence=" ".join(details),
        detail=detail,
    )


# ----------------------------------------------------------
#  主检测入口
# ----------------------------------------------------------
def detect_all(records: list[dict]) -> list[DetectResult]:
    """
    对历史记录执行全部独立检测，返回所有命中的长龙

    records: number 表记录列表，按 draw_nbr 升序(旧->新)
    检测路数 = len(DETECT_ATTRS) x 3种模式 + 赔率循环
    """
    if len(records) < MIN_THRESHOLD:
        return []

    results: list[DetectResult] = []

    for attr in DETECT_ATTRS:
        r = _detect_repeat(records, attr)
        if r:
            results.append(r)

        r = _detect_alternate(records, attr)
        if r:
            results.append(r)

        r = _detect_pattern(records, attr)
        if r:
            results.append(r)

    # 赔率循环(第10路)
    r = _detect_odds(records)
    if r:
        results.append(r)

    return results
