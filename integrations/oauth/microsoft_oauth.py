#!/usr/bin/env python3
"""
Microsoft OAuth Integration for Azure AD
 
Provides OAuth2 authentication flow for Microsoft Graph API access.
Supports Azure AD with multi-tenant configuration.
"""

import os
import json
import secrets
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode, quote

import requests
from requests.exceptions import RequestException


class MicrosoftOAuthHandler:
    """
    Microsoft OAuth 2.0 with Azure AD implementation.
    
    Supports:
    - Authorization Code flow
    - Token refresh with rotation
    - Multi-tenant configuration
    - Microsoft Graph API scopes
    - ID token parsing
    - Admin consent flow
    """
    
    # Default endpoints (tenant will be substituted)
    AUTH_ENDPOINT_TEMPLATE = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
    TOKEN_ENDPOINT_TEMPLATE = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    LOGOUT_ENDPOINT_TEMPLATE = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/logout"
    ADMIN_CONSENT_TEMPLATE = "https://login.microsoftonline.com/{tenant}/adminconsent"
    
    # Microsoft Graph API
    GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
    
    # Default scopes
    DEFAULT_SCOPES = [
        "https://graph.microsoft.com/User.Read",
        "https://graph.microsoft.com/Calendars.ReadWrite",
        "https://graph.microsoft.com/Mail.ReadWrite",
        "https://graph.microsoft.com/Contacts.ReadWrite",
        "offline_access"  # Required for refresh tokens
    ]
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        tenant: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        token_storage_path: Optional[str] = None
    ):
        """
        Initialize Microsoft OAuth integration.
        
        Args:
            client_id: Azure AD application (client) ID
            client_secret: Azure AD client secret
            redirect_uri: OAuth callback URL
            tenant: Tenant ID or 'common', 'organizations', 'consumers'
            scopes: List of Microsoft Graph API scopes
            token_storage_path: Path to store OAuth tokens
        """
        self.client_id = client_id or os.getenv("MICROSOFT_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("MICROSOFT_CLIENT_SECRET", "")
        self.redirect_uri = redirect_uri or os.getenv(
            "MICROSOFT_OAUTH_REDIRECT_URI",
            "http://localhost:8080/oauth/callback/microsoft"
        )
        self.tenant = tenant or os.getenv("MICROSOFT_TENANT_ID", "common")
        self.scopes = scopes or self.DEFAULT_SCOPES
        
        # Build tenant-specific endpoints
        self.auth_endpoint = self.AUTH_ENDPOINT_TEMPLATE.format(tenant=self.tenant)
        self.token_endpoint = self.TOKEN_ENDPOINT_TEMPLATE.format(tenant=self.tenant)
        self.logout_endpoint = self.LOGOUT_ENDPOINT_TEMPLATE.format(tenant=self.tenant)
        self.admin_consent_endpoint = self.ADMIN_CONSENT_TEMPLATE.format(tenant=self.tenant)
        
        # Token storage
        self.token_storage_path = Path(
            token_storage_path or os.getenv(
                "MICROSOFT_OAUTH_TOKEN_PATH",
                "./tokens/microsoft_oauth_token.json"
            )
        )
        self.token_storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Token data
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self.id_token: Optional[str] = None
        self.user_info: Optional[Dict[str, Any]] = None
        
        # Load existing token if available
        self._load_token()
    
    def get_authorization_url(
        self,
        state: Optional[str] = None,
        prompt: str = "select_account",
        domain_hint: Optional[str] = None,
        login_hint: Optional[str] = None
    ) -> str:
        """
        Generate Microsoft OAuth authorization URL.
        
        Args:
            state: State parameter for CSRF protection (auto-generated if None)
            prompt: Prompt behavior ('select_account', 'login', 'consent', 'none')
            domain_hint: Pre-fill domain for user login
            login_hint: Pre-fill user email
            
        Returns:
            Authorization URL to redirect user to
        """
        if not state:
            state = secrets.token_urlsafe(32)
        
        # Microsoft requires scopes as space-separated string
        scope_str = " ".join(self.scopes)
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": scope_str,
            "response_type": "code",
            "state": state,
            "response_mode": "query",
        }
        
        # Add optional parameters
        if prompt:
            params["prompt"] = prompt
        if domain_hint:
            params["domain_hint"] = domain_hint
        if login_hint:
            params["login_hint"] = login_hint
        
        return f"{self.auth_endpoint}?{urlencode(params)}"
    
    def get_admin_consent_url(self, state: Optional[str] = None) -> str:
        """
        Generate admin consent URL for organization-wide permissions.
        
        Some scopes require admin consent. This generates a URL for
        tenant administrators to grant consent for all users.
        
        Args:
            state: State parameter for CSRF protection
            
        Returns:
            Admin consent URL
        """
        if not state:
            state = secrets.token_urlsafe(32)
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
        }
        
        return f"{self.admin_consent_endpoint}?{urlencode(params)}"
    
    def exchange_code_for_token(self, code: str) -> bool:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            True if token exchange successful
        """
        try:
            # Microsoft requires scope in token request
            scope_str = " ".join(self.scopes)
            
            response = requests.post(
                self.token_endpoint,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json"
                },
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code",
                    "scope": scope_str
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract tokens
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                self.id_token = data.get("id_token")
                
                # Calculate expiration
                expires_in = data.get("expires_in", 3600)
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                
                # Parse ID token for user info
                if self.id_token:
                    self.user_info = self._parse_id_token(self.id_token)
                
                self._save_token()
                return True
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                print(f"Token exchange failed: {response.status_code}")
                print(f"Error: {error_data.get('error')}")
                print(f"Description: {error_data.get('error_description')}")
                return False
                
        except RequestException as e:
            print(f"Error exchanging code for token: {e}")
            return False
    
    def refresh_access_token(self) -> bool:
        """
        Refresh the access token using refresh token.
        
        Note: Microsoft rotates refresh tokens - each refresh returns
        a new access token AND a new refresh token.
        
        Returns:
            True if refresh successful
        """
        if not self.refresh_token:
            print("No refresh token available")
            return False
        
        try:
            # Microsoft requires scope in refresh request
            scope_str = " ".join(self.scopes)
            
            response = requests.post(
                self.token_endpoint,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json"
                },
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token",
                    "scope": scope_str
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Update tokens (Microsoft returns NEW refresh token)
                self.access_token = data.get("access_token")
                new_refresh = data.get("refresh_token")
                if new_refresh:
                    self.refresh_token = new_refresh
                
                # Update expiration
                expires_in = data.get("expires_in", 3600)
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                
                self._save_token()
                return True
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                print(f"Token refresh failed: {response.status_code}")
                print(f"Error: {error_data.get('error')}")
                print(f"Description: {error_data.get('error_description')}")
                return False
                
        except RequestException as e:
            print(f"Error refreshing token: {e}")
            return False
    
    def validate_token(self) -> bool:
        """
        Validate the access token by making a test call to Microsoft Graph.
        
        Returns:
            True if token is valid
        """
        if not self.access_token:
            return False
        
        # Check expiration first
        if self.token_expiry and datetime.now() >= self.token_expiry:
            # Try to refresh
            if not self.refresh_access_token():
                return False
        
        # Test token with /me endpoint
        try:
            response = requests.get(
                f"{self.GRAPH_API_BASE}/me",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/json"
                },
                timeout=10
            )
            
            return response.status_code == 200
            
        except RequestException:
            return False
    
    def revoke_token(self) -> bool:
        """
        Revoke the access token.
        
        Note: Microsoft doesn't have a standard token revocation endpoint.
        This method clears local tokens. Users should revoke app access
        via Azure portal or account settings.
        
        Returns:
            True (always succeeds locally)
        """
        print("Note: Microsoft tokens must be revoked via Azure portal or account settings")
        print("Clearing local token storage...")
        
        self.access_token = None
        self.refresh_token = None
        self.id_token = None
        self.token_expiry = None
        self.user_info = None
        
        if self.token_storage_path.exists():
            self.token_storage_path.unlink()
        
        return True
    
    def is_authenticated(self) -> bool:
        """
        Check if user is authenticated with valid token.
        
        Returns:
            True if authenticated and token is valid
        """
        if not self.access_token:
            return False
        
        # Check expiration and auto-refresh if needed
        if self.token_expiry and datetime.now() >= self.token_expiry:
            if not self.refresh_access_token():
                return False
        
        return True
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """
        Get authenticated user information from Microsoft Graph.
        
        Returns:
            User information dict or None if failed
        """
        if not self.is_authenticated():
            return None
        
        try:
            response = requests.get(
                f"{self.GRAPH_API_BASE}/me",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/json"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get user info: {response.status_code}")
                return None
                
        except RequestException as e:
            print(f"Error getting user info: {e}")
            return None
    
    def make_graph_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Make request to Microsoft Graph API.
        
        Args:
            endpoint: API endpoint (e.g., "/me/calendar/events")
            method: HTTP method
            data: Request payload
            params: Query parameters
            
        Returns:
            API response or None if failed
        """
        if not self.is_authenticated():
            print("Not authenticated. Please authenticate first.")
            return None
        
        url = f"{self.GRAPH_API_BASE}{endpoint}"
        
        try:
            response = requests.request(
                method,
                url,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                json=data,
                params=params,
                timeout=30
            )
            
            if response.status_code in [200, 201, 204]:
                # 204 No Content returns empty body
                if response.status_code == 204:
                    return {"status": "success"}
                return response.json()
            else:
                print(f"Graph API request failed: {response.status_code} - {response.text}")
                return None
                
        except RequestException as e:
            print(f"Error making Graph request: {e}")
            return None
    
    def _parse_id_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """
        Parse Microsoft ID token (JWT) to extract user information.
        
        Note: This is a basic parser that doesn't verify signature.
        For production, use PyJWT library with signature verification.
        
        Args:
            id_token: JWT ID token string
            
        Returns:
            Decoded token payload or None if failed
        """
        try:
            # JWT format: header.payload.signature
            parts = id_token.split('.')
            if len(parts) != 3:
                return None
            
            # Decode payload (add padding if needed)
            payload = parts[1]
            padding = 4 - (len(payload) % 4)
            if padding != 4:
                payload += '=' * padding
            
            decoded = base64.urlsafe_b64decode(payload)
            return json.loads(decoded)
            
        except (ValueError, json.JSONDecodeError) as e:
            print(f"Error parsing ID token: {e}")
            return None
    
    def _save_token(self):
        """Save OAuth token to file"""
        token_data = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "id_token": self.id_token,
            "token_expiry": self.token_expiry.isoformat() if self.token_expiry else None,
            "user_info": self.user_info,
            "tenant": self.tenant,
            "scopes": self.scopes,
            "saved_at": datetime.now().isoformat()
        }
        
        with open(self.token_storage_path, "w") as f:
            json.dump(token_data, f, indent=2)
    
    def _load_token(self):
        """Load OAuth token from file"""
        if not self.token_storage_path.exists():
            return
        
        try:
            with open(self.token_storage_path, "r") as f:
                token_data = json.load(f)
            
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            self.id_token = token_data.get("id_token")
            self.user_info = token_data.get("user_info")
            
            expiry_str = token_data.get("token_expiry")
            if expiry_str:
                self.token_expiry = datetime.fromisoformat(expiry_str)
                
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading token: {e}")


def main():
    """Test Microsoft OAuth integration"""
    print("Microsoft OAuth Integration for Azure AD")
    print("=" * 70)
    
    oauth = MicrosoftOAuthHandler()
    
    if not oauth.client_id or not oauth.client_secret:
        print("\n⚠️  OAuth credentials not configured!")
        print("\nSet the following environment variables:")
        print("  MICROSOFT_CLIENT_ID")
        print("  MICROSOFT_CLIENT_SECRET")
        print("  MICROSOFT_TENANT_ID (optional, defaults to 'common')")
        print("  MICROSOFT_OAUTH_REDIRECT_URI (optional)")
        print("\nTo create an Azure AD OAuth App:")
        print("  1. Go to https://portal.azure.com")
        print("  2. Navigate to 'Azure Active Directory' > 'App registrations'")
        print("  3. Click 'New registration'")
        print("  4. Set redirect URI to http://localhost:8080/oauth/callback/microsoft")
        print("  5. Create a client secret in 'Certificates & secrets'")
        return
    
    print(f"\nTenant: {oauth.tenant}")
    print(f"Scopes: {', '.join(oauth.scopes[:3])}...")
    
    if oauth.is_authenticated():
        print("\n✅ Already authenticated")
        user_info = oauth.get_user_info()
        if user_info:
            print(f"   User: {user_info.get('userPrincipalName')}")
            print(f"   Name: {user_info.get('displayName')}")
            print(f"   Email: {user_info.get('mail')}")
        
        # Test token validation
        if oauth.validate_token():
            print("   Token is valid ✓")
        else:
            print("   Token validation failed ✗")
    else:
        print("\n❌ Not authenticated")
        print("\nTo authenticate:")
        auth_url = oauth.get_authorization_url()
        print(f"  1. Visit: {auth_url}")
        print("  2. Authorize the application")
        print("  3. You'll be redirected with a code parameter")
        print("  4. Call exchange_code_for_token(code)")
        
        print("\nFor admin consent (if needed):")
        admin_url = oauth.get_admin_consent_url()
        print(f"  Visit: {admin_url}")


if __name__ == "__main__":
    main()
