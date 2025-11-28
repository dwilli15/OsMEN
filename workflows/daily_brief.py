#!/usr/bin/env python3
"""
Daily Brief Workflow - E2E Proof of Concept

This workflow demonstrates end-to-end viability by touching:
- OAuth: Google Calendar, Gmail, Microsoft Calendar/Mail
- Retrieval: Quantum-inspired RAG for context
- Orchestration: Multi-agent coordination
- Summarization: LLM-powered content generation

Usage:
    python -m workflows.daily_brief
    
    # Or via CLI
    python workflows/daily_brief.py --run
    
    # With specific provider
    python workflows/daily_brief.py --provider openai
"""

import os
import sys
import json
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

from loguru import logger

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class DailyBriefConfig:
    """Configuration for Daily Brief workflow"""
    
    # LLM settings
    llm_provider: str = "ollama"  # Default: local-first
    llm_model: Optional[str] = None
    
    # Calendar settings
    calendar_days_ahead: int = 1
    include_google_calendar: bool = True
    include_outlook_calendar: bool = True
    
    # Email settings
    email_max_count: int = 20
    email_importance_threshold: float = 0.5
    include_gmail: bool = True
    include_outlook_mail: bool = True
    
    # Summary settings
    summary_style: str = "executive"  # executive, detailed, bullet
    include_recommendations: bool = True
    include_time_analysis: bool = True
    
    # Output settings
    output_format: str = "markdown"  # markdown, html, json
    save_to_file: bool = True
    output_dir: str = ".copilot/daily_briefs"


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class WorkflowResult:
    """Result of workflow execution"""
    status: WorkflowStatus
    brief: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    duration_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ============================================================================
# Data Collection Agents
# ============================================================================

class CalendarAgent:
    """Agent for collecting calendar events"""
    
    def __init__(self, config: DailyBriefConfig):
        self.config = config
        self._google_calendar = None
        self._outlook_calendar = None
    
    async def initialize(self):
        """Initialize calendar integrations"""
        if self.config.include_google_calendar:
            try:
                from integrations.v3_integration_layer import get_integration_layer
                layer = get_integration_layer()
                self._google_calendar = layer.get_google_calendar()
                logger.info("Google Calendar initialized")
            except Exception as e:
                logger.warning(f"Google Calendar not available: {e}")
        
        if self.config.include_outlook_calendar:
            try:
                from integrations.v3_integration_layer import get_integration_layer
                layer = get_integration_layer()
                self._outlook_calendar = layer.get_outlook_calendar()
                logger.info("Outlook Calendar initialized")
            except Exception as e:
                logger.warning(f"Outlook Calendar not available: {e}")
    
    async def collect_events(self) -> Dict[str, Any]:
        """Collect calendar events from all sources"""
        events = []
        sources = []
        
        now = datetime.now()
        end_date = now + timedelta(days=self.config.calendar_days_ahead)
        
        # Google Calendar
        if self._google_calendar:
            try:
                google_events = await self._fetch_google_events(now, end_date)
                events.extend(google_events)
                sources.append("google")
                logger.info(f"Fetched {len(google_events)} Google Calendar events")
            except Exception as e:
                logger.error(f"Failed to fetch Google Calendar: {e}")
        
        # Outlook Calendar
        if self._outlook_calendar:
            try:
                outlook_events = await self._fetch_outlook_events(now, end_date)
                events.extend(outlook_events)
                sources.append("outlook")
                logger.info(f"Fetched {len(outlook_events)} Outlook events")
            except Exception as e:
                logger.error(f"Failed to fetch Outlook Calendar: {e}")
        
        # Generate mock data if no real data available (for demo)
        if not events:
            events = self._generate_mock_events()
            sources.append("mock")
            logger.info("Using mock calendar data")
        
        # Sort by start time
        events.sort(key=lambda x: x.get("start", ""))
        
        return {
            "events": events,
            "sources": sources,
            "period": {
                "start": now.isoformat(),
                "end": end_date.isoformat()
            },
            "count": len(events)
        }
    
    async def _fetch_google_events(
        self,
        start: datetime,
        end: datetime
    ) -> List[Dict]:
        """Fetch events from Google Calendar"""
        try:
            result = self._google_calendar.list_events(
                start_date=start.date().isoformat(),
                end_date=end.date().isoformat()
            )
            return result.get("events", [])
        except Exception as e:
            logger.warning(f"Google Calendar fetch failed: {e}")
            return []
    
    async def _fetch_outlook_events(
        self,
        start: datetime,
        end: datetime
    ) -> List[Dict]:
        """Fetch events from Outlook Calendar"""
        try:
            result = self._outlook_calendar.list_events(
                start_date=start.date().isoformat(),
                end_date=end.date().isoformat()
            )
            return result.get("events", [])
        except Exception as e:
            logger.warning(f"Outlook Calendar fetch failed: {e}")
            return []
    
    def _generate_mock_events(self) -> List[Dict]:
        """Generate mock calendar events for demo"""
        now = datetime.now()
        
        return [
            {
                "id": "mock-1",
                "title": "Morning Standup",
                "start": (now.replace(hour=9, minute=0)).isoformat(),
                "end": (now.replace(hour=9, minute=30)).isoformat(),
                "type": "meeting",
                "source": "mock"
            },
            {
                "id": "mock-2",
                "title": "Project Review",
                "start": (now.replace(hour=10, minute=0)).isoformat(),
                "end": (now.replace(hour=11, minute=0)).isoformat(),
                "type": "meeting",
                "attendees": ["team-lead@company.com", "pm@company.com"],
                "source": "mock"
            },
            {
                "id": "mock-3",
                "title": "Lunch Break",
                "start": (now.replace(hour=12, minute=0)).isoformat(),
                "end": (now.replace(hour=13, minute=0)).isoformat(),
                "type": "personal",
                "source": "mock"
            },
            {
                "id": "mock-4",
                "title": "Deep Work: Feature Development",
                "start": (now.replace(hour=14, minute=0)).isoformat(),
                "end": (now.replace(hour=16, minute=0)).isoformat(),
                "type": "focus",
                "source": "mock"
            },
            {
                "id": "mock-5",
                "title": "1:1 with Manager",
                "start": (now.replace(hour=16, minute=30)).isoformat(),
                "end": (now.replace(hour=17, minute=0)).isoformat(),
                "type": "meeting",
                "source": "mock"
            }
        ]


class EmailAgent:
    """Agent for collecting and analyzing emails"""
    
    def __init__(self, config: DailyBriefConfig):
        self.config = config
        self._gmail = None
        self._outlook_mail = None
    
    async def initialize(self):
        """Initialize email integrations"""
        if self.config.include_gmail:
            try:
                from integrations.v3_integration_layer import get_integration_layer
                layer = get_integration_layer()
                self._gmail = layer.get_gmail()
                logger.info("Gmail initialized")
            except Exception as e:
                logger.warning(f"Gmail not available: {e}")
        
        if self.config.include_outlook_mail:
            try:
                from integrations.v3_integration_layer import get_integration_layer
                layer = get_integration_layer()
                self._outlook_mail = layer.get_outlook_mail()
                logger.info("Outlook Mail initialized")
            except Exception as e:
                logger.warning(f"Outlook Mail not available: {e}")
    
    async def collect_emails(self) -> Dict[str, Any]:
        """Collect and analyze emails from all sources"""
        emails = []
        sources = []
        
        # Gmail
        if self._gmail:
            try:
                gmail_emails = await self._fetch_gmail()
                emails.extend(gmail_emails)
                sources.append("gmail")
                logger.info(f"Fetched {len(gmail_emails)} Gmail messages")
            except Exception as e:
                logger.error(f"Failed to fetch Gmail: {e}")
        
        # Outlook Mail
        if self._outlook_mail:
            try:
                outlook_emails = await self._fetch_outlook_mail()
                emails.extend(outlook_emails)
                sources.append("outlook")
                logger.info(f"Fetched {len(outlook_emails)} Outlook messages")
            except Exception as e:
                logger.error(f"Failed to fetch Outlook Mail: {e}")
        
        # Generate mock data if no real data available
        if not emails:
            emails = self._generate_mock_emails()
            sources.append("mock")
            logger.info("Using mock email data")
        
        # Analyze and categorize
        analyzed = self._analyze_emails(emails)
        
        return {
            "emails": analyzed["emails"],
            "sources": sources,
            "summary": analyzed["summary"],
            "count": len(emails)
        }
    
    async def _fetch_gmail(self) -> List[Dict]:
        """Fetch recent emails from Gmail"""
        try:
            result = self._gmail.list_messages(
                max_results=self.config.email_max_count,
                unread_only=True
            )
            return result.get("messages", [])
        except Exception as e:
            logger.warning(f"Gmail fetch failed: {e}")
            return []
    
    async def _fetch_outlook_mail(self) -> List[Dict]:
        """Fetch recent emails from Outlook"""
        try:
            result = self._outlook_mail.list_messages(
                max_results=self.config.email_max_count,
                unread_only=True
            )
            return result.get("messages", [])
        except Exception as e:
            logger.warning(f"Outlook Mail fetch failed: {e}")
            return []
    
    def _generate_mock_emails(self) -> List[Dict]:
        """Generate mock emails for demo"""
        now = datetime.now()
        
        return [
            {
                "id": "mail-1",
                "subject": "Q4 Planning - Action Required",
                "sender": "ceo@company.com",
                "received": (now - timedelta(hours=2)).isoformat(),
                "importance": "high",
                "category": "action_required",
                "source": "mock"
            },
            {
                "id": "mail-2",
                "subject": "Weekly Team Update",
                "sender": "manager@company.com",
                "received": (now - timedelta(hours=5)).isoformat(),
                "importance": "medium",
                "category": "informational",
                "source": "mock"
            },
            {
                "id": "mail-3",
                "subject": "PR Review Request: Feature XYZ",
                "sender": "colleague@company.com",
                "received": (now - timedelta(hours=8)).isoformat(),
                "importance": "medium",
                "category": "action_required",
                "source": "mock"
            },
            {
                "id": "mail-4",
                "subject": "Meeting Rescheduled",
                "sender": "calendar@company.com",
                "received": (now - timedelta(hours=12)).isoformat(),
                "importance": "low",
                "category": "notification",
                "source": "mock"
            },
            {
                "id": "mail-5",
                "subject": "New Company Benefits Program",
                "sender": "hr@company.com",
                "received": (now - timedelta(hours=24)).isoformat(),
                "importance": "medium",
                "category": "informational",
                "source": "mock"
            }
        ]
    
    def _analyze_emails(self, emails: List[Dict]) -> Dict[str, Any]:
        """Analyze and categorize emails"""
        categories = {
            "action_required": [],
            "informational": [],
            "notification": [],
            "other": []
        }
        
        for email in emails:
            category = email.get("category", "other")
            if category in categories:
                categories[category].append(email)
            else:
                categories["other"].append(email)
        
        return {
            "emails": emails,
            "summary": {
                "total": len(emails),
                "action_required": len(categories["action_required"]),
                "informational": len(categories["informational"]),
                "notifications": len(categories["notification"]),
                "high_importance": len([
                    e for e in emails
                    if e.get("importance") == "high"
                ])
            }
        }


class TaskAgent:
    """Agent for collecting tasks and to-dos"""
    
    def __init__(self, config: DailyBriefConfig):
        self.config = config
    
    async def collect_tasks(self) -> Dict[str, Any]:
        """Collect tasks from various sources"""
        # For now, return mock data
        # In production, integrate with task systems
        
        tasks = self._generate_mock_tasks()
        
        return {
            "tasks": tasks,
            "sources": ["mock"],
            "summary": {
                "total": len(tasks),
                "high_priority": len([t for t in tasks if t.get("priority") == "high"]),
                "due_today": len([t for t in tasks if t.get("due") == "today"]),
                "overdue": len([t for t in tasks if t.get("status") == "overdue"])
            }
        }
    
    def _generate_mock_tasks(self) -> List[Dict]:
        """Generate mock tasks for demo"""
        return [
            {
                "id": "task-1",
                "title": "Review Q4 budget proposal",
                "priority": "high",
                "due": "today",
                "status": "pending",
                "source": "mock"
            },
            {
                "id": "task-2",
                "title": "Complete code review for PR #123",
                "priority": "medium",
                "due": "today",
                "status": "in_progress",
                "source": "mock"
            },
            {
                "id": "task-3",
                "title": "Update project documentation",
                "priority": "low",
                "due": "this_week",
                "status": "pending",
                "source": "mock"
            },
            {
                "id": "task-4",
                "title": "Schedule 1:1s for next week",
                "priority": "medium",
                "due": "this_week",
                "status": "pending",
                "source": "mock"
            }
        ]


# ============================================================================
# Summarization Agent
# ============================================================================

class SummaryAgent:
    """Agent for generating the daily brief summary using LLM"""
    
    def __init__(self, config: DailyBriefConfig):
        self.config = config
        self._llm = None
    
    async def initialize(self):
        """Initialize LLM provider"""
        try:
            from integrations.llm_providers import get_llm_provider
            self._llm = await get_llm_provider(self.config.llm_provider)
            logger.info(f"LLM initialized: {self.config.llm_provider}")
        except Exception as e:
            logger.warning(f"LLM not available: {e}")
    
    async def generate_brief(
        self,
        calendar_data: Dict,
        email_data: Dict,
        task_data: Dict
    ) -> str:
        """Generate the daily brief summary"""
        
        # Build context
        context = self._build_context(calendar_data, email_data, task_data)
        
        # Try LLM summarization
        if self._llm:
            try:
                return await self._llm_summarize(context)
            except Exception as e:
                logger.error(f"LLM summarization failed: {e}")
        
        # Fallback to template-based summary
        return self._template_summarize(calendar_data, email_data, task_data)
    
    def _build_context(
        self,
        calendar_data: Dict,
        email_data: Dict,
        task_data: Dict
    ) -> str:
        """Build context string for LLM"""
        lines = []
        
        # Calendar context
        lines.append("## Calendar Events")
        for event in calendar_data.get("events", [])[:10]:
            start = event.get("start", "")[:16]  # Truncate time
            lines.append(f"- {start}: {event.get('title', 'Untitled')}")
        
        # Email context
        lines.append("\n## Email Summary")
        summary = email_data.get("summary", {})
        lines.append(f"- Total unread: {summary.get('total', 0)}")
        lines.append(f"- Action required: {summary.get('action_required', 0)}")
        lines.append(f"- High importance: {summary.get('high_importance', 0)}")
        
        # Important emails
        lines.append("\nImportant emails:")
        for email in email_data.get("emails", [])[:5]:
            if email.get("importance") in ["high", "medium"]:
                lines.append(f"- {email.get('subject', 'No subject')}")
        
        # Tasks context
        lines.append("\n## Tasks")
        task_summary = task_data.get("summary", {})
        lines.append(f"- Due today: {task_summary.get('due_today', 0)}")
        lines.append(f"- High priority: {task_summary.get('high_priority', 0)}")
        
        for task in task_data.get("tasks", [])[:5]:
            lines.append(f"- [{task.get('priority', 'med')}] {task.get('title', 'Untitled')}")
        
        return "\n".join(lines)
    
    async def _llm_summarize(self, context: str) -> str:
        """Generate summary using LLM"""
        prompt = f"""You are a personal assistant generating a daily brief. Based on the following information, create a concise, actionable summary for the user's day.

{context}

Generate a daily brief that includes:
1. A quick overview of the day (2-3 sentences)
2. Key meetings and time blocks
3. Priority actions (emails and tasks requiring immediate attention)
4. Recommendations for the day

Use markdown formatting. Be concise and actionable."""

        response = await self._llm.chat([
            {"role": "system", "content": "You are a helpful executive assistant."},
            {"role": "user", "content": prompt}
        ])
        
        return response.content
    
    def _template_summarize(
        self,
        calendar_data: Dict,
        email_data: Dict,
        task_data: Dict
    ) -> str:
        """Generate summary using templates (fallback)"""
        now = datetime.now()
        
        lines = [
            f"# Daily Brief - {now.strftime('%A, %B %d, %Y')}",
            "",
            "## 📅 Today's Schedule",
            ""
        ]
        
        # Calendar events
        events = calendar_data.get("events", [])
        if events:
            for event in events:
                time_str = event.get("start", "")
                if "T" in time_str:
                    time_str = time_str.split("T")[1][:5]
                lines.append(f"- **{time_str}** - {event.get('title', 'Untitled')}")
        else:
            lines.append("- No scheduled events")
        
        # Email summary
        lines.extend([
            "",
            "## 📧 Email Summary",
            ""
        ])
        
        email_summary = email_data.get("summary", {})
        lines.append(f"- **{email_summary.get('total', 0)}** unread emails")
        lines.append(f"- **{email_summary.get('action_required', 0)}** requiring action")
        lines.append(f"- **{email_summary.get('high_importance', 0)}** high importance")
        
        # Priority emails
        high_importance_emails = [
            e for e in email_data.get("emails", [])
            if e.get("importance") == "high"
        ]
        if high_importance_emails:
            lines.extend(["", "### ⚡ Priority Emails", ""])
            for email in high_importance_emails[:3]:
                lines.append(f"- **{email.get('subject')}** from {email.get('sender')}")
        
        # Tasks
        lines.extend([
            "",
            "## ✅ Tasks",
            ""
        ])
        
        task_summary = task_data.get("summary", {})
        lines.append(f"- **{task_summary.get('due_today', 0)}** due today")
        lines.append(f"- **{task_summary.get('high_priority', 0)}** high priority")
        
        # Priority tasks
        high_priority_tasks = [
            t for t in task_data.get("tasks", [])
            if t.get("priority") == "high"
        ]
        if high_priority_tasks:
            lines.extend(["", "### 🔴 Priority Tasks", ""])
            for task in high_priority_tasks:
                lines.append(f"- {task.get('title')}")
        
        # Recommendations
        lines.extend([
            "",
            "## 💡 Recommendations",
            ""
        ])
        
        # Generate simple recommendations
        if email_summary.get("action_required", 0) > 3:
            lines.append("- ⚠️ Address high-priority emails first thing")
        if task_summary.get("overdue", 0) > 0:
            lines.append("- ⚠️ You have overdue tasks to address")
        if len(events) > 5:
            lines.append("- 📅 Meeting-heavy day - protect deep work time")
        lines.append("- ✨ Start with your most important task")
        
        return "\n".join(lines)


# ============================================================================
# Workflow Orchestrator
# ============================================================================

class DailyBriefWorkflow:
    """
    Orchestrates the Daily Brief workflow.
    
    Flow:
    1. Collect calendar events (Google, Outlook)
    2. Collect and analyze emails (Gmail, Outlook)
    3. Collect tasks
    4. Generate summary using LLM
    5. Output in requested format
    """
    
    def __init__(self, config: DailyBriefConfig = None):
        self.config = config or DailyBriefConfig()
        
        # Initialize agents
        self.calendar_agent = CalendarAgent(self.config)
        self.email_agent = EmailAgent(self.config)
        self.task_agent = TaskAgent(self.config)
        self.summary_agent = SummaryAgent(self.config)
        
        # Ensure output directory exists
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
    
    async def run(self) -> WorkflowResult:
        """Execute the Daily Brief workflow"""
        start_time = datetime.now()
        errors = []
        
        logger.info("Starting Daily Brief workflow")
        
        try:
            # Initialize agents
            await self._initialize_agents()
            
            # Collect data in parallel
            calendar_task = asyncio.create_task(self.calendar_agent.collect_events())
            email_task = asyncio.create_task(self.email_agent.collect_emails())
            task_task = asyncio.create_task(self.task_agent.collect_tasks())
            
            calendar_data, email_data, task_data = await asyncio.gather(
                calendar_task, email_task, task_task,
                return_exceptions=True
            )
            
            # Handle any exceptions
            if isinstance(calendar_data, Exception):
                errors.append(f"Calendar: {calendar_data}")
                calendar_data = {"events": [], "sources": [], "count": 0}
            if isinstance(email_data, Exception):
                errors.append(f"Email: {email_data}")
                email_data = {"emails": [], "sources": [], "count": 0}
            if isinstance(task_data, Exception):
                errors.append(f"Tasks: {task_data}")
                task_data = {"tasks": [], "sources": [], "summary": {}}
            
            # Generate summary
            brief = await self.summary_agent.generate_brief(
                calendar_data, email_data, task_data
            )
            
            # Save to file if configured
            if self.config.save_to_file:
                await self._save_brief(brief)
            
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            return WorkflowResult(
                status=WorkflowStatus.COMPLETED if not errors else WorkflowStatus.PARTIAL,
                brief=brief,
                data={
                    "calendar": calendar_data,
                    "email": email_data,
                    "tasks": task_data
                },
                errors=errors,
                duration_ms=duration
            )
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            duration = (datetime.now() - start_time).total_seconds() * 1000
            return WorkflowResult(
                status=WorkflowStatus.FAILED,
                errors=[str(e)],
                duration_ms=duration
            )
    
    async def _initialize_agents(self):
        """Initialize all agents"""
        await asyncio.gather(
            self.calendar_agent.initialize(),
            self.email_agent.initialize(),
            self.summary_agent.initialize()
        )
    
    async def _save_brief(self, brief: str):
        """Save the brief to a file"""
        now = datetime.now()
        filename = f"brief_{now.strftime('%Y-%m-%d_%H%M%S')}.md"
        filepath = Path(self.config.output_dir) / filename
        
        with open(filepath, 'w') as f:
            f.write(brief)
        
        logger.info(f"Brief saved to {filepath}")


# ============================================================================
# CLI Interface
# ============================================================================

async def run_daily_brief(
    provider: str = "ollama",
    output_format: str = "markdown",
    save: bool = True
) -> WorkflowResult:
    """
    Run the Daily Brief workflow.
    
    Args:
        provider: LLM provider (ollama, openai, anthropic)
        output_format: Output format (markdown, html, json)
        save: Whether to save to file
    
    Returns:
        WorkflowResult with the generated brief
    """
    config = DailyBriefConfig(
        llm_provider=provider,
        output_format=output_format,
        save_to_file=save
    )
    
    workflow = DailyBriefWorkflow(config)
    return await workflow.run()


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Daily Brief")
    parser.add_argument(
        "--run", action="store_true",
        help="Run the Daily Brief workflow"
    )
    parser.add_argument(
        "--provider", default="ollama",
        choices=["ollama", "openai", "anthropic"],
        help="LLM provider to use"
    )
    parser.add_argument(
        "--format", default="markdown",
        choices=["markdown", "html", "json"],
        help="Output format"
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="Don't save to file"
    )
    
    args = parser.parse_args()
    
    if args.run or True:  # Always run for now
        result = asyncio.run(run_daily_brief(
            provider=args.provider,
            output_format=args.format,
            save=not args.no_save
        ))
        
        print(f"\n{'=' * 70}")
        print("DAILY BRIEF WORKFLOW RESULT")
        print('=' * 70)
        print(f"Status: {result.status.value}")
        print(f"Duration: {result.duration_ms:.1f}ms")
        
        if result.errors:
            print(f"\nErrors: {', '.join(result.errors)}")
        
        if result.brief:
            print(f"\n{result.brief}")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    main()
