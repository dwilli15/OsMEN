"""
OAuth-specific test fixtures.
"""

import pytest
from typing import Dict, Any
from datetime import datetime, timedelta


@pytest.fixture
def mock_google_oauth_config() -> Dict[str, Any]:
    """Mock Google OAuth configuration."""
    return {
        'provider': 'google',
        'client_id': 'test_google_client_id_123456',
        'client_secret': 'test_google_client_secret_abcdef',
        'redirect_uri': 'http://localhost:8080/oauth/callback',
        'scopes': [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/contacts.readonly',
        ],
        'access_type': 'offline',
        'prompt': 'consent',
    }


@pytest.fixture
def mock_microsoft_oauth_config() -> Dict[str, Any]:
    """Mock Microsoft OAuth configuration."""
    return {
        'provider': 'microsoft',
        'client_id': 'test_microsoft_client_id_789012',
        'client_secret': 'test_microsoft_client_secret_ghijkl',
        'redirect_uri': 'http://localhost:8080/oauth/callback',
        'tenant': 'common',
        'scopes': [
            'https://graph.microsoft.com/Calendars.ReadWrite',
            'https://graph.microsoft.com/Mail.ReadWrite',
            'https://graph.microsoft.com/Contacts.ReadWrite',
            'offline_access',
        ],
    }


@pytest.fixture
def mock_google_token_response() -> Dict[str, Any]:
    """Mock Google OAuth token response."""
    return {
        'access_token': 'google_access_token_mock_xyz123',
        'expires_in': 3600,
        'refresh_token': 'google_refresh_token_mock_abc456',
        'scope': 'https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/gmail.modify',
        'token_type': 'Bearer',
    }


@pytest.fixture
def mock_microsoft_token_response() -> Dict[str, Any]:
    """Mock Microsoft OAuth token response."""
    return {
        'token_type': 'Bearer',
        'scope': 'Calendars.ReadWrite Mail.ReadWrite offline_access',
        'expires_in': 3600,
        'ext_expires_in': 3600,
        'access_token': 'microsoft_access_token_mock_def789',
        'refresh_token': 'microsoft_refresh_token_mock_ghi012',
        'id_token': 'microsoft_id_token_mock_jkl345',
    }


@pytest.fixture
def mock_expired_token_response() -> Dict[str, Any]:
    """Mock an expired token response."""
    return {
        'access_token': 'expired_access_token_mock',
        'expires_in': -3600,  # Expired 1 hour ago
        'refresh_token': 'valid_refresh_token_mock',
        'token_type': 'Bearer',
        'scope': 'test_scope',
    }


@pytest.fixture
def mock_refresh_token_response() -> Dict[str, Any]:
    """Mock token refresh response."""
    return {
        'access_token': 'new_access_token_mock_refreshed',
        'expires_in': 3600,
        'token_type': 'Bearer',
        'scope': 'test_scope',
    }


@pytest.fixture
def mock_oauth_error_response() -> Dict[str, Any]:
    """Mock OAuth error response."""
    return {
        'error': 'invalid_grant',
        'error_description': 'The provided authorization grant is invalid, expired, or revoked.',
    }


@pytest.fixture
def mock_authorization_code() -> str:
    """Mock authorization code from OAuth flow."""
    return 'test_authorization_code_abc123xyz'


@pytest.fixture
def mock_state_parameter() -> str:
    """Mock state parameter for OAuth flow."""
    return 'test_state_parameter_secure_random_string_123'


@pytest.fixture
def mock_code_verifier() -> str:
    """Mock PKCE code verifier."""
    return 'test_code_verifier_long_random_string_for_pkce'


@pytest.fixture
def mock_code_challenge() -> str:
    """Mock PKCE code challenge."""
    return 'test_code_challenge_base64_encoded_sha256'
