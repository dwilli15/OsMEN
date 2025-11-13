# Focus Guardrails Workflow Runbook

## Overview
Automated productivity management enforcing focus sessions, timeboxing, and distraction blocking.

## Trigger
- **Type**: Event-driven + Scheduled
- **Frequency**: Active window monitoring (every 15 minutes) + Manual triggers
- **n8n Workflow**: `focus_guardrails_monitor.json`
- **Langflow Agent**: `focus_guardrails_specialist.json`

## Workflow Steps

### 1. Monitoring Trigger
- n8n monitors active window changes via PowerShell/AutoHotkey
- Scheduled check every 15 minutes
- Manual trigger via button/webhook for immediate focus session

### 2. Context Collection
- **Active Application**: Get current foreground window
- **Calendar Context**: Check for scheduled focus blocks
- **Focus Settings**: Load user preferences and whitelist
- **Pomodoro State**: Query current streak from vector memory
- **Time of Day**: Determine if in focus hours

### 3. Agent Evaluation
- Langflow Focus Steward receives context data
- Validates current app against whitelist
- Cross-references Pomodoro history for tailored nudges
- Determines appropriate action (allow/block/nudge)

### 4. Action Execution
- **Network Control**: Toggle Simplewall profiles for blocking
- **Timer Management**: Start/stop Pomodoro timer
- **Notifications**: Send focus reminders or alerts
- **Logging**: Record decisions and app usage patterns

### 5. Override Handling
- If user requests override, show reasoning dialog
- Log override request with justification
- Allow temporary exception (configurable duration)
- Update learning model with feedback

## Success Criteria
- Blocks flagged apps during active focus sessions
- Prompts user before applying overrides
- Logs all decisions for review
- Maintains >90% adherence rate

## Failure Handling

### Window Detection Fails
- Log error and continue monitoring
- Use last known state as fallback
- Alert user if monitoring unavailable for >5 minutes

### Agent Decision Error
- Default to allowing (fail open for usability)
- Log error for investigation
- Notify user of degraded mode

### Simplewall Control Fails
- Alert user immediately
- Manual intervention required
- Log failure and attempted recovery

## Manual Execution

### Start Focus Session
```bash
# Via n8n webhook:
curl -X POST http://localhost:5678/webhook/focus-start \
  -H "Content-Type: application/json" \
  -d '{
    "duration": 25,
    "type": "pomodoro",
    "strict_mode": true
  }'
```

### Stop Focus Session
```bash
curl -X POST http://localhost:5678/webhook/focus-stop \
  -H "Content-Type: application/json"
```

### Request Override
```bash
curl -X POST http://localhost:5678/webhook/focus-override \
  -H "Content-Type: application/json" \
  -d '{
    "app": "Chrome",
    "reason": "Research required",
    "duration": 15
  }'
```

## Focus Session Types

### Pomodoro (25 min work / 5 min break)
- Strict blocking enabled
- Automatic break reminders
- Tracks streak count

### Deep Work (90-120 min)
- Flexible blocking rules
- Calendar integration
- Scheduled breaks

### Light Focus (30-60 min)
- Gentle nudges only
- No hard blocks
- Notification management

## Configuration

### Whitelist Apps
Edit `config/focus_whitelist.yaml`:
```yaml
allowed_apps:
  - "Visual Studio Code"
  - "Terminal"
  - "Obsidian"
  - "Notion"

blocked_apps:
  - "Chrome" # unless research mode
  - "Discord"
  - "Slack"
  - "Twitter"

conditional_apps:
  Chrome:
    - allowed_domains: ["docs.google.com", "github.com"]
    - blocked_domains: ["youtube.com", "reddit.com"]
```

### Focus Hours
Edit `config/focus_schedule.yaml`:
```yaml
focus_hours:
  weekdays:
    morning: "09:00-12:00"
    afternoon: "14:00-17:00"
  weekends:
    enabled: false

auto_start: true
break_reminders: true
```

## Monitoring & Logs
- **Execution History**: n8n UI → Executions tab
- **Agent Logs**: `logs/focus_guardrails.log`
- **Usage Analytics**: `logs/app_usage_stats.json`
- **Override Log**: `logs/focus_overrides.log`

## Analytics Dashboard

### Daily Summary
```
Focus Time: 4.5 hours
Pomodoros Completed: 9/10
Distractions Blocked: 14
Override Requests: 2 (approved)
Adherence Rate: 92%
```

### Weekly Trends
- Focus time by day of week
- Most productive hours
- Common distraction patterns
- Override frequency

## Configuration Files
- `config/focus_whitelist.yaml` - App allow/block lists
- `config/focus_schedule.yaml` - Focus hours and preferences
- `config/pomodoro_settings.yaml` - Timer configuration
- `n8n/workflows/focus_guardrails_monitor.json` - Workflow
- `langflow/flows/focus_guardrails_specialist.json` - Agent graph

## Dependencies
- PowerShell or AutoHotkey for window monitoring
- Simplewall for network control
- Pomodoro timer (built-in or external)
- Notification system (Windows notifications)

## Troubleshooting

### Monitoring Not Working
- Check PowerShell execution policy
- Verify AutoHotkey script is running
- Test window detection: `Get-Process | Where-Object {$_.MainWindowTitle -ne ""}`

### Blocks Not Applying
- Verify Simplewall path in `.env`
- Check firewall profiles are configured
- Test manual Simplewall CLI commands

### Too Many False Blocks
- Adjust whitelist in `config/focus_whitelist.yaml`
- Lower strictness level in settings
- Add more allowed domains for conditional apps

### Not Enough Enforcement
- Enable strict mode in focus settings
- Reduce override approval duration
- Add more apps to block list

## Best Practices

### 1. Gradual Adoption
- Start with gentle nudges only
- Add blocks gradually as you build habit
- Review analytics weekly

### 2. Whitelist Maintenance
- Update allowed apps as needs change
- Add research domains to conditional list
- Remove unused apps from block list

### 3. Scheduled Focus
- Block calendar time for deep work
- Align with natural energy peaks
- Include buffer time for transitions

### 4. Override Discipline
- Always provide reason for overrides
- Review override log weekly
- Identify patterns and adjust rules

## Metrics & SLA
- **Monitoring Uptime**: > 99%
- **Detection Latency**: < 5 seconds
- **False Positive Rate**: < 5%
- **User Satisfaction**: Regular review of override requests
