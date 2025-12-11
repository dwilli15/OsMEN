#!/usr/bin/env python3
"""
Calibre Manager - Core Calibre integration for OsMEN
Handles library operations, book management, and format conversions.
"""

import json
import logging
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class CalibreConfig:
    """Configuration for Calibre integration"""

    calibre_path: Path = field(
        default_factory=lambda: Path(r"C:\Program Files\Calibre2")
    )
    library_path: Path = field(
        default_factory=lambda: Path.home() / "OneDrive" / "Calibre Library"
    )
    output_dir: Path = field(default_factory=lambda: Path("D:/OsMEN/content/ebooks"))
    timeout: int = 300  # seconds for conversion operations

    @classmethod
    def from_env(cls) -> "CalibreConfig":
        """Create config from environment variables"""
        return cls(
            calibre_path=Path(os.getenv("CALIBRE_PATH", r"C:\Program Files\Calibre2")),
            library_path=Path(
                os.getenv(
                    "CALIBRE_LIBRARY", str(Path.home() / "OneDrive" / "Calibre Library")
                )
            ),
            output_dir=Path(os.getenv("CALIBRE_OUTPUT_DIR", "D:/OsMEN/content/ebooks")),
            timeout=int(os.getenv("CALIBRE_TIMEOUT", "300")),
        )

    @property
    def calibredb(self) -> Path:
        return self.calibre_path / "calibredb.exe"

    @property
    def ebook_convert(self) -> Path:
        return self.calibre_path / "ebook-convert.exe"

    @property
    def calibre_debug(self) -> Path:
        return self.calibre_path / "calibre-debug.exe"

    @property
    def calibre_customize(self) -> Path:
        return self.calibre_path / "calibre-customize.exe"


@dataclass
class Book:
    """Represents a book in Calibre library"""

    id: int
    title: str
    authors: str
    formats: List[str]
    path: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    series: Optional[str] = None
    series_index: Optional[float] = None
    publisher: Optional[str] = None
    pubdate: Optional[str] = None
    rating: Optional[float] = None
    identifiers: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_calibredb(cls, data: Dict[str, Any]) -> "Book":
        """Create Book from calibredb output"""
        return cls(
            id=data.get("id", 0),
            title=data.get("title", "Unknown"),
            authors=data.get("authors", "Unknown"),
            formats=data.get("formats", "").split(",") if data.get("formats") else [],
            path=data.get("path"),
            tags=data.get("tags", "").split(",") if data.get("tags") else [],
            series=data.get("series"),
            series_index=data.get("series_index"),
            publisher=data.get("publisher"),
            pubdate=data.get("pubdate"),
            rating=data.get("rating"),
            identifiers=data.get("identifiers", {}),
        )


class CalibreManager:
    """
    Manages Calibre library operations and ebook conversions.

    Features:
    - Library search and management
    - Format conversions (EPUB, PDF, MOBI, AZW3, TXT)
    - Metadata operations
    - DRM detection and handling
    - Text extraction from ebooks
    """

    def __init__(self, config: Optional[CalibreConfig] = None):
        self.config = config or CalibreConfig.from_env()
        self._validate_installation()
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

    def _validate_installation(self) -> None:
        """Validate Calibre installation"""
        if not self.config.calibre_path.exists():
            raise FileNotFoundError(f"Calibre not found at {self.config.calibre_path}")
        if not self.config.calibredb.exists():
            raise FileNotFoundError(f"calibredb not found at {self.config.calibredb}")

    def _run_calibredb(self, *args, check_running: bool = True) -> Tuple[bool, str]:
        """Run calibredb command"""
        cmd = [str(self.config.calibredb)] + list(args)

        # Check if Calibre GUI is running
        if check_running:
            cmd.extend(["--with-library", str(self.config.library_path)])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.config.timeout
            )
            # If Calibre GUI is running, library is locked but accessible
            if "Another calibre program" in result.stderr:
                return True, "Library accessible (Calibre GUI running)"
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    def _run_convert(
        self, input_file: str, output_file: str, **options
    ) -> Tuple[bool, str]:
        """Run ebook-convert command"""
        cmd = [str(self.config.ebook_convert), input_file, output_file]

        # Add conversion options
        for key, value in options.items():
            if value is True:
                cmd.append(f"--{key.replace('_', '-')}")
            elif value is not False and value is not None:
                cmd.extend([f"--{key.replace('_', '-')}", str(value)])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.config.timeout
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Conversion timed out"
        except Exception as e:
            return False, str(e)

    def search(self, query: str, fields: Optional[List[str]] = None) -> List[Book]:
        """
        Search Calibre library.

        Args:
            query: Search query (supports Calibre search syntax)
            fields: Fields to return (default: id,title,authors,formats)

        Returns:
            List of matching Book objects
        """
        fields = fields or ["id", "title", "authors", "formats", "path", "tags"]

        success, output = self._run_calibredb(
            "list", "--fields", ",".join(fields), "--for-machine", "-s", query
        )

        if not success:
            logger.error(f"Search failed: {output}")
            return []

        try:
            data = json.loads(output)
            return [Book.from_calibredb(item) for item in data]
        except json.JSONDecodeError:
            logger.error(f"Failed to parse calibredb output: {output}")
            return []

    def get_book(self, book_id: int) -> Optional[Book]:
        """Get book by ID"""
        success, output = self._run_calibredb(
            "list",
            "--fields",
            "id,title,authors,formats,path,tags,series,series_index,publisher,pubdate,rating",
            "--for-machine",
            "-s",
            f"id:{book_id}",
        )

        if not success:
            return None

        try:
            data = json.loads(output)
            if data:
                return Book.from_calibredb(data[0])
        except json.JSONDecodeError:
            pass

        return None

    def add_book(self, file_path: str, automerge: bool = True) -> Optional[int]:
        """
        Add book to Calibre library.

        Args:
            file_path: Path to ebook file
            automerge: Auto-merge with existing book if duplicate

        Returns:
            Book ID if successful, None otherwise
        """
        args = ["add", file_path]
        if automerge:
            args.append("--automerge=overwrite")

        success, output = self._run_calibredb(*args)

        if success:
            # Try to extract book ID from output
            for line in output.split("\n"):
                if "Added book ids:" in line:
                    try:
                        book_id = int(line.split(":")[-1].strip())
                        return book_id
                    except ValueError:
                        pass
            logger.info(f"Book added: {output}")
            return -1  # Success but couldn't get ID

        logger.error(f"Failed to add book: {output}")
        return None

    def export_book(
        self,
        book_id: int,
        output_dir: Optional[Path] = None,
        format: Optional[str] = None,
    ) -> Optional[Path]:
        """
        Export book from Calibre library.

        Args:
            book_id: Book ID to export
            output_dir: Output directory
            format: Preferred format (e.g., 'epub', 'pdf')

        Returns:
            Path to exported file
        """
        output_dir = output_dir or self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        args = ["export", str(book_id), "--to-dir", str(output_dir)]
        if format:
            args.extend(["--formats", format])

        success, output = self._run_calibredb(*args)

        if success:
            # Find exported file
            book = self.get_book(book_id)
            if book:
                for fmt in [format] if format else book.formats:
                    pattern = f"*{book_id}*.{fmt.lower()}"
                    files = list(output_dir.glob(pattern))
                    if files:
                        return files[0]

        logger.error(f"Export failed: {output}")
        return None

    def convert(
        self,
        input_file: str,
        output_format: str,
        output_dir: Optional[Path] = None,
        **options,
    ) -> Optional[Path]:
        """
        Convert ebook to different format.

        Args:
            input_file: Input file path
            output_format: Target format (epub, pdf, mobi, azw3, txt, docx)
            output_dir: Output directory
            **options: Conversion options (e.g., base_font_size, embed_all_fonts)

        Returns:
            Path to converted file
        """
        input_path = Path(input_file)
        if not input_path.exists():
            logger.error(f"Input file not found: {input_file}")
            return None

        output_dir = output_dir or self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"{input_path.stem}.{output_format.lower()}"

        success, output = self._run_convert(
            str(input_path), str(output_file), **options
        )

        if success and output_file.exists():
            logger.info(f"Converted: {input_file} -> {output_file}")
            return output_file

        logger.error(f"Conversion failed: {output}")
        return None

    def extract_text(
        self, input_file: str, output_dir: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Extract text content from ebook.

        Args:
            input_file: Input ebook path
            output_dir: Output directory for text file

        Returns:
            Path to text file
        """
        return self.convert(
            input_file, "txt", output_dir, txt_output_formatting="plain"
        )

    def batch_convert(
        self,
        input_files: List[str],
        output_format: str,
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Optional[Path]]:
        """
        Convert multiple ebooks.

        Args:
            input_files: List of input file paths
            output_format: Target format
            output_dir: Output directory

        Returns:
            Dictionary mapping input files to output paths
        """
        results = {}
        for input_file in input_files:
            results[input_file] = self.convert(input_file, output_format, output_dir)
        return results

    def get_library_stats(self) -> Dict[str, Any]:
        """Get library statistics"""
        success, output = self._run_calibredb("list", "--for-machine")

        if not success:
            return {"error": output}

        try:
            books = json.loads(output)

            # Count formats
            format_counts = {}
            for book in books:
                for fmt in book.get("formats", "").split(","):
                    fmt = fmt.strip().upper()
                    if fmt:
                        format_counts[fmt] = format_counts.get(fmt, 0) + 1

            return {
                "total_books": len(books),
                "format_counts": format_counts,
                "library_path": str(self.config.library_path),
                "timestamp": datetime.now().isoformat(),
            }
        except json.JSONDecodeError:
            return {"error": "Failed to parse library data"}

    def get_installed_plugins(self) -> List[Dict[str, Any]]:
        """Get list of installed Calibre plugins"""
        try:
            result = subprocess.run(
                [
                    str(self.config.calibre_debug),
                    "-c",
                    "from calibre.customize.ui import initialized_plugins; "
                    "import json; "
                    "plugins = [{'name': p.name, 'version': str(p.version), 'type': type(p).__name__} "
                    "for p in initialized_plugins()]; "
                    "print(json.dumps(plugins))",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                # Extract JSON from output
                for line in result.stdout.strip().split("\n"):
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Failed to get plugins: {e}")

        return []

    def install_plugin(self, plugin_path: str) -> Tuple[bool, str]:
        """
        Install a Calibre plugin.

        Args:
            plugin_path: Path to plugin zip file

        Returns:
            Tuple of (success, message)
        """
        if not Path(plugin_path).exists():
            return False, f"Plugin file not found: {plugin_path}"

        try:
            result = subprocess.run(
                [str(self.config.calibre_customize), "-a", plugin_path],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                return True, result.stdout
            return False, result.stderr
        except Exception as e:
            return False, str(e)

    def health_check(self) -> Dict[str, Any]:
        """Check Calibre integration health"""
        health = {
            "calibre_installed": self.config.calibre_path.exists(),
            "calibredb_available": self.config.calibredb.exists(),
            "ebook_convert_available": self.config.ebook_convert.exists(),
            "library_path_exists": self.config.library_path.exists(),
            "output_dir_exists": self.config.output_dir.exists(),
        }

        # Test calibredb
        success, _ = self._run_calibredb("list", "--limit", "1", "--for-machine")
        health["calibredb_working"] = success

        # Get plugin info
        plugins = self.get_installed_plugins()
        health["plugins_count"] = len(plugins)
        health["dedrm_installed"] = any(p["name"] == "DeDRM" for p in plugins)
        health["deacsm_installed"] = any(p["name"] == "DeACSM" for p in plugins)

        health["status"] = (
            "healthy"
            if all(
                [
                    health["calibre_installed"],
                    health["calibredb_working"],
                    health["library_path_exists"],
                ]
            )
            else "degraded"
        )

        health["timestamp"] = datetime.now().isoformat()
        return health


def main():
    """Test Calibre Manager"""
    manager = CalibreManager()

    # Health check
    print("=== Health Check ===")
    health = manager.health_check()
    print(json.dumps(health, indent=2))

    # Library stats
    print("\n=== Library Stats ===")
    stats = manager.get_library_stats()
    print(json.dumps(stats, indent=2))

    # Search test
    print("\n=== Search Test ===")
    books = manager.search("Pastoral")
    for book in books[:5]:
        print(f"  {book.id}: {book.title} by {book.authors}")

    # Plugins
    print("\n=== Installed Plugins ===")
    plugins = manager.get_installed_plugins()
    for p in plugins:
        if "DRM" in p["name"] or "ACSM" in p["name"]:
            print(f"  {p['name']} v{p['version']}")


if __name__ == "__main__":
    main()
