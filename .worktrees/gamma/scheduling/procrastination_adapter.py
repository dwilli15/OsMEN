#!/usr/bin/env python3
"""
Procrastination Adaptation System

Learns from user behavior and adapts schedules.
Part of v1.5.0 - Priority & Scheduling Intelligence.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
import json


class ProcrastinationAdapter:
    """Adapt schedules based on procrastination patterns"""
    
    def __init__(self):
        self.completion_history = []
        self.procrastination_score = 0.5  # 0=never procrastinates, 1=always procrastinates
    
    def record_completion(self, task_id: str, due_date: str, 
                         completed_date: str, estimated_hours: float, 
                         actual_hours: float):
        """
        Record task completion
        
        Args:
            task_id: Task identifier
            due_date: Original due date
            completed_date: Actual completion date
            estimated_hours: Estimated effort
            actual_hours: Actual effort
        """
        try:
            due = datetime.fromisoformat(due_date)
            completed = datetime.fromisoformat(completed_date)
            
            days_before_due = (due - completed).days
            
            record = {
                'task_id': task_id,
                'due_date': due_date,
                'completed_date': completed_date,
                'days_before_due': days_before_due,
                'estimated_hours': estimated_hours,
                'actual_hours': actual_hours,
                'effort_accuracy': actual_hours / estimated_hours if estimated_hours > 0 else 1.0
            }
            
            self.completion_history.append(record)
            
            # Update procrastination score
            self._update_procrastination_score()
        
        except (ValueError, TypeError):
            pass
    
    def _update_procrastination_score(self):
        """Update procrastination score based on history"""
        if not self.completion_history:
            return
        
        # Calculate average days before due
        recent_completions = self.completion_history[-20:]  # Last 20 tasks
        
        total_days = sum(r['days_before_due'] for r in recent_completions)
        avg_days_before = total_days / len(recent_completions)
        
        # Score: 0 days before = high procrastination, 7+ days = low procrastination
        if avg_days_before <= 0:
            self.procrastination_score = 0.9  # High procrastination
        elif avg_days_before >= 7:
            self.procrastination_score = 0.1  # Low procrastination
        else:
            self.procrastination_score = 1.0 - (avg_days_before / 7.0)
    
    def adjust_deadline(self, original_deadline: str, task_type: str = 'assignment') -> str:
        """
        Adjust deadline based on procrastination patterns
        
        Args:
            original_deadline: Original due date
            task_type: Type of task
        
        Returns:
            Adjusted deadline (earlier to account for procrastination)
        """
        try:
            deadline_dt = datetime.fromisoformat(original_deadline)
            
            # Adjust based on procrastination score
            # High procrastination = move deadline earlier
            days_to_adjust = int(self.procrastination_score * 7)  # Up to 1 week earlier
            
            # More adjustment for complex tasks
            if task_type in ['project', 'exam']:
                days_to_adjust = int(days_to_adjust * 1.5)
            
            adjusted_deadline = deadline_dt - timedelta(days=days_to_adjust)
            
            return adjusted_deadline.isoformat()
        
        except (ValueError, TypeError):
            return original_deadline
    
    def get_recommended_start_date(self, due_date: str, estimated_hours: float) -> str:
        """
        Recommend when to start a task
        
        Args:
            due_date: Task due date
            estimated_hours: Estimated effort
        
        Returns:
            Recommended start date
        """
        try:
            due_dt = datetime.fromisoformat(due_date)
            
            # Calculate days needed (assuming 2 hours per day of work)
            days_needed = max(1, int(estimated_hours / 2))
            
            # Add buffer based on procrastination score
            buffer_days = int(self.procrastination_score * days_needed)
            
            total_days_needed = days_needed + buffer_days
            
            start_date = due_dt - timedelta(days=total_days_needed)
            
            return start_date.isoformat()
        
        except (ValueError, TypeError):
            return datetime.now().isoformat()
    
    def get_procrastination_report(self) -> Dict[str, Any]:
        """Get procrastination analysis report"""
        if not self.completion_history:
            return {'message': 'No completion history yet'}
        
        recent = self.completion_history[-20:]
        
        avg_days_before = sum(r['days_before_due'] for r in recent) / len(recent)
        avg_effort_accuracy = sum(r['effort_accuracy'] for r in recent) / len(recent)
        
        return {
            'procrastination_score': round(self.procrastination_score, 2),
            'interpretation': self._interpret_score(),
            'avg_days_before_due': round(avg_days_before, 1),
            'avg_effort_accuracy': round(avg_effort_accuracy, 2),
            'total_tasks_tracked': len(self.completion_history),
            'recommendations': self._get_recommendations()
        }
    
    def _interpret_score(self) -> str:
        """Interpret procrastination score"""
        if self.procrastination_score >= 0.7:
            return "High procrastination tendency - consider earlier deadlines"
        elif self.procrastination_score >= 0.4:
            return "Moderate procrastination - some buffer time recommended"
        else:
            return "Low procrastination - good time management"
    
    def _get_recommendations(self) -> List[str]:
        """Get recommendations based on patterns"""
        recommendations = []
        
        if self.procrastination_score >= 0.7:
            recommendations.append("Set personal deadlines 1 week before actual due dates")
            recommendations.append("Break large tasks into smaller daily goals")
            recommendations.append("Use accountability partners or study groups")
        elif self.procrastination_score >= 0.4:
            recommendations.append("Add 2-3 day buffer to deadlines")
            recommendations.append("Start complex projects at least 2 weeks early")
        else:
            recommendations.append("Current time management is effective")
            recommendations.append("Continue current planning strategies")
        
        return recommendations


def main():
    """Test procrastination adapter"""
    adapter = ProcrastinationAdapter()
    
    print("Procrastination Adaptation System")
    print("=" * 50)
    
    # Simulate some completion history
    adapter.record_completion('task1', '2024-10-15', '2024-10-14', 5, 6)  # 1 day before
    adapter.record_completion('task2', '2024-10-20', '2024-10-19', 4, 5)  # 1 day before
    adapter.record_completion('task3', '2024-10-25', '2024-10-20', 10, 12)  # 5 days before
    
    report = adapter.get_procrastination_report()
    print("\nProcrastination Analysis:")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
