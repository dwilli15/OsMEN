#!/usr/bin/env python3
"""
Team 3 Agent Demo - Autonomous Execution
Demonstrates the Team 3 agent working autonomously with orchestration
"""

import sys
import time
from pathlib import Path

# Add sprint directory to path
sprint_dir = Path(__file__).parent / 'sprint'
sys.path.insert(0, str(sprint_dir))

from day1.orchestration.orchestration_agent import OrchestrationAgent
from day1.team3_api_clients.team3_agent import Team3Agent


def demo_autonomous_execution():
    """Demonstrate autonomous execution with orchestration"""
    
    print("\n" + "="*70)
    print("TEAM 3 AGENT - AUTONOMOUS EXECUTION DEMO")
    print("="*70)
    print()
    print("This demo shows the Team 3 agent working autonomously on API client")
    print("generation tasks while coordinating with the orchestration agent.")
    print()
    print("The agent will:")
    print("  1. Initialize and connect to orchestration")
    print("  2. Execute tasks in dependency order")
    print("  3. Request secrets when needed")
    print("  4. Report blockers for missing secrets")
    print("  5. Continue with non-blocked tasks")
    print("  6. Request PR creation when complete")
    print()
    print("="*70)
    input("\nPress ENTER to start the demo...")
    
    # Create orchestration agent
    print("\n📋 Creating Orchestration Agent...")
    orchestration = OrchestrationAgent()
    print("✅ Orchestration agent ready")
    
    # Create Team 3 agent
    print("\n🤖 Creating Team 3 Agent...")
    agent = Team3Agent(orchestration_agent=orchestration)
    print("✅ Team 3 agent ready")
    
    # Show initial status
    print("\n" + agent.generate_status_report())
    print("\n" + orchestration.generate_status_report())
    
    input("\nPress ENTER to begin autonomous execution...")
    
    # Run autonomously
    print("\n🚀 Starting autonomous execution...")
    print("-" * 70)
    print()
    
    final_status = agent.run_autonomously(max_iterations=20)
    
    # Show final status
    print("\n" + "="*70)
    print("AUTONOMOUS EXECUTION COMPLETE")
    print("="*70)
    
    print("\n" + agent.generate_status_report())
    print("\n" + orchestration.generate_status_report())
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    status = agent.get_status()
    orch_status = orchestration.get_overall_status()
    
    print(f"\n✅ Tasks Completed: {status['completed']}/{status['total_tasks']}")
    print(f"🔴 Tasks Blocked: {status['blocked']}")
    print(f"⚪ Tasks Pending: {status['pending']}")
    print(f"📊 Overall Progress: {status['progress']}%")
    
    print(f"\n📨 Messages Sent: {orch_status['messages_count']}")
    print(f"⚠️  Blockers Reported: {orch_status['open_blockers']}")
    print(f"🔐 Secret Requests: {orch_status['pending_secrets']}")
    
    if orch_status['pending_secrets'] > 0:
        print("\n" + "="*70)
        print("SECRETS NEEDED")
        print("="*70)
        print("\nThe agent requires the following secrets to continue:")
        for secret in orch_status['secret_requests']:
            print(f"\n  🔑 {secret['secret_name']}")
            print(f"     Reason: {secret['reason']}")
        
        print("\nTo provide secrets, add them to the .env file or set as environment variables.")
        print("Then re-run the agent to complete the remaining tasks.")
    
    if status['progress'] == 100:
        print("\n🎉 ALL TASKS COMPLETE! Ready for PR creation.")
    else:
        print(f"\n⏸️  Execution paused at {status['progress']}% progress.")
        print("   Waiting for secrets to be provided.")
    
    print("\n" + "="*70)


def demo_step_by_step():
    """Demonstrate step-by-step execution with user interaction"""
    
    print("\n" + "="*70)
    print("TEAM 3 AGENT - STEP-BY-STEP EXECUTION DEMO")
    print("="*70)
    print()
    print("This demo allows you to step through tasks one at a time.")
    print()
    print("="*70)
    input("\nPress ENTER to start...")
    
    # Create agents
    print("\n📋 Creating agents...")
    orchestration = OrchestrationAgent()
    agent = Team3Agent(orchestration_agent=orchestration)
    
    # Show initial status
    print("\n" + agent.generate_status_report())
    
    # Execute tasks one by one
    task_count = 0
    for task in agent.tasks:
        if agent._check_dependencies(task) and task['status'].value == 'pending':
            task_count += 1
            print(f"\n{'='*70}")
            print(f"TASK {task_count}: {task['name']}")
            print(f"{'='*70}")
            print(f"Estimated time: {task['estimated_hours']} hours")
            print(f"Requires secret: {task.get('requires_secret', False)}")
            
            input("\nPress ENTER to execute this task...")
            
            agent.execute_task(task)
            
            print("\n" + agent.generate_status_report())
            
            if task_count >= 5:  # Limit to first 5 tasks for demo
                print("\n⏸️  Demo limited to first 5 tasks. Run autonomous mode for full execution.")
                break
    
    print("\n" + orchestration.generate_status_report())
    print("\n" + "="*70)


def main():
    """Main function"""
    print("\n" + "="*70)
    print("TEAM 3 AGENT DEMONSTRATION")
    print("="*70)
    print()
    print("Select demo mode:")
    print("  1. Autonomous Execution (recommended)")
    print("  2. Step-by-Step Execution")
    print("  3. Exit")
    print()
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == '1':
        demo_autonomous_execution()
    elif choice == '2':
        demo_step_by_step()
    elif choice == '3':
        print("\nGoodbye!")
        return
    else:
        print(f"\nInvalid choice: {choice}")
        return
    
    print("\n" + "="*70)
    print("Demo complete!")
    print("="*70)
    print()


if __name__ == "__main__":
    main()
