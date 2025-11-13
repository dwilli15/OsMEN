"""
Unified synchronization engine for multiple knowledge sources.
Handles bidirectional sync with conflict resolution.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum

from .notion_client import NotionClient
from .todoist_client import TodoistClient
from .obsidian_sync import ObsidianSync


class ConflictStrategy(Enum):
    """Conflict resolution strategies."""
    LAST_WRITE_WINS = "last_write_wins"
    PRIORITY_BASED = "priority_based"
    MANUAL = "manual"


class SyncEngine:
    """
    Unified bidirectional synchronization engine.
    Coordinates sync between Notion, Todoist, Obsidian, and OsMEN calendar.
    """
    
    def __init__(self, conflict_strategy: ConflictStrategy = ConflictStrategy.LAST_WRITE_WINS):
        """
        Initialize sync engine.
        
        Args:
            conflict_strategy: Strategy for resolving conflicts
        """
        self.notion = NotionClient()
        self.todoist = TodoistClient()
        self.obsidian = ObsidianSync()
        self.conflict_strategy = conflict_strategy
        
        # Sync state file
        self.state_file = os.path.join('.copilot', 'sync_state.json')
        self.state = self._load_state()
    
    def sync_all(self) -> Dict[str, any]:
        """
        Perform full synchronization across all sources.
        
        Returns:
            Sync result summary
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'tasks_synced': 0,
            'conflicts': [],
            'errors': []
        }
        
        try:
            # 1. Gather tasks from all sources
            notion_tasks = self.notion.extract_tasks()
            todoist_tasks = self.todoist.get_tasks()
            obsidian_tasks = self.obsidian.extract_tasks_from_vault()
            
            # 2. Merge and deduplicate
            all_tasks = self._merge_tasks(notion_tasks, todoist_tasks, obsidian_tasks)
            
            # 3. Detect conflicts
            conflicts = self._detect_conflicts(all_tasks)
            results['conflicts'] = conflicts
            
            # 4. Resolve conflicts
            resolved_tasks = self._resolve_conflicts(conflicts, all_tasks)
            
            # 5. Sync back to all sources
            for task in resolved_tasks:
                self._sync_task_to_all_sources(task)
                results['tasks_synced'] += 1
            
            # 6. Update state
            self._save_state(all_tasks)
            
        except Exception as e:
            results['errors'].append(str(e))
        
        return results
    
    def sync_task(self, task: Dict, sources: Optional[List[str]] = None) -> bool:
        """
        Sync a single task to specified sources.
        
        Args:
            task: Task dictionary
            sources: List of sources to sync to (None = all)
            
        Returns:
            Success boolean
        """
        if sources is None:
            sources = ['notion', 'todoist', 'obsidian']
        
        success = True
        
        if 'notion' in sources:
            success = success and self.notion.sync_task_to_notion(task)
        
        if 'todoist' in sources:
            success = success and self.todoist.sync_task_to_todoist(task)
        
        if 'obsidian' in sources:
            success = success and self.obsidian.sync_task_to_obsidian(task)
        
        return success
    
    def _merge_tasks(self, *task_lists) -> List[Dict]:
        """Merge tasks from multiple sources by ID or title."""
        merged = {}
        
        for task_list in task_lists:
            for task in task_list:
                # Create unique key
                key = task.get('id') or task.get('title', '').lower()
                
                if key in merged:
                    # Merge with existing
                    existing = merged[key]
                    # Keep most recent update
                    task_time = task.get('updated_at', task.get('created_at', ''))
                    existing_time = existing.get('updated_at', existing.get('created_at', ''))
                    
                    if task_time > existing_time:
                        merged[key] = task
                else:
                    merged[key] = task
        
        return list(merged.values())
    
    def _detect_conflicts(self, tasks: List[Dict]) -> List[Dict]:
        """
        Detect conflicting task versions.
        
        Returns:
            List of conflict dictionaries
        """
        conflicts = []
        seen = {}
        
        for task in tasks:
            title = task.get('title', '').lower()
            
            if title in seen:
                # Potential conflict
                existing = seen[title]
                if self._tasks_differ(existing, task):
                    conflicts.append({
                        'title': title,
                        'versions': [existing, task],
                        'fields_differ': self._get_diff_fields(existing, task)
                    })
            else:
                seen[title] = task
        
        return conflicts
    
    def _tasks_differ(self, task1: Dict, task2: Dict) -> bool:
        """Check if two tasks have different content."""
        fields = ['due_date', 'priority', 'is_completed']
        
        for field in fields:
            if task1.get(field) != task2.get(field):
                return True
        
        return False
    
    def _get_diff_fields(self, task1: Dict, task2: Dict) -> List[str]:
        """Get list of fields that differ between tasks."""
        fields = ['due_date', 'priority', 'is_completed', 'description']
        diff_fields = []
        
        for field in fields:
            if task1.get(field) != task2.get(field):
                diff_fields.append(field)
        
        return diff_fields
    
    def _resolve_conflicts(self, conflicts: List[Dict], all_tasks: List[Dict]) -> List[Dict]:
        """
        Resolve conflicts using configured strategy.
        
        Returns:
            List of resolved tasks
        """
        resolved = all_tasks.copy()
        
        for conflict in conflicts:
            versions = conflict['versions']
            
            if self.conflict_strategy == ConflictStrategy.LAST_WRITE_WINS:
                # Choose most recently updated
                chosen = max(versions, key=lambda t: t.get('updated_at', ''))
            
            elif self.conflict_strategy == ConflictStrategy.PRIORITY_BASED:
                # Choose by priority level
                priority_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
                chosen = max(versions, key=lambda t: priority_order.get(t.get('priority', 'low'), 0))
            
            else:  # MANUAL
                # For manual, keep first version and flag for review
                chosen = versions[0]
                chosen['needs_manual_review'] = True
            
            # Update resolved list
            title = conflict['title']
            for i, task in enumerate(resolved):
                if task.get('title', '').lower() == title:
                    resolved[i] = chosen
                    break
        
        return resolved
    
    def _sync_task_to_all_sources(self, task: Dict):
        """Sync task to all enabled sources."""
        self.sync_task(task, sources=['notion', 'todoist', 'obsidian'])
    
    def _load_state(self) -> Dict:
        """Load sync state from file."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_state(self, tasks: List[Dict]):
        """Save sync state to file."""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        
        state = {
            'last_sync': datetime.now().isoformat(),
            'task_count': len(tasks),
            'tasks': {t.get('id', t.get('title')): t.get('updated_at', '') for t in tasks}
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def get_sync_status(self) -> Dict:
        """Get current sync status."""
        return {
            'last_sync': self.state.get('last_sync', 'Never'),
            'task_count': self.state.get('task_count', 0),
            'notion_enabled': self.notion.client is not None,
            'todoist_enabled': self.todoist.client is not None,
            'obsidian_enabled': bool(self.obsidian.vault_path)
        }
