#!/usr/bin/env python3
"""
GitHub OAuth Integration for Copilot Access

Provides OAuth2 authentication flow for GitHub Copilot API access.
Uses web-based login instead of API tokens.
"""

import os
import json
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlencode

import requests
from requests.exceptions import RequestException


class GitHubOAuthIntegration:
    """OAuth integration for GitHub Copilot"""
    
    # GitHub OAuth endpoints
    AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_API_URL = "https://api.github.com/user"
    COPILOT_API_URL = "https://api.githubcopilot.com"
    
    # OAuth scopes needed for Copilot
    SCOPES = ["read:user", "copilot"]
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        token_storage_path: Optional[str] = None
    ):
        """Initialize GitHub OAuth integration
        
        Args:
            client_id: GitHub OAuth App client ID
            client_secret: GitHub OAuth App client secret
            redirect_uri: OAuth callback URL
            token_storage_path: Path to store OAuth tokens
        """
        self.client_id = client_id or os.getenv("GITHUB_OAUTH_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("GITHUB_OAUTH_CLIENT_SECRET", "")
        self.redirect_uri = redirect_uri or os.getenv(
            "GITHUB_OAUTH_REDIRECT_URI",
            "http://localhost:8000/oauth/github/callback"
        )
        
        self.token_storage_path = Path(
            token_storage_path or os.getenv(
                "OAUTH_TOKEN_PATH",
                "./tokens/github_oauth_token.json"
            )
        )
        self.token_storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        
        # Load existing token if available
        self._load_token()
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate GitHub OAuth authorization URL
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL to redirect user to
        """
        if not state:
            state = secrets.token_urlsafe(32)
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.SCOPES),
            "state": state,
        }
        
        return f"{self.AUTHORIZE_URL}?{urlencode(params)}"
    
    def exchange_code_for_token(self, code: str) -> bool:
        """Exchange authorization code for access token
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            True if token exchange successful
        """
        try:
            response = requests.post(
                self.TOKEN_URL,
                headers={"Accept": "application/json"},
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                
                # GitHub tokens typically don't expire, but we'll set a long expiry
                expires_in = data.get("expires_in", 31536000)  # 1 year default
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                
                self._save_token()
                return True
            else:
                print(f"Token exchange failed: {response.status_code} - {response.text}")
                return False
                
        except RequestException as e:
            print(f"Error exchanging code for token: {e}")
            return False
    
    def refresh_access_token(self) -> bool:
        """Refresh the access token if expired
        
        Returns:
            True if refresh successful
        """
        # GitHub tokens don't typically need refresh, but we implement for completeness
        if not self.refresh_token:
            return False
        
        # For now, GitHub OAuth doesn't support refresh tokens in the standard flow
        # If token is expired, user needs to re-authenticate
        return False
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated with valid token
        
        Returns:
            True if authenticated and token is valid
        """
        if not self.access_token:
            return False
        
        if self.token_expiry and datetime.now() >= self.token_expiry:
            # Try to refresh
            if not self.refresh_access_token():
                return False
        
        return True
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get authenticated user information
        
        Returns:
            User information dict or None if failed
        """
        if not self.is_authenticated():
            return None
        
        try:
            response = requests.get(
                self.USER_API_URL,
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
    
    def make_copilot_request(
        self,
        endpoint: str,
        method: str = "POST",
        data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make request to GitHub Copilot API
        
        Args:
            endpoint: API endpoint (e.g., "/v1/chat/completions")
            method: HTTP method
            data: Request payload
            
        Returns:
            API response or None if failed
        """
        if not self.is_authenticated():
            print("Not authenticated. Please authenticate first.")
            return None
        
        url = f"{self.COPILOT_API_URL}{endpoint}"
        
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
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"Copilot API request failed: {response.status_code} - {response.text}")
                return None
                
        except RequestException as e:
            print(f"Error making Copilot request: {e}")
            return None
    
    def generate_code(
        self,
        prompt: str,
        language: Optional[str] = None,
        max_tokens: int = 1000
    ) -> Optional[str]:
        """Generate code using GitHub Copilot
        
        Args:
            prompt: Code generation prompt
            language: Programming language (optional)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated code or None if failed
        """
        system_message = "You are GitHub Copilot, an AI pair programmer."
        if language:
            system_message += f" Generate code in {language}."
        
        data = {
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.2,
            "stream": False
        }
        
        response = self.make_copilot_request("/v1/chat/completions", data=data)
        
        if response and "choices" in response:
            return response["choices"][0]["message"]["content"]
        
        return None
    
    def _save_token(self):
        """Save OAuth token to file"""
        token_data = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_expiry": self.token_expiry.isoformat() if self.token_expiry else None,
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
            
            expiry_str = token_data.get("token_expiry")
            if expiry_str:
                self.token_expiry = datetime.fromisoformat(expiry_str)
                
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading token: {e}")
    
    def logout(self):
        """Clear stored authentication"""
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        
        if self.token_storage_path.exists():
            self.token_storage_path.unlink()


def main():
    """Test GitHub OAuth integration"""
    print("GitHub OAuth Integration for Copilot")
    print("=" * 50)
    
    oauth = GitHubOAuthIntegration()
    
    if not oauth.client_id or not oauth.client_secret:
        print("\n⚠️  OAuth credentials not configured!")
        print("\nSet the following environment variables:")
        print("  GITHUB_OAUTH_CLIENT_ID")
        print("  GITHUB_OAUTH_CLIENT_SECRET")
        print("  GITHUB_OAUTH_REDIRECT_URI (optional)")
        print("\nTo create a GitHub OAuth App:")
        print("  1. Go to https://github.com/settings/developers")
        print("  2. Click 'New OAuth App'")
        print("  3. Set callback URL to http://localhost:8000/oauth/github/callback")
        return
    
    if oauth.is_authenticated():
        print("\n✅ Already authenticated")
        user_info = oauth.get_user_info()
        if user_info:
            print(f"   User: {user_info.get('login')}")
            print(f"   Name: {user_info.get('name')}")
    else:
        print("\n❌ Not authenticated")
        print("\nTo authenticate:")
        print(f"  1. Visit: {oauth.get_authorization_url()}")
        print("  2. Authorize the application")
        print("  3. You'll be redirected with a code parameter")


if __name__ == "__main__":
    main()
