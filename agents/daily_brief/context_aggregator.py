"""
Context Aggregator for Daily Briefings
======================================

Production-ready module that gathers comprehensive context for briefing generation:
1. Previous 3 days of check-ins (AM + PM)
2. Previous 3 days of briefing scripts
3. Pending to-do items from trackers
4. Current week's syllabus schedule
5. Course progress and due dates
6. ADHD patterns and energy trends
7. Meditation practice continuity

This ensures briefings have full context of:
- User's recent capacity and energy patterns
- What was accomplished vs. carried over
- What's due soon in the course
- Continuity in ADHD strategies that are working

Usage:
    from agents.daily_brief.context_aggregator import ContextAggregator

    aggregator = ContextAggregator()
    context = aggregator.gather_full_context()
"""

import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from integrations.orchestration import Paths


@dataclass
class CheckInData:
    """Structured check-in data from markdown files"""

    date: str
    period: str  # "AM" or "PM"
    energy: int = 5
    sleep_hours: float = 0
    sleep_quality: int = 3
    priorities: List[str] = field(default_factory=list)
    focus_blocks_planned: List[str] = field(default_factory=list)
    focus_blocks_completed: List[str] = field(default_factory=list)
    adhd_state: str = "moderate"
    meditation_completed: bool = False
    meditation_type: str = ""
    meditation_duration: int = 0
    course_reading_goal: str = ""
    course_assignment_status: str = ""
    productivity_rate: int = 70  # PM only
    mood_trend: str = "stable"  # PM only
    carryover_tasks: List[str] = field(default_factory=list)  # PM only
    accomplishments: List[str] = field(default_factory=list)  # PM only
    tomorrow_focus: str = ""  # PM only
    notes: str = ""
    raw_content: str = ""


@dataclass
class BriefingData:
    """Previous briefing script data"""

    date: str
    word_count: int
    key_priorities: List[str] = field(default_factory=list)
    adhd_tip: str = ""
    boundary_reminder: str = ""
    content: str = ""


@dataclass
class SyllabusContext:
    """Current syllabus/schedule context"""

    current_week: int
    week_topic: str
    week_date: str
    class_day: str
    class_time: str
    readings_due: List[str] = field(default_factory=list)
    assignments_due: List[Dict] = field(default_factory=list)
    days_until_class: int = 0
    next_deadline: Optional[Dict] = None
    is_class_today: bool = False
    is_break_week: bool = False


@dataclass
class ADHDContext:
    """ADHD patterns from recent check-ins"""

    avg_energy_3day: float = 5.0
    energy_trend: str = "stable"  # "improving", "declining", "stable"
    best_time_of_day: str = "morning"
    common_derailers: List[str] = field(default_factory=list)
    working_strategies: List[str] = field(default_factory=list)
    recommended_focus_block_length: int = 25  # Based on recent success
    medication_consistency: float = 0.0


@dataclass
class ProgressContext:
    """Course and practice progress"""

    readings_completed: int = 0
    readings_total: int = 0
    readings_behind: int = 0
    reading_responses_done: int = 0
    reading_responses_required: int = 5
    days_until_next_assignment: int = 999
    next_assignment: str = ""
    meditation_streak: int = 0
    meditation_sessions_this_week: int = 0


@dataclass
class AggregatedContext:
    """Full aggregated context for briefing generation"""

    # Basic info
    date: str
    day_name: str
    date_formatted: str

    # Recent check-ins (most recent first)
    checkins: List[CheckInData] = field(default_factory=list)

    # Recent briefings
    briefings: List[BriefingData] = field(default_factory=list)

    # Structured contexts
    syllabus: Optional[SyllabusContext] = None
    adhd: Optional[ADHDContext] = None
    progress: Optional[ProgressContext] = None

    # Derived for quick access
    today_am_checkin: Optional[CheckInData] = None
    yesterday_pm_checkin: Optional[CheckInData] = None

    # Pending items
    pending_tasks: List[str] = field(default_factory=list)
    carryover_from_yesterday: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template rendering"""
        return {
            "date": self.date,
            "day_name": self.day_name,
            "date_formatted": self.date_formatted,
            "checkins": [vars(c) for c in self.checkins],
            "briefings": [vars(b) for b in self.briefings],
            "syllabus": vars(self.syllabus) if self.syllabus else {},
            "adhd": vars(self.adhd) if self.adhd else {},
            "progress": vars(self.progress) if self.progress else {},
            "today_am_checkin": (
                vars(self.today_am_checkin) if self.today_am_checkin else {}
            ),
            "yesterday_pm_checkin": (
                vars(self.yesterday_pm_checkin) if self.yesterday_pm_checkin else {}
            ),
            "pending_tasks": self.pending_tasks,
            "carryover_from_yesterday": self.carryover_from_yesterday,
        }


class CheckInParser:
    """Parse check-in markdown files into structured data.

    Refactored to use specialized extractor methods, reducing complexity
    from 45 to <15 per method (PHOENIX Protocol compliance).
    """

    # Regex patterns as class constants for reuse
    ENERGY_PATTERNS = [
        (r"\[x\]\s*1\s*-\s*Very Low", 1),
        (r"\[x\]\s*2\s*-\s*Low", 2),
        (r"\[x\]\s*3\s*-\s*Moderate", 3),
        (r"\[x\]\s*4\s*-\s*Good", 4),
        (r"\[x\]\s*5\s*-\s*Excellent", 5),
        (r"Energy Level[:\s]*(\d+)/10", None),
        (r"Energy[:\s]*(\d+)", None),
    ]

    ADHD_STATE_PATTERNS = [
        (r"\[x\]\s*Clear headed", "clear"),
        (r"\[x\]\s*Slightly foggy", "foggy"),
        (r"\[x\]\s*Struggling to start", "struggling"),
        (r"\[x\]\s*Hyperfocused on wrong thing", "misdirected"),
    ]

    @staticmethod
    def parse_file(filepath: Path) -> Optional[CheckInData]:
        """Parse a check-in file and extract structured data."""
        if not filepath.exists():
            return None

        try:
            content = filepath.read_text(encoding="utf-8")
            return CheckInParser.parse_content(content, filepath.stem)
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
            return None

    @staticmethod
    def parse_content(content: str, filename: str) -> CheckInData:
        """Parse check-in markdown content (main orchestrator method)."""
        # Extract date and period from filename
        parts = filename.rsplit("-", 1)
        date_str = parts[0] if len(parts) > 1 else filename
        period = parts[1] if len(parts) > 1 else "AM"

        data = CheckInData(date=date_str, period=period, raw_content=content)

        # Delegate to specialized extractors
        CheckInParser._extract_energy(content, data)
        CheckInParser._extract_sleep(content, data)
        CheckInParser._extract_priorities(content, data)
        CheckInParser._extract_focus_blocks(content, data)
        CheckInParser._extract_adhd_state(content, data)
        CheckInParser._extract_meditation(content, data)
        CheckInParser._extract_course_progress(content, data)

        if period == "PM":
            CheckInParser._extract_pm_fields(content, data)

        CheckInParser._extract_notes(content, data)

        return data

    @staticmethod
    def _extract_energy(content: str, data: CheckInData) -> None:
        """Extract energy level from content."""
        for pattern, fixed_value in CheckInParser.ENERGY_PATTERNS:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                data.energy = fixed_value if fixed_value else int(match.group(1))
                break

    @staticmethod
    def _extract_sleep(content: str, data: CheckInData) -> None:
        """Extract sleep hours and quality from content."""
        sleep_hours = re.search(r"Hours[:\s]*(\d+\.?\d*)", content)
        if sleep_hours:
            try:
                data.sleep_hours = float(sleep_hours.group(1))
            except ValueError:
                pass

        sleep_quality = re.search(r"Quality[:\s]*\(?(\d+)/5\)?", content)
        if sleep_quality:
            data.sleep_quality = int(sleep_quality.group(1))

    @staticmethod
    def _extract_priorities(content: str, data: CheckInData) -> None:
        """Extract priorities list from content."""
        priority_section = re.search(
            r"(?:Top 3 Priorities|Priorities Today).*?\n((?:\d+\..+?\n)+)",
            content,
            re.IGNORECASE | re.DOTALL,
        )
        if priority_section:
            raw_priorities = re.findall(
                r"\d+\.\s*(.+?)(?:\n|$)", priority_section.group(1)
            )
            data.priorities = [
                p.strip()
                for p in raw_priorities
                if p.strip() and not p.strip().startswith("#") and len(p.strip()) > 1
            ]

    @staticmethod
    def _extract_focus_blocks(content: str, data: CheckInData) -> None:
        """Extract planned and completed focus blocks."""
        focus_section = re.search(
            r"### Focus Blocks Planned.*?\n((?:.*?Deep Work Block.*?\n)+)",
            content,
            re.IGNORECASE | re.DOTALL,
        )
        if focus_section:
            focus_lines = focus_section.group(1)
            focus_blocks = re.findall(
                r"\[([x ])\]\s*Deep Work Block \d+.*?:\s*(.+?)(?:\n|$)",
                focus_lines,
                re.IGNORECASE,
            )
            data.focus_blocks_planned = [
                fb[1].strip()
                for fb in focus_blocks
                if fb[1].strip()
                and not fb[1].strip().startswith("-")
                and len(fb[1].strip()) > 1
            ]
            data.focus_blocks_completed = [
                fb[1].strip()
                for fb in focus_blocks
                if fb[0].lower() == "x" and fb[1].strip() and len(fb[1].strip()) > 1
            ]

    @staticmethod
    def _extract_adhd_state(content: str, data: CheckInData) -> None:
        """Extract ADHD mental state from content."""
        for pattern, state in CheckInParser.ADHD_STATE_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                data.adhd_state = state
                break

    @staticmethod
    def _extract_meditation(content: str, data: CheckInData) -> None:
        """Extract meditation practice data."""
        if re.search(r"\[x\]\s*Completed morning practice", content, re.IGNORECASE):
            data.meditation_completed = True

        med_type = re.search(r"Type[:\s]+([^\n]+)", content)
        if med_type:
            med_val = med_type.group(1).strip()
            if med_val and len(med_val) > 1:
                data.meditation_type = med_val

        med_duration = re.search(r"Duration[:\s]*\(?(\d+)", content)
        if med_duration:
            data.meditation_duration = int(med_duration.group(1))

    @staticmethod
    def _extract_course_progress(content: str, data: CheckInData) -> None:
        """Extract course-related progress data."""
        reading_goal = re.search(r"Chapter/Section[:\s]+([^\n]+)", content)
        if reading_goal:
            goal_val = reading_goal.group(1).strip()
            if goal_val and len(goal_val) > 1:
                data.course_reading_goal = goal_val

        assignment = re.search(r"Current assignment[:\s]+([^\n]+)", content)
        if assignment:
            assign_val = assignment.group(1).strip()
            if assign_val and len(assign_val) > 1:
                data.course_assignment_status = assign_val

    @staticmethod
    def _extract_pm_fields(content: str, data: CheckInData) -> None:
        """Extract PM-specific fields (productivity, accomplishments, etc.)."""
        # Productivity rate
        productivity = re.search(
            r"(?:Productivity|Overall productivity)[:\s]*(\d+)%?",
            content,
            re.IGNORECASE,
        )
        if productivity:
            data.productivity_rate = int(productivity.group(1))

        # Accomplishments
        accomplishments_section = re.search(
            r"(?:### Accomplishments|## Accomplishments).*?\n((?:\d+\..+?\n)+)",
            content,
            re.IGNORECASE | re.DOTALL,
        )
        if accomplishments_section:
            raw_acc = re.findall(
                r"\d+\.\s*(.+?)(?:\n|$)", accomplishments_section.group(1)
            )
            data.accomplishments = [
                a.strip() for a in raw_acc if a.strip() and len(a.strip()) > 1
            ]

        # Carryover tasks
        carryover_section = re.search(
            r"(?:### Incomplete Items|Carryover).*?\n((?:[-*]\s*.+?\n)+)",
            content,
            re.IGNORECASE | re.DOTALL,
        )
        if carryover_section:
            raw_carryover = re.findall(
                r"[-*]\s*(.+?)(?:\n|$)", carryover_section.group(1)
            )
            data.carryover_tasks = [
                c.strip() for c in raw_carryover if c.strip() and len(c.strip()) > 1
            ]

        # Tomorrow's priorities
        tomorrow_section = re.search(
            r"(?:### Top 3 Priorities|Tomorrow Preparation).*?\n((?:\d+\..+?\n)+)",
            content,
            re.IGNORECASE | re.DOTALL,
        )
        if tomorrow_section:
            raw_tomorrow = re.findall(
                r"\d+\.\s*(.+?)(?:\n|$)", tomorrow_section.group(1)
            )
            tomorrow_tasks = [
                t.strip() for t in raw_tomorrow if t.strip() and len(t.strip()) > 1
            ]
            if tomorrow_tasks:
                data.tomorrow_focus = tomorrow_tasks[0]

    @staticmethod
    def _extract_notes(content: str, data: CheckInData) -> None:
        """Extract notes section from content."""
        notes_match = re.search(r"##\s*Notes\s*\n(.*?)(?:\n---|\Z)", content, re.DOTALL)
        if notes_match:
            notes = notes_match.group(1).strip()
            notes = re.sub(r"<!--.*?-->", "", notes, flags=re.DOTALL).strip()
            if notes and len(notes) > 1:
                data.notes = notes


class SyllabusParser:
    """Parse and interpret syllabus for current context"""

    def __init__(self):
        self.course_data_path = Paths.HB411_ROOT / "course_data.json"
        self.course_data = self._load_course_data()

    def _load_course_data(self) -> Dict:
        """Load course data JSON"""
        if self.course_data_path.exists():
            with open(self.course_data_path, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def get_current_context(self, target_date: date = None) -> SyllabusContext:
        """Get syllabus context for a given date"""
        target_date = target_date or date.today()

        schedule = self.course_data.get("schedule", [])
        course = self.course_data.get("course", {})

        # Find current week based on date
        current_week_data = None
        current_week = 0

        for week_data in schedule:
            week_date = datetime.strptime(week_data["date"], "%Y-%m-%d").date()
            # Week is "current" if target_date is within 7 days after week start
            if week_date <= target_date < week_date + timedelta(days=7):
                current_week_data = week_data
                current_week = week_data.get("week", 0)
                break
            # Also track most recent past week as fallback
            if week_date <= target_date:
                current_week_data = week_data
                current_week = week_data.get("week", 0)

        if not current_week_data:
            # Default context if no week matches
            return SyllabusContext(
                current_week=0,
                week_topic="Course not in session",
                week_date="",
                class_day=course.get("schedule", {}).get("day", "Thursday"),
                class_time=course.get("schedule", {}).get(
                    "time", "10:00 AM - 12:00 PM CT"
                ),
            )

        # Calculate days until class
        class_day_name = course.get("schedule", {}).get("day", "Thursday")
        class_date = datetime.strptime(current_week_data["date"], "%Y-%m-%d").date()
        days_until = (class_date - target_date).days
        if days_until < 0:
            days_until = 7 + days_until  # Next week

        # Find next deadline
        next_deadline = self._find_next_deadline(target_date)

        # Build assignments due
        assignments_due = []
        for assignment in current_week_data.get("assignments_due", []):
            assignments_due.append(
                {
                    "name": assignment,
                    "is_required": "(required)" in assignment.lower(),
                }
            )

        return SyllabusContext(
            current_week=current_week,
            week_topic=current_week_data.get("topic", ""),
            week_date=current_week_data.get("date", ""),
            class_day=class_day_name,
            class_time=course.get("schedule", {}).get("time", "10:00 AM - 12:00 PM CT"),
            readings_due=current_week_data.get("readings", []),
            assignments_due=assignments_due,
            days_until_class=days_until if days_until >= 0 else 0,
            next_deadline=next_deadline,
            is_class_today=(days_until == 0),
            is_break_week=(current_week_data.get("class_type") == "break"),
        )

    def _find_next_deadline(self, target_date: date) -> Optional[Dict]:
        """Find the next assignment deadline"""
        assignments = self.course_data.get("assignments", [])

        upcoming = []
        for assign in assignments:
            if "due_date" in assign:
                due = datetime.strptime(assign["due_date"], "%Y-%m-%d").date()
                if due >= target_date:
                    upcoming.append(
                        {
                            "name": assign["name"],
                            "due_date": assign["due_date"],
                            "days_until": (due - target_date).days,
                            "weight": assign.get("weight", ""),
                        }
                    )

        if upcoming:
            upcoming.sort(key=lambda x: x["days_until"])
            return upcoming[0]
        return None


class ContextAggregator:
    """
    Main aggregator that combines all context sources for briefing generation.

    This is the production-ready implementation that ensures briefings have
    full context of user's recent history, schedule, and patterns.
    """

    def __init__(self, lookback_days: int = 3):
        self.lookback_days = lookback_days
        self.today = date.today()
        self.journal_dir = Paths.VAULT_JOURNAL / "daily"
        self.scripts_dir = Paths.HB411_BRIEFING_SCRIPTS
        self.goals_dir = Paths.VAULT_GOALS
        self.syllabus_parser = SyllabusParser()

    def gather_full_context(self) -> AggregatedContext:
        """Gather complete context for briefing generation"""
        context = AggregatedContext(
            date=self.today.isoformat(),
            day_name=self.today.strftime("%A"),
            date_formatted=self.today.strftime("%B %d, %Y"),
        )

        # Gather check-ins from past N days
        context.checkins = self._gather_checkins()

        # Set quick-access references
        for checkin in context.checkins:
            if checkin.date == self.today.isoformat() and checkin.period == "AM":
                context.today_am_checkin = checkin
            elif (
                checkin.date == (self.today - timedelta(days=1)).isoformat()
                and checkin.period == "PM"
            ):
                context.yesterday_pm_checkin = checkin

        # Gather previous briefings
        context.briefings = self._gather_briefings()

        # Get syllabus context
        context.syllabus = self.syllabus_parser.get_current_context(self.today)

        # Calculate ADHD patterns
        context.adhd = self._calculate_adhd_context(context.checkins)

        # Get progress context
        context.progress = self._get_progress_context()

        # Aggregate pending tasks and carryover
        context.carryover_from_yesterday = self._get_carryover(
            context.yesterday_pm_checkin
        )
        context.pending_tasks = self._aggregate_pending_tasks(context)

        return context

    def _gather_checkins(self) -> List[CheckInData]:
        """Gather check-ins from past N days"""
        checkins = []

        for days_ago in range(self.lookback_days + 1):
            check_date = self.today - timedelta(days=days_ago)
            date_str = check_date.isoformat()

            # Try AM check-in
            am_path = self.journal_dir / f"{date_str}-AM.md"
            am_data = CheckInParser.parse_file(am_path)
            if am_data:
                checkins.append(am_data)

            # Try PM check-in
            pm_path = self.journal_dir / f"{date_str}-PM.md"
            pm_data = CheckInParser.parse_file(pm_path)
            if pm_data:
                checkins.append(pm_data)

        return checkins

    def _gather_briefings(self) -> List[BriefingData]:
        """Gather previous briefing scripts"""
        briefings = []

        for days_ago in range(1, self.lookback_days + 1):
            script_date = self.today - timedelta(days=days_ago)
            script_path = self.scripts_dir / f"{script_date.isoformat()}.txt"

            if script_path.exists():
                content = script_path.read_text(encoding="utf-8")

                # Extract key info from previous briefing
                briefings.append(
                    BriefingData(
                        date=script_date.isoformat(),
                        word_count=len(content.split()),
                        content=content,
                        # Extract priorities mentioned
                        key_priorities=re.findall(
                            r"number one today[:\s]*([^.]+)", content, re.IGNORECASE
                        ),
                    )
                )

        return briefings

    def _calculate_adhd_context(self, checkins: List[CheckInData]) -> ADHDContext:
        """Calculate ADHD patterns from recent check-ins.

        Refactored from complexity 22 to ~12 (PHOENIX Protocol compliance).
        """
        context = ADHDContext()

        if not checkins:
            return context

        am_checkins = [c for c in checkins if c.period == "AM"]

        # Calculate energy patterns
        self._calculate_energy_patterns(am_checkins, context)

        # Determine best time of day
        self._determine_best_time(am_checkins, context)

        # Recommend focus block length
        self._recommend_focus_length(am_checkins, context)

        # Track working strategies
        self._extract_working_strategies(checkins, context)

        return context

    def _calculate_energy_patterns(
        self, am_checkins: List[CheckInData], context: ADHDContext
    ) -> None:
        """Calculate 3-day average energy and trend."""
        if not am_checkins:
            return

        energies = [c.energy for c in am_checkins[:3]]
        context.avg_energy_3day = sum(energies) / len(energies)

        # Determine trend
        if len(energies) >= 2:
            if energies[0] > energies[-1] + 1:
                context.energy_trend = "improving"
            elif energies[0] < energies[-1] - 1:
                context.energy_trend = "declining"
            else:
                context.energy_trend = "stable"

    def _determine_best_time(
        self, am_checkins: List[CheckInData], context: ADHDContext
    ) -> None:
        """Determine best time of day based on ADHD states."""
        if not am_checkins:
            return

        adhd_states = [c.adhd_state for c in am_checkins[:3]]
        if "clear" in adhd_states:
            context.best_time_of_day = "morning (capitalize now)"
        elif "foggy" in adhd_states or "struggling" in adhd_states:
            context.best_time_of_day = "afternoon (give mornings time)"

    def _recommend_focus_length(
        self, am_checkins: List[CheckInData], context: ADHDContext
    ) -> None:
        """Recommend focus block length based on completion rate."""
        if not am_checkins:
            return

        completed_blocks = sum(len(c.focus_blocks_completed) for c in am_checkins[:3])
        planned_blocks = sum(len(c.focus_blocks_planned) for c in am_checkins[:3])

        if planned_blocks > 0:
            completion_rate = completed_blocks / planned_blocks
            if completion_rate < 0.5:
                context.recommended_focus_block_length = 15  # Shorter blocks
            elif completion_rate > 0.8:
                context.recommended_focus_block_length = 50  # Longer blocks
            else:
                context.recommended_focus_block_length = 25  # Standard pomodoro

    def _extract_working_strategies(
        self, checkins: List[CheckInData], context: ADHDContext
    ) -> None:
        """Track working strategies from notes."""
        strategy_keywords = {
            "body doubling": "body doubling",
            "timer": "visual timer",
            "walk": "movement breaks",
        }

        for checkin in checkins:
            if checkin.notes:
                notes_lower = checkin.notes.lower()
                for keyword, strategy in strategy_keywords.items():
                    if keyword in notes_lower:
                        context.working_strategies.append(strategy)

        context.working_strategies = list(set(context.working_strategies))

    def _get_progress_context(self) -> ProgressContext:
        """Get course and practice progress"""
        context = ProgressContext()

        # Try to parse progress tracker
        progress_file = self.goals_dir / "hb411_progress.md"
        if progress_file.exists():
            content = progress_file.read_text(encoding="utf-8")

            # Extract readings completed
            completed = len(re.findall(r"✅", content))
            context.readings_completed = completed

            # Count total readings (look for chapter tracking tables)
            total_markers = len(re.findall(r"[⬜✅🟨]", content))
            context.readings_total = (
                total_markers if total_markers > 0 else 50
            )  # Default estimate

            # Get readings behind from explicit tracker if available
            behind_match = re.search(r"readings_behind[:\s]*(\d+)", content)
            if behind_match:
                context.readings_behind = int(behind_match.group(1))
            else:
                # Calculate based on syllabus week
                syllabus = self.syllabus_parser.get_current_context(self.today)
                if syllabus and syllabus.current_week > 0:
                    # Estimate: ~3 readings per week
                    expected = min(syllabus.current_week * 3, context.readings_total)
                    context.readings_behind = max(
                        0, expected - context.readings_completed
                    )

        # Get next assignment info from syllabus
        syllabus = self.syllabus_parser.get_current_context(self.today)
        if syllabus and syllabus.next_deadline:
            context.days_until_next_assignment = syllabus.next_deadline["days_until"]
            context.next_assignment = syllabus.next_deadline["name"]

        # Get meditation streak from recent check-ins
        med_log = self.goals_dir / "meditation_log.md"
        if med_log.exists():
            content = med_log.read_text(encoding="utf-8")
            # Count recent completed sessions
            sessions = re.findall(r"✅", content)
            context.meditation_sessions_this_week = min(len(sessions), 7)

        # Also check today's check-in for meditation
        for checkin in (
            self.aggregator_checkins if hasattr(self, "aggregator_checkins") else []
        ):
            if checkin.meditation_completed:
                context.meditation_sessions_this_week += 1

        return context

    def _get_carryover(self, yesterday_pm: Optional[CheckInData]) -> List[str]:
        """Get carryover tasks from yesterday's PM check-in"""
        if yesterday_pm and yesterday_pm.carryover_tasks:
            return yesterday_pm.carryover_tasks
        return []

    def _aggregate_pending_tasks(self, context: AggregatedContext) -> List[str]:
        """Aggregate all pending tasks from various sources"""
        pending = []

        # Add carryover from yesterday
        pending.extend(context.carryover_from_yesterday)

        # Add today's priorities if set
        if context.today_am_checkin:
            pending.extend(context.today_am_checkin.priorities)

        # Add any uncompleted focus blocks from recent days
        for checkin in context.checkins:
            if checkin.period == "AM":
                uncompleted = set(checkin.focus_blocks_planned) - set(
                    checkin.focus_blocks_completed
                )
                pending.extend(uncompleted)

        # Add course assignments if due soon
        if context.syllabus and context.syllabus.next_deadline:
            if context.syllabus.next_deadline["days_until"] <= 7:
                pending.append(
                    f"Course: {context.syllabus.next_deadline['name']} (due in {context.syllabus.next_deadline['days_until']} days)"
                )

        # Deduplicate while preserving order
        seen = set()
        unique_pending = []
        for task in pending:
            if task and task not in seen:
                seen.add(task)
                unique_pending.append(task)

        return unique_pending


def gather_context_for_briefing() -> Dict[str, Any]:
    """
    Convenience function to gather full context for briefing generation.
    Returns a dictionary ready for template rendering.
    """
    aggregator = ContextAggregator()
    context = aggregator.gather_full_context()
    return context.to_dict()


if __name__ == "__main__":
    # Test the aggregator
    print("=" * 60)
    print("Context Aggregator Test")
    print("=" * 60)

    aggregator = ContextAggregator()
    context = aggregator.gather_full_context()

    print(f"\nDate: {context.date}")
    print(f"Day: {context.day_name}")

    print(f"\n📋 Check-ins found: {len(context.checkins)}")
    for ci in context.checkins:
        print(
            f"  - {ci.date} {ci.period}: Energy={ci.energy}, Priorities={len(ci.priorities)}"
        )

    print(f"\n📝 Previous briefings: {len(context.briefings)}")
    for b in context.briefings:
        print(f"  - {b.date}: {b.word_count} words")

    if context.syllabus:
        print(f"\n📚 Syllabus Context:")
        print(f"  Week {context.syllabus.current_week}: {context.syllabus.week_topic}")
        print(f"  Days until class: {context.syllabus.days_until_class}")
        print(f"  Readings due: {len(context.syllabus.readings_due)}")
        if context.syllabus.next_deadline:
            print(
                f"  Next deadline: {context.syllabus.next_deadline['name']} in {context.syllabus.next_deadline['days_until']} days"
            )

    if context.adhd:
        print(f"\n🧠 ADHD Context:")
        print(f"  3-day avg energy: {context.adhd.avg_energy_3day:.1f}")
        print(f"  Trend: {context.adhd.energy_trend}")
        print(
            f"  Recommended focus blocks: {context.adhd.recommended_focus_block_length} min"
        )

    print(f"\n📌 Pending Tasks: {len(context.pending_tasks)}")
    for task in context.pending_tasks[:5]:
        print(f"  - {task}")

    print("\n✅ Context aggregation complete")
