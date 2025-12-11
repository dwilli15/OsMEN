#!/usr/bin/env python3
"""
BATCH M4B Audiobook Generator
Generates 32kbps M4B audiobooks for ALL extracted textbooks using Kokoro TTS
GPU-accelerated with CUDA for RTX 5070
"""

import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import torch

# TTS
try:
    import soundfile as sf
    from kokoro import KPipeline

    HAS_TTS = True
except ImportError:
    HAS_TTS = False
    print("⚠️ kokoro/soundfile not installed")

# GPU Setup
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🔧 Using device: {DEVICE}")
if DEVICE == "cuda":
    print(f"   GPU: {torch.cuda.get_device_name(0)}")


class BatchAudiobookGenerator:
    """Generate M4B audiobooks from extracted text."""

    # Voice assignments for variety
    VOICE_ROTATION = [
        "af_heart",  # American Female - Heart (warm)
        "af_bella",  # American Female - Bella (professional)
        "am_adam",  # American Male - Adam (authoritative)
        "af_nicole",  # American Female - Nicole (calm)
        "bf_emma",  # British Female - Emma (refined)
        "am_michael",  # American Male - Michael (neutral)
        "af_sarah",  # American Female - Sarah (friendly)
        "bm_george",  # British Male - George (classic)
    ]

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.pipeline = None
        self.current_voice = None
        self.voice_index = 0

    def _load_pipeline(self, voice: str):
        """Load Kokoro pipeline for voice with GPU support."""
        if self.pipeline is None or self.current_voice != voice:
            print(f"   Loading TTS voice: {voice} on {DEVICE}")
            self.pipeline = KPipeline(lang_code="a", device=DEVICE)  # GPU-accelerated
            self.current_voice = voice

    def _synthesize_text(self, text: str, voice: str) -> np.ndarray:
        """Synthesize text to audio array using GPU."""
        self._load_pipeline(voice)

        audio_segments = []
        for _, _, audio in self.pipeline(text, voice=voice):
            audio_segments.append(audio)

        if audio_segments:
            return np.concatenate(audio_segments)
        return np.array([])

    def _create_m4b(self, wav_file: Path, output_file: Path, metadata: Dict) -> bool:
        """Convert WAV to M4B with metadata. Ultra-compressed for storage efficiency."""
        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(wav_file),
                "-c:a",
                "aac",
                "-b:a",
                "32k",  # Ultra-low bitrate for speech (was 64k)
                "-ac",
                "1",  # Mono
                "-ar",
                "16000",  # 16kHz sample rate - plenty for speech (was 22050)
                "-metadata",
                f"title={metadata.get('title', 'Audiobook')}",
                "-metadata",
                f"artist={metadata.get('author', 'Unknown')}",
                "-metadata",
                f"album={metadata.get('title', 'Audiobook')}",
                "-metadata",
                "genre=Audiobook",
                "-movflags",
                "+faststart",
                str(output_file),
            ]
            result = subprocess.run(
                cmd, capture_output=True, timeout=3600
            )  # 1 hour timeout for large files
            return output_file.exists()
        except Exception as e:
            print(f"      FFmpeg error: {e}")
            return False

    def generate_book(
        self,
        metadata_file: Path,
        voice: Optional[str] = None,
        max_words: int = None,  # No limit - process full books
    ) -> Optional[Path]:
        """Generate audiobook from extracted textbook."""

        if not metadata_file.exists():
            return None

        with open(metadata_file) as f:
            book_meta = json.load(f)

        title = book_meta.get("title", "Unknown")
        safe_title = title.replace(" ", "_").replace(",", "")[:40]
        output_file = self.output_dir / f"{safe_title}.m4b"

        if output_file.exists():
            print(f"   ⏭️ Already exists: {output_file.name}")
            return output_file

        print(f"\n📖 {title}")
        print(f"   Words: {book_meta.get('total_words', 0):,}")

        # Select voice
        if not voice:
            voice = self.VOICE_ROTATION[self.voice_index % len(self.VOICE_ROTATION)]
            self.voice_index += 1

        print(f"   Voice: {voice}")

        # Collect text from chapters
        book_dir = metadata_file.parent
        all_text = []
        total_words = 0

        for chapter in book_meta.get("chapters", []):
            chapter_file = book_dir / chapter["text_file"]
            if chapter_file.exists():
                text = chapter_file.read_text(encoding="utf-8")
                all_text.append(text)
                total_words += len(text.split())

                if max_words and total_words > max_words:
                    print(
                        f"   ⚠️ Truncating at {total_words:,} words (limit: {max_words:,})"
                    )
                    break

        if not all_text:
            print(f"   ❌ No text found")
            return None

        combined_text = "\n\n".join(all_text)
        print(f"   Synthesizing {len(combined_text):,} characters...")

        try:
            # Synthesize in chunks
            chunk_size = 5000
            audio_segments = []

            for i in range(0, len(combined_text), chunk_size):
                chunk = combined_text[i : i + chunk_size]
                if chunk.strip():
                    audio = self._synthesize_text(chunk, voice)
                    if len(audio) > 0:
                        audio_segments.append(audio)

                    # Progress
                    progress = min(100, (i + chunk_size) / len(combined_text) * 100)
                    print(f"   Progress: {progress:.0f}%", end="\r")

            print()  # New line after progress

            if not audio_segments:
                print(f"   ❌ No audio generated")
                return None

            # Combine audio
            full_audio = np.concatenate(audio_segments)
            duration_min = len(full_audio) / 24000 / 60
            print(f"   Duration: {duration_min:.1f} minutes")

            # Save to temp WAV
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = Path(tmp.name)
                sf.write(str(tmp_path), full_audio, 24000)

            # Convert to M4B
            print(f"   Creating M4B...")
            success = self._create_m4b(tmp_path, output_file, book_meta)

            # Cleanup
            tmp_path.unlink(missing_ok=True)

            if success:
                size_mb = output_file.stat().st_size / (1024 * 1024)
                print(f"   ✅ {output_file.name} ({size_mb:.1f} MB)")
                return output_file
            else:
                print(f"   ❌ M4B creation failed")
                return None

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None

    def generate_all(self, readings_dir: Path, max_books: int = None) -> List[Path]:
        """Generate audiobooks for all extracted textbooks."""

        readings_dir = Path(readings_dir)
        results = []

        # Find all metadata files
        metadata_files = list(readings_dir.glob("*/metadata.json"))

        if max_books:
            metadata_files = metadata_files[:max_books]

        print(f"\n{'='*60}")
        print(f"🎧 BATCH AUDIOBOOK GENERATION")
        print(f"{'='*60}")
        print(f"Books to process: {len(metadata_files)}")
        print(f"Output: {self.output_dir}")

        for i, meta_file in enumerate(metadata_files, 1):
            print(f"\n[{i}/{len(metadata_files)}]", end="")
            result = self.generate_book(meta_file)
            if result:
                results.append(result)

        # Summary
        print(f"\n{'='*60}")
        print(f"✅ GENERATION COMPLETE")
        print(f"{'='*60}")
        print(f"Generated: {len(results)}/{len(metadata_files)} audiobooks")

        if results:
            total_size = sum(f.stat().st_size for f in results) / (1024 * 1024)
            print(f"Total size: {total_size:.1f} MB")

            # Save manifest
            manifest = {
                "generated": datetime.now().isoformat(),
                "total_books": len(results),
                "total_size_mb": round(total_size, 1),
                "audiobooks": [
                    {
                        "file": str(f.name),
                        "size_mb": round(f.stat().st_size / 1024 / 1024, 1),
                    }
                    for f in results
                ],
            }
            manifest_file = self.output_dir / "audiobooks_manifest.json"
            with open(manifest_file, "w") as f:
                json.dump(manifest, f, indent=2)
            print(f"Manifest: {manifest_file}")

        return results


def main():
    """Generate all audiobooks."""

    if not HAS_TTS:
        print("❌ TTS not available. Install: pip install kokoro soundfile numpy")
        return

    readings_dir = Path(
        r"D:\OsMEN\content\courses\HB411_HealthyBoundaries\readings\raw"
    )
    output_dir = Path(r"D:\OsMEN\content\courses\HB411_HealthyBoundaries\audiobooks")

    generator = BatchAudiobookGenerator(output_dir)

    # Generate all (set max_books=5 for testing, None for all)
    results = generator.generate_all(readings_dir, max_books=None)

    print(f"\n🎧 Generated {len(results)} audiobooks")


if __name__ == "__main__":
    main()
