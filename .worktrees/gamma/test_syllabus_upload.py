#!/usr/bin/env python3
"""
Gamma G1.2 coverage – syllabus upload endpoint validation.
"""

import sys
import types
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).parent))

from web.main import app, check_auth, BASE_DIR  # noqa: E402


class StubSyllabusParser:
    """Minimal parser stub returning deterministic data."""

    def parse(self, file_path: str):
        self.last_path = file_path
        return {
            "course_info": {"course_name": "Test Course"},
            "events": [{"title": "Event 1", "date": "2025-09-01"}],
            "assignments": [],
        }

    def normalize_data(self, parsed):
        return {
            "course": parsed["course_info"],
            "events": parsed["events"],
            "metadata": {"total_events": len(parsed["events"])},
        }


@pytest.fixture
def upload_client(monkeypatch):
    """Provide authenticated TestClient plus parser stub."""
    app.dependency_overrides[check_auth] = lambda: {"email": "gamma@osmen.ai"}
    stub_module = types.ModuleType("syllabus_parser")
    stub_module.SyllabusParser = StubSyllabusParser
    monkeypatch.setitem(sys.modules, "syllabus_parser", stub_module)
    client = TestClient(app)
    try:
        yield client
    finally:
        client.close()
        app.dependency_overrides.pop(check_auth, None)


def _cleanup_previews(created_files):
    for path in created_files:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def test_syllabus_upload_accepts_pdf_and_writes_preview(upload_client):
    """Validate happy-path upload flow with parser stub + preview persistence."""
    preview_dir = BASE_DIR.parent / "content" / "inbox"
    preview_dir.mkdir(parents=True, exist_ok=True)
    before = set(preview_dir.glob("syllabus_*.json"))

    files = {"file": ("sample.pdf", b"%PDF-1.4 fake content", "application/pdf")}
    response = upload_client.post("/api/syllabus/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["event_count"] == 1

    after = set(preview_dir.glob("syllabus_*.json"))
    created = after - before
    assert created, "Expected a preview artifact to be written"
    _cleanup_previews(created)


def test_syllabus_upload_rejects_unsupported_extension(upload_client):
    """Unsupported file extensions should return 400."""
    files = {"file": ("notes.txt", b"plain text", "text/plain")}
    response = upload_client.post("/api/syllabus/upload", files=files)

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_syllabus_upload_rejects_files_larger_than_10mb(upload_client):
    """Large files should be rejected before hitting parser logic."""
    oversized = b"x" * (10 * 1024 * 1024 + 1)
    files = {"file": ("big.pdf", oversized, "application/pdf")}
    response = upload_client.post("/api/syllabus/upload", files=files)

    assert response.status_code == 400
    assert response.json()["detail"] == "File too large (max 10MB)"


def test_syllabus_preview_endpoint_returns_normalized_data(upload_client):
    """Stored preview JSON should be retrievable via the preview API."""
    preview_dir = BASE_DIR.parent / "content" / "inbox"
    preview_dir.mkdir(parents=True, exist_ok=True)
    before = set(preview_dir.glob("syllabus_*.json"))

    files = {"file": ("sample.pdf", b"%PDF-1.4 fake content", "application/pdf")}
    response = upload_client.post("/api/syllabus/upload", files=files)
    assert response.status_code == 200
    preview_id = response.json()["preview_id"]

    preview_resp = upload_client.get(f"/api/syllabus/preview/{preview_id}")
    assert preview_resp.status_code == 200
    payload = preview_resp.json()
    assert payload["metadata"]["total_events"] == 1
    assert payload["events"][0]["title"] == "Event 1"

    after = set(preview_dir.glob("syllabus_*.json"))
    created = after - before
    _cleanup_previews(created)
