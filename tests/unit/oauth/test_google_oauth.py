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


def test_authorization_url_with_login_hint(google_handler):
    """Test authorization URL with login_hint parameter."""
    auth_url = google_handler.get_authorization_url(
        state='test_state',
        login_hint='user@example.com'
    )
    assert 'login_hint=user%40example.com' in auth_url


def test_authorization_url_with_granted_scopes(google_handler):
    """Test authorization URL with include_granted_scopes."""
    auth_url = google_handler.get_authorization_url(
        state='test_state',
        include_granted_scopes=True
    )
    assert 'include_granted_scopes=true' in auth_url


@patch('requests.post')
def test_exchange_code_success(mock_post, google_handler):
    """Test successful code exchange for tokens."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'access_token': 'test_access_token',
        'refresh_token': 'test_refresh_token',
        'expires_in': 3600,
        'token_type': 'Bearer',
        'scope': 'calendar gmail'
    }
    mock_post.return_value = mock_response
    
    result = google_handler.exchange_code_for_token('test_code')
    
    assert result['access_token'] == 'test_access_token'
    assert result['refresh_token'] == 'test_refresh_token'
    assert 'expires_at' in result


@patch('requests.post')
def test_exchange_code_failure(mock_post, google_handler):
    """Test failed code exchange."""
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = '{"error": "invalid_grant"}'
    mock_response.json.return_value = {
        'error': 'invalid_grant',
        'error_description': 'Invalid authorization code'
    }
    mock_post.return_value = mock_response
    
    with pytest.raises(OAuthTokenError) as exc_info:
        google_handler.exchange_code_for_token('invalid_code')
    
    assert 'Token exchange failed' in str(exc_info.value)


def test_exchange_code_empty_code(google_handler):
    """Test exchange with empty code."""
    with pytest.raises(OAuthTokenError) as exc_info:
        google_handler.exchange_code_for_token('')
    
    assert 'Authorization code is required' in str(exc_info.value)


@patch('requests.post')
def test_exchange_code_network_error(mock_post, google_handler):
    """Test network error during code exchange."""
    import requests
    mock_post.side_effect = requests.RequestException('Network error')
    
    with pytest.raises(OAuthTokenError) as exc_info:
        google_handler.exchange_code_for_token('test_code')
    
    assert 'Network error during token exchange' in str(exc_info.value)


@patch('requests.post')
def test_refresh_token_success(mock_post, google_handler):
    """Test successful token refresh."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'access_token': 'new_access_token',
        'expires_in': 3600,
        'token_type': 'Bearer'
    }
    mock_post.return_value = mock_response
    
    result = google_handler.refresh_token('test_refresh_token')
    
    assert result['access_token'] == 'new_access_token'
    assert 'expires_at' in result


@patch('requests.post')
def test_refresh_token_failure(mock_post, google_handler):
    """Test failed token refresh."""
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = '{"error": "invalid_grant"}'
    mock_response.json.return_value = {
        'error': 'invalid_grant',
        'error_description': 'Invalid refresh token'
    }
    mock_post.return_value = mock_response
    
    with pytest.raises(OAuthTokenError):
        google_handler.refresh_token('invalid_refresh_token')


def test_refresh_token_empty(google_handler):
    """Test refresh with empty refresh token."""
    with pytest.raises(OAuthTokenError) as exc_info:
        google_handler.refresh_token('')
    
    assert 'Refresh token is required' in str(exc_info.value)


@patch('requests.get')
def test_validate_token_success(mock_get, google_handler):
    """Test successful token validation."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'azp': 'test_client_id',
        'aud': 'test_client_id',
        'scope': 'calendar gmail',
        'exp': '1234567890',
        'expires_in': '3600'
    }
    mock_get.return_value = mock_response
    
    result = google_handler.validate_token('test_token')
    assert result['valid'] is True
    assert 'scope' in result


@patch('requests.get')
def test_validate_token_invalid(mock_get, google_handler):
    """Test invalid token validation."""
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = '{}'
    mock_response.json.return_value = {'error': 'invalid_token'}
    mock_get.return_value = mock_response
    
    result = google_handler.validate_token('invalid_token')
    assert result['valid'] is False


@patch('requests.post')
def test_revoke_token_success(mock_post, google_handler):
    """Test successful token revocation."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    result = google_handler.revoke_token('test_token')
    assert result is True


@patch('requests.post')
def test_revoke_token_failure(mock_post, google_handler):
    """Test failed token revocation."""
    mock_response = Mock()
    mock_response.status_code = 400
    mock_post.return_value = mock_response
    
    result = google_handler.revoke_token('invalid_token')
    assert result is False


def test_custom_endpoints(google_config):
    """Test custom endpoint configuration."""
    google_config['auth_endpoint'] = 'https://custom.auth.endpoint'
    google_config['token_endpoint'] = 'https://custom.token.endpoint'
    
    handler = GoogleOAuthHandler(google_config)
    
    assert handler.auth_endpoint == 'https://custom.auth.endpoint'
    assert handler.token_endpoint == 'https://custom.token.endpoint'


def test_authorization_url_without_state(google_handler):
    """Test authorization URL generation without explicit state."""
    auth_url = google_handler.get_authorization_url()
    # State should be auto-generated
    assert 'state=' in auth_url


@patch('requests.post')
def test_refresh_token_network_error(mock_post, google_handler):
    """Test network error during token refresh."""
    import requests
    mock_post.side_effect = requests.RequestException('Network error')
    
    with pytest.raises(OAuthTokenError) as exc_info:
        google_handler.refresh_token('test_refresh_token')
    
    assert 'Network error during token refresh' in str(exc_info.value)


@patch('requests.post')
def test_revoke_token_network_error(mock_post, google_handler):
    """Test network error during token revocation."""
    import requests
    mock_post.side_effect = requests.RequestException('Network error')
    
    result = google_handler.revoke_token('test_token')
    assert result is False


def test_revoke_token_empty(google_handler):
    """Test revoking empty token."""
    result = google_handler.revoke_token('')
    assert result is False


def test_validate_token_empty(google_handler):
    """Test validating empty token."""
    with pytest.raises(OAuthValidationError) as exc_info:
        google_handler.validate_token('')
    
    assert 'Access token is required' in str(exc_info.value)


@patch('requests.get')
def test_validate_token_network_error(mock_get, google_handler):
    """Test network error during token validation."""
    import requests
    mock_get.side_effect = requests.RequestException('Network error')
    
    with pytest.raises(OAuthValidationError) as exc_info:
        google_handler.validate_token('test_token')
    
    assert 'Network error during token validation' in str(exc_info.value)


def test_missing_client_secret():
    """Test initialization with missing client_secret."""
    config = {
        'client_id': 'test_id',
        'redirect_uri': 'http://localhost:8080/callback',
        'scopes': []
    }
    
    with pytest.raises(ValueError) as exc_info:
        GoogleOAuthHandler(config)
    
    assert 'client_secret is required' in str(exc_info.value)


def test_missing_redirect_uri():
    """Test initialization with missing redirect_uri."""
    config = {
        'client_id': 'test_id',
        'client_secret': 'test_secret',
        'scopes': []
    }
    
    with pytest.raises(ValueError) as exc_info:
        GoogleOAuthHandler(config)
    
    assert 'redirect_uri is required' in str(exc_info.value)
