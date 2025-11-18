# Team 1: Google OAuth Implementation - Day 1 TODO List

**Day 1 Focus**: OAuth Automation Framework & Google OAuth Flows

**Team Focus**: Implement complete Google OAuth 2.0 flow with authorization, token exchange, and refresh automation

**Timeline**: Day 1 - 8 hours

**Team Lead**: OAuth Lead

---

## 🎯 Primary Objectives

- [ ] Design universal OAuth handler class (foundation for all providers)
- [ ] Implement Google OAuth 2.0 complete flow
- [ ] Build OAuth flow generator script
- [ ] Create provider configuration YAML schema
- [ ] Implement OAuth setup wizard CLI (Google portion)
- [ ] Add OAuth provider registry

---

## 📋 Detailed Task List

### Hour 1-2: Universal OAuth Handler Design

#### Base OAuth Handler Class
- [ ] Create `integrations/oauth/` directory structure
- [ ] Design `OAuthHandler` abstract base class
  ```python
  class OAuthHandler(ABC):
      """Abstract base class for OAuth 2.0 providers."""
      
      @abstractmethod
      def get_authorization_url(self, **kwargs) -> str:
          """Generate OAuth authorization URL."""
          
      @abstractmethod
      def exchange_code_for_token(self, code: str) -> dict:
          """Exchange authorization code for access token."""
          
      @abstractmethod
      def refresh_token(self, refresh_token: str) -> dict:
          """Refresh an expired access token."""
  ```
- [ ] Define required methods
  - [ ] `get_authorization_url()` - Generate auth URL with state
  - [ ] `exchange_code_for_token()` - Exchange code for tokens
  - [ ] `refresh_token()` - Refresh access token
  - [ ] `revoke_token()` - Revoke token
  - [ ] `validate_token()` - Check token validity
- [ ] Design common OAuth utilities
  - [ ] State parameter generation (CSRF protection)
  - [ ] Scope management
  - [ ] Redirect URI handling
  - [ ] Error parsing

#### Provider Configuration Schema
- [ ] Create `config/oauth/` directory
- [ ] Design YAML configuration schema
  ```yaml
  provider: google
  type: oauth2
  auth_endpoint: https://accounts.google.com/o/oauth2/v2/auth
  token_endpoint: https://oauth2.googleapis.com/token
  revoke_endpoint: https://oauth2.googleapis.com/revoke
  client_id: ${GOOGLE_CLIENT_ID}
  client_secret: ${GOOGLE_CLIENT_SECRET}
  redirect_uri: http://localhost:8080/oauth/callback
  scopes:
    - https://www.googleapis.com/auth/calendar
    - https://www.googleapis.com/auth/gmail.modify
    - https://www.googleapis.com/auth/contacts
  ```
- [ ] Create `config/oauth/google.yaml` template
- [ ] Create configuration loader utility
- [ ] Validate configuration on load

#### OAuth Provider Registry
- [ ] Create `OAuthProviderRegistry` class
- [ ] Implement provider registration
  ```python
  registry.register('google', GoogleOAuthHandler)
  registry.register('microsoft', MicrosoftOAuthHandler)
  ```
- [ ] Implement provider factory pattern
  ```python
  handler = registry.get_handler('google', config)
  ```
- [ ] Add provider discovery/listing

---

### Hour 3-4: Google OAuth Flow Implementation

#### GoogleOAuthHandler Class
- [ ] Create `integrations/oauth/google_oauth.py`
- [ ] Implement `GoogleOAuthHandler` class
  ```python
  class GoogleOAuthHandler(OAuthHandler):
      """Google OAuth 2.0 implementation."""
      
      def __init__(self, config: dict):
          self.config = config
          self.client_id = config['client_id']
          self.client_secret = config['client_secret']
          self.redirect_uri = config['redirect_uri']
          self.scopes = config['scopes']
  ```

#### Authorization URL Generation
- [ ] Implement `get_authorization_url()`
  - [ ] Build authorization URL with parameters
  - [ ] Add client_id
  - [ ] Add redirect_uri
  - [ ] Add scope (space-separated)
  - [ ] Add response_type=code
  - [ ] Add state (CSRF token)
  - [ ] Add access_type=offline (for refresh token)
  - [ ] Add prompt=consent (force consent screen)
- [ ] Generate and store state parameter
  - [ ] Use secrets.token_urlsafe(32)
  - [ ] Store in session or database
  - [ ] Set 5-minute expiration
- [ ] Example output:
  ```
  https://accounts.google.com/o/oauth2/v2/auth?
    client_id=xxx&
    redirect_uri=http://localhost:8080/callback&
    scope=calendar gmail contacts&
    response_type=code&
    state=abc123&
    access_type=offline&
    prompt=consent
  ```

#### Token Exchange Implementation
- [ ] Implement `exchange_code_for_token()`
  - [ ] Validate authorization code format
  - [ ] Build token request payload
    ```python
    data = {
        'code': code,
        'client_id': self.client_id,
        'client_secret': self.client_secret,
        'redirect_uri': self.redirect_uri,
        'grant_type': 'authorization_code'
    }
    ```
  - [ ] POST to Google token endpoint
  - [ ] Handle token response
    ```python
    {
        'access_token': '...',
        'expires_in': 3600,
        'refresh_token': '...',
        'scope': '...',
        'token_type': 'Bearer'
    }
    ```
  - [ ] Extract and return tokens
  - [ ] Calculate expiration timestamp
  - [ ] Handle errors (invalid code, network errors)

---

### Hour 5-6: Token Refresh and Validation

#### Token Refresh Implementation
- [ ] Implement `refresh_token()`
  - [ ] Validate refresh token exists
  - [ ] Build refresh request payload
    ```python
    data = {
        'refresh_token': refresh_token,
        'client_id': self.client_id,
        'client_secret': self.client_secret,
        'grant_type': 'refresh_token'
    }
    ```
  - [ ] POST to Google token endpoint
  - [ ] Handle refresh response
    ```python
    {
        'access_token': '...',
        'expires_in': 3600,
        'scope': '...',
        'token_type': 'Bearer'
    }
    ```
  - [ ] Note: Google doesn't return new refresh_token
  - [ ] Return new access token
  - [ ] Handle errors (invalid refresh token)

#### Token Validation
- [ ] Implement `validate_token()`
  - [ ] Check token exists
  - [ ] Check token not expired
  - [ ] Optionally: Call Google tokeninfo endpoint
    ```
    GET https://oauth2.googleapis.com/tokeninfo?access_token=xxx
    ```
  - [ ] Parse validation response
  - [ ] Return validation status

#### Token Revocation
- [ ] Implement `revoke_token()`
  - [ ] POST to Google revoke endpoint
    ```
    POST https://oauth2.googleapis.com/revoke
    Content-Type: application/x-www-form-urlencoded
    token=<access_token or refresh_token>
    ```
  - [ ] Handle revocation response
  - [ ] Clear stored tokens
  - [ ] Return success/failure

---

### Hour 7-8: OAuth Setup Wizard and Testing

#### OAuth Setup Wizard CLI (Google)
- [ ] Create `cli_bridge/oauth_setup.py`
- [ ] Implement interactive Google OAuth setup
  ```python
  def setup_google_oauth():
      """Interactive Google OAuth setup wizard."""
      print("Google OAuth Setup Wizard")
      print("="*50)
      
      # Step 1: Check for credentials
      # Step 2: Generate authorization URL
      # Step 3: Open browser (optional)
      # Step 4: Wait for authorization code
      # Step 5: Exchange code for token
      # Step 6: Test token with API call
      # Step 7: Save configuration
  ```
- [ ] Wizard steps:
  - [ ] Welcome and instructions
  - [ ] Check GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
  - [ ] Prompt for credentials if missing
  - [ ] Generate authorization URL
  - [ ] Display URL to user
  - [ ] Optionally open browser automatically
  - [ ] Prompt for authorization code
  - [ ] Exchange code for tokens
  - [ ] Display success message
  - [ ] Test token with Calendar API list call
  - [ ] Save tokens securely
  - [ ] Display next steps

#### OAuth Flow Generator Script
- [ ] Create `scripts/automation/generate_oauth_flow.py`
- [ ] Auto-generate OAuth handler from YAML config
  ```bash
  python scripts/automation/generate_oauth_flow.py --config config/oauth/google.yaml
  ```
- [ ] Template-based code generation
  - [ ] Read provider config
  - [ ] Generate handler class code
  - [ ] Include provider-specific logic
  - [ ] Write to output file
- [ ] Make script extensible for new providers

#### Unit Tests
- [ ] Create `tests/unit/oauth/test_google_oauth.py`
- [ ] Test authorization URL generation
  - [ ] Verify all required parameters
  - [ ] Verify state parameter included
  - [ ] Verify scopes formatted correctly
- [ ] Test token exchange (mocked)
  - [ ] Mock successful token response
  - [ ] Verify token extraction
  - [ ] Verify expiration calculation
  - [ ] Test error handling
- [ ] Test token refresh (mocked)
  - [ ] Mock successful refresh
  - [ ] Verify new token returned
  - [ ] Test expired refresh token
- [ ] Test token validation
  - [ ] Test valid token
  - [ ] Test expired token
  - [ ] Test invalid token

---

## 🧪 Testing Requirements

### Unit Tests (10+ tests)
- [ ] Test OAuthHandler base class
- [ ] Test GoogleOAuthHandler initialization
- [ ] Test authorization URL generation
- [ ] Test token exchange success
- [ ] Test token exchange failure
- [ ] Test token refresh success
- [ ] Test token refresh failure
- [ ] Test token validation
- [ ] Test token revocation
- [ ] Test error handling

### Integration Tests (with mock server)
- [ ] Test complete OAuth flow
  - [ ] Authorization → Code → Token
  - [ ] Verify state validation
  - [ ] Verify token storage
- [ ] Test token refresh flow
- [ ] Test error scenarios

---

## 📦 Dependencies

### Python Packages
```python
requests>=2.31.0
pyyaml>=6.0
python-dotenv>=1.0.0
pytest>=7.4.0
pytest-mock>=3.11.0
responses>=0.23.0  # For mocking HTTP
```

### Environment Variables
```bash
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

---

## 📊 Success Metrics

### End of Day 1 Deliverables
- [ ] Universal OAuth handler base class complete
- [ ] Provider configuration system working
- [ ] GoogleOAuthHandler fully implemented
- [ ] OAuth provider registry functional
- [ ] Google OAuth flow working end-to-end
  - [ ] Can generate authorization URL
  - [ ] Can exchange code for tokens
  - [ ] Can refresh tokens
  - [ ] Can validate tokens
  - [ ] Can revoke tokens
- [ ] OAuth setup wizard working for Google
- [ ] 10+ unit tests passing
- [ ] Documentation complete
- [ ] Ready for Team 2 (Microsoft) to use base classes
- [ ] Ready for Team 3 (API Clients) to use tokens
- [ ] Ready for Team 5 (Security) to add encryption

---

## 🚀 Handoff to Other Teams

### For Team 2 (Microsoft OAuth)
- OAuthHandler base class ready to extend
- Configuration schema defined
- Pattern established for implementation
- Provider registry ready

### For Team 3 (API Clients)
- OAuth tokens available via GoogleOAuthHandler
- Token refresh mechanism working
- Configuration files ready

### For Team 4 (Testing)
- Test structure established
- Mock patterns defined
- Example tests to follow

### For Team 5 (Token Security)
- Token structure defined
- Storage interface defined
- Ready for encryption layer

---

## 📝 Notes

- Focus on Google OAuth first (most common)
- Design base classes to be provider-agnostic
- Document all OAuth flows clearly
- Handle errors gracefully with helpful messages
- Log OAuth events (but never log tokens!)
- Test both success and failure paths
- Make configuration user-friendly
- Provide clear setup instructions

---

**Team Contact**: OAuth Lead  
**Status Updates**: Every 2 hours to Orchestration  
**Blockers**: Report immediately  

---

## 🎯 Ready to Execute!

Build the OAuth foundation that all other teams depend on!

**LET'S BUILD! 🚀**
