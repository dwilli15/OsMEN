# Team 2: Microsoft OAuth Implementation - Day 1 TODO List

**Day 1 Focus**: OAuth Automation Framework & Microsoft OAuth Flows

**Team Focus**: Implement complete Microsoft OAuth 2.0 flow with Azure AD integration

**Timeline**: Day 1 - 8 hours

**Team Lead**: OAuth Lead (Secondary track)

---

## 🎯 Primary Objectives

- [ ] Implement Microsoft OAuth 2.0 complete flow
- [ ] Integrate with Azure AD
- [ ] Build Microsoft-specific OAuth flow generator
- [ ] Create Microsoft provider configuration
- [ ] Implement OAuth setup wizard CLI (Microsoft portion)
- [ ] Handle Microsoft-specific OAuth requirements

---

## 📋 Detailed Task List

### Hour 1-2: Azure AD Setup and Configuration

#### Azure AD Research and Preparation
- [ ] Review Azure AD OAuth documentation
- [ ] Understand multi-tenant vs single-tenant apps
- [ ] Review Microsoft Graph API scopes
- [ ] Review Microsoft identity platform best practices

#### Microsoft Provider Configuration
- [ ] Create `config/oauth/microsoft.yaml`
  ```yaml
  provider: microsoft
  type: oauth2
  auth_endpoint: https://login.microsoftonline.com/common/oauth2/v2.0/authorize
  token_endpoint: https://login.microsoftonline.com/common/oauth2/v2.0/token
  logout_endpoint: https://login.microsoftonline.com/common/oauth2/v2.0/logout
  client_id: ${MICROSOFT_CLIENT_ID}
  client_secret: ${MICROSOFT_CLIENT_SECRET}
  redirect_uri: http://localhost:8080/oauth/callback
  tenant: common  # or 'common', 'organizations', 'consumers', or specific tenant ID
  scopes:
    - https://graph.microsoft.com/Calendars.ReadWrite
    - https://graph.microsoft.com/Mail.ReadWrite
    - https://graph.microsoft.com/Contacts.ReadWrite
    - offline_access  # Required for refresh token
  ```
- [ ] Document tenant options
  - [ ] `common` - Any Microsoft account or work/school account
  - [ ] `organizations` - Work or school accounts only
  - [ ] `consumers` - Personal Microsoft accounts only  
  - [ ] Specific tenant ID - Single organization only

#### Microsoft Graph Scopes
- [ ] Define required scopes for Day 2 API work
  - [ ] Calendar scopes
    - [ ] `Calendars.Read`
    - [ ] `Calendars.ReadWrite`
  - [ ] Mail scopes
    - [ ] `Mail.Read`
    - [ ] `Mail.ReadWrite`
    - [ ] `Mail.Send`
  - [ ] Contacts scopes
    - [ ] `Contacts.Read`
    - [ ] `Contacts.ReadWrite`
  - [ ] Always include `offline_access` for refresh tokens
- [ ] Create scope configuration helper

---

### Hour 3-4: Microsoft OAuth Handler Implementation

#### MicrosoftOAuthHandler Class
- [ ] Create `integrations/oauth/microsoft_oauth.py`
- [ ] Implement `MicrosoftOAuthHandler` class
  ```python
  class MicrosoftOAuthHandler(OAuthHandler):
      """Microsoft OAuth 2.0 with Azure AD implementation."""
      
      def __init__(self, config: dict):
          self.config = config
          self.client_id = config['client_id']
          self.client_secret = config['client_secret']
          self.redirect_uri = config['redirect_uri']
          self.tenant = config.get('tenant', 'common')
          self.scopes = config['scopes']
          
          # Build tenant-specific endpoints
          self.auth_endpoint = f"https://login.microsoftonline.com/{self.tenant}/oauth2/v2.0/authorize"
          self.token_endpoint = f"https://login.microsoftonline.com/{self.tenant}/oauth2/v2.0/token"
  ```

#### Authorization URL Generation
- [ ] Implement `get_authorization_url()`
  - [ ] Build Microsoft authorization URL
  - [ ] Add client_id
  - [ ] Add redirect_uri
  - [ ] Add scope (space-separated)
  - [ ] Add response_type=code
  - [ ] Add state (CSRF token)
  - [ ] Add response_mode=query
  - [ ] Add prompt=consent (optional, for admin consent)
- [ ] Handle Microsoft-specific parameters
  - [ ] `domain_hint` - Pre-fill user's domain
  - [ ] `login_hint` - Pre-fill user's email
  - [ ] `prompt` - Select|login|consent|none
- [ ] Example output:
  ```
  https://login.microsoftonline.com/common/oauth2/v2.0/authorize?
    client_id=xxx&
    redirect_uri=http://localhost:8080/callback&
    scope=Calendars.ReadWrite Mail.ReadWrite offline_access&
    response_type=code&
    state=abc123&
    response_mode=query
  ```

#### Token Exchange Implementation
- [ ] Implement `exchange_code_for_token()`
  - [ ] Validate authorization code
  - [ ] Build token request
    ```python
    data = {
        'code': code,
        'client_id': self.client_id,
        'client_secret': self.client_secret,
        'redirect_uri': self.redirect_uri,
        'grant_type': 'authorization_code',
        'scope': ' '.join(self.scopes)  # Microsoft requires scope in token request
    }
    ```
  - [ ] POST to Microsoft token endpoint
  - [ ] Handle token response
    ```python
    {
        'token_type': 'Bearer',
        'scope': '...',
        'expires_in': 3600,
        'ext_expires_in': 3600,
        'access_token': '...',
        'refresh_token': '...',
        'id_token': '...'  # JWT with user info
    }
    ```
  - [ ] Extract tokens and metadata
  - [ ] Decode id_token (JWT) for user info
  - [ ] Calculate expiration timestamp
  - [ ] Handle errors

---

### Hour 5-6: Token Refresh and Azure AD Features

#### Token Refresh Implementation
- [ ] Implement `refresh_token()`
  - [ ] Validate refresh token
  - [ ] Build refresh request
    ```python
    data = {
        'refresh_token': refresh_token,
        'client_id': self.client_id,
        'client_secret': self.client_secret,
        'grant_type': 'refresh_token',
        'scope': ' '.join(self.scopes)
    }
    ```
  - [ ] POST to Microsoft token endpoint
  - [ ] Handle refresh response
    ```python
    {
        'token_type': 'Bearer',
        'scope': '...',
        'expires_in': 3600,
        'ext_expires_in': 3600,
        'access_token': '...',
        'refresh_token': '...'  # Microsoft returns new refresh token
    }
    ```
  - [ ] Update both access and refresh tokens
  - [ ] Handle errors

#### Token Validation
- [ ] Implement `validate_token()`
  - [ ] Check token exists and not expired
  - [ ] Optionally: Call Microsoft Graph /me endpoint
    ```
    GET https://graph.microsoft.com/v1.0/me
    Authorization: Bearer {access_token}
    ```
  - [ ] Validate response
  - [ ] Return validation status

#### Token Revocation
- [ ] Implement `revoke_token()`
  - [ ] Note: Microsoft doesn't have a standard revoke endpoint
  - [ ] Alternative: Remove token from local storage
  - [ ] Instruct user to revoke in Azure portal
  - [ ] Clear stored tokens
  - [ ] Log revocation attempt

#### Admin Consent Flow (if needed)
- [ ] Implement admin consent URL generation
  ```python
  def get_admin_consent_url(self):
      """Generate admin consent URL for organization-wide permissions."""
  ```
  - [ ] Build admin consent URL
  - [ ] Add client_id
  - [ ] Add redirect_uri
  - [ ] Add state
  - [ ] Use `/adminconsent` endpoint
- [ ] Handle admin consent callback
- [ ] Document when admin consent is needed

---

### Hour 7-8: OAuth Setup Wizard and Testing

#### OAuth Setup Wizard CLI (Microsoft)
- [ ] Add Microsoft setup to `cli_bridge/oauth_setup.py`
- [ ] Implement interactive Microsoft OAuth setup
  ```python
  def setup_microsoft_oauth():
      """Interactive Microsoft OAuth setup wizard."""
      print("Microsoft OAuth Setup Wizard")
      print("="*50)
      
      # Step 1: Check for credentials
      # Step 2: Select tenant type
      # Step 3: Generate authorization URL
      # Step 4: Open browser (optional)
      # Step 5: Wait for authorization code
      # Step 6: Exchange code for token
      # Step 7: Test token with Graph API call
      # Step 8: Save configuration
  ```
- [ ] Wizard steps:
  - [ ] Welcome and instructions
  - [ ] Check MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET
  - [ ] Prompt for tenant type (common/organizations/consumers)
  - [ ] Generate authorization URL
  - [ ] Display URL to user
  - [ ] Optionally open browser automatically
  - [ ] Prompt for authorization code
  - [ ] Exchange code for tokens
  - [ ] Decode and display user info from id_token
  - [ ] Test token with Graph API /me call
  - [ ] Save tokens securely
  - [ ] Display next steps

#### OAuth Flow Generator (Microsoft)
- [ ] Add Microsoft template to `scripts/automation/generate_oauth_flow.py`
- [ ] Support Microsoft-specific config options
  - [ ] Tenant configuration
  - [ ] Admin consent requirements
  - [ ] Microsoft Graph scopes
- [ ] Generate Microsoft handler code from template

#### Unit Tests
- [ ] Create `tests/unit/oauth/test_microsoft_oauth.py`
- [ ] Test authorization URL generation
  - [ ] Verify tenant in URL
  - [ ] Verify all required parameters
  - [ ] Verify scope format
- [ ] Test token exchange (mocked)
  - [ ] Mock successful response
  - [ ] Verify token extraction
  - [ ] Verify id_token parsing
  - [ ] Test error handling
- [ ] Test token refresh (mocked)
  - [ ] Mock successful refresh
  - [ ] Verify new access and refresh tokens
  - [ ] Test expired refresh token
- [ ] Test tenant handling
  - [ ] Test 'common' tenant
  - [ ] Test specific tenant ID
  - [ ] Test endpoint URL construction

---

## 🧪 Testing Requirements

### Unit Tests (10+ tests)
- [ ] Test MicrosoftOAuthHandler initialization
- [ ] Test authorization URL generation
  - [ ] Common tenant
  - [ ] Specific tenant
  - [ ] With optional parameters
- [ ] Test token exchange success
- [ ] Test token exchange failure
- [ ] Test token refresh success
- [ ] Test token refresh failure
- [ ] Test id_token parsing
- [ ] Test error handling
- [ ] Test admin consent URL generation

### Integration Tests (with mock server)
- [ ] Test complete Microsoft OAuth flow
  - [ ] Authorization → Code → Token
  - [ ] Verify id_token included
  - [ ] Verify refresh_token included
- [ ] Test token refresh flow
  - [ ] Verify new refresh token returned
- [ ] Test error scenarios

---

## 📦 Dependencies

### Python Packages
```python
requests>=2.31.0
pyjwt>=2.8.0  # For id_token decoding
cryptography>=41.0.0  # For JWT signature verification
pyyaml>=6.0
python-dotenv>=1.0.0
pytest>=7.4.0
pytest-mock>=3.11.0
responses>=0.23.0
```

### Environment Variables
```bash
MICROSOFT_CLIENT_ID=your_client_id_here
MICROSOFT_CLIENT_SECRET=your_client_secret_here
MICROSOFT_TENANT_ID=common  # or specific tenant ID
```

---

## 📊 Success Metrics

### End of Day 1 Deliverables
- [ ] MicrosoftOAuthHandler fully implemented
- [ ] Azure AD integration working
- [ ] Microsoft OAuth flow working end-to-end
  - [ ] Can generate authorization URL (with tenant)
  - [ ] Can exchange code for tokens
  - [ ] Can refresh tokens (gets new refresh token)
  - [ ] Can parse id_token
  - [ ] Can validate tokens
- [ ] Microsoft provider registered in OAuth registry
- [ ] OAuth setup wizard working for Microsoft
- [ ] Admin consent flow documented
- [ ] 10+ unit tests passing
- [ ] Documentation complete
- [ ] Ready for Day 2 Microsoft API integration

---

## 🚀 Handoff to Other Teams

### For Team 3 (API Clients - Day 2)
- Microsoft OAuth tokens available
- Microsoft Graph API ready for Day 2
- Token refresh mechanism working
- Configuration files ready

### For Team 4 (Testing)
- Microsoft OAuth tests as examples
- Mock patterns for Azure AD
- Integration test structure

### For Team 5 (Token Security)
- Microsoft token structure defined
- id_token handling defined
- Ready for encryption layer

---

## 📝 Notes

- Microsoft returns new refresh tokens on refresh (unlike Google)
- Always include `offline_access` scope for refresh tokens
- id_token contains user information (email, name, etc.)
- Admin consent may be required for some scopes
- Tenant configuration is important for proper auth flow
- Microsoft Graph uses different URL format than Google APIs
- Handle both personal and work/school accounts
- Test with both account types if possible

---

**Team Contact**: OAuth Lead  
**Status Updates**: Every 2 hours to Orchestration  
**Blockers**: Report immediately  
**Dependency**: Team 1 base classes must be complete first

---

## 🎯 Ready to Execute!

Build on Team 1's foundation to add Microsoft OAuth!

**LET'S BUILD! 🚀**
