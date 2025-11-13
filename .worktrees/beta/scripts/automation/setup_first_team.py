#!/usr/bin/env python3
"""
Setup the first agent team in OsMEN
Creates team configuration with coordinator and specialist agents
"""

import json
import sys
from pathlib import Path

def create_first_team():
    """Create and configure the first agent team"""
    
    print("="*60)
    print("First Team Setup")
    print("="*60)
    print()
    
    # Define the first team
    team = {
        "name": "Core Operations Team",
        "description": "Primary team for system operations and daily tasks",
        "agents": [
            {
                "name": "Coordinator",
                "role": "coordinator",
                "description": "Routes tasks to specialist agents",
                "flow_file": "langflow/flows/coordinator.json"
            },
            {
                "name": "Boot Hardening Specialist",
                "role": "security",
                "description": "System security and boot integrity",
                "flow_file": "langflow/flows/boot_hardening_specialist.json"
            },
            {
                "name": "Daily Brief Specialist",
                "role": "reporting",
                "description": "Daily briefings and status reports",
                "flow_file": "langflow/flows/daily_brief_specialist.json"
            },
            {
                "name": "Focus Guardrails Specialist",
                "role": "productivity",
                "description": "Productivity and distraction management",
                "flow_file": "langflow/flows/focus_guardrails_specialist.json"
            },
            {
                "name": "Knowledge Management Specialist",
                "role": "knowledge",
                "description": "Obsidian integration and knowledge base",
                "flow_file": "langflow/flows/knowledge_specialist.json"
            }
        ],
        "workflows": [
            {
                "name": "Daily Security Check",
                "trigger": "cron: 0 0 * * *",  # Midnight daily
                "workflow_file": "n8n/workflows/boot_hardening_trigger.json"
            },
            {
                "name": "Morning Brief",
                "trigger": "cron: 0 8 * * *",  # 8 AM daily
                "workflow_file": "n8n/workflows/daily_brief_trigger.json"
            },
            {
                "name": "Focus Session Monitor",
                "trigger": "cron: */15 * * * *",  # Every 15 minutes
                "workflow_file": "n8n/workflows/focus_guardrails_monitor.json"
            }
        ]
    }
    
    # Save team configuration
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    teams_dir = config_dir / "teams"
    teams_dir.mkdir(exist_ok=True)
    
    team_file = teams_dir / "core_operations.json"
    
    with open(team_file, 'w') as f:
        json.dump(team, f, indent=2)
    
    print(f"✅ Team configuration saved: {team_file}")
    
    # Create Langflow flows if they don't exist
    print()
    print("Checking Langflow flows...")
    
    langflow_dir = Path("langflow/flows")
    langflow_dir.mkdir(parents=True, exist_ok=True)
    
    for agent in team["agents"]:
        flow_file = Path(agent["flow_file"])
        if not flow_file.exists():
            print(f"⚠️  Flow file missing: {flow_file}")
            print(f"   Creating placeholder for {agent['name']}...")
            
            # Create basic flow structure
            flow = {
                "name": agent["name"],
                "description": agent["description"],
                "nodes": [],
                "edges": []
            }
            
            flow_file.parent.mkdir(parents=True, exist_ok=True)
            with open(flow_file, 'w') as f:
                json.dump(flow, f, indent=2)
            
            print(f"   ✅ Created: {flow_file}")
        else:
            print(f"✅ Flow exists: {flow_file}")
    
    # Create n8n workflows if they don't exist
    print()
    print("Checking n8n workflows...")
    
    n8n_dir = Path("n8n/workflows")
    n8n_dir.mkdir(parents=True, exist_ok=True)
    
    for workflow in team["workflows"]:
        workflow_file = Path(workflow["workflow_file"])
        if not workflow_file.exists():
            print(f"⚠️  Workflow file missing: {workflow_file}")
            print(f"   Creating placeholder for {workflow['name']}...")
            
            # Create basic workflow structure
            wf = {
                "name": workflow["name"],
                "nodes": [],
                "connections": {},
                "settings": {
                    "executionOrder": "v1"
                }
            }
            
            workflow_file.parent.mkdir(parents=True, exist_ok=True)
            with open(workflow_file, 'w') as f:
                json.dump(wf, f, indent=2)
            
            print(f"   ✅ Created: {workflow_file}")
        else:
            print(f"✅ Workflow exists: {workflow_file}")
    
    # Display team summary
    print()
    print("="*60)
    print("Team Configuration Summary")
    print("="*60)
    print(f"Team: {team['name']}")
    print(f"Agents: {len(team['agents'])}")
    
    for agent in team['agents']:
        print(f"  - {agent['name']} ({agent['role']})")
    
    print(f"\nWorkflows: {len(team['workflows'])}")
    for workflow in team['workflows']:
        print(f"  - {workflow['name']} ({workflow['trigger']})")
    
    print()
    print("="*60)
    print("✅ First team setup complete!")
    print("="*60)
    print()
    print("Next steps:")
    print("1. Configure flows in Langflow UI: http://localhost:7860")
    print("2. Configure workflows in n8n UI: http://localhost:5678")
    print("3. Test team coordination with sample tasks")
    
    return team

if __name__ == '__main__':
    try:
        create_first_team()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
