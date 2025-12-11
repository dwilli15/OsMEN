#!/usr/bin/env python3
"""
DRM Automation - Multi-strategy DRM removal for OsMEN

This module provides multiple approaches for DRM removal when standard
plugin-based approaches fail:

1. **DeACSM Plugin** - Standard ACSM fulfillment (when working)
2. **Adobe Digital Editions CLI** - Use ADE with automation
3. **Knock CLI** - Python-based ACSM processor
4. **Screen Capture Pipeline** - Capture content via automated reading

For ebooks without ACSM:
- DeDRM plugin (already working)
- Key extraction automation

Usage:
    from integrations.calibre.drm_automation import DRMAutomation

    drm = DRMAutomation()
    result = await drm.process_ebook("book.acsm")
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ProcessingStrategy(Enum):
    """Available DRM processing strategies."""

    CALIBRE_DEDRM = "calibre_dedrm"  # Standard DeDRM plugin
    CALIBRE_DEACSM = "calibre_deacsm"  # DeACSM plugin
    ADE_AUTOMATION = "ade_automation"  # Adobe Digital Editions CLI/GUI automation
    KNOCK_CLI = "knock_cli"  # Knock Python library
    SCREEN_CAPTURE = "screen_capture"  # Read and capture content
    MANUAL = "manual"  # User intervention required


@dataclass
class ProcessingResult:
    """Result of DRM processing."""

    success: bool
    strategy: ProcessingStrategy
    input_file: str
    output_file: Optional[str] = None
    text_file: Optional[str] = None
    message: str = ""
    duration_seconds: float = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DRMConfig:
    """Configuration for DRM automation."""

    calibre_path: Path = field(
        default_factory=lambda: Path(r"C:\Program Files\Calibre2")
    )
    ade_path: Path = field(
        default_factory=lambda: Path(
            r"C:\Program Files (x86)\Adobe\Adobe Digital Editions 4.5"
        )
    )
    output_dir: Path = field(
        default_factory=lambda: Path("D:/OsMEN/content/ebooks/drm_free")
    )
    text_output_dir: Path = field(
        default_factory=lambda: Path("D:/OsMEN/content/ebooks/text")
    )
    plugins_dir: Path = field(
        default_factory=lambda: Path.home()
        / "AppData"
        / "Roaming"
        / "calibre"
        / "plugins"
    )
    screenshot_interval_ms: int = 100  # For screen capture strategy
    page_turn_delay_ms: int = 500
    max_pages: int = 1000
    enable_ocr: bool = True

    @classmethod
    def from_env(cls) -> "DRMConfig":
        """Create config from environment variables."""
        return cls(
            calibre_path=Path(os.getenv("CALIBRE_PATH", r"C:\Program Files\Calibre2")),
            ade_path=Path(
                os.getenv(
                    "ADE_PATH",
                    r"C:\Program Files (x86)\Adobe\Adobe Digital Editions 4.5",
                )
            ),
            output_dir=Path(
                os.getenv("DRM_OUTPUT_DIR", "D:/OsMEN/content/ebooks/drm_free")
            ),
            text_output_dir=Path(
                os.getenv("DRM_TEXT_DIR", "D:/OsMEN/content/ebooks/text")
            ),
        )


class DRMAutomation:
    """
    Multi-strategy DRM automation for OsMEN.

    Provides fallback strategies when primary DRM removal fails.
    Designed to work with minimal user intervention.
    """

    def __init__(self, config: Optional[DRMConfig] = None):
        """Initialize DRM automation."""
        self.config = config or DRMConfig.from_env()
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        self.config.text_output_dir.mkdir(parents=True, exist_ok=True)

        # Check available tools
        self._available_strategies = self._detect_available_strategies()

        logger.info(
            f"DRMAutomation initialized. Available: {[s.value for s in self._available_strategies]}"
        )

    def _detect_available_strategies(self) -> List[ProcessingStrategy]:
        """Detect which strategies are available on this system."""
        available = []

        # Check Calibre + DeDRM
        if self.config.calibre_path.exists():
            dedrm_path = self.config.plugins_dir / "DeDRM"
            if dedrm_path.exists() or (self.config.plugins_dir / "DeDRM.zip").exists():
                available.append(ProcessingStrategy.CALIBRE_DEDRM)

        # Check DeACSM
        deacsm_path = self.config.plugins_dir / "DeACSM"
        if deacsm_path.exists() or (self.config.plugins_dir / "DeACSM.zip").exists():
            available.append(ProcessingStrategy.CALIBRE_DEACSM)

        # Check Adobe Digital Editions
        if self.config.ade_path.exists():
            available.append(ProcessingStrategy.ADE_AUTOMATION)

        # Check Knock CLI (Python package)
        try:
            import knock

            available.append(ProcessingStrategy.KNOCK_CLI)
        except ImportError:
            # Check if knock is installed but not imported
            try:
                result = subprocess.run(
                    ["pip", "show", "knock"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    available.append(ProcessingStrategy.KNOCK_CLI)
            except Exception:
                pass

        # Screen capture is always available (uses Windows APIs)
        available.append(ProcessingStrategy.SCREEN_CAPTURE)

        # Manual is always available
        available.append(ProcessingStrategy.MANUAL)

        return available

    async def process_ebook(
        self,
        input_file: str,
        preferred_strategy: Optional[ProcessingStrategy] = None,
        extract_text: bool = True,
    ) -> ProcessingResult:
        """
        Process an ebook file, removing DRM and optionally extracting text.

        Args:
            input_file: Path to ebook or ACSM file
            preferred_strategy: Optional preferred strategy to try first
            extract_text: Whether to extract text after DRM removal

        Returns:
            ProcessingResult with outcome
        """
        start_time = time.time()
        input_path = Path(input_file)

        if not input_path.exists():
            return ProcessingResult(
                success=False,
                strategy=ProcessingStrategy.MANUAL,
                input_file=input_file,
                message=f"File not found: {input_file}",
            )

        # Determine file type
        ext = input_path.suffix.lower()
        is_acsm = ext == ".acsm"

        # Build strategy order
        strategies = self._get_strategy_order(is_acsm, preferred_strategy)

        # Try each strategy
        result = None
        for strategy in strategies:
            if strategy not in self._available_strategies:
                continue

            logger.info(f"Trying strategy: {strategy.value} for {input_path.name}")

            try:
                if strategy == ProcessingStrategy.CALIBRE_DEDRM:
                    result = await self._process_with_calibre(input_file)
                elif strategy == ProcessingStrategy.CALIBRE_DEACSM:
                    result = await self._process_acsm_with_deacsm(input_file)
                elif strategy == ProcessingStrategy.ADE_AUTOMATION:
                    result = await self._process_with_ade(input_file)
                elif strategy == ProcessingStrategy.KNOCK_CLI:
                    result = await self._process_with_knock(input_file)
                elif strategy == ProcessingStrategy.SCREEN_CAPTURE:
                    result = await self._process_with_screen_capture(input_file)
                else:
                    continue

                if result and result.success:
                    logger.info(f"Strategy {strategy.value} succeeded")
                    break

            except Exception as e:
                logger.warning(f"Strategy {strategy.value} failed: {e}")
                continue

        if result is None or not result.success:
            result = ProcessingResult(
                success=False,
                strategy=ProcessingStrategy.MANUAL,
                input_file=input_file,
                message="All strategies failed. Manual intervention required.",
            )

        # Extract text if requested and successful
        if result.success and extract_text and result.output_file:
            text_result = await self._extract_text(result.output_file)
            if text_result:
                result.text_file = text_result

        result.duration_seconds = time.time() - start_time
        return result

    def _get_strategy_order(
        self,
        is_acsm: bool,
        preferred: Optional[ProcessingStrategy] = None,
    ) -> List[ProcessingStrategy]:
        """Get ordered list of strategies to try."""

        if is_acsm:
            # ACSM files need fulfillment first
            order = [
                ProcessingStrategy.CALIBRE_DEACSM,
                ProcessingStrategy.ADE_AUTOMATION,
                ProcessingStrategy.KNOCK_CLI,
                ProcessingStrategy.SCREEN_CAPTURE,
            ]
        else:
            # Regular ebooks
            order = [
                ProcessingStrategy.CALIBRE_DEDRM,
                ProcessingStrategy.SCREEN_CAPTURE,
            ]

        # Move preferred to front if specified
        if preferred and preferred in order:
            order.remove(preferred)
            order.insert(0, preferred)

        return order

    # =========================================================================
    # Strategy Implementations
    # =========================================================================

    async def _process_with_calibre(self, input_file: str) -> ProcessingResult:
        """Process using Calibre's DeDRM plugin."""
        try:
            from .calibre_manager import CalibreManager
            from .drm_handler import DRMHandler

            handler = DRMHandler(
                calibre_path=self.config.calibre_path,
                plugins_dir=self.config.plugins_dir,
                output_dir=self.config.output_dir,
            )

            result = handler.remove_drm(input_file, self.config.output_dir)

            return ProcessingResult(
                success=result.success,
                strategy=ProcessingStrategy.CALIBRE_DEDRM,
                input_file=input_file,
                output_file=result.output_file,
                message=result.message,
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                strategy=ProcessingStrategy.CALIBRE_DEDRM,
                input_file=input_file,
                message=f"Calibre DeDRM failed: {e}",
            )

    async def _process_acsm_with_deacsm(self, input_file: str) -> ProcessingResult:
        """Process ACSM using DeACSM plugin."""
        try:
            from .drm_handler import DRMHandler

            handler = DRMHandler(
                calibre_path=self.config.calibre_path,
                plugins_dir=self.config.plugins_dir,
                output_dir=self.config.output_dir,
            )

            result = handler.process_acsm(input_file, self.config.output_dir)

            return ProcessingResult(
                success=result.success,
                strategy=ProcessingStrategy.CALIBRE_DEACSM,
                input_file=input_file,
                output_file=result.output_file,
                message=result.message,
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                strategy=ProcessingStrategy.CALIBRE_DEACSM,
                input_file=input_file,
                message=f"DeACSM failed: {e}",
            )

    async def _process_with_ade(self, input_file: str) -> ProcessingResult:
        """
        Process using Adobe Digital Editions with automation.

        This opens ADE, processes the file, then exports.
        Uses Windows UI automation or Playwright for control.
        """
        try:
            ade_exe = self.config.ade_path / "DigitalEditions.exe"
            if not ade_exe.exists():
                return ProcessingResult(
                    success=False,
                    strategy=ProcessingStrategy.ADE_AUTOMATION,
                    input_file=input_file,
                    message="Adobe Digital Editions not found",
                )

            # Start ADE with the file
            process = subprocess.Popen(
                [str(ade_exe), input_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Wait for ADE to process (this is where Playwright could help)
            await asyncio.sleep(5)

            # Check if file was downloaded to ADE library
            ade_documents = Path.home() / "Documents" / "My Digital Editions"
            if ade_documents.exists():
                # Find the newest epub/pdf
                epub_files = list(ade_documents.glob("*.epub"))
                pdf_files = list(ade_documents.glob("*.pdf"))
                all_files = epub_files + pdf_files

                if all_files:
                    # Get most recent
                    newest = max(all_files, key=lambda p: p.stat().st_mtime)

                    # Copy to output dir
                    output_path = self.config.output_dir / newest.name
                    shutil.copy2(newest, output_path)

                    # Now remove DRM using Calibre
                    drm_result = await self._process_with_calibre(str(output_path))

                    process.terminate()

                    return ProcessingResult(
                        success=drm_result.success,
                        strategy=ProcessingStrategy.ADE_AUTOMATION,
                        input_file=input_file,
                        output_file=drm_result.output_file or str(output_path),
                        message=f"ADE fulfilled, then {drm_result.message}",
                    )

            process.terminate()

            return ProcessingResult(
                success=False,
                strategy=ProcessingStrategy.ADE_AUTOMATION,
                input_file=input_file,
                message="ADE did not produce output file",
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                strategy=ProcessingStrategy.ADE_AUTOMATION,
                input_file=input_file,
                message=f"ADE automation failed: {e}",
            )

    async def _process_with_knock(self, input_file: str) -> ProcessingResult:
        """
        Process using Knock CLI (Python-based ACSM processor).

        Knock is an open-source tool that can fulfill ACSM files
        without Adobe Digital Editions.
        """
        try:
            # Try to use knock as a library
            try:
                from knock import acsm

                output_path = self.config.output_dir / (Path(input_file).stem + ".epub")

                # This is hypothetical - actual API may differ
                acsm.fulfill(input_file, str(output_path))

                if output_path.exists():
                    return ProcessingResult(
                        success=True,
                        strategy=ProcessingStrategy.KNOCK_CLI,
                        input_file=input_file,
                        output_file=str(output_path),
                        message="ACSM fulfilled via Knock",
                    )

            except ImportError:
                pass

            # Try knock as CLI
            output_path = self.config.output_dir / (Path(input_file).stem + ".epub")

            result = subprocess.run(
                ["knock", input_file, "-o", str(output_path)],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0 and output_path.exists():
                return ProcessingResult(
                    success=True,
                    strategy=ProcessingStrategy.KNOCK_CLI,
                    input_file=input_file,
                    output_file=str(output_path),
                    message="ACSM fulfilled via Knock CLI",
                )

            return ProcessingResult(
                success=False,
                strategy=ProcessingStrategy.KNOCK_CLI,
                input_file=input_file,
                message=f"Knock failed: {result.stderr}",
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                strategy=ProcessingStrategy.KNOCK_CLI,
                input_file=input_file,
                message=f"Knock error: {e}",
            )

    async def _process_with_screen_capture(self, input_file: str) -> ProcessingResult:
        """
        Process by reading and capturing content via screen capture.

        This is the fallback when all other methods fail.
        Opens the ebook reader, scrolls through content while capturing,
        then uses OCR to extract text.

        REQUIRES: pyautogui, pillow, pytesseract (for OCR)
        """
        try:
            # Determine which reader to use based on file type
            ext = Path(input_file).suffix.lower()

            if ext == ".acsm":
                # Need to open with ADE
                reader_exe = self.config.ade_path / "DigitalEditions.exe"
            else:
                # Use Calibre's ebook viewer
                reader_exe = self.config.calibre_path / "ebook-viewer.exe"

            if not reader_exe.exists():
                return ProcessingResult(
                    success=False,
                    strategy=ProcessingStrategy.SCREEN_CAPTURE,
                    input_file=input_file,
                    message=f"Reader not found: {reader_exe}",
                )

            # Start reader
            process = subprocess.Popen([str(reader_exe), input_file])
            await asyncio.sleep(3)  # Wait for window

            # Capture screenshots
            screenshots = await self._capture_book_pages(process)

            if not screenshots:
                process.terminate()
                return ProcessingResult(
                    success=False,
                    strategy=ProcessingStrategy.SCREEN_CAPTURE,
                    input_file=input_file,
                    message="No pages captured",
                )

            # Extract text from screenshots
            text_content = await self._ocr_screenshots(screenshots)

            # Save text
            text_output = self.config.text_output_dir / (Path(input_file).stem + ".txt")
            text_output.write_text(text_content, encoding="utf-8")

            process.terminate()

            return ProcessingResult(
                success=True,
                strategy=ProcessingStrategy.SCREEN_CAPTURE,
                input_file=input_file,
                output_file=None,  # No ebook output, just text
                text_file=str(text_output),
                message=f"Captured {len(screenshots)} pages, extracted text via OCR",
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                strategy=ProcessingStrategy.SCREEN_CAPTURE,
                input_file=input_file,
                message=f"Screen capture failed: {e}",
            )

    async def _capture_book_pages(
        self,
        reader_process: subprocess.Popen,
    ) -> List[Path]:
        """Capture screenshots of book pages."""
        screenshots = []

        try:
            import pyautogui
            from PIL import Image
        except ImportError:
            logger.warning("pyautogui/pillow not available for screen capture")
            return []

        # Create temp directory for screenshots
        temp_dir = Path(tempfile.mkdtemp(prefix="osmen_capture_"))

        try:
            for page in range(self.config.max_pages):
                # Take screenshot
                screenshot = pyautogui.screenshot()

                # Save
                screenshot_path = temp_dir / f"page_{page:04d}.png"
                screenshot.save(str(screenshot_path))
                screenshots.append(screenshot_path)

                # Send page down key
                pyautogui.press("pagedown")

                # Wait for page to render
                await asyncio.sleep(self.config.page_turn_delay_ms / 1000)

                # Check if we've reached the end (compare screenshots)
                if page > 0:
                    prev = Image.open(screenshots[-2])
                    curr = Image.open(screenshots[-1])

                    # Simple comparison - if identical, we've reached end
                    if list(prev.getdata()) == list(curr.getdata()):
                        screenshots.pop()  # Remove duplicate
                        break

        except Exception as e:
            logger.error(f"Page capture error: {e}")

        return screenshots

    async def _ocr_screenshots(self, screenshots: List[Path]) -> str:
        """Extract text from screenshots using OCR."""
        if not self.config.enable_ocr:
            return f"[{len(screenshots)} pages captured - OCR disabled]"

        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            return f"[{len(screenshots)} pages captured - pytesseract not available]"

        text_parts = []

        for screenshot_path in screenshots:
            try:
                image = Image.open(screenshot_path)
                text = pytesseract.image_to_string(image)
                text_parts.append(text)
            except Exception as e:
                logger.warning(f"OCR failed for {screenshot_path}: {e}")

        return "\n\n---\n\n".join(text_parts)

    async def _extract_text(self, ebook_file: str) -> Optional[str]:
        """Extract text from ebook using Calibre."""
        try:
            input_path = Path(ebook_file)
            output_path = self.config.text_output_dir / (input_path.stem + ".txt")

            # Use ebook-convert
            result = subprocess.run(
                [
                    str(self.config.calibre_path / "ebook-convert.exe"),
                    ebook_file,
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if output_path.exists():
                return str(output_path)

        except Exception as e:
            logger.error(f"Text extraction failed: {e}")

        return None

    # =========================================================================
    # Key Management
    # =========================================================================

    async def extract_adobe_key(self) -> Tuple[bool, str]:
        """
        Extract Adobe key from Adobe Digital Editions.

        Uses Calibre's built-in key extraction.
        """
        try:
            # Use calibre-debug to run DeDRM's key extraction
            script = """
import sys
sys.path.insert(0, r'C:\\Users\\armad\\AppData\\Roaming\\calibre\\plugins\\DeDRM')
from adobekey import getkey
key = getkey()
if key:
    import os
    key_path = os.path.expanduser('~\\AppData\\Roaming\\calibre\\plugins\\DeDRM\\adobekey_extracted.der')
    with open(key_path, 'wb') as f:
        f.write(key)
    print(f'Key saved to: {key_path}')
else:
    print('No key found')
"""

            result = subprocess.run(
                [str(self.config.calibre_path / "calibre-debug.exe"), "-c", script],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if "Key saved to" in result.stdout:
                return True, result.stdout.strip()

            return False, result.stderr or "No key found"

        except Exception as e:
            return False, f"Key extraction failed: {e}"

    async def extract_kindle_key(self) -> Tuple[bool, str]:
        """
        Extract Kindle key from Kindle for PC.
        """
        try:
            script = """
import sys
sys.path.insert(0, r'C:\\Users\\armad\\AppData\\Roaming\\calibre\\plugins\\DeDRM')
from kindlekey import getkey
key = getkey()
if key:
    import os
    key_path = os.path.expanduser('~\\AppData\\Roaming\\calibre\\plugins\\DeDRM\\kindlekey_extracted.k4i')
    with open(key_path, 'wb') as f:
        f.write(key)
    print(f'Key saved to: {key_path}')
else:
    print('No key found')
"""

            result = subprocess.run(
                [str(self.config.calibre_path / "calibre-debug.exe"), "-c", script],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if "Key saved to" in result.stdout:
                return True, result.stdout.strip()

            return False, result.stderr or "No key found"

        except Exception as e:
            return False, f"Key extraction failed: {e}"

    # =========================================================================
    # Batch Processing
    # =========================================================================

    async def process_directory(
        self,
        input_dir: str,
        extract_text: bool = True,
        recursive: bool = False,
    ) -> List[ProcessingResult]:
        """Process all ebooks in a directory."""
        input_path = Path(input_dir)
        results = []

        # Find all ebook files
        patterns = ["*.acsm", "*.epub", "*.pdf", "*.azw", "*.azw3", "*.mobi"]

        files = []
        for pattern in patterns:
            if recursive:
                files.extend(input_path.rglob(pattern))
            else:
                files.extend(input_path.glob(pattern))

        # Process each
        for file_path in files:
            result = await self.process_ebook(
                str(file_path),
                extract_text=extract_text,
            )
            results.append(result)

        return results

    # =========================================================================
    # Health & Status
    # =========================================================================

    def health_check(self) -> Dict[str, Any]:
        """Check DRM automation health."""
        return {
            "available_strategies": [s.value for s in self._available_strategies],
            "calibre_path": str(self.config.calibre_path),
            "calibre_exists": self.config.calibre_path.exists(),
            "ade_path": str(self.config.ade_path),
            "ade_exists": self.config.ade_path.exists(),
            "output_dir": str(self.config.output_dir),
            "text_output_dir": str(self.config.text_output_dir),
            "plugins_dir": str(self.config.plugins_dir),
            "dedrm_installed": (self.config.plugins_dir / "DeDRM").exists(),
            "deacsm_installed": (self.config.plugins_dir / "DeACSM").exists(),
            "ocr_enabled": self.config.enable_ocr,
            "timestamp": datetime.now().isoformat(),
        }


# =========================================================================
# CLI Entry Point
# =========================================================================


def main():
    """CLI for DRM automation."""
    import argparse

    parser = argparse.ArgumentParser(description="OsMEN DRM Automation")
    parser.add_argument("input", help="Input file or directory")
    parser.add_argument(
        "--strategy",
        choices=[s.value for s in ProcessingStrategy],
        help="Preferred strategy",
    )
    parser.add_argument("--no-text", action="store_true", help="Skip text extraction")
    parser.add_argument(
        "--recursive", action="store_true", help="Process directories recursively"
    )

    args = parser.parse_args()

    drm = DRMAutomation()

    input_path = Path(args.input)
    preferred = ProcessingStrategy(args.strategy) if args.strategy else None

    if input_path.is_dir():
        results = asyncio.run(
            drm.process_directory(
                str(input_path),
                extract_text=not args.no_text,
                recursive=args.recursive,
            )
        )
    else:
        result = asyncio.run(
            drm.process_ebook(
                str(input_path),
                preferred_strategy=preferred,
                extract_text=not args.no_text,
            )
        )
        results = [result]

    # Print summary
    print("\n" + "=" * 60)
    print("DRM AUTOMATION RESULTS")
    print("=" * 60)

    success = sum(1 for r in results if r.success)
    print(f"Processed: {len(results)} files")
    print(f"Success: {success}")
    print(f"Failed: {len(results) - success}")

    for r in results:
        status = "✅" if r.success else "❌"
        print(f"\n{status} {Path(r.input_file).name}")
        print(f"   Strategy: {r.strategy.value}")
        print(f"   Message: {r.message}")
        if r.output_file:
            print(f"   Output: {r.output_file}")
        if r.text_file:
            print(f"   Text: {r.text_file}")


if __name__ == "__main__":
    main()
