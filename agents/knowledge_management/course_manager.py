#!/usr/bin/env python3
"""
Course Manager - Semester Course Load Import & Knowledge Management

Orchestrates the complete workflow for importing college syllabi:
1. Parse syllabus documents (PDF, DOCX)
2. Extract course info, assignments, exams, deadlines
3. Create structured notes in Obsidian vault
4. Sync events to calendar (Google/Outlook)
5. Build knowledge base for each course
6. Detect and resolve scheduling conflicts

Part of OsMEN Knowledge Management system.
"""

import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import OsMEN components
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from parsers.syllabus.conflict_validator import ConflictValidator
from parsers.syllabus.syllabus_parser import SyllabusParser
from tools.obsidian.obsidian_integration import ObsidianIntegration

try:
    from integrations.calendar.calendar_manager import CalendarManager

    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False
    logger.warning("Calendar integration not available")


@dataclass
class Course:
    """Represents a college course"""

    id: str
    code: str
    name: str
    instructor: str
    semester: str
    year: int
    credits: Optional[int] = None
    schedule: Optional[Dict] = None
    syllabus_path: Optional[str] = None
    obsidian_folder: Optional[str] = None
    created_at: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CourseEvent:
    """Represents an event from a course (exam, assignment, etc.)"""

    id: str
    course_id: str
    title: str
    event_type: str  # exam, assignment, project, lecture, deadline
    date: str  # ISO format
    time: Optional[str] = None
    duration_minutes: Optional[int] = None
    description: Optional[str] = None
    priority: str = "medium"  # high, medium, low
    reminder_days: int = 1
    calendar_event_id: Optional[str] = None
    status: str = "scheduled"  # scheduled, completed, cancelled

    def to_dict(self) -> Dict:
        return asdict(self)


class CourseManager:
    """
    Manages course imports and knowledge base for academic semester planning.

    Workflow:
    1. User uploads syllabus (PDF/DOCX)
    2. Parser extracts structured data
    3. Course created in knowledge base
    4. Events synced to calendar
    5. Conflicts detected and resolved
    6. Notes structure created in Obsidian
    """

    def __init__(self, data_dir: str = None):
        """
        Initialize Course Manager.

        Args:
            data_dir: Directory for storing course data
        """
        self.data_dir = Path(
            data_dir
            or os.getenv(
                "OSMEN_DATA_DIR",
                Path(__file__).parent.parent.parent / "data" / "courses",
            )
        )
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.syllabus_parser = SyllabusParser()
        self.conflict_validator = ConflictValidator()

        try:
            self.obsidian = ObsidianIntegration()
            self._obsidian_available = True
        except Exception as e:
            logger.warning(f"Obsidian integration not available: {e}")
            self._obsidian_available = False
            self.obsidian = None

        if CALENDAR_AVAILABLE:
            try:
                self.calendar = CalendarManager()
                self._calendar_available = True
            except Exception as e:
                logger.warning(f"Calendar integration not available: {e}")
                self._calendar_available = False
                self.calendar = None
        else:
            self._calendar_available = False
            self.calendar = None

        # Load existing courses
        self.courses: Dict[str, Course] = {}
        self.events: Dict[str, CourseEvent] = {}
        self._load_data()

        logger.info(f"CourseManager initialized with {len(self.courses)} courses")

    def _load_data(self):
        """Load existing course data from disk"""
        courses_file = self.data_dir / "courses.json"
        events_file = self.data_dir / "events.json"

        if courses_file.exists():
            try:
                with open(courses_file) as f:
                    data = json.load(f)
                    for course_data in data.get("courses", []):
                        course = Course(**course_data)
                        self.courses[course.id] = course
            except Exception as e:
                logger.error(f"Error loading courses: {e}")

        if events_file.exists():
            try:
                with open(events_file) as f:
                    data = json.load(f)
                    for event_data in data.get("events", []):
                        event = CourseEvent(**event_data)
                        self.events[event.id] = event
            except Exception as e:
                logger.error(f"Error loading events: {e}")

    def _save_data(self):
        """Save course data to disk"""
        courses_file = self.data_dir / "courses.json"
        events_file = self.data_dir / "events.json"

        with open(courses_file, "w") as f:
            json.dump(
                {
                    "courses": [c.to_dict() for c in self.courses.values()],
                    "updated_at": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )

        with open(events_file, "w") as f:
            json.dump(
                {
                    "events": [e.to_dict() for e in self.events.values()],
                    "updated_at": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )

    def import_syllabus(
        self,
        file_path: str,
        semester: str = None,
        year: int = None,
        sync_calendar: bool = True,
        create_obsidian_notes: bool = True,
    ) -> Dict[str, Any]:
        """
        Import a syllabus file and create course structure.

        Args:
            file_path: Path to syllabus PDF or DOCX
            semester: Semester name (Fall, Spring, Summer) - auto-detected if not provided
            year: Academic year - auto-detected if not provided
            sync_calendar: Whether to sync events to calendar
            create_obsidian_notes: Whether to create Obsidian notes structure

        Returns:
            Dictionary with import results
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        logger.info(f"Importing syllabus: {file_path}")

        result = {
            "success": True,
            "file": str(file_path),
            "course": None,
            "events_created": 0,
            "calendar_events": 0,
            "obsidian_notes": [],
            "conflicts": [],
            "warnings": [],
        }

        try:
            # Step 1: Parse syllabus
            parsed_data = self.syllabus_parser.parse(str(file_path))
            normalized_data = self.syllabus_parser.normalize_data(parsed_data)

            # Extract course info
            course_info = normalized_data.get("course", {})

            # Auto-detect semester/year if not provided
            if not semester:
                semester = (
                    course_info.get("semester", {}).get("term")
                    or self._detect_semester()
                )
            if not year:
                year = (
                    course_info.get("semester", {}).get("year") or datetime.now().year
                )

            # Step 2: Create course
            course = self._create_course(
                code=course_info.get("code") or self._extract_course_code(file_path),
                name=course_info.get("name") or file_path.stem,
                instructor=course_info.get("instructor", {}).get("name", "TBA"),
                semester=semester,
                year=year,
                credits=course_info.get("credits"),
                syllabus_path=str(file_path),
            )
            result["course"] = course.to_dict()

            # Step 3: Create events from parsed data
            events = []
            for event_data in normalized_data.get("events", []):
                event = self._create_event(
                    course_id=course.id,
                    title=event_data.get("title", "Untitled"),
                    event_type=event_data.get("type", "event"),
                    date=event_data.get("date"),
                    description=event_data.get("description"),
                    priority=event_data.get("priority", "medium"),
                    reminder_days=event_data.get("reminder", {}).get("advance_days", 1),
                )
                if event:
                    events.append(event)

            result["events_created"] = len(events)

            # Step 4: Check for conflicts
            all_events = list(self.events.values())
            conflicts = self.conflict_validator.find_conflicts(
                [e.to_dict() for e in all_events]
            )
            if conflicts:
                result["conflicts"] = conflicts
                result["warnings"].append(
                    f"Found {len(conflicts)} scheduling conflicts"
                )

            # Step 5: Create Obsidian notes structure
            if create_obsidian_notes and self._obsidian_available:
                notes_created = self._create_course_notes(course, events)
                result["obsidian_notes"] = notes_created

            # Step 6: Sync to calendar
            if sync_calendar and self._calendar_available:
                calendar_count = self._sync_events_to_calendar(events)
                result["calendar_events"] = calendar_count

            # Save data
            self._save_data()

            logger.info(f"Successfully imported course: {course.code} - {course.name}")

        except Exception as e:
            logger.error(f"Error importing syllabus: {e}")
            result["success"] = False
            result["error"] = str(e)

        return result

    def _create_course(
        self,
        code: str,
        name: str,
        instructor: str,
        semester: str,
        year: int,
        credits: int = None,
        syllabus_path: str = None,
    ) -> Course:
        """Create a new course"""
        course_id = str(uuid.uuid4())[:8]

        # Generate Obsidian folder path
        obsidian_folder = f"Courses/{year}/{semester}/{code}"

        course = Course(
            id=course_id,
            code=code,
            name=name,
            instructor=instructor,
            semester=semester,
            year=year,
            credits=credits,
            syllabus_path=syllabus_path,
            obsidian_folder=obsidian_folder,
            created_at=datetime.now().isoformat(),
        )

        self.courses[course.id] = course
        logger.info(f"Created course: {course.code}")

        return course

    def _create_event(
        self,
        course_id: str,
        title: str,
        event_type: str,
        date: str,
        description: str = None,
        priority: str = "medium",
        reminder_days: int = 1,
    ) -> Optional[CourseEvent]:
        """Create a course event"""
        if not date:
            logger.warning(f"Skipping event without date: {title}")
            return None

        event_id = str(uuid.uuid4())[:8]

        event = CourseEvent(
            id=event_id,
            course_id=course_id,
            title=title,
            event_type=event_type,
            date=date,
            description=description,
            priority=priority,
            reminder_days=reminder_days,
        )

        self.events[event.id] = event
        return event

    def _create_course_notes(
        self,
        course: Course,
        events: List[CourseEvent],
    ) -> List[str]:
        """Create Obsidian notes structure for a course"""
        notes_created = []

        if not self.obsidian:
            return notes_created

        # Create main course note
        course_content = self._generate_course_note(course, events)
        try:
            result = self.obsidian.create_note(
                title=f"{course.code} - {course.name}",
                content=course_content,
                folder=course.obsidian_folder,
                tags=["course", course.semester.lower(), str(course.year)],
                frontmatter={
                    "course_code": course.code,
                    "instructor": course.instructor,
                    "semester": f"{course.semester} {course.year}",
                    "status": "active",
                    "created": datetime.now().isoformat(),
                },
            )
            notes_created.append(
                f"{course.obsidian_folder}/{course.code} - {course.name}"
            )
            logger.info(f"Created course note: {course.code}")
        except Exception as e:
            logger.error(f"Error creating course note: {e}")

        # Create syllabus summary note
        try:
            syllabus_content = self._generate_syllabus_note(course, events)
            self.obsidian.create_note(
                title="Syllabus",
                content=syllabus_content,
                folder=course.obsidian_folder,
                tags=["syllabus", course.code.lower().replace(" ", "-")],
            )
            notes_created.append(f"{course.obsidian_folder}/Syllabus")
        except Exception as e:
            logger.error(f"Error creating syllabus note: {e}")

        # Create assignments tracking note
        try:
            assignments = [
                e
                for e in events
                if e.event_type in ["assignment", "project", "homework"]
            ]
            if assignments:
                assignments_content = self._generate_assignments_note(
                    course, assignments
                )
                self.obsidian.create_note(
                    title="Assignments",
                    content=assignments_content,
                    folder=course.obsidian_folder,
                    tags=["assignments", course.code.lower().replace(" ", "-")],
                )
                notes_created.append(f"{course.obsidian_folder}/Assignments")
        except Exception as e:
            logger.error(f"Error creating assignments note: {e}")

        # Create exams tracking note
        try:
            exams = [
                e
                for e in events
                if e.event_type in ["exam", "test", "midterm", "final", "quiz"]
            ]
            if exams:
                exams_content = self._generate_exams_note(course, exams)
                self.obsidian.create_note(
                    title="Exams",
                    content=exams_content,
                    folder=course.obsidian_folder,
                    tags=["exams", course.code.lower().replace(" ", "-")],
                )
                notes_created.append(f"{course.obsidian_folder}/Exams")
        except Exception as e:
            logger.error(f"Error creating exams note: {e}")

        return notes_created

    def _generate_course_note(self, course: Course, events: List[CourseEvent]) -> str:
        """Generate main course note content"""
        exams = [
            e for e in events if e.event_type in ["exam", "test", "midterm", "final"]
        ]
        assignments = [
            e for e in events if e.event_type in ["assignment", "project", "homework"]
        ]

        content = f"""# {course.code}: {course.name}

## Course Information
| Field | Value |
|-------|-------|
| **Instructor** | {course.instructor} |
| **Semester** | {course.semester} {course.year} |
| **Credits** | {course.credits or 'N/A'} |

## Quick Links
- [[Syllabus]]
- [[Assignments]]
- [[Exams]]
- [[Notes]]

## Key Dates
### Exams ({len(exams)})
"""
        for exam in sorted(exams, key=lambda x: x.date or "9999"):
            content += f"- [ ] **{exam.title}** - {exam.date}\n"

        content += f"""
### Assignments ({len(assignments)})
"""
        for assignment in sorted(assignments, key=lambda x: x.date or "9999"):
            content += f"- [ ] **{assignment.title}** - Due: {assignment.date}\n"

        content += """
## Notes
> Add your lecture notes and study materials here

## Resources
- Course materials: 
- Textbook: 
- Online resources: 

---
*Generated by OsMEN Course Manager*
"""
        return content

    def _generate_syllabus_note(self, course: Course, events: List[CourseEvent]) -> str:
        """Generate syllabus summary note"""
        content = f"""# {course.code} Syllabus

## Course Overview
- **Course**: {course.code} - {course.name}
- **Instructor**: {course.instructor}
- **Semester**: {course.semester} {course.year}

## Schedule Overview

| Date | Event | Type | Priority |
|------|-------|------|----------|
"""
        for event in sorted(events, key=lambda x: x.date or "9999"):
            content += f"| {event.date} | {event.title} | {event.event_type} | {event.priority} |\n"

        content += """
## Grading Breakdown
> Add grading information here

## Policies
> Add course policies here

## Office Hours
> Add office hours here

---
*Extracted from syllabus by OsMEN*
"""
        return content

    def _generate_assignments_note(
        self, course: Course, assignments: List[CourseEvent]
    ) -> str:
        """Generate assignments tracking note"""
        content = f"""# {course.code} Assignments

## Overview
Total Assignments: {len(assignments)}

## Assignment Tracker

| Status | Assignment | Due Date | Priority |
|--------|-----------|----------|----------|
"""
        for a in sorted(assignments, key=lambda x: x.date or "9999"):
            status = "⬜" if a.status == "scheduled" else "✅"
            priority_icon = (
                "🔴"
                if a.priority == "high"
                else "🟡" if a.priority == "medium" else "🟢"
            )
            content += (
                f"| {status} | {a.title} | {a.date} | {priority_icon} {a.priority} |\n"
            )

        content += """
## Notes

---
*Tracked by OsMEN*
"""
        return content

    def _generate_exams_note(self, course: Course, exams: List[CourseEvent]) -> str:
        """Generate exams tracking note"""
        content = f"""# {course.code} Exams

## Overview
Total Exams: {len(exams)}

## Exam Schedule

| Status | Exam | Date | Priority |
|--------|------|------|----------|
"""
        for e in sorted(exams, key=lambda x: x.date or "9999"):
            status = "⬜" if e.status == "scheduled" else "✅"
            content += f"| {status} | {e.title} | {e.date} | {e.priority} |\n"

        content += """
## Study Plan

### Preparation Checklist
- [ ] Review lecture notes
- [ ] Complete practice problems
- [ ] Review past exams
- [ ] Create study guide

---
*Tracked by OsMEN*
"""
        return content

    def _sync_events_to_calendar(self, events: List[CourseEvent]) -> int:
        """Sync events to calendar"""
        if not self.calendar:
            return 0

        synced_count = 0
        for event in events:
            try:
                course = self.courses.get(event.course_id)
                course_code = course.code if course else "Course"

                calendar_event = self.calendar.create_event(
                    title=f"[{course_code}] {event.title}",
                    start_time=event.date,
                    end_time=event.date,  # All-day event
                    description=event.description
                    or f"{event.event_type.title()} for {course_code}",
                    all_day=True,
                    reminders=[
                        {"method": "popup", "minutes": event.reminder_days * 24 * 60}
                    ],
                )

                if calendar_event:
                    event.calendar_event_id = calendar_event.get("id")
                    synced_count += 1

            except Exception as e:
                logger.error(f"Error syncing event to calendar: {e}")

        return synced_count

    def _detect_semester(self) -> str:
        """Detect current semester based on date"""
        month = datetime.now().month
        if month >= 8 and month <= 12:
            return "Fall"
        elif month >= 1 and month <= 5:
            return "Spring"
        else:
            return "Summer"

    def _extract_course_code(self, file_path: Path) -> str:
        """Try to extract course code from filename"""
        name = file_path.stem
        # Common patterns: "CS101", "CS 101", "MATH-201", etc.
        import re

        match = re.search(r"([A-Z]{2,4})\s*[-_]?\s*(\d{3,4})", name, re.IGNORECASE)
        if match:
            return f"{match.group(1).upper()} {match.group(2)}"
        return name[:20]  # Fallback to filename

    def get_semester_overview(
        self,
        semester: str = None,
        year: int = None,
    ) -> Dict[str, Any]:
        """
        Get overview of all courses for a semester.

        Args:
            semester: Semester name (Fall, Spring, Summer)
            year: Academic year

        Returns:
            Dictionary with semester overview
        """
        semester = semester or self._detect_semester()
        year = year or datetime.now().year

        # Filter courses for semester
        semester_courses = [
            c
            for c in self.courses.values()
            if c.semester == semester and c.year == year
        ]

        # Get events for these courses
        course_ids = {c.id for c in semester_courses}
        semester_events = [e for e in self.events.values() if e.course_id in course_ids]

        # Categorize events
        exams = [
            e
            for e in semester_events
            if e.event_type in ["exam", "test", "midterm", "final"]
        ]
        assignments = [
            e
            for e in semester_events
            if e.event_type in ["assignment", "project", "homework"]
        ]

        # Find upcoming events (next 7 days)
        today = datetime.now().date()
        next_week = today + timedelta(days=7)
        upcoming = [
            e
            for e in semester_events
            if e.date and today <= datetime.fromisoformat(e.date).date() <= next_week
        ]

        return {
            "semester": semester,
            "year": year,
            "courses": [c.to_dict() for c in semester_courses],
            "total_courses": len(semester_courses),
            "total_events": len(semester_events),
            "exams": len(exams),
            "assignments": len(assignments),
            "upcoming_this_week": [
                e.to_dict() for e in sorted(upcoming, key=lambda x: x.date)
            ],
            "conflicts": self.conflict_validator.find_conflicts(
                [e.to_dict() for e in semester_events]
            ),
        }

    def get_course(self, course_id: str) -> Optional[Dict]:
        """Get course details by ID"""
        course = self.courses.get(course_id)
        if not course:
            return None

        course_events = [
            e.to_dict() for e in self.events.values() if e.course_id == course_id
        ]

        return {
            "course": course.to_dict(),
            "events": sorted(course_events, key=lambda x: x.get("date", "9999")),
        }

    def list_courses(self, semester: str = None, year: int = None) -> List[Dict]:
        """List all courses, optionally filtered by semester/year"""
        courses = list(self.courses.values())

        if semester:
            courses = [c for c in courses if c.semester == semester]
        if year:
            courses = [c for c in courses if c.year == year]

        return [c.to_dict() for c in courses]

    def bulk_import(
        self,
        syllabus_files: List[str],
        semester: str = None,
        year: int = None,
    ) -> Dict[str, Any]:
        """
        Import multiple syllabi at once (semester setup).

        Args:
            syllabus_files: List of paths to syllabus files
            semester: Semester name
            year: Academic year

        Returns:
            Dictionary with bulk import results
        """
        semester = semester or self._detect_semester()
        year = year or datetime.now().year

        results = {
            "semester": semester,
            "year": year,
            "total_files": len(syllabus_files),
            "successful": 0,
            "failed": 0,
            "courses": [],
            "errors": [],
        }

        for file_path in syllabus_files:
            result = self.import_syllabus(
                file_path=file_path,
                semester=semester,
                year=year,
            )

            if result.get("success"):
                results["successful"] += 1
                results["courses"].append(result.get("course"))
            else:
                results["failed"] += 1
                results["errors"].append(
                    {"file": file_path, "error": result.get("error")}
                )

        # Create semester overview note in Obsidian
        if self._obsidian_available and results["successful"] > 0:
            self._create_semester_overview(semester, year)

        return results

    def _create_semester_overview(self, semester: str, year: int):
        """Create a semester overview note in Obsidian"""
        if not self.obsidian:
            return

        overview = self.get_semester_overview(semester, year)

        content = f"""# {semester} {year} Overview

## Courses ({overview['total_courses']})

| Course | Instructor | Exams | Assignments |
|--------|-----------|-------|-------------|
"""
        for course in overview["courses"]:
            course_id = course["id"]
            course_events = [
                e for e in self.events.values() if e.course_id == course_id
            ]
            exams = len(
                [
                    e
                    for e in course_events
                    if e.event_type in ["exam", "test", "midterm", "final"]
                ]
            )
            assignments = len(
                [
                    e
                    for e in course_events
                    if e.event_type in ["assignment", "project", "homework"]
                ]
            )
            content += f"| [[{course['code']} - {course['name']}]] | {course['instructor']} | {exams} | {assignments} |\n"

        content += f"""
## Quick Stats
- 📚 **Courses**: {overview['total_courses']}
- 📅 **Total Events**: {overview['total_events']}
- 📝 **Exams**: {overview['exams']}
- ✏️ **Assignments**: {overview['assignments']}

## Upcoming This Week
"""
        for event in overview.get("upcoming_this_week", []):
            content += f"- [ ] **{event['date']}** - {event['title']}\n"

        if overview.get("conflicts"):
            content += f"""
## ⚠️ Conflicts ({len(overview['conflicts'])})
"""
            for conflict in overview["conflicts"][:5]:
                content += f"- {conflict.get('description', 'Scheduling conflict')}\n"

        content += """
---
*Generated by OsMEN Course Manager*
"""

        try:
            self.obsidian.create_note(
                title=f"{semester} {year} Overview",
                content=content,
                folder=f"Courses/{year}/{semester}",
                tags=["semester-overview", semester.lower(), str(year)],
                frontmatter={
                    "semester": semester,
                    "year": year,
                    "total_courses": overview["total_courses"],
                    "created": datetime.now().isoformat(),
                },
            )
            logger.info(f"Created semester overview for {semester} {year}")
        except Exception as e:
            logger.error(f"Error creating semester overview: {e}")


def main():
    """Test Course Manager"""
    print("=" * 60)
    print("Course Manager Test")
    print("=" * 60)

    manager = CourseManager()

    # Show current semester
    semester = manager._detect_semester()
    year = datetime.now().year
    print(f"\nCurrent Semester: {semester} {year}")

    # List existing courses
    courses = manager.list_courses()
    print(f"Existing Courses: {len(courses)}")
    for course in courses:
        print(f"  - {course['code']}: {course['name']}")

    # Show semester overview
    overview = manager.get_semester_overview()
    print(f"\nSemester Overview:")
    print(f"  Courses: {overview['total_courses']}")
    print(f"  Events: {overview['total_events']}")
    print(f"  Upcoming: {len(overview.get('upcoming_this_week', []))}")

    print("\n✅ Course Manager ready!")


if __name__ == "__main__":
    main()
    main()
