# OsMEN Usage Guide

## Getting Started

After completing the setup (see [SETUP.md](SETUP.md)), you're ready to use OsMEN's agent capabilities.

## MVP Features

### 1. Boot Hardening

The boot hardening agent helps secure your system boot process and maintain system security.

#### Automatic Daily Check

The boot hardening check runs automatically every day at midnight. It:
- Verifies secure boot status
- Analyzes startup programs
- Checks for suspicious entries
- Provides hardening recommendations

#### Manual Execution

Run a manual boot hardening check:

```bash
# Using Python agent directly
python agents/boot_hardening/boot_hardening_agent.py

# Via Langflow UI
# 1. Open http://localhost:7860
# 2. Select "Boot Hardening Specialist" flow
# 3. Enter: "Perform security check"
# 4. Click Run

# Via n8n
# 1. Open http://localhost:5678
# 2. Find "Boot Hardening Trigger" workflow
# 3. Click "Execute Workflow"
```

#### Available Commands

- "Check boot integrity"
- "Analyze startup programs"
- "Review firewall rules"
- "Generate hardening report"

#### Example Output

```json
{
  "boot_integrity": {
    "status": "checked",
    "issues": ["Secure Boot is not enabled"],
    "recommendations": [
      "Enable Secure Boot in UEFI/BIOS",
      "Review startup programs with Autoruns"
    ]
  },
  "overall_status": "needs_attention"
}
```

### 2. Daily Brief

The daily brief agent provides a comprehensive morning briefing with system status and tasks.

#### Automatic Morning Brief

The daily brief is generated automatically every morning at 8:00 AM. It includes:
- System health status
- Scheduled tasks for the day
- Pending updates
- Resource usage trends
- Daily recommendations

#### Manual Generation

Generate a daily brief on demand:

```bash
# Using Python agent directly
python agents/daily_brief/daily_brief_agent.py

# Via Langflow UI
# 1. Open http://localhost:7860
# 2. Select "Daily Brief Specialist" flow
# 3. Enter: "Generate daily brief"
# 4. Click Run

# Via n8n
# 1. Open http://localhost:5678
# 2. Find "Daily Brief Trigger" workflow
# 3. Click "Execute Workflow"
```

#### Example Brief

```
Good morning!
Daily Brief for 2024-01-15 at 08:00

SYSTEM STATUS
-------------
CPU: Normal
Memory: Normal
Disk Space: Adequate
Network: Connected

SCHEDULED TASKS
---------------
- 09:00: System backup (maintenance)
- 14:00: Security scan (security)

PENDING UPDATES
---------------
System Updates: 0
Application Updates: 0
Security Patches: 0

RECOMMENDATIONS
---------------
- Review system logs for any anomalies
- Verify backup completion
- Check firewall rules
- Update antivirus definitions
```

### 3. Focus Guardrails

The focus guardrails agent helps maintain productivity by blocking distractions and managing focus sessions.

#### Automatic Monitoring

Focus monitoring runs every 15 minutes when enabled. It:
- Enforces focus session rules
- Blocks distracting websites
- Monitors application usage
- Sends focus reminders

#### Manual Focus Session

Start a focus session:

```bash
# Using Python agent directly
python agents/focus_guardrails/focus_guardrails_agent.py

# Via Langflow UI
# 1. Open http://localhost:7860
# 2. Select "Focus Guardrails Specialist" flow
# 3. Enter: "Start 25 minute focus session"
# 4. Click Run
```

#### Available Commands

- "Start focus session [duration]"
- "End focus session"
- "Block [website/app]"
- "Unblock [website/app]"
- "Show focus report"
- "Send focus reminder"

#### Blocked Sites (During Focus)

Default blocked sites during focus sessions:
- facebook.com
- twitter.com
- reddit.com
- youtube.com
- instagram.com

You can customize this list in the agent configuration.

#### Example Focus Session

```json
{
  "start_time": "2024-01-15T10:00:00",
  "duration_minutes": 25,
  "end_time": "2024-01-15T10:25:00",
  "status": "active",
  "blocked_sites": [
    "facebook.com",
    "twitter.com",
    "reddit.com"
  ]
}
```

## Advanced Usage

### Creating Custom Agents

1. **Design in Langflow**
   - Open Langflow UI
   - Create new flow
   - Add nodes: Input → LLM → Tools → Output
   - Configure Ollama connection
   - Add vector store retriever
   - Test and save

2. **Create n8n Workflow**
   - Open n8n UI
   - Create new workflow
   - Add trigger (schedule/webhook)
   - Add HTTP request to Langflow
   - Add post-processing logic
   - Activate workflow

3. **Implement Python Agent**
   ```python
   # agents/my_agent/my_agent.py
   class MyAgent:
       def __init__(self):
           pass
       
       def perform_task(self):
           # Your agent logic
           pass
   ```

### Integrating with Tools

#### Using Simplewall

```python
from tools.simplewall.simplewall_integration import SimplewallIntegration

simplewall = SimplewallIntegration()
result = simplewall.block_domain('example.com')
```

#### Using Sysinternals

```python
from tools.sysinternals.sysinternals_integration import SysinternalsIntegration

sysinternals = SysinternalsIntegration()
analysis = sysinternals.analyze_system_health()
```

#### Using FFmpeg

```python
from tools.ffmpeg.ffmpeg_integration import FFmpegIntegration

ffmpeg = FFmpegIntegration()
info = ffmpeg.get_media_info('video.mp4')
```

### Customizing Schedules

Edit n8n workflows to change schedules:

1. Open n8n UI
2. Select workflow
3. Click on Schedule Trigger node
4. Modify cron expression:
   - `0 8 * * *` - Daily at 8 AM
   - `*/15 * * * *` - Every 15 minutes
   - `0 */2 * * *` - Every 2 hours
   - `0 0 * * 1` - Every Monday at midnight

### Using Different LLM Models

Configure Ollama models in Langflow:

1. Pull new model:
   ```bash
   docker exec -it osmen-ollama ollama pull mistral
   ```

2. Update Langflow flow:
   - Open flow in Langflow UI
   - Select ChatOllama node
   - Change model to "mistral"
   - Save flow

### Memory Management

#### Storing in Qdrant

```python
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)
client.upsert(
    collection_name="osmen_memory",
    points=[{
        "id": "unique_id",
        "vector": embedding_vector,
        "payload": {"text": "content", "timestamp": "2024-01-15"}
    }]
)
```

#### Querying Memory

```python
results = client.search(
    collection_name="osmen_memory",
    query_vector=query_embedding,
    limit=5
)
```

## Configuration

### Environment Variables

Edit `.env` file to customize:

```bash
# Enable/disable agents
BOOT_HARDENING_ENABLED=true
DAILY_BRIEF_ENABLED=true
FOCUS_GUARDRAILS_ENABLED=true

# LLM settings
OLLAMA_MODEL=llama2

# Tool paths
SYSINTERNALS_PATH=C:\Tools\Sysinternals
SIMPLEWALL_PATH=C:\Program Files\simplewall
FFMPEG_PATH=C:\Tools\ffmpeg\bin
```

Apply changes:
```bash
docker-compose down
docker-compose up -d
```

### Langflow Configuration

Configuration files in `langflow/config/`:
- Flow templates
- Component settings
- API keys (if needed)

### n8n Configuration

Workflows stored in `n8n/workflows/`:
- Import/export workflows as JSON
- Share workflows with team
- Version control workflows

## Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f langflow
docker-compose logs -f n8n
docker-compose logs -f ollama

# Last 100 lines
docker-compose logs --tail=100 langflow
```

### Check Service Status

```bash
docker-compose ps
```

### Monitor Resource Usage

```bash
docker stats
```

### n8n Execution History

1. Open n8n UI
2. Click "Executions" in sidebar
3. View workflow execution history
4. Click on execution to see details

## Troubleshooting

### Agent Not Responding

1. Check service status:
   ```bash
   docker-compose ps
   ```

2. Check logs:
   ```bash
   docker-compose logs langflow
   ```

3. Restart service:
   ```bash
   docker-compose restart langflow
   ```

### LLM Inference Slow

1. Check GPU usage:
   ```bash
   nvidia-smi
   ```

2. Use faster model:
   ```bash
   docker exec -it osmen-ollama ollama pull mistral
   ```

3. Reduce temperature in Langflow flows

### Workflow Not Triggering

1. Check workflow is active in n8n UI
2. Verify schedule configuration
3. Check n8n logs:
   ```bash
   docker-compose logs n8n
   ```

### Memory Issues

1. Clear Qdrant collections:
   ```bash
   # Via API
   curl -X DELETE http://localhost:6333/collections/osmen_memory
   ```

2. Restart Qdrant:
   ```bash
   docker-compose restart qdrant
   ```

## Best Practices

1. **Regular Backups**
   - Backup PostgreSQL databases weekly
   - Export n8n workflows regularly
   - Save Langflow flows to git

2. **Security**
   - Change default passwords
   - Keep tools updated
   - Review firewall rules regularly

3. **Performance**
   - Monitor resource usage
   - Clean up old logs
   - Optimize Qdrant collections

4. **Customization**
   - Start with MVP features
   - Add agents incrementally
   - Test thoroughly before automation

## Next Steps

- Explore [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- Add custom agents for your needs
- Join the community and share workflows
- Contribute improvements back to the project
