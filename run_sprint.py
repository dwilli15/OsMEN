#!/usr/bin/env python3
"""
Sprint Runner - Orchestrates team agents for Day 1 OAuth sprint.

This script starts the orchestration agent and team agents,
coordinating their execution for the Day 1 sprint tasks.
"""

import os
import sys
import time
import threading
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))

from agents.orchestration_agent.orchestration_agent import OrchestrationAgent
from agents.team1_oauth_agent.team1_oauth_agent import Team1OAuthAgent
from loguru import logger


def run_orchestration_agent(agent: OrchestrationAgent, duration: int = 600):
    """
    Run orchestration agent in a thread.
    
    Args:
        agent: OrchestrationAgent instance
        duration: How long to run (seconds)
    """
    iterations = duration // 30  # 30 second intervals
    agent.run_coordination_loop(iterations=iterations, interval=30)


def run_team1_agent(agent: Team1OAuthAgent, duration: int = 600):
    """
    Run Team 1 agent in a thread.
    
    Args:
        agent: Team1OAuthAgent instance
        duration: How long to run (seconds)
    """
    max_iterations = duration // 30  # 30 second intervals
    result = agent.run(check_interval=30, max_iterations=max_iterations)
    logger.info(f"Team 1 agent completed: {result}")


def main():
    """Main entry point for sprint runner."""
    logger.info("=" * 60)
    logger.info("Starting Day 1 OAuth Sprint")
    logger.info("=" * 60)
    
    # Create agents
    orchestration = OrchestrationAgent()
    team1 = Team1OAuthAgent()
    
    # Register Team 1 with orchestration
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
    
    logger.info("Agents initialized and registered")
    logger.info("")
    
    # Start agents in separate threads
    duration = 600  # 10 minutes for demo
    
    orchestration_thread = threading.Thread(
        target=run_orchestration_agent,
        args=(orchestration, duration)
    )
    team1_thread = threading.Thread(
        target=run_team1_agent,
        args=(team1, duration)
    )
    
    # Start threads
    orchestration_thread.start()
    time.sleep(2)  # Let orchestration start first
    team1_thread.start()
    
    logger.info("All agents started. Running sprint...")
    logger.info("")
    
    # Wait for completion or timeout
    team1_thread.join(timeout=duration + 10)
    orchestration_thread.join(timeout=10)
    
    # Get final status
    logger.info("")
    logger.info("=" * 60)
    logger.info("Sprint Completed - Final Status")
    logger.info("=" * 60)
    
    status = orchestration.get_sprint_status()
    logger.info(f"Sprint Status: {status['status']}")
    logger.info(f"Elapsed Time: {status['elapsed_hours']} hours")
    logger.info(f"Total Tasks Completed: {status['total_tasks_completed']}")
    logger.info(f"Open Blockers: {len(status['open_blockers'])}")
    logger.info(f"Milestones: {len(status['milestones'])}")
    
    for team_name, team_data in status['teams'].items():
        logger.info(f"\nTeam: {team_name}")
        logger.info(f"  Status: {team_data['status']}")
        logger.info(f"  Tasks Completed: {len(team_data.get('tasks_completed', []))}")
        logger.info(f"  Current Task: {team_data.get('current_task', 'None')}")
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("Sprint Runner Finished")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
