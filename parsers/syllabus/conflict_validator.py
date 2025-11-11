#!/usr/bin/env python3
"""
Event Conflict Validator

Detects and resolves conflicts between calendar events.
Part of v1.4.0 - Syllabus Parser & Calendar Foundation.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
import json


class ConflictValidator:
    """Validate and detect conflicts between events"""
    
    def __init__(self):
        self.conflicts = []
    
    def find_conflicts(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find all conflicts in a list of events
        
        Args:
            events: List of event dictionaries
        
        Returns:
            List of conflict dictionaries
        """
        self.conflicts = []
        
        # Sort events by date
        sorted_events = sorted(events, key=lambda x: self._get_event_datetime(x))
        
        # Check each pair of events
        for i, event1 in enumerate(sorted_events):
            for event2 in sorted_events[i+1:]:
                conflict = self._check_conflict(event1, event2)
                if conflict:
                    self.conflicts.append(conflict)
        
        return self.conflicts
    
    def _get_event_datetime(self, event: Dict[str, Any]) -> datetime:
        """Extract datetime from event"""
        date_str = event.get("date") or event.get("due_date") or "2099-12-31"
        
        try:
            if isinstance(date_str, str):
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            elif isinstance(date_str, datetime):
                return date_str
        except (ValueError, AttributeError):
            pass
        
        return datetime(2099, 12, 31)
    
    def _check_conflict(self, event1: Dict[str, Any], event2: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if two events conflict
        
        Args:
            event1: First event
            event2: Second event
        
        Returns:
            Conflict dictionary if conflict exists, None otherwise
        """
        dt1 = self._get_event_datetime(event1)
        dt2 = self._get_event_datetime(event2)
        
        # Get event durations (default to 1 hour for events, instant for assignments)
        duration1 = event1.get("duration_minutes", 60 if event1.get("type") == "exam" else 0)
        duration2 = event2.get("duration_minutes", 60 if event2.get("type") == "exam" else 0)
        
        end1 = dt1 + timedelta(minutes=duration1)
        end2 = dt2 + timedelta(minutes=duration2)
        
        # Check for overlap
        if dt1 < end2 and dt2 < end1:
            conflict_type = self._determine_conflict_type(event1, event2, dt1, dt2)
            
            return {
                "type": conflict_type,
                "severity": self._calculate_severity(event1, event2, conflict_type),
                "event1": {
                    "id": event1.get("id"),
                    "title": event1.get("title"),
                    "date": dt1.isoformat(),
                    "type": event1.get("type")
                },
                "event2": {
                    "id": event2.get("id"),
                    "title": event2.get("title"),
                    "date": dt2.isoformat(),
                    "type": event2.get("type")
                },
                "suggestions": self._generate_suggestions(event1, event2, conflict_type)
            }
        
        return None
    
    def _determine_conflict_type(self, event1: Dict, event2: Dict, 
                                 dt1: datetime, dt2: datetime) -> str:
        """Determine the type of conflict"""
        if dt1.date() == dt2.date():
            if abs((dt2 - dt1).total_seconds()) < 3600:  # Within 1 hour
                return "direct_overlap"
            else:
                return "same_day"
        elif abs((dt2 - dt1).days) <= 1:
            return "adjacent_days"
        else:
            return "close_proximity"
    
    def _calculate_severity(self, event1: Dict, event2: Dict, conflict_type: str) -> str:
        """Calculate conflict severity"""
        # Both high priority events = critical
        if (event1.get("priority") == "high" and event2.get("priority") == "high" 
            and conflict_type == "direct_overlap"):
            return "critical"
        
        # One high priority with overlap = high
        elif ((event1.get("priority") == "high" or event2.get("priority") == "high")
              and conflict_type in ["direct_overlap", "same_day"]):
            return "high"
        
        # Same day but different types = medium
        elif conflict_type == "same_day":
            return "medium"
        
        # Adjacent days or close = low
        else:
            return "low"
    
    def _generate_suggestions(self, event1: Dict, event2: Dict, conflict_type: str) -> List[str]:
        """Generate suggestions to resolve conflict"""
        suggestions = []
        
        if conflict_type == "direct_overlap":
            suggestions.append("One event must be rescheduled")
            suggestions.append("Verify actual event times to confirm conflict")
        
        elif conflict_type == "same_day":
            if event1.get("type") == "exam" or event2.get("type") == "exam":
                suggestions.append("Plan extra study time to prepare for both")
                suggestions.append("Request accommodation if conflicts are severe")
            else:
                suggestions.append("Schedule buffer time between events")
                suggestions.append("Prioritize based on deadlines")
        
        elif conflict_type == "adjacent_days":
            suggestions.append("Distribute workload across both days")
            suggestions.append("Start preparation early")
        
        return suggestions
    
    def validate_event(self, new_event: Dict[str, Any], 
                      existing_events: List[Dict[str, Any]]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate a new event against existing events
        
        Args:
            new_event: Event to validate
            existing_events: List of existing events
        
        Returns:
            (is_valid, list_of_conflicts)
        """
        conflicts = []
        
        for existing_event in existing_events:
            conflict = self._check_conflict(new_event, existing_event)
            if conflict and conflict["severity"] in ["critical", "high"]:
                conflicts.append(conflict)
        
        is_valid = len(conflicts) == 0
        
        return is_valid, conflicts


def main():
    """Test conflict validator"""
    validator = ConflictValidator()
    
    print("Event Conflict Validator")
    print("=" * 50)
    
    # Test events
    test_events = [
        {
            "id": "1",
            "title": "Midterm Exam - CS 101",
            "date": "2024-10-15T10:00:00",
            "type": "exam",
            "priority": "high",
            "duration_minutes": 120
        },
        {
            "id": "2",
            "title": "Midterm Exam - MATH 201",
            "date": "2024-10-15T10:00:00",
            "type": "exam",
            "priority": "high",
            "duration_minutes": 120
        },
        {
            "id": "3",
            "title": "Homework 1 Due",
            "date": "2024-10-15",
            "type": "assignment",
            "priority": "medium"
        },
        {
            "id": "4",
            "title": "Project Due",
            "date": "2024-10-16",
            "type": "assignment",
            "priority": "high"
        }
    ]
    
    conflicts = validator.find_conflicts(test_events)
    
    print(f"\nFound {len(conflicts)} conflict(s):")
    print(json.dumps(conflicts, indent=2))
    
    # Test validation
    new_event = {
        "title": "Study Session",
        "date": "2024-10-15T14:00:00",
        "type": "event",
        "priority": "medium",
        "duration_minutes": 60
    }
    
    is_valid, new_conflicts = validator.validate_event(new_event, test_events)
    print(f"\nNew event valid: {is_valid}")
    if new_conflicts:
        print("Conflicts:")
        print(json.dumps(new_conflicts, indent=2))


if __name__ == "__main__":
    main()
