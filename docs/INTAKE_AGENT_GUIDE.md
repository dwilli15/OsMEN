# Natural Language Agent Team Creation Guide

## How n8n and Langflow Work Together

OsMEN uses a two-layer architecture where **n8n** and **Langflow** work together seamlessly:

### The Two Layers

#### 1. **Langflow** - The Reasoning Layer
- **Purpose**: Provides LLM-powered reasoning and decision-making
- **Function**: Houses the AI agents that process requests and make decisions
- **Technology**: Visual flow builder with LLM integration (Ollama, OpenAI, etc.)
- **Location**: http://localhost:7860

#### 2. **n8n** - The Orchestration Layer
- **Purpose**: Manages triggers, scheduling, and workflow automation
- **Function**: Calls Langflow agents at the right time and coordinates workflows
- **Technology**: Workflow automation with HTTP, cron, webhooks
- **Location**: http://localhost:5678

### Communication Flow

```
┌─────────────────────────────────────────────────────────────┐
│  TRIGGER LAYER (n8n)                                         │
│  - Cron schedules (e.g., daily at 8 AM)                     │
│  - Webhooks (e.g., when file uploaded)                      │
│  - Manual triggers (e.g., button click)                     │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       │ HTTP POST Request
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  REASONING LAYER (Langflow)                                  │
│  - Coordinator Agent (routes tasks)                         │
│  - Specialist Agents (execute tasks)                        │
│  - LLM Integration (Ollama/OpenAI)                          │
│  - Vector Memory (Qdrant)                                   │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       │ Agent Response
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  RESULTS (back to n8n)                                       │
│  - Log execution                                             │
│  - Send notifications                                        │
│  - Trigger next workflow step                               │
└─────────────────────────────────────────────────────────────┘
```

### Example: Daily Brief Agent

**n8n Workflow** (`daily_brief_trigger.json`):
1. Cron trigger activates at 8:00 AM daily
2. Check if `DAILY_BRIEF_ENABLED=true`
3. Make HTTP POST to `http://langflow:7860/api/v1/run/daily_brief_specialist`
4. Receive agent response
5. Format and log the daily brief

**Langflow Flow** (`daily_brief_specialist.json`):
1. Receive request from n8n
2. Use LLM (Ollama) to generate brief
3. Retrieve context from Qdrant vector memory
4. Return structured response to n8n

---

## Natural Language Intake Agent

The Intake Agent is a **meta-agent** that creates other agents based on natural language conversations.

### What Makes It Special

1. **No-Code Agent Creation**: Users describe what they need in plain English
2. **Conversational Interface**: The agent asks clarifying questions
3. **Custom Team Design**: Creates tailored agent teams, not cookie-cutter solutions
4. **Automatic Deployment**: Generates Langflow flows and n8n workflows
5. **Coordination**: Ensures agents work together without conflicts

### How It Works

```
User                    Intake Agent                  System
│                            │                           │
│  "I need help with         │                           │
│   security monitoring"     │                           │
├───────────────────────────>│                           │
│                            │ Analyzes requirements     │
│                            │ Asks clarifying questions │
│                            │                           │
│  "I want continuous        │                           │
│   monitoring with alerts"  │                           │
├───────────────────────────>│                           │
│                            │ Designs agent team:       │
│                            │ 1. Security Coordinator   │
│                            │ 2. Security Monitor       │
│                            │ 3. Continuous Monitor     │
│                            │ 4. Alert Specialist       │
│                            │                           │
│  "Yes, create them"        │                           │
├───────────────────────────>│                           │
│                            │ Creates Langflow flows    │
│                            ├──────────────────────────>│
│                            │ Creates n8n workflows     │
│                            ├──────────────────────────>│
│                            │ Deploys agents            │
│                            ├──────────────────────────>│
│                            │                           │
│  "✅ Team created!"        │                           │
│<───────────────────────────┤                           │
```

### Using the Intake Agent

#### Step 1: Access the UI

Visit: **http://localhost:8000/intake-agent**

You'll see a chat interface where you can talk to the intake agent.

#### Step 2: Describe Your Needs

Tell the agent what you need in natural language:

**Examples:**
- "I need help monitoring my system security"
- "I want to automate my daily workflow"
- "Help me manage my research projects"
- "I need content creation assistance"

#### Step 3: Answer Questions

The agent will ask clarifying questions:
- What's your main goal?
- How often do you need this done?
- What level of automation do you want?

Answer naturally - the agent understands conversational responses.

#### Step 4: Review the Proposed Team

The agent will design a custom team and show you:
- Agent names and purposes
- Capabilities of each agent
- How they'll work together

#### Step 5: Approve or Modify

- Say "yes" or "looks good" to create the team
- Request changes: "Add an agent for X" or "I don't need Y"

#### Step 6: Agents Are Created!

The intake agent:
1. Creates Langflow flows for each agent
2. Creates n8n workflows for triggers
3. Sets up coordination between agents
4. Deploys everything automatically

Your custom team is now running!

---

## Agent Coordination

The intake agent ensures your team works together smoothly:

### 1. **Task Routing**
A coordinator agent routes requests to the right specialist.

### 2. **Conflict Avoidance**
Agents are assigned distinct responsibilities - no overlap.

### 3. **Communication**
Agents share context through Qdrant vector memory.

### 4. **Redundancy Elimination**
Similar capabilities are consolidated into single agents.

### Example Team Architecture

For a security monitoring request:

```
Security Coordinator (Langflow)
├─> Security Monitor Specialist (Langflow)
│   └─> Runs via n8n hourly trigger
│   └─> Checks system vulnerabilities
│   └─> Stores findings in Qdrant
│
├─> Alert Specialist (Langflow)
│   └─> Monitors Qdrant for new threats
│   └─> Sends notifications
│
└─> Reporting Agent (Langflow)
    └─> Daily summary n8n trigger
    └─> Aggregates security events
    └─> Generates report
```

---

## Customization Examples

### Example 1: Research Team

**Request**: "I need help with academic research"

**Agent Creates:**
- Research Coordinator
- Literature Review Specialist
- Data Analysis Specialist
- Citation Manager
- Summary Generator

**n8n Workflows:**
- Daily literature search (cron)
- On-demand deep-dive research (webhook)
- Weekly summary compilation (cron)

### Example 2: Content Creation Team

**Request**: "Help me create and manage social media content"

**Agent Creates:**
- Content Coordinator
- Idea Generator Specialist
- Content Writer Specialist
- Image Creator Specialist
- Scheduling Agent

**n8n Workflows:**
- Daily content generation (cron)
- Schedule and post content (cron)
- Engagement monitoring (hourly)

### Example 3: Productivity Team

**Request**: "Automate my daily planning and task management"

**Agent Creates:**
- Productivity Coordinator
- Calendar Manager
- Task Prioritizer
- Focus Time Manager
- Progress Tracker

**n8n Workflows:**
- Morning planning session (8 AM)
- Task review and reprioritization (hourly)
- End-of-day summary (6 PM)

---

## How It Extends Existing Agents

The intake agent **doesn't discard** the existing Boot Hardening, Daily Brief, and Focus Guardrails agents.

Instead, it:

1. **Adds to them**: Creates new specialized agents alongside existing ones
2. **Coordinates with them**: New teams can include existing agents
3. **Follows the same pattern**: Uses Langflow + n8n architecture
4. **Shares resources**: All agents use the same Qdrant memory, Ollama LLM, etc.

Think of it as **expanding your agent workforce** rather than replacing it.

---

## Technical Details

### File Generation

When you approve an agent team, the intake agent creates:

**For each agent:**

1. **Langflow Flow** (`langflow/flows/{agent_name}.json`)
   - Defines agent's reasoning flow
   - Configures LLM prompts
   - Sets up vector memory access
   - Defines input/output

2. **n8n Workflow** (`n8n/workflows/{agent_name}_trigger.json`)
   - Sets up triggers (cron, webhook, etc.)
   - Calls the Langflow agent via HTTP
   - Handles response and logging
   - Manages workflow state

### Agent Communication

Agents communicate through:

1. **Qdrant Vector Memory**: Shared knowledge base
2. **Coordinator Pattern**: Central router for requests
3. **n8n State**: Workflow variables and context
4. **PostgreSQL**: Persistent configuration

### Customization Options

You can customize agents by editing:

- **Langflow flows**: Visual editor at http://localhost:7860
- **n8n workflows**: Visual editor at http://localhost:5678
- **Agent code**: Python files in `agents/` directory
- **Environment variables**: `.env` file

---

## FAQ

**Q: Do I need to know code to use the intake agent?**  
A: No! Just describe what you need in natural language.

**Q: Can I modify agents after they're created?**  
A: Yes, via the Langflow and n8n UIs or by talking to the intake agent again.

**Q: Will this work with cloud LLMs (OpenAI, Claude)?**  
A: Yes! Set your API key in `.env` and agents will use that instead of Ollama.

**Q: Can I create agents for specific tools (like Git, Docker)?**  
A: Yes! Tell the intake agent which tools you want to integrate.

**Q: How many agents can I create?**  
A: As many as you need! Each agent is lightweight.

**Q: Can agents talk to each other?**  
A: Yes, through the coordinator pattern and shared memory.

**Q: What if I don't like an agent?**  
A: Delete its files from `langflow/flows/` and `n8n/workflows/`, or ask the intake agent to remove it.

---

## Next Steps

1. **Try it**: Visit http://localhost:8000/intake-agent
2. **Create your first team**: Describe what you need
3. **Watch it work**: Monitor in Langflow and n8n UIs
4. **Customize**: Edit flows as needed
5. **Expand**: Create more teams for different needs

**The power is in your natural language!** 🚀
