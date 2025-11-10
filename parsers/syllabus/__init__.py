"""
Syllabus Parsers Module

Automated extraction of course information from syllabus documents.
"""

from .pdf_parser import PDFSyllabusParser
from .docx_parser import DOCXSyllabusParser
from .syllabus_parser import SyllabusParser
from .conflict_validator import ConflictValidator

__all__ = [
    'PDFSyllabusParser',
    'DOCXSyllabusParser',
    'SyllabusParser',
    'ConflictValidator'
]

__version__ = '1.0.0'
