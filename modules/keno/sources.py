"""
开奖数据源：PlayNow（代理）+ pc28.help（直连备用）
"""

import json
from dataclasses import dataclass

import httpx

from modules.keno.config import PLAYNOW_PROXY_URL, KENO_API_URL
from modules.keno.transform import is_valid_keno_nums
from shared.logger import get_logger


@dataclass(frozen=True)
class CompletedDraw:
    draw_nbr: int
    draw_date: str        # YYYY-MM-DD (CN)
    draw_time: str        # HH:MM:SS   (CN)
    draw_nbrs: list[int]  # 20 球，升序
    draw_bonus: int | None


@dataclass(frozen=True)
class UpcomingDraw:
    draw_nbr: int
    countdown: str


@dataclass(frozen=True)
class KenoApiSnapshot:
    completed: list[CompletedDraw]
    upcoming: UpcomingDraw | None


_PLAYNOW_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.playnow.com/lottery/keno/",
    "Origin": "https://www.playnow.com",
    "sec-ch-ua": '"Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
}


class PlayNowHttpSource:
    """PlayNow 单接口客户端：代理 + HTTP/2 + 错误节流。"""

    _ERROR_LOG_INTERVAL = 60

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url
        self.logger = get_logger(f"keno.{name}")
        self._client: httpx.AsyncClient | None = None
        self._error_count: int = 0

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                verify=True,
                timeout=httpx.Timeout(connect=5.0, read=8.0, write=5.0, pool=5.0),
                headers=_PLAYNOW_HEADERS,
                proxy=PLAYNOW_PROXY_URL,
                http2=True,
                limits=httpx.Limits(
                    max_connections=4,
                    max_keepalive_connections=2,
                    keepalive_expiry=30,
                ),
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def warmup(self) -> None:
        try:
            client = self._get_client()
            resp = await client.get(self.url)
            resp.raise_for_status()
            await resp.aread()
        except Exception:
            self._record_error()
        else:
            self._log_recovered()

    async def _rebuild_client(self) -> None:
        try:
            if self._client is not None and not self._client.is_closed:
                await self._client.aclose()
        except Exception:
            pass
        self._client = None

    def _record_error(self) -> None:
        self._error_count += 1

    def _log_error_throttled(self, label: str, exc: Exception) -> None:
        cnt = self._error_count
        if cnt == 1 or cnt % self._ERROR_LOG_INTERVAL == 0:
            self.logger.warning(
                f"[{self.name}] {label} (连续第 {cnt} 次): "
                f"{type(exc).__name__}: {exc}"
            )

    def _log_recovered(self) -> None:
        if self._error_count > 0:
            self.logger.info(f"[{self.name}] 已恢复正常 (之前连续失败 {self._error_count} 次)")
            self._error_count = 0

    async def fetch_json(self):
        try:
            client = self._get_client()
            resp = await client.get(self.url)
            resp.raise_for_status()
            data = resp.json()
            self._log_recovered()
            return data
        except (json.JSONDecodeError, httpx.DecodingError) as e:
            self._record_error()
            self._log_error_throttled("响应解析失败", e)
            return None
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as e:
            self._record_error()
            self._log_error_throttled("请求超时", e)
            return None
        except httpx.ConnectError as e:
            self._record_error()
            self._log_error_throttled("连接失败(代理或目标不可达)", e)
            return None
        except httpx.HTTPStatusError as e:
            self._record_error()
            self._log_error_throttled(f"HTTP {e.response.status_code}", e)
            return None
        except (httpx.RemoteProtocolError, httpx.LocalProtocolError) as e:
            self._record_error()
            self._log_error_throttled("协议错误", e)
            await self._rebuild_client()
            return None
        except Exception as e:
            self._record_error()
            self._log_error_throttled("未知异常", e)
            await self._rebuild_client()
            return None


class BusinessKenoSource:
    """pc28.help Keno JSON：直连、无需代理。"""

    _ERROR_LOG_INTERVAL = 30

    def __init__(self, name: str = "pc28_help", url: str | None = None):
        self.name = name
        self.url = url or KENO_API_URL
        self.logger = get_logger(f"keno.{name}")
        self._client: httpx.AsyncClient | None = None
        self._error_count: int = 0

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                verify=True,
                timeout=httpx.Timeout(connect=5.0, read=8.0, write=5.0, pool=5.0),
                follow_redirects=True,
                limits=httpx.Limits(
                    max_connections=2,
                    max_keepalive_connections=1,
                    keepalive_expiry=60,
                ),
            )
        return self._client

    def _record_error(self) -> None:
        self._error_count += 1

    def _log_error_throttled(self, label: str, exc: Exception) -> None:
        cnt = self._error_count
        if cnt == 1 or cnt % self._ERROR_LOG_INTERVAL == 0:
            self.logger.warning(
                f"[{self.name}] {label} (连续第 {cnt} 次): "
                f"{type(exc).__name__}: {exc}"
            )

    def _log_recovered(self) -> None:
        if self._error_count > 0:
            self.logger.info(f"[{self.name}] 已恢复正常 (之前连续失败 {self._error_count} 次)")
            self._error_count = 0

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def warmup(self) -> None:
        try:
            client = self._get_client()
            resp = await client.get(self.url)
            resp.raise_for_status()
            await resp.aread()
        except Exception:
            self._record_error()
        else:
            self._log_recovered()

    def _parse_body(self, body: dict) -> KenoApiSnapshot:
        data = body.get("data")
        if not isinstance(data, list):
            return KenoApiSnapshot(completed=[], upcoming=None)

        completed: list[CompletedDraw] = []
        for item in data:
            try:
                draw_nbr = int(item["nbr"])
                nums_raw = item["nbrs"]
                if isinstance(nums_raw, str):
                    parts = [int(x) for x in nums_raw.split(",") if x.strip() != ""]
                elif isinstance(nums_raw, list):
                    parts = [int(x) for x in nums_raw]
                else:
                    continue
                sorted_nums = sorted(parts)
                if not is_valid_keno_nums(sorted_nums):
                    continue
                draw_date = str(item["date"]).strip()
                draw_time = str(item["time"]).strip()
                if not draw_date or not draw_time:
                    continue
                bonus = item.get("bonus")
                completed.append(CompletedDraw(
                    draw_nbr=draw_nbr,
                    draw_date=draw_date,
                    draw_time=draw_time,
                    draw_nbrs=sorted_nums,
                    draw_bonus=int(bonus) if bonus not in (None, "") else None,
                ))
            except (KeyError, ValueError, TypeError):
                continue

        upcoming: UpcomingDraw | None = None
        countdown = body.get("countdown")
        if completed and isinstance(countdown, str) and countdown.strip():
            latest = max(d.draw_nbr for d in completed)
            upcoming = UpcomingDraw(draw_nbr=latest + 1, countdown=countdown.strip())

        return KenoApiSnapshot(completed=completed, upcoming=upcoming)

    async def fetch_snapshot(self) -> KenoApiSnapshot | None:
        try:
            client = self._get_client()
            resp = await client.get(self.url)
            resp.raise_for_status()
            body = resp.json()
            self._log_recovered()
        except (json.JSONDecodeError, httpx.DecodingError) as e:
            self._record_error()
            self._log_error_throttled("响应解析失败", e)
            return None
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as e:
            self._record_error()
            self._log_error_throttled("请求超时", e)
            return None
        except httpx.ConnectError as e:
            self._record_error()
            self._log_error_throttled("连接失败", e)
            return None
        except httpx.HTTPStatusError as e:
            self._record_error()
            self._log_error_throttled(f"HTTP {e.response.status_code}", e)
            return None
        except Exception as e:
            self._record_error()
            self._log_error_throttled("未知异常", e)
            return None

        if not isinstance(body, dict):
            return KenoApiSnapshot(completed=[], upcoming=None)
        return self._parse_body(body)
