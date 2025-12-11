#!/usr/bin/env python3
"""
HB411 Course Audiobook Generator
Uses the AudiobookCreatorAgent with Kokoro TTS to generate M4B audiobooks

Generates audiobooks for all course textbooks at 64kbps
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add OsMEN to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.audiobook_creator.audiobook_creator_agent import (
    AVAILABLE_VOICES,
    AudiobookCreatorAgent,
)


def generate_hb411_audiobooks():
    """Generate audiobooks for all HB411 course textbooks."""

    course_dir = Path(r"D:\OsMEN\content\courses\HB411_HealthyBoundaries")
    output_dir = course_dir / "audiobooks"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Textbooks to convert
    textbooks = [
        {
            "title": "Set Boundaries Find Peace",
            "author": "Nedra Glover Tawwab",
            "file": Path(r"D:\semester_start\setboundariesfindpeace.epub"),
            "voice": "af_heart",  # American Female - Heart (warm)
        },
        {
            "title": "What It Takes to Heal",
            "author": "Prentis Hemphill",
            "file": Path(
                r"D:\semester_start\What It Takes to Heal - Prentis Hemphill.epub"
            ),
            "voice": "af_bella",  # American Female - Bella (professional)
        },
        {
            "title": "Sacred Wounds",
            "author": "Teresa Pasquale",
            "file": Path(r"D:\semester_start\Sacred Wounds - Teresa B. Pasquale.epub"),
            "voice": "af_nicole",  # American Female - Nicole (calm)
        },
        {
            "title": "The Anxious Generation",
            "author": "Jonathan Haidt",
            "file": Path(
                r"D:\semester_start\The Anxious Generation_ How the - Jonathan Haidt.epub"
            ),
            "voice": "am_adam",  # American Male - Adam (authoritative)
        },
    ]

    print("=" * 60)
    print("📚 HB411 Audiobook Generation")
    print("=" * 60)
    print(f"Output: {output_dir}")
    print(f"Format: M4B @ 64kbps")
    print(f"Books: {len(textbooks)}")

    # Initialize agent
    agent = AudiobookCreatorAgent(output_dir=str(output_dir))

    # Check dependencies
    deps = agent.dependencies
    print("\n📦 Dependencies:")
    for dep, available in deps.items():
        status = "✅" if available else "❌"
        print(f"   {status} {dep}")

    if not deps.get("kokoro"):
        print("\n⚠️ Kokoro TTS not available!")
        print("Install with: pip install kokoro-onnx")
        return []

    if not deps.get("ffmpeg"):
        print("\n⚠️ FFmpeg not found!")
        print("Install with: winget install --id=Gyan.FFmpeg")
        return []

    results = []

    for book in textbooks:
        if not book["file"].exists():
            print(f"\n⚠️ Not found: {book['title']}")
            continue

        print(f"\n{'='*60}")
        print(f"📖 Processing: {book['title']}")
        print(f"   Author: {book['author']}")
        print(f"   Voice: {AVAILABLE_VOICES.get(book['voice'], book['voice'])}")
        print("=" * 60)

        try:
            # Validate ebook
            validation = agent.validate_ebook(str(book["file"]))
            if not validation.get("valid"):
                print(f"   ❌ Validation failed: {validation.get('error')}")
                continue

            print(f"   Chapters: {validation.get('chapter_count', 'unknown')}")
            print(f"   Words: {validation.get('word_count', 'unknown'):,}")

            # Generate audiobook
            job = agent.create_audiobook(
                ebook_path=str(book["file"]),
                voice=book["voice"],
                output_format="m4b",
                output_path=str(output_dir / f"{book['title'].replace(' ', '_')}.m4b"),
            )

            if job.get("status") == "completed":
                output_file = Path(job.get("output_path", ""))
                if output_file.exists():
                    size_mb = output_file.stat().st_size / (1024 * 1024)
                    print(f"   ✅ Created: {output_file.name} ({size_mb:.1f} MB)")
                    results.append(
                        {
                            "title": book["title"],
                            "file": str(output_file),
                            "size_mb": size_mb,
                        }
                    )
            else:
                print(f"   ⚠️ Status: {job.get('status', 'unknown')}")
                if job.get("error"):
                    print(f"   Error: {job['error']}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("✅ Generation Complete!")
    print("=" * 60)
    print(f"Generated: {len(results)}/{len(textbooks)} audiobooks")

    if results:
        total_size = sum(r["size_mb"] for r in results)
        print(f"Total size: {total_size:.1f} MB")

        # Save manifest
        manifest = {
            "course": "HB411 Healthy Boundaries for Leaders",
            "generated": datetime.now().isoformat(),
            "audiobooks": results,
        }
        manifest_file = output_dir / "audiobooks_manifest.json"
        with open(manifest_file, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"Manifest: {manifest_file}")

    return results


def test_single_chapter():
    """Test with a single chapter first."""
    course_dir = Path(r"D:\OsMEN\content\courses\HB411_HealthyBoundaries")

    # Use extracted text
    text_dir = course_dir / "readings" / "raw" / "Set_Boundaries__Find_Peace"
    chapter_file = text_dir / "chapter_001.txt"

    if not chapter_file.exists():
        print(f"No test file found at {chapter_file}")
        return

    print("🧪 Testing single chapter synthesis...")
    print(f"   File: {chapter_file.name}")

    # Read text
    text = chapter_file.read_text(encoding="utf-8")
    print(f"   Words: {len(text.split()):,}")

    try:
        import numpy as np
        import soundfile as sf
        from kokoro import KPipeline

        print("   Loading Kokoro...")
        pipeline = KPipeline(lang_code="a")  # American English

        print("   Synthesizing...")
        # Only do first 500 chars for test
        test_text = text[:500]

        audio_segments = []
        for _, _, audio in pipeline(test_text, voice="af_heart"):
            audio_segments.append(audio)

        if audio_segments:
            full_audio = np.concatenate(audio_segments)

            output_file = course_dir / "audiobooks" / "test_chapter.wav"
            output_file.parent.mkdir(parents=True, exist_ok=True)

            sf.write(str(output_file), full_audio, 24000)
            print(f"   ✅ Test audio: {output_file}")
            print(f"   Duration: {len(full_audio)/24000:.1f} seconds")
        else:
            print("   ❌ No audio generated")

    except ImportError as e:
        print(f"   ❌ Missing dependency: {e}")
        print("   Install with: pip install kokoro soundfile numpy")
    except Exception as e:
        print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate HB411 audiobooks")
    parser.add_argument("--test", action="store_true", help="Test single chapter")
    parser.add_argument("--full", action="store_true", help="Generate all audiobooks")
    args = parser.parse_args()

    if args.test:
        test_single_chapter()
    elif args.full:
        generate_hb411_audiobooks()
    else:
        # Default: show available voices
        print("HB411 Audiobook Generator")
        print("\nAvailable voices:")
        for voice_id, name in list(AVAILABLE_VOICES.items())[:10]:
            print(f"  {voice_id}: {name}")
        print("  ...")
        print(f"\nTotal: {len(AVAILABLE_VOICES)} voices")
        print("\nUsage:")
        print("  --test  : Test single chapter synthesis")
        print("  --full  : Generate all audiobooks")
