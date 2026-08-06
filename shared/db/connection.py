"""
数据库连接池 + 模块级 SQL 执行工具

设计:
- 全局单例 AsyncConnectionPool，延迟初始化
- 一组 fetch_*/execute_* 模块级函数，自动从 pool 借连接
- 所有方法支持可选 conn 参数：传入则复用已有连接（多步事务），不传则借池
- transaction(conn=None): 多步原子操作上下文（自动开启 conn.transaction()）
"""

import asyncio
from contextlib import asynccontextmanager

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from shared.config import (
    DB_CONFIG, DB_POOL_MIN_SIZE, DB_POOL_MAX_SIZE,
    DB_POOL_MAX_IDLE, DB_POOL_MAX_LIFETIME,
    DB_POOL_RECONNECT_TIMEOUT, DB_POOL_TIMEOUT, DB_POOL_NUM_WORKERS,
)
from shared.logger import get_logger

logger = get_logger("db.pool")

_conninfo = (
    f"host={DB_CONFIG['host']} "
    f"port={DB_CONFIG['port']} "
    f"dbname={DB_CONFIG['dbname']} "
    f"user={DB_CONFIG['user']} "
    f"password={DB_CONFIG['password']} "
    f"sslmode={DB_CONFIG['sslmode']}"
)

_pool: AsyncConnectionPool | None = None
_pool_lock: asyncio.Lock | None = None


def _get_lock() -> asyncio.Lock:
    global _pool_lock
    if _pool_lock is None:
        _pool_lock = asyncio.Lock()
    return _pool_lock


async def get_pool() -> AsyncConnectionPool:
    global _pool
    if _pool is not None:
        return _pool

    async with _get_lock():
        if _pool is not None:
            return _pool

        pool = AsyncConnectionPool(
            conninfo=_conninfo,
            min_size=DB_POOL_MIN_SIZE,
            max_size=DB_POOL_MAX_SIZE,
            max_idle=DB_POOL_MAX_IDLE,
            max_lifetime=DB_POOL_MAX_LIFETIME,
            reconnect_timeout=DB_POOL_RECONNECT_TIMEOUT,
            timeout=DB_POOL_TIMEOUT,
            num_workers=DB_POOL_NUM_WORKERS,
            kwargs={"autocommit": True},
            open=False,
        )
        await pool.open()
        logger.info(
            f"连接池已初始化 (min={DB_POOL_MIN_SIZE}, max={DB_POOL_MAX_SIZE}, "
            f"idle={DB_POOL_MAX_IDLE}s, lifetime={DB_POOL_MAX_LIFETIME}s)"
        )
        _pool = pool
        return _pool


async def init_pool() -> None:
    """预热: 启动时主动创建连接池并填充最小连接数"""
    await get_pool()
    logger.info("连接池预热完成")


async def close_pool() -> None:
    global _pool, _pool_lock
    if _pool is not None:
        await _pool.close()
        _pool = None
        _pool_lock = None
        logger.info("连接池已关闭")


# ── SQL 执行工具 ─────────────────────────────────────────

@asynccontextmanager
async def acquire(conn=None):
    """复用已有连接 (conn 非空) 或临时从 pool 借一个"""
    if conn is not None:
        yield conn
        return
    pool = await get_pool()
    async with pool.connection() as c:
        yield c


@asynccontextmanager
async def transaction(conn=None):
    """多步原子操作上下文：自动 acquire + 开启 conn.transaction()"""
    async with acquire(conn) as c:
        async with c.transaction():
            yield c


async def fetch_all(sql: str, params: tuple | None = None, *, conn=None) -> list[dict]:
    async with acquire(conn) as c:
        async with c.cursor(row_factory=dict_row) as cur:
            await cur.execute(sql, params)
            return await cur.fetchall()


async def fetch_one(sql: str, params: tuple | None = None, *, conn=None) -> dict | None:
    async with acquire(conn) as c:
        async with c.cursor(row_factory=dict_row) as cur:
            await cur.execute(sql, params)
            return await cur.fetchone()


async def execute(sql: str, params: tuple | None = None, *, conn=None) -> None:
    async with acquire(conn) as c:
        async with c.cursor() as cur:
            await cur.execute(sql, params)


async def execute_returning(sql: str, params: tuple | None = None, *, conn=None) -> dict | None:
    """执行 INSERT ... RETURNING，返回一行（冲突跳过返回 None）"""
    async with acquire(conn) as c:
        async with c.cursor(row_factory=dict_row) as cur:
            await cur.execute(sql, params)
            return await cur.fetchone()


async def execute_many(sql: str, params_list: list[tuple], *, conn=None) -> None:
    """批量执行；空列表直接返回；自动启用 pipeline 提升吞吐"""
    if not params_list:
        return
    async with acquire(conn) as c:
        async with c.pipeline():
            async with c.cursor() as cur:
                for params in params_list:
                    await cur.execute(sql, params)
