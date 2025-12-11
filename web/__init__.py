"""
OsMEN Web Dashboard
FastAPI-based web interface for syllabus management and calendar integration.
"""

from .app import app, create_app

__all__ = ["create_app", "app"]
