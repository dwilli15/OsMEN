import os
import time
from collections import defaultdict, deque
from typing import Optional

import redis.asyncio as redis
from fastapi import HTTPException, Request


class RateLimiter:
    """Token bucket style rate limiter with Redis or in-memory fallback."""

    def __init__(self):
        self.redis = None
        self.prefix = os.getenv("RATE_LIMIT_PREFIX", "osmen:rl")
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_password = os.getenv("REDIS_PASSWORD")
        try:
            self.redis = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                encoding="utf-8",
                decode_responses=True
            )
        except Exception:
            self.redis = None
        self._local = defaultdict(deque)

    def guard(self, scope: str, limit: int, window: int = 60):
        """Return a FastAPI dependency enforcing the provided limit."""

        async def dependency(request: Request):
            identifier = self._make_key(scope, request)
            allowed, retry_after = await self._allow(identifier, limit, window)
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={"Retry-After": str(max(1, retry_after))}
                )

        return dependency

    def _make_key(self, scope: str, request: Request) -> str:
        client = request.client.host if request.client else "unknown"
        return f"{self.prefix}:{scope}:{client}"

    async def _allow(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        if limit <= 0:
            return False, window
        if self.redis:
            try:
                current = await self.redis.incr(key)
                if current == 1:
                    await self.redis.expire(key, window)
                if current > limit:
                    ttl = await self.redis.ttl(key)
                    return False, ttl if ttl and ttl > 0 else window
                return True, 0
            except Exception:
                self.redis = None
        return self._allow_local(key, limit, window)

    def _allow_local(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        now = time.monotonic()
        bucket = self._local[key]
        while bucket and now - bucket[0] > window:
            bucket.popleft()
        if len(bucket) >= limit:
            retry = int(max(1, window - (now - bucket[0])))
            return False, retry
        bucket.append(now)
        return True, 0
