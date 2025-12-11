#!/usr/bin/env python3
"""
Book Text Extractor for OsMEN Course Materials
Extracts text from PDFs and EPUBs, handles OCR for scanned documents.
"""

import html.parser
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple

# Configure paths
os.environ["PATH"] += r";C:\Program Files\Tesseract-OCR"
POPPLER_PATH = os.path.expanduser(
    r"~\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe\poppler-25.07.0\Library\bin"
)
os.environ["PATH"] += f";{POPPLER_PATH}"


class EPUBExtractor:
    """Extract text from EPUB files."""

    def extract(self, epub_path: str) -> str:
        """Extract all text from an EPUB file."""
        epub_path = Path(epub_path)
        if not epub_path.exists():
            raise FileNotFoundError(f"EPUB not found: {epub_path}")

        print(f"📖 Extracting: {epub_path.name}")

        all_text = []

        with zipfile.ZipFile(epub_path, "r") as zf:
            # Find all HTML/XHTML content files
            content_files = [
                name
                for name in zf.namelist()
                if name.endswith((".html", ".xhtml", ".htm")) and "META-INF" not in name
            ]

            # Sort to maintain reading order (approximate)
            content_files.sort()

            for cf in content_files:
                try:
                    content = zf.read(cf).decode("utf-8", errors="ignore")
                    text = self._html_to_text(content)
                    if text.strip():
                        all_text.append(text)
                except Exception as e:
                    print(f"   ⚠️ Error reading {cf}: {e}")

        print(f"   ✅ Extracted {len(all_text)} sections")
        return "\n\n".join(all_text)

    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text."""
        # Remove script and style elements
        html_content = re.sub(
            r"<script[^>]*>.*?</script>",
            "",
            html_content,
            flags=re.DOTALL | re.IGNORECASE,
        )
        html_content = re.sub(
            r"<style[^>]*>.*?</style>",
            "",
            html_content,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # Replace common block elements with newlines
        html_content = re.sub(
            r"<(p|div|br|h[1-6]|li|tr)[^>]*>", "\n", html_content, flags=re.IGNORECASE
        )
        html_content = re.sub(
            r"</(p|div|h[1-6]|li|tr)>", "\n", html_content, flags=re.IGNORECASE
        )

        # Remove all other tags
        html_content = re.sub(r"<[^>]+>", "", html_content)

        # Decode HTML entities
        html_content = html_content.replace("&nbsp;", " ")
        html_content = html_content.replace("&amp;", "&")
        html_content = html_content.replace("&lt;", "<")
        html_content = html_content.replace("&gt;", ">")
        html_content = html_content.replace("&quot;", '"')
        html_content = html_content.replace("&#39;", "'")

        # Clean up whitespace
        lines = [line.strip() for line in html_content.split("\n")]
        html_content = "\n".join(line for line in lines if line)

        return html_content


def extract_pdf_text(pdf_path: str) -> Tuple[str, bool]:
    """
    Extract text from a PDF. Returns (text, needs_ocr).
    """
    import pdfplumber

    pdf_path = Path(pdf_path)
    print(f"📄 Analyzing: {pdf_path.name}")

    all_text = []
    total_chars = 0

    with pdfplumber.open(pdf_path) as pdf:
        num_pages = len(pdf.pages)

        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            total_chars += len(text.strip())
            all_text.append(f"--- Page {i+1} ---\n{text}")

            if (i + 1) % 20 == 0:
                print(f"   📝 Processed {i+1}/{num_pages} pages...", end="\r")

    # Determine if OCR needed (less than 100 chars per page average)
    avg_chars = total_chars / num_pages if num_pages > 0 else 0
    needs_ocr = avg_chars < 100

    if needs_ocr:
        print(
            f"   ⚠️ Low text content ({avg_chars:.0f} chars/page avg) - OCR recommended"
        )
    else:
        print(f"   ✅ Good text content ({avg_chars:.0f} chars/page avg)")

    return "\n\n".join(all_text), needs_ocr


def ocr_pdf(pdf_path: str, dpi: int = 150) -> str:
    """Run OCR on a scanned PDF."""
    import pytesseract
    from pdf2image import convert_from_path

    pdf_path = Path(pdf_path)
    print(f"🔍 Running OCR: {pdf_path.name}")

    # Configure tesseract
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    # Convert to images
    print(f"   📄 Converting PDF to images (DPI={dpi})...")
    images = convert_from_path(
        str(pdf_path),
        dpi=dpi,
        poppler_path=POPPLER_PATH if os.path.exists(POPPLER_PATH) else None,
        fmt="jpeg",
        thread_count=4,
    )

    # OCR each page
    all_text = []
    total_pages = len(images)

    for i, image in enumerate(images, 1):
        print(f"   📝 OCR page {i}/{total_pages}...", end="\r")
        text = pytesseract.image_to_string(image, lang="eng")
        all_text.append(f"--- Page {i} ---\n{text}")
        image.close()

    print(f"\n   ✅ OCR completed {total_pages} pages")
    return "\n\n".join(all_text)


def process_course_materials(
    raw_folder: str, text_folder: str, force_ocr: bool = False
) -> Dict:
    """
    Process all course materials in a folder.

    Args:
        raw_folder: Folder containing raw materials (PDFs, EPUBs)
        text_folder: Output folder for extracted text
        force_ocr: Force OCR even for PDFs with text

    Returns:
        Processing results summary
    """
    raw_path = Path(raw_folder)
    text_path = Path(text_folder)
    text_path.mkdir(parents=True, exist_ok=True)

    results = {
        "extracted": [],
        "ocr_processed": [],
        "skipped": [],
        "errors": [],
        "drm_files": [],
    }

    # Get all processable files
    files = list(raw_path.glob("*.pdf")) + list(raw_path.glob("*.epub"))
    acsm_files = list(raw_path.glob("*.acsm"))

    print(f"\n{'='*60}")
    print(f"📚 COURSE MATERIAL EXTRACTION")
    print(f"{'='*60}")
    print(f"Found: {len(files)} processable files, {len(acsm_files)} DRM files")
    print(f"Output: {text_path}")
    print()

    # Track DRM files
    for acsm in acsm_files:
        results["drm_files"].append(str(acsm))
        print(f"🔐 DRM file skipped: {acsm.name}")

    # Process each file
    for file_path in files:
        output_file = text_path / f"{file_path.stem}.txt"

        # Skip if already processed
        if output_file.exists() and not force_ocr:
            print(f"\n⏭️ Already processed: {file_path.name}")
            results["skipped"].append(str(file_path))
            continue

        print(f"\n{'─'*50}")

        try:
            if file_path.suffix.lower() == ".epub":
                # Extract EPUB
                extractor = EPUBExtractor()
                text = extractor.extract(str(file_path))

            elif file_path.suffix.lower() == ".pdf":
                # Try normal extraction first
                text, needs_ocr = extract_pdf_text(str(file_path))

                if needs_ocr or force_ocr:
                    # Run OCR
                    text = ocr_pdf(str(file_path))
                    results["ocr_processed"].append(str(file_path))
                else:
                    results["extracted"].append(str(file_path))
            else:
                continue

            # Save text
            output_file.write_text(text, encoding="utf-8")
            print(f"   💾 Saved: {output_file.name} ({len(text):,} chars)")

            if str(file_path) not in results["ocr_processed"]:
                results["extracted"].append(str(file_path))

        except Exception as e:
            print(f"   ❌ Error: {e}")
            results["errors"].append({"file": str(file_path), "error": str(e)})

    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Extracted: {len(results['extracted'])}")
    print(f"🔍 OCR Processed: {len(results['ocr_processed'])}")
    print(f"⏭️ Skipped: {len(results['skipped'])}")
    print(f"🔐 DRM Files: {len(results['drm_files'])}")
    print(f"❌ Errors: {len(results['errors'])}")

    if results["drm_files"]:
        print(
            f"\n⚠️ DRM files need manual processing via Adobe Digital Editions + Calibre:"
        )
        for f in results["drm_files"]:
            print(f"   • {Path(f).name}")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract text from course materials")
    parser.add_argument("raw_folder", help="Folder containing raw materials")
    parser.add_argument("--output", "-o", help="Output folder for text files")
    parser.add_argument(
        "--force-ocr", action="store_true", help="Force OCR on all PDFs"
    )

    args = parser.parse_args()

    raw_folder = args.raw_folder
    text_folder = args.output or str(Path(raw_folder).parent / "text")

    results = process_course_materials(raw_folder, text_folder, args.force_ocr)

    sys.exit(0 if not results["errors"] else 1)
