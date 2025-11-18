# Team 5: Token Management & Security

**Status**: ✅ Implementation Complete  
**Tests**: 26+ tests passing  
**Coverage**: Comprehensive security coverage

---

## Overview

Team 5 implements secure token management and OAuth security for the OsMEN system. This includes:

- **Token Encryption**: Fernet symmetric encryption for all OAuth tokens
- **Secure Storage**: SQLite-based token storage with encrypted values
- **Automatic Refresh**: Background token refresh before expiration
- **Credential Validation**: Pre-flight validation of OAuth credentials
- **Error Handling**: Comprehensive OAuth error framework
- **Security Logging**: Privacy-aware security event logging

---

## Components

### 1. EncryptionManager (`integrations/security/encryption_manager.py`)

Manages encryption and decryption of OAuth tokens using Fernet symmetric encryption.

**Features**:
- Secure token encryption/decryption
- Key generation utilities
- Proper error handling

**Usage**:
```python
from integrations.security.encryption_manager import EncryptionManager

# Generate a key (do this once, store in .env)
key = EncryptionManager.generate_key()

# Create manager
manager = EncryptionManager(key)

# Encrypt a token
encrypted = manager.encrypt_token("my_access_token")

# Decrypt it back
decrypted = manager.decrypt_token(encrypted)
```

### 2. TokenManager (`integrations/security/token_manager.py`)

Manages secure storage and retrieval of OAuth tokens in SQLite.

**Features**:
- Encrypted token storage
- Secure file permissions (600)
- Support for access and refresh tokens
- Token expiration tracking
- CRUD operations

**Usage**:
```python
from integrations.security.token_manager import TokenManager

# Initialize (uses OAUTH_ENCRYPTION_KEY from environment)
manager = TokenManager()

# Save a token
token_data = {
    'access_token': 'ya29.a0...',
    'refresh_token': '1//...',
    'expires_in': 3600,
    'scopes': ['email', 'profile']
}
manager.save_token('google', 'user@example.com', token_data)

# Retrieve a token
token = manager.get_token('google', 'user@example.com')

# Delete a token
manager.delete_token('google', 'user@example.com')

# List all tokens
tokens = manager.list_tokens()
```

### 3. TokenRefresher (`integrations/security/token_refresher.py`)

Automatically refreshes OAuth tokens before they expire.

**Features**:
- Checks token expiration
- Automatic refresh using refresh tokens
- Background scheduler for periodic checks
- Integrates with OAuth registry

**Usage**:
```python
from integrations.security.token_refresher import TokenRefresher, TokenRefreshScheduler

# Create refresher
refresher = TokenRefresher(token_manager, oauth_registry)

# Check and refresh a specific token
refresher.check_and_refresh_token('google', 'user@example.com')

# Or use the scheduler for automatic background refresh
scheduler = TokenRefreshScheduler(refresher, check_interval=300)  # 5 min
scheduler.start()
```

### 4. CredentialValidator (`integrations/security/credential_validator.py`)

Validates OAuth credentials and configuration.

**Features**:
- Environment variable validation
- Client ID format validation (Google, Microsoft)
- Redirect URI validation
- .gitignore safety checks

**Usage**:
```python
from integrations.security.credential_validator import CredentialValidator

# Check required environment variables
required = ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET']
results = CredentialValidator.validate_required_env_vars(required)

# Validate client ID format
is_valid = CredentialValidator.validate_client_id(
    '123456.apps.googleusercontent.com', 
    provider='google'
)

# Validate redirect URI
is_valid = CredentialValidator.validate_redirect_uri(
    'https://example.com/oauth/callback'
)
```

### 5. OAuth Error Framework (`integrations/oauth/oauth_errors.py`)

Comprehensive OAuth error handling with custom exceptions.

**Exception Hierarchy**:
- `OAuthError` (base)
  - `OAuthConfigError` - Configuration issues
  - `OAuthAuthorizationError` - Authorization failures
  - `OAuthTokenExchangeError` - Token exchange failures
  - `OAuthTokenRefreshError` - Token refresh failures
  - `OAuthInvalidTokenError` - Invalid/expired tokens
  - `OAuthRateLimitError` - Rate limit exceeded

**Usage**:
```python
from integrations.oauth.oauth_errors import OAuthErrorParser

# Parse error from OAuth provider response
response = {'error': 'invalid_client', 'error_description': 'Bad client ID'}
error = OAuthErrorParser.parse_error_response(response)

# Raises appropriate exception type (OAuthConfigError in this case)
raise error
```

### 6. SecurityLogger (`integrations/security/security_logger.py`)

Privacy-aware security event logging.

**Features**:
- Rotating log files (10MB max, 5 backups)
- Privacy protection (user IDs hashed)
- Structured event logging
- Separate security log file

**Usage**:
```python
from integrations.security.security_logger import SecurityLogger

logger = SecurityLogger()

# Log OAuth event
logger.log_oauth_event(
    event_type='token_exchange',
    provider='google',
    user_id='user@example.com',
    success=True,
    details={'scopes': ['email', 'profile']}
)

# Log security error
logger.log_security_error(
    error_type='invalid_credentials',
    details={'provider': 'google'}
)
```

---

## Setup

### 1. Install Dependencies

Ensure `cryptography` is installed:

```bash
pip install cryptography>=41.0.0
```

### 2. Generate Encryption Key

```bash
python3 scripts/automation/generate_encryption_key.py
```

This will output a key like:
```
Generated Encryption Key:
nJ8KF7xV9mZ3pQ5tY2wA6cE1hD4bG8fL0sN7rM9kX3vT5uW2yR4qP1zI6oU3aS==

Add this to your .env file as:
OAUTH_ENCRYPTION_KEY=nJ8KF7xV9mZ3pQ5tY2wA6cE1hD4bG8fL0sN7rM9kX3vT5uW2yR4qP1zI6oU3aS==
```

### 3. Add to .env

Add the generated key to your `.env` file:

```bash
OAUTH_ENCRYPTION_KEY=your_generated_key_here
```

⚠️ **SECURITY**: Never commit this key to version control! It's already in `.gitignore`.

### 4. Test Installation

```bash
python3 tests/unit/security/test_all_security.py
```

All tests should pass ✅

---

## Testing

### Run All Tests

```bash
cd tests/unit/security
python3 test_all_security.py
```

### Run Individual Test Suites

```bash
# Encryption tests
python3 test_encryption.py

# Token manager tests  
python3 test_token_manager.py

# Credential validator tests
python3 test_credential_validator.py

# OAuth error tests
python3 test_oauth_errors.py
```

### Test Coverage

- **Encryption Manager**: 10 tests
- **Token Manager**: 5 tests
- **Credential Validator**: 5 tests
- **OAuth Errors**: 6 tests
- **Total**: 26+ tests, all passing ✅

---

## Integration with Other Teams

### Team 1 (Google OAuth)

Team 1 can use Team 5 components to:

```python
from integrations.security.token_manager import TokenManager
from integrations.security.security_logger import SecurityLogger

# After OAuth flow completes
token_manager = TokenManager()
security_logger = SecurityLogger()

# Save the token
token_manager.save_token('google', user_email, token_data)

# Log the event
security_logger.log_oauth_event(
    'token_exchange', 'google', user_email, True
)
```

### Team 2 (Microsoft OAuth)

Similar integration for Microsoft tokens:

```python
token_manager.save_token('microsoft', user_email, token_data)
```

### Team 3 (API Clients)

API clients can retrieve tokens:

```python
# Get current valid token
token = token_manager.get_token('google', user_email)
if token:
    access_token = token['access_token']
    # Use with API client
```

With automatic refresh:

```python
from integrations.security.token_refresher import TokenRefresher

# Ensure token is fresh before API call
refresher.check_and_refresh_token('google', user_email)
token = token_manager.get_token('google', user_email)
```

---

## Security Best Practices

### ✅ DO

- **Use environment variables** for the encryption key
- **Generate a unique key** for each deployment
- **Rotate keys** periodically (future feature)
- **Monitor security logs** for unusual activity
- **Validate credentials** before OAuth flows
- **Handle errors** gracefully with proper exceptions

### ❌ DON'T

- **Never log** actual tokens (only hashes or IDs)
- **Never commit** `.env` file or encryption keys
- **Don't reuse** encryption keys across environments
- **Don't ignore** security warnings in logs
- **Don't store** unencrypted tokens anywhere
- **Don't skip** credential validation

---

## File Structure

```
integrations/security/
├── __init__.py                  # Package exports
├── encryption_manager.py        # Token encryption
├── token_manager.py             # Token storage
├── token_refresher.py           # Auto-refresh
├── credential_validator.py      # Validation
└── security_logger.py           # Security logging

integrations/oauth/
└── oauth_errors.py              # Error framework

scripts/automation/
└── generate_encryption_key.py   # Key generation

tests/unit/security/
├── test_encryption.py           # Encryption tests
├── test_token_manager.py        # Storage tests
├── test_credential_validator.py # Validation tests
├── test_oauth_errors.py         # Error tests
└── test_all_security.py         # Test runner
```

---

## Troubleshooting

### "No module named 'cryptography'"

Install the cryptography library:

```bash
pip install cryptography>=41.0.0
```

### "Encryption key must be provided"

Generate and set the `OAUTH_ENCRYPTION_KEY` environment variable:

```bash
python3 scripts/automation/generate_encryption_key.py
# Add output to .env file
```

### "Permission denied" on token database

The token database should have permissions 600 (owner read/write only). This is set automatically.

### Tests failing

Ensure you're running tests from the project root with PYTHONPATH set:

```bash
cd /home/runner/work/OsMEN/OsMEN
PYTHONPATH=/home/runner/work/OsMEN/OsMEN python3 tests/unit/security/test_all_security.py
```

---

## Future Enhancements

- [ ] Key rotation support
- [ ] Token revocation tracking
- [ ] Multi-factor authentication logging
- [ ] Advanced threat detection
- [ ] Compliance reporting (GDPR, etc.)
- [ ] Database encryption at rest
- [ ] Hardware security module (HSM) support

---

## Contact & Support

**Team**: Team 5 - Token Security  
**Agent**: Team 5 Security Agent (autonomous)  
**Coordination**: Orchestration Agent  
**Status Updates**: Every 2 hours to orchestration  
**Critical Issues**: Report to @dwilli15

---

**Security First, Always! 🔐**
