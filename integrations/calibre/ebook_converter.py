#!/usr/bin/env python3
"""
Ebook Converter - High-level conversion utilities for OsMEN
Provides text extraction, format conversion, and batch processing.
"""

import json
import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class OutputFormat(Enum):
    """Supported output formats"""

    EPUB = "epub"
    PDF = "pdf"
    MOBI = "mobi"
    AZW3 = "azw3"
    TXT = "txt"
    DOCX = "docx"
    HTML = "html"
    HTMLZ = "htmlz"
    RTF = "rtf"
    MD = "md"


class InputFormat(Enum):
    """Supported input formats"""

    EPUB = "epub"
    PDF = "pdf"
    MOBI = "mobi"
    AZW = "azw"
    AZW3 = "azw3"
    DOCX = "docx"
    DOC = "doc"
    HTML = "html"
    TXT = "txt"
    RTF = "rtf"
    CBZ = "cbz"
    CBR = "cbr"


@dataclass
class ConversionResult:
    """Result of conversion operation"""

    success: bool
    input_file: str
    output_file: Optional[str] = None
    input_format: Optional[str] = None
    output_format: Optional[str] = None
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    duration_seconds: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ExtractedText:
    """Extracted text content"""

    source_file: str
    text_file: str
    title: Optional[str] = None
    author: Optional[str] = None
    word_count: int = 0
    char_count: int = 0
    success: bool = True
    message: str = ""


class EbookConverter:
    """
    High-level ebook conversion and text extraction.

    Features:
    - Format conversion (EPUB, PDF, MOBI, TXT, DOCX)
    - Text extraction with OCR support
    - Batch processing
    - Metadata extraction and preservation
    - Quality presets for different use cases
    """

    # Conversion quality presets
    PRESETS = {
        "study": {  # Optimized for study/annotation
            "base_font_size": 12,
            "embed_all_fonts": False,
            "subset_embedded_fonts": True,
            "change_justification": "left",
            "smarten_punctuation": True,
        },
        "archive": {  # Maximum quality preservation
            "embed_all_fonts": True,
            "subset_embedded_fonts": False,
            "no_inline_toc": False,
            "keep_ligatures": True,
        },
        "kindle": {  # Optimized for Kindle
            "output_profile": "kindle_oasis",
            "mobi_file_type": "both",
            "personal_doc": True,
        },
        "text": {  # Plain text extraction
            "txt_output_formatting": "plain",
            "keep_links": False,
            "keep_image_references": False,
        },
    }

    def __init__(
        self,
        calibre_path: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        ocr_enabled: bool = True,
    ):
        self.calibre_path = calibre_path or Path(r"C:\Program Files\Calibre2")
        self.output_dir = output_dir or Path("D:/OsMEN/content/ebooks/converted")
        self.ocr_enabled = ocr_enabled

        self._validate()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _validate(self) -> None:
        """Validate converter installation"""
        if not self.calibre_path.exists():
            raise FileNotFoundError(f"Calibre not found: {self.calibre_path}")

    @property
    def ebook_convert(self) -> Path:
        return self.calibre_path / "ebook-convert.exe"

    @property
    def ebook_meta(self) -> Path:
        return self.calibre_path / "ebook-meta.exe"

    def _run_convert(
        self, input_file: str, output_file: str, timeout: int = 300, **options
    ) -> Tuple[bool, str, float]:
        """Run ebook-convert command"""
        import time

        start = time.time()

        cmd = [str(self.ebook_convert), input_file, output_file]

        for key, value in options.items():
            if value is True:
                cmd.append(f"--{key.replace('_', '-')}")
            elif value is not False and value is not None:
                cmd.extend([f"--{key.replace('_', '-')}", str(value)])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            duration = time.time() - start
            return result.returncode == 0, result.stdout + result.stderr, duration
        except subprocess.TimeoutExpired:
            return False, "Conversion timed out", time.time() - start
        except Exception as e:
            return False, str(e), time.time() - start

    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from ebook"""
        try:
            result = subprocess.run(
                [str(self.ebook_meta), file_path],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                metadata = {}
                for line in result.stdout.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        metadata[key.strip().lower()] = value.strip()
                return metadata
        except Exception as e:
            logger.debug(f"Metadata extraction error: {e}")

        return {}

    def convert(
        self,
        input_file: str,
        output_format: Union[str, OutputFormat],
        output_dir: Optional[Path] = None,
        preset: Optional[str] = None,
        **options,
    ) -> ConversionResult:
        """
        Convert ebook to target format.

        Args:
            input_file: Path to input file
            output_format: Target format (epub, pdf, txt, etc.)
            output_dir: Output directory
            preset: Quality preset (study, archive, kindle, text)
            **options: Additional conversion options

        Returns:
            ConversionResult with operation status
        """
        path = Path(input_file)
        if not path.exists():
            return ConversionResult(
                success=False,
                input_file=input_file,
                message=f"Input file not found: {input_file}",
            )

        # Get format string
        if isinstance(output_format, OutputFormat):
            fmt = output_format.value
        else:
            fmt = output_format.lower()

        output_dir = output_dir or self.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{path.stem}.{fmt}"

        # Apply preset options
        conv_options = {}
        if preset and preset in self.PRESETS:
            conv_options.update(self.PRESETS[preset])
        conv_options.update(options)

        # Get input metadata
        metadata = self.get_metadata(input_file)

        success, output, duration = self._run_convert(
            str(path), str(output_file), **conv_options
        )

        if success and output_file.exists():
            return ConversionResult(
                success=True,
                input_file=input_file,
                output_file=str(output_file),
                input_format=path.suffix.lower().replace(".", ""),
                output_format=fmt,
                message=f"Converted successfully in {duration:.1f}s",
                metadata=metadata,
                duration_seconds=duration,
            )

        return ConversionResult(
            success=False,
            input_file=input_file,
            input_format=path.suffix.lower().replace(".", ""),
            output_format=fmt,
            message=f"Conversion failed: {output}",
            duration_seconds=duration,
        )

    def extract_text(
        self, input_file: str, output_dir: Optional[Path] = None, use_ocr: bool = False
    ) -> ExtractedText:
        """
        Extract text content from ebook.

        Args:
            input_file: Path to input ebook
            output_dir: Output directory for text file
            use_ocr: Use OCR for scanned PDFs

        Returns:
            ExtractedText with content info
        """
        path = Path(input_file)
        if not path.exists():
            return ExtractedText(
                source_file=input_file,
                text_file="",
                success=False,
                message="Input file not found",
            )

        output_dir = output_dir or self.output_dir / "text"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{path.stem}.txt"

        # Check if OCR is needed for PDF
        if path.suffix.lower() == ".pdf" and use_ocr and self.ocr_enabled:
            return self._extract_with_ocr(str(path), str(output_file))

        # Use Calibre for text extraction
        result = self.convert(input_file, OutputFormat.TXT, output_dir, preset="text")

        if result.success and result.output_file:
            # Get text stats
            text_path = Path(result.output_file)
            content = text_path.read_text(encoding="utf-8", errors="ignore")

            return ExtractedText(
                source_file=input_file,
                text_file=result.output_file,
                title=result.metadata.get("title"),
                author=result.metadata.get("author"),
                word_count=len(content.split()),
                char_count=len(content),
                success=True,
                message="Text extracted successfully",
            )

        return ExtractedText(
            source_file=input_file, text_file="", success=False, message=result.message
        )

    def _extract_with_ocr(self, input_pdf: str, output_txt: str) -> ExtractedText:
        """Extract text from scanned PDF using OCR"""
        try:
            import subprocess

            # Check if ocrmypdf is available
            ocrmypdf_check = subprocess.run(
                ["where", "ocrmypdf"], capture_output=True, shell=True
            )

            if ocrmypdf_check.returncode != 0:
                # Fall back to Calibre
                logger.info("ocrmypdf not found, using Calibre for text extraction")
                return self._calibre_text_extract(input_pdf, output_txt)

            # Create temp file for OCR'd PDF
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp_pdf = tmp.name

            try:
                # Run OCR
                result = subprocess.run(
                    ["ocrmypdf", "--skip-text", input_pdf, tmp_pdf],
                    capture_output=True,
                    text=True,
                    timeout=600,
                )

                if result.returncode == 0:
                    # Extract text from OCR'd PDF
                    return self._calibre_text_extract(tmp_pdf, output_txt, input_pdf)
                else:
                    return ExtractedText(
                        source_file=input_pdf,
                        text_file="",
                        success=False,
                        message=f"OCR failed: {result.stderr}",
                    )
            finally:
                if os.path.exists(tmp_pdf):
                    os.unlink(tmp_pdf)

        except Exception as e:
            return ExtractedText(
                source_file=input_pdf,
                text_file="",
                success=False,
                message=f"OCR error: {e}",
            )

    def _calibre_text_extract(
        self, input_file: str, output_file: str, source_file: Optional[str] = None
    ) -> ExtractedText:
        """Extract text using Calibre"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        success, output, duration = self._run_convert(
            input_file, str(output_path), txt_output_formatting="plain"
        )

        if success and output_path.exists():
            content = output_path.read_text(encoding="utf-8", errors="ignore")
            metadata = self.get_metadata(input_file)

            return ExtractedText(
                source_file=source_file or input_file,
                text_file=str(output_path),
                title=metadata.get("title"),
                author=metadata.get("author"),
                word_count=len(content.split()),
                char_count=len(content),
                success=True,
                message="Text extracted via Calibre",
            )

        return ExtractedText(
            source_file=source_file or input_file,
            text_file="",
            success=False,
            message=f"Text extraction failed: {output}",
        )

    def batch_convert(
        self,
        input_files: List[str],
        output_format: Union[str, OutputFormat],
        output_dir: Optional[Path] = None,
        preset: Optional[str] = None,
    ) -> List[ConversionResult]:
        """
        Convert multiple ebooks.

        Args:
            input_files: List of input file paths
            output_format: Target format
            output_dir: Output directory
            preset: Quality preset

        Returns:
            List of ConversionResult objects
        """
        results = []
        for file_path in input_files:
            result = self.convert(file_path, output_format, output_dir, preset)
            results.append(result)
        return results

    def batch_extract_text(
        self,
        input_files: List[str],
        output_dir: Optional[Path] = None,
        use_ocr: bool = False,
    ) -> List[ExtractedText]:
        """
        Extract text from multiple ebooks.

        Args:
            input_files: List of input file paths
            output_dir: Output directory
            use_ocr: Use OCR for scanned PDFs

        Returns:
            List of ExtractedText objects
        """
        results = []
        for file_path in input_files:
            result = self.extract_text(file_path, output_dir, use_ocr)
            results.append(result)
        return results

    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get supported input and output formats"""
        return {
            "input": [f.value for f in InputFormat],
            "output": [f.value for f in OutputFormat],
            "presets": list(self.PRESETS.keys()),
        }

    def health_check(self) -> Dict[str, Any]:
        """Check converter health"""
        health = {
            "calibre_path": str(self.calibre_path),
            "ebook_convert_exists": self.ebook_convert.exists(),
            "ebook_meta_exists": self.ebook_meta.exists(),
            "output_dir": str(self.output_dir),
            "output_dir_exists": self.output_dir.exists(),
            "ocr_enabled": self.ocr_enabled,
        }

        # Check OCR tools
        if self.ocr_enabled:
            try:
                result = subprocess.run(
                    ["where", "ocrmypdf"], capture_output=True, shell=True
                )
                health["ocrmypdf_available"] = result.returncode == 0
            except Exception:
                health["ocrmypdf_available"] = False

        # Test ebook-convert
        try:
            result = subprocess.run(
                [str(self.ebook_convert), "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            health["ebook_convert_working"] = result.returncode == 0
            if result.returncode == 0:
                health["calibre_version"] = result.stdout.strip().split("\n")[0]
        except Exception:
            health["ebook_convert_working"] = False

        health["status"] = (
            "healthy"
            if all(
                [
                    health["ebook_convert_exists"],
                    health.get("ebook_convert_working", False),
                ]
            )
            else "degraded"
        )

        health["timestamp"] = datetime.now().isoformat()
        return health


def main():
    """Test Ebook Converter"""
    converter = EbookConverter()

    # Health check
    print("=== Converter Health ===")
    health = converter.health_check()
    print(json.dumps(health, indent=2))

    # Supported formats
    print("\n=== Supported Formats ===")
    formats = converter.get_supported_formats()
    print(f"Input: {', '.join(formats['input'])}")
    print(f"Output: {', '.join(formats['output'])}")
    print(f"Presets: {', '.join(formats['presets'])}")


if __name__ == "__main__":
    main()
