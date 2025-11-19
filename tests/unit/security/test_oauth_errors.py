#!/usr/bin/env python3
"""
Unit tests for OAuth Error Handling

Tests OAuth error exceptions and parsing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from integrations.oauth.oauth_errors import (
    OAuthError, OAuthConfigError, OAuthAuthorizationError,
    OAuthTokenExchangeError, OAuthTokenRefreshError,
    OAuthInvalidTokenError, OAuthRateLimitError,
    OAuthErrorParser
)


def test_oauth_error_hierarchy():
    """Test OAuth error exception hierarchy."""
    # All custom errors should inherit from OAuthError
    assert issubclass(OAuthConfigError, OAuthError)
    assert issubclass(OAuthAuthorizationError, OAuthError)
    assert issubclass(OAuthTokenExchangeError, OAuthError)
    assert issubclass(OAuthTokenRefreshError, OAuthError)
    assert issubclass(OAuthInvalidTokenError, OAuthError)
    assert issubclass(OAuthRateLimitError, OAuthError)
    
    print("✅ test_oauth_error_hierarchy passed")


def test_parse_invalid_client_error():
    """Test parsing invalid_client error."""
    response = {
        'error': 'invalid_client',
        'error_description': 'Client authentication failed'
    }
    
    error = OAuthErrorParser.parse_error_response(response)
    assert isinstance(error, OAuthConfigError)
    assert 'invalid_client' in str(error)
    
    print("✅ test_parse_invalid_client_error passed")


def test_parse_invalid_grant_error():
    """Test parsing invalid_grant error."""
    response = {
        'error': 'invalid_grant',
        'error_description': 'Authorization code is invalid'
    }
    
    error = OAuthErrorParser.parse_error_response(response)
    assert isinstance(error, OAuthTokenExchangeError)
    
    print("✅ test_parse_invalid_grant_error passed")


def test_parse_access_denied_error():
    """Test parsing access_denied error."""
    response = {
        'error': 'access_denied',
        'error_description': 'User denied access'
    }
    
    error = OAuthErrorParser.parse_error_response(response)
    assert isinstance(error, OAuthAuthorizationError)
    
    print("✅ test_parse_access_denied_error passed")


def test_parse_invalid_token_error():
    """Test parsing invalid_token error."""
    response = {
        'error': 'invalid_token'
    }
    
    error = OAuthErrorParser.parse_error_response(response)
    assert isinstance(error, OAuthInvalidTokenError)
    
    print("✅ test_parse_invalid_token_error passed")


def test_parse_unknown_error():
    """Test parsing unknown error."""
    response = {
        'error': 'unknown_error_type'
    }
    
    error = OAuthErrorParser.parse_error_response(response)
    assert isinstance(error, OAuthError)
    
    print("✅ test_parse_unknown_error passed")


def run_all_tests():
    """Run all OAuth error tests."""
    print("\nRunning OAuth Error Handling Tests")
    print("=" * 60)
    
    tests = [
        test_oauth_error_hierarchy,
        test_parse_invalid_client_error,
        test_parse_invalid_grant_error,
        test_parse_access_denied_error,
        test_parse_invalid_token_error,
        test_parse_unknown_error,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
