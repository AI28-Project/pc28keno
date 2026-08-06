"""
Keno 配置：PlayNow 主备 + pc28.help 备用；URL/代理自 .env。
"""

import os
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


def _require(key: str) -> str:
    v = os.getenv(key, "").strip()
    if not v:
        raise RuntimeError(f"缺少环境变量 {key}，请在根目录 .env 中配置（参考 .env.example）")
    return v


def _build_proxy_url() -> str:
    """
    由分段变量拼代理 URL：
      {scheme}://[{user}:{password}@]{host}:{port}
    """
    scheme = _require("PLAYNOW_PROXY_SCHEME").lower().rstrip(":/")
    if scheme not in ("socks5", "socks5h", "http", "https"):
        raise RuntimeError(
            "PLAYNOW_PROXY_SCHEME 仅支持 socks5 / socks5h / http / https，"
            f"当前={scheme!r}"
        )

    host = _require("PLAYNOW_PROXY_HOST")
    port = _require("PLAYNOW_PROXY_PORT")
    user = os.getenv("PLAYNOW_PROXY_USER", "").strip()
    password = os.getenv("PLAYNOW_PROXY_PASSWORD", "").strip()

    if user:
        auth = f"{quote(user, safe='')}:{quote(password, safe='')}@"
    else:
        auth = ""

    return f"{scheme}://{auth}{host}:{port}"


PLAYNOW_PRIMARY_URL = _require("PLAYNOW_PRIMARY_URL")
PLAYNOW_FALLBACK_URL = _require("PLAYNOW_FALLBACK_URL")
PLAYNOW_PROXY_URL = _build_proxy_url()
KENO_API_URL = _require("KENO_API_URL")

PRIMARY_INTERVAL = 1.0
FALLBACK_INTERVAL = 1.0
BACKUP_INTERVAL = 1.0

SOURCE_NAME = "keno"
KENO_TABLE = "keno"

BC_TIMEZONE = "America/Vancouver"
CN_TIMEZONE = "Asia/Shanghai"
