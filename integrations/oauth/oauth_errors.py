#!/usr/bin/env python3
"""OAuth Error Handling Framework

Defines exception hierarchy and error parsing for OAuth operations.
"""


class OAuthError(Exception):
    """Base exception for OAuth errors."""
    pass


class OAuthConfigError(OAuthError):
    """OAuth configuration error."""
    pass


class OAuthAuthorizationError(OAuthError):
    """Authorization failed."""
    pass


class OAuthTokenExchangeError(OAuthError):
    """Token exchange failed."""
    pass


class OAuthTokenRefreshError(OAuthError):
    """Token refresh failed."""
    pass


class OAuthInvalidTokenError(OAuthError):
    """Token is invalid or expired."""
    pass


class OAuthRateLimitError(OAuthError):
    """Rate limit exceeded."""
    pass


class OAuthErrorParser:
    """Parse OAuth error responses."""
    
    @staticmethod
    def parse_error_response(response_json: dict) -> OAuthError:
        """Parse error from OAuth provider response.
        
        Args:
            response_json: Error response from OAuth provider
        
        Returns:
            Appropriate OAuthError subclass
        """
        error = response_json.get('error', 'unknown_error')
        error_description = response_json.get('error_description', '')
        
        error_map = {
            'invalid_client': OAuthConfigError,
            'invalid_grant': OAuthTokenExchangeError,
            'invalid_token': OAuthInvalidTokenError,
            'unauthorized_client': OAuthAuthorizationError,
            'access_denied': OAuthAuthorizationError,
        }
        
        exception_class = error_map.get(error, OAuthError)
        message = f"{error}: {error_description}" if error_description else error
        
        return exception_class(message)
