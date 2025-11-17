#!/usr/bin/env python3
"""
Personal Assistant Agent
Provides task management, scheduling, reminders, and productivity assistance
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)


class PersonalAssistantAgent:
    """Personal Assistant Agent for productivity and task management."""
    
    def __init__(self):
        """Initialize the Personal Assistant Agent."""
        logger.info("PersonalAssistantAgent initialized successfully")
        self.tasks = []
        self.reminders = []
        self.schedule = []
    
    def create_task(self, title: str, description: str = "", priority: str = "medium", 
                   due_date: Optional[str] = None) -> Dict:
        """Create a new task.
        
        Args:
            title: Task title
            description: Task description
            priority: Priority level (low, medium, high, urgent)
            due_date: Due date in ISO format
            
        Returns:
            Dictionary with task details
        """
        task = {
            "id": len(self.tasks) + 1,
            "title": title,
            "description": description,
            "priority": priority,
            "due_date": due_date,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        self.tasks.append(task)
        logger.info(f"Created task: {title}")
        return task
    
    def get_tasks(self, status: Optional[str] = None, priority: Optional[str] = None) -> List[Dict]:
        """Get tasks filtered by status and/or priority.
        
        Args:
            status: Filter by status (pending, in_progress, completed)
            priority: Filter by priority (low, medium, high, urgent)
            
        Returns:
            List of filtered tasks
        """
        filtered_tasks = self.tasks
        
        if status:
            filtered_tasks = [t for t in filtered_tasks if t["status"] == status]
        if priority:
            filtered_tasks = [t for t in filtered_tasks if t["priority"] == priority]
        
        return filtered_tasks
    
    def set_reminder(self, title: str, time: str, message: str = "") -> Dict:
        """Set a reminder.
        
        Args:
            title: Reminder title
            time: Time in ISO format
            message: Optional reminder message
            
        Returns:
            Dictionary with reminder details
        """
        reminder = {
            "id": len(self.reminders) + 1,
            "title": title,
            "time": time,
            "message": message,
            "created_at": datetime.now().isoformat()
        }
        self.reminders.append(reminder)
        logger.info(f"Set reminder: {title} at {time}")
        return reminder
    
    def schedule_event(self, title: str, start_time: str, end_time: str, 
                      description: str = "") -> Dict:
        """Schedule a calendar event.
        
        Args:
            title: Event title
            start_time: Start time in ISO format
            end_time: End time in ISO format
            description: Event description
            
        Returns:
            Dictionary with event details
        """
        event = {
            "id": len(self.schedule) + 1,
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "description": description,
            "created_at": datetime.now().isoformat()
        }
        self.schedule.append(event)
        logger.info(f"Scheduled event: {title} from {start_time} to {end_time}")
        return event
    
    def get_daily_summary(self) -> Dict:
        """Generate daily summary of tasks, reminders, and schedule.
        
        Returns:
            Dictionary with daily summary
        """
        today = datetime.now().date().isoformat()
        
        # Get today's tasks
        today_tasks = [
            t for t in self.tasks 
            if t.get("due_date") and t["due_date"].startswith(today)
        ]
        
        # Get today's reminders
        today_reminders = [
            r for r in self.reminders
            if r.get("time") and r["time"].startswith(today)
        ]
        
        # Get today's schedule
        today_schedule = [
            e for e in self.schedule
            if e.get("start_time") and e["start_time"].startswith(today)
        ]
        
        summary = {
            "date": today,
            "tasks": {
                "total": len(today_tasks),
                "pending": len([t for t in today_tasks if t["status"] == "pending"]),
                "completed": len([t for t in today_tasks if t["status"] == "completed"])
            },
            "reminders": len(today_reminders),
            "events": len(today_schedule),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("Generated daily summary")
        return summary
    
    def generate_assistant_report(self) -> Dict:
        """Generate comprehensive assistant report.
        
        Returns:
            Dictionary with assistant status and statistics
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "operational",
            "statistics": {
                "total_tasks": len(self.tasks),
                "pending_tasks": len([t for t in self.tasks if t["status"] == "pending"]),
                "completed_tasks": len([t for t in self.tasks if t["status"] == "completed"]),
                "total_reminders": len(self.reminders),
                "scheduled_events": len(self.schedule)
            },
            "daily_summary": self.get_daily_summary()
        }


if __name__ == "__main__":
    # Test the agent
    logging.basicConfig(level=logging.INFO)
    
    agent = PersonalAssistantAgent()
    
    # Create sample tasks
    agent.create_task("Review project proposal", priority="high", 
                     due_date=datetime.now().date().isoformat())
    agent.create_task("Prepare presentation", priority="medium")
    agent.create_task("Send follow-up emails", priority="low")
    
    # Set reminders
    agent.set_reminder("Team meeting", (datetime.now() + timedelta(hours=2)).isoformat(), 
                      "Don't forget the weekly sync")
    
    # Schedule events
    agent.schedule_event(
        "Project kickoff", 
        (datetime.now() + timedelta(hours=1)).isoformat(),
        (datetime.now() + timedelta(hours=2)).isoformat(),
        "New project initialization meeting"
    )
    
    # Generate report
    report = agent.generate_assistant_report()
    print(json.dumps(report, indent=2))
