#!/usr/bin/env python3
"""
Ingest all HB411 course text files into ChromaDB.

These text files are the source documents for the audiobooks.
Embedding them enables semantic search across all course content.
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from integrations.memory.hybrid_memory import HybridMemory, MemoryConfig, MemoryTier


def ingest_hb411_texts():
    """Ingest all HB411 text files into long-term memory."""

    readings_root = Path(
        "D:/OsMEN/content/courses/HB411_HealthyBoundaries/readings/raw"
    )

    if not readings_root.exists():
        print(f"ERROR: {readings_root} does not exist")
        return

    # Find all text files
    txt_files = list(readings_root.rglob("*.txt"))
    print(f"\n{'='*60}")
    print(f"  HB411 Text Content Ingestion")
    print(f"{'='*60}")
    print(f"  Source: {readings_root}")
    print(f"  Files found: {len(txt_files)}")
    print(f"{'='*60}\n")

    if not txt_files:
        print("No text files found!")
        return

    # Initialize memory
    memory = HybridMemory(MemoryConfig.from_env())

    success = 0
    failed = 0
    skipped = 0

    for i, txt_file in enumerate(txt_files, 1):
        try:
            # Get relative path for metadata
            rel_path = txt_file.relative_to(readings_root)
            book_name = txt_file.parent.name
            chapter = txt_file.stem

            # Read content
            content = txt_file.read_text(encoding="utf-8", errors="replace")

            # Skip empty files
            if len(content.strip()) < 50:
                skipped += 1
                continue

            # Truncate very long content for embedding
            if len(content) > 8000:
                content = content[:8000] + "..."

            # Store in memory with rich metadata
            memory.remember(
                content=content,
                source="hb411_reading",
                tier=MemoryTier.LONG_TERM,
                context={
                    "type": "course_reading",
                    "course": "HB411",
                    "book": book_name,
                    "chapter": chapter,
                    "file_path": str(txt_file),
                    "ingested_at": datetime.now().isoformat(),
                },
            )

            success += 1

            # Progress indicator
            if i % 50 == 0:
                print(
                    f"  Progress: {i}/{len(txt_files)} ({success} stored, {skipped} skipped)"
                )

        except Exception as e:
            failed += 1
            print(f"  ERROR [{txt_file.name}]: {e}")

    print(f"\n{'='*60}")
    print(f"  Ingestion Complete")
    print(f"{'='*60}")
    print(f"  Total files: {len(txt_files)}")
    print(f"  Stored: {success}")
    print(f"  Skipped (empty): {skipped}")
    print(f"  Failed: {failed}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    ingest_hb411_texts()
