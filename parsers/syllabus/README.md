# Syllabus Parsers

Automated extraction of course information, schedules, and deadlines from syllabus documents.

## Overview

Part of v1.4.0 - Syllabus Parser & Calendar Foundation.

This module provides intelligent parsing of syllabus documents in multiple formats (PDF, DOCX), extracting structured data including:
- Course information (code, name, instructor, semester)
- Important dates (exams, assignments, deadlines)
- Event schedules
- Conflict detection

## Features

### Document Parsing
- **PDF Support** (`pdf_parser.py`): Uses PyPDF2 or pdfplumber for text extraction
- **DOCX Support** (`docx_parser.py`): Parses Word documents including tables
- **Unified Interface** (`syllabus_parser.py`): Auto-detects format and uses appropriate parser

### Data Processing
- **Event Extraction**: Automatically identifies exams, assignments, and deadlines
- **Date Recognition**: Multiple date format support (MM/DD/YYYY, Month DD YYYY, etc.)
- **Data Normalization**: Converts raw data into standardized structure
- **Conflict Detection** (`conflict_validator.py`): Identifies scheduling conflicts

## Installation

```bash
# Install required dependencies
pip install -r requirements.txt

# Or install parser dependencies directly
pip install PyPDF2 pdfplumber python-docx
```

## Usage

### Basic Parsing

```python
from parsers.syllabus import SyllabusParser

# Create parser instance
parser = SyllabusParser()

# Parse a PDF syllabus
result = parser.parse("path/to/syllabus.pdf")

# Parse a DOCX syllabus
result = parser.parse("path/to/syllabus.docx")

# Normalize the data
normalized = parser.normalize_data(result)
```

### Conflict Detection

```python
from parsers.syllabus.conflict_validator import ConflictValidator

validator = ConflictValidator()

# Check for conflicts
conflicts = validator.find_conflicts(events)

# Validate a new event
is_valid, conflicts = validator.validate_event(new_event, existing_events)
```

## Data Structure

### Parsed Output

```json
{
  "course_info": {
    "course_code": "CS 101",
    "course_name": "Introduction to Computer Science",
    "instructor": "Dr. Jane Smith",
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
```

### Normalized Output

```json
{
  "course": {
    "code": "CS 101",
    "instructor": {
      "name": "Dr. Jane Smith"
    },
    "semester": {
      "term": "Fall",
      "year": 2024
    }
  },
  "events": [
    {
      "title": "Midterm Exam",
      "date": "2024-10-15",
      "type": "exam",
      "priority": "high",
      "reminder": {
        "enabled": true,
        "advance_days": 7
      }
    }
  ]
}
```

## Modules

### pdf_parser.py
Extracts text from PDF files and identifies course information and events.

**Features:**
- Multiple PDF libraries support (PyPDF2, pdfplumber)
- Regex-based date extraction
- Event keyword matching
- Course code and instructor detection

### docx_parser.py
Parses Word documents including text and tables.

**Features:**
- python-docx integration
- Table parsing (for schedule tables)
- Same extraction logic as PDF parser
- Paragraph and table text extraction

### syllabus_parser.py
Unified interface that auto-detects file format.

**Features:**
- Automatic format detection (.pdf, .docx)
- Data normalization
- Priority calculation
- Reminder scheduling

### conflict_validator.py
Detects and resolves scheduling conflicts.

**Features:**
- Multi-event conflict detection
- Severity classification (critical/high/medium/low)
- Conflict type identification
- Resolution suggestions

## Event Detection

### Keywords Recognized

**Exams:** exam, test, midterm, final, quiz
**Assignments:** assignment, homework, project, paper, essay, lab, due
**Events:** class, lecture, session, meeting, deadline

### Date Formats Supported

- `MM/DD/YYYY` (e.g., 10/15/2024)
- `MM-DD-YYYY` (e.g., 10-15-2024)
- `Month DD, YYYY` (e.g., October 15, 2024)
- `Mon DD, YYYY` (e.g., Oct 15, 2024)

## Priority Calculation

Events are automatically assigned priorities:

- **High:** Exams, finals, midterms
- **Medium:** Projects, assignments, homework
- **Low:** Other events

## Conflict Detection

Conflicts are categorized by:

1. **Direct Overlap:** Events at exact same time → Critical/High
2. **Same Day:** Multiple events same day → Medium
3. **Adjacent Days:** Events on consecutive days → Low
4. **Close Proximity:** Events within a few days → Low

## Testing

```bash
# Test PDF parser
cd parsers/syllabus
python3 pdf_parser.py

# Test DOCX parser
python3 docx_parser.py

# Test unified parser
python3 syllabus_parser.py

# Test conflict validator
python3 conflict_validator.py
```

## Future Enhancements

- [ ] OCR support for scanned PDFs
- [ ] Natural language processing for better extraction
- [ ] Machine learning for improved accuracy
- [ ] Support for additional formats (TXT, HTML)
- [ ] Time extraction from text
- [ ] Location detection
- [ ] Recurring event support

## Dependencies

- PyPDF2 >= 3.0.0
- pdfplumber >= 0.10.0
- python-docx >= 1.0.0
- python-dateutil >= 2.8.0

## License

Part of the OsMEN project.
