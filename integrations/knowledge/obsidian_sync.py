"""
Obsidian vault synchronization for knowledge management.
Local file sync with markdown parsing and task extraction.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

try:
    import frontmatter
    FRONTMATTER_AVAILABLE = True
except ImportError:
    FRONTMATTER_AVAILABLE = False

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    # Create a dummy class for when watchdog is not available
    class FileSystemEventHandler:
        """Dummy FileSystemEventHandler for when watchdog is not installed"""
        pass


class ObsidianSync:
    """
    Obsidian vault synchronization.
    Monitors local vault for changes and syncs tasks.
    """
    
    def __init__(self, vault_path: Optional[str] = None):
        """
        Initialize Obsidian sync.
        
        Args:
            vault_path: Path to Obsidian vault directory
        """
        self.vault_path = vault_path or os.getenv('OBSIDIAN_VAULT_PATH', '')
        self.observer = None
        
        if not FRONTMATTER_AVAILABLE:
            print("Warning: python-frontmatter not installed.")
        
        if not WATCHDOG_AVAILABLE:
            print("Warning: watchdog not installed. File watching disabled.")
    
    def extract_tasks_from_vault(self) -> List[Dict]:
        """
        Extract all tasks from Obsidian vault.
        
        Returns:
            List of task dictionaries
        """
        if not self.vault_path or not os.path.exists(self.vault_path):
            return []
            
        tasks = []
        vault_dir = Path(self.vault_path)
        
        for md_file in vault_dir.rglob('*.md'):
            file_tasks = self.extract_tasks_from_file(str(md_file))
            tasks.extend(file_tasks)
        
        return tasks
    
    def extract_tasks_from_file(self, file_path: str) -> List[Dict]:
        """
        Extract tasks from a single markdown file.
        
        Args:
            file_path: Path to markdown file
            
        Returns:
            List of task dictionaries
        """
        if not os.path.exists(file_path):
            return []
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse frontmatter if available
            metadata = {}
            if FRONTMATTER_AVAILABLE:
                try:
                    post = frontmatter.loads(content)
                    metadata = post.metadata
                    content_without_fm = post.content
                except:
                    content_without_fm = content
            else:
                content_without_fm = content
            
            # Extract tasks from checkboxes
            tasks = []
            for line in content_without_fm.split('\n'):
                task = self._parse_task_line(line, file_path, metadata)
                if task:
                    tasks.append(task)
            
            return tasks
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []
    
    def _parse_task_line(self, line: str, file_path: str, 
                        metadata: Dict) -> Optional[Dict]:
        """Parse a single line for task checkbox."""
        line = line.strip()
        
        # Check for markdown checkbox syntax
        if not (line.startswith('- [ ]') or line.startswith('- [x]')):
            return None
        
        is_completed = line.startswith('- [x]')
        content = line[6:].strip()  # Remove checkbox syntax
        
        if not content:
            return None
        
        # Extract due date from content or metadata
        due_date = metadata.get('due') or metadata.get('due_date')
        
        # Extract priority from content or metadata
        priority = 'medium'
        if '!!' in content:
            priority = 'critical'
        elif '!' in content:
            priority = 'high'
        priority = metadata.get('priority', priority)
        
        return {
            'title': content,
            'due_date': due_date,
            'priority': priority,
            'is_completed': is_completed,
            'source': 'obsidian',
            'file_path': file_path,
            'file_name': os.path.basename(file_path)
        }
    
    def sync_task_to_obsidian(self, task: Dict) -> bool:
        """
        Sync task from OsMEN to Obsidian.
        
        Args:
            task: Task dictionary
            
        Returns:
            Success boolean
        """
        if not self.vault_path:
            return False
        
        # Determine file path
        if task.get('file_path'):
            file_path = task['file_path']
        else:
            # Create in daily note or tasks file
            tasks_dir = os.path.join(self.vault_path, 'Tasks')
            os.makedirs(tasks_dir, exist_ok=True)
            file_path = os.path.join(tasks_dir, 'OsMEN_Tasks.md')
        
        try:
            # Read existing content
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                content = "# Tasks from OsMEN\n\n"
            
            # Add or update task
            checkbox = '- [x]' if task.get('is_completed') else '- [ ]'
            task_line = f"{checkbox} {task.get('title', 'Untitled')}"
            
            # Add priority indicator
            if task.get('priority') == 'critical':
                task_line += ' !!'
            elif task.get('priority') == 'high':
                task_line += ' !'
            
            # Add due date if present
            if task.get('due_date'):
                task_line += f" 📅 {task['due_date']}"
            
            task_line += '\n'
            
            # Append to file
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(task_line)
            
            return True
        except Exception as e:
            print(f"Error syncing to Obsidian: {e}")
            return False
    
    def start_watching(self, callback=None):
        """
        Start watching vault for file changes.
        
        Args:
            callback: Function to call on file change
        """
        if not WATCHDOG_AVAILABLE or not self.vault_path:
            return
        
        if not os.path.exists(self.vault_path):
            return
        
        event_handler = ObsidianEventHandler(callback)
        self.observer = Observer()
        self.observer.schedule(event_handler, self.vault_path, recursive=True)
        self.observer.start()
    
    def stop_watching(self):
        """Stop watching vault."""
        if self.observer:
            self.observer.stop()
            self.observer.join()


class ObsidianEventHandler(FileSystemEventHandler):
    """File system event handler for Obsidian vault."""
    
    def __init__(self, callback=None):
        self.callback = callback
    
    def on_modified(self, event):
        """Handle file modification."""
        if event.is_directory:
            return
        
        if event.src_path.endswith('.md'):
            if self.callback:
                self.callback(event.src_path)
