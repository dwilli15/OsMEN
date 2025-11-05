# Daily Brief Workflow Runbook

## Overview
Automated morning briefing providing comprehensive system status, tasks, and priorities.

## Trigger
- **Type**: Scheduled (Cron)
- **Frequency**: Daily at 09:00 AM
- **n8n Workflow**: `daily_brief_trigger.json`
- **Langflow Agent**: `daily_brief_specialist.json`

## Workflow Steps

### 1. Scheduled Trigger
- n8n cron trigger fires at 09:00 daily
- Initiates data collection phase

### 2. Data Collection
- **Calendar Events**: Fetch today's schedule from configured calendar
- **Deadlines**: Query upcoming deadlines from task management system
- **System Health**: CPU, memory, disk usage metrics
- **Pending Updates**: Check for system/app updates
- **Bibliography**: Query research notes from Qdrant vector store

### 3. Agent Analysis
- Langflow Grad Navigator processes collected data
- Prioritizes tasks based on urgency and importance
- Cross-references bibliography memory for context
- Generates structured daily digest

### 4. Output Generation
- Format digest as markdown/HTML
- Optional: Convert to speech using text-to-speech
- Send via configured channels:
  - Email (if configured)
  - Notion page update (if configured)
  - Local file: `content/output/daily_brief_<date>.md`

### 5. Archival
- n8n archives summary to progress log
- Updates daily log in `logs/daily_briefs/`
- Stores in vector memory for future reference

## Success Criteria
- Digest delivered by 09:05 AM
- All data sources successfully queried
- Actionable next steps clearly surfaced
- No missing critical information

## Failure Handling

### Calendar Unavailable
- Continue with cached data from yesterday
- Note in brief that calendar is unavailable
- Use fallback to local task list

### Agent Generation Fails
- Use template-based brief with collected data
- Log error for investigation
- Send notification to user

### Delivery Fails
- Retry delivery 3 times with exponential backoff
- Save locally as fallback
- Alert user via alternative channel

## Manual Execution
```bash
# Trigger manually from n8n UI
# 1. Open n8n at http://localhost:5678
# 2. Navigate to "Daily Brief" workflow
# 3. Click "Execute Workflow" button

# Or via CLI:
curl -X POST http://localhost:5678/webhook/daily-brief \
  -H "Content-Type: application/json" \
  -d '{"trigger": "manual", "date": "2024-01-01"}'
```

## Example Output
```markdown
# Daily Brief - January 1, 2024

## 🎯 Top Priorities
1. [HIGH] Complete project proposal (due today at 5 PM)
2. [MED] Review pull requests (3 pending)
3. [LOW] Update documentation

## 📅 Today's Schedule
- 09:30 - Team standup
- 14:00 - Client meeting
- 16:00 - Focus session (2 hours)

## 💻 System Health
- CPU: 23% average
- Memory: 8.2 GB / 16 GB (51%)
- Disk: 145 GB free
- Updates: 2 pending (security)

## 📚 Research Context
- 3 papers added to reading list
- 2 citations pending verification
- Next: Review notes on distributed systems

## ⚠️ Attention Required
- System updates available (2 security patches)
- Low disk space warning (< 150 GB)
```

## Monitoring & Logs
- **Execution History**: n8n UI → Executions tab
- **Agent Logs**: `logs/daily_brief.log`
- **Output Archive**: `content/output/daily_brief_*.md`
- **Progress Log**: `logs/daily_briefs/progress.log`

## Configuration Files
- `config/daily_brief_settings.yaml` - Agent configuration
- `config/calendar_config.yaml` - Calendar integration settings
- `n8n/workflows/daily_brief_trigger.json` - Workflow definition
- `langflow/flows/daily_brief_specialist.json` - Agent graph

## Dependencies
- Calendar API access (Google Calendar/Outlook/iCal)
- Task management system (optional)
- Qdrant vector store for memory
- Email/notification service (optional)

## Troubleshooting

### Brief Not Generated
- Check cron trigger in n8n workflow
- Verify agent service is running
- Check Langflow logs for errors

### Missing Calendar Events
- Verify calendar API credentials in `.env`
- Check API rate limits
- Test calendar connection manually

### Incomplete Information
- Review data collection step logs
- Check individual service availability
- Adjust timeout settings if needed

### Delivery Failures
- Verify email/notification credentials
- Check network connectivity
- Ensure output directory is writable

## Customization

### Adjust Schedule
Edit cron expression in n8n workflow:
- Current: `0 9 * * *` (9 AM daily)
- Weekend skip: `0 9 * * 1-5` (9 AM weekdays)
- Multiple times: `0 9,15 * * *` (9 AM and 3 PM)

### Add Data Sources
1. Add new data collection node in n8n workflow
2. Update Langflow agent to process new data
3. Modify output template to include new section

### Change Output Format
Edit template in `config/daily_brief_template.md`:
- Markdown sections
- Priority ordering
- Style and formatting

## Metrics & SLA
- **Target Delivery**: 09:05 AM (± 5 minutes)
- **Success Rate**: > 98%
- **Data Completeness**: > 90%
- **Availability**: 99.9%
