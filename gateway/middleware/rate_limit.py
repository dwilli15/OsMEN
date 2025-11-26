#!/usr/bin/env python3
"""
OsMEN Rate Limiting Middleware
Production-grade rate limiting with multiple strategies
"""

import time
import asyncio
import hashlib
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional, Tuple
from functools import wraps
import json

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_second: float = 10.0
    requests_per_minute: float = 100.0
    requests_per_hour: float = 1000.0
    burst_size: int = 20
    enabled: bool = True
    
    # Per-endpoint customization
    endpoint_overrides: Dict[str, Dict[str, float]] = None
    
    # Exempt paths (no rate limiting)
    exempt_paths: list = None
    
    def __post_init__(self):
        if self.endpoint_overrides is None:
            self.endpoint_overrides = {}
        if self.exempt_paths is None:
            self.exempt_paths = ["/health", "/health/live", "/health/ready", "/metrics"]


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    remaining: int
    reset_at: datetime
    retry_after: Optional[float] = None
    limit: int = 0
    
    def to_headers(self) -> Dict[str, str]:
        """Generate rate limit headers."""
        return {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(max(0, self.remaining)),
            "X-RateLimit-Reset": str(int(self.reset_at.timestamp())),
            **({"Retry-After": str(int(self.retry_after))} if self.retry_after else {})
        }


class RateLimitStrategy(ABC):
    """Abstract base class for rate limiting strategies."""
    
    @abstractmethod
    def check(self, key: str, config: RateLimitConfig) -> RateLimitResult:
        """Check if request should be allowed."""
        pass
    
    @abstractmethod
    def reset(self, key: str):
        """Reset rate limit for a key."""
        pass


class TokenBucketStrategy(RateLimitStrategy):
    """
    Token bucket rate limiting.
    Allows bursts while maintaining average rate.
    """
    
    def __init__(self):
        # {key: (tokens, last_refill_time)}
        self._buckets: Dict[str, Tuple[float, float]] = defaultdict(lambda: (0.0, 0.0))
        self._lock = asyncio.Lock() if asyncio.get_event_loop().is_running() else None
    
    def check(self, key: str, config: RateLimitConfig) -> RateLimitResult:
        current_time = time.time()
        tokens, last_refill = self._buckets[key]
        
        # Calculate tokens to add since last request
        time_passed = current_time - last_refill if last_refill > 0 else 0
        tokens_to_add = time_passed * config.requests_per_second
        tokens = min(config.burst_size, tokens + tokens_to_add)
        
        if tokens >= 1:
            # Allow request, consume one token
            tokens -= 1
            self._buckets[key] = (tokens, current_time)
            
            return RateLimitResult(
                allowed=True,
                remaining=int(tokens),
                reset_at=datetime.utcnow() + timedelta(seconds=1/config.requests_per_second),
                limit=config.burst_size
            )
        else:
            # Deny request
            time_until_token = (1 - tokens) / config.requests_per_second
            self._buckets[key] = (tokens, current_time)
            
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=datetime.utcnow() + timedelta(seconds=time_until_token),
                retry_after=time_until_token,
                limit=config.burst_size
            )
    
    def reset(self, key: str):
        if key in self._buckets:
            del self._buckets[key]


class SlidingWindowStrategy(RateLimitStrategy):
    """
    Sliding window rate limiting.
    More accurate than fixed windows, prevents burst at window boundaries.
    """
    
    def __init__(self, window_size: int = 60):
        self.window_size = window_size
        # {key: list of timestamps}
        self._requests: Dict[str, list] = defaultdict(list)
    
    def check(self, key: str, config: RateLimitConfig) -> RateLimitResult:
        current_time = time.time()
        window_start = current_time - self.window_size
        
        # Remove old requests
        self._requests[key] = [t for t in self._requests[key] if t > window_start]
        
        limit = int(config.requests_per_minute if self.window_size == 60 else config.requests_per_hour)
        current_count = len(self._requests[key])
        
        if current_count < limit:
            # Allow request
            self._requests[key].append(current_time)
            
            return RateLimitResult(
                allowed=True,
                remaining=limit - current_count - 1,
                reset_at=datetime.utcnow() + timedelta(seconds=self.window_size),
                limit=limit
            )
        else:
            # Deny request
            oldest_request = min(self._requests[key]) if self._requests[key] else current_time
            retry_after = oldest_request + self.window_size - current_time
            
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=datetime.utcnow() + timedelta(seconds=retry_after),
                retry_after=max(0, retry_after),
                limit=limit
            )
    
    def reset(self, key: str):
        if key in self._requests:
            del self._requests[key]


class FixedWindowStrategy(RateLimitStrategy):
    """
    Fixed window rate limiting.
    Simple and memory efficient, but allows bursts at window boundaries.
    """
    
    def __init__(self, window_size: int = 60):
        self.window_size = window_size
        # {key: (count, window_start)}
        self._windows: Dict[str, Tuple[int, float]] = {}
    
    def _get_window_start(self, current_time: float) -> float:
        return (current_time // self.window_size) * self.window_size
    
    def check(self, key: str, config: RateLimitConfig) -> RateLimitResult:
        current_time = time.time()
        window_start = self._get_window_start(current_time)
        
        if key not in self._windows or self._windows[key][1] != window_start:
            # New window
            self._windows[key] = (0, window_start)
        
        count, _ = self._windows[key]
        limit = int(config.requests_per_minute if self.window_size == 60 else config.requests_per_hour)
        
        if count < limit:
            # Allow request
            self._windows[key] = (count + 1, window_start)
            
            return RateLimitResult(
                allowed=True,
                remaining=limit - count - 1,
                reset_at=datetime.fromtimestamp(window_start + self.window_size),
                limit=limit
            )
        else:
            # Deny request
            retry_after = window_start + self.window_size - current_time
            
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=datetime.fromtimestamp(window_start + self.window_size),
                retry_after=retry_after,
                limit=limit
            )
    
    def reset(self, key: str):
        if key in self._windows:
            del self._windows[key]


class RateLimiter:
    """
    Main rate limiter with multiple strategies.
    
    Usage:
        limiter = RateLimiter()
        
        # FastAPI middleware
        @app.middleware("http")
        async def rate_limit_middleware(request, call_next):
            result = limiter.check(request)
            if not result.allowed:
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded"},
                    headers=result.to_headers()
                )
            response = await call_next(request)
            for key, value in result.to_headers().items():
                response.headers[key] = value
            return response
    """
    
    def __init__(
        self,
        config: Optional[RateLimitConfig] = None,
        strategies: Optional[Dict[str, RateLimitStrategy]] = None
    ):
        self.config = config or RateLimitConfig()
        
        # Default strategies
        self.strategies = strategies or {
            "burst": TokenBucketStrategy(),
            "minute": SlidingWindowStrategy(window_size=60),
            "hour": FixedWindowStrategy(window_size=3600)
        }
        
        # Statistics
        self._stats = {
            "total_requests": 0,
            "allowed_requests": 0,
            "denied_requests": 0,
            "by_key": defaultdict(lambda: {"allowed": 0, "denied": 0})
        }
    
    def _get_key(self, request: Any, key_func: Optional[Callable] = None) -> str:
        """Extract rate limit key from request."""
        if key_func:
            return key_func(request)
        
        # Default: use IP address
        if hasattr(request, "client") and request.client:
            client_ip = request.client.host
        elif hasattr(request, "remote_addr"):
            client_ip = request.remote_addr
        else:
            client_ip = "unknown"
        
        # Include user ID if authenticated
        user_id = None
        if hasattr(request, "state") and hasattr(request.state, "user"):
            user_id = getattr(request.state.user, "id", None)
        
        if user_id:
            return f"user:{user_id}"
        return f"ip:{client_ip}"
    
    def _get_endpoint_config(self, path: str) -> RateLimitConfig:
        """Get rate limit config for specific endpoint."""
        for pattern, overrides in self.config.endpoint_overrides.items():
            if path.startswith(pattern) or pattern == path:
                # Create new config with overrides
                return RateLimitConfig(
                    requests_per_second=overrides.get("rps", self.config.requests_per_second),
                    requests_per_minute=overrides.get("rpm", self.config.requests_per_minute),
                    requests_per_hour=overrides.get("rph", self.config.requests_per_hour),
                    burst_size=overrides.get("burst", self.config.burst_size),
                    enabled=self.config.enabled,
                    exempt_paths=self.config.exempt_paths
                )
        return self.config
    
    def check(
        self,
        request: Any,
        key_func: Optional[Callable] = None
    ) -> RateLimitResult:
        """
        Check if request should be rate limited.
        
        Args:
            request: The incoming request object
            key_func: Optional function to extract rate limit key
        
        Returns:
            RateLimitResult with allowed status and headers
        """
        self._stats["total_requests"] += 1
        
        if not self.config.enabled:
            return RateLimitResult(
                allowed=True,
                remaining=999,
                reset_at=datetime.utcnow() + timedelta(hours=1),
                limit=999
            )
        
        # Get request path
        path = getattr(request, "url", None)
        if path:
            path = str(path.path) if hasattr(path, "path") else str(path)
        else:
            path = getattr(request, "path", "/")
        
        # Check exempt paths
        if path in self.config.exempt_paths:
            return RateLimitResult(
                allowed=True,
                remaining=999,
                reset_at=datetime.utcnow() + timedelta(hours=1),
                limit=999
            )
        
        # Get rate limit key
        key = self._get_key(request, key_func)
        endpoint_config = self._get_endpoint_config(path)
        
        # Check all strategies (must pass all)
        results = []
        for strategy_name, strategy in self.strategies.items():
            result = strategy.check(f"{key}:{strategy_name}", endpoint_config)
            results.append(result)
            
            if not result.allowed:
                self._stats["denied_requests"] += 1
                self._stats["by_key"][key]["denied"] += 1
                logger.warning(
                    f"Rate limit exceeded for {key} on {path} ({strategy_name})"
                )
                return result
        
        # All strategies passed
        self._stats["allowed_requests"] += 1
        self._stats["by_key"][key]["allowed"] += 1
        
        # Return most restrictive result
        return min(results, key=lambda r: r.remaining)
    
    def reset(self, key: str):
        """Reset all rate limits for a key."""
        for strategy_name, strategy in self.strategies.items():
            strategy.reset(f"{key}:{strategy_name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        return {
            "total_requests": self._stats["total_requests"],
            "allowed_requests": self._stats["allowed_requests"],
            "denied_requests": self._stats["denied_requests"],
            "denial_rate": (
                self._stats["denied_requests"] / self._stats["total_requests"]
                if self._stats["total_requests"] > 0 else 0
            ),
            "top_denied": sorted(
                [(k, v["denied"]) for k, v in self._stats["by_key"].items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(config: Optional[RateLimitConfig] = None) -> RateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(config)
    return _rate_limiter


def rate_limit(
    requests_per_second: Optional[float] = None,
    requests_per_minute: Optional[float] = None,
    burst_size: Optional[int] = None,
    key_func: Optional[Callable] = None
):
    """
    Decorator for rate limiting individual functions.
    
    Usage:
        @rate_limit(requests_per_second=5, burst_size=10)
        async def my_endpoint():
            pass
    """
    def decorator(func):
        # Create dedicated limiter for this endpoint
        config = RateLimitConfig(
            requests_per_second=requests_per_second or 10,
            requests_per_minute=requests_per_minute or 100,
            burst_size=burst_size or 20
        )
        limiter = RateLimiter(config)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Try to find request in args
            request = None
            for arg in args:
                if hasattr(arg, "client") or hasattr(arg, "remote_addr"):
                    request = arg
                    break
            
            if request:
                result = limiter.check(request, key_func)
                if not result.allowed:
                    # For async functions, raise an exception
                    raise RateLimitExceeded(result)
            
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if hasattr(arg, "client") or hasattr(arg, "remote_addr"):
                    request = arg
                    break
            
            if request:
                result = limiter.check(request, key_func)
                if not result.allowed:
                    raise RateLimitExceeded(result)
            
            return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, result: RateLimitResult):
        self.result = result
        super().__init__(f"Rate limit exceeded. Retry after {result.retry_after}s")


# FastAPI integration
def create_rate_limit_middleware(config: Optional[RateLimitConfig] = None):
    """
    Create FastAPI rate limiting middleware.
    
    Usage:
        from fastapi import FastAPI
        from gateway.middleware.rate_limit import create_rate_limit_middleware
        
        app = FastAPI()
        app.middleware("http")(create_rate_limit_middleware())
    """
    limiter = get_rate_limiter(config)
    
    async def middleware(request, call_next):
        result = limiter.check(request)
        
        if not result.allowed:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": result.retry_after,
                    "message": f"Too many requests. Please wait {int(result.retry_after or 1)} seconds."
                },
                headers=result.to_headers()
            )
        
        response = await call_next(request)
        
        # Add rate limit headers to response
        for key, value in result.to_headers().items():
            response.headers[key] = value
        
        return response
    
    return middleware


if __name__ == "__main__":
    # Demo
    import sys
    
    # Create a mock request
    class MockRequest:
        def __init__(self, ip: str, path: str = "/api/test"):
            self.client = type("Client", (), {"host": ip})()
            self.url = type("URL", (), {"path": path})()
    
    # Test rate limiter
    config = RateLimitConfig(
        requests_per_second=2,
        burst_size=5
    )
    limiter = RateLimiter(config)
    
    print("Testing rate limiter...")
    print("-" * 40)
    
    request = MockRequest("192.168.1.1")
    
    for i in range(10):
        result = limiter.check(request)
        status = "✅ ALLOWED" if result.allowed else "❌ DENIED"
        print(f"Request {i+1}: {status} (remaining: {result.remaining})")
        
        if not result.allowed:
            print(f"   Retry after: {result.retry_after:.2f}s")
    
    print("-" * 40)
    print("\nStatistics:")
    stats = limiter.get_stats()
    print(f"  Total: {stats['total_requests']}")
    print(f"  Allowed: {stats['allowed_requests']}")
    print(f"  Denied: {stats['denied_requests']}")
    print(f"  Denial Rate: {stats['denial_rate']:.1%}")
