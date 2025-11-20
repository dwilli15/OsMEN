"""Token bucket rate limiter"""
import time
import threading
from collections import defaultdict

class RateLimiter:
    """
    Token bucket rate limiter for API calls.
    
    Thread-safe implementation for concurrent usage.
    """
    
    def __init__(self, requests_per_second: float = 10.0):
        self.rate = requests_per_second
        self.tokens = defaultdict(lambda: self.rate)
        self.last_update = defaultdict(lambda: time.time())
        self.lock = threading.Lock()
    
    def acquire(self, key: str = 'default', tokens: int = 1) -> bool:
        """
        Acquire tokens for an API call.
        
        Args:
            key: Rate limit key (e.g., API endpoint)
            tokens: Number of tokens to acquire
        
        Returns:
            True if tokens acquired, False otherwise
        """
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update[key]
            
            # Refill tokens based on elapsed time
            self.tokens[key] = min(
                self.rate,
                self.tokens[key] + elapsed * self.rate
            )
            self.last_update[key] = now
            
            if self.tokens[key] >= tokens:
                self.tokens[key] -= tokens
                return True
            
            return False
    
    def wait(self, key: str = 'default', tokens: int = 1):
        """
        Wait until tokens are available.
        
        Args:
            key: Rate limit key
            tokens: Number of tokens needed
        """
        while not self.acquire(key, tokens):
            time.sleep(0.1)

# Decorator for rate limiting
def rate_limit(requests_per_second: float = 10.0):
    """Rate limit decorator"""
    limiter = RateLimiter(requests_per_second)
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            limiter.wait()
            return func(*args, **kwargs)
        return wrapper
    return decorator
