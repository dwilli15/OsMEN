#!/usr/bin/env python3
"""
Manual Override Support

Allows users to manually adjust priorities and schedules.
Part of v1.5.0 - Priority & Scheduling Intelligence.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import json


class ManualOverrideManager:
    """Manage manual overrides for priorities and schedules"""
    
    def __init__(self):
        self.overrides = {}
        self.override_history = []
    
    def set_priority_override(self, task_id: str, new_priority: str, 
                             reason: str = None) -> bool:
        """
        Manually override task priority
        
        Args:
            task_id: Task identifier
            new_priority: New priority (critical/high/medium/low)
            reason: Reason for override
        
        Returns:
            True if successful
        """
        if new_priority not in ['critical', 'high', 'medium', 'low']:
            return False
        
        override = {
            'type': 'priority',
            'task_id': task_id,
            'new_value': new_priority,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'active': True
        }
        
        self.overrides[f"priority_{task_id}"] = override
        self.override_history.append(override.copy())
        
        return True
    
    def set_date_override(self, task_id: str, new_date: str, 
                         reason: str = None) -> bool:
        """
        Manually override task due date
        
        Args:
            task_id: Task identifier
            new_date: New due date (ISO format)
            reason: Reason for override
        
        Returns:
            True if successful
        """
        override = {
            'type': 'due_date',
            'task_id': task_id,
            'new_value': new_date,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'active': True
        }
        
        self.overrides[f"date_{task_id}"] = override
        self.override_history.append(override.copy())
        
        return True
    
    def set_effort_override(self, task_id: str, estimated_hours: float,
                           reason: str = None) -> bool:
        """
        Manually override effort estimate
        
        Args:
            task_id: Task identifier
            estimated_hours: Estimated hours
            reason: Reason for override
        
        Returns:
            True if successful
        """
        override = {
            'type': 'effort',
            'task_id': task_id,
            'new_value': estimated_hours,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'active': True
        }
        
        self.overrides[f"effort_{task_id}"] = override
        self.override_history.append(override.copy())
        
        return True
    
    def remove_override(self, override_key: str) -> bool:
        """Remove an override"""
        if override_key in self.overrides:
            self.overrides[override_key]['active'] = False
            del self.overrides[override_key]
            return True
        return False
    
    def apply_overrides(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply overrides to a task
        
        Args:
            task: Original task
        
        Returns:
            Task with overrides applied
        """
        task_id = task.get('id', task.get('title'))
        modified_task = task.copy()
        
        # Apply priority override
        priority_key = f"priority_{task_id}"
        if priority_key in self.overrides:
            modified_task['priority'] = self.overrides[priority_key]['new_value']
            modified_task['priority_overridden'] = True
        
        # Apply date override
        date_key = f"date_{task_id}"
        if date_key in self.overrides:
            modified_task['due_date'] = self.overrides[date_key]['new_value']
            modified_task['date_overridden'] = True
        
        # Apply effort override
        effort_key = f"effort_{task_id}"
        if effort_key in self.overrides:
            modified_task['estimated_hours'] = self.overrides[effort_key]['new_value']
            modified_task['effort_overridden'] = True
        
        return modified_task
    
    def get_override_summary(self) -> Dict[str, Any]:
        """Get summary of all active overrides"""
        summary = {
            'total_active': len(self.overrides),
            'by_type': {},
            'overrides': list(self.overrides.values())
        }
        
        for override in self.overrides.values():
            override_type = override['type']
            summary['by_type'][override_type] = summary['by_type'].get(override_type, 0) + 1
        
        return summary


def main():
    """Test manual override manager"""
    manager = ManualOverrideManager()
    
    print("Manual Override Support")
    print("=" * 50)
    
    # Test overrides
    manager.set_priority_override('task1', 'critical', 'Urgent deadline approaching')
    manager.set_date_override('task2', '2024-11-15', 'Professor extended deadline')
    manager.set_effort_override('task3', 10.5, 'More complex than initially thought')
    
    summary = manager.get_override_summary()
    print("\nOverride Summary:")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
