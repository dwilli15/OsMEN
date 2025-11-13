#!/usr/bin/env python3
"""
PDF Syllabus Parser

Extracts course information, schedules, and deadlines from PDF syllabi.
Part of v1.4.0 - Syllabus Parser & Calendar Foundation.
"""

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    print("Warning: PyPDF2 not installed. Install with: pip install PyPDF2")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("Warning: pdfplumber not installed. Install with: pip install pdfplumber")


class PDFSyllabusParser:
    """Parse PDF syllabi to extract course information and events"""
    
    def __init__(self):
        self.course_info = {}
        self.events = []
        self.assignments = []
        
        # Date patterns
        self.date_patterns = [
            r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b',  # MM/DD/YYYY or M/D/YY
            r'\b(\d{1,2})-(\d{1,2})-(\d{2,4})\b',  # MM-DD-YYYY
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})\b',  # Month DD, YYYY
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+(\d{1,2}),?\s+(\d{4})\b',  # Mon DD, YYYY
        ]
        
        # Event keywords
        self.exam_keywords = ['exam', 'test', 'midterm', 'final', 'quiz']
        self.assignment_keywords = ['assignment', 'homework', 'project', 'paper', 'essay', 'lab', 'due']
        self.event_keywords = ['class', 'lecture', 'session', 'meeting', 'deadline']
    
    def parse_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Parse PDF syllabus
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Dictionary with course info, events, and assignments
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        # Try pdfplumber first (better text extraction)
        if PDFPLUMBER_AVAILABLE:
            text = self._extract_text_pdfplumber(pdf_path)
        elif PYPDF2_AVAILABLE:
            text = self._extract_text_pypdf2(pdf_path)
        else:
            raise ImportError("No PDF library available. Install PyPDF2 or pdfplumber")
        
        # Parse extracted text
        return self._parse_text(text)
    
    def _extract_text_pdfplumber(self, pdf_path: Path) -> str:
        """Extract text using pdfplumber"""
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text
    
    def _extract_text_pypdf2(self, pdf_path: Path) -> str:
        """Extract text using PyPDF2"""
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def _parse_text(self, text: str) -> Dict[str, Any]:
        """Parse extracted text to find course info and events"""
        # Extract course information
        self.course_info = self._extract_course_info(text)
        
        # Extract dates and events
        dates = self._extract_dates(text)
        
        # Extract events and assignments
        self.events = self._extract_events(text, dates)
        self.assignments = self._extract_assignments(text, dates)
        
        return {
            "course_info": self.course_info,
            "events": self.events,
            "assignments": self.assignments,
            "raw_dates": dates
        }
    
    def _extract_course_info(self, text: str) -> Dict[str, Any]:
        """Extract basic course information"""
        info = {
            "course_code": None,
            "course_name": None,
            "instructor": None,
            "semester": None,
            "year": None
        }
        
        # Course code pattern (e.g., CS 101, MATH 201)
        course_code_match = re.search(r'\b([A-Z]{2,4})\s*(\d{3,4}[A-Z]?)\b', text)
        if course_code_match:
            info["course_code"] = f"{course_code_match.group(1)} {course_code_match.group(2)}"
        
        # Instructor pattern
        instructor_patterns = [
            r'Instructor:\s*([^\n]+)',
            r'Professor:\s*([^\n]+)',
            r'Dr\.\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
        ]
        for pattern in instructor_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info["instructor"] = match.group(1).strip()
                break
        
        # Semester pattern
        semester_match = re.search(r'(Fall|Spring|Summer|Winter)\s+(\d{4})', text, re.IGNORECASE)
        if semester_match:
            info["semester"] = semester_match.group(1).capitalize()
            info["year"] = int(semester_match.group(2))
        
        return info
    
    def _extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """Extract all dates from text"""
        dates = []
        
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group(0)
                date_obj = self._parse_date(match)
                if date_obj:
                    dates.append({
                        "text": date_str,
                        "date": date_obj,
                        "position": match.start()
                    })
        
        # Sort by position in text
        dates.sort(key=lambda x: x["position"])
        return dates
    
    def _parse_date(self, match) -> Optional[datetime]:
        """Parse regex match into datetime object"""
        try:
            groups = match.groups()
            
            if len(groups) >= 3:
                # Try different formats
                if groups[0].isdigit():  # Numeric month
                    month, day, year = int(groups[0]), int(groups[1]), int(groups[2])
                    if year < 100:  # Two-digit year
                        year += 2000
                    return datetime(year, month, day)
                else:  # Month name
                    month_name = groups[0]
                    day = int(groups[1])
                    year = int(groups[2])
                    
                    month_map = {
                        'jan': 1, 'january': 1,
                        'feb': 2, 'february': 2,
                        'mar': 3, 'march': 3,
                        'apr': 4, 'april': 4,
                        'may': 5,
                        'jun': 6, 'june': 6,
                        'jul': 7, 'july': 7,
                        'aug': 8, 'august': 8,
                        'sep': 9, 'september': 9,
                        'oct': 10, 'october': 10,
                        'nov': 11, 'november': 11,
                        'dec': 12, 'december': 12,
                    }
                    
                    month = month_map.get(month_name.lower())
                    if month:
                        return datetime(year, month, day)
        except (ValueError, AttributeError):
            pass
        
        return None
    
    def _extract_events(self, text: str, dates: List[Dict]) -> List[Dict[str, Any]]:
        """Extract exam and class events"""
        events = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Check for exam keywords
            for keyword in self.exam_keywords:
                if keyword in line_lower:
                    # Look for date nearby
                    date = self._find_nearest_date(line, dates, i, lines)
                    if date:
                        events.append({
                            "type": "exam",
                            "title": line.strip()[:100],  # Limit length
                            "date": date.isoformat(),
                            "description": line.strip()
                        })
                    break
        
        return events
    
    def _extract_assignments(self, text: str, dates: List[Dict]) -> List[Dict[str, Any]]:
        """Extract assignments and homework"""
        assignments = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Check for assignment keywords
            for keyword in self.assignment_keywords:
                if keyword in line_lower and 'due' in line_lower:
                    # Look for date nearby
                    date = self._find_nearest_date(line, dates, i, lines)
                    if date:
                        assignments.append({
                            "type": "assignment",
                            "title": line.strip()[:100],
                            "due_date": date.isoformat(),
                            "description": line.strip()
                        })
                    break
        
        return assignments
    
    def _find_nearest_date(self, line: str, dates: List[Dict], 
                          line_idx: int, all_lines: List[str]) -> Optional[datetime]:
        """Find the nearest date to a given line"""
        # First check if date is in the same line
        for date_info in dates:
            if date_info["text"] in line:
                return date_info["date"]
        
        # Check surrounding lines (within 2 lines)
        window_text = ' '.join(all_lines[max(0, line_idx-2):min(len(all_lines), line_idx+3)])
        
        for date_info in dates:
            if date_info["text"] in window_text:
                return date_info["date"]
        
        return None


def main():
    """Test PDF parser"""
    parser = PDFSyllabusParser()
    
    print("PDF Syllabus Parser")
    print("=" * 50)
    
    if not PYPDF2_AVAILABLE and not PDFPLUMBER_AVAILABLE:
        print("❌ No PDF libraries installed")
        print("   Install with: pip install PyPDF2 pdfplumber")
        return
    
    print("✅ PDF parsing libraries available")
    
    # Example: Create a test structure
    test_text = """
    CS 350 - Software Engineering
    Fall 2024
    Instructor: Dr. Jane Smith
    
    Schedule:
    September 15, 2024 - First Day of Class
    October 1, 2024 - Midterm Exam
    November 15, 2024 - Project Due
    December 10, 2024 - Final Exam
    
    Assignments:
    Homework 1 due September 22, 2024
    Homework 2 due October 6, 2024
    """
    
    result = parser._parse_text(test_text)
    
    print("\nParsed Information:")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
