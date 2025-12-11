#!/usr/bin/env python3
"""
COMPREHENSIVE Textbook Extractor - ALL Course Materials
Extracts text from ALL EPUB and PDF files for TTS processing
"""

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import ebooklib
import pdfplumber
from bs4 import BeautifulSoup
from ebooklib import epub


@dataclass
class Chapter:
    number: int
    title: str
    word_count: int
    estimated_minutes: float
    text_file: str


@dataclass
class TextbookExtraction:
    title: str
    author: str
    source_file: str
    format: str
    total_chapters: int
    total_words: int
    estimated_hours: float
    extraction_date: str
    chapters: List[Chapter]
    output_dir: str


def clean_text(text: str) -> str:
    """Clean extracted text for TTS."""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\b\d+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(
        r"^.*(?:Page|Copyright).*$", "", text, flags=re.MULTILINE | re.IGNORECASE
    )
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)
    return text.strip()


def extract_epub(file_path: Path) -> tuple:
    """Extract chapters from EPUB."""
    try:
        book = epub.read_epub(str(file_path))
    except Exception as e:
        print(f"      ⚠️ EPUB read error: {e}")
        return [], file_path.stem

    chapters = []
    chapter_num = 0

    title = book.get_metadata("DC", "title")
    title = title[0][0] if title else file_path.stem

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            try:
                content = item.get_content().decode("utf-8", errors="ignore")
                soup = BeautifulSoup(content, "html.parser")

                chapter_title = None
                for h in soup.find_all(["h1", "h2", "h3"]):
                    chapter_title = h.get_text().strip()
                    if chapter_title and len(chapter_title) > 3:
                        break

                text = soup.get_text(separator="\n", strip=True)
                text = clean_text(text)

                if len(text) > 300:
                    chapter_num += 1
                    chapters.append(
                        {
                            "number": chapter_num,
                            "title": chapter_title or f"Chapter {chapter_num}",
                            "text": text,
                        }
                    )
            except Exception as e:
                continue

    return chapters, title


def extract_pdf(file_path: Path, pages_per_section: int = 15) -> tuple:
    """Extract sections from PDF."""
    chapters = []
    section_num = 0
    current_pages = []

    try:
        with pdfplumber.open(str(file_path)) as pdf:
            total_pages = len(pdf.pages)

            for i, page in enumerate(pdf.pages):
                try:
                    text = page.extract_text() or ""
                    current_pages.append(text)
                except:
                    continue

                if (i + 1) % pages_per_section == 0 or i == total_pages - 1:
                    combined = "\n".join(current_pages)
                    combined = clean_text(combined)

                    if len(combined) > 300:
                        section_num += 1
                        start_page = max(1, i + 2 - pages_per_section)
                        chapters.append(
                            {
                                "number": section_num,
                                "title": f"Section {section_num} (Pages {start_page}-{i + 1})",
                                "text": combined,
                            }
                        )
                    current_pages = []
    except Exception as e:
        print(f"      ⚠️ PDF read error: {e}")
        return [], file_path.stem

    return chapters, file_path.stem


def process_textbook(
    file_path: Path, output_base: Path
) -> Optional[TextbookExtraction]:
    """Process a single textbook."""
    file_path = Path(file_path)
    if not file_path.exists():
        return None

    suffix = file_path.suffix.lower()
    if suffix == ".epub":
        chapters, title = extract_epub(file_path)
    elif suffix == ".pdf":
        chapters, title = extract_pdf(file_path)
    else:
        return None

    if not chapters:
        print(f"      ❌ No content extracted")
        return None

    safe_name = re.sub(r"[^\w\-]", "_", title)[:60]
    output_dir = output_base / safe_name
    output_dir.mkdir(parents=True, exist_ok=True)

    chapter_records = []
    total_words = 0

    for ch in chapters:
        text_file = output_dir / f"chapter_{ch['number']:03d}.txt"
        text_file.write_text(ch["text"], encoding="utf-8")

        word_count = len(ch["text"].split())
        total_words += word_count
        est_minutes = word_count / 150

        chapter_records.append(
            Chapter(
                number=ch["number"],
                title=ch["title"][:80],
                word_count=word_count,
                estimated_minutes=round(est_minutes, 1),
                text_file=text_file.name,
            )
        )

    extraction = TextbookExtraction(
        title=title,
        author="Unknown",
        source_file=str(file_path),
        format=suffix[1:].upper(),
        total_chapters=len(chapters),
        total_words=total_words,
        estimated_hours=round(total_words / 150 / 60, 1),
        extraction_date=datetime.now().isoformat(),
        chapters=chapter_records,
        output_dir=str(output_dir),
    )

    meta_file = output_dir / "metadata.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(asdict(extraction), f, indent=2, default=str)

    return extraction


def main():
    """Process ALL course textbooks."""

    # ALL source locations
    sources = [
        Path(r"D:\semester_start"),
        Path(r"D:\OsMEN\content\courses\M483INT_Pastoral_Ministry\raw"),
        Path(r"D:\OsMEN\content\courses\M483INT_Pastoral_Ministry\downloads"),
        Path(r"D:\OsMEN\content\courses\M483INT_Pastoral_Ministry\processed"),
    ]

    output_base = Path(r"D:\OsMEN\content\courses\HB411_HealthyBoundaries\readings\raw")

    print("=" * 70)
    print("📚 COMPREHENSIVE Textbook Extraction - ALL MATERIALS")
    print("=" * 70)

    # Collect all files
    all_files = []
    for source in sources:
        if source.exists():
            for ext in ["*.epub", "*.pdf"]:
                all_files.extend(source.glob(ext))

    # Remove duplicates by filename
    seen = set()
    unique_files = []
    for f in all_files:
        if f.name not in seen and f.stat().st_size > 50000:  # > 50KB
            seen.add(f.name)
            unique_files.append(f)

    print(f"\nFound {len(unique_files)} unique files to process\n")

    results = []
    failed = []

    for i, file_path in enumerate(sorted(unique_files), 1):
        print(f"[{i}/{len(unique_files)}] 📖 {file_path.name[:50]}...")

        try:
            extraction = process_textbook(file_path, output_base)
            if extraction:
                results.append(asdict(extraction))
                print(
                    f"      ✅ {extraction.total_chapters} chapters, {extraction.total_words:,} words"
                )
            else:
                failed.append(file_path.name)
        except Exception as e:
            print(f"      ❌ Error: {e}")
            failed.append(file_path.name)

    # Save master index
    index_file = output_base / "extraction_index.json"
    total_words = sum(r["total_words"] for r in results)
    total_hours = sum(r["estimated_hours"] for r in results)

    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "extraction_date": datetime.now().isoformat(),
                "total_books": len(results),
                "total_words": total_words,
                "total_hours": round(total_hours, 1),
                "failed_files": failed,
                "books": results,
            },
            f,
            indent=2,
            default=str,
        )

    print("\n" + "=" * 70)
    print("✅ EXTRACTION COMPLETE")
    print("=" * 70)
    print(f"\n📊 Summary:")
    print(f"   Processed: {len(results)} textbooks")
    print(f"   Failed: {len(failed)} files")
    print(f"   Total words: {total_words:,}")
    print(f"   Estimated audio: {total_hours:.1f} hours")
    print(f"\n   Index: {index_file}")

    if failed:
        print(f"\n⚠️ Failed files:")
        for f in failed:
            print(f"   - {f}")


if __name__ == "__main__":
    main()
