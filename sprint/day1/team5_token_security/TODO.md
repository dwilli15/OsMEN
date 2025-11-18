# Team 5: Token Management & Security - Day 1 TODO List

**Day 1 Focus**: Token Management & Security

**Team Focus**: Implement secure token storage, encryption, refresh automation, and security validation

**Timeline**: Day 1 - 8 hours

**Team Lead**: Security Engineer

---

## 🎯 Primary Objectives

- [ ] Build token encryption/decryption system
- [ ] Create secure token storage (TokenManager)
- [ ] Implement automatic token refresh automation
- [ ] Add token validation and health checks
- [ ] Implement credential validation
- [ ] Create OAuth error handling framework
- [ ] Build security logging system
- [ ] Ensure all security best practices implemented

---

## 📋 Detailed Task List

### Hour 1-2: Token Encryption System

#### Encryption Library Setup
- [ ] Install cryptography library
  ```bash
  pip install cryptography>=41.0.0
  ```
- [ ] Create `integrations/security/` directory structure

#### Encryption Manager Implementation
- [ ] Create `integrations/security/encryption_manager.py`
- [ ] Implement `EncryptionManager` class
  ```python
  from cryptography.fernet import Fernet
  from cryptography.hazmat.primitives import hashes
  from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
  import base64
  import os
  
  class EncryptionManager:
      """Manages encryption/decryption of sensitive data (tokens)."""
      
      def __init__(self, key_source=None):
          """Initialize with encryption key from environment or parameter."""
          if key_source is None:
              key_source = os.getenv('OAUTH_ENCRYPTION_KEY')
          
          if not key_source:
              raise ValueError("Encryption key must be provided")
          
          self.cipher = Fernet(key_source.encode())
      
      def encrypt_token(self, plaintext: str) -> str:
          """Encrypt a token."""
          if not plaintext:
              raise ValueError("Cannot encrypt empty token")
          
          encrypted = self.cipher.encrypt(plaintext.encode())
          return base64.urlsafe_b64encode(encrypted).decode()
      
      def decrypt_token(self, ciphertext: str) -> str:
          """Decrypt a token."""
          if not ciphertext:
              raise ValueError("Cannot decrypt empty ciphertext")
          
          try:
              decoded = base64.urlsafe_b64decode(ciphertext.encode())
              decrypted = self.cipher.decrypt(decoded)
              return decrypted.decode()
          except Exception as e:
              raise ValueError(f"Decryption failed: {e}")
  ```

#### Key Generation and Management
- [ ] Create key generation utility
  ```python
  @staticmethod
  def generate_key() -> str:
      """Generate a new encryption key."""
      return Fernet.generate_key().decode()
  ```

- [ ] Create `.env.example` with encryption key template
  ```bash
  # OAuth Encryption Key
  # Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
  OAUTH_ENCRYPTION_KEY=

  # Google OAuth Credentials
  GOOGLE_CLIENT_ID=
  GOOGLE_CLIENT_SECRET=

  # Microsoft OAuth Credentials
  MICROSOFT_CLIENT_ID=
  MICROSOFT_CLIENT_SECRET=
  ```

- [ ] Create key setup script
  - [ ] `scripts/generate_encryption_key.py`
    ```python
    #!/usr/bin/env python3
    """Generate encryption key for OAuth tokens."""
    from cryptography.fernet import Fernet
    
    print("Generated Encryption Key:")
    print(Fernet.generate_key().decode())
    print("\nAdd this to your .env file as OAUTH_ENCRYPTION_KEY")
    ```
  - [ ] Make executable: `chmod +x scripts/generate_encryption_key.py`

#### Encryption Testing
- [ ] Create `tests/unit/security/test_encryption.py`
  ```python
  import pytest
  from integrations.security.encryption_manager import EncryptionManager
  
  def test_encryption_round_trip():
      """Test encryption and decryption."""
      manager = EncryptionManager(EncryptionManager.generate_key())
      original = "test_access_token_12345"
      
      encrypted = manager.encrypt_token(original)
      decrypted = manager.decrypt_token(encrypted)
      
      assert decrypted == original
      assert encrypted != original  # Verify it was actually encrypted
  
  def test_encrypt_empty_token():
      """Test that encrypting empty token raises error."""
      manager = EncryptionManager(EncryptionManager.generate_key())
      with pytest.raises(ValueError):
          manager.encrypt_token("")
  
  # Add 8+ more tests
  ```

---

### Hour 3-4: Token Storage System

#### Token Manager Implementation
- [ ] Create `integrations/security/token_manager.py`
- [ ] Implement `TokenManager` class
  ```python
  import sqlite3
  from datetime import datetime, timedelta
  from typing import Optional, Dict
  from integrations.security.encryption_manager import EncryptionManager
  
  class TokenManager:
      """Manages secure storage and retrieval of OAuth tokens."""
      
      def __init__(self, db_path='~/.osmen/tokens.db', encryption_key=None):
          self.db_path = os.path.expanduser(db_path)
          self.encryptor = EncryptionManager(encryption_key)
          self._init_database()
      
      def _init_database(self):
          """Initialize the token database."""
          os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
          
          with sqlite3.connect(self.db_path) as conn:
              conn.execute('''
                  CREATE TABLE IF NOT EXISTS tokens (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      provider TEXT NOT NULL,
                      user_id TEXT NOT NULL,
                      access_token_encrypted TEXT NOT NULL,
                      refresh_token_encrypted TEXT,
                      expires_at TIMESTAMP NOT NULL,
                      scopes TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      UNIQUE(provider, user_id)
                  )
              ''')
              conn.commit()
          
          # Set secure file permissions (600)
          os.chmod(self.db_path, 0o600)
  ```

#### Token CRUD Operations
- [ ] Implement token storage
  ```python
  def save_token(self, provider: str, user_id: str, token_data: Dict) -> bool:
      """Save or update token."""
      encrypted_access = self.encryptor.encrypt_token(token_data['access_token'])
      encrypted_refresh = None
      if token_data.get('refresh_token'):
          encrypted_refresh = self.encryptor.encrypt_token(token_data['refresh_token'])
      
      expires_at = datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600))
      scopes = ' '.join(token_data.get('scopes', []))
      
      with sqlite3.connect(self.db_path) as conn:
          conn.execute('''
              INSERT OR REPLACE INTO tokens 
              (provider, user_id, access_token_encrypted, refresh_token_encrypted, expires_at, scopes, updated_at)
              VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
          ''', (provider, user_id, encrypted_access, encrypted_refresh, expires_at, scopes))
          conn.commit()
      
      return True
  ```

- [ ] Implement token retrieval
  ```python
  def get_token(self, provider: str, user_id: str) -> Optional[Dict]:
      """Retrieve and decrypt token."""
      with sqlite3.connect(self.db_path) as conn:
          conn.row_factory = sqlite3.Row
          cursor = conn.execute('''
              SELECT * FROM tokens WHERE provider = ? AND user_id = ?
          ''', (provider, user_id))
          row = cursor.fetchone()
      
      if not row:
          return None
      
      token = {
          'access_token': self.encryptor.decrypt_token(row['access_token_encrypted']),
          'expires_at': datetime.fromisoformat(row['expires_at']),
          'scopes': row['scopes'].split() if row['scopes'] else []
      }
      
      if row['refresh_token_encrypted']:
          token['refresh_token'] = self.encryptor.decrypt_token(row['refresh_token_encrypted'])
      
      return token
  ```

- [ ] Implement token deletion
  ```python
  def delete_token(self, provider: str, user_id: str) -> bool:
      """Delete a token."""
      with sqlite3.connect(self.db_path) as conn:
          conn.execute('DELETE FROM tokens WHERE provider = ? AND user_id = ?', (provider, user_id))
          conn.commit()
      return True
  ```

- [ ] Implement list all tokens
  ```python
  def list_tokens(self) -> List[Dict]:
      """List all stored tokens (without decrypting)."""
      with sqlite3.connect(self.db_path) as conn:
          conn.row_factory = sqlite3.Row
          cursor = conn.execute('''
              SELECT provider, user_id, expires_at, scopes, created_at, updated_at
              FROM tokens
          ''')
          return [dict(row) for row in cursor.fetchall()]
  ```

---

### Hour 5-6: Automatic Token Refresh

#### Token Refresh Automation
- [ ] Create `integrations/security/token_refresher.py`
- [ ] Implement `TokenRefresher` class
  ```python
  from datetime import datetime, timedelta
  from integrations.security.token_manager import TokenManager
  from integrations.oauth.oauth_handler import OAuthHandler
  import logging
  
  logger = logging.getLogger(__name__)
  
  class TokenRefresher:
      """Automatically refreshes expiring tokens."""
      
      def __init__(self, token_manager: TokenManager, oauth_registry):
          self.token_manager = token_manager
          self.oauth_registry = oauth_registry
      
      def check_and_refresh_token(self, provider: str, user_id: str) -> bool:
          """Check if token needs refresh and refresh if necessary."""
          token = self.token_manager.get_token(provider, user_id)
          
          if not token:
              logger.warning(f"No token found for {provider}/{user_id}")
              return False
          
          # Refresh if expiring within 5 minutes
          if self._is_expiring_soon(token['expires_at'], minutes=5):
              logger.info(f"Token expiring soon for {provider}/{user_id}, refreshing...")
              return self._refresh_token(provider, user_id, token)
          
          return True  # Token is still valid
      
      def _is_expiring_soon(self, expires_at: datetime, minutes: int = 5) -> bool:
          """Check if token expires within specified minutes."""
          return datetime.now() + timedelta(minutes=minutes) >= expires_at
      
      def _refresh_token(self, provider: str, user_id: str, token: Dict) -> bool:
          """Refresh an expiring token."""
          if 'refresh_token' not in token:
              logger.error(f"No refresh token available for {provider}/{user_id}")
              return False
          
          try:
              # Get OAuth handler for provider
              handler = self.oauth_registry.get_handler(provider)
              
              # Refresh the token
              new_token = handler.refresh_token(token['refresh_token'])
              
              # Save updated token
              self.token_manager.save_token(provider, user_id, new_token)
              
              logger.info(f"Successfully refreshed token for {provider}/{user_id}")
              return True
              
          except Exception as e:
              logger.error(f"Failed to refresh token for {provider}/{user_id}: {e}")
              return False
  ```

#### Background Refresh Scheduler
- [ ] Create periodic refresh checker
  ```python
  import time
  import threading
  
  class TokenRefreshScheduler:
      """Background scheduler for token refresh."""
      
      def __init__(self, token_refresher: TokenRefresher, check_interval=300):
          """Initialize with 5-minute default check interval."""
          self.refresher = token_refresher
          self.check_interval = check_interval
          self.running = False
          self.thread = None
      
      def start(self):
          """Start background refresh checking."""
          if self.running:
              return
          
          self.running = True
          self.thread = threading.Thread(target=self._refresh_loop, daemon=True)
          self.thread.start()
          logger.info("Token refresh scheduler started")
      
      def stop(self):
          """Stop background refresh checking."""
          self.running = False
          if self.thread:
              self.thread.join(timeout=5)
          logger.info("Token refresh scheduler stopped")
      
      def _refresh_loop(self):
          """Background loop to check and refresh tokens."""
          while self.running:
              try:
                  tokens = self.refresher.token_manager.list_tokens()
                  for token_info in tokens:
                      self.refresher.check_and_refresh_token(
                          token_info['provider'],
                          token_info['user_id']
                      )
              except Exception as e:
                  logger.error(f"Error in refresh loop: {e}")
              
              time.sleep(self.check_interval)
  ```

---

### Hour 7-8: Credential Validation and Error Handling

#### Credential Validation
- [ ] Create `integrations/security/credential_validator.py`
- [ ] Implement validation functions
  ```python
  import os
  import re
  from typing import List, Dict
  
  class CredentialValidator:
      """Validates OAuth credentials and configuration."""
      
      @staticmethod
      def validate_required_env_vars(required_vars: List[str]) -> Dict[str, bool]:
          """Check if required environment variables are set."""
          results = {}
          for var in required_vars:
              value = os.getenv(var)
              results[var] = bool(value and value.strip())
          return results
      
      @staticmethod
      def validate_client_id(client_id: str, provider: str = 'google') -> bool:
          """Validate client ID format."""
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
          """Validate redirect URI format."""
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
          """Check if .env is properly gitignored."""
          gitignore_path = '.gitignore'
          if not os.path.exists(gitignore_path):
              return False
          
          with open(gitignore_path, 'r') as f:
              content = f.read()
              return '.env' in content
  ```

#### OAuth Error Handling Framework
- [ ] Create `integrations/oauth/oauth_errors.py`
- [ ] Define custom exception hierarchy
  ```python
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
  ```

- [ ] Implement error parser
  ```python
  class OAuthErrorParser:
      """Parse OAuth error responses."""
      
      @staticmethod
      def parse_error_response(response_json: dict) -> OAuthError:
          """Parse error from OAuth provider response."""
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
  ```

#### Security Logging
- [ ] Create `integrations/security/security_logger.py`
- [ ] Implement security event logging
  ```python
  import logging
  from datetime import datetime
  from typing import Dict, Any
  import hashlib
  
  class SecurityLogger:
      """Logs security-related events."""
      
      def __init__(self, log_file='~/.osmen/security.log'):
          self.log_file = os.path.expanduser(log_file)
          self.logger = self._setup_logger()
      
      def _setup_logger(self):
          """Set up security logger with file handler."""
          logger = logging.getLogger('osmen.security')
          logger.setLevel(logging.INFO)
          
          # Create log directory
          os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
          
          # File handler with rotation
          handler = logging.handlers.RotatingFileHandler(
              self.log_file,
              maxBytes=10*1024*1024,  # 10MB
              backupCount=5
          )
          
          formatter = logging.Formatter(
              '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
          )
          handler.setFormatter(formatter)
          logger.addHandler(handler)
          
          return logger
      
      def log_oauth_event(self, event_type: str, provider: str, 
                         user_id: str, success: bool, details: Dict[str, Any] = None):
          """Log OAuth-related event."""
          # Hash user_id for privacy
          user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
          
          event = {
              'timestamp': datetime.now().isoformat(),
              'event_type': event_type,
              'provider': provider,
              'user_hash': user_hash,
              'success': success,
              'details': details or {}
          }
          
          if success:
              self.logger.info(f"OAuth Event: {event}")
          else:
              self.logger.warning(f"OAuth Event Failed: {event}")
      
      def log_token_event(self, event_type: str, provider: str, user_id: str):
          """Log token-related event (creation, refresh, deletion)."""
          self.log_oauth_event(event_type, provider, user_id, True, {'event': 'token_operation'})
      
      def log_security_error(self, error_type: str, details: Dict[str, Any]):
          """Log security error."""
          self.logger.error(f"Security Error - {error_type}: {details}")
  ```

---

## 🧪 Testing Requirements

### Unit Tests (15+ tests)
- [ ] Test encryption/decryption
  - [ ] Round-trip test
  - [ ] Invalid key test
  - [ ] Empty token test
  - [ ] Key generation test
- [ ] Test TokenManager
  - [ ] Save token test
  - [ ] Retrieve token test
  - [ ] Delete token test
  - [ ] List tokens test
  - [ ] Database initialization test
- [ ] Test TokenRefresher
  - [ ] Check expiring token test
  - [ ] Refresh token test
  - [ ] No refresh token test
  - [ ] Refresh failure test
- [ ] Test CredentialValidator
  - [ ] Validate client ID test
  - [ ] Validate redirect URI test
  - [ ] Check environment vars test

---

## 📦 Dependencies

```
# Add to requirements.txt
cryptography>=41.0.0
python-dotenv>=1.0.0
```

---

## 📊 Success Metrics

### End of Day 1 Deliverables
- [ ] Encryption system fully functional
- [ ] Token storage with encryption working
- [ ] Automatic token refresh implemented
- [ ] Credential validation framework complete
- [ ] OAuth error handling framework complete
- [ ] Security logging implemented
- [ ] 15+ security tests passing
- [ ] All tokens encrypted at rest
- [ ] Documentation complete
- [ ] Ready to integrate with Teams 1, 2, 3

---

## 🚀 Handoff to Other Teams

### For Team 1 (Google OAuth)
- TokenManager ready to store Google tokens
- Encryption ready for sensitive data
- Refresh automation ready

### For Team 2 (Microsoft OAuth)
- TokenManager ready for Microsoft tokens
- id_token storage support
- Refresh automation handles Microsoft's new refresh tokens

### For Team 3 (API Clients)
- Tokens available via TokenManager
- Automatic refresh ensures valid tokens
- Error handling for expired tokens

### For Team 4 (Testing)
- Security tests as examples
- Encryption tests complete
- Mock token storage for testing

---

## 📝 Notes

- Never log actual tokens, only hashes or IDs
- Always encrypt tokens at rest
- Use secure file permissions (600) for token database
- Implement automatic token refresh proactively
- Validate all inputs
- Handle all errors gracefully
- Log all security events
- Test encryption thoroughly
- Document key management procedures
- Prepare for key rotation (future)

---

**Team Contact**: Security Engineer  
**Status Updates**: Every 2 hours to Orchestration  
**Blockers**: Report immediately  
**Critical**: Security is everyone's responsibility

---

## 🎯 Ready to Execute!

Security first, always!

**LET'S SECURE IT! 🔐**
