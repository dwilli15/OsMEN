# Innovation Agent Documentation

## Overview

The Innovation Agent is an autonomous monitoring system that discovers, evaluates, and proposes improvements to OsMEN by tracking:
- GitHub releases for key frameworks
- RSS feeds from tech communities
- Academic papers from ArXiv
- Productivity tool launches

## Features

### Automated Monitoring
- **Weekly Scans**: Runs every Sunday at 6 PM UTC via GitHub Actions
- **Smart Caching**: Avoids duplicate discoveries
- **Watch List Integration**: Uses `.copilot/memory.json` configuration

### Discovery Sources
1. **GitHub Releases**
   - microsoft/autogen
   - microsoft/semantic-kernel
   - langchain-ai/langgraph
   - joaomdmoura/crewAI
   - run-llama/llama_index
   - langflow-ai/langflow
   - n8n-io/n8n

2. **RSS Feeds**
   - Hacker News
   - r/MachineLearning
   - r/LocalLLaMA

3. **ArXiv Papers**
   - Autonomous agents
   - LLM orchestration
   - Agentic workflows

### Innovation Scoring

Each discovery is evaluated on:
- **Relevance Score** (1-10): Alignment with grad school workflows
- **Complexity Score** (1-10): Integration difficulty (lower is better)
- **Impact Score** (1-10): Expected improvement to UX
- **Risk Level** (low/medium/high): Security, privacy, stability concerns
- **No-Code Compatible** (yes/no): Can non-technical user manage it?

**Threshold for Suggestions:**
- Relevance ≥ 7
- Complexity ≤ 6
- Impact ≥ 6
- Risk ≤ medium
- No-Code Compatible = yes

### Recommendations

Based on scoring, innovations receive one of:
- **implement**: Ready for implementation
- **research_more**: Needs further investigation
- **hold**: Wait for maturity
- **reject**: Not suitable

## Usage

### Manual Scan
```bash
python agents/innovation_agent/innovation_agent.py
```

### Via MCP Server
```python
from gateway.mcp_server import MCPServer, ToolCallRequest

server = MCPServer()

# Run weekly scan
request = ToolCallRequest(
    tool='innovation_weekly_scan',
    parameters={}
)
response = server.call_tool(request)
print(f"Found {len(response.result)} innovations")
```

### Via GitHub Actions
Automatically runs every Sunday. Creates:
1. Updated `docs/INNOVATION_BACKLOG.md`
2. GitHub issue for review

## Output Files

### Innovation Backlog
Location: `docs/INNOVATION_BACKLOG.md`

Contains all discoveries organized by date with full details:
- Name and category
- Source and URL
- Summary and evaluation scores
- Recommendation

### Cache
Location: `agents/innovation_agent/config/cache.json`

Tracks:
- Seen URLs (to avoid duplicates)
- Last scan timestamp

## Configuration

### Watch List
Edit `.copilot/memory.json`:

```json
{
  "innovation_agent": {
    "watch_list": [
      "MS Agent Framework",
      "Agent Lightning",
      "LangGraph updates",
      "CrewAI releases",
      ...
    ]
  }
}
```

### Scan Frequency
Edit `.github/workflows/innovation-scan.yml`:

```yaml
schedule:
  - cron: '0 18 * * 0'  # Sunday 6 PM UTC
```

## Integration with Workflow

### Approval Process
1. Weekly scan runs automatically
2. Results added to backlog
3. GitHub issue created for review
4. User reviews and approves/rejects
5. Pre-approved tasks can auto-execute

### Pre-Approved Tasks
See `.copilot/pre_approved_tasks.json` for tasks that can run autonomously.

## Examples

### Sample Discovery

```markdown
### langflow-ai/langflow v1.5.0

**Category:** framework
**Source:** GitHub Releases
**URL:** https://github.com/langflow-ai/langflow/releases/tag/v1.5.0
**Date:** 2025-11-10

**Summary:**
New version with improved agent coordination and memory management...

**Evaluation:**
- Relevance: 9/10
- Complexity: 4/10
- Impact: 8/10
- Risk: low
- No-Code Compatible: Yes

**Recommendation:** implement
```

## Testing

Run test suite:
```bash
python test_innovation_agent.py
```

Or via integration tests:
```bash
python test_mcp_integration.py
```

## Troubleshooting

### No discoveries
- Check internet connectivity
- Verify watch list in memory.json
- Check cache.json for last scan time
- Review scoring thresholds in innovation_guidelines.md

### GitHub rate limiting
- Add GITHUB_TOKEN to environment
- Reduce scan frequency
- Limit repositories in watch list

### ArXiv connection errors
- Normal in restricted network environments
- Other sources (GitHub, RSS) will still work
- Can disable ArXiv in innovation_agent.py

## Security

- No secrets required for basic operation
- Optional GITHUB_TOKEN improves rate limits
- All data stays local (no cloud APIs)
- Respects privacy and no-code principles

## Future Enhancements

- [ ] ProductHunt integration
- [ ] Email digest delivery
- [ ] Automatic implementation of approved items
- [ ] ML-based relevance scoring
- [ ] Integration with calendar for scheduled reviews
- [ ] Slack/Discord notifications

## Support

For issues or questions:
- Check `docs/INNOVATION_BACKLOG.md` for examples
- Review `.copilot/innovation_guidelines.md` for criteria
- See test files for usage examples
- Open GitHub issue for bugs

---

**Last Updated:** 2025-11-11
**Version:** 1.0.0
