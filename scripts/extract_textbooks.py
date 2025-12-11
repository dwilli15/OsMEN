#!/usr/bin/env python3
"""
Course Textbook Extractor and Preparation
Extracts text from all course textbooks for TTS processing

Outputs:
- Extracted text files per chapter
- Metadata JSON for audiobook generation
- Ready for Kokoro TTS pipeline
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
    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)
    # Remove page numbers
    text = re.sub(r"\b\d+\s*$", "", text, flags=re.MULTILINE)
    # Remove headers/footers patterns
    text = re.sub(
        r"^.*(?:Chapter|Page|Copyright).*$",
        "",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    # Clean up punctuation
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)
    return text.strip()


def extract_epub(file_path: Path) -> List[Dict]:
    """Extract chapters from EPUB."""
    book = epub.read_epub(str(file_path))
    chapters = []
    chapter_num = 0

    # Get book title
    title = book.get_metadata("DC", "title")
    title = title[0][0] if title else file_path.stem

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            content = item.get_content().decode("utf-8", errors="ignore")
            soup = BeautifulSoup(content, "html.parser")

            # Find chapter title
            chapter_title = None
            for h in soup.find_all(["h1", "h2", "h3"]):
                chapter_title = h.get_text().strip()
                if chapter_title and len(chapter_title) > 3:
                    break

            # Get text
            text = soup.get_text(separator="\n", strip=True)
            text = clean_text(text)

            if len(text) > 500:
                chapter_num += 1
                chapters.append(
                    {
                        "number": chapter_num,
                        "title": chapter_title or f"Chapter {chapter_num}",
                        "text": text,
                    }
                )

    return chapters, title


def extract_pdf(file_path: Path, pages_per_section: int = 15) -> List[Dict]:
    """Extract sections from PDF."""
    chapters = []
    section_num = 0
    current_pages = []

    with pdfplumber.open(str(file_path)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            current_pages.append(text)

            if (i + 1) % pages_per_section == 0 or i == len(pdf.pages) - 1:
                combined = "\n".join(current_pages)
                combined = clean_text(combined)

                if len(combined) > 500:
                    section_num += 1
                    chapters.append(
                        {
                            "number": section_num,
                            "title": f"Section {section_num} (Pages {i + 2 - pages_per_section}-{i + 1})",
                            "text": combined,
                        }
                    )
                current_pages = []

    return chapters, file_path.stem


def process_textbook(
    file_path: Path, output_base: Path, author: str = "Unknown"
) -> Optional[TextbookExtraction]:
    """Process a single textbook and extract all text."""

    file_path = Path(file_path)
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return None

    print(f"\n📖 Processing: {file_path.name}")

    # Extract based on format
    suffix = file_path.suffix.lower()
    if suffix == ".epub":
        chapters, title = extract_epub(file_path)
    elif suffix == ".pdf":
        chapters, title = extract_pdf(file_path)
    else:
        print(f"❌ Unsupported format: {suffix}")
        return None

    if not chapters:
        print(f"❌ No content extracted")
        return None

    # Create output directory
    safe_name = re.sub(r"[^\w\-]", "_", title)[:50]
    output_dir = output_base / safe_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save chapters
    chapter_records = []
    total_words = 0

    for ch in chapters:
        # Save text file
        text_file = output_dir / f"chapter_{ch['number']:03d}.txt"
        text_file.write_text(ch["text"], encoding="utf-8")

        word_count = len(ch["text"].split())
        total_words += word_count

        # Estimate ~150 words per minute for audiobook
        est_minutes = word_count / 150

        chapter_records.append(
            Chapter(
                number=ch["number"],
                title=ch["title"],
                word_count=word_count,
                estimated_minutes=round(est_minutes, 1),
                text_file=text_file.name,
            )
        )

        print(
            f"   ✅ {ch['title'][:40]} ({word_count:,} words, ~{est_minutes:.0f} min)"
        )

    # Create extraction record
    extraction = TextbookExtraction(
        title=title,
        author=author,
        source_file=str(file_path),
        format=suffix[1:].upper(),
        total_chapters=len(chapters),
        total_words=total_words,
        estimated_hours=round(total_words / 150 / 60, 1),
        extraction_date=datetime.now().isoformat(),
        chapters=chapter_records,
        output_dir=str(output_dir),
    )

    # Save metadata
    meta_file = output_dir / "metadata.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(asdict(extraction), f, indent=2, default=str)

    print(f"\n   📊 Total: {total_words:,} words, ~{extraction.estimated_hours} hours")
    print(f"   💾 Saved to: {output_dir}")

    return extraction


def main():
    """Process all HB411 course textbooks."""

    # Course textbooks with file paths
    textbooks = [
        {
            "title": "Set Boundaries Find Peace",
            "author": "Nedra Glover Tawwab",
            "paths": [
                Path(r"D:\semester_start\setboundariesfindpeace.epub"),
                Path(
                    r"D:\semester_start\Set Boundaries, Find Peace - Nedra Glover Tawwab.pdf"
                ),
            ],
        },
        {
            "title": "What It Takes to Heal",
            "author": "Prentis Hemphill",
            "paths": [
                Path(
                    r"D:\semester_start\What It Takes to Heal - Prentis Hemphill.epub"
                ),
                Path(
                    r"D:\semester_start\Prentis Hemphill - What It Takes to Heal.epub"
                ),
            ],
        },
        {
            "title": "Sacred Wounds",
            "author": "Teresa Pasquale",
            "paths": [
                Path(r"D:\semester_start\Sacred Wounds - Teresa B. Pasquale.epub"),
            ],
        },
        {
            "title": "Saying No to Say Yes",
            "author": "David C. Olsen & Nancy G. Devor",
            "paths": [
                Path(r"D:\semester_start\saynotosayyes.epub"),
                Path(r"D:\semester_start\Saying No to Say Yes - David C. Olsen.pdf"),
            ],
        },
        {
            "title": "The Anxious Generation",
            "author": "Jonathan Haidt",
            "paths": [
                Path(
                    r"D:\semester_start\The Anxious Generation_ How the - Jonathan Haidt.epub"
                ),
            ],
        },
        {
            "title": "Healthy Boundaries 201",
            "author": "Marie Fortune",
            "paths": [
                Path(
                    r"D:\semester_start\FaithTrust-HealthyBoundaries201-English-2012.pdf"
                ),
            ],
        },
        {
            "title": "Responding to Spiritual Leader Misconduct",
            "author": "Lauren D. Sawyer et al.",
            "paths": [
                Path(
                    r"D:\semester_start\Responding to Spiritual Leader Misconduct Handbook_FINAL_Digital_9_29_22.pdf"
                ),
            ],
        },
    ]

    output_base = Path(r"D:\OsMEN\content\courses\HB411_HealthyBoundaries\readings\raw")

    print("=" * 60)
    print("📚 HB411 Textbook Extraction")
    print("=" * 60)

    results = []

    for book in textbooks:
        # Find first existing file
        file_path = None
        for p in book["paths"]:
            if p.exists():
                file_path = p
                break

        if not file_path:
            print(f"\n⚠️ Not found: {book['title']}")
            continue

        extraction = process_textbook(file_path, output_base, book["author"])
        if extraction:
            results.append(asdict(extraction))

    # Save master index
    index_file = output_base / "extraction_index.json"
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "course": "HB411 Healthy Boundaries for Leaders",
                "extraction_date": datetime.now().isoformat(),
                "total_books": len(results),
                "total_words": sum(r["total_words"] for r in results),
                "total_hours": round(sum(r["estimated_hours"] for r in results), 1),
                "books": results,
            },
            f,
            indent=2,
            default=str,
        )

    print("\n" + "=" * 60)
    print("✅ Extraction Complete!")
    print("=" * 60)
    print(f"\nProcessed: {len(results)} textbooks")
    print(f"Total words: {sum(r['total_words'] for r in results):,}")
    print(f"Estimated audio: {sum(r['estimated_hours'] for r in results):.1f} hours")
    print(f"\nIndex saved: {index_file}")


if __name__ == "__main__":
    main()
