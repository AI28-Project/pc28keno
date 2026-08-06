"""
全局配置 - 数据库连接等公共配置（自根目录 .env 加载）
"""

import os
from pathlib import Path

from dotenv import load_dotenv

_root = Path(__file__).resolve().parent.parent
load_dotenv(_root / ".env")


def _require(key: str) -> str:
    v = os.getenv(key)
    if v is None or v == "":
        raise RuntimeError(f"缺少环境变量 {key}，请在项目根目录配置 .env（参考 .env.example）")
    return v


# 数据库：本地填 127.0.0.1；云 RDS 填实例地址。SSL 见 DB_SSLMODE。
_SSL_MODES = {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}
_sslmode = os.getenv("DB_SSLMODE", "prefer").strip().lower() or "prefer"
if _sslmode not in _SSL_MODES:
    raise RuntimeError(
        f"DB_SSLMODE 非法: {_sslmode!r}，可选: {', '.join(sorted(_SSL_MODES))}"
    )

DB_CONFIG = {
    "host": _require("DB_HOST"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": _require("DB_NAME"),
    "user": _require("DB_USER"),
    "password": _require("DB_PASSWORD"),
    "sslmode": _sslmode,
}

# 采集 3 路 + 4 处理器峰值
DB_POOL_MIN_SIZE = 8
DB_POOL_MAX_SIZE = 20
DB_POOL_MAX_IDLE = 600.0
DB_POOL_MAX_LIFETIME = 3600.0
DB_POOL_RECONNECT_TIMEOUT = 60.0
DB_POOL_TIMEOUT = 5.0
DB_POOL_NUM_WORKERS = 3

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
