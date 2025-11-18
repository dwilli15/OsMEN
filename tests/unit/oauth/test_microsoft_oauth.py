#!/usr/bin/env python3
"""
Unit tests for Microsoft OAuth Handler

Tests Microsoft OAuth 2.0 implementation with Azure AD integration.
"""

import os
import sys
import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from integrations.oauth.microsoft_oauth import MicrosoftOAuthHandler


class TestMicrosoftOAuthHandler:
    """Test suite for MicrosoftOAuthHandler"""
    
    @pytest.fixture
    def handler(self, tmp_path):
        """Create a test OAuth handler instance"""
        token_path = tmp_path / "test_token.json"
        return MicrosoftOAuthHandler(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080/callback",
            tenant="common",
            token_storage_path=str(token_path)
        )
    
    @pytest.fixture
    def mock_token_response(self) -> Dict[str, Any]:
        """Mock successful token response from Microsoft"""
        return {
            "token_type": "Bearer",
            "scope": "User.Read Calendars.ReadWrite offline_access",
            "expires_in": 3600,
            "ext_expires_in": 3600,
            "access_token": "test_access_token_12345",
            "refresh_token": "test_refresh_token_67890",
            "id_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiZW1haWwiOiJqb2huQGV4YW1wbGUuY29tIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        }
    
    @pytest.fixture
    def mock_user_info(self) -> Dict[str, Any]:
        """Mock user information from Microsoft Graph"""
        return {
            "id": "12345678-1234-1234-1234-123456789012",
            "displayName": "John Doe",
            "userPrincipalName": "john.doe@example.com",
            "mail": "john.doe@example.com"
        }
    
    def test_initialization(self, handler):
        """Test OAuth handler initialization"""
        assert handler.client_id == "test_client_id"
        assert handler.client_secret == "test_client_secret"
        assert handler.redirect_uri == "http://localhost:8080/callback"
        assert handler.tenant == "common"
        assert handler.access_token is None
        assert handler.refresh_token is None
    
    def test_authorization_url_generation(self, handler):
        """Test authorization URL generation"""
        auth_url = handler.get_authorization_url(state="test_state_123")
        
        # Verify URL contains required parameters
        assert handler.auth_endpoint in auth_url
        assert "client_id=test_client_id" in auth_url
        assert "response_type=code" in auth_url
        assert "state=test_state_123" in auth_url
        assert "offline_access" in auth_url
    
    @patch('requests.post')
    def test_exchange_code_for_token_success(self, mock_post, handler, mock_token_response):
        """Test successful token exchange"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_token_response
        mock_post.return_value = mock_response
        
        success = handler.exchange_code_for_token("test_auth_code")
        
        assert success is True
        assert handler.access_token == "test_access_token_12345"
        assert handler.refresh_token == "test_refresh_token_67890"
    
    @patch('requests.post')
    def test_refresh_token_success(self, mock_post, handler, mock_token_response):
        """Test successful token refresh"""
        handler.refresh_token = "old_refresh_token"
        
        refresh_response = mock_token_response.copy()
        refresh_response['access_token'] = "new_access_token"
        refresh_response['refresh_token'] = "new_refresh_token"
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = refresh_response
        mock_post.return_value = mock_response
        
        success = handler.refresh_access_token()
        
        assert success is True
        assert handler.access_token == "new_access_token"
        assert handler.refresh_token == "new_refresh_token"


def run_tests():
    """Run tests with pytest"""
    import subprocess
    
    result = subprocess.run(
        ["python3", "-m", "pytest", __file__, "-v"],
        cwd=Path(__file__).parent.parent.parent.parent
    )
    
    return result.returncode


if __name__ == "__main__":
    print("Microsoft OAuth Handler Unit Tests")
    print("=" * 70)
    
    try:
        import pytest
        print("\nRunning tests with pytest...\n")
        exit_code = run_tests()
        sys.exit(exit_code)
    except ImportError:
        print("\n⚠️  pytest not installed")
        print("Install with: pip install pytest pytest-mock")
