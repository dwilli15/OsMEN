#!/usr/bin/env python3
"""
M4B Audiobook Generator for Course Textbooks
Converts EPUB/PDF to 64kbps M4B audiobooks using Kokoro TTS

Features:
- Extracts text from EPUB/PDF
- Splits into chapters
- Generates speech with Kokoro TTS (54 voices)
- Combines into M4B with chapter markers
- Targets 64kbps AAC for small file size
"""

import hashlib
import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Text extraction
try:
    import ebooklib
    from bs4 import BeautifulSoup
    from ebooklib import epub

    HAS_EPUB = True
except ImportError:
    HAS_EPUB = False
    print("⚠️ ebooklib not installed - EPUB support disabled")

try:
    import pdfplumber

    HAS_PDF = True
except ImportError:
    HAS_PDF = False
    print("⚠️ pdfplumber not installed - PDF support disabled")

# TTS
try:
    import soundfile as sf
    import torch

    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("⚠️ torch/soundfile not installed - TTS disabled")


@dataclass
class Chapter:
    """Represents a book chapter."""

    number: int
    title: str
    text: str
    audio_path: Optional[Path] = None


@dataclass
class AudiobookConfig:
    """Configuration for audiobook generation."""

    voice: str = "af_heart"  # Default Kokoro voice
    speed: float = 1.0
    bitrate: str = "64k"
    sample_rate: int = 24000
    output_format: str = "m4b"


class TextExtractor:
    """Extract text from EPUB and PDF files."""

    @staticmethod
    def extract_epub(file_path: Path) -> List[Chapter]:
        """Extract chapters from EPUB file."""
        if not HAS_EPUB:
            raise ImportError("ebooklib required for EPUB extraction")

        book = epub.read_epub(str(file_path))
        chapters = []
        chapter_num = 0

        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                content = item.get_content().decode("utf-8", errors="ignore")
                soup = BeautifulSoup(content, "html.parser")

                # Try to find chapter title
                title = None
                for heading in soup.find_all(["h1", "h2", "h3"]):
                    title = heading.get_text().strip()
                    break

                # Extract text
                text = soup.get_text(separator=" ", strip=True)
                text = re.sub(r"\s+", " ", text)

                if len(text) > 500:  # Minimum chapter length
                    chapter_num += 1
                    chapters.append(
                        Chapter(
                            number=chapter_num,
                            title=title or f"Chapter {chapter_num}",
                            text=text,
                        )
                    )

        return chapters

    @staticmethod
    def extract_pdf(file_path: Path, pages_per_chapter: int = 20) -> List[Chapter]:
        """Extract chapters from PDF file."""
        if not HAS_PDF:
            raise ImportError("pdfplumber required for PDF extraction")

        chapters = []
        current_text = []
        chapter_num = 0

        with pdfplumber.open(str(file_path)) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                current_text.append(text)

                # Create chapter every N pages
                if (i + 1) % pages_per_chapter == 0 or i == len(pdf.pages) - 1:
                    combined = " ".join(current_text)
                    combined = re.sub(r"\s+", " ", combined)

                    if len(combined) > 500:
                        chapter_num += 1
                        chapters.append(
                            Chapter(
                                number=chapter_num,
                                title=f"Section {chapter_num}",
                                text=combined,
                            )
                        )
                    current_text = []

        return chapters

    @staticmethod
    def extract(file_path: Path) -> List[Chapter]:
        """Auto-detect format and extract."""
        suffix = file_path.suffix.lower()
        if suffix == ".epub":
            return TextExtractor.extract_epub(file_path)
        elif suffix == ".pdf":
            return TextExtractor.extract_pdf(file_path)
        else:
            raise ValueError(f"Unsupported format: {suffix}")


class KokoroTTS:
    """Kokoro Text-to-Speech wrapper."""

    # Voice map (subset of 54 voices)
    VOICES = {
        "af_heart": "American Female - Heart (warm)",
        "af_bella": "American Female - Bella (professional)",
        "af_nicole": "American Female - Nicole (calm)",
        "af_sarah": "American Female - Sarah (friendly)",
        "am_adam": "American Male - Adam (authoritative)",
        "am_michael": "American Male - Michael (neutral)",
        "bf_emma": "British Female - Emma (refined)",
        "bm_george": "British Male - George (classic)",
    }

    def __init__(self, voice: str = "af_heart", device: str = None):
        self.voice = voice
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self._loaded = False

    def _load_model(self):
        """Lazy load the Kokoro model."""
        if self._loaded:
            return

        try:
            from kokoro import KPipeline

            self.model = KPipeline(lang_code="a")
            self._loaded = True
            print(f"✅ Kokoro TTS loaded on {self.device}")
        except Exception as e:
            print(f"⚠️ Kokoro load failed: {e}")
            self.model = None

    def synthesize(self, text: str, output_path: Path) -> bool:
        """Synthesize text to audio file."""
        self._load_model()

        if not self.model:
            print("❌ TTS model not available")
            return False

        try:
            # Split long text into chunks (Kokoro has limits)
            chunks = self._split_text(text, max_chars=1000)
            audio_segments = []

            for i, chunk in enumerate(chunks):
                generator = self.model(chunk, voice=self.voice)
                for _, _, audio in generator:
                    audio_segments.append(audio)

            # Concatenate
            import numpy as np

            full_audio = (
                np.concatenate(audio_segments) if audio_segments else np.array([])
            )

            # Save
            sf.write(str(output_path), full_audio, 24000)
            return True

        except Exception as e:
            print(f"❌ TTS synthesis failed: {e}")
            return False

    def _split_text(self, text: str, max_chars: int = 1000) -> List[str]:
        """Split text into speakable chunks."""
        # Split on sentence boundaries
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks = []
        current_chunk = []
        current_len = 0

        for sentence in sentences:
            if current_len + len(sentence) > max_chars and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_len = 0
            current_chunk.append(sentence)
            current_len += len(sentence)

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks


class AudiobookGenerator:
    """Generate M4B audiobooks from text."""

    def __init__(self, config: AudiobookConfig = None):
        self.config = config or AudiobookConfig()
        self.tts = KokoroTTS(voice=self.config.voice) if HAS_TORCH else None

    def generate(
        self, input_file: Path, output_dir: Path, metadata: Dict = None
    ) -> Optional[Path]:
        """Generate M4B audiobook from input file."""

        input_file = Path(input_file)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate output filename
        stem = input_file.stem.replace(" ", "_")[:50]
        output_file = output_dir / f"{stem}.m4b"

        print(f"\n{'='*60}")
        print(f"📚 Generating Audiobook: {input_file.name}")
        print(f"{'='*60}")

        # Extract chapters
        print("\n📖 Extracting text...")
        try:
            chapters = TextExtractor.extract(input_file)
            print(f"   Found {len(chapters)} chapters")
        except Exception as e:
            print(f"❌ Text extraction failed: {e}")
            return None

        if not chapters:
            print("❌ No chapters extracted")
            return None

        # Create temp directory for chapter audio
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            chapter_files = []

            # Generate audio for each chapter
            print(f"\n🎤 Synthesizing with voice: {self.config.voice}")
            for chapter in chapters:
                print(f"   Chapter {chapter.number}: {chapter.title[:40]}...", end=" ")

                audio_path = temp_path / f"chapter_{chapter.number:03d}.wav"

                if self.tts and self.tts.synthesize(chapter.text[:10000], audio_path):
                    chapter.audio_path = audio_path
                    chapter_files.append(audio_path)
                    print("✅")
                else:
                    print("⚠️ skipped")

            if not chapter_files:
                print("❌ No audio generated")
                return None

            # Combine into M4B
            print(f"\n📀 Creating M4B ({self.config.bitrate})...")
            success = self._create_m4b(
                chapter_files,
                chapters,
                output_file,
                metadata or {"title": input_file.stem},
            )

            if success:
                size_mb = output_file.stat().st_size / (1024 * 1024)
                print(f"✅ Created: {output_file.name} ({size_mb:.1f} MB)")
                return output_file
            else:
                print("❌ M4B creation failed")
                return None

    def _create_m4b(
        self,
        chapter_files: List[Path],
        chapters: List[Chapter],
        output_path: Path,
        metadata: Dict,
    ) -> bool:
        """Combine chapter audio into M4B with metadata."""

        try:
            # First, create a file list for concatenation
            temp_dir = chapter_files[0].parent
            concat_list = temp_dir / "concat.txt"

            with open(concat_list, "w") as f:
                for audio_file in chapter_files:
                    f.write(f"file '{audio_file}'\n")

            # Create chapter metadata file
            chapter_meta = temp_dir / "chapters.txt"
            with open(chapter_meta, "w") as f:
                f.write(";FFMETADATA1\n")
                f.write(f"title={metadata.get('title', 'Audiobook')}\n")
                f.write(f"artist={metadata.get('author', 'Unknown')}\n")
                f.write(f"album={metadata.get('title', 'Audiobook')}\n")
                f.write(f"genre=Audiobook\n")

                # Chapter markers (simplified - would need actual timestamps)
                timestamp = 0
                for chapter in chapters:
                    f.write(f"\n[CHAPTER]\n")
                    f.write(f"TIMEBASE=1/1000\n")
                    f.write(f"START={timestamp * 1000}\n")
                    timestamp += 300  # Estimate 5 min per chapter
                    f.write(f"END={timestamp * 1000}\n")
                    f.write(f"title={chapter.title}\n")

            # Combine with FFmpeg
            temp_combined = temp_dir / "combined.wav"

            # Concatenate WAV files
            cmd_concat = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-c",
                "copy",
                str(temp_combined),
            ]
            subprocess.run(cmd_concat, capture_output=True, check=True)

            # Convert to M4B (AAC in M4A container)
            cmd_m4b = [
                "ffmpeg",
                "-y",
                "-i",
                str(temp_combined),
                "-i",
                str(chapter_meta),
                "-map",
                "0:a",
                "-map_metadata",
                "1",
                "-c:a",
                "aac",
                "-b:a",
                self.config.bitrate,
                "-ac",
                "1",  # Mono for smaller size
                "-ar",
                "22050",  # Lower sample rate for speech
                "-movflags",
                "+faststart",
                str(output_path),
            ]
            subprocess.run(cmd_m4b, capture_output=True, check=True)

            return output_path.exists()

        except subprocess.CalledProcessError as e:
            print(f"FFmpeg error: {e}")
            return False
        except Exception as e:
            print(f"Error creating M4B: {e}")
            return False


def generate_course_audiobooks(course_dir: Path, textbooks: List[Dict]) -> List[Path]:
    """Generate audiobooks for all course textbooks."""

    audiobook_dir = course_dir / "audiobooks"
    audiobook_dir.mkdir(parents=True, exist_ok=True)

    generator = AudiobookGenerator(AudiobookConfig(voice="af_heart", bitrate="64k"))

    generated = []

    for book in textbooks:
        file_path = book.get("path")
        if not file_path or not Path(file_path).exists():
            print(f"⚠️ File not found: {book.get('title', 'Unknown')}")
            continue

        output = generator.generate(
            Path(file_path),
            audiobook_dir,
            metadata={
                "title": book.get("title", "Unknown"),
                "author": book.get("author", "Unknown"),
            },
        )

        if output:
            generated.append(output)

    return generated


def main():
    """Test audiobook generation."""

    # Find a test file
    test_files = [
        Path(r"D:\semester_start\setboundariesfindpeace.epub"),
        Path(r"D:\semester_start\Set Boundaries, Find Peace - Nedra Glover Tawwab.pdf"),
    ]

    for test_file in test_files:
        if test_file.exists():
            output_dir = Path(
                r"D:\OsMEN\content\courses\HB411_HealthyBoundaries\audiobooks"
            )
            generator = AudiobookGenerator()
            result = generator.generate(test_file, output_dir)
            if result:
                print(f"\n✅ Test successful: {result}")
            break
    else:
        print("No test files found")


if __name__ == "__main__":
    main()
