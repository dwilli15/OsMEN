# OAuth Workflow for GitHub Copilot and OpenAI Codex

## Overview

This guide explains how to use the OAuth-based Langflow workflow for code generation using GitHub Copilot or OpenAI Codex **without direct API keys**. Instead, you'll authenticate via web-based OAuth login.

## Features

- **GitHub Copilot OAuth**: Use GitHub Copilot through OAuth web login
- **OpenAI OAuth**: Authenticate with OpenAI via secure token storage
- **Langflow Workflow**: Visual workflow for code generation
- **No API Keys in Flows**: OAuth tokens are managed securely
- **Session Management**: Persistent authentication across sessions
- **Token Refresh**: Automatic token refresh when needed

## Prerequisites

1. **GitHub OAuth App** (for GitHub Copilot):
   - GitHub account with Copilot subscription
   - OAuth App credentials

2. **OpenAI Account** (for OpenAI Codex):
   - OpenAI API account
   - API key (stored via OAuth-like flow)

3. **OsMEN Installation**:
   - Docker and Docker Compose
   - OsMEN services running

## Setup Instructions

### 1. Create GitHub OAuth App

To use GitHub Copilot with OAuth:

1. **Go to GitHub Developer Settings**:
   - Visit: https://github.com/settings/developers
   - Click "OAuth Apps" → "New OAuth App"

2. **Configure OAuth App**:
   ```
   Application name: OsMEN Code Assistant
   Homepage URL: http://localhost:8000
   Authorization callback URL: http://localhost:8000/oauth/github/callback
   ```

3. **Get Client Credentials**:
   - After creating the app, note the **Client ID**
   - Generate a **Client Secret**
   - Keep these secure!

4. **Add to .env file**:
   ```bash
   GITHUB_OAUTH_CLIENT_ID=your_client_id_here
   GITHUB_OAUTH_CLIENT_SECRET=your_client_secret_here
   GITHUB_OAUTH_REDIRECT_URI=http://localhost:8000/oauth/github/callback
   ```

### 2. Configure OpenAI Authentication

For OpenAI (which primarily uses API keys):

1. **Get API Key**:
   - Visit: https://platform.openai.com/api-keys
   - Create a new API key
   - Copy the key (starts with `sk-`)

2. **Add to .env file** (optional, can use web auth):
   ```bash
   OPENAI_OAUTH_CLIENT_ID=your_app_id_here
   OPENAI_OAUTH_CLIENT_SECRET=your_app_secret_here
   OPENAI_OAUTH_REDIRECT_URI=http://localhost:8000/oauth/openai/callback
   ```

### 3. Configure Token Storage

Set the token storage path in `.env`:

```bash
OAUTH_TOKEN_PATH=./tokens
```

This directory will store OAuth tokens securely. It's already in `.gitignore`.

### 4. Start OsMEN Services

```bash
# Start all services
make start
# or
docker-compose up -d

# Verify services are running
make status
```

## Using the OAuth Workflow

### Option 1: Web Dashboard

1. **Access Dashboard**:
   ```
   http://localhost:8000
   ```

2. **Authenticate with GitHub Copilot**:
   - Navigate to: `http://localhost:8000/oauth/github/login`
   - You'll be redirected to GitHub
   - Click "Authorize application"
   - You'll be redirected back with confirmation

3. **Authenticate with OpenAI**:
   - Navigate to: `http://localhost:8000/oauth/openai/login`
   - Enter your OpenAI API key
   - Click "Authenticate"

4. **Check Authentication Status**:
   ```bash
   curl http://localhost:8000/oauth/status
   ```
   
   Response:
   ```json
   {
     "github": {
       "authenticated": true,
       "username": "your_github_username",
       "valid_token": true
     },
     "openai": {
       "authenticated": true,
       "valid_token": true
     }
   }
   ```

### Option 2: Langflow UI

1. **Access Langflow**:
   ```
   http://localhost:7860
   ```

2. **Import Workflow**:
   - Click "Import Flow"
   - Select: `langflow/flows/code_assistant_oauth.json`
   - The workflow will load

3. **Configure Workflow**:
   - Click on "OAuth Authentication Check" node
   - Select provider: `github` or `openai`
   - Save configuration

4. **Test Workflow**:
   - Enter a code request in the input node
   - Example: "Write a Python function to sort a list of dictionaries by a key"
   - Run the workflow
   - If not authenticated, you'll get a login URL
   - If authenticated, you'll get generated code

### Option 3: API Usage

```python
import requests

# Check if authenticated
response = requests.get("http://localhost:8000/oauth/status")
status = response.json()

if not status["github"]["authenticated"]:
    print("Please authenticate: http://localhost:8000/oauth/github/login")
else:
    # Use the Langflow workflow via API
    # The workflow will automatically use the authenticated token
    pass
```

## Workflow Architecture

The `code_assistant_oauth.json` workflow consists of:

```
┌─────────────┐
│ User Input  │
└──────┬──────┘
       │
       v
┌─────────────────────┐
│ OAuth Auth Check    │ ← Verifies authentication
└──────┬──────────────┘
       │
       v
┌─────────────────────┐
│ Provider Router     │ ← Routes to correct LLM
└──────┬──────────────┘
       │
       ├──────────────────┐
       │                  │
       v                  v
┌─────────────┐    ┌────────────────┐
│GitHub       │    │ OpenAI Codex   │
│Copilot      │    │ Generator      │
└──────┬──────┘    └────────┬───────┘
       │                    │
       └────────┬───────────┘
                │
                v
         ┌─────────────┐
         │ Formatter   │
         └──────┬──────┘
                │
                v
         ┌─────────────┐
         │   Output    │
         └─────────────┘
```

## Authentication Flow

### GitHub OAuth Flow

```
1. User visits /oauth/github/login
2. Redirect to GitHub authorization page
3. User authorizes application
4. GitHub redirects back with authorization code
5. Exchange code for access token
6. Store token securely in ./tokens/
7. Use token for Copilot API requests
```

### OpenAI Flow

```
1. User visits /oauth/openai/login
2. User enters API key in form
3. Validate API key
4. Store key securely in ./tokens/
5. Use key for OpenAI API requests
```

## Security Considerations

### Token Storage

- OAuth tokens are stored in `./tokens/` directory
- This directory is in `.gitignore` by default
- Tokens are stored as JSON files with restricted permissions
- **Never commit tokens to version control**

### Environment Variables

```bash
# Required for GitHub OAuth
GITHUB_OAUTH_CLIENT_ID=...
GITHUB_OAUTH_CLIENT_SECRET=...

# Required for OpenAI
OPENAI_OAUTH_CLIENT_ID=... (optional)
OPENAI_OAUTH_CLIENT_SECRET=... (optional)

# Token storage
OAUTH_TOKEN_PATH=./tokens
```

### Best Practices

1. **Keep OAuth credentials secure**:
   - Don't share Client ID/Secret publicly
   - Use environment variables, not hardcoded values
   - Rotate secrets periodically

2. **Use HTTPS in production**:
   ```bash
   ENFORCE_HTTPS=true
   SESSION_COOKIE_SECURE=true
   ```

3. **Set appropriate redirect URIs**:
   - Development: `http://localhost:8000/oauth/*/callback`
   - Production: `https://your-domain.com/oauth/*/callback`

4. **Monitor token usage**:
   ```bash
   # Check authentication status
   curl http://localhost:8000/oauth/status
   ```

## Troubleshooting

### "Not authenticated" Error

**Problem**: Workflow returns authentication required message.

**Solution**:
1. Check authentication status: `http://localhost:8000/oauth/status`
2. If not authenticated, visit login URL
3. Verify OAuth credentials in `.env`

### "Token exchange failed" Error

**Problem**: OAuth callback fails to exchange code for token.

**Solution**:
1. Verify Client ID and Secret are correct
2. Check redirect URI matches OAuth app configuration
3. Ensure callback URL is accessible
4. Check logs: `docker-compose logs web`

### "Invalid API key" (OpenAI)

**Problem**: OpenAI authentication fails.

**Solution**:
1. Verify API key is correct and starts with `sk-`
2. Check API key has necessary permissions
3. Ensure API key is not expired
4. Try generating a new key

### Tokens Not Persisting

**Problem**: Authentication required on every restart.

**Solution**:
1. Check `OAUTH_TOKEN_PATH` is set correctly
2. Verify tokens directory exists: `mkdir -p ./tokens`
3. Check file permissions
4. Ensure tokens directory is not in Docker ephemeral storage

## Advanced Usage

### Programmatic Authentication

```python
from integrations.oauth.github_oauth import GitHubOAuthIntegration

# Initialize OAuth
oauth = GitHubOAuthIntegration()

# Check if authenticated
if oauth.is_authenticated():
    # Generate code
    code = oauth.generate_code(
        prompt="Write a function to merge two sorted arrays",
        language="python"
    )
    print(code)
else:
    # Get authorization URL
    auth_url = oauth.get_authorization_url()
    print(f"Please authenticate: {auth_url}")
```

### Custom Langflow Components

The workflow uses custom components for OAuth:

```python
# OAuth Check Component
from integrations.oauth.github_oauth import GitHubOAuthIntegration
from integrations.oauth.openai_oauth import OpenAIOAuthIntegration

class OAuthCheck:
    def check_auth(self, provider: str) -> dict:
        if provider == 'github':
            oauth = GitHubOAuthIntegration()
        elif provider == 'openai':
            oauth = OpenAIOAuthIntegration()
        
        return {
            'authenticated': oauth.is_authenticated(),
            'provider': provider,
            'oauth': oauth
        }
```

### Token Refresh

Tokens are automatically refreshed when expired:

```python
# GitHub tokens don't typically expire
# But if they do, re-authentication is required

# OpenAI tokens can be refreshed
if not oauth.is_authenticated():
    if oauth.refresh_access_token():
        print("Token refreshed successfully")
    else:
        print("Re-authentication required")
```

## API Endpoints

### OAuth Endpoints

```
GET  /oauth/github/login       - Initiate GitHub OAuth flow
GET  /oauth/github/callback    - GitHub OAuth callback
GET  /oauth/openai/login       - OpenAI authentication form
POST /oauth/openai/callback    - OpenAI API key submission
GET  /oauth/status             - Check authentication status
POST /oauth/github/logout      - Logout from GitHub
POST /oauth/openai/logout      - Logout from OpenAI
```

### Example Usage

```bash
# Check status
curl http://localhost:8000/oauth/status

# Logout from GitHub
curl -X POST http://localhost:8000/oauth/github/logout

# Logout from OpenAI
curl -X POST http://localhost:8000/oauth/openai/logout
```

## Integration with Existing Agents

The OAuth workflow integrates with existing OsMEN agents:

```python
# In your agent code
from integrations.oauth.github_oauth import GitHubOAuthIntegration

class MyAgent:
    def __init__(self):
        self.copilot = GitHubOAuthIntegration()
    
    def generate_code(self, prompt: str):
        if not self.copilot.is_authenticated():
            return "Please authenticate at http://localhost:8000/oauth/github/login"
        
        return self.copilot.generate_code(prompt)
```

## Production Deployment

### HTTPS Configuration

Update `.env` for production:

```bash
GITHUB_OAUTH_REDIRECT_URI=https://your-domain.com/oauth/github/callback
OPENAI_OAUTH_REDIRECT_URI=https://your-domain.com/oauth/openai/callback
ENFORCE_HTTPS=true
SESSION_COOKIE_SECURE=true
```

### Update OAuth Apps

1. Go to GitHub OAuth app settings
2. Update "Authorization callback URL" to production URL
3. Save changes

### Token Storage in Production

```bash
# Use persistent volume for tokens
docker-compose.yml:
  volumes:
    - ./tokens:/app/tokens:rw
```

## Support

For issues or questions:

1. Check logs: `docker-compose logs web`
2. Verify configuration: `cat .env | grep OAUTH`
3. Test authentication: `http://localhost:8000/oauth/status`
4. Review documentation: `docs/OAUTH_WORKFLOW.md`

## References

- [GitHub OAuth Apps Documentation](https://docs.github.com/en/developers/apps/building-oauth-apps)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [Langflow Documentation](https://docs.langflow.org/)
- [OsMEN Architecture](docs/ARCHITECTURE.md)
