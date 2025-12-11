"""
Calibre Integration for OsMEN
Provides ebook management, conversion, and DRM handling capabilities.
"""

from .calibre_manager import CalibreManager
from .drm_handler import DRMHandler
from .ebook_converter import EbookConverter

__all__ = ["CalibreManager", "DRMHandler", "EbookConverter"]
