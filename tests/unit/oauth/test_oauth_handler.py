"""
Unit tests for OAuth handler functionality.

These tests use mocks to test OAuth flows without hitting real endpoints.
"""

import pytest
from tests.mocks.mock_oauth_server import MockOAuthServer, get_mock_oauth_server, reset_mock_oauth_server
from tests.fixtures.oauth_fixtures import *  # Import all OAuth fixtures


class TestOAuthBasics:
    """Test basic OAuth functionality."""
    
    def test_mock_oauth_server_initialization(self):
        """Test that mock OAuth server initializes correctly."""
        server = MockOAuthServer()
        
        assert server is not None
        assert len(server.auth_codes) == 0
        assert len(server.tokens) == 0
        assert len(server.refresh_tokens) == 0
    
    def test_mock_oauth_server_singleton(self):
        """Test that get_mock_oauth_server returns singleton."""
        server1 = get_mock_oauth_server()
        server2 = get_mock_oauth_server()
        
        assert server1 is server2
    
    def test_mock_oauth_server_reset(self):
        """Test that reset clears all server state."""
        server = get_mock_oauth_server()
        
        # Add some data
        server.generate_auth_code('client123', 'http://localhost', 'scope1', 'state123')
        
        # Reset
        reset_mock_oauth_server()
        
        # Verify cleared
        assert len(server.auth_codes) == 0


class TestGoogleOAuthMock:
    """Test Google OAuth using mock server."""
    
    def setup_method(self):
        """Reset mock server before each test."""
        reset_mock_oauth_server()
        self.server = get_mock_oauth_server()
    
    def test_google_authorization_url_generation(self, mock_google_oauth_config):
        """Test generating Google authorization URL."""
        config = mock_google_oauth_config
        
        url = self.server.mock_google_authorization_url(
            client_id=config['client_id'],
            redirect_uri=config['redirect_uri'],
            scopes=config['scopes'],
            state='test_state_123'
        )
        
        assert 'accounts.google.com' in url
        assert config['client_id'] in url
        assert 'redirect_uri=' in url
        assert 'scope=' in url
        assert 'state=test_state_123' in url
        assert 'access_type=offline' in url
        assert 'prompt=consent' in url
    
    def test_google_authorization_request_tracking(self, mock_google_oauth_config):
        """Test that authorization requests are tracked."""
        config = mock_google_oauth_config
        
        self.server.mock_google_authorization_url(
            client_id=config['client_id'],
            redirect_uri=config['redirect_uri'],
            scopes=config['scopes'],
            state='test_state_456'
        )
        
        assert len(self.server.authorization_requests) == 1
        request = self.server.authorization_requests[0]
        assert request['provider'] == 'google'
        assert request['client_id'] == config['client_id']
    
    def test_google_token_exchange_success(self, mock_google_oauth_config):
        """Test successful token exchange."""
        config = mock_google_oauth_config
        
        # Generate auth code
        auth_code = self.server.generate_auth_code(
            client_id=config['client_id'],
            redirect_uri=config['redirect_uri'],
            scope=' '.join(config['scopes']),
            state='test_state'
        )
        
        # Exchange code for token
        token_response = self.server.mock_token_exchange(
            provider='google',
            code=auth_code,
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            redirect_uri=config['redirect_uri']
        )
        
        assert 'access_token' in token_response
        assert 'refresh_token' in token_response
        assert token_response['token_type'] == 'Bearer'
        assert token_response['expires_in'] == 3600
        assert 'error' not in token_response
    
    def test_google_token_exchange_invalid_code(self, mock_google_oauth_config):
        """Test token exchange with invalid authorization code."""
        config = mock_google_oauth_config
        
        # Try to exchange invalid code
        token_response = self.server.mock_token_exchange(
            provider='google',
            code='invalid_code_xyz',
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            redirect_uri=config['redirect_uri']
        )
        
        assert 'error' in token_response
        assert token_response['error'] == 'invalid_grant'
    
    def test_google_token_exchange_code_reuse(self, mock_google_oauth_config):
        """Test that authorization codes cannot be reused."""
        config = mock_google_oauth_config
        
        # Generate auth code
        auth_code = self.server.generate_auth_code(
            client_id=config['client_id'],
            redirect_uri=config['redirect_uri'],
            scope=' '.join(config['scopes']),
            state='test_state'
        )
        
        # Exchange code for token (first time)
        token_response1 = self.server.mock_token_exchange(
            provider='google',
            code=auth_code,
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            redirect_uri=config['redirect_uri']
        )
        
        assert 'access_token' in token_response1
        
        # Try to reuse the same code (second time)
        token_response2 = self.server.mock_token_exchange(
            provider='google',
            code=auth_code,
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            redirect_uri=config['redirect_uri']
        )
        
        assert 'error' in token_response2
        assert token_response2['error'] == 'invalid_grant'
    
    def test_google_token_refresh_success(self, mock_google_oauth_config):
        """Test successful token refresh."""
        config = mock_google_oauth_config
        
        # Generate and exchange auth code
        auth_code = self.server.generate_auth_code(
            client_id=config['client_id'],
            redirect_uri=config['redirect_uri'],
            scope=' '.join(config['scopes']),
            state='test_state'
        )
        
        token_response = self.server.mock_token_exchange(
            provider='google',
            code=auth_code,
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            redirect_uri=config['redirect_uri']
        )
        
        refresh_token = token_response['refresh_token']
        
        # Refresh the token
        refresh_response = self.server.mock_token_refresh(
            provider='google',
            refresh_token=refresh_token,
            client_id=config['client_id'],
            client_secret=config['client_secret']
        )
        
        assert 'access_token' in refresh_response
        assert refresh_response['token_type'] == 'Bearer'
        assert refresh_response['expires_in'] == 3600
        assert 'error' not in refresh_response
    
    def test_google_token_refresh_invalid_token(self, mock_google_oauth_config):
        """Test token refresh with invalid refresh token."""
        config = mock_google_oauth_config
        
        refresh_response = self.server.mock_token_refresh(
            provider='google',
            refresh_token='invalid_refresh_token',
            client_id=config['client_id'],
            client_secret=config['client_secret']
        )
        
        assert 'error' in refresh_response
        assert refresh_response['error'] == 'invalid_grant'


class TestMicrosoftOAuthMock:
    """Test Microsoft OAuth using mock server."""
    
    def setup_method(self):
        """Reset mock server before each test."""
        reset_mock_oauth_server()
        self.server = get_mock_oauth_server()
    
    def test_microsoft_authorization_url_generation(self, mock_microsoft_oauth_config):
        """Test generating Microsoft authorization URL."""
        config = mock_microsoft_oauth_config
        
        url = self.server.mock_microsoft_authorization_url(
            client_id=config['client_id'],
            redirect_uri=config['redirect_uri'],
            scopes=config['scopes'],
            state='test_state_ms',
            tenant=config['tenant']
        )
        
        assert 'login.microsoftonline.com' in url
        assert config['client_id'] in url
        assert config['tenant'] in url
        assert 'redirect_uri=' in url
        assert 'scope=' in url
        assert 'state=test_state_ms' in url
    
    def test_microsoft_token_exchange_success(self, mock_microsoft_oauth_config):
        """Test successful Microsoft token exchange."""
        config = mock_microsoft_oauth_config
        
        # Generate auth code
        auth_code = self.server.generate_auth_code(
            client_id=config['client_id'],
            redirect_uri=config['redirect_uri'],
            scope=' '.join(config['scopes']),
            state='test_state'
        )
        
        # Exchange code for token
        token_response = self.server.mock_token_exchange(
            provider='microsoft',
            code=auth_code,
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            redirect_uri=config['redirect_uri']
        )
        
        assert 'access_token' in token_response
        assert 'refresh_token' in token_response
        assert 'id_token' in token_response  # Microsoft-specific
        assert token_response['token_type'] == 'Bearer'
        assert 'error' not in token_response
    
    def test_microsoft_token_refresh_success(self, mock_microsoft_oauth_config):
        """Test successful Microsoft token refresh."""
        config = mock_microsoft_oauth_config
        
        # Generate and exchange auth code
        auth_code = self.server.generate_auth_code(
            client_id=config['client_id'],
            redirect_uri=config['redirect_uri'],
            scope=' '.join(config['scopes']),
            state='test_state'
        )
        
        token_response = self.server.mock_token_exchange(
            provider='microsoft',
            code=auth_code,
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            redirect_uri=config['redirect_uri']
        )
        
        refresh_token = token_response['refresh_token']
        
        # Refresh the token
        refresh_response = self.server.mock_token_refresh(
            provider='microsoft',
            refresh_token=refresh_token,
            client_id=config['client_id'],
            client_secret=config['client_secret']
        )
        
        assert 'access_token' in refresh_response
        assert 'error' not in refresh_response
