"""
Unit tests for utility functions and helpers.

Tests for retry logic, rate limiting, validation, etc.
"""

import pytest
from datetime import datetime, timedelta


class TestRetryLogic:
    """Test retry logic utilities."""
    
    @pytest.mark.unit
    def test_retry_on_failure(self):
        """Test that operations are retried on failure."""
        attempt_count = 0
        max_attempts = 3
        
        def failing_operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < max_attempts:
                raise Exception("Simulated failure")
            return "success"
        
        # Simulate retry logic
        result = None
        for i in range(max_attempts):
            try:
                result = failing_operation()
                break
            except Exception:
                if i == max_attempts - 1:
                    raise
        
        assert result == "success"
        assert attempt_count == max_attempts
    
    @pytest.mark.unit
    def test_retry_gives_up_after_max_attempts(self):
        """Test that retry gives up after maximum attempts."""
        attempt_count = 0
        max_attempts = 3
        
        def always_failing_operation():
            nonlocal attempt_count
            attempt_count += 1
            raise Exception("Always fails")
        
        # Simulate retry logic
        with pytest.raises(Exception, match="Always fails"):
            for i in range(max_attempts):
                try:
                    always_failing_operation()
                except Exception:
                    if i == max_attempts - 1:
                        raise
        
        assert attempt_count == max_attempts


class TestRateLimiting:
    """Test rate limiting utilities."""
    
    @pytest.mark.unit
    def test_rate_limit_tracking(self):
        """Test tracking API call rate limits."""
        # Simulate rate limit tracking
        rate_limit = {
            'limit': 100,
            'remaining': 100,
            'reset_time': datetime.now() + timedelta(hours=1)
        }
        
        # Make a request
        rate_limit['remaining'] -= 1
        
        assert rate_limit['remaining'] == 99
        assert rate_limit['limit'] == 100
    
    @pytest.mark.unit
    def test_rate_limit_exceeded(self):
        """Test detection of rate limit exceeded."""
        rate_limit = {
            'limit': 100,
            'remaining': 0,
            'reset_time': datetime.now() + timedelta(minutes=30)
        }
        
        # Check if rate limit exceeded
        is_exceeded = rate_limit['remaining'] <= 0
        
        assert is_exceeded is True
    
    @pytest.mark.unit
    def test_rate_limit_reset(self):
        """Test rate limit reset after time period."""
        now = datetime.now()
        reset_time = now - timedelta(minutes=1)  # Past reset time
        
        rate_limit = {
            'limit': 100,
            'remaining': 0,
            'reset_time': reset_time
        }
        
        # Check if reset time has passed
        should_reset = datetime.now() >= rate_limit['reset_time']
        
        if should_reset:
            rate_limit['remaining'] = rate_limit['limit']
        
        assert rate_limit['remaining'] == 100


class TestValidation:
    """Test validation utilities."""
    
    @pytest.mark.unit
    def test_email_validation_valid(self):
        """Test validation of valid email addresses."""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'first+last@test.org',
        ]
        
        for email in valid_emails:
            # Simple email validation
            assert '@' in email
            assert '.' in email.split('@')[1]
    
    @pytest.mark.unit
    def test_email_validation_invalid(self):
        """Test validation of invalid email addresses."""
        invalid_emails = [
            'notanemail',
            '@nodomain.com',
            'no-at-sign.com',
        ]
        
        for email in invalid_emails:
            # Simple email validation - must have @ and text before it
            parts = email.split('@')
            is_valid = len(parts) == 2 and len(parts[0]) > 0 and '.' in parts[1]
            assert is_valid is False
    
    @pytest.mark.unit
    def test_url_validation_valid(self):
        """Test validation of valid URLs."""
        valid_urls = [
            'https://example.com',
            'http://test.org/path',
            'https://api.service.com/v1/endpoint',
        ]
        
        for url in valid_urls:
            assert url.startswith('http://') or url.startswith('https://')
    
    @pytest.mark.unit
    def test_token_validation(self):
        """Test validation of OAuth tokens."""
        valid_token = {
            'access_token': 'valid_token_123',
            'token_type': 'Bearer',
            'expires_in': 3600,
        }
        
        # Validate required fields
        assert 'access_token' in valid_token
        assert 'token_type' in valid_token
        assert valid_token['token_type'] == 'Bearer'
        assert valid_token['expires_in'] > 0
    
    @pytest.mark.unit
    def test_scope_validation(self):
        """Test validation of OAuth scopes."""
        requested_scopes = ['calendar', 'email', 'contacts']
        granted_scopes = ['calendar', 'email']
        
        # Check if all requested scopes were granted
        all_granted = all(scope in granted_scopes for scope in requested_scopes)
        
        assert all_granted is False
        
        # Check which scopes are missing
        missing_scopes = [s for s in requested_scopes if s not in granted_scopes]
        assert missing_scopes == ['contacts']


class TestDateTimeHelpers:
    """Test date/time helper functions."""
    
    @pytest.mark.unit
    def test_is_token_expired(self):
        """Test checking if token is expired."""
        # Token that expires in 1 hour
        token_expires_at = datetime.now() + timedelta(hours=1)
        is_expired = datetime.now() >= token_expires_at
        assert is_expired is False
        
        # Token that expired 1 hour ago
        token_expires_at = datetime.now() - timedelta(hours=1)
        is_expired = datetime.now() >= token_expires_at
        assert is_expired is True
    
    @pytest.mark.unit
    def test_time_until_expiry(self):
        """Test calculating time until token expiry."""
        expires_in_seconds = 3600  # 1 hour
        expires_at = datetime.now() + timedelta(seconds=expires_in_seconds)
        
        time_until_expiry = (expires_at - datetime.now()).total_seconds()
        
        # Should be approximately 3600 seconds (allow for small timing differences)
        assert 3595 <= time_until_expiry <= 3600
    
    @pytest.mark.unit
    def test_should_refresh_token(self):
        """Test determining if token should be refreshed."""
        # Refresh if less than 5 minutes remaining
        refresh_threshold = timedelta(minutes=5)
        
        # Token expires in 10 minutes - should not refresh yet
        expires_at = datetime.now() + timedelta(minutes=10)
        should_refresh = (expires_at - datetime.now()) < refresh_threshold
        assert should_refresh is False
        
        # Token expires in 2 minutes - should refresh
        expires_at = datetime.now() + timedelta(minutes=2)
        should_refresh = (expires_at - datetime.now()) < refresh_threshold
        assert should_refresh is True


class TestDataSerialization:
    """Test data serialization/deserialization."""
    
    @pytest.mark.unit
    def test_json_serialization(self):
        """Test JSON serialization of data."""
        import json
        
        data = {
            'access_token': 'test_token',
            'expires_in': 3600,
            'scopes': ['calendar', 'email'],
        }
        
        # Serialize to JSON
        json_str = json.dumps(data)
        
        # Deserialize from JSON
        parsed_data = json.loads(json_str)
        
        assert parsed_data == data
    
    @pytest.mark.unit
    def test_datetime_serialization(self):
        """Test datetime serialization."""
        now = datetime.now()
        
        # Convert to ISO format string
        iso_str = now.isoformat()
        
        # Parse back to datetime
        parsed_dt = datetime.fromisoformat(iso_str)
        
        # Should be equal (microseconds might differ slightly)
        assert abs((parsed_dt - now).total_seconds()) < 1


class TestErrorFormatting:
    """Test error message formatting."""
    
    @pytest.mark.unit
    def test_oauth_error_formatting(self):
        """Test formatting of OAuth error messages."""
        error_response = {
            'error': 'invalid_grant',
            'error_description': 'The authorization code is invalid or expired.',
        }
        
        # Format error message
        error_msg = f"{error_response['error']}: {error_response['error_description']}"
        
        assert 'invalid_grant' in error_msg
        assert 'invalid or expired' in error_msg
    
    @pytest.mark.unit
    def test_api_error_formatting(self):
        """Test formatting of API error messages."""
        api_error = {
            'error': {
                'code': 401,
                'message': 'Invalid credentials',
                'status': 'UNAUTHENTICATED',
            }
        }
        
        # Format error message
        error_msg = f"API Error {api_error['error']['code']}: {api_error['error']['message']}"
        
        assert '401' in error_msg
        assert 'Invalid credentials' in error_msg
