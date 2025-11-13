# OsMEN Common Scenarios & Use Cases

This guide shows you how to accomplish common tasks with OsMEN.

## Table of Contents

1. [Daily Operations](#daily-operations)
2. [Security Monitoring](#security-monitoring)
3. [Productivity Management](#productivity-management)
4. [Knowledge Management](#knowledge-management)
5. [Custom Workflows](#custom-workflows)
6. [Troubleshooting](#troubleshooting)

---

## Daily Operations

### Get Your Morning Brief

**Scenario**: Start your day with a comprehensive status report.

```bash
# Run the Daily Brief agent
python3 agents/daily_brief/daily_brief_agent.py
```

**Expected Output**:
- System health status
- Today's scheduled tasks
- Pending notifications
- Resource usage summary

**Automate it**:
1. Open n8n: http://localhost:5678
2. Import `n8n/workflows/daily_brief_trigger.json`
3. Set schedule to 8:00 AM daily
4. Activate workflow

### Check System Security

**Scenario**: Verify your system security posture.

```bash
# Run Boot Hardening agent
python3 agents/boot_hardening/boot_hardening_agent.py
```

**What it checks**:
- Startup programs
- Boot integrity
- Firewall configuration
- Security issues

**Review results**:
- Check `logs/boot_hardening.log`
- Review any flagged issues
- Follow recommendations

---

## Security Monitoring

### Set Up Continuous Security Monitoring

**Scenario**: Monitor security 24/7 with automated checks.

**Steps**:

1. **Configure Boot Hardening Schedule**:
   ```bash
   # Edit the n8n workflow
   # Set to run every 6 hours or daily at midnight
   ```

2. **Set Up Alerts**:
   - Configure n8n to send notifications
   - Email, Slack, Discord, etc.
   - Only on security issues detected

3. **Review Historical Data**:
   - Check Qdrant for stored scan results
   - Track trends over time
   - Identify recurring issues

### Firewall Management (Windows)

**Scenario**: Manage Windows Firewall via Simplewall.

**Prerequisites**:
- Simplewall installed: https://www.henrypp.org/product/simplewall
- Path configured in `.env`: `SIMPLEWALL_PATH=C:\\Program Files\\simplewall`

**Usage**:

```python
from tools.simplewall import SimplewallIntegration

# Initialize
simplewall = SimplewallIntegration()

# Block an application
simplewall.block_application("chrome.exe")

# Block a domain
simplewall.block_domain("facebook.com")

# Allow an application
simplewall.allow_application("firefox.exe")

# Get current rules
rules = simplewall.get_rules()
```

### Analyze Startup Programs (Windows)

**Scenario**: Review what runs on system startup.

**Prerequisites**:
- Sysinternals Suite: https://docs.microsoft.com/sysinternals
- Path in `.env`: `SYSINTERNALS_PATH=C:\\Tools\\Sysinternals`

**Usage**:

```python
from tools.sysinternals import SysinternalsIntegration

# Initialize
sysinternals = SysinternalsIntegration()

# Get startup programs (using Autoruns)
startup_items = sysinternals.get_startup_programs()

# Check for suspicious items
for item in startup_items:
    if item.get('verified') is False:
        print(f"⚠️  Unverified: {item['name']}")
```

---

## Productivity Management

### Start a Focus Session

**Scenario**: Block distractions for deep work.

```bash
# Start a 25-minute Pomodoro session
python3 agents/focus_guardrails/focus_guardrails_agent.py
```

**Customize**:

Edit `config/focus_guardrails_settings.yaml`:
```yaml
focus_duration: 50  # minutes
break_duration: 10  # minutes
blocked_sites:
  - facebook.com
  - twitter.com
  - reddit.com
  - youtube.com
```

### Schedule Focus Time

**Scenario**: Automatically block distractions during work hours.

1. Open n8n: http://localhost:5678
2. Import `n8n/workflows/focus_guardrails_monitor.json`
3. Configure schedule:
   - Monday-Friday, 9 AM - 5 PM
   - Block distracting sites
   - Send break reminders
4. Activate workflow

### Track Productivity

**Scenario**: Monitor how you spend your time.

The Focus Guardrails agent logs all activity:
- Application usage
- Website visits
- Focus session duration
- Break patterns

**View data**:
```bash
# Check logs
cat logs/focus_guardrails.log

# Or query Qdrant for historical data
```

---

## Knowledge Management

### Set Up Obsidian Integration

**Scenario**: Connect your Obsidian vault to OsMEN.

**Steps**:

1. **Configure Vault Path**:
   ```bash
   # In .env file
   OBSIDIAN_VAULT_PATH=/path/to/your/vault
   ```

2. **Restart MCP Server**:
   ```bash
   docker-compose restart mcp-server
   ```

3. **Test Connection**:
   ```bash
   # Check MCP server can access vault
   curl http://localhost:8081/tools
   ```

### Create Notes from Agent Output

**Scenario**: Automatically save agent results to Obsidian.

**Using n8n workflow**:

1. Create workflow in n8n
2. Add trigger (schedule, webhook, etc.)
3. Run agent (HTTP request node)
4. Parse agent output
5. Create Obsidian note via MCP

**Example workflow**:
```
Schedule (8 AM) → Daily Brief Agent → Parse JSON → Create Note in Obsidian
```

### Search Knowledge Base

**Scenario**: Query your notes using AI.

```python
from integrations.knowledge import ObsidianSync

# Initialize
obsidian = ObsidianSync(vault_path="/path/to/vault")

# Search notes
results = obsidian.search("meeting notes project X")

# Get note content
note = obsidian.get_note("2024-01-15.md")

# Find backlinks
backlinks = obsidian.get_backlinks("Project X")
```

---

## Custom Workflows

### Create a Custom Agent

**Scenario**: Build your own specialized agent.

1. **Create Agent Directory**:
   ```bash
   mkdir -p agents/my_agent
   ```

2. **Create Agent Script**:
   ```python
   # agents/my_agent/my_agent.py
   from datetime import datetime
   
   class MyAgent:
       def __init__(self):
           self.name = "My Custom Agent"
       
       def run(self):
           return {
               "timestamp": datetime.now().isoformat(),
               "status": "success",
               "results": {
                   # Your agent logic here
               }
           }
   
   if __name__ == "__main__":
       agent = MyAgent()
       print(agent.run())
   ```

3. **Create Langflow Flow**:
   - Open Langflow: http://localhost:7860
   - Design your flow visually
   - Export to `langflow/flows/my_agent.json`

4. **Create n8n Workflow**:
   - Open n8n: http://localhost:5678
   - Create trigger and execution logic
   - Export to `n8n/workflows/my_agent.json`

### Integrate External API

**Scenario**: Connect OsMEN to external service.

**Example - Weather API**:

```python
# integrations/weather/weather_api.py
import requests
import os

class WeatherIntegration:
    def __init__(self):
        self.api_key = os.getenv('WEATHER_API_KEY')
        self.base_url = "https://api.weatherapi.com/v1"
    
    def get_current(self, location: str):
        response = requests.get(
            f"{self.base_url}/current.json",
            params={
                "key": self.api_key,
                "q": location
            }
        )
        return response.json()
```

**Add to .env**:
```bash
WEATHER_API_KEY=your_api_key_here
```

**Use in agent**:
```python
from integrations.weather import WeatherIntegration

weather = WeatherIntegration()
current = weather.get_current("New York")
```

### Schedule Complex Workflows

**Scenario**: Run multi-step automation daily.

**Example - Morning Routine**:

1. Get weather forecast
2. Run security scan
3. Generate daily brief
4. Check calendar
5. Create Obsidian daily note
6. Send notification

**In n8n**:
- Create workflow with 6 HTTP request nodes
- Chain them together
- Add error handling
- Schedule for 7 AM daily

---

## Troubleshooting

### Agent Not Running

**Symptoms**: Agent returns errors or doesn't execute.

**Checks**:
1. Environment configured: `cat .env | grep -i enabled`
2. Dependencies installed: `python3 -m pip list`
3. LLM provider accessible: `python3 scripts/automation/test_llm_providers.py`
4. Logs for errors: `cat logs/osmen.log`

**Fix**:
```bash
# Reinstall dependencies
python3 -m pip install --user -r requirements.txt

# Check agent directly
python3 agents/daily_brief/daily_brief_agent.py

# Verify configuration
python3 scripts/automation/validate_security.py
```

### Services Not Starting

**Symptoms**: `docker-compose up` fails.

**Checks**:
1. Docker running: `docker ps`
2. Ports available: `lsof -i :5678` (Mac/Linux)
3. Disk space: `df -h`
4. Logs: `docker-compose logs`

**Fix**:
```bash
# Stop all containers
docker-compose down

# Remove volumes (careful - deletes data!)
docker-compose down -v

# Restart Docker
# Windows/Mac: Restart Docker Desktop
# Linux: sudo systemctl restart docker

# Start fresh
docker-compose up -d
```

### LLM Not Responding

**Symptoms**: Agents timeout or return empty responses.

**For OpenAI**:
```bash
# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**For LM Studio**:
- Check it's running on port 1234
- Model loaded in LM Studio
- Server started in LM Studio

**For Ollama**:
```bash
# Check if running
docker exec -it osmen-ollama ollama list

# Pull model if needed
docker exec -it osmen-ollama ollama pull llama2
```

### Workflow Execution Failed

**Symptoms**: n8n workflow shows error status.

**Debug**:
1. Open n8n: http://localhost:5678
2. Click on failed execution
3. Review error message
4. Check each node's output
5. Test individual nodes

**Common issues**:
- Invalid credentials
- Network timeout
- Incorrect data format
- Missing environment variables

---

## Advanced Scenarios

### Multi-Agent Coordination

**Scenario**: Have agents work together on complex tasks.

**Example - Project Analysis**:
1. Research Agent: Gather information
2. Knowledge Agent: Store in Obsidian
3. Daily Brief: Include in morning report
4. Focus Agent: Block time for work

**Implementation**:
- Use n8n to orchestrate
- Share data via Qdrant vector store
- Coordinate via PostgreSQL database

### Custom Memory System

**Scenario**: Build agent memory across sessions.

**Using Qdrant**:

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Connect to Qdrant
client = QdrantClient(host="localhost", port=6333)

# Create collection for memories
client.create_collection(
    collection_name="agent_memory",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
)

# Store memory
client.upsert(
    collection_name="agent_memory",
    points=[
        PointStruct(
            id=1,
            vector=[...],  # embedding from LLM
            payload={
                "text": "User prefers morning meetings",
                "timestamp": "2024-01-15T10:00:00",
                "source": "daily_brief_agent"
            }
        )
    ]
)

# Retrieve relevant memories
results = client.search(
    collection_name="agent_memory",
    query_vector=[...],  # query embedding
    limit=5
)
```

---

## Need More Help?

- **Documentation**: `docs/` directory
- **Runbooks**: `docs/runbooks/` for specific agents
- **Troubleshooting**: `docs/TROUBLESHOOTING.md`
- **Issues**: https://github.com/dwilli15/OsMEN/issues
- **Discussions**: https://github.com/dwilli15/OsMEN/discussions
