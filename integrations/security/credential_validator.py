#!/usr/bin/env python3
"""
Credential Validator for OAuth Configuration

Validates OAuth credentials and configuration before use.
"""

import os
import re
from typing import List, Dict


class CredentialValidator:
    """Validates OAuth credentials and configuration."""
    
    @staticmethod
    def validate_required_env_vars(required_vars: List[str]) -> Dict[str, bool]:
        """Check if required environment variables are set.
        
        Args:
            required_vars: List of required variable names
        
        Returns:
            Dict mapping variable names to whether they're set
        """
        results = {}
        for var in required_vars:
            value = os.getenv(var)
            results[var] = bool(value and value.strip())
        return results
    
    @staticmethod
    def validate_client_id(client_id: str, provider: str = 'google') -> bool:
        """Validate client ID format.
        
        Args:
            client_id: Client ID to validate
            provider: Provider type ('google' or 'microsoft')
        
        Returns:
            True if format is valid
        """
        if not client_id or not client_id.strip():
            return False
        
        if provider == 'google':
            # Google client IDs typically end with .apps.googleusercontent.com
            pattern = r'^[\w\-]+\.apps\.googleusercontent\.com$'
            return bool(re.match(pattern, client_id))
        elif provider == 'microsoft':
            # Microsoft client IDs are UUIDs
            pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
            return bool(re.match(pattern, client_id, re.IGNORECASE))
        
        return True  # Unknown provider, skip format validation
    
    @staticmethod
    def validate_redirect_uri(uri: str) -> bool:
        """Validate redirect URI format.
        
        Args:
            uri: Redirect URI to validate
        
        Returns:
            True if format is valid
        """
        if not uri:
            return False
        
        # Must be http or https
        if not (uri.startswith('http://') or uri.startswith('https://')):
            return False
        
        # Should not contain fragments
        if '#' in uri:
            return False
        
        return True
    
    @staticmethod
    def check_secrets_not_committed() -> bool:
        """Check if .env is properly gitignored.
        
        Returns:
            True if .env is in .gitignore
        """
        gitignore_path = '.gitignore'
        if not os.path.exists(gitignore_path):
            return False
        
        with open(gitignore_path, 'r') as f:
            content = f.read()
            return '.env' in content
