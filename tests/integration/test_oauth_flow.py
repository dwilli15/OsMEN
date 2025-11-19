"""
Integration tests for OAuth flow.

These tests verify the complete OAuth flow from authorization to token management.
"""

import pytest
from tests.mocks.mock_oauth_server import get_mock_oauth_server, reset_mock_oauth_server
from tests.fixtures.oauth_fixtures import *


class TestGoogleOAuthFlow:
    """Test complete Google OAuth flow."""
    
    def setup_method(self):
        """Reset mock server before each test."""
        reset_mock_oauth_server()
        self.server = get_mock_oauth_server()
    
    @pytest.mark.integration
    @pytest.mark.oauth
    def test_complete_google_oauth_flow(self, mock_google_oauth_config):
        """Test complete OAuth flow from authorization URL to token."""
        config = mock_google_oauth_config
        
        # Step 1: Generate authorization URL
        auth_url = self.server.mock_google_authorization_url(
            client_id=config['client_id'],
            redirect_uri=config['redirect_uri'],
            scopes=config['scopes'],
            state='test_state_123'
        )
        
        assert 'accounts.google.com' in auth_url
        assert config['client_id'] in auth_url
        
        # Step 2: Simulate user authorization (get code)
        auth_code = self.server.generate_auth_code(
            client_id=config['client_id'],
            redirect_uri=config['redirect_uri'],
            scope=' '.join(config['scopes']),
            state='test_state_123'
        )
        
        assert auth_code is not None
        
        # Step 3: Exchange code for token
        token_response = self.server.mock_token_exchange(
            provider='google',
            code=auth_code,
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            redirect_uri=config['redirect_uri']
        )
        
        # Step 4: Validate token structure
        assert 'access_token' in token_response
        assert 'refresh_token' in token_response
        assert 'expires_in' in token_response
        assert 'token_type' in token_response
        assert token_response['token_type'] == 'Bearer'
        
        # Step 5: Verify token is stored
        assert token_response['access_token'] in self.server.tokens
        assert token_response['refresh_token'] in self.server.refresh_tokens
    
    @pytest.mark.integration
    @pytest.mark.oauth
    def test_google_token_refresh_flow(self, mock_google_oauth_config):
        """Test token refresh workflow."""
        config = mock_google_oauth_config
        
        # Step 1: Obtain initial tokens
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
        original_access_token = token_response['access_token']
        
        # Step 2: Use refresh token to get new access token
        refresh_response = self.server.mock_token_refresh(
            provider='google',
            refresh_token=refresh_token,
            client_id=config['client_id'],
            client_secret=config['client_secret']
        )
        
        # Step 3: Validate new token
        assert 'access_token' in refresh_response
        assert refresh_response['access_token'] != original_access_token
        assert 'expires_in' in refresh_response
        
        # Step 4: Verify new token is stored
        assert refresh_response['access_token'] in self.server.tokens


class TestMicrosoftOAuthFlow:
    """Test complete Microsoft OAuth flow."""
    
    def setup_method(self):
        """Reset mock server before each test."""
        reset_mock_oauth_server()
        self.server = get_mock_oauth_server()
    
    @pytest.mark.integration
    @pytest.mark.oauth
    def test_complete_microsoft_oauth_flow(self, mock_microsoft_oauth_config):
        """Test complete Microsoft OAuth flow."""
        config = mock_microsoft_oauth_config
        
        # Step 1: Generate authorization URL
        auth_url = self.server.mock_microsoft_authorization_url(
            client_id=config['client_id'],
            redirect_uri=config['redirect_uri'],
            scopes=config['scopes'],
            state='test_state_ms',
            tenant=config['tenant']
        )
        
        assert 'login.microsoftonline.com' in auth_url
        assert config['client_id'] in auth_url
        assert config['tenant'] in auth_url
        
        # Step 2: Simulate user authorization (get code)
        auth_code = self.server.generate_auth_code(
            client_id=config['client_id'],
            redirect_uri=config['redirect_uri'],
            scope=' '.join(config['scopes']),
            state='test_state_ms'
        )
        
        # Step 3: Exchange code for token
        token_response = self.server.mock_token_exchange(
            provider='microsoft',
            code=auth_code,
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            redirect_uri=config['redirect_uri']
        )
        
        # Step 4: Validate token structure (Microsoft-specific)
        assert 'access_token' in token_response
        assert 'refresh_token' in token_response
        assert 'id_token' in token_response  # Microsoft-specific
        assert 'ext_expires_in' in token_response  # Microsoft-specific
        assert token_response['token_type'] == 'Bearer'
    
    @pytest.mark.integration
    @pytest.mark.oauth
    def test_microsoft_token_refresh_flow(self, mock_microsoft_oauth_config):
        """Test Microsoft token refresh workflow."""
        config = mock_microsoft_oauth_config
        
        # Obtain initial tokens
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
        assert 'ext_expires_in' in refresh_response


class TestOAuthErrorHandling:
    """Test OAuth error handling scenarios."""
    
    def setup_method(self):
        """Reset mock server before each test."""
        reset_mock_oauth_server()
        self.server = get_mock_oauth_server()
    
    @pytest.mark.integration
    @pytest.mark.oauth
    def test_invalid_client_id_error(self, mock_google_oauth_config):
        """Test error handling for invalid client ID."""
        config = mock_google_oauth_config
        
        auth_code = self.server.generate_auth_code(
            client_id=config['client_id'],
            redirect_uri=config['redirect_uri'],
            scope='test_scope',
            state='test_state'
        )
        
        # Try to exchange with wrong client ID
        token_response = self.server.mock_token_exchange(
            provider='google',
            code=auth_code,
            client_id='wrong_client_id',
            client_secret=config['client_secret'],
            redirect_uri=config['redirect_uri']
        )
        
        assert 'error' in token_response
        assert token_response['error'] == 'invalid_client'
    
    @pytest.mark.integration
    @pytest.mark.oauth
    def test_authorization_code_expiry(self, mock_google_oauth_config):
        """Test that authorization codes can only be used once."""
        config = mock_google_oauth_config
        
        auth_code = self.server.generate_auth_code(
            client_id=config['client_id'],
            redirect_uri=config['redirect_uri'],
            scope='test_scope',
            state='test_state'
        )
        
        # First use - should succeed
        token_response1 = self.server.mock_token_exchange(
            provider='google',
            code=auth_code,
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            redirect_uri=config['redirect_uri']
        )
        
        assert 'access_token' in token_response1
        
        # Second use - should fail
        token_response2 = self.server.mock_token_exchange(
            provider='google',
            code=auth_code,
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            redirect_uri=config['redirect_uri']
        )
        
        assert 'error' in token_response2


class TestMultiProviderOAuth:
    """Test OAuth with multiple providers."""
    
    def setup_method(self):
        """Reset mock server before each test."""
        reset_mock_oauth_server()
        self.server = get_mock_oauth_server()
    
    @pytest.mark.integration
    @pytest.mark.oauth
    def test_multiple_providers_simultaneously(self, mock_google_oauth_config, mock_microsoft_oauth_config):
        """Test managing OAuth for multiple providers at once."""
        google_config = mock_google_oauth_config
        ms_config = mock_microsoft_oauth_config
        
        # Google OAuth flow
        google_code = self.server.generate_auth_code(
            client_id=google_config['client_id'],
            redirect_uri=google_config['redirect_uri'],
            scope='google_scope',
            state='google_state'
        )
        
        google_tokens = self.server.mock_token_exchange(
            provider='google',
            code=google_code,
            client_id=google_config['client_id'],
            client_secret=google_config['client_secret'],
            redirect_uri=google_config['redirect_uri']
        )
        
        # Microsoft OAuth flow
        ms_code = self.server.generate_auth_code(
            client_id=ms_config['client_id'],
            redirect_uri=ms_config['redirect_uri'],
            scope='microsoft_scope',
            state='ms_state'
        )
        
        ms_tokens = self.server.mock_token_exchange(
            provider='microsoft',
            code=ms_code,
            client_id=ms_config['client_id'],
            client_secret=ms_config['client_secret'],
            redirect_uri=ms_config['redirect_uri']
        )
        
        # Verify both providers have tokens
        assert 'access_token' in google_tokens
        assert 'access_token' in ms_tokens
        assert google_tokens['access_token'] != ms_tokens['access_token']
        
        # Verify id_token only in Microsoft response
        assert 'id_token' not in google_tokens
        assert 'id_token' in ms_tokens
