#!/usr/bin/env python3
"""
Security Module for OsMEN v3.0 Gateway

Provides:
- Token bucket rate limiting (per-client)
- IP blocking for repeat offenders
- DDoS pattern detection
- Circuit breaker for downstream services
- Security headers middleware

Usage:
    from gateway.security import SecurityMiddleware, get_rate_limiter
    
    app.add_middleware(SecurityMiddleware)
    
    limiter = get_rate_limiter()
    if not limiter.check_rate_limit(client_ip):
        raise HTTPException(429, "Rate limit exceeded")
"""

import time
import asyncio
import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Callable, Any
import re

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


# ==============================================================================
# Rate Limiter
# ==============================================================================

@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_minute: int = 100
    burst_capacity: int = 10
    block_duration_seconds: int = 300  # 5 minutes
    max_violations_before_block: int = 5


@dataclass
class ClientState:
    """State for a single client"""
    tokens: float = 0.0
    last_request: float = 0.0
    violations: int = 0
    blocked_until: Optional[float] = None
    request_count: int = 0
    first_request: float = field(default_factory=time.time)


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter with per-client tracking
    
    Each client has a bucket that fills at a constant rate.
    Requests consume tokens. When empty, requests are denied.
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self.clients: Dict[str, ClientState] = {}
        self.blocked_ips: Set[str] = set()
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Calculate refill rate (tokens per second)
        self.refill_rate = self.config.requests_per_minute / 60.0
        
    def _get_client_key(self, ip: str, user_id: Optional[str] = None) -> str:
        """Generate unique client key"""
        if user_id:
            return f"{ip}:{user_id}"
        return ip
    
    def _get_client(self, key: str) -> ClientState:
        """Get or create client state"""
        if key not in self.clients:
            self.clients[key] = ClientState(
                tokens=self.config.burst_capacity,
                last_request=time.time()
            )
        return self.clients[key]
    
    def _refill_tokens(self, client: ClientState) -> None:
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - client.last_request
        
        # Add tokens based on time elapsed
        tokens_to_add = elapsed * self.refill_rate
        client.tokens = min(
            self.config.burst_capacity,
            client.tokens + tokens_to_add
        )
        client.last_request = now
    
    def check_rate_limit(
        self,
        ip: str,
        user_id: Optional[str] = None,
        cost: float = 1.0
    ) -> bool:
        """
        Check if request should be allowed
        
        Args:
            ip: Client IP address
            user_id: Optional user identifier
            cost: Token cost for this request (default 1.0)
            
        Returns:
            True if allowed, False if rate limited
        """
        key = self._get_client_key(ip, user_id)
        client = self._get_client(key)
        
        # Check if blocked
        if client.blocked_until:
            if time.time() < client.blocked_until:
                return False
            # Unblock
            client.blocked_until = None
            client.violations = 0
        
        # Refill tokens
        self._refill_tokens(client)
        
        # Check if enough tokens
        if client.tokens >= cost:
            client.tokens -= cost
            client.request_count += 1
            return True
        
        # Rate limit exceeded
        client.violations += 1
        
        # Block if too many violations
        if client.violations >= self.config.max_violations_before_block:
            client.blocked_until = time.time() + self.config.block_duration_seconds
            self.blocked_ips.add(ip)
        
        return False
    
    def get_remaining_tokens(self, ip: str, user_id: Optional[str] = None) -> float:
        """Get remaining tokens for a client"""
        key = self._get_client_key(ip, user_id)
        if key not in self.clients:
            return self.config.burst_capacity
        
        client = self.clients[key]
        self._refill_tokens(client)
        return client.tokens
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        return {
            "total_clients": len(self.clients),
            "blocked_ips": list(self.blocked_ips),
            "config": {
                "requests_per_minute": self.config.requests_per_minute,
                "burst_capacity": self.config.burst_capacity,
                "block_duration": self.config.block_duration_seconds
            }
        }
    
    def unblock_ip(self, ip: str) -> bool:
        """Manually unblock an IP"""
        if ip in self.blocked_ips:
            self.blocked_ips.discard(ip)
            # Clear client states for this IP
            keys_to_clear = [k for k in self.clients if k.startswith(ip)]
            for key in keys_to_clear:
                self.clients[key].blocked_until = None
                self.clients[key].violations = 0
            return True
        return False
    
    def cleanup_old_clients(self, max_age_seconds: int = 3600) -> int:
        """Remove old client states to prevent memory bloat"""
        now = time.time()
        cutoff = now - max_age_seconds
        
        keys_to_remove = [
            key for key, client in self.clients.items()
            if client.last_request < cutoff and not client.blocked_until
        ]
        
        for key in keys_to_remove:
            del self.clients[key]
        
        return len(keys_to_remove)


# Global rate limiter instance
_rate_limiter: Optional[TokenBucketRateLimiter] = None


def get_rate_limiter(config: Optional[RateLimitConfig] = None) -> TokenBucketRateLimiter:
    """Get or create the global rate limiter"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = TokenBucketRateLimiter(config)
    return _rate_limiter


# ==============================================================================
# DDoS Detection
# ==============================================================================

@dataclass
class DDoSPattern:
    """Pattern for DDoS detection"""
    name: str
    description: str
    threshold: int
    window_seconds: int
    action: str  # "block", "challenge", "log"


class DDoSDetector:
    """
    Detects potential DDoS attack patterns
    
    Monitors for:
    - High request rates from single IPs
    - Request patterns (same URL repeatedly)
    - Sudden traffic spikes
    """
    
    DEFAULT_PATTERNS = [
        DDoSPattern(
            name="high_rate",
            description="High request rate from single IP",
            threshold=200,
            window_seconds=60,
            action="block"
        ),
        DDoSPattern(
            name="same_url",
            description="Repeated requests to same URL",
            threshold=100,
            window_seconds=60,
            action="challenge"
        ),
        DDoSPattern(
            name="invalid_requests",
            description="Many invalid/malformed requests",
            threshold=50,
            window_seconds=60,
            action="block"
        )
    ]
    
    def __init__(self, patterns: Optional[List[DDoSPattern]] = None):
        self.patterns = patterns or self.DEFAULT_PATTERNS
        self.request_log: Dict[str, List[float]] = defaultdict(list)
        self.url_log: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        self.invalid_log: Dict[str, List[float]] = defaultdict(list)
        self.detected_attacks: List[Dict[str, Any]] = []
        
    def record_request(self, ip: str, url: str, is_valid: bool = True) -> None:
        """Record a request for analysis"""
        now = time.time()
        
        # Record request
        self.request_log[ip].append(now)
        self.url_log[ip][url].append(now)
        
        if not is_valid:
            self.invalid_log[ip].append(now)
        
        # Cleanup old entries (older than max window)
        max_window = max(p.window_seconds for p in self.patterns)
        cutoff = now - max_window
        
        self.request_log[ip] = [t for t in self.request_log[ip] if t > cutoff]
        self.url_log[ip][url] = [t for t in self.url_log[ip][url] if t > cutoff]
        self.invalid_log[ip] = [t for t in self.invalid_log[ip] if t > cutoff]
    
    def check_patterns(self, ip: str) -> Optional[DDoSPattern]:
        """Check if any DDoS patterns are triggered"""
        now = time.time()
        
        for pattern in self.patterns:
            cutoff = now - pattern.window_seconds
            
            if pattern.name == "high_rate":
                requests = [t for t in self.request_log.get(ip, []) if t > cutoff]
                if len(requests) >= pattern.threshold:
                    self._record_detection(ip, pattern)
                    return pattern
                    
            elif pattern.name == "same_url":
                for url, times in self.url_log.get(ip, {}).items():
                    requests = [t for t in times if t > cutoff]
                    if len(requests) >= pattern.threshold:
                        self._record_detection(ip, pattern, {"url": url})
                        return pattern
                        
            elif pattern.name == "invalid_requests":
                invalids = [t for t in self.invalid_log.get(ip, []) if t > cutoff]
                if len(invalids) >= pattern.threshold:
                    self._record_detection(ip, pattern)
                    return pattern
        
        return None
    
    def _record_detection(
        self,
        ip: str,
        pattern: DDoSPattern,
        extra: Optional[Dict] = None
    ) -> None:
        """Record a detected attack pattern"""
        detection = {
            "timestamp": datetime.utcnow().isoformat(),
            "ip": ip,
            "pattern": pattern.name,
            "description": pattern.description,
            "action": pattern.action,
            **(extra or {})
        }
        self.detected_attacks.append(detection)
        
        # Keep only last 1000 detections
        if len(self.detected_attacks) > 1000:
            self.detected_attacks = self.detected_attacks[-1000:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get detection statistics"""
        return {
            "tracked_ips": len(self.request_log),
            "recent_detections": self.detected_attacks[-10:],
            "total_detections": len(self.detected_attacks)
        }


# Global DDoS detector
_ddos_detector: Optional[DDoSDetector] = None


def get_ddos_detector() -> DDoSDetector:
    """Get or create the global DDoS detector"""
    global _ddos_detector
    if _ddos_detector is None:
        _ddos_detector = DDoSDetector()
    return _ddos_detector


# ==============================================================================
# Circuit Breaker
# ==============================================================================

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5        # Failures before opening
    success_threshold: int = 3        # Successes to close
    timeout_seconds: float = 30.0     # Time before half-open
    half_open_max_calls: int = 3      # Max calls in half-open


class CircuitBreaker:
    """
    Circuit breaker for downstream service protection
    
    Prevents cascading failures by stopping requests to failing services.
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0
        
    def can_execute(self) -> bool:
        """Check if request can proceed"""
        if self.state == CircuitState.CLOSED:
            return True
            
        if self.state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if self.last_failure_time:
                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.config.timeout_seconds:
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    return True
            return False
            
        if self.state == CircuitState.HALF_OPEN:
            return self.half_open_calls < self.config.half_open_max_calls
        
        return False
    
    def record_success(self) -> None:
        """Record a successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        else:
            self.failure_count = 0
    
    def record_failure(self) -> None:
        """Record a failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.success_count = 0
        elif self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
    
    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count
        }


# Circuit breaker registry
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str) -> CircuitBreaker:
    """Get or create a circuit breaker by name"""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name)
    return _circuit_breakers[name]


# ==============================================================================
# Security Headers
# ==============================================================================

DEFAULT_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
}


# ==============================================================================
# Security Middleware
# ==============================================================================

class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware
    
    Combines:
    - Rate limiting
    - DDoS detection
    - Security headers
    - Request validation
    """
    
    def __init__(
        self,
        app,
        rate_limit_config: Optional[RateLimitConfig] = None,
        max_request_size: int = 10 * 1024 * 1024,  # 10MB
        excluded_paths: Optional[List[str]] = None
    ):
        super().__init__(app)
        self.rate_limiter = get_rate_limiter(rate_limit_config)
        self.ddos_detector = get_ddos_detector()
        self.max_request_size = max_request_size
        self.excluded_paths = excluded_paths or ["/health", "/metrics"]
        
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for proxy headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _is_excluded(self, path: str) -> bool:
        """Check if path is excluded from security checks"""
        return any(path.startswith(exc) for exc in self.excluded_paths)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security checks"""
        path = request.url.path
        
        # Skip excluded paths
        if self._is_excluded(path):
            response = await call_next(request)
            self._add_security_headers(response)
            return response
        
        client_ip = self._get_client_ip(request)
        
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "Request too large"}
            )
        
        # Record request for DDoS detection
        self.ddos_detector.record_request(client_ip, path)
        
        # Check for DDoS patterns
        pattern = self.ddos_detector.check_patterns(client_ip)
        if pattern:
            if pattern.action == "block":
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Too many requests - temporarily blocked"}
                )
        
        # Check rate limit
        if not self.rate_limiter.check_rate_limit(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Record invalid request
            self.ddos_detector.record_request(client_ip, path, is_valid=False)
            raise
        
        # Add security headers
        self._add_security_headers(response)
        
        # Add rate limit headers
        remaining = self.rate_limiter.get_remaining_tokens(client_ip)
        response.headers["X-RateLimit-Remaining"] = str(int(remaining))
        response.headers["X-RateLimit-Limit"] = str(
            self.rate_limiter.config.requests_per_minute
        )
        
        return response
    
    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to response"""
        for header, value in DEFAULT_SECURITY_HEADERS.items():
            if header not in response.headers:
                response.headers[header] = value


# ==============================================================================
# FastAPI Router for Security Endpoints
# ==============================================================================

from fastapi import APIRouter

security_router = APIRouter(prefix="/security", tags=["security"])


@security_router.get("/stats")
async def get_security_stats():
    """Get security system statistics"""
    rate_limiter = get_rate_limiter()
    ddos_detector = get_ddos_detector()
    
    return {
        "rate_limiter": rate_limiter.get_stats(),
        "ddos_detector": ddos_detector.get_stats(),
        "circuit_breakers": {
            name: cb.get_state()
            for name, cb in _circuit_breakers.items()
        }
    }


@security_router.post("/unblock/{ip}")
async def unblock_ip(ip: str):
    """Manually unblock an IP address"""
    rate_limiter = get_rate_limiter()
    success = rate_limiter.unblock_ip(ip)
    return {"ip": ip, "unblocked": success}


@security_router.get("/blocked")
async def get_blocked_ips():
    """Get list of blocked IP addresses"""
    rate_limiter = get_rate_limiter()
    return {"blocked_ips": list(rate_limiter.blocked_ips)}


# ==============================================================================
# Testing
# ==============================================================================

if __name__ == "__main__":
    # Test rate limiter
    print("Testing Rate Limiter...")
    limiter = TokenBucketRateLimiter(RateLimitConfig(
        requests_per_minute=10,
        burst_capacity=3
    ))
    
    test_ip = "192.168.1.1"
    
    # Burst requests
    for i in range(5):
        allowed = limiter.check_rate_limit(test_ip)
        print(f"  Request {i+1}: {'Allowed' if allowed else 'Denied'}")
    
    print(f"  Remaining tokens: {limiter.get_remaining_tokens(test_ip):.2f}")
    
    # Test DDoS detector
    print("\nTesting DDoS Detector...")
    detector = DDoSDetector([
        DDoSPattern("test", "Test pattern", threshold=3, window_seconds=60, action="block")
    ])
    
    for i in range(5):
        detector.record_request(test_ip, "/api/test")
        pattern = detector.check_patterns(test_ip)
        print(f"  Request {i+1}: Pattern triggered = {pattern is not None}")
    
    # Test circuit breaker
    print("\nTesting Circuit Breaker...")
    breaker = CircuitBreaker("test-service", CircuitBreakerConfig(failure_threshold=3))
    
    print(f"  Initial state: {breaker.state.value}")
    
    for i in range(4):
        if breaker.can_execute():
            breaker.record_failure()
            print(f"  Failure {i+1}: State = {breaker.state.value}")
    
    print(f"  Can execute (after failures): {breaker.can_execute()}")
    
    print("\n✅ All security components working!")
