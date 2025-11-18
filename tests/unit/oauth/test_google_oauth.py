"""
Unit tests for Google OAuth implementation.

Tests cover:
- Authorization URL generation
- Token exchange
- Token refresh
- Token validation
- Token revocation
- Error handling
"""

import pytest
from unittest.mock import Mock, patch
from integrations.oauth.google_oauth import GoogleOAuthHandler
from integrations.oauth.oauth_handler import OAuthTokenError, OAuthValidationError


@pytest.fixture
def google_config():
    """Test configuration for Google OAuth."""
    return {
        'client_id': 'test_client_id',
        'client_secret': 'test_client_secret',
        'redirect_uri': 'http://localhost:8080/callback',
        'scopes': [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/gmail.modify'
        ]
    }


@pytest.fixture
def google_handler(google_config):
    """Create a Google OAuth handler for testing."""
    return GoogleOAuthHandler(google_config)


def test_initialization(google_handler, google_config):
    """Test Google OAuth handler initialization."""
    assert google_handler.client_id == google_config['client_id']
    assert google_handler.client_secret == google_config['client_secret']
    assert google_handler.redirect_uri == google_config['redirect_uri']
    assert google_handler.scopes == google_config['scopes']


def test_authorization_url_generation(google_handler):
    """Test authorization URL generation."""
    auth_url = google_handler.get_authorization_url(state='test_state_123')
    
    # Verify URL structure
    assert auth_url.startswith('https://accounts.google.com/o/oauth2/v2/auth?')
    assert 'client_id=test_client_id' in auth_url
    assert 'redirect_uri=http%3A%2F%2Flocalhost%3A8080%2Fcallback' in auth_url
    assert 'response_type=code' in auth_url
    assert 'state=test_state_123' in auth_url
    assert 'access_type=offline' in auth_url
    assert 'prompt=consent' in auth_url


def test_missing_client_id():
    """Test initialization with missing client_id."""
    config = {
        'client_secret': 'test_secret',
        'redirect_uri': 'http://localhost:8080/callback',
        'scopes': []
    }
    
    with pytest.raises(ValueError) as exc_info:
        GoogleOAuthHandler(config)
    
    assert 'client_id is required' in str(exc_info.value)
