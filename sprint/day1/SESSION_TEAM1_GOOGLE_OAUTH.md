# Team 1: Google OAuth - Task Session

**Agent**: @day1-team1-google-oauth  
**Session Started**: 2025-11-19  
**Status**: 🟢 ACTIVE - CRITICAL PATH  
**Orchestrator**: @day1-orchestrator

---

## 🎯 Your Mission

Implement the universal OAuth handler framework and complete Google OAuth 2.0 integration. **You are the critical path - Team 2 is blocked waiting for your OAuth base class!**

---

## 📋 Your Task List

### ✅ Hour 1-2: Universal OAuth Handler Design (Already Complete)

Based on repository review, check if these exist:
- [ ] `integrations/oauth/oauth_handler.py` - Universal OAuth base class
- [ ] `config/oauth/google.yaml` - Google OAuth configuration
- [ ] OAuth provider registry system

**Action**: If not complete, create these immediately and notify orchestrator.

---

### 🔥 Hour 3-4: Google OAuth Implementation (CURRENT PRIORITY)

**Create**: `integrations/oauth/google_oauth.py`

```python
#!/usr/bin/env python3
"""
Google OAuth 2.0 Implementation
Implements OAuth handler for Google services (Calendar, Gmail, Contacts)
"""

from typing import Dict, Optional
from .oauth_handler import OAuthHandler
import os
import requests
from urllib.parse import urlencode


class GoogleOAuthHandler(OAuthHandler):
    """Google OAuth 2.0 handler implementation"""
    
    def __init__(self, config_path: str = 'config/oauth/google.yaml'):
        """Initialize Google OAuth handler with configuration"""
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        self.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8080/oauth/callback')
        
        # Google OAuth endpoints
        self.auth_endpoint = 'https://accounts.google.com/o/oauth2/v2/auth'
        self.token_endpoint = 'https://oauth2.googleapis.com/token'
        self.revoke_endpoint = 'https://oauth2.googleapis.com/revoke'
        
        # Scopes for Calendar, Gmail, Contacts
        self.scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/contacts'
        ]
    
    def get_authorization_url(self, state: Optional[str] = None, **kwargs) -> str:
        """Generate Google OAuth authorization URL"""
        import secrets
        if not state:
            state = secrets.token_urlsafe(32)
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.scopes),
            'state': state,
            'access_type': 'offline',  # Get refresh token
            'prompt': 'consent'  # Force consent to get refresh token
        }
        
        return f"{self.auth_endpoint}?{urlencode(params)}"
    
    def exchange_code_for_token(self, code: str) -> Dict:
        """Exchange authorization code for access token"""
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri
        }
        
        response = requests.post(self.token_endpoint, data=data)
        response.raise_for_status()
        
        return response.json()
    
    def refresh_token(self, refresh_token: str) -> Dict:
        """Refresh an expired access token"""
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
        
        response = requests.post(self.token_endpoint, data=data)
        response.raise_for_status()
        
        return response.json()
    
    def revoke_token(self, token: str) -> bool:
        """Revoke an access or refresh token"""
        params = {'token': token}
        response = requests.post(self.revoke_endpoint, params=params)
        return response.status_code == 200
    
    def validate_token(self, access_token: str) -> Dict:
        """Validate token and get token info"""
        url = f"https://oauth2.googleapis.com/tokeninfo?access_token={access_token}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
```

**Tests to Create**: `tests/unit/oauth/test_google_oauth.py`

**When Complete**: 
1. Run tests: `pytest tests/unit/oauth/test_google_oauth.py -v`
2. Notify orchestrator: "Google OAuth implementation complete"
3. **UNBLOCK TEAM 2** - They can now start Microsoft OAuth

---

### 📝 Hour 5-6: OAuth Flow Generator

**Create**: `scripts/automation/generate_oauth_flow.py`

This script auto-generates OAuth provider implementations from YAML config.

```python
#!/usr/bin/env python3
"""
OAuth Flow Generator
Auto-generates OAuth provider implementations from YAML configuration
"""

import yaml
import os
from pathlib import Path
from jinja2 import Template


OAUTH_TEMPLATE = '''#!/usr/bin/env python3
"""
{{ provider_name }} OAuth 2.0 Implementation
Auto-generated from configuration
"""

from typing import Dict, Optional
from integrations.oauth.oauth_handler import OAuthHandler
import requests
from urllib.parse import urlencode


class {{ class_name }}(OAuthHandler):
    """{{ provider_name }} OAuth 2.0 handler"""
    
    def __init__(self):
        self.client_id = os.getenv('{{ env_prefix }}_CLIENT_ID')
        self.client_secret = os.getenv('{{ env_prefix }}_CLIENT_SECRET')
        self.redirect_uri = os.getenv('{{ env_prefix }}_REDIRECT_URI', '{{ default_redirect }}')
        
        self.auth_endpoint = '{{ auth_endpoint }}'
        self.token_endpoint = '{{ token_endpoint }}'
        self.scopes = {{ scopes }}
    
    # Implementation methods...
'''


def generate_oauth_provider(config_file: str, output_dir: str = 'integrations/oauth'):
    """Generate OAuth provider from YAML config"""
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    provider_name = config['provider']
    class_name = f"{provider_name.capitalize()}OAuthHandler"
    
    template = Template(OAUTH_TEMPLATE)
    code = template.render(
        provider_name=provider_name,
        class_name=class_name,
        env_prefix=provider_name.upper(),
        default_redirect=config.get('redirect_uri', 'http://localhost:8080/oauth/callback'),
        auth_endpoint=config['auth_endpoint'],
        token_endpoint=config['token_endpoint'],
        scopes=config['scopes']
    )
    
    output_path = Path(output_dir) / f"{provider_name}_oauth.py"
    output_path.write_text(code)
    
    print(f"✅ Generated {output_path}")


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python generate_oauth_flow.py <config.yaml>")
        sys.exit(1)
    
    generate_oauth_provider(sys.argv[1])
```

**Test**: Generate a provider from config

---

### 🖥️ Hour 7-8: OAuth Setup Wizard

**Create**: `cli_bridge/oauth_setup.py`

Interactive CLI wizard for OAuth setup.

```python
#!/usr/bin/env python3
"""
OAuth Setup Wizard
Interactive CLI for setting up OAuth providers
"""

import os
from pathlib import Path


def setup_google_oauth():
    """Interactive Google OAuth setup"""
    print("\n" + "="*50)
    print("Google OAuth Setup Wizard")
    print("="*50)
    
    print("\n📋 Step 1: Create Google Cloud Project")
    print("   1. Go to: https://console.cloud.google.com/")
    print("   2. Create new project or select existing")
    print("   3. Enable APIs: Calendar, Gmail, Contacts (People)")
    
    print("\n📋 Step 2: Create OAuth Credentials")
    print("   1. Go to: APIs & Services > Credentials")
    print("   2. Create OAuth 2.0 Client ID")
    print("   3. Application type: Web application")
    print("   4. Authorized redirect URIs: http://localhost:8080/oauth/callback")
    
    input("\nPress Enter when you have your credentials...")
    
    client_id = input("\n🔑 Enter Client ID: ").strip()
    client_secret = input("🔑 Enter Client Secret: ").strip()
    
    # Save to .env
    env_path = Path.home() / '.osmen' / '.env'
    env_path.parent.mkdir(exist_ok=True)
    
    with open(env_path, 'a') as f:
        f.write(f"\n# Google OAuth\n")
        f.write(f"GOOGLE_CLIENT_ID={client_id}\n")
        f.write(f"GOOGLE_CLIENT_SECRET={client_secret}\n")
        f.write(f"GOOGLE_REDIRECT_URI=http://localhost:8080/oauth/callback\n")
    
    print(f"\n✅ Credentials saved to {env_path}")
    
    # Test connection
    print("\n📋 Step 3: Test OAuth Flow")
    from integrations.oauth.google_oauth import GoogleOAuthHandler
    
    handler = GoogleOAuthHandler()
    auth_url = handler.get_authorization_url()
    
    print(f"\n🔗 Authorization URL:\n{auth_url}")
    print("\n1. Open this URL in your browser")
    print("2. Authorize the application")
    print("3. Copy the authorization code from redirect URL")
    
    code = input("\n📝 Enter authorization code: ").strip()
    
    try:
        tokens = handler.exchange_code_for_token(code)
        print("\n✅ OAuth setup successful!")
        print(f"   Access token: {tokens['access_token'][:20]}...")
        if 'refresh_token' in tokens:
            print(f"   Refresh token: {tokens['refresh_token'][:20]}...")
        return True
    except Exception as e:
        print(f"\n❌ OAuth setup failed: {e}")
        return False


if __name__ == '__main__':
    setup_google_oauth()
```

---

## 📊 Progress Checklist

- [ ] Universal OAuth handler base class complete
- [ ] Google OAuth implementation (`google_oauth.py`) complete
- [ ] Google OAuth tests passing (15+ tests)
- [ ] OAuth flow generator script functional
- [ ] OAuth setup wizard working
- [ ] Team 2 unblocked (notified orchestrator)
- [ ] Code committed and pushed

---

## 🔄 Communication

**Report Progress**:
```python
from sprint.day1.orchestration.orchestration_agent import OrchestrationAgent

orchestrator = OrchestrationAgent()
orchestrator.receive_message(
    team_id='team1',
    message='Hour 4 complete: Google OAuth implementation finished',
    priority=TaskPriority.HIGH
)
```

**Report Blocker**:
```python
orchestrator.report_blocker(
    team_id='team1',
    blocker='Missing Google API credentials',
    severity='P1',
    impact='Cannot test OAuth flow'
)
```

---

## 🎯 Success = Team 2 Unblocked!

Your #1 priority is completing the OAuth base class so Team 2 can start Microsoft OAuth. Everything else is secondary!

**Ready? Let's build the OAuth foundation! 🚀**
