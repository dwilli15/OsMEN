#!/usr/bin/env python3
"""
Priority Ranking System

Intelligent task prioritization based on multiple factors.
Part of v1.5.0 - Priority & Scheduling Intelligence.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import json


class PriorityRanker:
    """Rank tasks and events by priority"""
    
    def __init__(self):
        self.weights = {'urgency': 0.4, 'importance': 0.3, 'effort': 0.2, 'dependency': 0.1}
    
    def calculate_priority(self, task: Dict[str, Any]) -> float:
        """Calculate priority score (0-100)"""
        urgency_score = self._calculate_urgency(task)
        importance_score = self._calculate_importance(task)
        effort_score = self._calculate_effort(task)
        dependency_score = self._calculate_dependency(task)
        
        total_score = (
            urgency_score * self.weights['urgency'] +
            importance_score * self.weights['importance'] +
            effort_score * self.weights['effort'] +
            dependency_score * self.weights['dependency']
        )
        
        return min(100, max(0, total_score))
    
    def _calculate_urgency(self, task: Dict[str, Any]) -> float:
        """Calculate urgency score based on due date"""
        due_date_str = task.get('date') or task.get('due_date')
        if not due_date_str:
            return 50.0
        
        try:
            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
            days_until_due = (due_date - datetime.now()).days
            
            if days_until_due < 0:
                return 100.0
            elif days_until_due == 0:
                return 95.0
            elif days_until_due == 1:
                return 90.0
            elif days_until_due <= 3:
                return 80.0
            elif days_until_due <= 7:
                return 60.0
            else:
                return max(20.0, 100 - (days_until_due * 2))
        except (ValueError, TypeError):
            return 50.0
    
    def _calculate_importance(self, task: Dict[str, Any]) -> float:
        """Calculate importance score"""
        manual_priority = task.get('priority', 'medium').lower()
        
        if manual_priority == 'critical':
            score = 100.0
        elif manual_priority == 'high':
            score = 80.0
        elif manual_priority == 'medium':
            score = 50.0
        else:
            score = 30.0
        
        if 'exam' in task.get('type', '').lower() or 'final' in task.get('title', '').lower():
            score = max(score, 90.0)
        
        return score
    
    def _calculate_effort(self, task: Dict[str, Any]) -> float:
        """Calculate effort score"""
        estimated_hours = task.get('estimated_hours', 0)
        
        if estimated_hours >= 20:
            return 90.0
        elif estimated_hours >= 10:
            return 70.0
        elif estimated_hours >= 5:
            return 50.0
        else:
            return 30.0
    
    def _calculate_dependency(self, task: Dict[str, Any]) -> float:
        """Calculate dependency score"""
        blocks_count = task.get('blocks_count', 0)
        
        if blocks_count >= 3:
            return 90.0
        elif blocks_count == 2:
            return 70.0
        elif blocks_count == 1:
            return 50.0
        else:
            return 30.0
    
    def rank_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank all tasks by priority"""
        ranked_tasks = []
        
        for task in tasks:
            task_copy = task.copy()
            task_copy['priority_score'] = self.calculate_priority(task)
            ranked_tasks.append(task_copy)
        
        ranked_tasks.sort(key=lambda x: x['priority_score'], reverse=True)
        return ranked_tasks


def main():
    print("Priority Ranking System - Ready")


if __name__ == "__main__":
    main()
