#!/usr/bin/env python3
"""
ICS Calendar Generator for Course Schedules
Generates separate .ics files for:
- Class sessions
- Reading assignments
- Major assignments
- Special events
"""

import hashlib
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


def generate_uid(content: str) -> str:
    """Generate unique UID for calendar event."""
    return hashlib.md5(content.encode()).hexdigest()[:16] + "@osmen.local"


def format_datetime(dt: datetime) -> str:
    """Format datetime for ICS (local time)."""
    return dt.strftime("%Y%m%dT%H%M%S")


def format_date(dt: datetime) -> str:
    """Format date only for ICS."""
    return dt.strftime("%Y%m%d")


def escape_text(text: str) -> str:
    """Escape special characters for ICS format."""
    text = text.replace("\\", "\\\\")
    text = text.replace(",", "\\,")
    text = text.replace(";", "\\;")
    text = text.replace("\n", "\\n")
    return text


def create_ics_event(
    summary: str,
    start: datetime,
    end: Optional[datetime] = None,
    description: str = "",
    location: str = "",
    all_day: bool = False,
    alarm_minutes: Optional[int] = None,
) -> str:
    """Create a single ICS event."""
    uid = generate_uid(f"{summary}{start}")
    now = datetime.now()

    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{format_datetime(now)}",
        f"SUMMARY:{escape_text(summary)}",
    ]

    if all_day:
        lines.append(f"DTSTART;VALUE=DATE:{format_date(start)}")
        if end:
            lines.append(f"DTEND;VALUE=DATE:{format_date(end + timedelta(days=1))}")
    else:
        lines.append(f"DTSTART:{format_datetime(start)}")
        if end:
            lines.append(f"DTEND:{format_datetime(end)}")

    if description:
        lines.append(f"DESCRIPTION:{escape_text(description)}")

    if location:
        lines.append(f"LOCATION:{escape_text(location)}")

    if alarm_minutes:
        lines.extend(
            [
                "BEGIN:VALARM",
                "ACTION:DISPLAY",
                f"DESCRIPTION:Reminder: {escape_text(summary)}",
                f"TRIGGER:-PT{alarm_minutes}M",
                "END:VALARM",
            ]
        )

    lines.append("END:VEVENT")
    return "\n".join(lines)


def create_ics_file(events: list, calendar_name: str) -> str:
    """Create complete ICS file content."""
    header = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//OsMEN//Course Calendar//EN",
        f"X-WR-CALNAME:{calendar_name}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    footer = ["END:VCALENDAR"]

    return "\n".join(header + events + footer)


def parse_time(time_str: str) -> tuple[int, int]:
    """Parse time string like '10:00 AM' or '11:59 PM'."""
    match = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)", time_str, re.IGNORECASE)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        am_pm = match.group(3).upper()

        if am_pm == "PM" and hour != 12:
            hour += 12
        elif am_pm == "AM" and hour == 12:
            hour = 0

        return hour, minute
    return 10, 0  # Default


def generate_class_sessions(course_data: dict, output_dir: Path) -> None:
    """Generate ICS for class sessions."""
    events = []
    schedule = course_data["schedule"]
    zoom_link = course_data["course"]["schedule"]["zoom_link"]

    for week in schedule:
        if week["class_type"] in ["break", "none"]:
            continue

        date_str = week["date"]
        date = datetime.strptime(date_str, "%Y-%m-%d")
        topic = week["topic"]

        # Handle intensive vs regular class
        if week["class_type"] == "intensive":
            # 9:30 AM - 4:30 PM
            start = date.replace(hour=9, minute=30)
            end = date.replace(hour=16, minute=30)
            summary = f"HB411 INTENSIVE: {topic}"
        elif week["class_type"] == "asynchronous":
            # All-day marker
            start = date
            end = date
            summary = f"HB411 (Async): {topic}"
            event = create_ics_event(
                summary=summary,
                start=start,
                end=end,
                description=f"Week {week['week']}: {topic}\n\nAsync work week - no live session.\n\nNote: {week.get('note', '')}",
                all_day=True,
            )
            events.append(event)
            continue
        else:
            # Regular 10 AM - 12 PM CT
            start = date.replace(hour=10, minute=0)
            end = date.replace(hour=12, minute=0)
            summary = f"HB411: {topic}"

        description_parts = [f"Week {week['week']}: {topic}"]

        if week.get("readings"):
            description_parts.append("\nReadings Due:")
            for r in week["readings"]:
                description_parts.append(f"  • {r}")

        if week.get("assignments_due"):
            description_parts.append("\nAssignments Due:")
            for a in week["assignments_due"]:
                description_parts.append(f"  • {a}")

        if week.get("note"):
            description_parts.append(f"\nNote: {week['note']}")

        description_parts.append(f"\nZoom: {zoom_link}")

        event = create_ics_event(
            summary=summary,
            start=start,
            end=end,
            description="\n".join(description_parts),
            location=zoom_link,
            alarm_minutes=30,
        )
        events.append(event)

    ics_content = create_ics_file(events, "HB411 Class Sessions")
    output_path = output_dir / "HB411_class_sessions.ics"
    output_path.write_text(ics_content, encoding="utf-8")
    print(f"✅ Created: {output_path.name} ({len(events)} events)")


def generate_reading_calendar(course_data: dict, output_dir: Path) -> None:
    """Generate ICS for weekly readings."""
    events = []
    schedule = course_data["schedule"]

    for week in schedule:
        if not week.get("readings"):
            continue

        date_str = week["date"]
        class_date = datetime.strptime(date_str, "%Y-%m-%d")
        topic = week["topic"]

        # Reading reminder: 3 days before class (Monday for Thursday class)
        reminder_date = class_date - timedelta(days=3)
        reminder_date = reminder_date.replace(hour=8, minute=0)

        readings_list = "\n".join([f"• {r}" for r in week["readings"]])

        supplementary = ""
        if week.get("supplementary"):
            supplementary = "\n\nSupplementary:\n" + "\n".join(
                [f"• {s}" for s in week["supplementary"]]
            )

        watch = ""
        if week.get("watch"):
            watch = "\n\nWatch/Listen:\n" + "\n".join([f"• {w}" for w in week["watch"]])

        event = create_ics_event(
            summary=f"📚 HB411 Readings Due: Week {week['week']}",
            start=reminder_date,
            end=reminder_date + timedelta(hours=1),
            description=f"Readings for Week {week['week']}: {topic}\n\nComplete before Thursday class:\n\n{readings_list}{supplementary}{watch}",
            alarm_minutes=1440,  # 24 hours
        )
        events.append(event)

        # Also add a morning-of reminder
        class_morning = class_date.replace(hour=6, minute=0)
        event_morning = create_ics_event(
            summary=f"📖 HB411 Today: {topic}",
            start=class_morning,
            end=class_morning + timedelta(minutes=30),
            description=f"Today's topic: {topic}\n\nEnsure readings complete:\n{readings_list}",
            alarm_minutes=0,
        )
        events.append(event_morning)

    ics_content = create_ics_file(events, "HB411 Weekly Readings")
    output_path = output_dir / "HB411_readings.ics"
    output_path.write_text(ics_content, encoding="utf-8")
    print(f"✅ Created: {output_path.name} ({len(events)} events)")


def generate_assignments_calendar(course_data: dict, output_dir: Path) -> None:
    """Generate ICS for major assignments."""
    events = []
    assignments = course_data["assignments"]

    assignment_details = {
        "Journal": {
            "description": "5 journal entries (250-300 words each).\n\nRequired:\n• Aug 21: Boundary Image prompt\n\nPlus 4 of your choice from prompts in course.",
            "color": "blue",
        },
        "Guiding Document Paper": {
            "description": "1250-1500 words analyzing how a community document addresses boundaries.\n\nAnalyze policies, handbooks, or codes of ethics from ministry contexts.",
            "color": "green",
        },
        "Reading Responses": {
            "description": "Complete 5 of 9 options (250-350 words each).\n\nDue by 6 AM Thursday of assigned week.",
            "color": "yellow",
        },
        "Navigating Boundaries Presentation": {
            "description": "Small group presentation on assigned book.\n\nAlso complete a Reading Response for your presentation day.",
            "color": "purple",
        },
        "Project Synopsis": {
            "description": "Brief synopsis of your final project plan.\n\nPass/Fail grading - ensures you're on track.",
            "color": "orange",
        },
        "Final Project Presentation": {
            "description": "3 slides maximum, 12 minutes max.\n\nUpload to Populi by 11:59 PM on your presentation day.",
            "color": "red",
        },
        "Final Integrative Project/Paper": {
            "description": "2500-3000 words.\n\nOption A: Research paper on boundaries topic.\nOption B: Reflective project with creative element.\n\nUse at least 5 course sources plus additional research.",
            "color": "red",
        },
    }

    for assignment in assignments:
        name = assignment["name"]
        weight = assignment["weight"]
        details = assignment_details.get(name, {})

        # Handle assignments with specific due dates
        if assignment.get("due_date"):
            due_date = datetime.strptime(assignment["due_date"], "%Y-%m-%d")
            due_time = assignment.get("due_time", "11:59 PM")
            hour, minute = parse_time(due_time)
            due_datetime = due_date.replace(hour=hour, minute=minute)

            description = f"Weight: {weight}\n\n{details.get('description', assignment.get('description', ''))}"

            # Due date event
            event = create_ics_event(
                summary=f"🎯 HB411 DUE: {name} ({weight})",
                start=due_datetime,
                end=due_datetime + timedelta(minutes=30),
                description=description,
                alarm_minutes=1440,  # 24 hours before
            )
            events.append(event)

            # Work reminder 1 week before
            reminder_date = due_datetime - timedelta(days=7)
            event_reminder = create_ics_event(
                summary=f"⚡ HB411 Due in 1 Week: {name}",
                start=reminder_date,
                end=reminder_date + timedelta(hours=1),
                description=f"{name} due in one week!\n\nWeight: {weight}\n\n{details.get('description', '')}",
                alarm_minutes=60,
            )
            events.append(event_reminder)

        # Handle presentations with multiple dates
        if assignment.get("presentation_dates"):
            for pres_date in assignment["presentation_dates"]:
                date = datetime.strptime(pres_date, "%Y-%m-%d")
                event = create_ics_event(
                    summary=f"🎤 HB411 Presentation Day: {name}",
                    start=date.replace(hour=10, minute=0),
                    end=date.replace(hour=12, minute=0),
                    description=f"Presentation opportunity\n\nWeight: {weight}\n\n{details.get('description', assignment.get('description', ''))}",
                    alarm_minutes=1440,
                )
                events.append(event)

    ics_content = create_ics_file(events, "HB411 Assignments")
    output_path = output_dir / "HB411_assignments.ics"
    output_path.write_text(ics_content, encoding="utf-8")
    print(f"✅ Created: {output_path.name} ({len(events)} events)")


def generate_special_events_calendar(course_data: dict, output_dir: Path) -> None:
    """Generate ICS for special events (intensive, breaks, etc.)."""
    events = []

    # Intensive Day
    intensive = create_ics_event(
        summary="🔥 HB411 INTENSIVE DAY",
        start=datetime(2025, 8, 28, 9, 30),
        end=datetime(2025, 8, 28, 16, 30),
        description="Full-day intensive session!\n\n9:30 AM - 4:30 PM CT\n\nTopics:\n• Grounding Values\n• Ethical Commitments\n• Flourishing\n\nHeavy reading load - complete all readings beforehand.",
        location=course_data["course"]["schedule"]["zoom_link"],
        alarm_minutes=1440,
    )
    events.append(intensive)

    # Intensive prep reminder
    prep = create_ics_event(
        summary="⚠️ Prepare for HB411 Intensive",
        start=datetime(2025, 8, 27, 18, 0),
        end=datetime(2025, 8, 27, 19, 0),
        description="Tomorrow is the full-day intensive!\n\nChecklist:\n✓ Complete all readings\n✓ Watch required videos\n✓ Prepare snacks/lunch\n✓ Clear schedule 9:30 AM - 4:30 PM",
        alarm_minutes=120,
    )
    events.append(prep)

    # Fall Break
    fall_break = create_ics_event(
        summary="🍂 HB411 Fall Break - No Class",
        start=datetime(2025, 10, 16),
        all_day=True,
        description="Fall Break - Enjoy the rest!\n\nNext class: Oct 23 - Navigating Boundaries I: Technology",
    )
    events.append(fall_break)

    # Async week
    async_week = create_ics_event(
        summary="📝 HB411 Async Work Week",
        start=datetime(2025, 10, 9),
        all_day=True,
        description="No live class this week.\n\nUse time for:\n• Group presentation planning\n• Final project preparation\n• Catching up on readings",
    )
    events.append(async_week)

    # First day
    first_day = create_ics_event(
        summary="🎉 HB411 First Day of Class!",
        start=datetime(2025, 8, 14, 10, 0),
        end=datetime(2025, 8, 14, 12, 0),
        description="Welcome to Healthy Boundaries for Leaders!\n\nIntroductions and course overview.\n\nMake sure you have:\n✓ Reviewed syllabus\n✓ Checked Populi\n✓ Zoom working",
        location=course_data["course"]["schedule"]["zoom_link"],
        alarm_minutes=60,
    )
    events.append(first_day)

    # Last day of class
    last_class = create_ics_event(
        summary="🎓 HB411 Final Class Session",
        start=datetime(2025, 11, 20, 10, 0),
        end=datetime(2025, 11, 20, 12, 0),
        description="Final day of live sessions!\n\nPresentations Part II\nJournal Due by 11:59 PM\n\nFinal Paper due Nov 24.",
        location=course_data["course"]["schedule"]["zoom_link"],
        alarm_minutes=60,
    )
    events.append(last_class)

    # Final paper deadline
    final_deadline = create_ics_event(
        summary="🏁 HB411 FINAL PAPER DEADLINE",
        start=datetime(2025, 11, 24, 23, 59),
        end=datetime(2025, 11, 25, 0, 0),
        description="Final Integrative Project/Paper due!\n\n2500-3000 words\n25% of grade\n\nSubmit to Populi by 11:59 PM",
        alarm_minutes=720,  # 12 hours
    )
    events.append(final_deadline)

    # Office hours reminder (recurring concept - just add first one as example)
    office_hours = create_ics_event(
        summary="📞 Dr. House Office Hours Available",
        start=datetime(2025, 8, 18, 13, 0),
        end=datetime(2025, 8, 18, 15, 0),
        description="Dr. Kathryn House's office hours\n\nMondays, 1-3 PM CT\n\nEmail: khouse@meadville.edu\n\nGreat for questions about:\n• Paper topics\n• Course content\n• Final project planning",
    )
    events.append(office_hours)

    ics_content = create_ics_file(events, "HB411 Special Events")
    output_path = output_dir / "HB411_special_events.ics"
    output_path.write_text(ics_content, encoding="utf-8")
    print(f"✅ Created: {output_path.name} ({len(events)} events)")


def generate_master_calendar(course_data: dict, output_dir: Path) -> None:
    """Generate combined master calendar."""
    # Just read all the individual files and combine
    all_events = []

    for ics_file in output_dir.glob("HB411_*.ics"):
        if "master" in ics_file.name:
            continue
        content = ics_file.read_text(encoding="utf-8")
        # Extract events
        in_event = False
        event_lines = []
        for line in content.split("\n"):
            if line.startswith("BEGIN:VEVENT"):
                in_event = True
                event_lines = [line]
            elif line.startswith("END:VEVENT"):
                event_lines.append(line)
                all_events.append("\n".join(event_lines))
                in_event = False
            elif in_event:
                event_lines.append(line)

    ics_content = create_ics_file(all_events, "HB411 Master Calendar")
    output_path = output_dir / "HB411_master_calendar.ics"
    output_path.write_text(ics_content, encoding="utf-8")
    print(f"✅ Created: {output_path.name} ({len(all_events)} total events)")


def main():
    """Main entry point."""
    # Paths
    course_dir = Path(r"D:\OsMEN\content\courses\HB411_HealthyBoundaries")
    course_data_path = course_dir / "course_data.json"
    calendar_dir = course_dir / "calendar"

    # Ensure calendar directory exists
    calendar_dir.mkdir(parents=True, exist_ok=True)

    # Load course data
    with open(course_data_path, "r", encoding="utf-8") as f:
        course_data = json.load(f)

    print("\n" + "=" * 60)
    print("📅 HB411 Calendar Generator")
    print("=" * 60)
    print(f"\nCourse: {course_data['course']['name']}")
    print(f"Semester: {course_data['course']['semester']}")
    print(f"Output: {calendar_dir}\n")

    # Generate all calendars
    generate_class_sessions(course_data, calendar_dir)
    generate_reading_calendar(course_data, calendar_dir)
    generate_assignments_calendar(course_data, calendar_dir)
    generate_special_events_calendar(course_data, calendar_dir)
    generate_master_calendar(course_data, calendar_dir)

    print("\n" + "=" * 60)
    print("✅ All calendars generated successfully!")
    print("=" * 60)
    print(f"\nFiles created in: {calendar_dir}")
    for f in sorted(calendar_dir.glob("*.ics")):
        print(f"  • {f.name}")


if __name__ == "__main__":
    main()
