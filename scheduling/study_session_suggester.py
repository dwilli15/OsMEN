#!/usr/bin/env python3
"""
Study Session Suggester

Generates optimized study session recommendations.
Part of v1.5.0 - Priority & Scheduling Intelligence.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import json


class StudySessionSuggester:
    """Generate study session suggestions"""
    
    def __init__(self):
        self.session_types = {
            'deep_focus': {'duration': 90, 'break': 20, 'best_time': 'morning'},
            'standard': {'duration': 50, 'break': 15, 'best_time': 'any'},
            'short': {'duration': 25, 'break': 5, 'best_time': 'any'},
            'review': {'duration': 30, 'break': 10, 'best_time': 'evening'}
        }
    
    def suggest_sessions(self, tasks: List[Dict[str, Any]], 
                        available_hours_per_day: int = 4) -> List[Dict[str, Any]]:
        """
        Generate study session suggestions
        
        Args:
            tasks: List of tasks requiring study
            available_hours_per_day: Hours available daily
        
        Returns:
            List of suggested study sessions
        """
        suggestions = []
        
        # Sort by priority
        sorted_tasks = sorted(tasks, key=lambda x: x.get('priority_score', 0), reverse=True)
        
        for task in sorted_tasks[:5]:  # Top 5 tasks
            task_suggestions = self._suggest_for_task(task, available_hours_per_day)
            suggestions.extend(task_suggestions)
        
        return suggestions
    
    def _suggest_for_task(self, task: Dict[str, Any], 
                         available_hours: int) -> List[Dict[str, Any]]:
        """Generate suggestions for a specific task"""
        suggestions = []
        
        estimated_hours = task.get('estimated_hours', 5)
        task_type = task.get('type', '').lower()
        
        # Determine session type
        if task_type == 'exam':
            session_type = 'deep_focus'
            sessions_needed = max(1, int(estimated_hours / 1.5))
        elif 'project' in task_type:
            session_type = 'standard'
            sessions_needed = max(1, int(estimated_hours / 0.8))
        else:
            session_type = 'standard'
            sessions_needed = max(1, int(estimated_hours / 0.8))
        
        session_config = self.session_types[session_type]
        
        # Generate session schedule
        start_date = datetime.now()
        for i in range(min(sessions_needed, 7)):  # Max 7 sessions
            session_date = start_date + timedelta(days=i)
            
            suggestions.append({
                'task_id': task.get('id'),
                'task_title': task.get('title'),
                'session_number': i + 1,
                'total_sessions': sessions_needed,
                'date': session_date.isoformat(),
                'session_type': session_type,
                'duration_minutes': session_config['duration'],
                'break_minutes': session_config['break'],
                'recommended_time': session_config['best_time'],
                'focus_areas': self._generate_focus_areas(task, i + 1, sessions_needed)
            })
        
        return suggestions
    
    def _generate_focus_areas(self, task: Dict[str, Any], 
                             session_num: int, total_sessions: int) -> List[str]:
        """Generate focus areas for each session"""
        task_type = task.get('type', '').lower()
        
        if task_type == 'exam':
            if session_num == 1:
                return ["Review lecture notes", "Identify key concepts"]
            elif session_num == total_sessions:
                return ["Practice problems", "Review difficult topics"]
            else:
                return [f"Study chapter/topic {session_num}", "Practice exercises"]
        elif 'project' in task_type:
            if session_num == 1:
                return ["Plan and outline", "Research"]
            elif session_num == total_sessions:
                return ["Final review", "Polish and submit"]
            else:
                return [f"Work on section {session_num}", "Document progress"]
        else:
            return ["Complete assignment", "Review and check work"]
    
    def optimize_schedule(self, sessions: List[Dict[str, Any]], 
                         energy_pattern: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """Optimize session schedule based on energy patterns"""
        if energy_pattern is None:
            energy_pattern = {
                'morning': 0.9,
                'afternoon': 0.7,
                'evening': 0.6,
                'night': 0.3
            }
        
        optimized = []
        
        for session in sessions:
            recommended_time = session['recommended_time']
            
            # Assign specific time based on energy
            if recommended_time == 'morning':
                session['suggested_start_time'] = '09:00'
            elif recommended_time == 'evening':
                session['suggested_start_time'] = '18:00'
            else:
                # Use highest energy time
                best_time = max(energy_pattern.items(), key=lambda x: x[1])[0]
                if best_time == 'morning':
                    session['suggested_start_time'] = '10:00'
                elif best_time == 'afternoon':
                    session['suggested_start_time'] = '14:00'
                else:
                    session['suggested_start_time'] = '19:00'
            
            optimized.append(session)
        
        return optimized


def main():
    """Test study session suggester"""
    suggester = StudySessionSuggester()
    
    print("Study Session Suggester")
    print("=" * 50)
    
    # Test task
    test_task = {
        'id': '1',
        'title': 'CS 101 Final Exam',
        'type': 'exam',
        'estimated_hours': 15,
        'priority_score': 95
    }
    
    suggestions = suggester.suggest_sessions([test_task], available_hours_per_day=4)
    
    print(f"\nGenerated {len(suggestions)} study sessions:")
    for session in suggestions[:3]:
        print(f"\nSession {session['session_number']}:")
        print(f"  Date: {session['date'][:10]}")
        print(f"  Type: {session['session_type']}")
        print(f"  Duration: {session['duration_minutes']} min")
        print(f"  Focus: {', '.join(session['focus_areas'])}")


if __name__ == "__main__":
    main()
