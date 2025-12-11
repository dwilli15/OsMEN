#!/usr/bin/env python3
"""
Audiobook Creator Agent
Converts ebooks to audiobooks using Audiblez (Kokoro TTS) with voice selection and chapter splitting.

Dependencies:
- audiblez: EPUB to audiobook conversion with Kokoro TTS
- ebooklib: EPUB parsing
- soundfile: Audio file handling
- spacy: NLP for sentence tokenization
- kokoro: High-quality TTS engine
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Available voices in Kokoro/Audiblez (first letter = language code)
AVAILABLE_VOICES = {
    # American English
    "af_alloy": "American Female - Alloy",
    "af_aoede": "American Female - Aoede",
    "af_bella": "American Female - Bella",
    "af_heart": "American Female - Heart",
    "af_jessica": "American Female - Jessica",
    "af_kore": "American Female - Kore",
    "af_nicole": "American Female - Nicole",
    "af_nova": "American Female - Nova",
    "af_river": "American Female - River",
    "af_sarah": "American Female - Sarah",
    "af_sky": "American Female - Sky (Default)",
    "am_adam": "American Male - Adam",
    "am_echo": "American Male - Echo",
    "am_eric": "American Male - Eric",
    "am_fenrir": "American Male - Fenrir",
    "am_liam": "American Male - Liam",
    "am_michael": "American Male - Michael",
    "am_onyx": "American Male - Onyx",
    # British English
    "bf_alice": "British Female - Alice",
    "bf_emma": "British Female - Emma",
    "bf_isabella": "British Female - Isabella",
    "bf_lily": "British Female - Lily",
    "bm_daniel": "British Male - Daniel",
    "bm_fable": "British Male - Fable",
    "bm_george": "British Male - George",
    "bm_lewis": "British Male - Lewis",
    # Japanese
    "jf_alpha": "Japanese Female - Alpha",
    "jf_gongitsune": "Japanese Female - Gongitsune",
    "jf_nezumi": "Japanese Female - Nezumi",
    "jf_tebukuro": "Japanese Female - Tebukuro",
    "jm_kumo": "Japanese Male - Kumo",
    # Chinese
    "zf_xiaobei": "Chinese Female - Xiaobei",
    "zf_xiaoni": "Chinese Female - Xiaoni",
    "zf_xiaoxiao": "Chinese Female - Xiaoxiao",
    "zf_xiaoyi": "Chinese Female - Xiaoyi",
    "zm_yunjian": "Chinese Male - Yunjian",
    "zm_yunxi": "Chinese Male - Yunxi",
    "zm_yunxia": "Chinese Male - Yunxia",
    "zm_yunyang": "Chinese Male - Yunyang",
    # Korean
    "kf_sarah": "Korean Female - Sarah",
    "km_kevin": "Korean Male - Kevin",
    # French
    "ff_siwis": "French Female - Siwis",
    # Hindi
    "hf_alpha": "Hindi Female - Alpha",
    "hf_beta": "Hindi Female - Beta",
    "hm_omega": "Hindi Male - Omega",
    "hm_psi": "Hindi Male - Psi",
    # Italian
    "if_sara": "Italian Female - Sara",
    "im_nicola": "Italian Male - Nicola",
    # Portuguese (Brazilian)
    "pf_dora": "Portuguese Female - Dora",
    "pm_alex": "Portuguese Male - Alex",
    "pm_santa": "Portuguese Male - Santa",
    # Spanish
    "ef_dora": "Spanish Female - Dora",
    "em_alex": "Spanish Male - Alex",
    "em_santa": "Spanish Male - Santa",
}

DEFAULT_VOICE = "af_heart"  # American Female - Heart (user preferred)
SUPPORTED_FORMATS = ["epub", "pdf", "txt", "html"]
OUTPUT_FORMATS = ["m4b", "mp3", "wav"]


class AudiobookCreatorAgent:
    """Audiobook Creator Agent for ebook to audiobook conversion using Audiblez/Kokoro TTS."""

    def __init__(self, output_dir: Optional[str] = None):
        """Initialize the Audiobook Creator Agent.

        Args:
            output_dir: Default output directory for audiobooks
        """
        self.output_dir = Path(output_dir) if output_dir else Path.home() / "Audiobooks"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.conversion_jobs: List[Dict] = []
        self._check_dependencies()

        logger.info(f"AudiobookCreatorAgent initialized. Output: {self.output_dir}")

    def _check_dependencies(self) -> Dict[str, bool]:
        """Check if required dependencies are available."""
        deps = {
            "audiblez": False,
            "ebooklib": False,
            "soundfile": False,
            "kokoro": False,
            "spacy": False,
            "ffmpeg": False,
        }

        try:
            import audiblez

            deps["audiblez"] = True
        except ImportError:
            logger.warning("audiblez not installed. Run: pip install audiblez")

        try:
            import ebooklib

            deps["ebooklib"] = True
        except ImportError:
            logger.warning("ebooklib not installed. Run: pip install ebooklib")

        try:
            import soundfile

            deps["soundfile"] = True
        except ImportError:
            logger.warning("soundfile not installed. Run: pip install soundfile")

        try:
            # Try kokoro-onnx first (lighter weight, ONNX runtime)
            from kokoro_onnx import Kokoro

            deps["kokoro"] = True
        except ImportError:
            try:
                # Fall back to full kokoro (requires torch)
                from kokoro import KPipeline

                deps["kokoro"] = True
            except ImportError:
                logger.warning("kokoro not installed. Run: pip install kokoro-onnx")

        try:
            import spacy

            deps["spacy"] = True
        except ImportError:
            logger.warning("spacy not installed. Run: pip install spacy")

        # Check FFmpeg
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], capture_output=True, text=True, timeout=5
            )
            deps["ffmpeg"] = result.returncode == 0
        except Exception:
            logger.warning(
                "FFmpeg not found. Install via: winget install --id=Gyan.FFmpeg"
            )

        self.dependencies = deps
        return deps

    def get_available_voices(self, language: Optional[str] = None) -> Dict[str, str]:
        """Get available voices, optionally filtered by language.

        Args:
            language: Language code prefix (a=American, b=British, j=Japanese, etc.)

        Returns:
            Dictionary of voice_id -> voice_description
        """
        if language:
            return {k: v for k, v in AVAILABLE_VOICES.items() if k.startswith(language)}
        return AVAILABLE_VOICES.copy()

    def validate_ebook(self, ebook_path: str) -> Dict:
        """Validate an ebook file before conversion.

        Args:
            ebook_path: Path to ebook file

        Returns:
            Validation result with file info
        """
        path = Path(ebook_path)

        if not path.exists():
            return {"valid": False, "error": f"File not found: {ebook_path}"}

        suffix = path.suffix.lower().lstrip(".")
        if suffix not in SUPPORTED_FORMATS:
            return {
                "valid": False,
                "error": f"Unsupported format: {suffix}. Supported: {SUPPORTED_FORMATS}",
            }

        file_size = path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)

        result = {
            "valid": True,
            "path": str(path.absolute()),
            "filename": path.name,
            "format": suffix,
            "size_bytes": file_size,
            "size_mb": round(file_size_mb, 2),
        }

        # Get additional info for EPUB files
        if suffix == "epub" and self.dependencies.get("ebooklib"):
            try:
                from ebooklib import epub

                book = epub.read_epub(str(path))
                result["title"] = (
                    book.get_metadata("DC", "title")[0][0]
                    if book.get_metadata("DC", "title")
                    else None
                )
                result["author"] = (
                    book.get_metadata("DC", "creator")[0][0]
                    if book.get_metadata("DC", "creator")
                    else None
                )
                result["chapters"] = len(
                    [item for item in book.get_items() if item.get_type() == 9]
                )  # ITEM_DOCUMENT
            except Exception as e:
                logger.warning(f"Could not read EPUB metadata: {e}")

        return result

    def convert_ebook(
        self,
        ebook_path: str,
        voice: str = DEFAULT_VOICE,
        speed: float = 1.0,
        output_format: str = "m4b",
        output_folder: Optional[str] = None,
        use_cuda: bool = False,
        pick_chapters: bool = False,
    ) -> Dict:
        """Convert an ebook to audiobook using Audiblez.

        Args:
            ebook_path: Path to ebook file (EPUB, PDF, TXT)
            voice: Voice ID from available voices (default: af_sky)
            speed: Narration speed 0.5-2.0 (default: 1.0)
            output_format: Output format (m4b, mp3, wav)
            output_folder: Output folder (default: self.output_dir)
            use_cuda: Use GPU acceleration if available
            pick_chapters: Interactively pick chapters (CLI only)

        Returns:
            Dictionary with job details and status
        """
        # Validate input
        validation = self.validate_ebook(ebook_path)
        if not validation["valid"]:
            return {"status": "error", "error": validation["error"]}

        if voice not in AVAILABLE_VOICES:
            return {
                "status": "error",
                "error": f"Invalid voice: {voice}. Use get_available_voices() to see options.",
            }

        if not 0.5 <= speed <= 2.0:
            return {"status": "error", "error": "Speed must be between 0.5 and 2.0"}

        if output_format not in OUTPUT_FORMATS:
            return {
                "status": "error",
                "error": f"Invalid format: {output_format}. Supported: {OUTPUT_FORMATS}",
            }

        # Check dependencies
        if not self.dependencies.get("audiblez"):
            return {
                "status": "error",
                "error": "audiblez not installed. Run: pip install audiblez",
            }

        # Create job record
        output_dir = Path(output_folder) if output_folder else self.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        job = {
            "id": len(self.conversion_jobs) + 1,
            "ebook_path": str(Path(ebook_path).absolute()),
            "ebook_info": validation,
            "voice": voice,
            "voice_name": AVAILABLE_VOICES[voice],
            "speed": speed,
            "output_format": output_format,
            "output_folder": str(output_dir),
            "use_cuda": use_cuda,
            "status": "queued",
            "progress": 0,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "output_file": None,
            "error": None,
        }
        self.conversion_jobs.append(job)

        logger.info(
            f"Job {job['id']}: Converting {validation['filename']} with voice {voice}"
        )

        # Run conversion via CLI (subprocess for isolation)
        try:
            job["status"] = "processing"

            cmd = [
                sys.executable,
                "-m",
                "audiblez",
                job["ebook_path"],
                "-v",
                voice,
                "-s",
                str(speed),
                "-o",
                str(output_dir),
            ]

            if use_cuda:
                cmd.append("-c")

            logger.info(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600 * 4,  # 4 hour timeout for long books
                cwd=str(output_dir),
            )

            if result.returncode == 0:
                job["status"] = "completed"
                job["progress"] = 100
                job["completed_at"] = datetime.now().isoformat()

                # Find output file
                ebook_stem = Path(ebook_path).stem
                for ext in [".m4b", ".mp3", ".wav"]:
                    potential_output = output_dir / f"{ebook_stem}{ext}"
                    if potential_output.exists():
                        job["output_file"] = str(potential_output)
                        break

                logger.info(
                    f"Job {job['id']}: Completed - {job.get('output_file', 'output file not found')}"
                )
            else:
                job["status"] = "failed"
                job["error"] = result.stderr or result.stdout or "Unknown error"
                logger.error(f"Job {job['id']}: Failed - {job['error']}")

        except subprocess.TimeoutExpired:
            job["status"] = "failed"
            job["error"] = "Conversion timed out (>4 hours)"
            logger.error(f"Job {job['id']}: Timeout")
        except Exception as e:
            job["status"] = "failed"
            job["error"] = str(e)
            logger.error(f"Job {job['id']}: Exception - {e}")

        return job

    async def convert_ebook_async(
        self,
        ebook_path: str,
        voice: str = DEFAULT_VOICE,
        speed: float = 1.0,
        output_format: str = "m4b",
        output_folder: Optional[str] = None,
        use_cuda: bool = False,
        progress_callback: Optional[callable] = None,
    ) -> Dict:
        """Async version of convert_ebook with progress callbacks.

        Args:
            ebook_path: Path to ebook file
            voice: Voice ID
            speed: Narration speed
            output_format: Output format
            output_folder: Output folder
            use_cuda: Use CUDA
            progress_callback: Async callback(progress: int, message: str)

        Returns:
            Job result dictionary
        """
        # Validate
        validation = self.validate_ebook(ebook_path)
        if not validation["valid"]:
            return {"status": "error", "error": validation["error"]}

        output_dir = Path(output_folder) if output_folder else self.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        job = {
            "id": len(self.conversion_jobs) + 1,
            "ebook_path": str(Path(ebook_path).absolute()),
            "voice": voice,
            "speed": speed,
            "status": "processing",
            "started_at": datetime.now().isoformat(),
        }
        self.conversion_jobs.append(job)

        if progress_callback:
            await progress_callback(0, "Starting conversion...")

        cmd = [
            sys.executable,
            "-m",
            "audiblez",
            job["ebook_path"],
            "-v",
            voice,
            "-s",
            str(speed),
            "-o",
            str(output_dir),
        ]
        if use_cuda:
            cmd.append("-c")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(output_dir),
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            job["status"] = "completed"
            job["completed_at"] = datetime.now().isoformat()

            ebook_stem = Path(ebook_path).stem
            for ext in [".m4b", ".mp3", ".wav"]:
                potential = output_dir / f"{ebook_stem}{ext}"
                if potential.exists():
                    job["output_file"] = str(potential)
                    break

            if progress_callback:
                await progress_callback(100, "Conversion complete!")
        else:
            job["status"] = "failed"
            job["error"] = stderr.decode() or stdout.decode() or "Unknown error"
            if progress_callback:
                await progress_callback(-1, f"Failed: {job['error']}")

        return job

    def get_job_status(self, job_id: int) -> Optional[Dict]:
        """Get status of a conversion job.

        Args:
            job_id: Job ID

        Returns:
            Job status dictionary or None
        """
        for job in self.conversion_jobs:
            if job["id"] == job_id:
                return {
                    "job_id": job_id,
                    "status": job["status"],
                    "progress": job.get("progress", 0),
                    "ebook": Path(job["ebook_path"]).name,
                    "voice": job.get("voice_name", job.get("voice")),
                    "started_at": job["started_at"],
                    "completed_at": job.get("completed_at"),
                    "output_file": job.get("output_file"),
                    "error": job.get("error"),
                }
        return None

    def list_jobs(self, status: Optional[str] = None) -> List[Dict]:
        """List all conversion jobs.

        Args:
            status: Filter by status (queued, processing, completed, failed)

        Returns:
            List of job summaries
        """
        jobs = self.conversion_jobs
        if status:
            jobs = [j for j in jobs if j["status"] == status]

        return [self.get_job_status(j["id"]) for j in jobs]

    # =========================================================================
    # Voice Profile Support (for cloned voices)
    # =========================================================================

    def get_voice_profiles(self) -> List[Dict]:
        """Get available voice profiles (cloned voices).

        Returns:
            List of voice profile summaries
        """
        try:
            from integrations.voice_cloning import VoiceCloner

            cloner = VoiceCloner()
            return cloner.list_profiles()
        except ImportError:
            logger.debug("Voice cloning module not available")
            return []

    async def create_voice_profile(
        self,
        name: str,
        reference_audio: str,
        description: str = "",
        language: str = "en",
        gender: str = "neutral",
    ) -> Dict:
        """Create a voice profile from reference audio for audiobook narration.

        Args:
            name: Profile name (e.g., "david_attenborough", "my_voice")
            reference_audio: Path to reference audio file (5-30 seconds recommended)
            description: Human-readable description
            language: Primary language code
            gender: Voice gender (male/female/neutral)

        Returns:
            Created profile info
        """
        try:
            from integrations.voice_cloning import VoiceCloner

            cloner = VoiceCloner()
            profile = await cloner.create_profile(
                name=name,
                reference_audio=reference_audio,
                description=description,
                language=language,
                gender=gender,
            )
            return {
                "status": "success",
                "profile": {
                    "name": profile.name,
                    "description": profile.description,
                    "language": profile.language,
                    "gender": profile.gender,
                    "backends": profile.backend_compatibility,
                },
            }
        except ImportError:
            return {"status": "error", "error": "Voice cloning module not available"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def convert_with_cloned_voice(
        self,
        ebook_path: str,
        voice_profile: str,
        speed: float = 1.0,
        output_format: str = "m4b",
        output_folder: Optional[str] = None,
    ) -> Dict:
        """Convert ebook using a cloned voice profile (requires Coqui XTTS).

        This uses the voice cloning system instead of Kokoro preset voices.
        Requires more GPU resources but produces speech in your chosen voice.

        Args:
            ebook_path: Path to ebook file
            voice_profile: Name of saved voice profile
            speed: Narration speed
            output_format: Output format (m4b, mp3, wav)
            output_folder: Output folder

        Returns:
            Job result dictionary
        """
        try:
            from integrations.voice_cloning import VoiceCloner

            cloner = VoiceCloner()

            # Load profile
            profile = cloner.load_profile(voice_profile)
            if not profile:
                return {
                    "status": "error",
                    "error": f"Profile not found: {voice_profile}",
                }

            # Validate ebook
            validation = self.validate_ebook(ebook_path)
            if not validation["valid"]:
                return {"status": "error", "error": validation["error"]}

            output_dir = Path(output_folder) if output_folder else self.output_dir
            output_dir.mkdir(parents=True, exist_ok=True)

            # For now, use the profile's reference audio with XTTS
            # Full chapter-by-chapter cloning would require custom implementation
            job = {
                "id": len(self.conversion_jobs) + 1,
                "ebook_path": str(Path(ebook_path).absolute()),
                "voice_profile": voice_profile,
                "voice_type": "cloned",
                "status": "processing",
                "started_at": datetime.now().isoformat(),
                "message": "Voice cloning conversion started. This may take longer than preset voices.",
            }
            self.conversion_jobs.append(job)

            logger.info(
                f"Job {job['id']}: Converting with cloned voice '{voice_profile}'"
            )

            # Note: Full implementation would process each chapter with XTTS
            # For now, we indicate this is available but audiblez CLI doesn't support custom voices
            job["status"] = "pending"
            job["message"] = (
                "Voice cloning audiobook conversion requires custom chapter processing. "
                "For preset voices, use convert_ebook() with voices like 'af_heart'. "
                "Full cloned voice support coming in future update."
            )

            return job

        except ImportError:
            return {
                "status": "error",
                "error": "Voice cloning module not available. Install: pip install TTS",
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_all_voices(self) -> Dict[str, List]:
        """Get all available voices including preset and profile-based.

        Returns:
            Dictionary with 'preset' and 'profiles' voice lists
        """
        result = {
            "preset": [
                {"id": k, "name": v, "backend": "kokoro"}
                for k, v in AVAILABLE_VOICES.items()
            ],
            "profiles": self.get_voice_profiles(),
            "default": DEFAULT_VOICE,
        }
        return result

    def generate_report(self) -> Dict:
        """Generate comprehensive audiobook creator report.

        Returns:
            Dictionary with creator status and statistics
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": (
                "operational" if all(self.dependencies.values()) else "degraded"
            ),
            "output_directory": str(self.output_dir),
            "dependencies": self.dependencies,
            "available_voices": len(AVAILABLE_VOICES),
            "supported_input_formats": SUPPORTED_FORMATS,
            "supported_output_formats": OUTPUT_FORMATS,
            "statistics": {
                "total_jobs": len(self.conversion_jobs),
                "queued": len(
                    [j for j in self.conversion_jobs if j["status"] == "queued"]
                ),
                "processing": len(
                    [j for j in self.conversion_jobs if j["status"] == "processing"]
                ),
                "completed": len(
                    [j for j in self.conversion_jobs if j["status"] == "completed"]
                ),
                "failed": len(
                    [j for j in self.conversion_jobs if j["status"] == "failed"]
                ),
            },
            "recent_jobs": [
                self.get_job_status(j["id"]) for j in self.conversion_jobs[-5:]
            ],
        }


def quick_convert(
    ebook_path: str,
    voice: str = DEFAULT_VOICE,
    speed: float = 1.0,
    output_folder: Optional[str] = None,
) -> Dict:
    """Quick conversion function for simple use cases.

    Args:
        ebook_path: Path to ebook
        voice: Voice ID (default: af_sky)
        speed: Speed 0.5-2.0 (default: 1.0)
        output_folder: Output folder (default: ~/Audiobooks)

    Returns:
        Conversion result
    """
    agent = AudiobookCreatorAgent(output_dir=output_folder)
    return agent.convert_ebook(ebook_path, voice=voice, speed=speed)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    agent = AudiobookCreatorAgent()

    # Print report
    report = agent.generate_report()
    print(json.dumps(report, indent=2))

    # List voices
    print("\n" + "=" * 50)
    print("Available Voices (American English):")
    print("=" * 50)
    for voice_id, description in agent.get_available_voices("a").items():
        marker = " (default)" if voice_id == DEFAULT_VOICE else ""
        print(f"  {voice_id}: {description}{marker}")

    print("\n" + "=" * 50)
    print("Usage Examples:")
    print("=" * 50)
    print(
        """
    # Quick conversion
    from agents.audiobook_creator import quick_convert
    result = quick_convert("book.epub", voice="af_sarah", speed=1.2)
    
    # Full control
    from agents.audiobook_creator import AudiobookCreatorAgent
    agent = AudiobookCreatorAgent(output_dir="./audiobooks")
    
    # Check available voices
    voices = agent.get_available_voices("b")  # British voices
    
    # Validate before converting
    info = agent.validate_ebook("book.epub")
    
    # Convert
    job = agent.convert_ebook(
        "book.epub",
        voice="bf_emma",
        speed=1.1,
        use_cuda=True
    )
    
    # Check status
    status = agent.get_job_status(job["id"])
    
    # CLI usage:
    # audiblez book.epub -v af_sky -s 1.2
    """
    )
