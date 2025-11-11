#!/usr/bin/env python3
"""
Syllabus to Calendar Integration
Automatically parses syllabi and creates calendar events
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.syllabus_parser.syllabus_parser import SyllabusParser, SyllabusEvent
from tools.calendar_integration.calendar_integration import (
    CalendarEvent, GoogleCalendarIntegration, OutlookCalendarIntegration, 
    ConflictDetector
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyllabusToCalendarIntegration:
    """Integrates syllabus parsing with calendar creation"""
    
    def __init__(self, calendar_provider: str = "google"):
        self.parser = SyllabusParser()
        self.calendar_provider = calendar_provider
        
        if calendar_provider == "google":
            self.calendar = GoogleCalendarIntegration()
        elif calendar_provider == "outlook":
            self.calendar = OutlookCalendarIntegration()
        else:
            raise ValueError(f"Unknown calendar provider: {calendar_provider}")
    
    def process_syllabus(self, file_path: str, authenticate: bool = False) -> Dict[str, Any]:
        """Process syllabus and create calendar events"""
        logger.info(f"Processing syllabus: {file_path}")
        
        # Parse syllabus
        if file_path.endswith('.pdf'):
            syllabus_events = self.parser.parse_pdf(file_path)
        elif file_path.endswith('.docx'):
            syllabus_events = self.parser.parse_docx(file_path)
        else:
            raise ValueError("Unsupported file format. Use PDF or DOCX")
        
        logger.info(f"Extracted {len(syllabus_events)} events from syllabus")
        
        # Validate events
        validation_issues = self.parser.validate_events(syllabus_events)
        
        # Convert to calendar events
        calendar_events = self._convert_to_calendar_events(syllabus_events)
        
        # Check for conflicts
        conflicts = ConflictDetector.find_conflicts(calendar_events)
        
        # Create events in calendar (only if authenticated)
        created_event_ids = []
        if authenticate:
            try:
                self.calendar.authenticate()
                created_event_ids = self._create_calendar_events(calendar_events)
            except Exception as e:
                logger.error(f"Calendar creation failed: {e}")
        
        return {
            "syllabus_file": file_path,
            "events_extracted": len(syllabus_events),
            "validation_issues": validation_issues,
            "conflicts": conflicts,
            "events_created": len(created_event_ids),
            "created_event_ids": created_event_ids,
            "calendar_provider": self.calendar_provider
        }
    
    def _convert_to_calendar_events(self, syllabus_events: List[SyllabusEvent]) -> List[CalendarEvent]:
        """Convert syllabus events to calendar events"""
        calendar_events = []
        
        for syllabus_event in syllabus_events:
            if not syllabus_event.date:
                continue
            
            # Determine event duration based on type
            duration = self._get_event_duration(syllabus_event.event_type)
            end_time = syllabus_event.date + duration
            
            # Create title with course code
            title = f"[{syllabus_event.course}] {syllabus_event.title}"
            
            # Add weight to description if present
            description = syllabus_event.description
            if syllabus_event.weight > 0:
                description += f"\n\nGrade Weight: {syllabus_event.weight}%"
            
            calendar_event = CalendarEvent(
                title=title,
                start=syllabus_event.date,
                end=end_time,
                description=description,
                location=syllabus_event.location
            )
            
            calendar_events.append(calendar_event)
        
        return calendar_events
    
    def _get_event_duration(self, event_type: str) -> timedelta:
        """Get default duration for event type"""
        durations = {
            "exam": timedelta(hours=2),
            "assignment": timedelta(hours=1),  # Deadline time
            "project": timedelta(hours=1),
            "class": timedelta(hours=1, minutes=15),
            "deadline": timedelta(minutes=30)
        }
        return durations.get(event_type, timedelta(hours=1))
    
    def _create_calendar_events(self, events: List[CalendarEvent]) -> List[str]:
        """Create events in calendar"""
        return self.calendar.batch_create_events(events)
    
    def bulk_import_semester(self, syllabus_files: List[str], semester_name: str) -> Dict[str, Any]:
        """Import multiple syllabi for a semester"""
        logger.info(f"Bulk importing {len(syllabus_files)} syllabi for {semester_name}")
        
        all_results = []
        total_events = 0
        total_conflicts = []
        
        for file_path in syllabus_files:
            try:
                result = self.process_syllabus(file_path, authenticate=False)
                all_results.append(result)
                total_events += result["events_extracted"]
                total_conflicts.extend(result["conflicts"])
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                all_results.append({
                    "syllabus_file": file_path,
                    "error": str(e)
                })
        
        return {
            "semester": semester_name,
            "syllabi_processed": len(syllabus_files),
            "total_events": total_events,
            "total_conflicts": len(total_conflicts),
            "conflicts": total_conflicts,
            "results": all_results
        }


def test_integration():
    """Test syllabus to calendar integration"""
    print("\n" + "="*50)
    print("Testing Syllabus to Calendar Integration")
    print("="*50)
    
    integration = SyllabusToCalendarIntegration(calendar_provider="google")
    
    # Create a test syllabus file
    test_syllabus = """
    CS 301 - Advanced Programming
    
    Assignment 1: Due 01/20/2024 (15%)
    Midterm Exam: March 5, 2024 (30%)
    Final Project: May 10, 2024 (35%)
    """
    
    test_file = Path("/tmp/test_syllabus.txt")
    test_file.write_text(test_syllabus)
    
    try:
        # Note: Won't actually create events without authentication
        print("\nProcessing test syllabus (without calendar creation)...")
        
        # Manually test parsing
        parser = SyllabusParser()
        events = parser._extract_events(test_syllabus, "CS 301")
        
        print(f"✅ Extracted {len(events)} events")
        
        # Test conversion
        calendar_events = integration._convert_to_calendar_events(events)
        print(f"✅ Converted to {len(calendar_events)} calendar events")
        
        # Test conflict detection
        conflicts = ConflictDetector.find_conflicts(calendar_events)
        print(f"✅ Conflict detection: {len(conflicts)} conflicts found")
        
        return len(events) > 0
        
    finally:
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    success = test_integration()
    print(f"\n{'✅ Integration test passed' if success else '❌ Integration test failed'}")
