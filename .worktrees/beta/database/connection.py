import asyncio
import os
from typing import Optional

import asyncpg

_POOL: Optional[asyncpg.Pool] = None


def get_database_dsn() -> str:
    dsn = os.getenv("OSMEN_DB_DSN")
    if dsn:
        return dsn
    user = os.getenv("OSMEN_DB_USER", "osmen_app")
    password = os.getenv("OSMEN_DB_PASSWORD", "osmen_app_password")
    host = os.getenv("OSMEN_DB_HOST", "localhost")
    port = os.getenv("OSMEN_DB_PORT", "5432")
    name = os.getenv("OSMEN_DB_NAME", "osmen_app")
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


def get_pool_limits() -> tuple[int, int]:
    min_size = int(os.getenv("OSMEN_DB_POOL_MIN", "1"))
    max_size = int(os.getenv("OSMEN_DB_POOL_MAX", "5"))
    return max(1, min_size), max(min_size, max_size)


async def get_pool() -> asyncpg.Pool:
    global _POOL
    if _POOL is None:
        min_size, max_size = get_pool_limits()
        _POOL = await asyncpg.create_pool(
            dsn=get_database_dsn(),
            min_size=min_size,
            max_size=max_size,
            command_timeout=60,
        )
    return _POOL


async def close_pool() -> None:
    global _POOL
    if _POOL is not None:
        await _POOL.close()
        _POOL = None


async def run_in_pool(query: str, *args):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)


if __name__ == "__main__":
    async def _test():
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1")
        await close_pool()
    asyncio.run(_test())
