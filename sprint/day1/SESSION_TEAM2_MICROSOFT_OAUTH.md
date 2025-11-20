# Team 2: Microsoft OAuth - Task Session

**Agent**: @day1-team2-microsoft-oauth  
**Session Started**: 2025-11-19  
**Status**: 🟡 WAITING - Blocked by Team 1  
**Orchestrator**: @day1-orchestrator

---

## ⚠️ CURRENT STATUS: BLOCKED

**Blocking Dependency**: Waiting for Team 1 to complete OAuth base class

**Your Agent**: `sprint/day1/team2_microsoft_oauth/team2_agent.py` is ready to execute automatically once unblocked.

---

## 🕐 While Waiting (Hour 1-2)

### Azure AD Research

Review Azure AD OAuth documentation:
- Microsoft identity platform: https://docs.microsoft.com/azure/active-directory/develop/
- OAuth 2.0 auth code flow: https://docs.microsoft.com/azure/active-directory/develop/v2-oauth2-auth-code-flow
- Graph API permissions: https://docs.microsoft.com/graph/permissions-reference

### Prepare Implementation

1. **Review Microsoft OAuth Configuration**:
   - Check `config/oauth/microsoft.yaml`
   - Document Azure AD-specific requirements
   - Note differences from Google OAuth

2. **Azure AD Setup Planning**:
   - Tenant ID handling
   - id_token parsing requirements
   - Microsoft Graph API scopes
   - Personal (MSA) vs Work (AAD) accounts

3. **Document Microsoft-Specific Quirks**:
   - Token refresh timing differences
   - Scope format differences
   - Error response formats

---

## 🚀 After Team 1 Completes (Hour 3+)

### Execute Your Autonomous Agent

```bash
cd sprint/day1/team2_microsoft_oauth
python3 execute_team2.py
```

Your agent (`team2_agent.py`) will automatically:
1. Create `integrations/oauth/microsoft_oauth.py`
2. Extend Team 1's `OAuthHandler` base class
3. Implement Azure AD authorization flow
4. Handle id_token parsing
5. Integrate with Team 5's token encryption
6. Report progress to orchestrator

---

## 📋 Your Deliverables

### Hour 3-4: Microsoft OAuth Implementation

**Create**: `integrations/oauth/microsoft_oauth.py`

```python
#!/usr/bin/env python3
"""
Microsoft OAuth 2.0 Implementation with Azure AD
"""

from typing import Dict, Optional
from .oauth_handler import OAuthHandler
import os
import requests
from urllib.parse import urlencode
import jwt


class MicrosoftOAuthHandler(OAuthHandler):
    """Microsoft OAuth 2.0 handler with Azure AD integration"""
    
    def __init__(self, config_path: str = 'config/oauth/microsoft.yaml'):
        """Initialize Microsoft OAuth handler"""
        self.client_id = os.getenv('MICROSOFT_CLIENT_ID')
        self.client_secret = os.getenv('MICROSOFT_CLIENT_SECRET')
        self.tenant_id = os.getenv('MICROSOFT_TENANT_ID', 'common')
        self.redirect_uri = os.getenv('MICROSOFT_REDIRECT_URI', 'http://localhost:8080/oauth/callback')
        
        # Microsoft OAuth endpoints (with tenant)
        base_url = f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0'
        self.auth_endpoint = f'{base_url}/authorize'
        self.token_endpoint = f'{base_url}/token'
        
        # Microsoft Graph API scopes
        self.scopes = [
            'https://graph.microsoft.com/Calendars.ReadWrite',
            'https://graph.microsoft.com/Mail.ReadWrite',
            'https://graph.microsoft.com/Contacts.ReadWrite',
            'offline_access'  # Required for refresh token
        ]
    
    def get_authorization_url(self, state: Optional[str] = None, **kwargs) -> str:
        """Generate Microsoft OAuth authorization URL"""
        import secrets
        if not state:
            state = secrets.token_urlsafe(32)
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.scopes),
            'state': state,
            'response_mode': 'query'
        }
        
        return f"{self.auth_endpoint}?{urlencode(params)}"
    
    def exchange_code_for_token(self, code: str) -> Dict:
        """Exchange authorization code for tokens (includes id_token)"""
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.scopes)
        }
        
        response = requests.post(self.token_endpoint, data=data)
        response.raise_for_status()
        
        tokens = response.json()
        
        # Parse id_token if present
        if 'id_token' in tokens:
            tokens['user_info'] = self._parse_id_token(tokens['id_token'])
        
        return tokens
    
    def refresh_token(self, refresh_token: str) -> Dict:
        """Refresh an expired access token"""
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
            'scope': ' '.join(self.scopes)
        }
        
        response = requests.post(self.token_endpoint, data=data)
        response.raise_for_status()
        
        return response.json()
    
    def revoke_token(self, token: str) -> bool:
        """Revoke an access token (Microsoft doesn't have revoke endpoint)"""
        # Microsoft doesn't provide token revocation endpoint
        # Tokens expire naturally or user can revoke in account settings
        return True
    
    def validate_token(self, access_token: str) -> Dict:
        """Validate token by calling Microsoft Graph"""
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers)
        response.raise_for_status()
        return response.json()
    
    def _parse_id_token(self, id_token: str) -> Dict:
        """Parse JWT id_token to extract user info"""
        # Decode without verification (client already authenticated)
        decoded = jwt.decode(id_token, options={"verify_signature": False})
        return {
            'name': decoded.get('name'),
            'email': decoded.get('preferred_username') or decoded.get('email'),
            'user_id': decoded.get('oid') or decoded.get('sub')
        }
```

### Hour 5-6: Azure AD Integration

1. **Handle id_token parsing** (extract user profile)
2. **Test token exchange** with Azure AD
3. **Implement token refresh** with Microsoft-specific handling
4. **Integrate with Team 5** token encryption

### Hour 7-8: Microsoft Setup Wizard

**Extend**: `cli_bridge/oauth_setup.py`

Add `setup_microsoft_oauth()` function similar to Google setup.

---

## 📊 Progress Checklist

- [ ] Wait for Team 1 OAuth base class (monitor orchestrator)
- [ ] Execute `team2_agent.py` when unblocked
- [ ] Microsoft OAuth implementation complete
- [ ] Azure AD integration working
- [ ] id_token parsing functional
- [ ] Token exchange and refresh tested
- [ ] Microsoft setup wizard added
- [ ] 15+ tests passing
- [ ] Code committed

---

## 🔄 Communication

Your agent handles communication automatically, but you can also:

```python
from sprint.day1.orchestration.orchestration_agent import OrchestrationAgent

orchestrator = OrchestrationAgent()

# When unblocked
orchestrator.receive_message(
    team_id='team2',
    message='Team 1 complete, starting Microsoft OAuth implementation',
    priority=TaskPriority.HIGH
)

# When complete
orchestrator.receive_message(
    team_id='team2',
    message='Microsoft OAuth implementation complete',
    priority=TaskPriority.HIGH
)
```

---

## 🎯 Success Criteria

- ✅ Microsoft OAuth 2.0 flow working
- ✅ Azure AD integration complete
- ✅ Token exchange with id_token parsing
- ✅ Refresh token working
- ✅ Integration with Team 5 encryption
- ✅ Setup wizard functional
- ✅ 15+ tests passing

---

## 🚨 Monitor for Unblock Signal

**Watch for**: Orchestrator message "Team 1 OAuth base class complete - Team 2 unblocked"

**Then**: Execute your agent and implement Microsoft OAuth!

**Ready to go when unblocked! 🚀**
