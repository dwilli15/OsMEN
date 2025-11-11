#!/usr/bin/env python3
"""
Intelligent Snooze Manager

Smart snooze functionality with learning and pattern recognition.
Part of v1.6.0 - Adaptive Reminders & Health Integration.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
from pathlib import Path


class IntelligentSnoozeManager:
    """Manage intelligent snoozing with pattern learning"""
    
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.snooze_patterns_path = self.repo_root / ".copilot" / "snooze_patterns.json"
        self.patterns = self._load_patterns()
        
        # Snooze duration presets (in hours)
        self.presets = {
            "quick": 1,
            "short": 4,
            "standard": 24,
            "long": 72,
            "weekend": 120  # ~5 days
        }
    
    def _load_patterns(self) -> Dict[str, Any]:
        """Load snooze patterns"""
        if self.snooze_patterns_path.exists():
            with open(self.snooze_patterns_path, 'r') as f:
                return json.load(f)
        return {"snooze_history": [], "user_preferences": {}}
    
    def _save_patterns(self):
        """Save snooze patterns"""
        self.snooze_patterns_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.snooze_patterns_path, 'w') as f:
            json.dump(self.patterns, f, indent=2)
    
    def calculate_intelligent_snooze_duration(self, 
                                             reminder: Dict[str, Any],
                                             task: Dict[str, Any]) -> int:
        """
        Calculate optimal snooze duration based on patterns
        
        Args:
            reminder: Reminder dictionary
            task: Task dictionary
        
        Returns:
            Snooze duration in hours
        """
        # Get task type and time context
        task_type = task.get('type', 'assignment')
        snooze_count = reminder.get('snooze_count', 0)
        
        # Check user's historical preference for this task type
        user_pref = self._get_user_preference(task_type)
        if user_pref:
            return user_pref
        
        # Calculate based on due date proximity
        due_date_str = task.get('date') or task.get('due_date')
        if due_date_str:
            try:
                due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                hours_until_due = (due_date - datetime.now()).total_seconds() / 3600
                
                # Adaptive snooze based on time remaining
                if hours_until_due <= 24:
                    return self.presets["quick"]  # 1 hour
                elif hours_until_due <= 48:
                    return self.presets["short"]  # 4 hours
                elif hours_until_due <= 168:  # 1 week
                    return self.presets["standard"]  # 24 hours
                else:
                    return self.presets["long"]  # 72 hours
            except (ValueError, TypeError):
                pass
        
        # Decrease snooze duration with each snooze (urgency increases)
        if snooze_count == 0:
            return self.presets["standard"]  # 24 hours
        elif snooze_count == 1:
            return self.presets["short"]  # 4 hours
        else:
            return self.presets["quick"]  # 1 hour
    
    def _get_user_preference(self, task_type: str) -> Optional[int]:
        """Get user's preferred snooze duration for task type"""
        prefs = self.patterns.get("user_preferences", {})
        return prefs.get(task_type)
    
    def record_snooze(self, reminder_id: str, task: Dict[str, Any], 
                     duration_hours: int):
        """Record snooze action for learning"""
        snooze_record = {
            "reminder_id": reminder_id,
            "task_type": task.get('type', 'unknown'),
            "task_priority": task.get('priority', 'medium'),
            "duration_hours": duration_hours,
            "timestamp": datetime.now().isoformat(),
            "time_of_day": datetime.now().hour
        }
        
        self.patterns.setdefault("snooze_history", []).append(snooze_record)
        
        # Update preferences based on patterns
        self._update_preferences()
        self._save_patterns()
    
    def _update_preferences(self):
        """Update user preferences based on snooze history"""
        history = self.patterns.get("snooze_history", [])
        if len(history) < 5:
            return  # Need more data
        
        # Calculate most common snooze duration per task type
        type_durations = {}
        for record in history[-50:]:  # Last 50 snoozes
            task_type = record.get('task_type', 'unknown')
            duration = record.get('duration_hours', 24)
            
            if task_type not in type_durations:
                type_durations[task_type] = []
            type_durations[task_type].append(duration)
        
        # Update preferences with median duration
        preferences = {}
        for task_type, durations in type_durations.items():
            if durations:
                durations.sort()
                median_idx = len(durations) // 2
                preferences[task_type] = durations[median_idx]
        
        self.patterns["user_preferences"] = preferences
    
    def suggest_snooze_options(self, reminder: Dict[str, Any],
                               task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Suggest snooze duration options
        
        Returns:
            List of snooze options with labels
        """
        intelligent_duration = self.calculate_intelligent_snooze_duration(reminder, task)
        
        options = [
            {
                "label": "Quick (1 hour)",
                "duration_hours": self.presets["quick"],
                "recommended": intelligent_duration == self.presets["quick"]
            },
            {
                "label": "Short (4 hours)",
                "duration_hours": self.presets["short"],
                "recommended": intelligent_duration == self.presets["short"]
            },
            {
                "label": "Tomorrow (24 hours)",
                "duration_hours": self.presets["standard"],
                "recommended": intelligent_duration == self.presets["standard"]
            },
            {
                "label": "Later this week (72 hours)",
                "duration_hours": self.presets["long"],
                "recommended": intelligent_duration == self.presets["long"]
            }
        ]
        
        # Check if it's Friday - add weekend option
        if datetime.now().weekday() == 4:  # Friday
            options.append({
                "label": "After weekend (120 hours)",
                "duration_hours": self.presets["weekend"],
                "recommended": False
            })
        
        return options
    
    def should_allow_snooze(self, reminder: Dict[str, Any],
                           task: Dict[str, Any]) -> bool:
        """
        Determine if snoozing should be allowed
        
        Returns:
            True if snooze is allowed
        """
        snooze_count = reminder.get('snooze_count', 0)
        
        # Max snoozes reached?
        if snooze_count >= 5:
            return False
        
        # Too close to due date?
        due_date_str = task.get('date') or task.get('due_date')
        if due_date_str:
            try:
                due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                hours_until_due = (due_date - datetime.now()).total_seconds() / 3600
                
                # Don't allow snooze if < 2 hours until due
                if hours_until_due < 2:
                    return False
            except (ValueError, TypeError):
                pass
        
        return True
    
    def get_snooze_analytics(self) -> Dict[str, Any]:
        """Get analytics on snooze patterns"""
        history = self.patterns.get("snooze_history", [])
        
        if not history:
            return {
                "total_snoozes": 0,
                "average_duration_hours": 0,
                "most_common_time": "N/A",
                "snooze_by_task_type": {}
            }
        
        # Calculate statistics
        total = len(history)
        avg_duration = sum(r.get('duration_hours', 0) for r in history) / total
        
        # Most common time of day
        times = [r.get('time_of_day', 12) for r in history]
        most_common_time = max(set(times), key=times.count)
        
        # By task type
        by_type = {}
        for record in history:
            task_type = record.get('task_type', 'unknown')
            by_type[task_type] = by_type.get(task_type, 0) + 1
        
        return {
            "total_snoozes": total,
            "average_duration_hours": round(avg_duration, 1),
            "most_common_time": f"{most_common_time}:00",
            "snooze_by_task_type": by_type
        }


def main():
    print("Intelligent Snooze Manager - Ready")


if __name__ == "__main__":
    main()
