"""
Keno 20 球 → PC28；PlayNow 时间 BC → CN。
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from modules.keno.config import BC_TIMEZONE, CN_TIMEZONE

_BC_TZ = ZoneInfo(BC_TIMEZONE)
_CN_TZ = ZoneInfo(CN_TIMEZONE)

_GROUP1_POS = (2, 5, 8, 11, 14, 17)
_GROUP2_POS = (3, 6, 9, 12, 15, 18)
_GROUP3_POS = (4, 7, 10, 13, 16, 19)

_KENO_MIN = 1
_KENO_MAX = 80


def is_valid_keno_nums(nums: list[int]) -> bool:
    if not isinstance(nums, list) or len(nums) != 20:
        return False
    for n in nums:
        if not isinstance(n, int) or n < _KENO_MIN or n > _KENO_MAX:
            return False
    return True


def transform_keno_to_pc28(nums: list[int]) -> tuple[int, int, int, int]:
    """升序后按固定位取模得到三码。"""
    if len(nums) != 20:
        raise ValueError(f"Keno 开奖号码应为 20 个，实际 {len(nums)}")

    sorted_nums = sorted(nums)
    num1 = sum(sorted_nums[i - 1] for i in _GROUP1_POS) % 10
    num2 = sum(sorted_nums[i - 1] for i in _GROUP2_POS) % 10
    num3 = sum(sorted_nums[i - 1] for i in _GROUP3_POS) % 10
    return num1, num2, num3, num1 + num2 + num3


def _iso_no_tz_to_bc(iso_str: str) -> datetime:
    if "." in iso_str:
        iso_str = iso_str.split(".")[0]
    return datetime.fromisoformat(iso_str).replace(tzinfo=_BC_TZ)


def _month_day_ampm_to_bc(date_str: str, time_str: str) -> datetime:
    naive = datetime.strptime(f"{date_str} {time_str}", "%b %d, %Y %I:%M:%S %p")
    return naive.replace(tzinfo=_BC_TZ)


def bc_to_cn_date_time(dt_bc: datetime) -> tuple[str, str]:
    dt_cn = dt_bc.astimezone(_CN_TZ)
    return dt_cn.strftime("%Y-%m-%d"), dt_cn.strftime("%H:%M:%S")


def parse_primary_time(iso_str: str) -> tuple[str, str]:
    return bc_to_cn_date_time(_iso_no_tz_to_bc(iso_str))


def parse_fallback_time(date_str: str, time_str: str) -> tuple[str, str]:
    return bc_to_cn_date_time(_month_day_ampm_to_bc(date_str, time_str))
