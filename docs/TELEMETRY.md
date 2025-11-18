# Telemetry and Privacy Disclosure

Complete transparency about data collection, telemetry, and privacy practices in OsMEN.

## Summary

**OsMEN does NOT collect or transmit telemetry data.**

This is a fully local-first, privacy-focused system. All data remains on your infrastructure unless you explicitly integrate with external services.

## Data Collection Policy

### ❌ What We DON'T Collect

- No usage statistics
- No error reports
- No analytics
- No user behavior tracking
- No automatic crash reports
- No phone-home functionality

### ✅ What Stays Local

All of the following data remains entirely on your infrastructure:

| Data Type | Storage Location | Privacy Level |
|-----------|-----------------|---------------|
| Agent conversations | PostgreSQL + Qdrant | Private |
| User content | Local file system | Private |
| Workflow data | Docker volumes | Private |
| Configuration | .env file | Private |
| API keys | .env file | Sensitive |
| Logs | Local logs/ directory | Private |
| Database | PostgreSQL container | Private |
| Vector embeddings | Qdrant container | Private |

## External Data Transmission

### When Data Leaves Your System

Data is ONLY transmitted externally when YOU explicitly configure integrations:

#### LLM Providers (Optional)

If you configure cloud LLM providers, prompts and responses are sent to:

| Provider | Data Sent | Privacy Policy |
|----------|-----------|---------------|
| **OpenAI** | Prompts, context | [OpenAI Privacy](https://openai.com/privacy) |
| **Anthropic** | Prompts, context | [Anthropic Privacy](https://www.anthropic.com/privacy) |
| **Google** | Prompts, context | [Google Privacy](https://policies.google.com/privacy) |
| **GitHub Copilot** | Code, prompts | [GitHub Privacy](https://docs.github.com/en/site-policy/privacy-policies) |
| **Amazon Q** | Prompts, context | [AWS Privacy](https://aws.amazon.com/privacy/) |

**To avoid external transmission:** Use local LLMs (Ollama, LM Studio)

#### Tool Integrations (Optional)

If you enable tool integrations, relevant data is sent to:

| Integration | Data Sent | Required |
|------------|-----------|----------|
| **Gmail** | Email content, metadata | No |
| **Outlook** | Email content, metadata | No |
| **Zoom** | Meeting data, transcripts | No |
| **Notion** | Notes, page content | No |
| **Obsidian** | None (local only) | No |
| **Google Calendar** | Event data | No |

**All integrations are opt-in and can be disabled.**

#### Update Checks (Optional)

If enabled, version checks connect to:

```
https://api.github.com/repos/dwilli15/OsMEN/releases/latest
```

**Transmitted:** Current version number  
**Received:** Latest version info  
**To disable:** Set `CHECK_UPDATES=false` in .env

## Privacy Modes

### Full Privacy Mode (Local-Only)

For maximum privacy:

```bash
# .env configuration for full privacy
# Use local LLM only
OLLAMA_URL=http://ollama:11434
LM_STUDIO_URL=http://host.docker.internal:1234

# Disable cloud providers (comment out or remove)
# OPENAI_API_KEY=
# ANTHROPIC_API_KEY=
# GEMINI_API_KEY=

# Disable external tool integrations
EMAIL_MANAGER_ENABLED=false
ZOOM_LIVE_CAPTION_ENABLED=false
NOTION_SYNC_ENABLED=false
TODOIST_SYNC_ENABLED=false

# Disable update checks
CHECK_UPDATES=false

# Use local Obsidian only
OBSIDIAN_VAULT_PATH=./obsidian-vault
```

**In this mode:**
- ✅ All data stays on your infrastructure
- ✅ No external API calls
- ✅ No internet connection required (after initial setup)
- ✅ Complete data sovereignty

### Hybrid Mode (Recommended)

Balance between privacy and functionality:

```bash
# Use cloud LLM for complex tasks
OPENAI_API_KEY=your-key-here

# Use local LLM for sensitive tasks
OLLAMA_URL=http://ollama:11434

# Enable only necessary integrations
EMAIL_MANAGER_ENABLED=true
ZOOM_LIVE_CAPTION_ENABLED=false
NOTION_SYNC_ENABLED=false
```

## Data Retention

### Local Data Retention

You have full control over data retention:

| Data Type | Default Retention | Configurable |
|-----------|------------------|--------------|
| Conversations | Indefinite | Yes |
| Logs | 30 days | Yes |
| Vector embeddings | Indefinite | Yes |
| Workflow history | Indefinite | Yes |
| Cache | 1 hour | Yes |

**Configure retention:**

```bash
# .env
LOG_RETENTION_DAYS=30
CACHE_TTL_SECONDS=3600
VECTOR_RETENTION_DAYS=365  # Or 0 for indefinite
```

**Manual cleanup:**

```bash
# Clear old logs
find logs/ -name "*.log" -mtime +30 -delete

# Clear cache
docker exec osmen-redis redis-cli FLUSHDB

# Clear old vectors (if configured)
# This removes embeddings older than specified date
```

### Cloud Provider Retention

When using cloud LLM providers, data retention is governed by their policies:

| Provider | Retention | Can Request Deletion |
|----------|-----------|---------------------|
| OpenAI | 30 days (API) | Yes |
| Anthropic | Not stored | N/A |
| Google | Per account settings | Yes |
| GitHub | Per account settings | Yes |

**Best Practice:** Review each provider's data retention policy before use.

## GDPR Compliance

### Data Subject Rights

As OsMEN is self-hosted, YOU are the data controller. Users can exercise rights:

1. **Right to Access:** View all data via PostgreSQL/Qdrant
2. **Right to Rectification:** Edit data directly
3. **Right to Erasure:** Delete data from database
4. **Right to Data Portability:** Export via backup scripts
5. **Right to Object:** Disable specific features

### Implementation

```python
# Example: Export user data (GDPR Article 20)
def export_user_data(user_id):
    # Export conversations
    conversations = db.query("SELECT * FROM conversations WHERE user_id = ?", user_id)
    
    # Export vectors
    vectors = qdrant.search(filter={"user_id": user_id})
    
    # Package as JSON
    return {
        "conversations": conversations,
        "vectors": vectors,
        "format": "JSON",
        "timestamp": datetime.now().isoformat()
    }

# Example: Delete user data (GDPR Article 17)
def delete_user_data(user_id):
    db.execute("DELETE FROM conversations WHERE user_id = ?", user_id)
    db.execute("DELETE FROM user_preferences WHERE user_id = ?", user_id)
    qdrant.delete(filter={"user_id": user_id})
    redis.delete(f"cache:user:{user_id}:*")
```

## CCPA Compliance

For California residents, OsMEN supports:

1. **Right to Know:** Full data transparency
2. **Right to Delete:** Complete data deletion
3. **Right to Opt-Out:** Disable all external integrations
4. **Right to Non-Discrimination:** No feature restrictions

## Logging and Monitoring

### What's Logged Locally

```python
# Example log entry
{
    "timestamp": "2024-11-18T10:00:00Z",
    "level": "INFO",
    "service": "gateway",
    "event": "agent_execution",
    "agent": "daily_brief",
    "user_id": "user123",  # Optional
    "duration_ms": 2341,
    "status": "success"
}
```

**Logs contain:**
- Timestamps
- Service names
- Event types
- Performance metrics
- Error messages (sanitized)

**Logs DO NOT contain:**
- Full conversation content
- API keys
- Passwords
- Personal identifiable information (by default)

### Log Sanitization

```python
# Automatic sanitization of sensitive data
import re

def sanitize_log(message):
    # Remove API keys
    message = re.sub(r'(api[_-]key["\s:=]+)[^"\s]+', r'\1***REDACTED***', message, flags=re.IGNORECASE)
    # Remove tokens
    message = re.sub(r'(token["\s:=]+)[^"\s]+', r'\1***REDACTED***', message, flags=re.IGNORECASE)
    # Remove passwords
    message = re.sub(r'(password["\s:=]+)[^"\s]+', r'\1***REDACTED***', message, flags=re.IGNORECASE)
    return message
```

## Security and Encryption

### Data at Rest

**Default Encryption:**
- Docker volumes: Depends on host filesystem
- PostgreSQL: Not encrypted by default
- Qdrant: Not encrypted by default

**Enable Encryption:**

```bash
# PostgreSQL encryption
# Add to docker-compose.yml
services:
  postgres:
    environment:
      - POSTGRES_INITDB_ARGS=--data-checksums
    volumes:
      - encrypted_volume:/var/lib/postgresql/data

# Use encrypted filesystem (LUKS on Linux)
cryptsetup luksFormat /dev/sdb
cryptsetup open /dev/sdb encrypted_disk
mkfs.ext4 /dev/mapper/encrypted_disk
mount /dev/mapper/encrypted_disk /mnt/encrypted
```

### Data in Transit

**Internal Communication:**
- Within Docker network: Unencrypted (isolated)
- Can enable TLS for service-to-service

**External Communication:**
- API Gateway: TLS/HTTPS required for production
- LLM APIs: Always HTTPS
- Tool integrations: HTTPS

**Enable HTTPS:**

```bash
# In .env
ENFORCE_HTTPS=true

# In docker-compose.yml
services:
  gateway:
    ports:
      - "443:443"
    volumes:
      - ./certs:/certs
    environment:
      - TLS_CERT=/certs/fullchain.pem
      - TLS_KEY=/certs/privkey.pem
```

## Third-Party Services

### Analytics (Disabled by Default)

OsMEN does not include analytics by default. If you choose to add analytics:

**Options:**
- Self-hosted: Matomo, Plausible, Umami
- Cloud: Google Analytics (requires explicit setup)

**To add (example):**
```yaml
# docker-compose.analytics.yml
services:
  plausible:
    image: plausible/analytics:latest
    environment:
      - SECRET_KEY_BASE=your-secret-key
```

### Error Tracking (Optional)

**Sentry Integration (Opt-in):**

```bash
# In .env - leave empty to disable
SENTRY_DSN=  # Empty = disabled

# To enable:
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
SENTRY_ENVIRONMENT=production
```

**What Sentry collects (if enabled):**
- Error stack traces
- Request context
- User-agent
- Does NOT collect: Prompts, API keys, conversation content

## Opting Out

### Disable All External Communication

```bash
# Complete opt-out configuration
# .env

# Disable cloud LLMs (use local only)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
GITHUB_TOKEN=

# Enable local LLM
OLLAMA_URL=http://ollama:11434
LM_STUDIO_URL=http://host.docker.internal:1234

# Disable all cloud integrations
EMAIL_MANAGER_ENABLED=false
ZOOM_LIVE_CAPTION_ENABLED=false
NOTION_SYNC_ENABLED=false
TODOIST_SYNC_ENABLED=false

# Disable error tracking
SENTRY_DSN=

# Disable update checks
CHECK_UPDATES=false

# Disable all external tool integrations
EXTERNAL_TOOLS_ENABLED=false
```

### Network-Level Blocking

```bash
# Firewall rules to prevent external access
# (while allowing necessary services)

# Allow only essential services
sudo ufw default deny outgoing
sudo ufw allow out 53/udp  # DNS
sudo ufw allow out to [your-ollama-instance]

# Block everything else
sudo ufw enable
```

## Audit and Verification

### Verify No External Communication

```bash
# Monitor network traffic
sudo tcpdump -i any -n | grep -v "localhost\|127.0.0.1"

# Check open connections
netstat -an | grep ESTABLISHED

# Analyze with Wireshark
wireshark -i any -f "not host localhost"
```

### Audit Logs

```bash
# Check all HTTP requests in logs
grep -r "http://" logs/ | grep -v "localhost\|127.0.0.1"

# Check for external DNS queries
sudo tcpdump -i any port 53
```

## Privacy-Enhancing Features

### Conversation Encryption

```python
# Optional: Encrypt conversations before storing
from cryptography.fernet import Fernet

key = Fernet.generate_key()
cipher = Fernet(key)

def store_encrypted_conversation(content):
    encrypted = cipher.encrypt(content.encode())
    db.execute("INSERT INTO conversations (content) VALUES (?)", encrypted)

def retrieve_encrypted_conversation(id):
    encrypted = db.query("SELECT content FROM conversations WHERE id = ?", id)
    return cipher.decrypt(encrypted).decode()
```

### Ephemeral Mode

```bash
# Run in ephemeral mode (no persistence)
docker-compose -f docker-compose.ephemeral.yml up

# All data in memory, deleted on restart
```

## Contact for Privacy Questions

- **Privacy Policy Questions:** privacy@osmen.dev
- **Data Deletion Requests:** privacy@osmen.dev
- **Security Concerns:** security@osmen.dev
- **General Questions:** [GitHub Discussions](https://github.com/dwilli15/OsMEN/discussions)

## Changes to This Policy

When we update this telemetry policy:

1. Update `TELEMETRY.md` with changes
2. Tag the change in git
3. Announce in release notes
4. No retroactive changes to data handling

## Resources

- [GDPR Compliance Checklist](https://gdpr.eu/checklist/)
- [CCPA Compliance Guide](https://oag.ca.gov/privacy/ccpa)
- [Privacy by Design](https://www.ipc.on.ca/wp-content/uploads/resources/7foundationalprinciples.pdf)
- [Local-First Software](https://www.inkandswitch.com/local-first/)

---

**Last Updated:** 2024-11-18  
**Policy Version:** 1.0  
**Effective Date:** 2024-11-18
