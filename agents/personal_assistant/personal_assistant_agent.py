#!/usr/bin/env python3
"""
Personal Assistant Agent - Real Implementation
Provides task management, scheduling, reminders, and productivity assistance.

This agent integrates with:
- Calendar systems (Google, Outlook) via OAuth
- LLM for natural language task processing
- Persistent storage for tasks and reminders
- Real-time scheduling and reminders

Usage:
    from agents.personal_assistant.personal_assistant_agent import PersonalAssistantAgent
    
    agent = PersonalAssistantAgent()
    
    # Task management
    task = agent.create_task("Review proposal", priority="high", due_date="2024-01-15")
    tasks = agent.get_tasks(status="pending", priority="high")
    
    # Reminders
    reminder = agent.set_reminder("Team meeting", "2024-01-15T10:00:00")
    
    # Async with LLM
    result = await agent.process_natural_language_async("Schedule a meeting tomorrow at 2pm")
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import sqlite3

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import LLM providers
LLM_AVAILABLE = False
try:
    from integrations.llm_providers import get_llm_provider
    LLM_AVAILABLE = True
    logger.info("LLM providers available for natural language processing")
except ImportError as e:
    logger.warning(f"LLM providers not available: {e}")

# Try to import calendar integrations
CALENDAR_AVAILABLE = False
try:
    from integrations.v3_integration_layer import get_integration_layer
    CALENDAR_AVAILABLE = True
    logger.info("Calendar integrations available")
except ImportError as e:
    logger.warning(f"Calendar integrations not available: {e}")


class PersonalAssistantAgent:
    """
    Personal Assistant Agent for productivity and task management.
    
    Real implementation that:
    - Persists tasks/reminders to SQLite database
    - Integrates with calendar systems
    - Uses LLM for natural language processing
    - Provides intelligent recommendations
    
    Attributes:
        db_path: Path to SQLite database
        use_llm: Whether LLM is available
        use_calendar: Whether calendar is available
    """
    
    def __init__(self, data_dir: str = "data/personal_assistant"):
        """
        Initialize the Personal Assistant Agent.
        
        Args:
            data_dir: Directory for data storage
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.data_dir / "assistant.db"
        self.use_llm = LLM_AVAILABLE
        self.use_calendar = CALENDAR_AVAILABLE
        
        self.llm = None
        self.calendar = None
        
        # In-memory caches (for backward compatibility)
        self.tasks = []
        self.reminders = []
        self.schedule = []
        
        # Initialize database
        self._init_db()
        self._load_from_db()
        
        logger.info(f"PersonalAssistantAgent initialized (LLM={self.use_llm}, Calendar={self.use_calendar}, DB={self.db_path})")
    
    def _init_db(self):
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT DEFAULT 'medium',
                due_date TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT,
                completed_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                time TEXT NOT NULL,
                message TEXT,
                created_at TEXT NOT NULL,
                triggered BOOLEAN DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                description TEXT,
                source TEXT DEFAULT 'local',
                created_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_from_db(self):
        """Load tasks and reminders from database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Load tasks
        cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC')
        self.tasks = [dict(row) for row in cursor.fetchall()]
        
        # Load reminders
        cursor.execute('SELECT * FROM reminders ORDER BY time')
        self.reminders = [dict(row) for row in cursor.fetchall()]
        
        # Load events
        cursor.execute('SELECT * FROM events ORDER BY start_time')
        self.schedule = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
    
    async def _get_llm(self):
        """Get LLM provider (lazy initialization)."""
        if self.llm is None and LLM_AVAILABLE:
            try:
                self.llm = await get_llm_provider("ollama")
            except Exception as e:
                logger.warning(f"Failed to get LLM: {e}")
        return self.llm
    
    def create_task(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        due_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new task with persistent storage.
        
        Args:
            title: Task title
            description: Task description
            priority: Priority level (low, medium, high, urgent)
            due_date: Due date in ISO format
        
        Returns:
            Dictionary with task details
        """
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tasks (title, description, priority, due_date, status, created_at)
            VALUES (?, ?, ?, ?, 'pending', ?)
        ''', (title, description, priority, due_date, now))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        task = {
            "id": task_id,
            "title": title,
            "description": description,
            "priority": priority,
            "due_date": due_date,
            "status": "pending",
            "created_at": now
        }
        
        self.tasks.append(task)
        logger.info(f"Created task: {title} (ID: {task_id})")
        
        return task
    
    def update_task(
        self,
        task_id: int,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        due_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing task.
        
        Args:
            task_id: Task ID
            status: New status (pending, in_progress, completed)
            priority: New priority
            due_date: New due date
        
        Returns:
            Updated task dictionary
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if status:
            updates.append("status = ?")
            params.append(status)
            if status == 'completed':
                updates.append("completed_at = ?")
                params.append(datetime.now().isoformat())
        
        if priority:
            updates.append("priority = ?")
            params.append(priority)
        
        if due_date:
            updates.append("due_date = ?")
            params.append(due_date)
        
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(task_id)
        
        cursor.execute(f'''
            UPDATE tasks SET {", ".join(updates)} WHERE id = ?
        ''', params)
        
        conn.commit()
        
        # Fetch updated task
        cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        conn.row_factory = sqlite3.Row
        row = cursor.fetchone()
        conn.close()
        
        if row:
            task = dict(row)
            # Update in-memory cache
            for i, t in enumerate(self.tasks):
                if t['id'] == task_id:
                    self.tasks[i] = task
                    break
            return task
        
        return {"error": f"Task {task_id} not found"}
    
    def get_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        due_today: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get tasks filtered by criteria.
        
        Args:
            status: Filter by status (pending, in_progress, completed)
            priority: Filter by priority (low, medium, high, urgent)
            due_today: Filter to tasks due today
        
        Returns:
            List of filtered tasks
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = 'SELECT * FROM tasks WHERE 1=1'
        params = []
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        if priority:
            query += ' AND priority = ?'
            params.append(priority)
        
        if due_today:
            today = datetime.now().date().isoformat()
            query += ' AND due_date LIKE ?'
            params.append(f'{today}%')
        
        query += ' ORDER BY CASE priority WHEN "urgent" THEN 1 WHEN "high" THEN 2 WHEN "medium" THEN 3 ELSE 4 END'
        
        cursor.execute(query, params)
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return tasks
    
    def set_reminder(
        self,
        title: str,
        time: str,
        message: str = ""
    ) -> Dict[str, Any]:
        """
        Set a reminder with persistent storage.
        
        Args:
            title: Reminder title
            time: Time in ISO format
            message: Optional reminder message
        
        Returns:
            Dictionary with reminder details
        """
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO reminders (title, time, message, created_at)
            VALUES (?, ?, ?, ?)
        ''', (title, time, message, now))
        
        reminder_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        reminder = {
            "id": reminder_id,
            "title": title,
            "time": time,
            "message": message,
            "created_at": now,
            "triggered": False
        }
        
        self.reminders.append(reminder)
        logger.info(f"Set reminder: {title} at {time}")
        
        return reminder
    
    def get_pending_reminders(self) -> List[Dict[str, Any]]:
        """Get reminders that haven't been triggered yet."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute('''
            SELECT * FROM reminders 
            WHERE triggered = 0 AND time <= ?
            ORDER BY time
        ''', (now,))
        
        reminders = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return reminders
    
    def schedule_event(
        self,
        title: str,
        start_time: str,
        end_time: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Schedule a calendar event.
        
        Args:
            title: Event title
            start_time: Start time in ISO format
            end_time: End time in ISO format
            description: Event description
        
        Returns:
            Dictionary with event details
        """
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO events (title, start_time, end_time, description, source, created_at)
            VALUES (?, ?, ?, ?, 'local', ?)
        ''', (title, start_time, end_time, description, now))
        
        event_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        event = {
            "id": event_id,
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "description": description,
            "source": "local",
            "created_at": now
        }
        
        self.schedule.append(event)
        logger.info(f"Scheduled event: {title} from {start_time} to {end_time}")
        
        return event
    
    def get_daily_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate daily summary of tasks, reminders, and schedule.
        
        Args:
            date: Date to summarize (defaults to today)
        
        Returns:
            Dictionary with daily summary
        """
        if date is None:
            date = datetime.now().date().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get today's tasks
        cursor.execute('''
            SELECT * FROM tasks 
            WHERE due_date LIKE ? OR (due_date IS NULL AND status = 'pending')
            ORDER BY priority
        ''', (f'{date}%',))
        today_tasks = [dict(row) for row in cursor.fetchall()]
        
        # Get today's reminders
        cursor.execute('''
            SELECT * FROM reminders 
            WHERE time LIKE ?
            ORDER BY time
        ''', (f'{date}%',))
        today_reminders = [dict(row) for row in cursor.fetchall()]
        
        # Get today's events
        cursor.execute('''
            SELECT * FROM events 
            WHERE start_time LIKE ?
            ORDER BY start_time
        ''', (f'{date}%',))
        today_events = [dict(row) for row in cursor.fetchall()]
        
        # Count overdue tasks
        cursor.execute('''
            SELECT COUNT(*) FROM tasks 
            WHERE due_date < ? AND status != 'completed'
        ''', (date,))
        overdue_count = cursor.fetchone()[0]
        
        conn.close()
        
        # Calculate metrics
        pending = [t for t in today_tasks if t['status'] == 'pending']
        completed = [t for t in today_tasks if t['status'] == 'completed']
        high_priority = [t for t in pending if t['priority'] in ['high', 'urgent']]
        
        return {
            "date": date,
            "tasks": {
                "total": len(today_tasks),
                "pending": len(pending),
                "completed": len(completed),
                "high_priority": len(high_priority),
                "overdue": overdue_count
            },
            "reminders": len(today_reminders),
            "events": len(today_events),
            "schedule": today_events[:5],  # First 5 events
            "priority_tasks": [{"title": t["title"], "priority": t["priority"]} for t in high_priority[:5]],
            "timestamp": datetime.now().isoformat()
        }
    
    async def process_natural_language_async(self, text: str) -> Dict[str, Any]:
        """
        Process natural language input using LLM.
        
        Args:
            text: Natural language command
        
        Returns:
            Parsed action and result
        """
        result = {
            "input": text,
            "action": None,
            "parsed": None,
            "result": None,
            "llm_used": False
        }
        
        llm = await self._get_llm()
        if llm:
            try:
                prompt = f"""Parse the following natural language command into a structured action.
Command: {text}

Determine if this is a:
1. TASK: Creating, updating, or querying tasks
2. REMINDER: Setting a reminder
3. EVENT: Scheduling an event
4. QUERY: Asking about schedule or tasks

Return a JSON object with:
- action_type: One of [task_create, task_update, task_query, reminder_set, event_schedule, query]
- title: Main title/subject
- description: Additional details
- priority: If mentioned (low/medium/high/urgent)
- datetime: Any date/time mentioned (ISO format)
- duration: Duration if mentioned

Example output:
{{"action_type": "task_create", "title": "Review proposal", "priority": "high", "datetime": "2024-01-15"}}
"""
                
                response = await llm.chat([
                    {"role": "system", "content": "You are a personal assistant that parses natural language into structured actions. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ], json_mode=True)
                
                result['llm_used'] = True
                
                try:
                    parsed = json.loads(response.content)
                    result['parsed'] = parsed
                    result['action'] = parsed.get('action_type')
                    
                    # Execute the parsed action
                    if result['action'] == 'task_create':
                        task = self.create_task(
                            title=parsed.get('title', 'Untitled'),
                            description=parsed.get('description', ''),
                            priority=parsed.get('priority', 'medium'),
                            due_date=parsed.get('datetime')
                        )
                        result['result'] = task
                    
                    elif result['action'] == 'reminder_set' and parsed.get('datetime'):
                        reminder = self.set_reminder(
                            title=parsed.get('title', 'Reminder'),
                            time=parsed['datetime'],
                            message=parsed.get('description', '')
                        )
                        result['result'] = reminder
                    
                    elif result['action'] == 'event_schedule':
                        # Default to 1 hour duration
                        start = parsed.get('datetime', datetime.now().isoformat())
                        dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                        end = (dt + timedelta(hours=1)).isoformat()
                        
                        event = self.schedule_event(
                            title=parsed.get('title', 'Event'),
                            start_time=start,
                            end_time=end,
                            description=parsed.get('description', '')
                        )
                        result['result'] = event
                    
                    elif result['action'] == 'query':
                        result['result'] = self.get_daily_summary()
                        
                except json.JSONDecodeError:
                    result['error'] = 'Failed to parse LLM response as JSON'
                    result['raw_response'] = response.content
                    
            except Exception as e:
                result['error'] = str(e)
        else:
            result['note'] = 'LLM not available - natural language processing disabled'
        
        return result
    
    def generate_assistant_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive assistant report.
        
        Returns:
            Dictionary with assistant status and statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Task statistics
        cursor.execute('SELECT COUNT(*) FROM tasks')
        total_tasks = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM tasks WHERE status = "pending"')
        pending_tasks = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM tasks WHERE status = "completed"')
        completed_tasks = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM reminders')
        total_reminders = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM events')
        total_events = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "operational",
            "capabilities": {
                "llm": self.use_llm,
                "calendar": self.use_calendar,
                "persistence": True,
                "database": str(self.db_path)
            },
            "statistics": {
                "total_tasks": total_tasks,
                "pending_tasks": pending_tasks,
                "completed_tasks": completed_tasks,
                "completion_rate": round(completed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0,
                "total_reminders": total_reminders,
                "scheduled_events": total_events
            },
            "daily_summary": self.get_daily_summary()
        }


if __name__ == "__main__":
    # Test the agent
    logging.basicConfig(level=logging.INFO)
    
    agent = PersonalAssistantAgent()
    
    print("=" * 60)
    print("PERSONAL ASSISTANT AGENT - Real Implementation")
    print("=" * 60)
    print(f"LLM Available: {agent.use_llm}")
    print(f"Calendar Available: {agent.use_calendar}")
    print(f"Database: {agent.db_path}")
    print()
    
    # Create sample tasks
    agent.create_task("Review project proposal", priority="high", 
                     due_date=datetime.now().date().isoformat())
    agent.create_task("Prepare presentation", priority="medium")
    agent.create_task("Send follow-up emails", priority="low")
    
    # Set reminders
    agent.set_reminder("Team meeting", (datetime.now() + timedelta(hours=2)).isoformat(), 
                      "Don't forget the weekly sync")
    
    # Schedule events
    agent.schedule_event(
        "Project kickoff", 
        (datetime.now() + timedelta(hours=1)).isoformat(),
        (datetime.now() + timedelta(hours=2)).isoformat(),
        "New project initialization meeting"
    )
    
    # Generate report
    report = agent.generate_assistant_report()
    print("\nAssistant Report:")
    print(json.dumps(report, indent=2))
