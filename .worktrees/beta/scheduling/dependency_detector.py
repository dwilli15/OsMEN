#!/usr/bin/env python3
"""
Dependency Detection System

Detects and manages task dependencies.
Part of v1.5.0 - Priority & Scheduling Intelligence.
"""

from typing import List, Dict, Any, Set, Optional
import json


class DependencyDetector:
    """Detect and manage task dependencies"""
    
    def __init__(self):
        self.dependency_graph = {}
    
    def detect_dependencies(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Detect dependencies between tasks
        
        Args:
            tasks: List of tasks
        
        Returns:
            Dictionary mapping task IDs to their dependencies
        """
        dependencies = {}
        
        for task in tasks:
            task_id = task.get('id', task.get('title'))
            dependencies[task_id] = []
            
            # Check explicit dependencies
            if task.get('depends_on'):
                dependencies[task_id].extend(task['depends_on'])
            
            # Detect implicit dependencies
            implicit_deps = self._detect_implicit_dependencies(task, tasks)
            dependencies[task_id].extend(implicit_deps)
        
        self.dependency_graph = dependencies
        return dependencies
    
    def _detect_implicit_dependencies(self, task: Dict[str, Any], 
                                     all_tasks: List[Dict[str, Any]]) -> List[str]:
        """Detect implicit dependencies based on content"""
        dependencies = []
        
        task_title = task.get('title', '').lower()
        task_type = task.get('type', '').lower()
        
        # Pattern: "Homework X" depends on previous homeworks
        if 'homework' in task_title or 'assignment' in task_title:
            import re
            number_match = re.search(r'(\d+)', task_title)
            if number_match:
                task_number = int(number_match.group(1))
                
                # Look for previous homework
                for other_task in all_tasks:
                    other_title = other_task.get('title', '').lower()
                    other_number_match = re.search(r'(\d+)', other_title)
                    
                    if other_number_match:
                        other_number = int(other_number_match.group(1))
                        if other_number == task_number - 1:
                            if ('homework' in other_title or 'assignment' in other_title):
                                dependencies.append(other_task.get('id', other_task.get('title')))
        
        # Pattern: Exam depends on related homeworks/assignments
        if 'exam' in task_type or 'exam' in task_title:
            for other_task in all_tasks:
                other_type = other_task.get('type', '').lower()
                if 'assignment' in other_type or 'homework' in other_type:
                    # Same course?
                    if self._same_course(task, other_task):
                        dependencies.append(other_task.get('id', other_task.get('title')))
        
        return dependencies
    
    def _same_course(self, task1: Dict[str, Any], task2: Dict[str, Any]) -> bool:
        """Check if two tasks are from the same course"""
        # Simple heuristic: check if title starts with same course code
        title1_words = task1.get('title', '').split()
        title2_words = task2.get('title', '').split()
        
        if title1_words and title2_words:
            return title1_words[0] == title2_words[0]
        
        return False
    
    def get_blocked_tasks(self, task_id: str) -> List[str]:
        """Get tasks blocked by this task"""
        blocked = []
        
        for tid, deps in self.dependency_graph.items():
            if task_id in deps:
                blocked.append(tid)
        
        return blocked
    
    def get_prerequisite_tasks(self, task_id: str) -> List[str]:
        """Get prerequisite tasks"""
        return self.dependency_graph.get(task_id, [])
    
    def is_ready_to_start(self, task_id: str, completed_tasks: Set[str]) -> bool:
        """Check if task is ready to start"""
        prerequisites = self.get_prerequisite_tasks(task_id)
        
        for prereq in prerequisites:
            if prereq not in completed_tasks:
                return False
        
        return True
    
    def get_dependency_chain(self, task_id: str) -> List[str]:
        """Get full dependency chain for a task"""
        chain = []
        visited = set()
        
        def traverse(tid):
            if tid in visited:
                return
            visited.add(tid)
            
            prereqs = self.get_prerequisite_tasks(tid)
            for prereq in prereqs:
                traverse(prereq)
                if prereq not in chain:
                    chain.append(prereq)
        
        traverse(task_id)
        return chain


def main():
    """Test dependency detector"""
    detector = DependencyDetector()
    
    print("Dependency Detection System")
    print("=" * 50)
    
    # Test tasks
    test_tasks = [
        {'id': '1', 'title': 'CS 101 Homework 1', 'type': 'assignment'},
        {'id': '2', 'title': 'CS 101 Homework 2', 'type': 'assignment'},
        {'id': '3', 'title': 'CS 101 Homework 3', 'type': 'assignment'},
        {'id': '4', 'title': 'CS 101 Midterm Exam', 'type': 'exam'},
    ]
    
    dependencies = detector.detect_dependencies(test_tasks)
    
    print("\nDetected Dependencies:")
    for task_id, deps in dependencies.items():
        if deps:
            print(f"- Task {task_id} depends on: {deps}")
    
    print("\nBlocked Tasks:")
    blocked = detector.get_blocked_tasks('2')
    print(f"- Homework 2 blocks: {blocked}")


if __name__ == "__main__":
    main()
