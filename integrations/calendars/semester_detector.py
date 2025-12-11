#!/usr/bin/env python3
"""
Semester Boundary Detection

Detects and manages academic semester boundaries.
Part of v1.4.0 - Syllabus Parser & Calendar Foundation.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json


class SemesterDetector:
    """Detect and manage semester boundaries"""
    
    # Common semester patterns in US universities
    SEMESTER_PATTERNS = {
        'fall': {'start_month': 8, 'end_month': 12, 'typical_weeks': 15},
        'spring': {'start_month': 1, 'end_month': 5, 'typical_weeks': 15},
        'summer': {'start_month': 6, 'end_month': 7, 'typical_weeks': 8},
        'winter': {'start_month': 12, 'end_month': 1, 'typical_weeks': 3},
    }
    
    def detect_semester(self, events: List[Dict]) -> Optional[Dict]:
        """
        Detect semester information from events
        
        Args:
            events: List of course events
        
        Returns:
            Semester info dict or None
        """
        if not events:
            return None
        
        # Find date range
        dates = []
        for event in events:
            date_str = event.get('date') or event.get('due_date')
            if date_str:
                try:
                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    dates.append(date)
                except (ValueError, TypeError):
                    continue
        
        if not dates:
            return None
        
        start_date = min(dates)
        end_date = max(dates)
        
        # Determine semester type
        semester_type = self._determine_semester_type(start_date)
        
        return {
            'type': semester_type,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'duration_weeks': (end_date - start_date).days // 7,
            'year': start_date.year
        }
    
    def _determine_semester_type(self, start_date: datetime) -> str:
        """Determine semester type from start date"""
        month = start_date.month
        
        if 8 <= month <= 12:
            return 'fall'
        elif 1 <= month <= 5:
            return 'spring'
        elif 6 <= month <= 7:
            return 'summer'
        else:
            return 'winter'
    
    def get_semester_weeks(self, semester_info: Dict) -> List[Tuple[datetime, datetime]]:
        """Get list of weeks in semester"""
        start = datetime.fromisoformat(semester_info['start_date'])
        end = datetime.fromisoformat(semester_info['end_date'])
        
        weeks = []
        current = start
        
        while current < end:
            week_end = min(current + timedelta(days=7), end)
            weeks.append((current, week_end))
            current = week_end
        
        return weeks


def main():
    print("Semester Detector - Ready")


if __name__ == "__main__":
    main()
