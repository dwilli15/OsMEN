#!/usr/bin/env python3
"""
OCR PDF Processing Script for OsMEN
Converts scanned PDFs to searchable PDFs and extracts text.

Usage:
    python ocr_pdf.py <input_pdf> [output_pdf] [--text-only]
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

# Add Tesseract and Poppler to PATH
os.environ["PATH"] += r";C:\Program Files\Tesseract-OCR"
os.environ["PATH"] += r";C:\Program Files\Poppler\Library\bin"

# Try to find Poppler in common locations
poppler_paths = [
    os.path.expanduser(
        r"~\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe\poppler-25.07.0\Library\bin"
    ),
    r"C:\Program Files\Poppler\Library\bin",
    r"C:\Program Files\poppler-25.07.0\Library\bin",
    r"C:\tools\poppler\Library\bin",
    os.path.expanduser(r"~\AppData\Local\Programs\Poppler\bin"),
]

poppler_path = None
for p in poppler_paths:
    if os.path.exists(p):
        poppler_path = p
        os.environ["PATH"] += f";{p}"
        break

import pytesseract
from pdf2image import convert_from_path
from PIL import Image

# Configure tesseract path
tesseract_paths = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]

for tp in tesseract_paths:
    if os.path.exists(tp):
        pytesseract.pytesseract.tesseract_cmd = tp
        break


def ocr_pdf_to_text(
    pdf_path: str,
    output_txt: Optional[str] = None,
    dpi: int = 200,
    first_page: int = 1,
    last_page: Optional[int] = None,
) -> str:
    """
    Convert a scanned PDF to text using OCR.

    Args:
        pdf_path: Path to input PDF
        output_txt: Optional path to save text file
        dpi: Resolution for PDF rendering (higher = better OCR but slower)
        first_page: First page to process (1-indexed)
        last_page: Last page to process (None = all pages)

    Returns:
        Extracted text from all pages
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    print(f"🔍 Processing: {pdf_path.name}")
    print(f"   DPI: {dpi}, Pages: {first_page} to {last_page or 'end'}")

    # Convert PDF pages to images
    print("   📄 Converting PDF to images...")
    images = convert_from_path(
        str(pdf_path),
        dpi=dpi,
        first_page=first_page,
        last_page=last_page,
        poppler_path=poppler_path,
        fmt="jpeg",
        thread_count=4,
    )

    # OCR each page
    all_text = []
    total_pages = len(images)

    for i, image in enumerate(images, start=first_page):
        print(f"   📝 OCR page {i}/{first_page + total_pages - 1}...", end="\r")

        # Perform OCR
        text = pytesseract.image_to_string(image, lang="eng")
        all_text.append(f"--- Page {i} ---\n{text}\n")

        # Free memory
        image.close()

    print(f"\n   ✅ Completed {total_pages} pages")

    full_text = "\n".join(all_text)

    # Save text file if requested
    if output_txt:
        output_path = Path(output_txt)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(full_text, encoding="utf-8")
        print(f"   💾 Saved to: {output_path}")

    return full_text


def ocr_pdf_to_searchable(pdf_path: str, output_pdf: str, dpi: int = 200) -> None:
    """
    Convert a scanned PDF to a searchable PDF with OCR text layer.

    Args:
        pdf_path: Path to input PDF
        output_pdf: Path for output searchable PDF
        dpi: Resolution for processing
    """
    from PIL import Image

    pdf_path = Path(pdf_path)
    output_pdf = Path(output_pdf)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    print(f"🔍 Creating searchable PDF: {pdf_path.name}")

    # Convert to images
    images = convert_from_path(
        str(pdf_path),
        dpi=dpi,
        poppler_path=poppler_path,
        fmt="jpeg",
        thread_count=4,
    )

    # Create PDF with OCR text
    pdf_pages = []
    for i, image in enumerate(images, 1):
        print(f"   📝 Processing page {i}/{len(images)}...", end="\r")

        # Get OCR PDF data for this page
        pdf_data = pytesseract.image_to_pdf_or_hocr(image, extension="pdf", lang="eng")
        pdf_pages.append(pdf_data)
        image.close()

    print(f"\n   📦 Merging {len(pdf_pages)} pages...")

    # Simple concatenation won't work for PDFs, so save first page and note limitation
    # For proper PDF merging, we'd need pikepdf or PyPDF2
    try:
        import pikepdf

        with pikepdf.Pdf.new() as output:
            for pdf_data in pdf_pages:
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp.write(pdf_data)
                    tmp_path = tmp.name

                with pikepdf.Pdf.open(tmp_path) as page_pdf:
                    output.pages.extend(page_pdf.pages)

                os.unlink(tmp_path)

            output.save(str(output_pdf))

        print(f"   ✅ Saved searchable PDF: {output_pdf}")

    except ImportError:
        print("   ⚠️ pikepdf not available, saving only text extraction")
        text_path = output_pdf.with_suffix(".txt")
        ocr_pdf_to_text(str(pdf_path), str(text_path), dpi=dpi)


def analyze_pdf_needs_ocr(pdf_path: str, sample_pages: int = 3) -> bool:
    """
    Analyze if a PDF needs OCR by checking if text can be extracted.

    Args:
        pdf_path: Path to PDF
        sample_pages: Number of pages to sample

    Returns:
        True if PDF appears to need OCR
    """
    try:
        import pdfplumber

        with pdfplumber.open(pdf_path) as pdf:
            total_chars = 0
            pages_to_check = min(sample_pages, len(pdf.pages))

            for i in range(pages_to_check):
                text = pdf.pages[i].extract_text() or ""
                total_chars += len(text.strip())

            avg_chars = total_chars / pages_to_check if pages_to_check > 0 else 0

            # If less than 100 chars per page on average, probably scanned
            return avg_chars < 100

    except Exception as e:
        print(f"Error analyzing PDF: {e}")
        return True  # Assume needs OCR if we can't analyze


def batch_ocr_folder(
    input_folder: str, output_folder: str, text_folder: Optional[str] = None
) -> dict:
    """
    Process all PDFs in a folder that need OCR.

    Args:
        input_folder: Folder containing PDFs
        output_folder: Folder for searchable PDFs
        text_folder: Optional folder for text extraction

    Returns:
        Dict with processing results
    """
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    if text_folder:
        text_path = Path(text_folder)
        text_path.mkdir(parents=True, exist_ok=True)

    results = {"processed": [], "skipped": [], "errors": []}

    pdfs = list(input_path.glob("*.pdf"))
    print(f"📂 Found {len(pdfs)} PDF files")

    for pdf in pdfs:
        print(f"\n{'='*50}")

        try:
            needs_ocr = analyze_pdf_needs_ocr(str(pdf))

            if needs_ocr:
                print(f"🔍 {pdf.name} - Needs OCR")

                # Extract text
                if text_folder:
                    txt_output = text_path / f"{pdf.stem}.txt"
                    ocr_pdf_to_text(str(pdf), str(txt_output))
                else:
                    # Create searchable PDF
                    pdf_output = output_path / f"{pdf.stem}_ocr.pdf"
                    ocr_pdf_to_searchable(str(pdf), str(pdf_output))

                results["processed"].append(str(pdf))
            else:
                print(f"✅ {pdf.name} - Already has text, skipping OCR")
                results["skipped"].append(str(pdf))

        except Exception as e:
            print(f"❌ Error processing {pdf.name}: {e}")
            results["errors"].append({"file": str(pdf), "error": str(e)})

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="OCR PDF Processing for OsMEN")
    parser.add_argument("input", help="Input PDF file or folder")
    parser.add_argument("output", nargs="?", help="Output file/folder (optional)")
    parser.add_argument(
        "--text-only",
        action="store_true",
        help="Only extract text, don't create searchable PDF",
    )
    parser.add_argument(
        "--dpi", type=int, default=200, help="Resolution for OCR (default: 200)"
    )
    parser.add_argument(
        "--batch", action="store_true", help="Process all PDFs in input folder"
    )

    args = parser.parse_args()

    input_path = Path(args.input)

    if args.batch or input_path.is_dir():
        # Batch mode
        output_folder = args.output or str(input_path / "ocr_output")
        text_folder = str(input_path.parent / "text") if args.text_only else None
        results = batch_ocr_folder(str(input_path), output_folder, text_folder)

        print(f"\n{'='*50}")
        print(f"📊 Results:")
        print(f"   Processed: {len(results['processed'])}")
        print(f"   Skipped: {len(results['skipped'])}")
        print(f"   Errors: {len(results['errors'])}")

    else:
        # Single file mode
        if args.text_only:
            output = args.output or str(input_path.with_suffix(".txt"))
            text = ocr_pdf_to_text(str(input_path), output, dpi=args.dpi)
            print(f"\n📄 Extracted {len(text)} characters")
        else:
            output = args.output or str(input_path.with_stem(f"{input_path.stem}_ocr"))
            ocr_pdf_to_searchable(str(input_path), output, dpi=args.dpi)
