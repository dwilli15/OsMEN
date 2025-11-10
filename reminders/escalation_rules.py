#!/usr/bin/env python3
"""
Enhanced Escalation Rules Engine

Advanced escalation logic with time-based and behavior-based rules.
Part of v1.6.0 - Adaptive Reminders & Health Integration.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
from pathlib import Path


class EscalationRulesEngine:
    """Manage complex escalation rules for reminders"""
    
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.rules_path = self.repo_root / ".copilot" / "escalation_rules.json"
        self.rules = self._load_rules()
    
    def _load_rules(self) -> Dict[str, Any]:
        """Load escalation rules"""
        if self.rules_path.exists():
            with open(self.rules_path, 'r') as f:
                return json.load(f)
        
        # Default escalation rules
        return {
            "time_based": {
                "days_until_due": [
                    {"threshold": 1, "level": "critical", "frequency_hours": 2},
                    {"threshold": 2, "level": "urgent", "frequency_hours": 6},
                    {"threshold": 5, "level": "moderate", "frequency_hours": 12},
                    {"threshold": 999, "level": "gentle", "frequency_hours": 24}
                ]
            },
            "behavior_based": {
                "snooze_escalation": {
                    "enabled": True,
                    "thresholds": [
                        {"snooze_count": 1, "action": "none"},
                        {"snooze_count": 2, "action": "escalate_one_level"},
                        {"snooze_count": 4, "action": "escalate_to_urgent"},
                        {"snooze_count": 6, "action": "escalate_to_critical"}
                    ]
                },
                "ignore_escalation": {
                    "enabled": True,
                    "threshold_hours": 48,
                    "action": "escalate_one_level"
                }
            },
            "priority_multipliers": {
                "critical": 2.0,
                "high": 1.5,
                "medium": 1.0,
                "low": 0.5
            },
            "channel_rules": {
                "gentle": ["dashboard"],
                "moderate": ["dashboard", "email"],
                "urgent": ["dashboard", "email", "notification"],
                "critical": ["dashboard", "email", "notification", "sms"]
            }
        }
    
    def _save_rules(self):
        """Save escalation rules"""
        self.rules_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.rules_path, 'w') as f:
            json.dump(self.rules, f, indent=2)
    
    def calculate_escalation_level(self, task: Dict[str, Any], 
                                   reminder: Dict[str, Any]) -> str:
        """
        Calculate escalation level based on multiple factors
        
        Args:
            task: Task dictionary
            reminder: Reminder dictionary
        
        Returns:
            Escalation level string
        """
        # Time-based escalation
        time_level = self._calculate_time_based_level(task)
        
        # Behavior-based escalation
        behavior_level = self._calculate_behavior_based_level(reminder)
        
        # Priority adjustment
        priority_level = self._adjust_for_priority(task, time_level)
        
        # Take the highest escalation level
        levels = ['gentle', 'moderate', 'urgent', 'critical']
        max_level = max(
            levels.index(time_level),
            levels.index(behavior_level),
            levels.index(priority_level)
        )
        
        return levels[max_level]
    
    def _calculate_time_based_level(self, task: Dict[str, Any]) -> str:
        """Calculate escalation level based on time until due"""
        due_date_str = task.get('date') or task.get('due_date')
        if not due_date_str:
            return 'moderate'
        
        try:
            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
            days_until_due = (due_date - datetime.now()).days
            
            for rule in self.rules["time_based"]["days_until_due"]:
                if days_until_due <= rule["threshold"]:
                    return rule["level"]
            
            return 'gentle'
        except (ValueError, TypeError):
            return 'moderate'
    
    def _calculate_behavior_based_level(self, reminder: Dict[str, Any]) -> str:
        """Calculate escalation based on user behavior"""
        current_level = reminder.get('escalation_level', 'gentle')
        snooze_count = reminder.get('snooze_count', 0)
        
        # Snooze-based escalation
        if self.rules["behavior_based"]["snooze_escalation"]["enabled"]:
            for threshold in self.rules["behavior_based"]["snooze_escalation"]["thresholds"]:
                if snooze_count >= threshold["snooze_count"]:
                    action = threshold["action"]
                    
                    if action == "escalate_one_level":
                        current_level = self._escalate_one_level(current_level)
                    elif action == "escalate_to_urgent":
                        current_level = "urgent"
                    elif action == "escalate_to_critical":
                        current_level = "critical"
        
        # Ignore-based escalation
        if self.rules["behavior_based"]["ignore_escalation"]["enabled"]:
            last_sent = reminder.get('last_sent')
            if last_sent:
                last_sent_dt = datetime.fromisoformat(last_sent)
                hours_since = (datetime.now() - last_sent_dt).total_seconds() / 3600
                
                threshold_hours = self.rules["behavior_based"]["ignore_escalation"]["threshold_hours"]
                if hours_since > threshold_hours:
                    current_level = self._escalate_one_level(current_level)
        
        return current_level
    
    def _adjust_for_priority(self, task: Dict[str, Any], base_level: str) -> str:
        """Adjust escalation level based on task priority"""
        priority = task.get('priority', 'medium')
        multiplier = self.rules["priority_multipliers"].get(priority, 1.0)
        
        if multiplier >= 2.0 and base_level in ['gentle', 'moderate']:
            return 'urgent'
        elif multiplier >= 1.5 and base_level == 'gentle':
            return 'moderate'
        
        return base_level
    
    def _escalate_one_level(self, current_level: str) -> str:
        """Escalate to next level"""
        levels = ['gentle', 'moderate', 'urgent', 'critical']
        if current_level in levels:
            idx = levels.index(current_level)
            if idx < len(levels) - 1:
                return levels[idx + 1]
        return current_level
    
    def get_channels_for_level(self, level: str) -> List[str]:
        """Get notification channels for escalation level"""
        return self.rules["channel_rules"].get(level, ["email"])
    
    def get_frequency_for_level(self, level: str) -> int:
        """Get reminder frequency in hours for level"""
        for rule in self.rules["time_based"]["days_until_due"]:
            if rule["level"] == level:
                return rule["frequency_hours"]
        return 24


def main():
    print("Enhanced Escalation Rules Engine - Ready")


if __name__ == "__main__":
    main()
