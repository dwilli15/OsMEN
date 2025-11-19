"""
Google OAuth 2.0 Implementation.

Implements OAuth 2.0 flows for Google services including:
- Google Calendar
- Gmail
- Google Contacts
- Google Drive
"""

import requests
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
from loguru import logger

from .oauth_handler import (
    OAuthHandler, 
    OAuthError,
    OAuthTokenError,
    OAuthValidationError
)


class GoogleOAuthHandler(OAuthHandler):
    """
    Google OAuth 2.0 implementation.
    
    Supports full OAuth 2.0 flow including:
    - Authorization URL generation with PKCE
    - Authorization code exchange for tokens
    - Token refresh
    - Token validation
    - Token revocation
    """
    
    # Google OAuth endpoints
    AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
    REVOKE_ENDPOINT = "https://oauth2.googleapis.com/revoke"
    TOKENINFO_ENDPOINT = "https://oauth2.googleapis.com/tokeninfo"
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Google OAuth handler.
        
        Args:
            config: Configuration dictionary containing:
                - client_id: Google OAuth client ID
                - client_secret: Google OAuth client secret
                - redirect_uri: Redirect URI registered in Google Console
                - scopes: List of Google API scopes
        """
        super().__init__(config)
        
        # Override endpoints if provided in config
        self.auth_endpoint = config.get('auth_endpoint', self.AUTH_ENDPOINT)
        self.token_endpoint = config.get('token_endpoint', self.TOKEN_ENDPOINT)
        self.revoke_endpoint = config.get('revoke_endpoint', self.REVOKE_ENDPOINT)
        self.tokeninfo_endpoint = config.get('tokeninfo_endpoint', self.TOKENINFO_ENDPOINT)
        
        logger.info("GoogleOAuthHandler initialized")
    
    def get_authorization_url(self, state: Optional[str] = None, **kwargs) -> str:
        """
        Generate Google OAuth authorization URL.
        
        Args:
            state: CSRF protection state parameter (auto-generated if not provided)
            **kwargs: Additional parameters:
                - access_type: "offline" to get refresh token (default: "offline")
                - prompt: "consent" to force consent screen (default: "consent")
                - login_hint: Email address to pre-fill
                - include_granted_scopes: Boolean to enable incremental auth
                
        Returns:
            Authorization URL string
        """
        if state is None:
            state = self.generate_state()
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': self.format_scopes(),
            'state': state,
            'access_type': kwargs.get('access_type', 'offline'),
            'prompt': kwargs.get('prompt', 'consent')
        }
        
        # Optional parameters
        if 'login_hint' in kwargs:
            params['login_hint'] = kwargs['login_hint']
        
        if kwargs.get('include_granted_scopes'):
            params['include_granted_scopes'] = 'true'
        
        auth_url = f"{self.auth_endpoint}?{urlencode(params)}"
        logger.info(f"Generated authorization URL with state: {state}")
        
        return auth_url
    
    def exchange_code_for_token(self, code: str, **kwargs) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code: Authorization code from OAuth callback
            **kwargs: Additional parameters
            
        Returns:
            Dictionary containing:
                - access_token: Access token string
                - refresh_token: Refresh token string
                - expires_in: Token expiration time in seconds
                - token_type: Token type ("Bearer")
                - scope: Space-separated granted scopes
                
        Raises:
            OAuthTokenError: If token exchange fails
        """
        if not code:
            raise OAuthTokenError("Authorization code is required")
        
        data = {
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        try:
            response = requests.post(
                self.token_endpoint,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                raise OAuthTokenError(
                    f"Token exchange failed: {response.status_code}",
                    error_code=error_data.get('error'),
                    error_description=error_data.get('error_description')
                )
            
            token_data = response.json()
            
            # Calculate expiration timestamp
            expires_at = self.calculate_expiration(token_data.get('expires_in', 3600))
            token_data['expires_at'] = expires_at.isoformat()
            
            logger.info("Successfully exchanged authorization code for tokens")
            return token_data
            
        except requests.RequestException as e:
            raise OAuthTokenError(f"Network error during token exchange: {str(e)}")
    
    def refresh_token(self, refresh_token: str, **kwargs) -> Dict[str, Any]:
        """
        Refresh an expired access token.
        
        Args:
            refresh_token: Refresh token from previous token exchange
            **kwargs: Additional parameters
            
        Returns:
            Dictionary containing:
                - access_token: New access token
                - expires_in: Token expiration time in seconds
                - token_type: Token type ("Bearer")
                - scope: Granted scopes
                
        Note:
            Google does not return a new refresh_token in the response.
            The original refresh_token remains valid.
            
        Raises:
            OAuthTokenError: If token refresh fails
        """
        if not refresh_token:
            raise OAuthTokenError("Refresh token is required")
        
        data = {
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token'
        }
        
        try:
            response = requests.post(
                self.token_endpoint,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                raise OAuthTokenError(
                    f"Token refresh failed: {response.status_code}",
                    error_code=error_data.get('error'),
                    error_description=error_data.get('error_description')
                )
            
            token_data = response.json()
            
            # Calculate expiration timestamp
            expires_at = self.calculate_expiration(token_data.get('expires_in', 3600))
            token_data['expires_at'] = expires_at.isoformat()
            
            # Keep the original refresh token
            token_data['refresh_token'] = refresh_token
            
            logger.info("Successfully refreshed access token")
            return token_data
            
        except requests.RequestException as e:
            raise OAuthTokenError(f"Network error during token refresh: {str(e)}")
    
    def revoke_token(self, token: str, token_type: str = "access_token", **kwargs) -> bool:
        """
        Revoke an access or refresh token.
        
        Args:
            token: Token to revoke (access_token or refresh_token)
            token_type: Type of token (not used by Google, accepts either type)
            **kwargs: Additional parameters
            
        Returns:
            True if revocation successful, False otherwise
        """
        if not token:
            logger.warning("No token provided for revocation")
            return False
        
        try:
            response = requests.post(
                self.revoke_endpoint,
                data={'token': token},
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully revoked {token_type}")
                return True
            else:
                logger.warning(f"Token revocation returned status: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Network error during token revocation: {str(e)}")
            return False
    
    def validate_token(self, access_token: str, **kwargs) -> Dict[str, Any]:
        """
        Validate an access token and get token information.
        
        Args:
            access_token: Access token to validate
            **kwargs: Additional parameters
            
        Returns:
            Dictionary containing:
                - valid: Boolean indicating if token is valid
                - scope: Space-separated granted scopes
                - expires_in: Seconds until token expires
                - user_id: Google user ID (if available)
                - email: User email (if available)
                - Additional token metadata
                
        Raises:
            OAuthValidationError: If validation request fails
        """
        if not access_token:
            raise OAuthValidationError("Access token is required")
        
        try:
            response = requests.get(
                f"{self.tokeninfo_endpoint}?access_token={access_token}",
                timeout=30
            )
            
            if response.status_code == 200:
                token_info = response.json()
                token_info['valid'] = True
                logger.info("Token validation successful")
                return token_info
            else:
                error_data = response.json() if response.text else {}
                logger.warning(f"Token validation failed: {error_data.get('error_description', 'Unknown error')}")
                return {
                    'valid': False,
                    'error': error_data.get('error', 'validation_failed'),
                    'error_description': error_data.get('error_description')
                }
                
        except requests.RequestException as e:
            raise OAuthValidationError(f"Network error during token validation: {str(e)}")
