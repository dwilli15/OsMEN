#!/usr/bin/env python3
"""
Demonstration of Team 1 Agent autonomous operation and coordination.

This script shows how Team 1 agent:
1. Registers with orchestration agent
2. Autonomously executes tasks from TODO.md
3. Reports progress at intervals
4. Requests secrets when needed
5. Reports milestones
6. Requests PR creation when appropriate
"""

import os
import sys
import time
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))

from agents.orchestration_agent.orchestration_agent import OrchestrationAgent
from agents.team1_oauth_agent.team1_oauth_agent import Team1OAuthAgent
from loguru import logger


def demonstrate_autonomous_operation():
    """Demonstrate Team 1 agent autonomous operation."""
    
    logger.info("=" * 70)
    logger.info("Team 1 Agent Autonomous Operation Demonstration")
    logger.info("=" * 70)
    logger.info("")
    
    # Create orchestration agent
    logger.info("Step 1: Initialize Orchestration Agent")
    logger.info("-" * 70)
    orchestration = OrchestrationAgent()
    logger.info("✅ Orchestration agent ready")
    logger.info("")
    
    # Create Team 1 agent
    logger.info("Step 2: Initialize Team 1 OAuth Agent")
    logger.info("-" * 70)
    team1 = Team1OAuthAgent()
    logger.info(f"✅ Team 1 agent ready with {len(team1.tasks)} tasks")
    logger.info("")
    
    # Register team with orchestration
    logger.info("Step 3: Register Team 1 with Orchestration")
    logger.info("-" * 70)
    orchestration.register_team("team1_google_oauth", {
        'lead': 'OAuth Lead',
        'focus': 'Google OAuth Implementation',
        'dependencies': [],
        'deliverables': [
            'Universal OAuth handler base class',
            'Google OAuth 2.0 implementation',
            'OAuth provider registry',
            'Google OAuth setup wizard'
        ]
    })
    logger.info("✅ Team registered successfully")
    logger.info("")
    
    # Show task list
    logger.info("Step 4: Team 1 Task Checklist")
    logger.info("-" * 70)
    logger.info("Tasks to be executed autonomously:")
    logger.info("")
    for i, task in enumerate(team1.tasks, 1):
        status = "✅" if task.get('completed') else "⏳"
        logger.info(f"  {status} {i:2d}. {task['name']} (Hour {task['hour']})")
    logger.info("")
    
    # Simulate a few coordination cycles
    logger.info("Step 5: Simulated Autonomous Execution (3 tasks)")
    logger.info("-" * 70)
    logger.info("Team 1 will now autonomously execute tasks and coordinate with orchestration...")
    logger.info("")
    
    # Execute first 3 tasks to demonstrate
    for i in range(3):
        logger.info(f"\n--- Cycle {i+1} ---")
        
        # Team 1 executes next task
        pending_tasks = [t for t in team1.tasks if not t.get('completed', False)]
        if pending_tasks:
            task = pending_tasks[0]
            logger.info(f"Team 1: Executing '{task['name']}'")
            
            # Execute the task
            success = team1.execute_task(task)
            
            if success:
                # Report status to orchestration
                team1.report_status()
                logger.info("Team 1: ✅ Task completed, status reported to orchestration")
                
                # Orchestration processes messages
                orchestration.process_messages()
                logger.info("Orchestration: Processed status update from Team 1")
                
                # Check if milestone reached
                if len(team1.completed_tasks) % 4 == 0:
                    team1.report_milestone(
                        f"Checkpoint at {len(team1.completed_tasks)} tasks",
                        f"Completed {len(team1.completed_tasks)}/{len(team1.tasks)} tasks"
                    )
                    orchestration.process_messages()
                    logger.info("Team 1: 🎯 Milestone reported to orchestration")
            
            time.sleep(1)  # Brief pause for readability
    
    logger.info("")
    logger.info("Step 6: Final Status")
    logger.info("-" * 70)
    
    # Get final sprint status
    status = orchestration.get_sprint_status()
    
    logger.info(f"Sprint Status: {status['status']}")
    logger.info(f"Total Tasks Completed: {status['total_tasks_completed']}")
    logger.info(f"Milestones Reached: {len(status['milestones'])}")
    logger.info(f"Open Blockers: {len(status['open_blockers'])}")
    logger.info("")
    
    # Show team status
    team_data = status['teams'].get('team1_google_oauth', {})
    logger.info("Team 1 Status:")
    logger.info(f"  Current Status: {team_data.get('status', 'unknown')}")
    logger.info(f"  Tasks Completed: {len(team_data.get('tasks_completed', []))}")
    logger.info(f"  Current Task: {team_data.get('current_task', 'None')}")
    logger.info("")
    
    # Show example of secret request
    logger.info("Step 7: Demonstrate Secret Request")
    logger.info("-" * 70)
    logger.info("Team 1 needs OAuth credentials...")
    team1.request_secret('GOOGLE_CLIENT_ID', 'Required for Google OAuth')
    logger.info("Team 1: Secret request sent to orchestration")
    
    orchestration.process_messages()
    logger.info("Orchestration: Secret request received, will notify user @dwilli15")
    logger.info("")
    
    # Show example of PR request
    logger.info("Step 8: Demonstrate PR Request")
    logger.info("-" * 70)
    logger.info("Team 1 completes major milestone, requests PR...")
    team1.request_pr(
        "OAuth Infrastructure Complete",
        "Implemented OAuth base classes and Google provider"
    )
    logger.info("Team 1: PR request sent to orchestration")
    
    orchestration.process_messages()
    logger.info("Orchestration: PR request received, will coordinate with other teams")
    logger.info("")
    
    # Summary
    logger.info("=" * 70)
    logger.info("Demonstration Complete!")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Key Capabilities Demonstrated:")
    logger.info("  ✅ Autonomous task execution from TODO.md checklist")
    logger.info("  ✅ Progress reporting to orchestration agent")
    logger.info("  ✅ Milestone detection and reporting")
    logger.info("  ✅ Secret request mechanism (for OAuth credentials)")
    logger.info("  ✅ PR request coordination")
    logger.info("  ✅ Message-based inter-agent communication")
    logger.info("")
    logger.info("Team 1 agent can now run fully autonomously with:")
    logger.info("  python3 run_sprint.py")
    logger.info("")
    logger.info("Or interact with orchestration to coordinate:")
    logger.info("  - Secret requests from user @dwilli15")
    logger.info("  - PR creation at appropriate milestones")
    logger.info("  - Blocker resolution")
    logger.info("  - Cross-team dependencies")
    logger.info("")


def show_message_queue():
    """Show the message queue contents."""
    logger.info("=" * 70)
    logger.info("Message Queue Contents")
    logger.info("=" * 70)
    logger.info("")
    
    message_dir = Path("/tmp/osmen_messages")
    
    if not message_dir.exists():
        logger.info("No message queue found (agents haven't run yet)")
        return
    
    for agent_dir in sorted(message_dir.iterdir()):
        if agent_dir.is_dir():
            logger.info(f"Agent: {agent_dir.name}")
            
            inbox = agent_dir / "inbox"
            outbox = agent_dir / "outbox"
            
            if inbox.exists():
                inbox_count = len(list(inbox.glob("*.json")))
                logger.info(f"  Inbox: {inbox_count} messages")
            
            if outbox.exists():
                outbox_count = len(list(outbox.glob("*.json")))
                logger.info(f"  Outbox: {outbox_count} messages")
            
            logger.info("")


def main():
    """Main entry point."""
    print("\n")
    demonstrate_autonomous_operation()
    print("\n")
    show_message_queue()
    print("\n")


if __name__ == "__main__":
    main()
