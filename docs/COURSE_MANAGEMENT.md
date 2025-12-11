# Course Management System

The OsMEN Course Management system provides a complete solution for importing college syllabi and managing your academic course load. It integrates with your calendar and Obsidian vault to keep all course information organized.

## Features

- **Syllabus Parsing**: Automatic extraction of course info, assignments, exams from PDF/DOCX
- **Calendar Sync**: Events synced to Google Calendar or Outlook
- **Obsidian Integration**: Structured notes created for each course
- **Conflict Detection**: Scheduling conflicts identified automatically
- **Semester Overview**: Dashboard of all courses and upcoming deadlines

## Quick Start

### 1. Import a Single Syllabus

```python
from agents.knowledge_management.course_manager import CourseManager

manager = CourseManager()

result = manager.import_syllabus(
    file_path="path/to/syllabus.pdf",
    semester="Fall",  # Optional - auto-detected
    year=2025,        # Optional - defaults to current year
    sync_calendar=True,
    create_obsidian_notes=True
)

print(f"Imported: {result['course']['code']} - {result['course']['name']}")
print(f"Events created: {result['events_created']}")
```

### 2. Bulk Import (Semester Setup)

```python
# Import multiple syllabi at once
result = manager.bulk_import(
    syllabus_files=[
        "syllabi/CS401_syllabus.pdf",
        "syllabi/MATH301_syllabus.pdf",
        "syllabi/PHYS201_syllabus.pdf",
    ],
    semester="Fall",
    year=2025
)

print(f"Imported {result['successful']} of {result['total_files']} courses")
```

### 3. Get Semester Overview

```python
overview = manager.get_semester_overview("Fall", 2025)

print(f"Courses: {overview['total_courses']}")
print(f"Exams: {overview['exams']}")
print(f"Assignments: {overview['assignments']}")

# Upcoming this week
for event in overview['upcoming_this_week']:
    print(f"  {event['date']}: {event['title']}")
```

## API Endpoints

The Course Management API is available at `/api/courses/`:

### Upload Syllabus (Preview)
```http
POST /api/courses/upload
Content-Type: multipart/form-data

file: syllabus.pdf
semester: Fall (optional)
year: 2025 (optional)
```

Returns parsed preview before confirmation.

### Confirm Import
```http
POST /api/courses/import/confirm
Content-Type: application/json

{
  "file_path": "/path/to/uploaded/syllabus.pdf",
  "semester": "Fall",
  "year": 2025,
  "sync_calendar": true,
  "create_obsidian_notes": true
}
```

### Bulk Import
```http
POST /api/courses/import/bulk
Content-Type: application/json

{
  "file_paths": [
    "/path/to/syllabus1.pdf",
    "/path/to/syllabus2.pdf"
  ],
  "semester": "Fall",
  "year": 2025
}
```

### List Courses
```http
GET /api/courses?semester=Fall&year=2025
```

### Get Semester Overview
```http
GET /api/courses/semester?semester=Fall&year=2025
```

### Get Course Details
```http
GET /api/courses/{course_id}
```

### Sync Course to Calendar
```http
POST /api/courses/{course_id}/sync/calendar
```

### Create/Update Obsidian Notes
```http
POST /api/courses/{course_id}/sync/obsidian
```

### Mark Event Complete
```http
PATCH /api/courses/{course_id}/events/{event_id}/complete
```

## MCP Tools

Course management is also available via MCP tools:

| Tool | Description |
|------|-------------|
| `course_import_syllabus` | Import a syllabus file (PDF/DOCX) |
| `course_list` | List all courses |
| `course_semester_overview` | Get semester overview |
| `course_bulk_import` | Import multiple syllabi |
| `course_sync_calendar` | Sync course to calendar |
| `course_sync_obsidian` | Create Obsidian notes |

## n8n Workflow

The `course_semester_setup.json` workflow automates:

1. **Webhook Trigger**: Accepts syllabus file upload
2. **Parsing**: Extracts course information
3. **Calendar Sync**: Creates calendar events
4. **Obsidian Notes**: Creates course structure
5. **Conflict Check**: Alerts on scheduling conflicts
6. **Weekly Review**: Scheduled overview of upcoming events

To import via n8n:
```bash
curl -X POST http://localhost:5678/webhook/course-import \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/path/to/syllabus.pdf", "semester": "Fall", "year": 2025}'
```

## Obsidian Templates

Course notes are created using these templates:

| Template | Purpose |
|----------|---------|
| `Course Template.md` | Main course note with links |
| `Semester Overview Template.md` | Semester dashboard |
| `Assignment Tracker Template.md` | Track assignments |
| `Exam Tracker Template.md` | Track exams and study plans |
| `Syllabus Template.md` | Syllabus summary |
| `Lecture Notes Template.md` | Individual lecture notes |

Templates are in `obsidian-vault/Templates/`.

## File Structure

After importing courses, your Obsidian vault will have:

```
obsidian-vault/
├── Templates/
│   ├── Course Template.md
│   ├── Semester Overview Template.md
│   └── ...
└── Courses/
    └── 2025/
        └── Fall/
            ├── Fall 2025 Overview.md
            ├── CS 401/
            │   ├── CS 401 - Advanced Algorithms.md
            │   ├── Syllabus.md
            │   ├── Assignments.md
            │   ├── Exams.md
            │   └── Lecture Notes/
            └── MATH 301/
                └── ...
```

## Configuration

Set the following environment variables:

```bash
# Obsidian vault path
OBSIDIAN_VAULT_PATH=./obsidian-vault

# Course data storage
OSMEN_DATA_DIR=./data/courses

# Upload directory
OSMEN_UPLOAD_DIR=./data/uploads/syllabi
```

## Extracted Data

The syllabus parser extracts:

### Course Information
- Course code and name
- Instructor name and contact
- Semester and year
- Credit hours
- Schedule/location

### Events
- Exam dates (midterm, final, quizzes)
- Assignment due dates
- Project deadlines
- Important dates (add/drop, withdrawal)

### Structure
- Grading breakdown
- Required materials
- Office hours
- Course policies

## Conflict Detection

The system automatically detects:

| Conflict Type | Description | Severity |
|--------------|-------------|----------|
| Direct Overlap | Same time events | Critical |
| Same Day | Multiple exams same day | High |
| Adjacent Days | Back-to-back deadlines | Medium |
| Close Proximity | Events within days | Low |

Suggestions for resolution are provided with each conflict.

## Tips

1. **Upload early**: Import syllabi at the start of semester
2. **Check conflicts**: Review detected conflicts immediately
3. **Use templates**: Customize templates for your workflow
4. **Weekly reviews**: Use semester overview for planning
5. **Mark complete**: Track progress by marking events done

## Troubleshooting

### Syllabus not parsing correctly
- Ensure PDF is text-based (not scanned image)
- Check DOCX isn't password protected
- Try converting to different format

### Calendar sync failing
- Verify OAuth credentials are configured
- Check calendar permissions
- Review logs in `logs/calendar.log`

### Obsidian notes not created
- Set `OBSIDIAN_VAULT_PATH` environment variable
- Ensure vault directory is writable
- Check Obsidian integration logs

## Related Documentation

- [Calendar Integration](docs/CALENDAR_INTEGRATION.md)
- [Obsidian Integration](docs/OBSIDIAN_INTEGRATION.md)
- [Syllabus Parser](parsers/syllabus/README.md)
- [Personal Assistant](agents/personal_assistant/README.md)
