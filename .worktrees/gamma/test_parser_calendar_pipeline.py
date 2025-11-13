#!/usr/bin/env python3
"""
Gamma G1.3 coverage – parser -> calendar -> scheduling pipeline validation.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

import pytest

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).parent))

from integrations.calendar.multi_calendar_sync import MultiCalendarSync  # noqa: E402
from parsers.syllabus.syllabus_parser import SyllabusParser  # noqa: E402
from scheduling.priority_ranker import PriorityRanker  # noqa: E402


class RecordingCalendar:
    """Minimal calendar stub capturing created events."""

    def __init__(self, name: str):
        self.name = name
        self.created_events: List[Dict[str, Any]] = []

    def create_event(self, event: Dict[str, Any]):
        self.created_events.append(event)
        return {"id": f"{self.name}-{len(self.created_events)}"}

    def update_event(self, event_id: str, data: Dict[str, Any]):
        return True

    def delete_event(self, event_id: str):
        return True


def _detect_conflicts(events: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """Detect simple conflicts by matching identical dates."""
    conflicts = {}
    for event in events:
        key = event.get("date")
        if not key:
            continue
        conflicts.setdefault(key, []).append(event)
    return [group for group in conflicts.values() if len(group) > 1]


def test_parser_calendar_pipeline_ranks_and_syncs_events():
    """End-to-end harness: parser normalization -> ranking -> multi-calendar sync."""
    parser = SyllabusParser()
    parsed_payload = {
        "course_info": {
            "course_code": "BIO 210",
            "course_name": "Cell Biology",
            "semester": "Fall",
            "year": 2025,
        },
        "events": [
            {"type": "lecture", "title": "Lecture 1", "date": "2025-09-01"},
            {"type": "lecture", "title": "Lecture 2", "date": "2025-09-03"},
            {"type": "exam", "title": "Midterm Exam", "date": "2025-10-10"},
        ],
        "assignments": [
            {"type": "assignment", "title": "Lab Report 1", "due_date": "2025-09-05"},
            {"type": "assignment", "title": "Lab Report 2", "due_date": "2025-09-12"},
            # Intentional conflict (same date as lecture 2)
            {"type": "quiz", "title": "Quiz 1", "due_date": "2025-09-03"},
        ],
    }

    normalized = parser.normalize_data(parsed_payload)
    events = normalized["events"]
    for idx, event in enumerate(events):
        event["id"] = f"evt-{idx}"
        event["estimated_hours"] = 4 if event["type"] == "assignment" else 2
        event["blocks_count"] = 1 if "Lab" in event["title"] else 0

    ranker = PriorityRanker()
    ranked_events = ranker.rank_tasks(events)

    conflicts = _detect_conflicts(ranked_events)
    assert conflicts, "Expected at least one conflicting date"

    sync = MultiCalendarSync()
    google = RecordingCalendar("google")
    outlook = RecordingCalendar("outlook")
    sync.add_calendar("google", google)
    sync.add_calendar("outlook", outlook)

    results = sync.sync_all_events(ranked_events, ["google", "outlook"])

    assert len(results) == len(ranked_events)
    assert len(google.created_events) == len(ranked_events)
    assert len(outlook.created_events) == len(ranked_events)

    status = sync.get_sync_status()
    assert status["total_synced_events"] == len(ranked_events)
    assert set(status["calendars_configured"]) == {"google", "outlook"}

    # Verify sync map captured both calendars for the highest priority event.
    top_event_id = ranked_events[0]["id"]
    assert set(status["sync_map"][top_event_id].keys()) == {"google", "outlook"}
