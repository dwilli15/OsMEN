# Memory System Usage Guide

## Overview

The OsMEN memory system provides persistent context continuity across sessions, enabling the AI assistant to maintain state, learn from past interactions, and operate autonomously within defined boundaries.

## Components

### 1. Conversation Storage (`conversation_store.py`)

**Purpose:** Stores all AI agent conversations with 45-day retention and permanent summaries.

**Features:**
- SQLite database for efficient storage and querying
- Automatic archival after 45 days
- Permanent summary generation
- Full-text search capability
- Metadata and context tracking

**Usage:**

```python
from conversation_store import ConversationStore

# Initialize
store = ConversationStore()

# Add conversation
conv_id = store.add_conversation(
    user_message="How do I set up the calendar?",
    agent_response="To set up calendar integration...",
    agent_name="copilot",
    context={"session": "planning", "phase": "v1.4.0"},
    metadata={"priority": "high"}
)

# Retrieve recent conversations
recent = store.get_conversations(limit=50)

# Search conversations
results = store.search_conversations("calendar integration")

# Get summaries
summaries = store.get_summaries()

# Cleanup (runs automatically daily)
deleted = store.cleanup_old_conversations(days=45)
```

**Database Location:** `.copilot/conversations.db`

### 2. Daily Summary Generator (`daily_summary.py`)

**Purpose:** Creates and sends daily email summaries of system activity.

**Features:**
- Analyzes previous day's conversations
- Tracks autonomous actions
- Identifies items requiring review
- Generates HTML and plain text emails
- Archives summaries as JSON files

**Usage:**

```python
from daily_summary import DailySummaryGenerator

# Initialize
generator = DailySummaryGenerator()

# Generate summary (defaults to yesterday)
summary = generator.generate_daily_summary()

# Save to file
generator.save_summary_to_file(summary)

# Send email (requires SMTP configuration)
recipient = "user@example.com"
generator.send_email_summary(summary, recipient)
```

**Email Schedule:** Daily at 6 PM UTC (configurable in `.github/workflows/daily-summary.yml`)

**Summary Archives:** `.copilot/daily_summaries/`

### 3. Auto-Update on PR Merge

**Purpose:** Automatically updates memory system when PRs are merged to main.

**Features:**
- Updates `memory.json` with PR details
- Adds PR to conversation history
- Updates `CONTEXT.md` with recent accomplishments
- Logs merge in `PROGRESS.md` daily log

**Configuration:** `.github/workflows/auto-update-memory.yml`

**Trigger:** Automatic on PR merge to main

### 4. Memory Files

#### `.copilot/memory.json`
**Purpose:** Machine-readable system state

**Contains:**
- System version and phase
- User profile and preferences
- Integration configurations
- Automation rules
- Conversation history (last 100 entries)
- Decisions made
- Learned preferences

**Auto-Updates:** Yes, on PR merge

#### `docs/CONTEXT.md`
**Purpose:** Human-readable current state

**Contains:**
- Active work and priorities
- Recent accomplishments
- User profile
- Tool integrations
- Decision-making framework
- Innovation watch list
- Next actions

**Auto-Updates:** Yes, on PR merge

#### `docs/DECISION_LOG.md`
**Purpose:** Architectural Decision Records (ADRs)

**Contains:**
- Major design decisions
- Rationale and alternatives
- Consequences and validation

**Auto-Updates:** Manual (add new ADRs as needed)

#### `PROGRESS.md`
**Purpose:** Timestamped task tracking

**Contains:**
- Current sprint progress
- Completed sprints
- Daily progress logs
- Metrics and velocity
- Blockers and risks

**Auto-Updates:** Yes, on PR merge (daily log)

#### `CHANGELOG.md`
**Purpose:** Version history

**Format:** Keep a Changelog standard

**Auto-Updates:** Manual (update on releases)

## Automation

### Daily Tasks (6 PM UTC)
1. Generate daily summary
2. Clean conversations older than 45 days
3. Archive summaries
4. Send email (if configured)

### On PR Merge
1. Update memory.json
2. Update CONTEXT.md
3. Add to PROGRESS.md daily log
4. Commit changes to main

### Weekly Tasks (Manual)
1. Review pre-approved tasks list
2. Review innovation backlog
3. Prune outdated items
4. Update priorities

## Configuration

### Email Delivery

Set environment variables in repository settings:

```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=osmen@yourdomain.com
```

Add recipient to `memory.json`:

```json
{
  "user_profile": {
    "email": "your-email@example.com"
  }
}
```

### Conversation Retention

Default: 45 days for full conversations, permanent summaries

To change:

```python
# In daily_summary.py
store.cleanup_old_conversations(days=30)  # Change to desired days
```

### Summary Schedule

Edit `.github/workflows/daily-summary.yml`:

```yaml
on:
  schedule:
    # Change cron expression (currently 6 PM UTC)
    - cron: '0 18 * * *'
```

## Usage Patterns

### For Copilot Agents

When invoked, Copilot can:

1. **Read context:**
```python
import json
with open('.copilot/memory.json') as f:
    memory = json.load(f)
    current_phase = memory['system_state']['current_phase']
```

2. **Store conversations:**
```python
store = ConversationStore()
store.add_conversation(
    user_message=user_input,
    agent_response=my_response,
    context={"phase": "v1.4.0"}
)
```

3. **Check past decisions:**
```python
# Search for similar past conversations
results = store.search_conversations("calendar integration")
```

### For Users

**View Daily Summary:**
- Check email inbox at 6 PM
- Or view web dashboard (when implemented in v1.7.0)
- Or check `.copilot/daily_summaries/` directory

**Review Autonomous Actions:**
- Daily digest includes all autonomous actions
- Weekly review on Sunday at 6 PM
- Approve/reject via web dashboard

**Search Conversations:**
```bash
python3 << 'EOF'
from conversation_store import ConversationStore
store = ConversationStore()
results = store.search_conversations("your search term")
for r in results:
    print(f"{r['timestamp']}: {r['user_message'][:100]}")
EOF
```

## Troubleshooting

### Email Not Sending

1. Check SMTP configuration in repository secrets
2. Verify recipient email in memory.json
3. Check GitHub Actions logs for error messages
4. Fallback: Summaries always saved to `.copilot/daily_summaries/`

### Database Locked

If SQLite database is locked:

```bash
# Check if process is using it
lsof .copilot/conversations.db

# If stuck, can safely delete and rebuild
rm .copilot/conversations.db
# Next conversation will recreate it
```

### Memory Not Updating on PR Merge

1. Check PR was merged (not just closed)
2. Verify GitHub Actions workflow completed
3. Check workflow permissions in repository settings
4. Look at Actions tab for error logs

### Missing Conversations

Conversations are automatically archived after 45 days. To retrieve:

```python
summaries = store.get_summaries()
# Search summaries for the time period
```

## Best Practices

### For Development

1. **Add Context:** Always include context when storing conversations
2. **Use Metadata:** Tag conversations with priority, category, etc.
3. **Search First:** Check past conversations before asking Copilot
4. **Review Summaries:** Weekly review keeps you informed

### For Autonomy

1. **Start Conservative:** Begin with few pre-approved tasks
2. **Review Weekly:** Sunday 6 PM review is critical
3. **Monitor Daily:** Read daily digest emails
4. **Audit Trail:** All autonomous actions are logged

### For Privacy

1. **Local Storage:** All data stored locally in repository
2. **Retention Policy:** 45 days for full conversations
3. **No External Calls:** Email is optional, everything works offline
4. **Git Ignored:** Add `.copilot/conversations.db` to .gitignore for privacy

## Future Enhancements

Planned for future versions:

- **v1.7.0:** Web dashboard for viewing conversations and summaries
- **v1.7.0:** Interactive approval interface for daily digest
- **v1.8.0:** Integration with Obsidian for knowledge management
- **v2.0.0:** AI-powered conversation analysis and insights

## Support

For issues or questions:
- Check documentation in `docs/` directory
- Review `TROUBLESHOOTING.md`
- Search past conversations in database
- Create GitHub issue

---

**Last Updated:** 2025-11-09  
**Version:** 1.2.0  
**Status:** Implemented and operational
