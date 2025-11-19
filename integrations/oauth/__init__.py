"""
OAuth integration module for OsMEN.

Provides OAuth 2.0 authentication for multiple providers:
- Google (Calendar, Gmail, Contacts)
- Microsoft (Outlook, Azure AD)
- GitHub
- OpenAI

Usage:
    from integrations.oauth import get_oauth_handler
    
    # Get a Google OAuth handler
    handler = get_oauth_handler('google', config)
    
    # Generate authorization URL
    auth_url = handler.get_authorization_url()
    
    # Exchange code for tokens
    tokens = handler.exchange_code_for_token(code)
"""

from .oauth_handler import OAuthHandler, OAuthError, OAuthTokenError, OAuthValidationError
from .oauth_registry import (
    OAuthProviderRegistry,
    get_registry,
    register_provider,
    get_oauth_handler
)
from .google_oauth import GoogleOAuthHandler

# Register Google OAuth provider with global registry
register_provider('google', GoogleOAuthHandler)

__all__ = [
    'OAuthHandler',
    'OAuthError',
    'OAuthTokenError',
    'OAuthValidationError',
    'OAuthProviderRegistry',
    'get_registry',
    'register_provider',
    'get_oauth_handler',
    'GoogleOAuthHandler'
]
