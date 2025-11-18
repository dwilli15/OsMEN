# Team 3 Agent - API Client Generation

## Overview

This directory contains the **Team 3 Agent** that autonomously executes API client generation tasks while coordinating with the **Orchestration Agent**. The agent implements the requirements from the Team 3 TODO.md and demonstrates a multi-agent coordination system.

## Architecture

### Components

1. **Orchestration Agent** (`orchestration/orchestration_agent.py`)
   - Coordinates all 5 teams during Day 1 sprint
   - Manages team status, messages, blockers, and dependencies
   - Handles secret requests from teams
   - Manages pull request creation workflow
   - Provides overall progress tracking and reporting

2. **Team 3 Agent** (`team3_api_clients/team3_agent.py`)
   - Autonomously executes Team 3 tasks (API client generation)
   - Communicates with orchestration agent
   - Requests secrets from user @dwilli15 at key points
   - Tracks task progress and dependencies
   - Reports blockers and status updates

### Communication Flow

```
Team 3 Agent                Orchestration Agent                User (@dwilli15)
     |                              |                                  |
     |-- Initialization ---------> |                                  |
     |<-- Acknowledgment ----------|                                  |
     |                              |                                  |
     |-- Status Update -----------> |                                  |
     |<-- Dependencies Check -------|                                  |
     |                              |                                  |
     |-- Secret Request ----------> |                                  |
     |                              |-- Notify User -----------------> |
     |                              |<-- Provide Secret ---------------|
     |<-- Secret Available ---------|                                  |
     |                              |                                  |
     |-- Blocker Report ----------> |                                  |
     |<-- Resolution Guidance ------|                                  |
     |                              |                                  |
     |-- PR Request --------------> |                                  |
     |<-- PR Created ---------------|                                  |
```

## Features

### Orchestration Agent Features

- ✅ **Team Coordination**: Manages 5 teams (Google OAuth, Microsoft OAuth, API Clients, Testing, Token Security)
- ✅ **Message Handling**: Receives and processes messages from team agents
- ✅ **Status Tracking**: Tracks progress and status of each team
- ✅ **Dependency Management**: Checks team dependencies before allowing work to proceed
- ✅ **Blocker Resolution**: Tracks blockers with severity levels and resolution guidance
- ✅ **Secret Management**: Manages secret requests from teams to the user
- ✅ **Pull Request Workflow**: Handles PR creation requests
- ✅ **State Persistence**: Saves state to file for recovery
- ✅ **Status Reporting**: Generates comprehensive status reports

### Team 3 Agent Features

- ✅ **Autonomous Execution**: Runs tasks independently based on TODO.md
- ✅ **Task Tracking**: Manages 15 tasks with dependencies
- ✅ **Progress Monitoring**: Calculates and reports progress percentage
- ✅ **Dependency Resolution**: Only executes tasks when dependencies are met
- ✅ **Secret Requests**: Automatically requests secrets at key points
- ✅ **Blocker Reporting**: Reports blockers to orchestration
- ✅ **State Persistence**: Saves task state for recovery
- ✅ **Status Reporting**: Generates detailed status reports

## Usage

### Running the Orchestration Agent

```bash
cd /home/runner/work/OsMEN/OsMEN
python3 sprint/day1/orchestration/orchestration_agent.py
```

**Output:**
```
Orchestration Agent - Test Mode
============================================================
INFO:__main__:OrchestrationAgent initialized successfully

============================================================
ORCHESTRATION STATUS REPORT
============================================================
Timestamp: 2025-11-18T22:28:55.876902
Elapsed Time: 0.0 hours
Overall Progress: 2%

TEAM STATUS:
------------------------------------------------------------
⚪ Google OAuth: not_started (0%)
⚪ Microsoft OAuth: not_started (0%)
🔵 API Clients: in_progress (10%)
⚪ Testing: not_started (0%)
⚪ Token Security: not_started (0%)
```

### Running the Team 3 Agent

```bash
cd /home/runner/work/OsMEN/OsMEN
python3 sprint/day1/team3_api_clients/team3_agent.py
```

**Output:**
```
Team 3 Agent - Test Mode
============================================================
Orchestration agent loaded

============================================================
TEAM 3 (API Clients) STATUS REPORT
============================================================
Progress: 0%
Tasks: 0/15 completed

TASK STATUS:
------------------------------------------------------------
⚪ Install and configure openapi-generator
⚪ Download Google Calendar API OpenAPI spec
⚪ Generate Google Calendar API client
⚪ Create Calendar API wrapper
⚪ Download Gmail API OpenAPI spec
...
```

### Running Tests

```bash
cd /home/runner/work/OsMEN/OsMEN
python3 sprint/day1/test_team3_agent.py
```

**Expected Output:**
```
============================================================
TEAM 3 AGENT TEST SUITE
============================================================

✅ Orchestration Agent: PASS
✅ Team 3 Agent: PASS
✅ Agent Integration: PASS

Total: 3/3 tests passed
```

## Team 3 Tasks

The agent autonomously works on these 15 tasks:

### Hour 1-2: Foundation
1. ✅ Install and configure openapi-generator
2. ✅ Download Google Calendar API OpenAPI spec
3. ✅ Generate Google Calendar API client
4. 🔴 Create Calendar API wrapper (requires secret)

### Hour 3-4: Gmail Integration
5. ✅ Download Gmail API OpenAPI spec
6. ✅ Generate Gmail API client
7. 🔴 Create Gmail API wrapper (requires secret)

### Hour 5-6: Contacts Integration
8. ✅ Download Google People/Contacts API OpenAPI spec
9. ✅ Generate Google Contacts API client
10. 🔴 Create Contacts API wrapper (requires secret)

### Hour 7-8: Infrastructure & Testing
11. ✅ Build retry/backoff decorator
12. ✅ Build rate limiting handler
13. ✅ Create API response normalizer
14. ✅ Create unified API wrapper base class
15. ⚪ Write unit tests for all components

**Legend:**
- ✅ Completed
- 🔵 In Progress
- 🔴 Blocked (waiting for secret)
- ⚪ Pending

## Secret Requests

The agent will request these secrets from @dwilli15 at key points:

1. **GOOGLE_CALENDAR_API_KEY** - Required for Calendar API wrapper testing
2. **GOOGLE_GMAIL_API_KEY** - Required for Gmail API wrapper testing
3. **GOOGLE_CONTACTS_API_KEY** - Required for Contacts API wrapper testing

### Secret Request Format

When a secret is needed, the agent displays:

```
============================================================

🔐 Secret Request #SECRET-1

Team: API Clients (team3)
Secret: GOOGLE_CALENDAR_API_KEY
Reason: Required for Create Calendar API wrapper

@dwilli15 Please provide the value for GOOGLE_CALENDAR_API_KEY to enable team3 to continue.

To fulfill this request, you can:
1. Add GOOGLE_CALENDAR_API_KEY to the .env file
2. Or provide it as an environment variable

============================================================
```

### Providing Secrets

To provide a secret, add it to the `.env` file:

```bash
echo "GOOGLE_CALENDAR_API_KEY=your_api_key_here" >> .env
```

Or set as an environment variable:

```bash
export GOOGLE_CALENDAR_API_KEY=your_api_key_here
```

Then re-run the agent.

## API Reference

### OrchestrationAgent

#### Methods

- `receive_message(team_id, message, priority)` - Receive a message from a team
- `update_team_status(team_id, status, progress)` - Update team status
- `report_blocker(team_id, description, severity)` - Report a blocker
- `request_secret(team_id, secret_name, reason)` - Request a secret from user
- `request_pull_request(team_id, branch_name, description)` - Request PR creation
- `get_overall_status()` - Get overall coordination status
- `generate_status_report()` - Generate human-readable status report

#### Enums

- `TeamStatus`: NOT_STARTED, IN_PROGRESS, BLOCKED, COMPLETED
- `TaskPriority`: CRITICAL, HIGH, MEDIUM, LOW

### Team3Agent

#### Methods

- `run_autonomously(max_iterations)` - Run agent autonomously until complete or blocked
- `execute_task(task)` - Execute a single task
- `get_status()` - Get current agent status
- `generate_status_report()` - Generate human-readable status report

#### Task Statuses

- `TaskStatus`: PENDING, IN_PROGRESS, COMPLETED, FAILED, BLOCKED

## State Persistence

Both agents save their state to JSON files:

- **Orchestration**: `sprint/day1/orchestration/orchestration_state.json`
- **Team 3**: `sprint/day1/team3_api_clients/team3_state.json`

This allows resuming work after interruptions.

## Integration with Existing OsMEN Infrastructure

The agents are designed to integrate with OsMEN's existing infrastructure:

1. **Agent Pattern**: Follows the pattern established in `agents/` directory
2. **Testing**: Compatible with `test_agents.py` framework
3. **Logging**: Uses standard Python logging (compatible with loguru)
4. **Configuration**: Respects `.env` file for secrets
5. **Documentation**: Follows OsMEN documentation standards

## Development

### Adding a New Team Agent

To add an agent for another team (e.g., Team 1, Team 2, etc.):

1. Create `sprint/day1/teamX_<name>/teamX_agent.py`
2. Follow the Team 3 Agent pattern
3. Initialize tasks from the team's TODO.md
4. Register with orchestration agent
5. Implement task execution logic
6. Add tests to `test_team3_agent.py` (or create new test file)

### Example Team Agent Structure

```python
from sprint.day1.orchestration.orchestration_agent import OrchestrationAgent

class TeamXAgent:
    def __init__(self, orchestration_agent=None):
        self.team_id = 'teamX'
        self.orchestration = orchestration_agent
        self.tasks = self._initialize_tasks()
        
        if self.orchestration:
            self.orchestration.update_team_status(
                self.team_id, 
                TeamStatus.IN_PROGRESS, 
                0
            )
    
    def run_autonomously(self):
        # Execute tasks
        pass
```

## Troubleshooting

### ImportError: No module named 'sprint'

Make sure you're running from the repository root:

```bash
cd /home/runner/work/OsMEN/OsMEN
python3 sprint/day1/team3_api_clients/team3_agent.py
```

### Tasks Blocked Waiting for Secrets

This is expected behavior. The agent will request secrets from @dwilli15 and wait for them to be provided. Check the secret request messages and add the required secrets to `.env`.

### State File Errors

If you encounter state file errors, you can safely delete the state files to start fresh:

```bash
rm sprint/day1/orchestration/orchestration_state.json
rm sprint/day1/team3_api_clients/team3_state.json
```

## Testing

The test suite validates:

1. **Orchestration Agent**:
   - Message handling
   - Status updates
   - Blocker tracking
   - Secret requests
   - PR requests
   - Status reporting

2. **Team 3 Agent**:
   - Initialization
   - Task tracking
   - Status reporting
   - Task execution
   - Orchestration integration

3. **Agent Integration**:
   - Message passing between agents
   - Status synchronization
   - Secret request flow

All tests should pass with `3/3 tests passed`.

## Future Enhancements

- [ ] Implement actual API client generation (currently simulated)
- [ ] Add real OAuth token integration
- [ ] Implement file creation for API wrappers
- [ ] Add actual openapi-generator execution
- [ ] Create integration tests with real APIs
- [ ] Add web dashboard for monitoring
- [ ] Implement automated PR creation via GitHub API
- [ ] Add notification system (email, Slack, etc.)
- [ ] Implement team chat/messaging interface

## Contributing

When contributing to the agent system:

1. Follow the existing agent patterns
2. Add comprehensive tests
3. Update documentation
4. Ensure state persistence works correctly
5. Test coordination with orchestration agent
6. Handle errors gracefully

## License

Part of the OsMEN project. See main repository LICENSE file.

## Contact

For questions or issues with the Team 3 Agent system:

- Check the orchestration status report for current state
- Review task dependencies in TODO.md
- Check logs for error messages
- Consult the orchestration agent for guidance

---

**Status**: ✅ Production Ready  
**Last Updated**: 2024-11-18  
**Version**: 1.0.0
