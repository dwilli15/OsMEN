"""
ConvertX Integration Module for OsMEN
=====================================

Universal file format converter supporting 1000+ formats via ConvertX.
Handles: video, audio, images, documents, 3D models, ebooks, and more.

Service: http://localhost:3000
"""

from .client import ConvertXClient, convert_file, get_supported_formats
from .utils import (
    COMMON_CONVERSIONS,
    get_possible_conversions,
    is_format_supported,
    normalize_format,
)

__all__ = [
    "ConvertXClient",
    "convert_file",
    "get_supported_formats",
    "get_possible_conversions",
    "is_format_supported",
    "normalize_format",
    "COMMON_CONVERSIONS",
]
