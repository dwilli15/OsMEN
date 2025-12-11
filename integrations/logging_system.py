"""
OsMEN Agent Logging System
Provides continuity between sessions by logging all agent actions

ALL PATHS ARE IMPORTED FROM integrations/paths.py - SINGLE SOURCE OF TRUTH

Location: D:/OsMEN/logs/
Structure:
- agent_sessions/      # Per-session logs
- check_ins/          # Daily check-in status
- audio_generations/  # Briefing/podcast generation logs
- system_events/      # System-level events

Integration Points:
- paths.py: All path constants (LOGS_ROOT, etc.)
- orchestration.py: Pipeline execution and state
- daily_briefing_generator.py: Briefing generation
- osmen_cli.py: CLI commands
"""

import json
import os
from dataclasses import asdict, dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import paths from single source of truth
from integrations.paths import HB411_OBSIDIAN as OBSIDIAN_ROOT
from integrations.paths import (
    LOG_AGENT_SESSIONS,
    LOG_AUDIO_GENERATIONS,
    LOG_CHECK_INS,
    LOG_SYSTEM_EVENTS,
    LOGS_ROOT,
    OSMEN_ROOT,
)


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LogEntry:
    """Standard log entry structure"""

    timestamp: str
    agent: str
    action: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    status: str
    notes: str = ""
    level: str = "info"
    duration_ms: Optional[int] = None

    def to_dict(self) -> Dict:
        return asdict(self)


class AgentLogger:
    """Central logging for all OsMEN agents"""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.session_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.session_file = LOG_AGENT_SESSIONS / f"{self.session_id}_{agent_name}.json"
        self.entries: List[LogEntry] = []
        self._start_session()

    def _start_session(self):
        """Initialize session log"""
        self.log(
            action="session_start",
            inputs={"agent": self.agent_name},
            outputs={"session_id": self.session_id},
            status="active",
            notes="Session initialized",
        )
        self._save()

    def log(
        self,
        action: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        status: str,
        notes: str = "",
        level: str = "info",
        duration_ms: Optional[int] = None,
    ) -> LogEntry:
        """Add a log entry"""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            agent=self.agent_name,
            action=action,
            inputs=inputs,
            outputs=outputs,
            status=status,
            notes=notes,
            level=level,
            duration_ms=duration_ms,
        )
        self.entries.append(entry)
        self._save()
        return entry

    def _save(self):
        """Save session log to file"""
        with open(self.session_file, "w") as f:
            json.dump(
                {
                    "session_id": self.session_id,
                    "agent": self.agent_name,
                    "started": self.entries[0].timestamp if self.entries else None,
                    "entries": [e.to_dict() for e in self.entries],
                },
                f,
                indent=2,
            )

    def end_session(self, summary: str = ""):
        """Close out the session"""
        self.log(
            action="session_end",
            inputs={},
            outputs={"total_entries": len(self.entries)},
            status="completed",
            notes=summary,
        )


class CheckInTracker:
    """Track daily check-in status"""

    def __init__(self):
        self.today = date.today().isoformat()
        self.status_file = LOG_CHECK_INS / f"{self.today}_checkin.json"

    def get_status(self) -> Dict:
        """Get today's check-in status"""
        if self.status_file.exists():
            with open(self.status_file) as f:
                return json.load(f)
        return {
            "date": self.today,
            "am_completed": False,
            "am_time": None,
            "am_file": None,
            "pm_completed": False,
            "pm_time": None,
            "pm_file": None,
            "briefing_generated": False,
            "briefing_file": None,
        }

    def update_status(self, updates: Dict):
        """Update check-in status"""
        status = self.get_status()
        status.update(updates)
        with open(self.status_file, "w") as f:
            json.dump(status, f, indent=2)

    def verify_am_checkin(self) -> bool:
        """Check if AM check-in is done"""
        return self.get_status()["am_completed"]

    def verify_pm_checkin(self) -> bool:
        """Check if PM check-in is done"""
        return self.get_status()["pm_completed"]

    def prompt_if_missing(self) -> Optional[str]:
        """Return prompt message if check-in needed"""
        status = self.get_status()
        now = datetime.now().hour

        if now >= 6 and now < 12 and not status["am_completed"]:
            return (
                "🌅 Good morning! Please complete your AM check-in before continuing."
            )

        if now >= 20 and not status["pm_completed"]:
            return "🌙 Good evening! Please complete your PM check-in."

        return None


class AudioGenerationLog:
    """Log audio generation events"""

    @staticmethod
    def log_generation(
        audio_type: str,  # "briefing" or "podcast"
        script_file: str,
        audio_file: str,
        duration_sec: int,
        voice: str,
        source_data: Dict,
    ):
        """Log an audio generation"""
        today = date.today().isoformat()
        log_file = LOG_AUDIO_GENERATIONS / f"{today}_audio.json"

        # Load existing or create new
        if log_file.exists():
            with open(log_file) as f:
                data = json.load(f)
        else:
            data = {"date": today, "generations": []}

        data["generations"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "type": audio_type,
                "script_file": script_file,
                "audio_file": audio_file,
                "duration_sec": duration_sec,
                "voice": voice,
                "source_data": source_data,
            }
        )

        with open(log_file, "w") as f:
            json.dump(data, f, indent=2)


class SystemEventLog:
    """Log system-level events"""

    @staticmethod
    def log_event(event_type: str, source: str, details: Dict, level: str = "info"):
        """Log a system event"""
        today = date.today().isoformat()
        log_file = LOG_SYSTEM_EVENTS / f"{today}_events.json"

        if log_file.exists():
            with open(log_file) as f:
                data = json.load(f)
        else:
            data = {"date": today, "events": []}

        data["events"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "type": event_type,
                "source": source,
                "details": details,
                "level": level,
            }
        )

        with open(log_file, "w") as f:
            json.dump(data, f, indent=2)


def get_recent_context(days: int = 3) -> Dict:
    """Get recent session context for continuity"""
    context = {
        "recent_sessions": [],
        "recent_checkins": [],
        "recent_audio": [],
        "recent_events": [],
    }

    today = date.today()

    # Gather recent session logs
    session_dir = LOG_AGENT_SESSIONS
    for f in sorted(session_dir.glob("*.json"), reverse=True)[:10]:
        with open(f) as file:
            session = json.load(file)
            context["recent_sessions"].append(
                {
                    "session_id": session.get("session_id"),
                    "agent": session.get("agent"),
                    "started": session.get("started"),
                    "entry_count": len(session.get("entries", [])),
                }
            )

    # Gather recent check-ins
    checkin_dir = LOG_CHECK_INS
    for f in sorted(checkin_dir.glob("*.json"), reverse=True)[:days]:
        with open(f) as file:
            context["recent_checkins"].append(json.load(file))

    # Gather recent audio generations
    audio_dir = LOG_AUDIO_GENERATIONS
    for f in sorted(audio_dir.glob("*.json"), reverse=True)[:days]:
        with open(f) as file:
            context["recent_audio"].append(json.load(file))

    return context


# Convenience function for agents
def agent_startup_check(agent_name: str) -> tuple[AgentLogger, Optional[str]]:
    """
    Standard startup check for all agents.
    Returns logger and optional prompt message.

    Usage:
        logger, prompt = agent_startup_check("daily-briefing")
        if prompt:
            print(prompt)
            # May want to require check-in before proceeding
    """
    logger = AgentLogger(agent_name)
    tracker = CheckInTracker()
    prompt = tracker.prompt_if_missing()

    # Log the check-in status
    logger.log(
        action="startup_checkin_verify",
        inputs={"current_time": datetime.now().isoformat()},
        outputs=tracker.get_status(),
        status="verified",
        notes=prompt or "Check-ins up to date",
    )

    return logger, prompt


if __name__ == "__main__":
    # Demo/test
    print("OsMEN Agent Logging System")
    print("=" * 50)

    # Test agent logger
    logger, prompt = agent_startup_check("test-agent")

    if prompt:
        print(f"\n⚠️ {prompt}")

    # Log some actions
    logger.log(
        action="test_action",
        inputs={"test": "data"},
        outputs={"result": "success"},
        status="completed",
        notes="Test log entry",
    )

    logger.end_session("Test session completed")

    print(f"\n✅ Session logged to: {logger.session_file}")

    # Show recent context
    context = get_recent_context()
    print(f"\n📊 Recent Context:")
    print(f"   Sessions: {len(context['recent_sessions'])}")
    print(f"   Check-ins: {len(context['recent_checkins'])}")
    print(f"   Audio generations: {len(context['recent_audio'])}")
