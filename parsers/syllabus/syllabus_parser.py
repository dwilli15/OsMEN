#!/usr/bin/env python3
"""
Unified Syllabus Parser

Automatically detects file type and uses appropriate parser.
Part of v1.4.0 - Syllabus Parser & Calendar Foundation.
"""

from pathlib import Path
from typing import Dict, List, Any
import json

from pdf_parser import PDFSyllabusParser
from docx_parser import DOCXSyllabusParser


class SyllabusParser:
    """Unified interface for parsing syllabi in various formats"""
    
    def __init__(self):
        self.pdf_parser = PDFSyllabusParser()
        self.docx_parser = DOCXSyllabusParser()
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse syllabus file (auto-detects format)
        
        Args:
            file_path: Path to syllabus file
        
        Returns:
            Dictionary with parsed course information
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Detect file type by extension
        extension = file_path.suffix.lower()
        
        if extension == '.pdf':
            return self.pdf_parser.parse_pdf(str(file_path))
        elif extension in ['.docx', '.doc']:
            return self.docx_parser.parse_docx(str(file_path))
        else:
            raise ValueError(f"Unsupported file format: {extension}")
    
    def normalize_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize parsed data into standard format
        
        Args:
            parsed_data: Raw parsed data
        
        Returns:
            Normalized data structure
        """
        normalized = {
            "course": self._normalize_course_info(parsed_data.get("course_info", {})),
            "events": self._normalize_events(
                parsed_data.get("events", []) + parsed_data.get("assignments", [])
            ),
            "metadata": {
                "parsed_at": json.dumps(None),  # Will be set when actually parsing
                "source_file": None,
                "total_events": len(parsed_data.get("events", [])) + len(parsed_data.get("assignments", []))
            }
        }
        
        return normalized
    
    def _normalize_course_info(self, course_info: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize course information"""
        return {
            "id": None,  # To be generated
            "code": course_info.get("course_code"),
            "name": course_info.get("course_name"),
            "instructor": {
                "name": course_info.get("instructor"),
                "email": None,  # Not typically in syllabus
                "office_hours": None
            },
            "semester": {
                "term": course_info.get("semester"),
                "year": course_info.get("year"),
                "start_date": None,
                "end_date": None
            },
            "credits": None,
            "schedule": {
                "days": [],  # e.g., ["Monday", "Wednesday"]
                "time": None,  # e.g., "10:00-11:30"
                "location": None
            }
        }
    
    def _normalize_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize events and assignments"""
        normalized_events = []
        
        for event in events:
            normalized_event = {
                "id": None,  # To be generated
                "title": event.get("title", "Untitled Event"),
                "description": event.get("description", ""),
                "type": event.get("type", "event"),
                "date": event.get("date") or event.get("due_date"),
                "time": None,  # Not typically in syllabus text
                "duration_minutes": None,
                "location": None,
                "priority": self._calculate_priority(event),
                "reminder": {
                    "enabled": True,
                    "advance_days": self._calculate_reminder_days(event)
                },
                "status": "scheduled"
            }
            
            normalized_events.append(normalized_event)
        
        # Sort by date
        normalized_events.sort(key=lambda x: x["date"] if x["date"] else "9999-99-99")
        
        return normalized_events
    
    def _calculate_priority(self, event: Dict[str, Any]) -> str:
        """Calculate event priority based on type"""
        event_type = event.get("type", "").lower()
        title = event.get("title", "").lower()
        
        if "final" in title or "exam" in title:
            return "high"
        elif "midterm" in title or "test" in title:
            return "high"
        elif "project" in title:
            return "medium"
        elif "assignment" in title or "homework" in title:
            return "medium"
        else:
            return "low"
    
    def _calculate_reminder_days(self, event: Dict[str, Any]) -> int:
        """Calculate how many days in advance to remind"""
        priority = self._calculate_priority(event)
        
        if priority == "high":
            return 7  # 1 week for exams
        elif priority == "medium":
            return 3  # 3 days for assignments
        else:
            return 1  # 1 day for other events


def main():
    """Test unified parser"""
    parser = SyllabusParser()
    
    print("Unified Syllabus Parser")
    print("=" * 50)
    
    # Test with simulated data
    test_data = {
        "course_info": {
            "course_code": "CS 101",
            "course_name": "Introduction to Computer Science",
            "instructor": "Dr. Alice Brown",
            "semester": "Fall",
            "year": 2024
        },
        "events": [
            {
                "type": "exam",
                "title": "Midterm Exam",
                "date": "2024-10-15",
                "description": "Midterm covering chapters 1-5"
            }
        ],
        "assignments": [
            {
                "type": "assignment",
                "title": "Homework 1",
                "due_date": "2024-09-30",
                "description": "Complete exercises 1-10"
            }
        ]
    }
    
    normalized = parser.normalize_data(test_data)
    
    print("\nNormalized Data:")
    print(json.dumps(normalized, indent=2))


if __name__ == "__main__":
    main()
