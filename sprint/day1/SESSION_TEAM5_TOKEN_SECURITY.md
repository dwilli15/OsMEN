# Team 5: Token Security - Task Session

**Agent**: @day1-team5-token-security  
**Session Started**: 2025-11-19  
**Status**: 🟢 ACTIVE - Integrates with All Teams  
**Orchestrator**: @day1-orchestrator

---

## 🎯 Your Mission

Implement secure token encryption, storage, and automatic refresh. Ensure all OAuth tokens are protected and never stored in plaintext.

---

## 📋 Hour 1-2: Token Encryption System

### Install Cryptography Library

```bash
pip install cryptography
```

### Create Encryption Manager

**File**: `integrations/security/encryption_manager.py`

```python
#!/usr/bin/env python3
"""
Encryption Manager
Secure token encryption using Fernet (symmetric encryption)
"""

import os
from pathlib import Path
from cryptography.fernet import Fernet


class EncryptionManager:
    """Manages encryption/decryption of sensitive data"""
    
    def __init__(self, key_file: str = None):
        """
        Initialize encryption manager
        
        Args:
            key_file: Path to encryption key file (default: ~/.osmen/encryption.key)
        """
        if key_file is None:
            key_file = Path.home() / '.osmen' / 'encryption.key'
        else:
            key_file = Path(key_file)
        
        self.key_file = key_file
        self.key = self._load_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _load_or_create_key(self) -> bytes:
        """Load existing key or generate new one"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            return self._generate_key()
    
    def _generate_key(self) -> bytes:
        """Generate new encryption key and save securely"""
        key = Fernet.generate_key()
        
        # Create directory with secure permissions
        self.key_file.parent.mkdir(mode=0o700, exist_ok=True)
        
        # Write key with secure permissions
        with open(self.key_file, 'wb') as f:
            f.write(key)
        
        # Ensure key file is read-only
        os.chmod(self.key_file, 0o600)
        
        return key
    
    def encrypt(self, data: str) -> bytes:
        """Encrypt string data"""
        return self.cipher.encrypt(data.encode())
    
    def decrypt(self, encrypted: bytes) -> str:
        """Decrypt data back to string"""
        return self.cipher.decrypt(encrypted).decode()
    
    def encrypt_dict(self, data: dict) -> bytes:
        """Encrypt dictionary (as JSON)"""
        import json
        return self.encrypt(json.dumps(data))
    
    def decrypt_dict(self, encrypted: bytes) -> dict:
        """Decrypt back to dictionary"""
        import json
        return json.loads(self.decrypt(encrypted))
    
    def rotate_key(self, old_key_file: str = None):
        """Rotate encryption key (re-encrypt all data with new key)"""
        # Advanced feature for key rotation
        pass
```

### Create Key Generation Script

**File**: `scripts/automation/generate_encryption_key.py`

```python
#!/usr/bin/env python3
"""Generate encryption key for OsMEN"""

from integrations.security.encryption_manager import EncryptionManager

if __name__ == '__main__':
    manager = EncryptionManager()
    print(f"✅ Encryption key generated: {manager.key_file}")
    print(f"   Permissions: {oct(manager.key_file.stat().st_mode)[-3:]}")
```

---

## 📋 Hour 3-4: Secure Token Storage

### Create Token Manager

**File**: `integrations/security/token_manager.py`

```python
#!/usr/bin/env python3
"""
Token Manager
Secure storage and retrieval of OAuth tokens
"""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from .encryption_manager import EncryptionManager


class TokenManager:
    """Manages secure storage of OAuth tokens"""
    
    def __init__(self, storage_path: str = None, encryption_manager: EncryptionManager = None):
        """
        Initialize token manager
        
        Args:
            storage_path: Path to token storage file
            encryption_manager: Encryption manager instance
        """
        if storage_path is None:
            storage_path = Path.home() / '.osmen' / 'tokens.enc'
        else:
            storage_path = Path(storage_path)
        
        self.storage_path = storage_path
        self.encryption = encryption_manager or EncryptionManager()
        
        # Ensure storage directory exists with secure permissions
        self.storage_path.parent.mkdir(mode=0o700, exist_ok=True)
    
    def store_token(self, provider: str, token_data: Dict) -> None:
        """
        Store encrypted token for provider
        
        Args:
            provider: OAuth provider name (google, microsoft, etc.)
            token_data: Token data dict (access_token, refresh_token, etc.)
        """
        # Load existing tokens
        all_tokens = self._load_all_tokens()
        
        # Add metadata
        token_data['stored_at'] = datetime.now().isoformat()
        token_data['provider'] = provider
        
        # Store for this provider
        all_tokens[provider] = token_data
        
        # Encrypt and save
        encrypted = self.encryption.encrypt_dict(all_tokens)
        with open(self.storage_path, 'wb') as f:
            f.write(encrypted)
        
        # Secure permissions
        self.storage_path.chmod(0o600)
    
    def get_token(self, provider: str) -> Optional[Dict]:
        """
        Retrieve decrypted token for provider
        
        Args:
            provider: OAuth provider name
            
        Returns:
            Token data dict or None if not found
        """
        all_tokens = self._load_all_tokens()
        return all_tokens.get(provider)
    
    def delete_token(self, provider: str) -> bool:
        """
        Delete token for provider
        
        Args:
            provider: OAuth provider name
            
        Returns:
            True if deleted, False if not found
        """
        all_tokens = self._load_all_tokens()
        if provider in all_tokens:
            del all_tokens[provider]
            encrypted = self.encryption.encrypt_dict(all_tokens)
            with open(self.storage_path, 'wb') as f:
                f.write(encrypted)
            return True
        return False
    
    def list_providers(self) -> list:
        """List all providers with stored tokens"""
        all_tokens = self._load_all_tokens()
        return list(all_tokens.keys())
    
    def _load_all_tokens(self) -> Dict:
        """Load all tokens from encrypted storage"""
        if not self.storage_path.exists():
            return {}
        
        try:
            with open(self.storage_path, 'rb') as f:
                encrypted = f.read()
            return self.encryption.decrypt_dict(encrypted)
        except Exception as e:
            # If decryption fails, return empty (corrupted file)
            return {}
```

---

## 📋 Hour 5-6: Automatic Token Refresh

### Create Token Refresher

**File**: `integrations/security/token_refresher.py`

```python
#!/usr/bin/env python3
"""
Token Refresher
Automatic token refresh before expiry
"""

from typing import Dict
from datetime import datetime, timedelta
from .token_manager import TokenManager


class TokenRefresher:
    """Handles automatic token refresh"""
    
    def __init__(self, token_manager: TokenManager, oauth_handlers: Dict):
        """
        Initialize token refresher
        
        Args:
            token_manager: TokenManager instance
            oauth_handlers: Dict of provider -> OAuthHandler instances
        """
        self.token_manager = token_manager
        self.oauth_handlers = oauth_handlers
    
    def refresh_if_needed(self, provider: str, threshold_seconds: int = 300) -> Dict:
        """
        Refresh token if expiring soon
        
        Args:
            provider: OAuth provider name
            threshold_seconds: Refresh if expiring within this many seconds
            
        Returns:
            Current (possibly refreshed) token data
        """
        token_data = self.token_manager.get_token(provider)
        
        if not token_data:
            raise ValueError(f"No token found for provider: {provider}")
        
        if self._is_expiring_soon(token_data, threshold_seconds):
            # Refresh the token
            refreshed = self._refresh_token(provider, token_data)
            self.token_manager.store_token(provider, refreshed)
            return refreshed
        
        return token_data
    
    def _is_expiring_soon(self, token_data: Dict, threshold_seconds: int) -> bool:
        """Check if token is expiring soon"""
        if 'expires_in' not in token_data or 'stored_at' not in token_data:
            return False
        
        stored_at = datetime.fromisoformat(token_data['stored_at'])
        expires_in = token_data['expires_in']
        expiry_time = stored_at + timedelta(seconds=expires_in)
        time_until_expiry = (expiry_time - datetime.now()).total_seconds()
        
        return time_until_expiry < threshold_seconds
    
    def _refresh_token(self, provider: str, token_data: Dict) -> Dict:
        """Refresh the token using OAuth handler"""
        if provider not in self.oauth_handlers:
            raise ValueError(f"No OAuth handler for provider: {provider}")
        
        handler = self.oauth_handlers[provider]
        refresh_token = token_data.get('refresh_token')
        
        if not refresh_token:
            raise ValueError(f"No refresh token available for provider: {provider}")
        
        # Call OAuth handler to refresh
        new_tokens = handler.refresh_token(refresh_token)
        
        # Merge with existing data (keep refresh_token if not returned)
        if 'refresh_token' not in new_tokens:
            new_tokens['refresh_token'] = refresh_token
        
        return new_tokens
```

---

## 📋 Hour 7-8: Security Logging & Integration

### Create Security Logger

**File**: `integrations/security/security_logger.py`

```python
#!/usr/bin/env python3
"""
Security Logger
Audit logging for security-sensitive operations
"""

import logging
from pathlib import Path
from typing import Any
import re


class SecurityLogger:
    """Logger for security events with sensitive data redaction"""
    
    def __init__(self, log_file: str = None):
        """Initialize security logger"""
        if log_file is None:
            log_file = Path.home() / '.osmen' / 'security.log'
        else:
            log_file = Path(log_file)
        
        log_file.parent.mkdir(mode=0o700, exist_ok=True)
        
        self.logger = logging.getLogger('osmen.security')
        self.logger.setLevel(logging.INFO)
        
        # File handler
        handler = logging.FileHandler(log_file, mode='a')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
    
    def log_token_operation(self, operation: str, provider: str, success: bool):
        """Log token storage/retrieval operations"""
        self.logger.info(f"Token {operation} for {provider}: {'SUCCESS' if success else 'FAILED'}")
    
    def log_encryption_operation(self, operation: str, success: bool):
        """Log encryption operations"""
        self.logger.info(f"Encryption {operation}: {'SUCCESS' if success else 'FAILED'}")
    
    def redact_sensitive_data(self, data: Any) -> str:
        """Redact sensitive data from logs"""
        text = str(data)
        
        # Redact tokens (anything that looks like a token)
        text = re.sub(r'["\']?access_token["\']?\s*:\s*["\']([^"\']+)["\']', 
                     '"access_token": "[REDACTED]"', text)
        text = re.sub(r'["\']?refresh_token["\']?\s*:\s*["\']([^"\']+)["\']',
                     '"refresh_token": "[REDACTED]"', text)
        text = re.sub(r'["\']?client_secret["\']?\s*:\s*["\']([^"\']+)["\']',
                     '"client_secret": "[REDACTED]"', text)
        
        return text
```

### Integration Tests

Create security tests to validate:
- No plaintext tokens in storage
- Encryption/decryption works correctly
- Token refresh works
- Security logging works

---

## 📊 Progress Checklist

- [ ] Encryption manager using Fernet
- [ ] Key generation with secure permissions
- [ ] Token manager with encrypted storage
- [ ] Multi-provider token support
- [ ] Token refresher with expiry detection
- [ ] Security logger with redaction
- [ ] Integration with Teams 1, 2, 3
- [ ] 20+ security tests passing
- [ ] No plaintext tokens validated

---

## 🔄 Communication

```python
orchestrator.receive_message(
    team_id='team5',
    message='Token encryption system complete, ready for integration',
    priority=TaskPriority.HIGH
)
```

---

## 🎯 Success Criteria

- ✅ Fernet encryption working
- ✅ Secure token storage operational
- ✅ Automatic token refresh
- ✅ Security logging with redaction
- ✅ Integration with all OAuth providers
- ✅ 20+ security tests passing
- ✅ Zero plaintext tokens

**Let's secure those tokens! 🔒**
