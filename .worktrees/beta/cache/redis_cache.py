import json
import os
from typing import Any, Awaitable, Callable, Optional

import redis.asyncio as redis

_redis_client: Optional[redis.Redis] = None


async def get_client() -> Optional[redis.Redis]:
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    host = os.getenv("REDIS_HOST", "redis")
    port = int(os.getenv("REDIS_PORT", "6379"))
    password = os.getenv("REDIS_PASSWORD") or None
    db = int(os.getenv("REDIS_CACHE_DB", "0"))
    try:
        _redis_client = redis.Redis(host=host, port=port, password=password, db=db, encoding="utf-8", decode_responses=True)
        await _redis_client.ping()
    except Exception:
        _redis_client = None
    return _redis_client


async def cache_json(key: str, compute: Callable[[], Awaitable[Any]], ttl: Optional[int] = None) -> Any:
    ttl = ttl or int(os.getenv("REDIS_CACHE_TTL_SECONDS", "60"))
    client = await get_client()
    if client is None:
        return await compute()
    cached = await client.get(key)
    if cached:
        return json.loads(cached)
    result = await compute()
    await client.set(key, json.dumps(result), ex=ttl)
    return result
