# Productivity Monitor Documentation

## Overview

The Productivity Monitor is a comprehensive time and focus tracking system that helps monitor work sessions, application usage, and productivity trends over time.

## Features

### Focus Session Tracking
- **Pomodoro Sessions**: 25-minute focused work periods
- **Custom Sessions**: Flexible duration and types
- **Productivity Scoring**: Rate each session (1-10)
- **Distraction Tracking**: Count interruptions
- **Session Notes**: Add context to each session

### Application Usage Logging
- Track time spent in applications
- Categorize as productive/unproductive
- Monitor usage patterns

### Metrics & Analytics
- **Daily Summaries**: Focus time, sessions, scores
- **Weekly Trends**: Aggregate data over 7 days
- **Energy Tracking**: Optional energy level logging
- **Historical Data**: SQLite database for long-term tracking

## Database Schema

### Tables

#### focus_sessions
- `id`: Primary key
- `start_time`: ISO timestamp
- `end_time`: ISO timestamp
- `duration_minutes`: Calculated duration
- `session_type`: pomodoro, deep_work, etc.
- `productivity_score`: 1-10 rating
- `distractions_count`: Number of interruptions
- `completed`: Boolean flag
- `notes`: Text notes

#### app_usage
- `id`: Primary key
- `timestamp`: ISO timestamp
- `application`: App name
- `category`: work, communication, entertainment, etc.
- `duration_seconds`: Time spent
- `is_productive`: Boolean flag

#### daily_metrics
- `id`: Primary key
- `date`: Unique date (YYYY-MM-DD)
- `focus_time_minutes`: Total focus time
- `productive_time_minutes`: Total productive time
- `distraction_time_minutes`: Total distraction time
- `sessions_completed`: Number of sessions
- `average_productivity_score`: Mean score
- `energy_level`: Optional 1-10 rating
- `notes`: Daily notes

## Usage

### Direct Python API

```python
from tools.productivity.productivity_monitor import ProductivityMonitor

monitor = ProductivityMonitor()

# Start a focus session
result = monitor.start_focus_session("pomodoro", 25)
session_id = result["session_id"]

# End the session
result = monitor.end_focus_session(
    session_id=session_id,
    productivity_score=8,
    distractions=2,
    notes="Worked on innovation agent"
)

# Get daily summary
summary = monitor.get_daily_summary()
print(f"Completed {summary['sessions_completed']} sessions today")
print(f"Total focus time: {summary['focus_time_minutes']} minutes")
print(f"Average score: {summary['average_productivity_score']}/10")

# Get weekly trends
trends = monitor.get_weekly_trends()
print(f"This week: {trends['total_sessions']} sessions")
print(f"Total focus: {trends['total_focus_time_minutes']} minutes")
```

### Via MCP Server

```python
from gateway.mcp_server import MCPServer, ToolCallRequest

server = MCPServer()

# Start session
request = ToolCallRequest(
    tool='productivity_start_session',
    parameters={'session_type': 'deep_work', 'duration': 45}
)
response = server.call_tool(request)
session_id = response.result['session_id']

# End session
request = ToolCallRequest(
    tool='productivity_end_session',
    parameters={
        'session_id': session_id,
        'productivity_score': 9,
        'distractions': 0
    }
)
response = server.call_tool(request)

# Daily summary
request = ToolCallRequest(
    tool='productivity_daily_summary',
    parameters={}
)
response = server.call_tool(request)

# Weekly trends
request = ToolCallRequest(
    tool='productivity_weekly_trends',
    parameters={}
)
response = server.call_tool(request)
```

### Via Focus Guardrails Agent

The Productivity Monitor integrates with the Focus Guardrails Agent:

```python
# Focus Guardrails Agent automatically:
# 1. Starts session when you begin focused work
# 2. Tracks distractions during session
# 3. Ends session and logs metrics
# 4. Updates daily/weekly stats
```

## Session Types

### Pomodoro (25 minutes)
Standard focused work session with 5-minute break.

### Deep Work (45-90 minutes)
Extended focused session for complex tasks.

### Short Task (15 minutes)
Quick focused burst for small tasks.

### Meeting (30-60 minutes)
Collaborative work session.

### Custom
Define your own session type and duration.

## Productivity Scoring Guide

Rate sessions on 1-10 scale:

- **1-3**: Poor focus, many distractions, little accomplished
- **4-6**: Moderate focus, some distractions, decent progress
- **7-8**: Good focus, few distractions, solid progress
- **9-10**: Excellent focus, no distractions, great progress

## Application Categories

### Productive
- IDEs (VSCode, PyCharm)
- Documentation (browsers on docs sites)
- Communication (for work)
- Design tools

### Neutral
- File management
- System utilities
- Email (depends on context)

### Unproductive
- Social media
- Entertainment
- Games
- Non-work browsing

## Daily Summary

Example output:
```json
{
  "date": "2025-11-11",
  "sessions_completed": 8,
  "focus_time_minutes": 200,
  "average_productivity_score": 7.5,
  "app_usage_by_category": {
    "development": 180,
    "communication": 30,
    "documentation": 45
  }
}
```

## Weekly Trends

Example output:
```json
{
  "period": "last_7_days",
  "start_date": "2025-11-04",
  "end_date": "2025-11-11",
  "total_sessions": 42,
  "total_focus_time_minutes": 1050,
  "average_productivity_score": 7.8,
  "daily_breakdown": [
    {"date": "2025-11-04", "sessions": 6, "focus_time": 150, "avg_score": 7.5},
    {"date": "2025-11-05", "sessions": 7, "focus_time": 175, "avg_score": 8.0},
    ...
  ]
}
```

## Integration with Other Tools

### Langflow
- Trigger workflows based on productivity metrics
- Automate actions after low productivity days
- Send reminders for focus sessions

### n8n
- Export data to Google Sheets
- Send daily summary emails
- Integrate with calendar for blocking focus time
- Post updates to Slack/Discord

### Obsidian
- Create daily notes with productivity stats
- Link to session notes
- Track trends in knowledge vault

## Analytics & Insights

### Patterns to Monitor
- Best productivity time of day
- Optimal session length
- Distraction trends
- Energy level correlation with productivity

### Goals & Tracking
- Daily focus time target (e.g., 240 minutes = 4 hours)
- Session completion rate
- Average productivity score target (e.g., ≥7.5)
- Distraction reduction over time

## Data Management

### Database Location
`tools/productivity/productivity.db`

### Backup
```bash
# Backup database
cp tools/productivity/productivity.db backups/productivity_$(date +%Y%m%d).db

# Or use SQLite command
sqlite3 tools/productivity/productivity.db ".backup backups/productivity.db"
```

### Export Data
```bash
# Export to CSV
sqlite3 -header -csv tools/productivity/productivity.db \
  "SELECT * FROM focus_sessions" > sessions.csv

sqlite3 -header -csv tools/productivity/productivity.db \
  "SELECT * FROM daily_metrics" > daily_metrics.csv
```

### Privacy
- All data stored locally
- No cloud sync (unless explicitly configured)
- Database can be encrypted
- Can be excluded from backups via `.gitignore`

## Testing

Run tests:
```bash
# Direct test
python tools/productivity/productivity_monitor.py

# Integration test
python test_mcp_integration.py
```

## Troubleshooting

### Database locked
- Close other connections to database
- Check for long-running queries
- Restart monitoring service

### Missing sessions
- Verify session was ended (completed=True)
- Check timestamp filtering
- Review database directly with sqlite3

### Inaccurate metrics
- Verify scoring consistency
- Check for double-counting
- Review app categorization

## Future Enhancements

- [ ] Real-time app monitoring (active window tracking)
- [ ] Automatic categorization using ML
- [ ] Web dashboard for visualizations
- [ ] Mobile app for tracking on-the-go
- [ ] Integration with wearables (heart rate, activity)
- [ ] Pomodoro timer with notifications
- [ ] Smart break recommendations
- [ ] Team productivity comparisons (opt-in)

## Support

For issues or questions:
- Review test files for examples
- Check database schema
- Examine log files
- Open GitHub issue for bugs

---

**Last Updated:** 2025-11-11
**Version:** 1.0.0
