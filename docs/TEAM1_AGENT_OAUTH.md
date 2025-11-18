# Team 1 Agent & Orchestration System

## Overview

This document describes the autonomous agent coordination system for the OsMEN Day 1 OAuth sprint. The system enables multiple team agents to work in parallel, coordinating their efforts through a central orchestration agent.

## Architecture

### Components

1. **Orchestration Agent** (`agents/orchestration_agent/`)
   - Coordinates all team agents
   - Manages inter-agent communication via message queue
   - Tracks progress and milestones
   - Handles blocker resolution
   - Facilitates secret requests from users
   - Coordinates PR creation

2. **Team 1 OAuth Agent** (`agents/team1_oauth_agent/`)
   - Autonomous execution of Google OAuth implementation tasks
   - Follows TODO.md checklist from `sprint/day1/team1_google_oauth/`
   - Reports progress to orchestration agent
   - Requests secrets when needed (OAuth credentials)
   - Creates milestones at key checkpoints

3. **OAuth Implementation** (`integrations/oauth/`)
   - Base OAuth handler framework
   - Google OAuth 2.0 implementation
   - Provider registry system
   - Configuration management

### Message-Based Coordination

Agents communicate through a file-based message queue in `/tmp/osmen_messages/`:

```
/tmp/osmen_messages/
├── orchestration/
│   ├── inbox/          # Messages TO orchestration agent
│   └── outbox/         # Messages FROM orchestration agent
└── team1_google_oauth/
    ├── inbox/          # Messages TO team1 agent
    └── outbox/         # Messages FROM team1 agent
```

### Message Types

1. **team_registration** - Team registers with orchestration
2. **status_update** - Regular progress updates
3. **blocker_report** - Report blocking issues
4. **secret_request** - Request credentials from user
5. **pr_request** - Request pull request creation
6. **milestone_completed** - Report milestone achievement
7. **start_work** - Orchestration signals teams to begin

## Usage

### Running the Sprint

Execute the sprint runner to start autonomous coordination:

```bash
python3 run_sprint.py
```

This will:
1. Initialize orchestration and team agents
2. Register teams with orchestration
3. Start coordination loop
4. Execute tasks autonomously
5. Report final status

### Manual Agent Control

You can also run agents individually for testing:

```python
from agents.orchestration_agent.orchestration_agent import OrchestrationAgent
from agents.team1_oauth_agent.team1_oauth_agent import Team1OAuthAgent

# Create orchestration agent
orchestration = OrchestrationAgent()

# Create and register team agent
team1 = Team1OAuthAgent()
orchestration.register_team("team1_google_oauth", {
    'lead': 'OAuth Lead',
    'focus': 'Google OAuth Implementation'
})

# Run orchestration loop
orchestration.run_coordination_loop(iterations=10, interval=30)

# Or run team agent directly
result = team1.run(check_interval=30, max_iterations=20)
```

## OAuth Setup

### Using the OAuth Wizard

The interactive OAuth setup wizard guides you through configuration:

```bash
python3 cli_bridge/oauth_setup.py
```

The wizard will:
1. Check for OAuth credentials (or help you get them)
2. Generate authorization URL
3. Open browser for user consent
4. Exchange authorization code for tokens
5. Validate tokens
6. Save configuration securely

### Manual OAuth Configuration

1. **Get OAuth Credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create project and enable APIs (Calendar, Gmail, Contacts)
   - Create OAuth 2.0 Client ID
   - Add redirect URI: `http://localhost:8080/oauth/callback`
   - Copy Client ID and Client Secret

2. **Configure Environment**:
   ```bash
   # Add to .env file
   GOOGLE_CLIENT_ID=your_client_id_here
   GOOGLE_CLIENT_SECRET=your_client_secret_here
   ```

3. **Use OAuth Handler**:
   ```python
   from integrations.oauth import get_oauth_handler
   
   # Get Google OAuth handler
   config = {
       'client_id': os.getenv('GOOGLE_CLIENT_ID'),
       'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
       'redirect_uri': 'http://localhost:8080/oauth/callback',
       'scopes': [
           'https://www.googleapis.com/auth/calendar',
           'https://www.googleapis.com/auth/gmail.modify'
       ]
   }
   
   handler = get_oauth_handler('google', config)
   
   # Generate authorization URL
   auth_url = handler.get_authorization_url()
   print(f"Visit: {auth_url}")
   
   # After user authorizes, exchange code for tokens
   code = input("Enter authorization code: ")
   tokens = handler.exchange_code_for_token(code)
   
   # Use access token
   access_token = tokens['access_token']
   
   # Refresh token when expired
   new_tokens = handler.refresh_token(tokens['refresh_token'])
   ```

## Team 1 Tasks

The Team 1 agent autonomously executes these tasks:

### Hour 1-2: Foundation
- [x] Create OAuth directory structure
- [x] Implement OAuthHandler base class
- [x] Create configuration schema
- [x] Implement provider registry

### Hour 3-4: Google OAuth
- [x] Create GoogleOAuthHandler
- [x] Implement authorization URL generation
- [x] Implement token exchange

### Hour 5-6: Token Management
- [x] Implement token refresh
- [x] Implement token validation
- [x] Implement token revocation

### Hour 7-8: Tooling & Testing
- [x] Create OAuth setup wizard
- [x] Create unit tests
- [ ] Implement OAuth flow generator script

## Testing

### Unit Tests

Run OAuth unit tests:

```bash
python3 -m pytest tests/unit/oauth/ -v
```

Current test coverage:
- OAuth handler initialization
- Authorization URL generation
- Configuration validation

### Integration Testing

Test the agent coordination system:

```bash
# Run sprint with limited duration
python3 run_sprint.py

# Check message queue
ls -la /tmp/osmen_messages/*/inbox/
```

### Existing Tests

All existing agent tests still pass:

```bash
python3 test_agents.py
# Output: 15/15 tests passed ✅
```

## Configuration

### OAuth Provider Configuration

Provider configurations are stored in `config/oauth/`:

```yaml
# config/oauth/google.yaml
provider: google
type: oauth2

# OAuth endpoints
auth_endpoint: https://accounts.google.com/o/oauth2/v2/auth
token_endpoint: https://oauth2.googleapis.com/token

# Credentials (from .env)
client_id: ${GOOGLE_CLIENT_ID}
client_secret: ${GOOGLE_CLIENT_SECRET}

# Scopes
scopes:
  - https://www.googleapis.com/auth/calendar
  - https://www.googleapis.com/auth/gmail.modify
  - https://www.googleapis.com/auth/contacts
```

### Agent Configuration

Agents can be configured via their constructors:

```python
# Custom message directory
agent = Team1OAuthAgent(message_dir="/custom/path/messages")

# Custom repository root
agent = Team1OAuthAgent(repo_root="/path/to/osmen")
```

## Security Considerations

1. **Secrets Management**:
   - Never commit `.env` file with real credentials
   - OAuth tokens stored with 600 permissions
   - Team agent requests secrets from user via orchestration

2. **Token Storage**:
   - Tokens saved to `~/.osmen/tokens/` (user-only access)
   - Future: Encrypt tokens at rest (Team 5 integration)

3. **Communication**:
   - Message queue in `/tmp` (ephemeral)
   - No sensitive data in message files
   - Secrets referenced by name, not value

## Troubleshooting

### Agent Won't Start

Check message directory permissions:
```bash
ls -la /tmp/osmen_messages/
chmod 755 /tmp/osmen_messages/
```

### OAuth Credentials Not Found

Verify environment variables:
```bash
echo $GOOGLE_CLIENT_ID
echo $GOOGLE_CLIENT_SECRET
```

Or use the wizard:
```bash
python3 cli_bridge/oauth_setup.py
```

### Messages Not Delivered

Check message queue:
```bash
# List pending messages
find /tmp/osmen_messages -name "*.json" -type f

# View a message
cat /tmp/osmen_messages/orchestration/inbox/123456789.json
```

Clear stuck messages:
```bash
rm -rf /tmp/osmen_messages/*/inbox/*.json
```

## Future Enhancements

1. **Additional Teams**:
   - Team 2: Microsoft OAuth
   - Team 3: API Client Generation
   - Team 4: Testing Infrastructure
   - Team 5: Token Security

2. **Enhanced Coordination**:
   - Dependency graph management
   - Parallel task execution
   - Automatic blocker resolution
   - Real-time progress dashboard

3. **OAuth Features**:
   - Additional providers (GitHub, Azure, AWS)
   - PKCE support
   - Token encryption (integration with Team 5)
   - Automatic token refresh daemon

## References

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [OWASP OAuth Security](https://cheatsheetseries.owasp.org/cheatsheets/OAuth2_Cheat_Sheet.html)
- Team 1 TODO: `sprint/day1/team1_google_oauth/TODO.md`
- Orchestration TODO: `sprint/day1/orchestration/TODO.md`
