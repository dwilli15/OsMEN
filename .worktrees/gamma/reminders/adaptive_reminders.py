#!/usr/bin/env python3
"""
Adaptive Reminder System

Intelligent reminder system that learns from user behavior.
Part of v1.6.0 - Adaptive Reminders & Health Integration.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
from pathlib import Path


class AdaptiveReminderSystem:
    """Manage adaptive reminders with behavioral learning"""
    
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.completion_history_path = self.repo_root / ".copilot" / "completion_history.json"
        self.reminder_config_path = self.repo_root / ".copilot" / "reminder_config.json"
        
        self.completion_history = self._load_completion_history()
        self.reminder_config = self._load_reminder_config()
        
        # Escalation levels
        self.escalation_levels = {
            'gentle': {'frequency_hours': 24, 'channels': ['dashboard']},
            'moderate': {'frequency_hours': 12, 'channels': ['dashboard', 'email']},
            'urgent': {'frequency_hours': 6, 'channels': ['dashboard', 'email', 'notification']},
            'critical': {'frequency_hours': 2, 'channels': ['dashboard', 'email', 'notification']},
        }
    
    def _load_completion_history(self) -> Dict[str, Any]:
        """Load task completion history"""
        if self.completion_history_path.exists():
            with open(self.completion_history_path, 'r') as f:
                return json.load(f)
        return {"tasks": [], "reminders": []}
    
    def _load_reminder_config(self) -> Dict[str, Any]:
        """Load reminder configuration"""
        if self.reminder_config_path.exists():
            with open(self.reminder_config_path, 'r') as f:
                return json.load(f)
        
        return {
            "enabled": True,
            "default_advance_days": 3,
            "snooze_duration_hours": 24,
            "max_reminders_per_task": 5,
            "quiet_hours": {"start": "22:00", "end": "08:00"},
            "preferred_channels": ["email", "dashboard"]
        }
    
    def _save_completion_history(self):
        """Save completion history"""
        self.completion_history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.completion_history_path, 'w') as f:
            json.dump(self.completion_history, f, indent=2)
    
    def calculate_optimal_reminder_time(self, task: Dict[str, Any]) -> datetime:
        """Calculate optimal reminder time based on task and history"""
        due_date_str = task.get('date') or task.get('due_date')
        if not due_date_str:
            return datetime.now() + timedelta(hours=1)
        
        try:
            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return datetime.now() + timedelta(hours=1)
        
        task_type = task.get('type', 'assignment')
        avg_days_before = self._get_average_completion_timing(task_type)
        base_advance_days = max(1, min(avg_days_before + 1, 7))
        
        priority = task.get('priority', 'medium')
        if priority == 'critical':
            base_advance_days += 2
        elif priority == 'high':
            base_advance_days += 1
        
        reminder_time = due_date - timedelta(days=base_advance_days)
        
        if reminder_time < datetime.now():
            reminder_time = datetime.now() + timedelta(hours=1)
        
        return self._adjust_for_quiet_hours(reminder_time)
    
    def _get_average_completion_timing(self, task_type: str) -> int:
        """Get average days before due date user completes this type"""
        relevant_completions = [
            t for t in self.completion_history.get("tasks", [])
            if t.get('type') == task_type and t.get('days_before_due') is not None
        ]
        
        if not relevant_completions:
            return 3
        
        avg = sum(t['days_before_due'] for t in relevant_completions) / len(relevant_completions)
        return max(1, int(avg))
    
    def _adjust_for_quiet_hours(self, reminder_time: datetime) -> datetime:
        """Adjust reminder to avoid quiet hours"""
        quiet_start = self.reminder_config["quiet_hours"]["start"]
        quiet_end = self.reminder_config["quiet_hours"]["end"]
        
        quiet_start_hour = int(quiet_start.split(':')[0])
        quiet_end_hour = int(quiet_end.split(':')[0])
        
        hour = reminder_time.hour
        
        if quiet_start_hour > quiet_end_hour:
            if hour >= quiet_start_hour or hour < quiet_end_hour:
                reminder_time = reminder_time.replace(hour=quiet_end_hour, minute=0)
        else:
            if quiet_start_hour <= hour < quiet_end_hour:
                reminder_time = reminder_time.replace(hour=quiet_end_hour, minute=0)
        
        return reminder_time
    
    def create_reminder(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create a reminder for a task"""
        reminder_time = self.calculate_optimal_reminder_time(task)
        
        reminder = {
            "id": f"reminder_{task.get('id', 'unknown')}_{datetime.now().timestamp()}",
            "task_id": task.get('id'),
            "task_title": task.get('title'),
            "reminder_time": reminder_time.isoformat(),
            "created_at": datetime.now().isoformat(),
            "status": "scheduled",
            "channels": self.reminder_config.get("preferred_channels", ["email"]),
            "escalation_level": self._determine_escalation_level(task, reminder_time),
            "snooze_count": 0,
            "sent_count": 0
        }
        
        self.completion_history.setdefault("reminders", []).append(reminder)
        self._save_completion_history()
        
        return reminder
    
    def _determine_escalation_level(self, task: Dict[str, Any], reminder_time: datetime) -> str:
        """Determine initial escalation level"""
        due_date_str = task.get('date') or task.get('due_date')
        if not due_date_str:
            return 'moderate'
        
        try:
            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
            days_until_due = (due_date - reminder_time).days
            
            priority = task.get('priority', 'medium')
            
            if priority == 'critical' or days_until_due <= 1:
                return 'critical'
            elif priority == 'high' or days_until_due <= 2:
                return 'urgent'
            elif days_until_due <= 5:
                return 'moderate'
            else:
                return 'gentle'
        except (ValueError, TypeError):
            return 'moderate'
    
    def snooze_reminder(self, reminder_id: str, duration_hours: int = None) -> bool:
        """Snooze a reminder"""
        if duration_hours is None:
            duration_hours = self.reminder_config["snooze_duration_hours"]
        
        for reminder in self.completion_history.get("reminders", []):
            if reminder["id"] == reminder_id:
                old_time = datetime.fromisoformat(reminder["reminder_time"])
                new_time = old_time + timedelta(hours=duration_hours)
                
                reminder["reminder_time"] = new_time.isoformat()
                reminder["snooze_count"] += 1
                reminder["status"] = "snoozed"
                
                self._save_completion_history()
                return True
        
        return False
    
    def escalate_reminder(self, reminder_id: str) -> bool:
        """Escalate reminder to next level"""
        level_order = ['gentle', 'moderate', 'urgent', 'critical']
        
        for reminder in self.completion_history.get("reminders", []):
            if reminder["id"] == reminder_id:
                current_level = reminder.get("escalation_level", "gentle")
                
                if current_level in level_order:
                    current_index = level_order.index(current_level)
                    if current_index < len(level_order) - 1:
                        new_level = level_order[current_index + 1]
                        reminder["escalation_level"] = new_level
                        reminder["channels"] = self.escalation_levels[new_level]["channels"]
                        
                        self._save_completion_history()
                        return True
        
        return False
    
    def get_due_reminders(self) -> List[Dict[str, Any]]:
        """Get reminders that are due now"""
        now = datetime.now()
        due_reminders = []
        
        for reminder in self.completion_history.get("reminders", []):
            if reminder["status"] in ["scheduled", "snoozed"]:
                reminder_time = datetime.fromisoformat(reminder["reminder_time"])
                
                if reminder_time <= now:
                    if reminder["sent_count"] < self.reminder_config["max_reminders_per_task"]:
                        due_reminders.append(reminder)
        
        return due_reminders


def main():
    print("Adaptive Reminder System - Ready")


if __name__ == "__main__":
    main()
