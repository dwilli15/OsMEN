"""
OAuth Handler Base Class and Common Utilities.

Abstract base class for OAuth 2.0 providers with common utilities for:
- Authorization URL generation
- Token exchange
- Token refresh
- Token validation and revocation
- State parameter management (CSRF protection)
"""

import secrets
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


class OAuthHandler(ABC):
    """
    Abstract base class for OAuth 2.0 providers.
    
    All OAuth provider implementations (Google, Microsoft, etc.) should
    inherit from this class and implement the required methods.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OAuth handler with provider configuration.
        
        Args:
            config: Configuration dictionary containing:
                - client_id: OAuth application client ID
                - client_secret: OAuth application client secret
                - redirect_uri: Redirect URI for OAuth callback
                - scopes: List of OAuth scopes to request
                - Additional provider-specific configuration
        """
        self.config = config
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.redirect_uri = config.get('redirect_uri')
        self.scopes = config.get('scopes', [])
        
        # Validate required configuration
        if not self.client_id:
            raise ValueError("client_id is required in configuration")
        if not self.client_secret:
            raise ValueError("client_secret is required in configuration")
        if not self.redirect_uri:
            raise ValueError("redirect_uri is required in configuration")
    
    @abstractmethod
    def get_authorization_url(self, state: Optional[str] = None, **kwargs) -> str:
        """
        Generate OAuth authorization URL.
        
        Args:
            state: CSRF protection state parameter (auto-generated if not provided)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Authorization URL string
        """
        pass
    
    @abstractmethod
    def exchange_code_for_token(self, code: str, **kwargs) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth callback
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dictionary containing:
                - access_token: Access token string
                - refresh_token: Refresh token string (if available)
                - expires_in: Token expiration time in seconds
                - token_type: Token type (usually "Bearer")
                - scope: Granted scopes
        """
        pass
    
    @abstractmethod
    def refresh_token(self, refresh_token: str, **kwargs) -> Dict[str, Any]:
        """
        Refresh an expired access token.
        
        Args:
            refresh_token: Refresh token from previous token exchange
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dictionary containing:
                - access_token: New access token
                - expires_in: Token expiration time in seconds
                - token_type: Token type (usually "Bearer")
                - scope: Granted scopes
        """
        pass
    
    @abstractmethod
    def revoke_token(self, token: str, token_type: str = "access_token", **kwargs) -> bool:
        """
        Revoke an access or refresh token.
        
        Args:
            token: Token to revoke
            token_type: Type of token ("access_token" or "refresh_token")
            **kwargs: Additional provider-specific parameters
            
        Returns:
            True if revocation successful, False otherwise
        """
        pass
    
    @abstractmethod
    def validate_token(self, access_token: str, **kwargs) -> Dict[str, Any]:
        """
        Validate an access token and get token info.
        
        Args:
            access_token: Access token to validate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dictionary containing token information:
                - valid: Boolean indicating if token is valid
                - expires_at: Expiration timestamp (if available)
                - scope: Granted scopes
                - Additional provider-specific info
        """
        pass
    
    # Common utility methods
    
    @staticmethod
    def generate_state() -> str:
        """
        Generate a secure random state parameter for CSRF protection.
        
        Returns:
            URL-safe random string (32 bytes)
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def calculate_expiration(expires_in: int) -> datetime:
        """
        Calculate token expiration timestamp.
        
        Args:
            expires_in: Expiration time in seconds from now
            
        Returns:
            Datetime object representing expiration time
        """
        return datetime.now() + timedelta(seconds=expires_in)
    
    def format_scopes(self, scopes: Optional[List[str]] = None) -> str:
        """
        Format scopes for OAuth request (space-separated by default).
        
        Args:
            scopes: List of scope strings (uses self.scopes if not provided)
            
        Returns:
            Space-separated scope string
        """
        scope_list = scopes if scopes is not None else self.scopes
        return ' '.join(scope_list)
    
    def is_token_expired(self, expires_at: datetime) -> bool:
        """
        Check if a token is expired.
        
        Args:
            expires_at: Token expiration datetime
            
        Returns:
            True if token is expired, False otherwise
        """
        # Add 60 second buffer to account for clock skew
        return datetime.now() >= (expires_at - timedelta(seconds=60))


class OAuthError(Exception):
    """Base exception for OAuth errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 error_description: Optional[str] = None):
        """
        Initialize OAuth error.
        
        Args:
            message: Error message
            error_code: OAuth error code (if available)
            error_description: Detailed error description (if available)
        """
        super().__init__(message)
        self.error_code = error_code
        self.error_description = error_description


class OAuthAuthorizationError(OAuthError):
    """Error during authorization flow."""
    pass


class OAuthTokenError(OAuthError):
    """Error during token exchange or refresh."""
    pass


class OAuthValidationError(OAuthError):
    """Error during token validation."""
    pass
