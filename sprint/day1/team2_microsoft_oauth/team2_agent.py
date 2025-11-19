#!/usr/bin/env python3
"""
Team 2 Agent: Microsoft OAuth Implementation
Autonomous agent that monitors and coordinates Team 2's Microsoft OAuth tasks.
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


class TaskStatus(Enum):
    """Task status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETE = "complete"
    FAILED = "failed"


class Team2Agent:
    """
    Autonomous agent for Team 2 Microsoft OAuth implementation.
    
    Monitors progress, coordinates with orchestration agent, and requests
    user secrets when needed.
    """
    
    def __init__(self, orchestration_endpoint: Optional[str] = None):
        """
        Initialize Team 2 agent.
        
        Args:
            orchestration_endpoint: URL for orchestration agent communication
        """
        self.team_name = "Team 2: Microsoft OAuth"
        self.team_id = "team2"
        self.orchestration_endpoint = orchestration_endpoint or os.getenv(
            "ORCHESTRATION_ENDPOINT",
            "http://localhost:8080/orchestration"
        )
        
        # Task tracking
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.current_hour = 0
        self.blockers: List[Dict[str, Any]] = []
        
        # Paths
        self.base_path = Path(__file__).parent.parent.parent.parent
        self.todo_path = Path(__file__).parent / "TODO.md"
        self.status_file = Path(__file__).parent / "team2_status.json"
        
        # Initialize tasks from TODO
        self._load_tasks_from_todo()
        
        # Load or create status
        self._load_status()
        
    def _load_tasks_from_todo(self):
        """Parse TODO.md and extract tasks"""
        # Key tasks from TODO
        self.tasks = {
            # Hour 1-2: Azure AD Setup
            "azure_ad_research": {
                "name": "Azure AD Research and Preparation",
                "status": TaskStatus.PENDING,
                "hour": 1,
                "dependencies": [],
                "description": "Review Azure AD OAuth documentation and best practices"
            },
            "microsoft_config": {
                "name": "Microsoft Provider Configuration",
                "status": TaskStatus.PENDING,
                "hour": 1,
                "dependencies": [],
                "description": "Create config/oauth/microsoft.yaml"
            },
            "microsoft_scopes": {
                "name": "Microsoft Graph Scopes",
                "status": TaskStatus.PENDING,
                "hour": 2,
                "dependencies": ["microsoft_config"],
                "description": "Define required scopes for Microsoft Graph API"
            },
            
            # Hour 3-4: Microsoft OAuth Handler
            "microsoft_oauth_handler": {
                "name": "MicrosoftOAuthHandler Class",
                "status": TaskStatus.PENDING,
                "hour": 3,
                "dependencies": ["microsoft_config"],
                "description": "Create integrations/oauth/microsoft_oauth.py"
            },
            "authorization_url": {
                "name": "Authorization URL Generation",
                "status": TaskStatus.PENDING,
                "hour": 3,
                "dependencies": ["microsoft_oauth_handler"],
                "description": "Implement get_authorization_url()"
            },
            "token_exchange": {
                "name": "Token Exchange Implementation",
                "status": TaskStatus.PENDING,
                "hour": 4,
                "dependencies": ["authorization_url"],
                "description": "Implement exchange_code_for_token()"
            },
            
            # Hour 5-6: Token Refresh and Azure AD Features
            "token_refresh": {
                "name": "Token Refresh Implementation",
                "status": TaskStatus.PENDING,
                "hour": 5,
                "dependencies": ["token_exchange"],
                "description": "Implement refresh_token()"
            },
            "token_validation": {
                "name": "Token Validation",
                "status": TaskStatus.PENDING,
                "hour": 5,
                "dependencies": ["token_exchange"],
                "description": "Implement validate_token()"
            },
            "admin_consent": {
                "name": "Admin Consent Flow",
                "status": TaskStatus.PENDING,
                "hour": 6,
                "dependencies": ["authorization_url"],
                "description": "Implement admin consent URL generation"
            },
            
            # Hour 7-8: Testing and Wizard
            "oauth_setup_wizard": {
                "name": "OAuth Setup Wizard CLI",
                "status": TaskStatus.PENDING,
                "hour": 7,
                "dependencies": ["token_refresh", "token_validation"],
                "description": "Add Microsoft setup to cli_bridge/oauth_setup.py"
            },
            "unit_tests": {
                "name": "Unit Tests",
                "status": TaskStatus.PENDING,
                "hour": 7,
                "dependencies": ["microsoft_oauth_handler"],
                "description": "Create tests/unit/oauth/test_microsoft_oauth.py"
            },
            "integration_tests": {
                "name": "Integration Tests",
                "status": TaskStatus.PENDING,
                "hour": 8,
                "dependencies": ["unit_tests", "oauth_setup_wizard"],
                "description": "Test complete Microsoft OAuth flow"
            }
        }
    
    def _load_status(self):
        """Load status from file"""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r') as f:
                    data = json.load(f)
                    # Restore task statuses
                    for task_id, task_data in data.get('tasks', {}).items():
                        if task_id in self.tasks:
                            self.tasks[task_id]['status'] = TaskStatus(task_data['status'])
                    self.current_hour = data.get('current_hour', 0)
                    self.blockers = data.get('blockers', [])
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load status: {e}")
    
    def _save_status(self):
        """Save status to file"""
        data = {
            'team_id': self.team_id,
            'team_name': self.team_name,
            'current_hour': self.current_hour,
            'timestamp': datetime.now().isoformat(),
            'tasks': {
                task_id: {
                    'name': task['name'],
                    'status': task['status'].value,
                    'hour': task['hour'],
                    'description': task['description']
                }
                for task_id, task in self.tasks.items()
            },
            'blockers': self.blockers
        }
        
        with open(self.status_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def report_to_orchestration(self, message_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send message to orchestration agent.
        
        Args:
            message_type: Type of message (status_update, blocker, request_secret, etc.)
            data: Message data
            
        Returns:
            Response from orchestration agent
        """
        message = {
            'team_id': self.team_id,
            'team_name': self.team_name,
            'timestamp': datetime.now().isoformat(),
            'message_type': message_type,
            'data': data
        }
        
        print(f"\n📡 Sending to Orchestration: {message_type}")
        print(f"   Data: {json.dumps(data, indent=2)}")
        
        # TODO: In a real implementation, this would make an HTTP request
        # For now, we'll log to a file
        orchestration_log = self.base_path / "sprint" / "day1" / "orchestration" / "messages.jsonl"
        orchestration_log.parent.mkdir(parents=True, exist_ok=True)
        
        with open(orchestration_log, 'a') as f:
            f.write(json.dumps(message) + '\n')
        
        # Simulated response
        return {
            'status': 'acknowledged',
            'team_id': self.team_id,
            'timestamp': datetime.now().isoformat()
        }
    
    def request_secret(self, secret_name: str, description: str) -> Optional[str]:
        """
        Request a secret from the user via orchestration agent.
        
        Args:
            secret_name: Name of the secret (e.g., MICROSOFT_CLIENT_ID)
            description: Description of what the secret is for
            
        Returns:
            Secret value or None if not provided
        """
        # First check environment
        value = os.getenv(secret_name)
        if value:
            print(f"✅ Secret {secret_name} found in environment")
            return value
        
        # Request via orchestration
        response = self.report_to_orchestration('request_secret', {
            'secret_name': secret_name,
            'description': description,
            'urgency': 'high',
            'required_for': 'Microsoft OAuth implementation'
        })
        
        print(f"\n🔐 SECRET REQUIRED: {secret_name}")
        print(f"   Description: {description}")
        print(f"   Please set environment variable or provide via orchestration agent")
        
        # In real implementation, orchestration would prompt user
        # For now, return None to indicate blocking
        return None
    
    def check_dependencies(self, task_id: str) -> bool:
        """
        Check if all dependencies for a task are complete.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if all dependencies are complete
        """
        task = self.tasks[task_id]
        for dep_id in task['dependencies']:
            if dep_id in self.tasks:
                if self.tasks[dep_id]['status'] != TaskStatus.COMPLETE:
                    return False
        return True
    
    def get_pending_tasks(self, current_hour: int) -> List[str]:
        """
        Get list of pending tasks for current hour.
        
        Args:
            current_hour: Current hour of work (1-8)
            
        Returns:
            List of task IDs that can be started
        """
        pending = []
        for task_id, task in self.tasks.items():
            if (task['status'] == TaskStatus.PENDING and
                task['hour'] <= current_hour and
                self.check_dependencies(task_id)):
                pending.append(task_id)
        return pending
    
    def update_task_status(self, task_id: str, status: TaskStatus, notes: str = ""):
        """
        Update task status and report to orchestration.
        
        Args:
            task_id: Task identifier
            status: New status
            notes: Optional notes about the status change
        """
        if task_id not in self.tasks:
            print(f"Warning: Unknown task {task_id}")
            return
        
        old_status = self.tasks[task_id]['status']
        self.tasks[task_id]['status'] = status
        
        print(f"\n📝 Task Update: {self.tasks[task_id]['name']}")
        print(f"   {old_status.value} → {status.value}")
        if notes:
            print(f"   Notes: {notes}")
        
        # Report to orchestration
        self.report_to_orchestration('task_update', {
            'task_id': task_id,
            'task_name': self.tasks[task_id]['name'],
            'old_status': old_status.value,
            'new_status': status.value,
            'notes': notes
        })
        
        self._save_status()
    
    def report_blocker(self, task_id: str, description: str, severity: str = "high"):
        """
        Report a blocker to orchestration.
        
        Args:
            task_id: Blocked task identifier
            description: Description of the blocker
            severity: Severity level (low, medium, high, critical)
        """
        blocker = {
            'task_id': task_id,
            'task_name': self.tasks[task_id]['name'],
            'description': description,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        }
        
        self.blockers.append(blocker)
        
        print(f"\n🚫 BLOCKER REPORTED")
        print(f"   Task: {self.tasks[task_id]['name']}")
        print(f"   Severity: {severity}")
        print(f"   Description: {description}")
        
        self.report_to_orchestration('blocker', blocker)
        self._save_status()
    
    def generate_status_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive status report.
        
        Returns:
            Status report dictionary
        """
        completed = sum(1 for t in self.tasks.values() if t['status'] == TaskStatus.COMPLETE)
        in_progress = sum(1 for t in self.tasks.values() if t['status'] == TaskStatus.IN_PROGRESS)
        blocked = sum(1 for t in self.tasks.values() if t['status'] == TaskStatus.BLOCKED)
        pending = sum(1 for t in self.tasks.values() if t['status'] == TaskStatus.PENDING)
        
        # Convert tasks to JSON-serializable format
        tasks_serializable = {
            task_id: {
                'name': task['name'],
                'status': task['status'].value,
                'hour': task['hour'],
                'description': task['description'],
                'dependencies': task['dependencies']
            }
            for task_id, task in self.tasks.items()
        }
        
        return {
            'team_id': self.team_id,
            'team_name': self.team_name,
            'timestamp': datetime.now().isoformat(),
            'current_hour': self.current_hour,
            'summary': {
                'total_tasks': len(self.tasks),
                'completed': completed,
                'in_progress': in_progress,
                'blocked': blocked,
                'pending': pending,
                'completion_percentage': (completed / len(self.tasks)) * 100
            },
            'tasks': tasks_serializable,
            'blockers': self.blockers
        }
    
    def print_status(self):
        """Print current status to console"""
        report = self.generate_status_report()
        
        print(f"\n{'='*70}")
        print(f"{self.team_name} - Hour {self.current_hour} Status Report")
        print(f"{'='*70}")
        print(f"\nProgress: {report['summary']['completion_percentage']:.1f}% complete")
        print(f"  ✅ Completed: {report['summary']['completed']}")
        print(f"  🏗️  In Progress: {report['summary']['in_progress']}")
        print(f"  🚫 Blocked: {report['summary']['blocked']}")
        print(f"  ⏸️  Pending: {report['summary']['pending']}")
        
        if self.blockers:
            print(f"\n⚠️  Active Blockers: {len(self.blockers)}")
            for blocker in self.blockers:
                print(f"  - {blocker['task_name']}: {blocker['description']}")
        
        # Show tasks by status
        print(f"\nTask Breakdown:")
        for status in TaskStatus:
            tasks = [t for t in self.tasks.values() if t['status'] == status]
            if tasks:
                print(f"\n  {status.value.upper()}:")
                for task in tasks:
                    print(f"    - {task['name']}")
    
    def run_autonomous_cycle(self):
        """
        Run one autonomous work cycle.
        This would be called periodically to make progress on tasks.
        """
        print(f"\n🤖 Running autonomous cycle for {self.team_name}")
        print(f"   Current hour: {self.current_hour}")
        
        # Get pending tasks for current hour
        pending = self.get_pending_tasks(self.current_hour)
        
        if pending:
            print(f"\n   Available tasks: {len(pending)}")
            for task_id in pending:
                print(f"     - {self.tasks[task_id]['name']}")
        else:
            print(f"\n   No tasks available (check dependencies or advance hour)")
        
        # Report status to orchestration
        self.report_to_orchestration('status_update', self.generate_status_report())
        
        self.print_status()


def main():
    """Main entry point for Team 2 agent"""
    print("="*70)
    print("Team 2 Agent: Microsoft OAuth Implementation")
    print("="*70)
    
    agent = Team2Agent()
    
    # Initial status report
    agent.print_status()
    
    # Example: Start first hour
    agent.current_hour = 1
    print(f"\n\n🚀 Starting Hour {agent.current_hour}")
    agent.run_autonomous_cycle()
    
    print("\n\n📋 Next Steps:")
    print("1. Agent is initialized and ready to work")
    print("2. Tasks are loaded from TODO.md")
    print("3. Agent can report to orchestration agent")
    print("4. Agent can request secrets when needed")
    print("\n💡 To proceed with implementation:")
    print("   - Set current_hour to advance through timeline")
    print("   - Update task statuses as work progresses")
    print("   - Agent will coordinate with orchestration automatically")


if __name__ == "__main__":
    main()
