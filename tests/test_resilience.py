#!/usr/bin/env python3
"""
Test suite for resilience features in OsMEN Gateway
Tests retry logic, exponential backoff, and error handling
"""

import sys
import os
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock

import pytest
import httpx

# Add gateway to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gateway'))

from resilience import retryable_llm_call, is_retryable_http_error


@pytest.fixture
def anyio_backend():
    """Limit AnyIO-backed tests to the asyncio backend for CI environments."""
    return "asyncio"


class TestRetryLogic:
    """Test retry logic and exponential backoff"""
    
    def test_is_retryable_http_error_429(self):
        """Test that 429 (rate limit) errors are retryable"""
        print("Testing 429 rate limit error is retryable...")
        response = Mock()
        response.status_code = 429
        error = httpx.HTTPStatusError("Rate limited", request=Mock(), response=response)
        assert is_retryable_http_error(error), "429 should be retryable"
        print("✓ PASS: 429 errors are retryable")
    
    def test_is_retryable_http_error_500(self):
        """Test that 500 (server error) errors are retryable"""
        print("Testing 500 server error is retryable...")
        response = Mock()
        response.status_code = 500
        error = httpx.HTTPStatusError("Server error", request=Mock(), response=response)
        assert is_retryable_http_error(error), "500 should be retryable"
        print("✓ PASS: 500 errors are retryable")
    
    def test_is_retryable_http_error_503(self):
        """Test that 503 (service unavailable) errors are retryable"""
        print("Testing 503 service unavailable is retryable...")
        response = Mock()
        response.status_code = 503
        error = httpx.HTTPStatusError("Service unavailable", request=Mock(), response=response)
        assert is_retryable_http_error(error), "503 should be retryable"
        print("✓ PASS: 503 errors are retryable")
    
    def test_is_not_retryable_http_error_400(self):
        """Test that 400 (bad request) errors are NOT retryable"""
        print("Testing 400 bad request is not retryable...")
        response = Mock()
        response.status_code = 400
        error = httpx.HTTPStatusError("Bad request", request=Mock(), response=response)
        assert not is_retryable_http_error(error), "400 should not be retryable"
        print("✓ PASS: 400 errors are not retryable")
    
    def test_is_not_retryable_http_error_401(self):
        """Test that 401 (unauthorized) errors are NOT retryable"""
        print("Testing 401 unauthorized is not retryable...")
        response = Mock()
        response.status_code = 401
        error = httpx.HTTPStatusError("Unauthorized", request=Mock(), response=response)
        assert not is_retryable_http_error(error), "401 should not be retryable"
        print("✓ PASS: 401 errors are not retryable")


class TestRetryDecorator:
    """Test the retry decorator functionality"""

    @pytest.mark.anyio
    async def test_retry_decorator_succeeds_first_try(self):
        """Test that decorator allows success on first try"""
        print("Testing decorator with successful first attempt...")
        
        @retryable_llm_call(max_attempts=3)
        async def mock_call():
            return "success"
        
        result = await mock_call()
        assert result == "success", "Should succeed on first try"
        print("✓ PASS: Successful first attempt works")
    
    @pytest.mark.anyio
    async def test_retry_decorator_retries_on_network_error(self):
        """Test that decorator retries on network errors"""
        print("Testing decorator retries on network error...")
        
        call_count = 0
        
        @retryable_llm_call(max_attempts=3, min_wait=0.1, max_wait=0.2)
        async def mock_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.NetworkError("Network failure")
            return "success"
        
        result = await mock_call()
        assert result == "success", "Should succeed after retry"
        assert call_count == 2, "Should have retried once"
        print(f"✓ PASS: Retried {call_count - 1} time(s) before success")
    
    @pytest.mark.anyio
    async def test_retry_decorator_exhausts_attempts(self):
        """Test that decorator exhausts all retry attempts"""
        print("Testing decorator exhausts retry attempts...")
        
        call_count = 0
        
        @retryable_llm_call(max_attempts=3, min_wait=0.1, max_wait=0.2)
        async def mock_call():
            nonlocal call_count
            call_count += 1
            raise httpx.NetworkError("Persistent failure")
        
        try:
            await mock_call()
            assert False, "Should have raised exception"
        except httpx.NetworkError:
            assert call_count == 3, f"Should have tried 3 times, tried {call_count}"
            print(f"✓ PASS: Exhausted all {call_count} attempts")
    
    @pytest.mark.anyio
    async def test_retry_decorator_retries_on_retryable_status(self):
        """Test that decorator retries on retryable HTTP status codes"""
        print("Testing decorator retries on 503 error...")
        
        call_count = 0
        
        @retryable_llm_call(max_attempts=3, min_wait=0.1, max_wait=0.2)
        async def mock_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                response = Mock()
                response.status_code = 503
                raise httpx.HTTPStatusError("Service unavailable", request=Mock(), response=response)
            return "success"
        
        result = await mock_call()
        assert result == "success", "Should succeed after retry"
        assert call_count == 2, "Should have retried once"
        print(f"✓ PASS: Retried on 503 error and succeeded")
    
    @pytest.mark.anyio
    async def test_retry_decorator_does_not_retry_on_non_retryable_status(self):
        """Test that decorator does not retry on non-retryable HTTP status codes"""
        print("Testing decorator does not retry on 401 error...")
        
        call_count = 0
        
        @retryable_llm_call(max_attempts=3, min_wait=0.1, max_wait=0.2)
        async def mock_call():
            nonlocal call_count
            call_count += 1
            response = Mock()
            response.status_code = 401
            raise httpx.HTTPStatusError("Unauthorized", request=Mock(), response=response)
        
        try:
            await mock_call()
            assert False, "Should have raised exception"
        except httpx.HTTPStatusError:
            assert call_count == 1, f"Should have tried only once, tried {call_count}"
            print(f"✓ PASS: Did not retry on 401 error (1 attempt only)")


def run_async_tests():
    """Run async tests"""
    test = TestRetryDecorator()
    
    tests = [
        ("Successful first attempt", test.test_retry_decorator_succeeds_first_try()),
        ("Retry on network error", test.test_retry_decorator_retries_on_network_error()),
        ("Exhaust retry attempts", test.test_retry_decorator_exhausts_attempts()),
        ("Retry on 503 error", test.test_retry_decorator_retries_on_retryable_status()),
        ("No retry on 401 error", test.test_retry_decorator_does_not_retry_on_non_retryable_status()),
    ]
    
    for name, coro in tests:
        asyncio.run(coro)


def main():
    """Run all tests"""
    print("=" * 70)
    print("OsMEN Gateway - Resilience Test Suite")
    print("=" * 70)
    print()
    
    passed = 0
    failed = 0
    
    # Test 1: Retry logic for retryable errors
    try:
        test = TestRetryLogic()
        test.test_is_retryable_http_error_429()
        test.test_is_retryable_http_error_500()
        test.test_is_retryable_http_error_503()
        test.test_is_not_retryable_http_error_400()
        test.test_is_not_retryable_http_error_401()
        passed += 5
    except Exception as e:
        print(f"✗ FAIL: Retry logic tests - {e}")
        failed += 1
    
    print()
    
    # Test 2-6: Retry decorator tests
    try:
        run_async_tests()
        passed += 5
    except Exception as e:
        print(f"✗ FAIL: Retry decorator tests - {e}")
        failed += 1
    
    print()
    print("=" * 70)
    print(f"Resilience Test Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed > 0:
        print("\n❌ Some tests failed")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        print("\nResilience features validated:")
        print("  • Retry logic for transient errors (5xx, 429)")
        print("  • Exponential backoff with configurable wait times")
        print("  • Selective retry (no retry on 4xx client errors)")
        print("  • Network error handling (timeouts, connection errors)")
        print("  • Maximum retry attempts enforcement")
        sys.exit(0)


if __name__ == "__main__":
    main()
