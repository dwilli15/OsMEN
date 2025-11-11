"""
Todoist API integration for task management.
Real API implementation using official Todoist SDK.
"""

import os
from datetime import datetime
from typing import List, Dict, Optional

try:
    from todoist_api_python.api import TodoistAPI
    TODOIST_AVAILABLE = True
except ImportError:
    TODOIST_AVAILABLE = False


class TodoistClient:
    """
    Todoist API client for task synchronization.
    Uses official Todoist SDK with real API calls.
    """
    
    def __init__(self, api_token: Optional[str] = None):
        """Initialize Todoist client with API token."""
        self.api_token = api_token or os.getenv('TODOIST_API_TOKEN')
        
        if not TODOIST_AVAILABLE:
            print("Warning: todoist-api-python not installed. Using manual mode.")
            self.client = None
            return
            
        if self.api_token:
            try:
                self.client = TodoistAPI(self.api_token)
            except Exception as e:
                print(f"Error initializing Todoist: {e}")
                self.client = None
        else:
            print("Warning: No Todoist API token provided. Using manual mode.")
            self.client = None
    
    def get_tasks(self, project_id: Optional[str] = None, 
                  label: Optional[str] = None) -> List[Dict]:
        """
        Get tasks from Todoist.
        
        Args:
            project_id: Filter by project ID
            label: Filter by label
            
        Returns:
            List of task dictionaries
        """
        if not self.client:
            return []
            
        try:
            tasks = self.client.get_tasks(
                project_id=project_id,
                label=label
            )
            return [self._parse_todoist_task(t) for t in tasks]
        except Exception as e:
            print(f"Error getting Todoist tasks: {e}")
            return []
    
    def create_task(self, content: str, due_date: Optional[str] = None,
                   priority: int = 1, project_id: Optional[str] = None,
                   labels: Optional[List[str]] = None) -> Optional[Dict]:
        """
        Create a new task in Todoist.
        
        Args:
            content: Task content/title
            due_date: Due date string (YYYY-MM-DD)
            priority: Priority 1-4 (4 is highest)
            project_id: Project ID
            labels: List of label names
            
        Returns:
            Created task dict
        """
        if not self.client:
            return None
            
        try:
            task = self.client.add_task(
                content=content,
                due_date=due_date,
                priority=priority,
                project_id=project_id,
                labels=labels or []
            )
            return self._parse_todoist_task(task)
        except Exception as e:
            print(f"Error creating Todoist task: {e}")
            return None
    
    def update_task(self, task_id: str, content: Optional[str] = None,
                   due_date: Optional[str] = None, priority: Optional[int] = None) -> bool:
        """
        Update an existing Todoist task.
        
        Args:
            task_id: Task ID to update
            content: New content
            due_date: New due date
            priority: New priority (1-4)
            
        Returns:
            Success boolean
        """
        if not self.client:
            return False
            
        try:
            self.client.update_task(
                task_id=task_id,
                content=content,
                due_date=due_date,
                priority=priority
            )
            return True
        except Exception as e:
            print(f"Error updating Todoist task: {e}")
            return False
    
    def complete_task(self, task_id: str) -> bool:
        """
        Complete a Todoist task.
        
        Args:
            task_id: Task ID to complete
            
        Returns:
            Success boolean
        """
        if not self.client:
            return False
            
        try:
            self.client.close_task(task_id=task_id)
            return True
        except Exception as e:
            print(f"Error completing Todoist task: {e}")
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a Todoist task.
        
        Args:
            task_id: Task ID to delete
            
        Returns:
            Success boolean
        """
        if not self.client:
            return False
            
        try:
            self.client.delete_task(task_id=task_id)
            return True
        except Exception as e:
            print(f"Error deleting Todoist task: {e}")
            return False
    
    def _parse_todoist_task(self, todoist_task) -> Dict:
        """Parse Todoist task object into dict."""
        # Map Todoist priority (4=highest) to OsMEN priority
        priority_map = {
            4: 'critical',
            3: 'high',
            2: 'medium',
            1: 'low'
        }
        
        return {
            'id': todoist_task.id,
            'title': todoist_task.content,
            'due_date': todoist_task.due.date if todoist_task.due else None,
            'priority': priority_map.get(todoist_task.priority, 'low'),
            'is_completed': todoist_task.is_completed,
            'project_id': todoist_task.project_id,
            'labels': todoist_task.labels,
            'source': 'todoist',
            'url': todoist_task.url
        }
    
    def sync_task_to_todoist(self, task: Dict) -> bool:
        """
        Sync task from OsMEN to Todoist.
        
        Args:
            task: Task dictionary
            
        Returns:
            Success boolean
        """
        if not self.client:
            return False
            
        # Map OsMEN priority to Todoist priority
        priority_map = {
            'critical': 4,
            'high': 3,
            'medium': 2,
            'low': 1
        }
        
        todoist_priority = priority_map.get(task.get('priority', 'low'), 1)
        
        if task.get('todoist_id'):
            # Update existing
            return self.update_task(
                task_id=task['todoist_id'],
                content=task.get('title'),
                due_date=task.get('due_date'),
                priority=todoist_priority
            )
        else:
            # Create new
            result = self.create_task(
                content=task.get('title', 'Untitled'),
                due_date=task.get('due_date'),
                priority=todoist_priority,
                labels=task.get('labels', [])
            )
            return result is not None
