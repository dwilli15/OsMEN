# Boot Hardening Workflow Runbook

## Overview
Automated system hardening on boot, monitoring for anomalies and applying baseline security policies.

## Trigger
- **Type**: Scheduled (Windows Task Scheduler webhook)
- **Frequency**: On system restart + Daily at midnight
- **n8n Workflow**: `boot_hardening_trigger.json`
- **Langflow Agent**: `boot_hardening_specialist.json`

## Workflow Steps

### 1. Trigger Detection
- n8n receives system restart event from Task Scheduler webhook
- Alternatively, scheduled daily trigger fires at 00:00

### 2. Data Collection
- **Process List**: PowerShell command `Get-Process` for running processes
- **Network Status**: `netstat -ano` for active connections
- **Startup Items**: Sysinternals Autoruns for boot programs
- **Baseline Rules**: Load firewall baseline from `config/firewall_baseline.yaml`

### 3. Agent Analysis
- Langflow OS Sentry agent receives collected data
- Evaluates deviations from baseline security policy
- Identifies suspicious processes or network connections
- Generates firewall rule diff recommendations

### 4. Action Execution
- n8n executes Simplewall CLI updates for approved changes
- Logs all changes to audit trail
- Generates human-readable security report

### 5. Human Approval Path
- If risky action detected (confidence < 80%), escalate to user
- Display reasoning and recommended actions
- Wait for user approval before executing
- Log decision (approved/rejected) with timestamp

## Success Criteria
- Baseline policy applied within 30 seconds of boot
- Human-readable report generated and logged
- Fails safe on error (no changes if uncertain)
- All actions audited in n8n execution history

## Failure Handling

### Process Collection Fails
- Log error with details
- Continue with partial data if available
- Alert user if critical data missing

### Agent Analysis Error
- Fail safe: do not apply any changes
- Generate error report with diagnostic info
- Send notification to user

### Simplewall Execution Fails
- Rollback any partial changes
- Log failure details
- Alert user with remediation steps

## Manual Execution
```bash
# Trigger manually from n8n UI
# 1. Open n8n at http://localhost:5678
# 2. Navigate to "Boot Hardening" workflow
# 3. Click "Execute Workflow" button

# Or via CLI:
curl -X POST http://localhost:5678/webhook/boot-hardening \
  -H "Content-Type: application/json" \
  -d '{"trigger": "manual"}'
```

## Monitoring & Logs
- **Execution History**: n8n UI → Executions tab
- **Agent Logs**: `logs/boot_hardening.log`
- **Audit Trail**: `logs/security_audit.log`
- **Error Logs**: n8n execution errors + `logs/errors.log`

## Rollback Procedure
1. Navigate to n8n execution history
2. Find the failed/incorrect execution
3. Review the changes that were applied
4. Manually revert firewall rules using Simplewall UI
5. Restore from backup if available: `config/firewall_backup_<timestamp>.yaml`

## Configuration Files
- `config/firewall_baseline.yaml` - Default security rules
- `config/boot_hardening_settings.yaml` - Agent configuration
- `n8n/workflows/boot_hardening_trigger.json` - Workflow definition
- `langflow/flows/boot_hardening_specialist.json` - Agent graph

## Dependencies
- Simplewall CLI installed and accessible
- Sysinternals Autoruns available
- PowerShell with admin privileges
- Windows Task Scheduler configured

## Troubleshooting

### Agent Not Triggering
- Check Task Scheduler for webhook configuration
- Verify n8n webhook URL is accessible
- Check n8n service status: `docker compose ps n8n`

### Firewall Changes Not Applying
- Verify Simplewall path in `.env`
- Check admin privileges for script execution
- Review Simplewall logs for errors

### False Positives
- Review agent confidence scores in execution logs
- Adjust threshold in `config/boot_hardening_settings.yaml`
- Add exceptions to baseline policy

## Metrics & SLA
- **Target Completion**: < 30 seconds
- **Success Rate**: > 95%
- **False Positive Rate**: < 10%
- **Availability**: 99.5% (excludes system downtime)
