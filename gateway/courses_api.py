#!/usr/bin/env python3
"""
Course Management API Router

Provides REST endpoints for:
- Uploading and parsing syllabi
- Managing course loads
- Syncing to calendar and Obsidian
- Semester overview
"""

import logging
import os
import shutil

# Add parent to path for imports
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.knowledge_management.course_manager import CourseManager

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/courses", tags=["Courses"])

# Initialize course manager
_course_manager = None


def get_course_manager() -> CourseManager:
    """Get or create CourseManager instance"""
    global _course_manager
    if _course_manager is None:
        _course_manager = CourseManager()
    return _course_manager


# ─────────────────────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────────────────────


class CourseResponse(BaseModel):
    """Course information response"""

    id: str
    code: str
    name: str
    instructor: str
    semester: str
    year: int
    credits: Optional[int] = None
    obsidian_folder: Optional[str] = None
    created_at: Optional[str] = None


class EventResponse(BaseModel):
    """Course event response"""

    id: str
    course_id: str
    title: str
    event_type: str
    date: str
    priority: str = "medium"
    status: str = "scheduled"


class ImportPreviewResponse(BaseModel):
    """Preview of syllabus import before confirmation"""

    success: bool
    file_name: str
    course: Optional[CourseResponse] = None
    events: List[EventResponse] = []
    conflicts: List[dict] = []
    warnings: List[str] = []


class ImportConfirmRequest(BaseModel):
    """Request to confirm and finalize import"""

    file_path: str
    semester: Optional[str] = None
    year: Optional[int] = None
    sync_calendar: bool = True
    create_obsidian_notes: bool = True


class BulkImportRequest(BaseModel):
    """Request to import multiple syllabi"""

    file_paths: List[str]
    semester: Optional[str] = None
    year: Optional[int] = None


class SemesterOverviewResponse(BaseModel):
    """Semester overview response"""

    semester: str
    year: int
    total_courses: int
    total_events: int
    exams: int
    assignments: int
    courses: List[CourseResponse]
    upcoming_this_week: List[EventResponse]
    conflicts: List[dict]


# ─────────────────────────────────────────────────────────────────────────────
# Upload & Parse Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/upload", response_model=ImportPreviewResponse)
async def upload_syllabus(
    file: UploadFile = File(...),
    semester: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
):
    """
    Upload a syllabus file (PDF/DOCX) and get a preview of parsed content.

    Returns extracted course info and events for review before confirmation.
    """
    # Validate file type
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: PDF, DOCX. Got: {file.content_type}",
        )

    # Save uploaded file temporarily
    upload_dir = Path(os.getenv("OSMEN_UPLOAD_DIR", "data/uploads/syllabi"))
    upload_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename.replace(' ', '_')}"
    file_path = upload_dir / safe_filename

    try:
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Parse syllabus (preview only, don't save yet)
        manager = get_course_manager()

        # Import for preview
        result = manager.import_syllabus(
            file_path=str(file_path),
            semester=semester,
            year=year,
            sync_calendar=False,  # Don't sync yet - just preview
            create_obsidian_notes=False,
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=422,
                detail=f"Failed to parse syllabus: {result.get('error')}",
            )

        # Build preview response
        course_data = result.get("course", {})

        # Get events for this course
        course_id = course_data.get("id")
        events = [
            EventResponse(
                id=e.id,
                course_id=e.course_id,
                title=e.title,
                event_type=e.event_type,
                date=e.date or "",
                priority=e.priority,
                status=e.status,
            )
            for e in manager.events.values()
            if e.course_id == course_id
        ]

        return ImportPreviewResponse(
            success=True,
            file_name=file.filename,
            course=CourseResponse(**course_data) if course_data else None,
            events=events,
            conflicts=result.get("conflicts", []),
            warnings=result.get("warnings", []),
        )

    except Exception as e:
        logger.error(f"Error processing syllabus: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/confirm")
async def confirm_import(request: ImportConfirmRequest):
    """
    Confirm and finalize a syllabus import.

    This will:
    - Sync events to calendar (if enabled)
    - Create Obsidian notes structure (if enabled)
    - Finalize the course in the knowledge base
    """
    manager = get_course_manager()

    result = manager.import_syllabus(
        file_path=request.file_path,
        semester=request.semester,
        year=request.year,
        sync_calendar=request.sync_calendar,
        create_obsidian_notes=request.create_obsidian_notes,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=422, detail=f"Import failed: {result.get('error')}"
        )

    return result


@router.post("/import/bulk")
async def bulk_import(request: BulkImportRequest):
    """
    Import multiple syllabi at once for semester setup.

    This is ideal for beginning-of-semester course load setup.
    """
    manager = get_course_manager()

    result = manager.bulk_import(
        syllabus_files=request.file_paths,
        semester=request.semester,
        year=request.year,
    )

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Course CRUD Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/", response_model=List[CourseResponse])
async def list_courses(
    semester: Optional[str] = Query(None, description="Filter by semester"),
    year: Optional[int] = Query(None, description="Filter by year"),
):
    """List all courses, optionally filtered by semester and year"""
    manager = get_course_manager()
    courses = manager.list_courses(semester=semester, year=year)
    return [CourseResponse(**c) for c in courses]


@router.get("/semester")
async def get_semester_overview(
    semester: Optional[str] = Query(None, description="Semester name"),
    year: Optional[int] = Query(None, description="Academic year"),
):
    """Get comprehensive overview of all courses for a semester"""
    manager = get_course_manager()
    overview = manager.get_semester_overview(semester=semester, year=year)

    return SemesterOverviewResponse(
        semester=overview["semester"],
        year=overview["year"],
        total_courses=overview["total_courses"],
        total_events=overview["total_events"],
        exams=overview["exams"],
        assignments=overview["assignments"],
        courses=[CourseResponse(**c) for c in overview["courses"]],
        upcoming_this_week=[
            EventResponse(**e) for e in overview.get("upcoming_this_week", [])
        ],
        conflicts=overview.get("conflicts", []),
    )


@router.get("/{course_id}")
async def get_course(course_id: str):
    """Get detailed information about a specific course"""
    manager = get_course_manager()
    course = manager.get_course(course_id)

    if not course:
        raise HTTPException(status_code=404, detail=f"Course {course_id} not found")

    return course


@router.delete("/{course_id}")
async def delete_course(course_id: str):
    """Delete a course and its associated events"""
    manager = get_course_manager()

    if course_id not in manager.courses:
        raise HTTPException(status_code=404, detail=f"Course {course_id} not found")

    # Remove course
    del manager.courses[course_id]

    # Remove associated events
    events_to_remove = [
        eid for eid, e in manager.events.items() if e.course_id == course_id
    ]
    for eid in events_to_remove:
        del manager.events[eid]

    # Save changes
    manager._save_data()

    return {
        "success": True,
        "message": f"Course {course_id} deleted",
        "events_removed": len(events_to_remove),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Event Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/{course_id}/events", response_model=List[EventResponse])
async def get_course_events(course_id: str):
    """Get all events for a specific course"""
    manager = get_course_manager()

    events = [
        EventResponse(
            id=e.id,
            course_id=e.course_id,
            title=e.title,
            event_type=e.event_type,
            date=e.date or "",
            priority=e.priority,
            status=e.status,
        )
        for e in manager.events.values()
        if e.course_id == course_id
    ]

    return sorted(events, key=lambda x: x.date)


@router.patch("/{course_id}/events/{event_id}/complete")
async def mark_event_complete(course_id: str, event_id: str):
    """Mark an event (assignment/exam) as completed"""
    manager = get_course_manager()

    if event_id not in manager.events:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

    event = manager.events[event_id]

    if event.course_id != course_id:
        raise HTTPException(
            status_code=400, detail="Event does not belong to this course"
        )

    event.status = "completed"
    manager._save_data()

    return {"success": True, "event_id": event_id, "status": "completed"}


# ─────────────────────────────────────────────────────────────────────────────
# Sync Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/{course_id}/sync/calendar")
async def sync_course_to_calendar(course_id: str):
    """Sync course events to calendar"""
    manager = get_course_manager()

    if course_id not in manager.courses:
        raise HTTPException(status_code=404, detail=f"Course {course_id} not found")

    if not manager._calendar_available:
        raise HTTPException(
            status_code=503, detail="Calendar integration not available"
        )

    # Get course events
    events = [e for e in manager.events.values() if e.course_id == course_id]

    synced = manager._sync_events_to_calendar(events)

    return {"success": True, "course_id": course_id, "events_synced": synced}


@router.post("/{course_id}/sync/obsidian")
async def sync_course_to_obsidian(course_id: str):
    """Create/update Obsidian notes for a course"""
    manager = get_course_manager()

    if course_id not in manager.courses:
        raise HTTPException(status_code=404, detail=f"Course {course_id} not found")

    if not manager._obsidian_available:
        raise HTTPException(
            status_code=503, detail="Obsidian integration not available"
        )

    course = manager.courses[course_id]
    events = [e for e in manager.events.values() if e.course_id == course_id]

    notes = manager._create_course_notes(course, events)

    return {"success": True, "course_id": course_id, "notes_created": notes}
