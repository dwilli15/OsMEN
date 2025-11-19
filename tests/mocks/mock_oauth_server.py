"""
Mock OAuth server for testing OAuth flows without hitting real endpoints.
"""

import json
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs
import base64
import hashlib


class MockOAuthServer:
    """
    Mock OAuth 2.0 server for testing.
    
    Simulates OAuth providers (Google, Microsoft) for testing purposes.
    """
    
    def __init__(self):
        """Initialize mock OAuth server."""
        self.auth_codes: Dict[str, Dict] = {}
        self.tokens: Dict[str, Dict] = {}
        self.refresh_tokens: Dict[str, Dict] = {}
        
        # Track requests for testing
        self.authorization_requests = []
        self.token_requests = []
        self.refresh_requests = []
    
    def generate_auth_code(self, client_id: str, redirect_uri: str, scope: str, state: str) -> str:
        """Generate an authorization code."""
        auth_code = f"auth_code_{len(self.auth_codes)}"
        
        self.auth_codes[auth_code] = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': scope,
            'state': state,
            'used': False,
        }
        
        return auth_code
    
    def mock_google_authorization_url(self, client_id: str, redirect_uri: str, 
                                     scopes: list, state: str) -> str:
        """Generate mock Google authorization URL."""
        scope_str = ' '.join(scopes)
        
        # Track the request
        self.authorization_requests.append({
            'provider': 'google',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': scope_str,
            'state': state,
        })
        
        # Return a mock URL
        url = (
            f"https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope={scope_str}"
            f"&state={state}"
            f"&access_type=offline"
            f"&prompt=consent"
            f"&response_type=code"
        )
        
        return url
    
    def mock_microsoft_authorization_url(self, client_id: str, redirect_uri: str,
                                        scopes: list, state: str, tenant: str = 'common') -> str:
        """Generate mock Microsoft authorization URL."""
        scope_str = ' '.join(scopes)
        
        # Track the request
        self.authorization_requests.append({
            'provider': 'microsoft',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': scope_str,
            'state': state,
            'tenant': tenant,
        })
        
        # Return a mock URL
        url = (
            f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope={scope_str}"
            f"&state={state}"
            f"&response_type=code"
            f"&response_mode=query"
        )
        
        return url
    
    def mock_token_exchange(self, provider: str, code: str, client_id: str,
                           client_secret: str, redirect_uri: str) -> Dict[str, Any]:
        """Mock token exchange endpoint."""
        # Validate auth code
        if code not in self.auth_codes:
            return {
                'error': 'invalid_grant',
                'error_description': 'Invalid authorization code',
            }
        
        auth_code_data = self.auth_codes[code]
        
        if auth_code_data['used']:
            return {
                'error': 'invalid_grant',
                'error_description': 'Authorization code already used',
            }
        
        if auth_code_data['client_id'] != client_id:
            return {
                'error': 'invalid_client',
                'error_description': 'Client ID mismatch',
            }
        
        # Mark code as used
        auth_code_data['used'] = True
        
        # Generate tokens
        access_token = f"{provider}_access_token_{len(self.tokens)}"
        refresh_token = f"{provider}_refresh_token_{len(self.refresh_tokens)}"
        
        token_data = {
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': 3600,
            'refresh_token': refresh_token,
            'scope': auth_code_data['scope'],
        }
        
        # Add provider-specific fields
        if provider == 'microsoft':
            token_data['id_token'] = f"microsoft_id_token_mock_{len(self.tokens)}"
            token_data['ext_expires_in'] = 3600
        
        # Store tokens
        self.tokens[access_token] = {
            'provider': provider,
            'client_id': client_id,
            'scope': auth_code_data['scope'],
            'expires_in': 3600,
        }
        
        self.refresh_tokens[refresh_token] = {
            'provider': provider,
            'client_id': client_id,
            'scope': auth_code_data['scope'],
        }
        
        # Track request
        self.token_requests.append({
            'provider': provider,
            'code': code,
            'client_id': client_id,
        })
        
        return token_data
    
    def mock_token_refresh(self, provider: str, refresh_token: str,
                          client_id: str, client_secret: str) -> Dict[str, Any]:
        """Mock token refresh endpoint."""
        # Validate refresh token
        if refresh_token not in self.refresh_tokens:
            return {
                'error': 'invalid_grant',
                'error_description': 'Invalid refresh token',
            }
        
        refresh_token_data = self.refresh_tokens[refresh_token]
        
        if refresh_token_data['client_id'] != client_id:
            return {
                'error': 'invalid_client',
                'error_description': 'Client ID mismatch',
            }
        
        # Generate new access token
        new_access_token = f"{provider}_access_token_refreshed_{len(self.tokens)}"
        
        token_data = {
            'access_token': new_access_token,
            'token_type': 'Bearer',
            'expires_in': 3600,
            'scope': refresh_token_data['scope'],
        }
        
        # Add provider-specific fields
        if provider == 'microsoft':
            token_data['ext_expires_in'] = 3600
        
        # Store new token
        self.tokens[new_access_token] = {
            'provider': provider,
            'client_id': client_id,
            'scope': refresh_token_data['scope'],
            'expires_in': 3600,
        }
        
        # Track request
        self.refresh_requests.append({
            'provider': provider,
            'refresh_token': refresh_token,
            'client_id': client_id,
        })
        
        return token_data
    
    def reset(self):
        """Reset the mock server state."""
        self.auth_codes.clear()
        self.tokens.clear()
        self.refresh_tokens.clear()
        self.authorization_requests.clear()
        self.token_requests.clear()
        self.refresh_requests.clear()


# Singleton instance for testing
_mock_oauth_server = None


def get_mock_oauth_server() -> MockOAuthServer:
    """Get or create the singleton mock OAuth server."""
    global _mock_oauth_server
    if _mock_oauth_server is None:
        _mock_oauth_server = MockOAuthServer()
    return _mock_oauth_server


def reset_mock_oauth_server():
    """Reset the mock OAuth server."""
    global _mock_oauth_server
    if _mock_oauth_server is not None:
        _mock_oauth_server.reset()
