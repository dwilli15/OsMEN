# Memory System Quick Start Guide

The OsMEN Memory & Context System provides persistent memory, conversation history, and automated daily summaries for continuous operation.

## Overview

The memory system consists of:
- **Conversation Storage**: SQLite database with 45-day retention
- **Daily Summaries**: Automated generation and archival
- **Context Tracking**: Real-time system state monitoring
- **Auto-Updates**: GitHub workflow integration

## Quick Usage

### 1. Check System Status

```bash
# Run comprehensive tests
python3 test_memory_system.py

# Generate a summary manually
cd .copilot
python3 daily_summary.py
```

### 2. Add a Conversation

```python
from conversation_store import ConversationStore

store = ConversationStore()

# Add a conversation
conv_id = store.add_conversation(
    user_message="How do I set up calendar integration?",
    agent_response="To set up calendar integration...",
    context={"phase": "v1.4.0", "feature": "calendar"}
)

print(f"Conversation saved: {conv_id}")
```

### 3. Retrieve Conversations

```python
from datetime import datetime, timedelta, timezone

# Get recent conversations
recent = store.get_conversations(limit=10)

# Get conversations from last 7 days
week_ago = datetime.now(timezone.utc) - timedelta(days=7)
recent_week = store.get_conversations(start_date=week_ago, limit=100)

# Search conversations
results = store.search_conversations("calendar")
```

### 4. Generate Daily Summary

```python
from daily_summary import DailySummaryGenerator

generator = DailySummaryGenerator()

# Generate summary for yesterday (default)
summary = generator.generate_daily_summary()

# Generate for specific date
from datetime import datetime
specific_date = datetime(2025, 11, 8)
summary = generator.generate_daily_summary(date=specific_date)

# Save to file
generator.save_summary_to_file(summary)

# Send via email (requires SMTP configuration)
# generator.send_email_summary(summary, "user@example.com")
```

### 5. Configure Email Summaries

Set environment variables in your shell or `.env` file:

```bash
# SMTP Configuration
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export SMTP_FROM="osmen@yourdomain.com"
```

Then send summaries:

```python
generator.send_email_summary(summary, "recipient@example.com")
```

## Automated Workflows

### Daily Summary Workflow

Runs automatically at 6 PM UTC (customizable in `.github/workflows/daily-summary.yml`):

```yaml
on:
  schedule:
    - cron: '0 18 * * *'  # Adjust to your timezone
  workflow_dispatch:      # Manual trigger available
```

**What it does:**
1. Generates daily summary
2. Archives summary as artifact (90-day retention)
3. Cleans up conversations older than 45 days
4. Creates permanent summaries from archived conversations

### Auto-Update Workflow

Runs automatically when PRs are merged to main:

**What it does:**
1. Updates `memory.json` with PR details
2. Updates `CONTEXT.md` with recent accomplishments
3. Updates `PROGRESS.md` with daily log entry
4. Commits and pushes changes

## File Structure

```
.copilot/
├── memory.json                 # System state and user profile
├── conversation_store.py       # Conversation storage module
├── daily_summary.py           # Summary generation module
├── conversations.db           # SQLite database (auto-created)
└── daily_summaries/           # Archived summaries
    └── summary_YYYY-MM-DD.json

docs/
├── CONTEXT.md                 # Current state (human-readable)
├── DECISION_LOG.md           # Architectural decisions
├── ROADMAP.md                # Development timeline
└── MASTER_PLAN.md            # Multi-phase plan

PROGRESS.md                    # Timestamped task tracking
CHANGELOG.md                   # Version history
```

## Database Schema

### Conversations Table

```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    user_message TEXT NOT NULL,
    agent_response TEXT NOT NULL,
    agent_name TEXT DEFAULT 'copilot',
    context TEXT,                -- JSON blob
    metadata TEXT,               -- JSON blob
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Summaries Table

```sql
CREATE TABLE summaries (
    id TEXT PRIMARY KEY,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    summary TEXT NOT NULL,
    conversation_count INTEGER,
    key_topics TEXT,             -- JSON array
    decisions_made TEXT,         -- JSON array
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Memory Retention Policy

- **Conversations**: 45 days (configurable)
- **Summaries**: Permanent
- **memory.json history**: Last 100 entries
- **GitHub Artifacts**: 90 days

## Customization

### Change Retention Period

Edit `conversation_store.py`:

```python
# Default is 45 days
deleted = store.cleanup_old_conversations(days=30)  # Change to 30 days
```

Or in the workflow:

```yaml
- name: Cleanup old conversations
  run: |
    python3 -c "
    from conversation_store import ConversationStore
    store = ConversationStore()
    store.cleanup_old_conversations(days=60)  # 60 days instead
    "
```

### Change Summary Schedule

Edit `.github/workflows/daily-summary.yml`:

```yaml
on:
  schedule:
    # Run at 9 AM UTC instead of 6 PM
    - cron: '0 9 * * *'
```

### Customize Summary Content

Edit `daily_summary.py` methods:
- `_extract_highlights()`: Change how highlights are detected
- `_identify_review_items()`: Modify what requires review
- `format_email_html()`: Customize HTML template
- `format_email_text()`: Customize text template

## Troubleshooting

### Conversations Not Saving

Check database permissions:
```bash
ls -la .copilot/conversations.db
```

Test manually:
```bash
python3 .copilot/conversation_store.py
```

### Summaries Not Generating

Check Python version (requires 3.12+):
```bash
python3 --version
```

Run manually:
```bash
cd .copilot
python3 daily_summary.py
```

### Email Not Sending

Verify SMTP settings:
```bash
echo $SMTP_SERVER
echo $SMTP_USERNAME
```

Test with a simple script:
```python
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('username', 'password')
# If this works, your credentials are correct
```

### Workflow Not Running

Check GitHub Actions permissions:
- Go to repository Settings > Actions > General
- Ensure "Read and write permissions" is enabled

Manually trigger:
- Go to Actions tab
- Select "Daily Summary Generation"
- Click "Run workflow"

## Advanced Usage

### Custom Conversation Metadata

```python
store.add_conversation(
    user_message="Question",
    agent_response="Answer",
    context={
        "phase": "v1.4.0",
        "feature": "calendar",
        "priority": "high",
        "assignee": "copilot"
    },
    metadata={
        "session_id": "abc123",
        "duration_ms": 1500,
        "model": "gpt-4"
    }
)
```

### Batch Retrieval

```python
# Get all conversations from a specific phase
phase_convs = store.search_conversations("v1.4.0")

# Get all error-related conversations
error_convs = store.search_conversations("error")
```

### Custom Summary Analysis

```python
from daily_summary import DailySummaryGenerator

generator = DailySummaryGenerator()
summary = generator.generate_daily_summary()

# Extract specific metrics
conv_count = summary['conversations']['count']
pending_count = len(summary['pending_tasks'])
review_count = len(summary['requires_review'])

print(f"Daily Stats: {conv_count} convs, {pending_count} pending, {review_count} to review")
```

## Security Considerations

1. **Never commit** `.copilot/conversations.db` to git (already in `.gitignore`)
2. **Encrypt SMTP passwords** using GitHub secrets
3. **Limit access** to memory.json (contains user profile)
4. **Review summaries** before external sharing
5. **Rotate credentials** periodically

## Support

- **Issues**: [GitHub Issues](https://github.com/dwilli15/OsMEN/issues)
- **Documentation**: See `docs/` directory
- **Tests**: Run `python3 test_memory_system.py`

---

**Last Updated**: 2025-11-09  
**Version**: 1.2.0
