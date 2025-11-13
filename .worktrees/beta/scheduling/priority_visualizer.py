#!/usr/bin/env python3
"""
Priority Visualization

Generate visual representations of task priorities.
Part of v1.5.0 - Priority & Scheduling Intelligence.
"""

from typing import List, Dict, Any
import json


class PriorityVisualizer:
    """Generate priority visualizations"""
    
    def __init__(self):
        self.priority_colors = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }
    
    def generate_text_view(self, tasks: List[Dict[str, Any]]) -> str:
        """
        Generate text-based priority view
        
        Args:
            tasks: List of tasks with priority scores
        
        Returns:
            Formatted text view
        """
        output = "# Task Priority Dashboard\n\n"
        
        # Group by priority
        grouped = self._group_by_priority(tasks)
        
        for priority_level in ['critical', 'high', 'medium', 'low']:
            if priority_level in grouped and grouped[priority_level]:
                icon = self.priority_colors[priority_level]
                output += f"## {icon} {priority_level.upper()} Priority\n\n"
                
                for task in grouped[priority_level]:
                    score = task.get('priority_score', 0)
                    title = task.get('title', 'Untitled')
                    due = task.get('date') or task.get('due_date', 'No due date')
                    
                    output += f"- [{score:.0f}/100] {title}\n"
                    output += f"  Due: {due}\n"
                    if task.get('estimated_hours'):
                        output += f"  Effort: {task['estimated_hours']}h\n"
                    output += "\n"
        
        return output
    
    def generate_timeline_view(self, tasks: List[Dict[str, Any]]) -> str:
        """Generate chronological timeline view"""
        output = "# Timeline View\n\n"
        
        # Sort by date
        sorted_tasks = sorted(
            tasks,
            key=lambda x: x.get('date') or x.get('due_date') or '9999-99-99'
        )
        
        current_date = None
        for task in sorted_tasks:
            task_date = task.get('date') or task.get('due_date')
            if not task_date:
                continue
            
            # Extract date only
            date_only = task_date[:10]
            
            if date_only != current_date:
                current_date = date_only
                output += f"\n## {current_date}\n\n"
            
            priority = task.get('priority', 'medium')
            icon = self.priority_colors.get(priority, '⚪')
            score = task.get('priority_score', 0)
            
            output += f"{icon} [{score:.0f}] {task.get('title', 'Untitled')}\n"
        
        return output
    
    def generate_matrix_view(self, tasks: List[Dict[str, Any]]) -> str:
        """Generate Eisenhower Matrix view (urgent vs important)"""
        output = "# Eisenhower Matrix\n\n"
        
        # Categorize tasks
        urgent_important = []
        urgent_not_important = []
        not_urgent_important = []
        not_urgent_not_important = []
        
        for task in tasks:
            is_urgent = self._is_urgent(task)
            is_important = self._is_important(task)
            
            if is_urgent and is_important:
                urgent_important.append(task)
            elif is_urgent and not is_important:
                urgent_not_important.append(task)
            elif not is_urgent and is_important:
                not_urgent_important.append(task)
            else:
                not_urgent_not_important.append(task)
        
        # Format output
        output += "## 🔴 URGENT & IMPORTANT (Do First)\n"
        for task in urgent_important:
            output += f"- {task.get('title')}\n"
        
        output += "\n## 🟠 URGENT but not Important (Delegate/Quick)\n"
        for task in urgent_not_important:
            output += f"- {task.get('title')}\n"
        
        output += "\n## 🟡 NOT URGENT but Important (Schedule)\n"
        for task in not_urgent_important:
            output += f"- {task.get('title')}\n"
        
        output += "\n## 🟢 NOT URGENT & not Important (Eliminate)\n"
        for task in not_urgent_not_important:
            output += f"- {task.get('title')}\n"
        
        return output
    
    def _group_by_priority(self, tasks: List[Dict[str, Any]]) -> Dict[str, List]:
        """Group tasks by priority level"""
        grouped = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        for task in tasks:
            priority = task.get('priority', 'medium').lower()
            if priority in grouped:
                grouped[priority].append(task)
        
        return grouped
    
    def _is_urgent(self, task: Dict[str, Any]) -> bool:
        """Check if task is urgent"""
        from datetime import datetime, timedelta
        
        date_str = task.get('date') or task.get('due_date')
        if not date_str:
            return False
        
        try:
            due_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            days_until = (due_date - datetime.now()).days
            return days_until <= 3
        except (ValueError, TypeError):
            return False
    
    def _is_important(self, task: Dict[str, Any]) -> bool:
        """Check if task is important"""
        priority = task.get('priority', 'medium').lower()
        task_type = task.get('type', '').lower()
        
        return priority in ['critical', 'high'] or 'exam' in task_type


def main():
    """Test priority visualizer"""
    visualizer = PriorityVisualizer()
    
    print("Priority Visualization System")
    print("=" * 50)
    
    # Test tasks
    test_tasks = [
        {'title': 'Final Exam', 'priority': 'critical', 'priority_score': 95, 'date': '2024-11-15', 'type': 'exam'},
        {'title': 'Homework 3', 'priority': 'medium', 'priority_score': 60, 'due_date': '2024-11-12'},
        {'title': 'Project', 'priority': 'high', 'priority_score': 85, 'due_date': '2024-11-20'},
    ]
    
    print("\n" + visualizer.generate_text_view(test_tasks))


if __name__ == "__main__":
    main()
