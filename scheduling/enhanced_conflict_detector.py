#!/usr/bin/env python3
"""
Enhanced Conflict Detection Engine

Advanced conflict detection with resolution strategies.
Part of v1.4.0 - Syllabus Parser & Calendar Foundation.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'parsers' / 'syllabus'))

from conflict_validator import ConflictValidator
from datetime import datetime, timedelta
from typing import List, Dict, Any


class EnhancedConflictDetector(ConflictValidator):
    """Enhanced conflict detection with resolution strategies"""
    
    def __init__(self):
        super().__init__()
        self.resolution_strategies = []
    
    def detect_all_conflicts(self, events: List[Dict[str, Any]], 
                            tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect all types of conflicts
        
        Args:
            events: Calendar events
            tasks: Tasks and assignments
        
        Returns:
            Comprehensive conflict report
        """
        all_items = events + tasks
        
        # Basic conflicts
        conflicts = self.find_conflicts(all_items)
        
        # Advanced conflict types
        workload_conflicts = self._detect_workload_conflicts(all_items)
        study_time_conflicts = self._detect_insufficient_study_time(all_items)
        
        return {
            'total_conflicts': len(conflicts),
            'time_conflicts': conflicts,
            'workload_conflicts': workload_conflicts,
            'study_time_conflicts': study_time_conflicts,
            'resolution_strategies': self._generate_strategies(conflicts, workload_conflicts)
        }
    
    def _detect_workload_conflicts(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect days with excessive workload"""
        workload_conflicts = []
        
        # Group by date
        daily_workload = {}
        for item in items:
            date_str = item.get('date') or item.get('due_date')
            if date_str:
                try:
                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
                    if date not in daily_workload:
                        daily_workload[date] = []
                    daily_workload[date].append(item)
                except (ValueError, TypeError):
                    continue
        
        # Check for excessive workload (>8 hours per day)
        for date, day_items in daily_workload.items():
            total_hours = sum(item.get('estimated_hours', 2) for item in day_items)
            
            if total_hours > 8:
                workload_conflicts.append({
                    'date': date.isoformat(),
                    'total_hours': total_hours,
                    'items_count': len(day_items),
                    'severity': 'high' if total_hours > 12 else 'medium',
                    'recommendation': 'Redistribute tasks across multiple days'
                })
        
        return workload_conflicts
    
    def _detect_insufficient_study_time(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect exams with insufficient preparation time"""
        study_conflicts = []
        
        for item in items:
            if item.get('type') == 'exam':
                exam_date_str = item.get('date')
                if not exam_date_str:
                    continue
                
                try:
                    exam_date = datetime.fromisoformat(exam_date_str.replace('Z', '+00:00'))
                    days_until_exam = (exam_date - datetime.now()).days
                    
                    required_study_hours = item.get('estimated_hours', 10)
                    
                    # Check if enough time to study
                    if days_until_exam < required_study_hours / 2:  # Assuming 2 hours study per day
                        study_conflicts.append({
                            'exam': item.get('title'),
                            'date': exam_date_str,
                            'days_until': days_until_exam,
                            'required_hours': required_study_hours,
                            'severity': 'critical' if days_until_exam < 3 else 'high',
                            'recommendation': f'Start studying immediately - need {required_study_hours}h'
                        })
                except (ValueError, TypeError):
                    continue
        
        return study_conflicts
    
    def _generate_strategies(self, time_conflicts: List[Dict], 
                           workload_conflicts: List[Dict]) -> List[str]:
        """Generate resolution strategies"""
        strategies = []
        
        if time_conflicts:
            strategies.append("Review time conflicts and reschedule non-critical events")
        
        if workload_conflicts:
            strategies.append("Redistribute workload across multiple days")
            strategies.append("Consider requesting deadline extensions for lower-priority tasks")
        
        if not strategies:
            strategies.append("No major conflicts detected - schedule looks manageable")
        
        return strategies


def main():
    print("Enhanced Conflict Detection Engine - Ready")


if __name__ == "__main__":
    main()
