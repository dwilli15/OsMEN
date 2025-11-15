#!/usr/bin/env python3
"""
OpenAI OAuth Integration for Codex Access

Provides OAuth2 with PKCE authentication flow for OpenAI API access.
Uses web-based login instead of direct API keys.
"""

import os
import json
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlencode

import requests
from requests.exceptions import RequestException


class OpenAIOAuthIntegration:
    """OAuth integration for OpenAI Codex"""
    
    # OpenAI OAuth endpoints (Note: OpenAI primarily uses API keys, not OAuth)
    # This is a demonstration implementation for OAuth-like flows
    API_BASE_URL = "https://api.openai.com/v1"
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        token_storage_path: Optional[str] = None
    ):
        """Initialize OpenAI OAuth integration
        
        Args:
            client_id: OAuth client ID (if using OAuth flow)
            client_secret: OAuth client secret
            redirect_uri: OAuth callback URL
            token_storage_path: Path to store OAuth tokens
        """
        self.client_id = client_id or os.getenv("OPENAI_OAUTH_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("OPENAI_OAUTH_CLIENT_SECRET", "")
        self.redirect_uri = redirect_uri or os.getenv(
            "OPENAI_OAUTH_REDIRECT_URI",
            "http://localhost:8000/oauth/openai/callback"
        )
        
        self.token_storage_path = Path(
            token_storage_path or os.getenv(
                "OAUTH_TOKEN_PATH",
                "./tokens/openai_oauth_token.json"
            )
        )
        self.token_storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        
        # PKCE (Proof Key for Code Exchange) parameters
        self.code_verifier: Optional[str] = None
        self.code_challenge: Optional[str] = None
        
        # Load existing token if available
        self._load_token()
    
    def _generate_pkce_params(self) -> tuple[str, str]:
        """Generate PKCE code verifier and challenge
        
        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        # Generate code verifier (random string)
        self.code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(32)
        ).decode('utf-8').rstrip('=')
        
        # Generate code challenge (SHA256 hash of verifier)
        challenge_bytes = hashlib.sha256(self.code_verifier.encode('utf-8')).digest()
        self.code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')
        
        return self.code_verifier, self.code_challenge
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate OAuth authorization URL with PKCE
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL to redirect user to
        """
        if not state:
            state = secrets.token_urlsafe(32)
        
        # Generate PKCE parameters
        _, code_challenge = self._generate_pkce_params()
        
        # Note: This is a placeholder. OpenAI doesn't have a standard OAuth flow
        # In practice, you would use the OpenAI API key obtained through their dashboard
        # and potentially wrap it in an OAuth-like flow for your application
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openai",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        
        # Placeholder authorization URL
        auth_url = f"https://platform.openai.com/authorize"
        return f"{auth_url}?{urlencode(params)}"
    
    def exchange_code_for_token(self, code: str) -> bool:
        """Exchange authorization code for access token using PKCE
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            True if token exchange successful
        """
        # Note: OpenAI uses API keys, not OAuth tokens
        # This is a demonstration of how an OAuth flow would work
        # In practice, you'd store the API key securely
        
        if not self.code_verifier:
            print("Code verifier not found. Start authorization flow first.")
            return False
        
        try:
            # Placeholder token endpoint
            token_url = f"{self.API_BASE_URL}/oauth/token"
            
            response = requests.post(
                token_url,
                headers={"Accept": "application/json"},
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code",
                    "code_verifier": self.code_verifier,
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                
                expires_in = data.get("expires_in", 3600)
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                
                self._save_token()
                return True
            else:
                print(f"Token exchange failed: {response.status_code} - {response.text}")
                return False
                
        except RequestException as e:
            print(f"Error exchanging code for token: {e}")
            return False
    
    def set_api_key(self, api_key: str) -> bool:
        """Set OpenAI API key directly (alternative to OAuth)
        
        Args:
            api_key: OpenAI API key
            
        Returns:
            True if API key is valid
        """
        self.access_token = api_key
        self.token_expiry = datetime.now() + timedelta(days=365)  # Keys don't expire
        
        # Verify the API key works
        if self.is_authenticated() and self._verify_api_key():
            self._save_token()
            return True
        else:
            self.access_token = None
            return False
    
    def _verify_api_key(self) -> bool:
        """Verify that the API key works
        
        Returns:
            True if API key is valid
        """
        try:
            response = requests.get(
                f"{self.API_BASE_URL}/models",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                },
                timeout=10
            )
            return response.status_code == 200
        except RequestException:
            return False
    
    def refresh_access_token(self) -> bool:
        """Refresh the access token if expired
        
        Returns:
            True if refresh successful
        """
        if not self.refresh_token:
            return False
        
        try:
            token_url = f"{self.API_BASE_URL}/oauth/token"
            
            response = requests.post(
                token_url,
                headers={"Accept": "application/json"},
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token",
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                
                expires_in = data.get("expires_in", 3600)
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                
                self._save_token()
                return True
            else:
                return False
                
        except RequestException:
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
    
    def make_api_request(
        self,
        endpoint: str,
        method: str = "POST",
        data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make request to OpenAI API
        
        Args:
            endpoint: API endpoint (e.g., "/completions")
            method: HTTP method
            data: Request payload
            
        Returns:
            API response or None if failed
        """
        if not self.is_authenticated():
            print("Not authenticated. Please authenticate first.")
            return None
        
        url = f"{self.API_BASE_URL}{endpoint}"
        
        try:
            response = requests.request(
                method,
                url,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                json=data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"API request failed: {response.status_code} - {response.text}")
                return None
                
        except RequestException as e:
            print(f"Error making API request: {e}")
            return None
    
    def generate_code(
        self,
        prompt: str,
        model: str = "gpt-4",
        max_tokens: int = 1000,
        temperature: float = 0.2
    ) -> Optional[str]:
        """Generate code using OpenAI Codex/GPT
        
        Args:
            prompt: Code generation prompt
            model: Model to use (gpt-4, gpt-3.5-turbo, etc.)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated code or None if failed
        """
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful coding assistant."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        response = self.make_api_request("/chat/completions", data=data)
        
        if response and "choices" in response:
            return response["choices"][0]["message"]["content"]
        
        return None
    
    def list_models(self) -> Optional[list]:
        """List available models
        
        Returns:
            List of model IDs or None if failed
        """
        response = self.make_api_request("/models", method="GET")
        
        if response and "data" in response:
            return [model["id"] for model in response["data"]]
        
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
    """Test OpenAI OAuth integration"""
    print("OpenAI OAuth Integration")
    print("=" * 50)
    
    oauth = OpenAIOAuthIntegration()
    
    # Check if already authenticated
    if oauth.is_authenticated():
        print("\n✅ Already authenticated")
        models = oauth.list_models()
        if models:
            print(f"   Available models: {len(models)}")
            print(f"   Sample models: {', '.join(models[:5])}")
    else:
        print("\n❌ Not authenticated")
        print("\nTo authenticate:")
        print("  Option 1 (Recommended): Use API key")
        print("    api_key = os.getenv('OPENAI_API_KEY')")
        print("    oauth.set_api_key(api_key)")
        print("\n  Option 2: OAuth flow (if implemented by OpenAI)")
        print(f"    Visit: {oauth.get_authorization_url()}")


if __name__ == "__main__":
    main()
