#!/usr/bin/env python3
"""
OsMEN Voice Cloning Integration

Provides high-quality voice cloning capabilities using multiple TTS backends:
- Coqui XTTS: Zero-shot multilingual voice cloning (16 languages)
- Kokoro-ONNX: Fast, lightweight TTS with 54 preset voices
- StyleTTS2: Expressive TTS with style transfer
- IndexTTS: Industrial-grade Chinese/English with emotion control

Voice Profiles:
- Save speaker embeddings from reference audio
- Load and use profiles by name
- Blend multiple speakers

Usage:
    from integrations.voice_cloning import VoiceCloner, VoiceProfile

    cloner = VoiceCloner()

    # Create profile from reference audio
    profile = await cloner.create_profile("my_voice", "reference.wav")

    # Generate speech with cloned voice
    audio = await cloner.synthesize(
        text="Hello world",
        voice_profile="my_voice",
        output_path="output.wav"
    )

    # Or use zero-shot with any audio reference
    audio = await cloner.clone_and_speak(
        text="Hello world",
        reference_audio="any_voice.wav",
        output_path="output.wav"
    )
"""

import asyncio
import hashlib
import json
import logging
import os
import pickle
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

PROFILES_DIR = Path(os.getenv("OSMEN_VOICE_PROFILES", "data/voice_profiles"))
CACHE_DIR = Path(os.getenv("OSMEN_TTS_CACHE", "cache/tts"))

# Default voices for different backends
DEFAULT_KOKORO_VOICE = "af_heart"  # American Female - Heart
DEFAULT_XTTS_VOICE = "en_US-jenny-medium"
DEFAULT_LANGUAGE = "en"


class TTSBackend(Enum):
    """Available TTS backends for voice cloning"""

    KOKORO_ONNX = "kokoro_onnx"  # Fast, 54 preset voices
    COQUI_XTTS = "coqui_xtts"  # Zero-shot cloning, 16 languages
    STYLETTS2 = "styletts2"  # Expressive with style transfer
    INDEX_TTS = "index_tts"  # Industrial Chinese/English + emotion


class VoiceGender(Enum):
    """Voice gender classification"""

    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class VoiceLanguage(Enum):
    """Supported languages"""

    ENGLISH = "en"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    FRENCH = "fr"
    SPANISH = "es"
    PORTUGUESE = "pt"
    ITALIAN = "it"
    GERMAN = "de"
    HINDI = "hi"
    TURKISH = "tr"


@dataclass
class VoiceProfile:
    """A saved voice profile with speaker embedding"""

    name: str
    description: str = ""
    reference_audio: Optional[str] = None
    language: str = "en"
    gender: str = "neutral"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Speaker embeddings (backend-specific)
    xtts_embedding: Optional[np.ndarray] = None
    xtts_gpt_cond_latent: Optional[np.ndarray] = None
    styletts2_style: Optional[np.ndarray] = None

    # Metadata
    sample_rate: int = 24000
    duration_seconds: float = 0.0
    backend_compatibility: List[str] = field(default_factory=list)

    def save(self, profiles_dir: Optional[Path] = None) -> Path:
        """Save profile to disk"""
        profiles_dir = profiles_dir or PROFILES_DIR
        profiles_dir.mkdir(parents=True, exist_ok=True)

        profile_path = profiles_dir / f"{self.name}.profile"

        # Convert to dict for JSON
        data = {
            "name": self.name,
            "description": self.description,
            "reference_audio": self.reference_audio,
            "language": self.language,
            "gender": self.gender,
            "created_at": self.created_at,
            "sample_rate": self.sample_rate,
            "duration_seconds": self.duration_seconds,
            "backend_compatibility": self.backend_compatibility,
        }

        # Save JSON metadata
        with open(profile_path.with_suffix(".json"), "w") as f:
            json.dump(data, f, indent=2)

        # Save numpy embeddings separately
        embeddings = {}
        if self.xtts_embedding is not None:
            embeddings["xtts_embedding"] = self.xtts_embedding
        if self.xtts_gpt_cond_latent is not None:
            embeddings["xtts_gpt_cond_latent"] = self.xtts_gpt_cond_latent
        if self.styletts2_style is not None:
            embeddings["styletts2_style"] = self.styletts2_style

        if embeddings:
            np.savez(profile_path.with_suffix(".npz"), **embeddings)

        logger.info(f"Saved voice profile: {self.name}")
        return profile_path

    @classmethod
    def load(cls, name: str, profiles_dir: Optional[Path] = None) -> "VoiceProfile":
        """Load profile from disk"""
        profiles_dir = profiles_dir or PROFILES_DIR
        json_path = profiles_dir / f"{name}.json"
        npz_path = profiles_dir / f"{name}.npz"

        if not json_path.exists():
            raise FileNotFoundError(f"Profile not found: {name}")

        with open(json_path) as f:
            data = json.load(f)

        profile = cls(**data)

        # Load embeddings if present
        if npz_path.exists():
            embeddings = np.load(npz_path, allow_pickle=True)
            if "xtts_embedding" in embeddings:
                profile.xtts_embedding = embeddings["xtts_embedding"]
            if "xtts_gpt_cond_latent" in embeddings:
                profile.xtts_gpt_cond_latent = embeddings["xtts_gpt_cond_latent"]
            if "styletts2_style" in embeddings:
                profile.styletts2_style = embeddings["styletts2_style"]

        return profile


# ============================================================================
# Kokoro ONNX Backend (Fast, Lightweight)
# ============================================================================


class KokoroONNXBackend:
    """
    Kokoro: Fast, high-quality TTS with 54 preset voices

    Uses the full kokoro package (KPipeline) which is what audiblez uses.

    Pros: Very fast, GPU-friendly, good quality
    Cons: No voice cloning (preset voices only)
    """

    # Voice mapping (code -> description)
    VOICES = {
        # American English
        "af_alloy": ("American Female - Alloy", "female", "en"),
        "af_aoede": ("American Female - Aoede", "female", "en"),
        "af_bella": ("American Female - Bella", "female", "en"),
        "af_heart": ("American Female - Heart", "female", "en"),
        "af_jessica": ("American Female - Jessica", "female", "en"),
        "af_kore": ("American Female - Kore", "female", "en"),
        "af_nicole": ("American Female - Nicole", "female", "en"),
        "af_nova": ("American Female - Nova", "female", "en"),
        "af_river": ("American Female - River", "female", "en"),
        "af_sarah": ("American Female - Sarah", "female", "en"),
        "af_sky": ("American Female - Sky", "female", "en"),
        "am_adam": ("American Male - Adam", "male", "en"),
        "am_echo": ("American Male - Echo", "male", "en"),
        "am_eric": ("American Male - Eric", "male", "en"),
        "am_fenrir": ("American Male - Fenrir", "male", "en"),
        "am_liam": ("American Male - Liam", "male", "en"),
        "am_michael": ("American Male - Michael", "male", "en"),
        "am_onyx": ("American Male - Onyx", "male", "en"),
        # British English
        "bf_alice": ("British Female - Alice", "female", "en"),
        "bf_emma": ("British Female - Emma", "female", "en"),
        "bf_isabella": ("British Female - Isabella", "female", "en"),
        "bf_lily": ("British Female - Lily", "female", "en"),
        "bm_daniel": ("British Male - Daniel", "male", "en"),
        "bm_fable": ("British Male - Fable", "male", "en"),
        "bm_george": ("British Male - George", "male", "en"),
        "bm_lewis": ("British Male - Lewis", "male", "en"),
        # Japanese
        "jf_alpha": ("Japanese Female - Alpha", "female", "ja"),
        "jf_gongitsune": ("Japanese Female - Gongitsune", "female", "ja"),
        "jf_nezumi": ("Japanese Female - Nezumi", "female", "ja"),
        "jf_tebukuro": ("Japanese Female - Tebukuro", "female", "ja"),
        "jm_kumo": ("Japanese Male - Kumo", "male", "ja"),
        # Chinese
        "zf_xiaobei": ("Chinese Female - Xiaobei", "female", "zh"),
        "zf_xiaoni": ("Chinese Female - Xiaoni", "female", "zh"),
        "zf_xiaoxiao": ("Chinese Female - Xiaoxiao", "female", "zh"),
        "zf_xiaoyi": ("Chinese Female - Xiaoyi", "female", "zh"),
        "zm_yunjian": ("Chinese Male - Yunjian", "male", "zh"),
        "zm_yunxi": ("Chinese Male - Yunxi", "male", "zh"),
        "zm_yunxia": ("Chinese Male - Yunxia", "male", "zh"),
        "zm_yunyang": ("Chinese Male - Yunyang", "male", "zh"),
        # Korean
        "kf_sarah": ("Korean Female - Sarah", "female", "ko"),
        "km_kevin": ("Korean Male - Kevin", "male", "ko"),
        # French
        "ff_siwis": ("French Female - Siwis", "female", "fr"),
        # Hindi
        "hf_alpha": ("Hindi Female - Alpha", "female", "hi"),
        "hf_beta": ("Hindi Female - Beta", "female", "hi"),
        "hm_omega": ("Hindi Male - Omega", "male", "hi"),
        "hm_psi": ("Hindi Male - Psi", "male", "hi"),
        # Italian
        "if_sara": ("Italian Female - Sara", "female", "it"),
        "im_nicola": ("Italian Male - Nicola", "male", "it"),
        # Portuguese
        "pf_dora": ("Portuguese Female - Dora", "female", "pt"),
        "pm_alex": ("Portuguese Male - Alex", "male", "pt"),
        "pm_santa": ("Portuguese Male - Santa", "male", "pt"),
        # Spanish
        "ef_dora": ("Spanish Female - Dora", "female", "es"),
        "em_alex": ("Spanish Male - Alex", "male", "es"),
        "em_santa": ("Spanish Male - Santa", "male", "es"),
    }

    # Language code mapping for KPipeline
    LANG_CODES = {
        "en": "a",  # American English
        "en-us": "a",
        "en-gb": "b",  # British English
        "ja": "j",
        "zh": "z",
        "ko": "k",
        "fr": "f",
        "hi": "h",
        "it": "i",
        "pt": "p",
        "es": "e",
    }

    def __init__(self):
        self.available = False
        self.pipelines: Dict[str, Any] = {}  # lang_code -> KPipeline
        self._check_availability()

    def _check_availability(self):
        """Check if kokoro is available"""
        try:
            from kokoro import KPipeline

            self.available = True
            logger.info("Kokoro TTS backend available")
        except ImportError:
            logger.warning("kokoro not installed. Install with: pip install kokoro")

    def _get_pipeline(self, lang_code: str = "a"):
        """Lazy-load the Kokoro pipeline for a language"""
        if lang_code not in self.pipelines:
            try:
                from kokoro import KPipeline

                self.pipelines[lang_code] = KPipeline(lang_code=lang_code)
                logger.info(f"Kokoro pipeline loaded for language: {lang_code}")
            except Exception as e:
                logger.error(f"Failed to load Kokoro pipeline: {e}")
                return None
        return self.pipelines[lang_code]

    def _voice_to_lang_code(self, voice: str) -> str:
        """Get language code from voice ID"""
        if voice in self.VOICES:
            lang = self.VOICES[voice][2]
            # Map language to Kokoro language code
            prefix = voice[0]  # First letter: a=American, b=British, j=Japanese, etc.
            return prefix
        return "a"  # Default to American English

    def get_voices(self) -> List[Dict[str, str]]:
        """Get available preset voices"""
        return [
            {
                "id": code,
                "name": info[0],
                "gender": info[1],
                "language": info[2],
                "backend": "kokoro_onnx",
            }
            for code, info in self.VOICES.items()
        ]

    async def synthesize(
        self,
        text: str,
        voice: str = DEFAULT_KOKORO_VOICE,
        output_path: Optional[Union[str, Path]] = None,
        speed: float = 1.0,
    ) -> Dict[str, Any]:
        """Synthesize speech with Kokoro TTS"""
        if not self.available:
            return {"error": "Kokoro not available"}

        # Get the right pipeline for this voice's language
        lang_code = self._voice_to_lang_code(voice)
        pipeline = self._get_pipeline(lang_code)
        if pipeline is None:
            return {"error": "Failed to load Kokoro pipeline"}

        try:
            # Validate voice
            if voice not in self.VOICES:
                logger.warning(f"Unknown voice {voice}, using {DEFAULT_KOKORO_VOICE}")
                voice = DEFAULT_KOKORO_VOICE

            # Generate audio using KPipeline
            # KPipeline returns generator of (graphemes, phonemes, audio) tuples
            audio_chunks = []
            sample_rate = 24000  # Kokoro uses 24kHz

            def generate():
                for gs, ps, audio in pipeline(text, voice=voice, speed=speed):
                    audio_chunks.append(audio)

            await asyncio.to_thread(generate)

            # Concatenate all audio chunks
            if audio_chunks:
                audio = np.concatenate(audio_chunks)
            else:
                return {"error": "No audio generated"}

            # Save if output path provided
            if output_path:
                import soundfile as sf

                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                sf.write(str(output_path), audio, sample_rate)

                return {
                    "success": True,
                    "output_path": str(output_path),
                    "voice": voice,
                    "sample_rate": sample_rate,
                    "duration": len(audio) / sample_rate,
                    "backend": "kokoro_onnx",
                }
            else:
                return {
                    "success": True,
                    "audio": audio,
                    "sample_rate": sample_rate,
                    "voice": voice,
                    "backend": "kokoro_onnx",
                }

        except Exception as e:
            logger.error(f"Kokoro synthesis failed: {e}")
            return {"error": str(e)}


# ============================================================================
# Coqui XTTS Backend (Zero-Shot Voice Cloning)
# ============================================================================


class CoquiXTTSBackend:
    """
    Coqui XTTS: Zero-shot multilingual voice cloning

    Pros: Best voice cloning quality, 16 languages, streaming support
    Cons: Slower, requires GPU for good performance
    """

    SUPPORTED_LANGUAGES = [
        "en",
        "es",
        "fr",
        "de",
        "it",
        "pt",
        "pl",
        "tr",
        "ru",
        "nl",
        "cs",
        "ar",
        "zh-cn",
        "ja",
        "hu",
        "ko",
    ]

    def __init__(self, use_gpu: bool = True):
        self.available = False
        self.model = None
        self.use_gpu = use_gpu
        self._check_availability()

    def _check_availability(self):
        """Check if Coqui TTS is available"""
        try:
            from TTS.api import TTS

            self.available = True
            logger.info("Coqui XTTS backend available")
        except ImportError:
            logger.warning("TTS not installed. Install with: pip install TTS")

    def _get_model(self):
        """Lazy-load the XTTS model"""
        if self.model is None and self.available:
            try:
                import torch
                from TTS.api import TTS

                device = "cuda" if self.use_gpu and torch.cuda.is_available() else "cpu"
                logger.info(f"Loading XTTS model on {device}...")

                self.model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
                if device == "cuda":
                    self.model = self.model.to(device)

                logger.info("XTTS model loaded")
            except Exception as e:
                logger.error(f"Failed to load XTTS model: {e}")
                self.available = False
        return self.model

    async def extract_speaker_embedding(
        self, reference_audio: Union[str, Path, List[Union[str, Path]]]
    ) -> Dict[str, Any]:
        """Extract speaker embedding from reference audio for later use"""
        if not self.available:
            return {"error": "Coqui XTTS not available"}

        try:
            import torch
            import torchaudio
            from TTS.tts.configs.xtts_config import XttsConfig
            from TTS.tts.models.xtts import Xtts

            model = self._get_model()
            if model is None:
                return {"error": "Failed to load XTTS model"}

            # Convert to list
            if isinstance(reference_audio, (str, Path)):
                reference_audio = [str(reference_audio)]
            else:
                reference_audio = [str(p) for p in reference_audio]

            # Get conditioning latents
            gpt_cond_latent, speaker_embedding = await asyncio.to_thread(
                model.synthesizer.tts_model.get_conditioning_latents,
                audio_path=reference_audio,
            )

            return {
                "success": True,
                "gpt_cond_latent": gpt_cond_latent.cpu().numpy(),
                "speaker_embedding": speaker_embedding.cpu().numpy(),
                "reference_files": reference_audio,
            }

        except Exception as e:
            logger.error(f"Speaker embedding extraction failed: {e}")
            return {"error": str(e)}

    async def synthesize(
        self,
        text: str,
        reference_audio: Optional[Union[str, Path, List[Union[str, Path]]]] = None,
        speaker_embedding: Optional[np.ndarray] = None,
        gpt_cond_latent: Optional[np.ndarray] = None,
        speaker: Optional[str] = None,  # Built-in speaker name
        language: str = "en",
        output_path: Optional[Union[str, Path]] = None,
        split_sentences: bool = True,
    ) -> Dict[str, Any]:
        """Synthesize speech with voice cloning"""
        if not self.available:
            return {"error": "Coqui XTTS not available"}

        model = self._get_model()
        if model is None:
            return {"error": "Failed to load XTTS model"}

        try:
            import torch

            output_path = Path(output_path) if output_path else None
            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)

            # Use pre-computed embeddings if provided
            if speaker_embedding is not None and gpt_cond_latent is not None:
                # Manual inference with embeddings
                gpt_cond = torch.tensor(gpt_cond_latent)
                spk_emb = torch.tensor(speaker_embedding)

                out = await asyncio.to_thread(
                    model.synthesizer.tts_model.inference,
                    text,
                    language,
                    gpt_cond,
                    spk_emb,
                )
                audio = out["wav"]
                sample_rate = 24000

            elif reference_audio:
                # Clone from reference audio
                if isinstance(reference_audio, (str, Path)):
                    reference_audio = [str(reference_audio)]

                audio = await asyncio.to_thread(
                    model.tts,
                    text=text,
                    speaker_wav=reference_audio,
                    language=language,
                    split_sentences=split_sentences,
                )
                sample_rate = model.synthesizer.output_sample_rate

            elif speaker:
                # Use built-in speaker
                audio = await asyncio.to_thread(
                    model.tts_to_file if output_path else model.tts,
                    text=text,
                    speaker=speaker,
                    language=language,
                    file_path=str(output_path) if output_path else None,
                    split_sentences=split_sentences,
                )
                sample_rate = model.synthesizer.output_sample_rate

                if output_path:
                    return {
                        "success": True,
                        "output_path": str(output_path),
                        "speaker": speaker,
                        "language": language,
                        "backend": "coqui_xtts",
                    }
            else:
                return {
                    "error": "Either reference_audio, speaker_embedding, or speaker required"
                }

            # Save output
            if output_path:
                import soundfile as sf

                sf.write(str(output_path), audio, sample_rate)

                return {
                    "success": True,
                    "output_path": str(output_path),
                    "sample_rate": sample_rate,
                    "duration": len(audio) / sample_rate,
                    "language": language,
                    "backend": "coqui_xtts",
                }
            else:
                return {
                    "success": True,
                    "audio": audio,
                    "sample_rate": sample_rate,
                    "language": language,
                    "backend": "coqui_xtts",
                }

        except Exception as e:
            logger.error(f"XTTS synthesis failed: {e}")
            return {"error": str(e)}

    def get_speakers(self) -> List[str]:
        """Get built-in speaker names"""
        if not self.available:
            return []

        try:
            model = self._get_model()
            if model and hasattr(model, "speakers"):
                return model.speakers or []
        except Exception:
            pass
        return []


# ============================================================================
# VoiceCloner: Unified Voice Cloning API
# ============================================================================


class VoiceCloner:
    """
    Unified voice cloning API with automatic backend selection

    Priority: XTTS (cloning) > Kokoro (preset voices)
    """

    def __init__(
        self,
        default_backend: TTSBackend = TTSBackend.KOKORO_ONNX,
        use_gpu: bool = True,
        profiles_dir: Optional[Path] = None,
        cache_dir: Optional[Path] = None,
    ):
        self.default_backend = default_backend
        self.profiles_dir = profiles_dir or PROFILES_DIR
        self.cache_dir = cache_dir or CACHE_DIR

        # Ensure directories exist
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize backends
        self.backends: Dict[TTSBackend, Any] = {}

        # Kokoro ONNX (fast, preset voices)
        self.backends[TTSBackend.KOKORO_ONNX] = KokoroONNXBackend()

        # Coqui XTTS (voice cloning)
        self.backends[TTSBackend.COQUI_XTTS] = CoquiXTTSBackend(use_gpu=use_gpu)

        # Profile cache
        self._profile_cache: Dict[str, VoiceProfile] = {}

        logger.info(
            f"VoiceCloner initialized with backends: {self.get_available_backends()}"
        )

    def get_available_backends(self) -> List[str]:
        """Get list of available backends"""
        return [
            backend.value for backend, impl in self.backends.items() if impl.available
        ]

    def get_status(self) -> Dict[str, Any]:
        """Get detailed status of all backends"""
        return {
            "backends": {
                backend.value: impl.available for backend, impl in self.backends.items()
            },
            "default_backend": self.default_backend.value,
            "profiles_count": len(list(self.profiles_dir.glob("*.json"))),
            "profiles_dir": str(self.profiles_dir),
        }

    # =========================================================================
    # Profile Management
    # =========================================================================

    async def create_profile(
        self,
        name: str,
        reference_audio: Union[str, Path, List[Union[str, Path]]],
        description: str = "",
        language: str = "en",
        gender: str = "neutral",
    ) -> VoiceProfile:
        """
        Create a voice profile from reference audio

        Args:
            name: Profile name (unique identifier)
            reference_audio: Path(s) to reference audio file(s)
            description: Human-readable description
            language: Primary language
            gender: Voice gender (male/female/neutral)

        Returns:
            VoiceProfile with extracted embeddings
        """
        # Get duration from audio
        duration = 0.0
        if isinstance(reference_audio, (str, Path)):
            ref_path = Path(reference_audio)
            reference_audio = str(ref_path)
            try:
                import soundfile as sf

                info = sf.info(str(ref_path))
                duration = info.duration
            except Exception:
                pass
        else:
            reference_audio = [str(p) for p in reference_audio]

        profile = VoiceProfile(
            name=name,
            description=description,
            reference_audio=(
                reference_audio
                if isinstance(reference_audio, str)
                else reference_audio[0]
            ),
            language=language,
            gender=gender,
            duration_seconds=duration,
        )

        # Extract XTTS embedding if available
        xtts = self.backends.get(TTSBackend.COQUI_XTTS)
        if xtts and xtts.available:
            result = await xtts.extract_speaker_embedding(reference_audio)
            if result.get("success"):
                profile.xtts_embedding = result["speaker_embedding"]
                profile.xtts_gpt_cond_latent = result["gpt_cond_latent"]
                profile.backend_compatibility.append("coqui_xtts")

        # Kokoro doesn't support custom voices, but profile can specify preferred preset
        if self.backends[TTSBackend.KOKORO_ONNX].available:
            profile.backend_compatibility.append("kokoro_onnx")

        # Save profile
        profile.save(self.profiles_dir)
        self._profile_cache[name] = profile

        logger.info(f"Created voice profile: {name} ({profile.backend_compatibility})")
        return profile

    def load_profile(self, name: str) -> Optional[VoiceProfile]:
        """Load a voice profile by name"""
        if name in self._profile_cache:
            return self._profile_cache[name]

        try:
            profile = VoiceProfile.load(name, self.profiles_dir)
            self._profile_cache[name] = profile
            return profile
        except FileNotFoundError:
            logger.warning(f"Profile not found: {name}")
            return None

    def list_profiles(self) -> List[Dict[str, Any]]:
        """List all available voice profiles"""
        profiles = []
        for json_path in self.profiles_dir.glob("*.json"):
            try:
                with open(json_path) as f:
                    data = json.load(f)
                    profiles.append(
                        {
                            "name": data["name"],
                            "description": data.get("description", ""),
                            "language": data.get("language", "en"),
                            "gender": data.get("gender", "neutral"),
                            "created_at": data.get("created_at", ""),
                            "backends": data.get("backend_compatibility", []),
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to load profile {json_path}: {e}")
        return profiles

    def delete_profile(self, name: str) -> bool:
        """Delete a voice profile"""
        json_path = self.profiles_dir / f"{name}.json"
        npz_path = self.profiles_dir / f"{name}.npz"

        deleted = False
        if json_path.exists():
            json_path.unlink()
            deleted = True
        if npz_path.exists():
            npz_path.unlink()
            deleted = True

        if name in self._profile_cache:
            del self._profile_cache[name]

        return deleted

    # =========================================================================
    # Synthesis
    # =========================================================================

    def get_voices(self, backend: Optional[TTSBackend] = None) -> List[Dict[str, str]]:
        """Get available voices (preset voices + profiles)"""
        voices = []

        # Add Kokoro preset voices
        kokoro = self.backends.get(TTSBackend.KOKORO_ONNX)
        if (
            kokoro
            and kokoro.available
            and (backend is None or backend == TTSBackend.KOKORO_ONNX)
        ):
            voices.extend(kokoro.get_voices())

        # Add voice profiles as custom voices
        for profile_info in self.list_profiles():
            voices.append(
                {
                    "id": f"profile:{profile_info['name']}",
                    "name": f"Profile: {profile_info['name']}",
                    "description": profile_info.get("description", ""),
                    "gender": profile_info.get("gender", "neutral"),
                    "language": profile_info.get("language", "en"),
                    "backend": "voice_profile",
                    "profile_name": profile_info["name"],
                }
            )

        return voices

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        voice_profile: Optional[str] = None,
        reference_audio: Optional[Union[str, Path]] = None,
        language: str = "en",
        output_path: Optional[Union[str, Path]] = None,
        backend: Optional[TTSBackend] = None,
        speed: float = 1.0,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Synthesize speech with the best available backend

        Args:
            text: Text to synthesize
            voice: Preset voice ID (e.g., "af_heart" for Kokoro)
            voice_profile: Name of saved voice profile
            reference_audio: Path to reference audio for zero-shot cloning
            language: Language code
            output_path: Optional output file path
            backend: Force specific backend
            speed: Speech speed multiplier (Kokoro only)
            **kwargs: Backend-specific options

        Returns:
            Dict with success status, output path, and metadata
        """
        # Determine best backend
        if backend:
            selected_backend = backend
        elif voice_profile or reference_audio:
            # Voice cloning needed - use XTTS
            selected_backend = TTSBackend.COQUI_XTTS
        elif voice and voice.startswith("profile:"):
            # Profile reference in voice string
            voice_profile = voice.replace("profile:", "")
            selected_backend = TTSBackend.COQUI_XTTS
        else:
            # Use default (Kokoro for preset voices)
            selected_backend = self.default_backend

        # Get backend implementation
        impl = self.backends.get(selected_backend)
        if not impl or not impl.available:
            # Fallback
            for fallback_backend in [TTSBackend.KOKORO_ONNX, TTSBackend.COQUI_XTTS]:
                impl = self.backends.get(fallback_backend)
                if impl and impl.available:
                    selected_backend = fallback_backend
                    break
            else:
                return {"error": "No TTS backends available"}

        # Handle voice profile
        if voice_profile:
            profile = self.load_profile(voice_profile)
            if not profile:
                return {"error": f"Voice profile not found: {voice_profile}"}

            if (
                selected_backend == TTSBackend.COQUI_XTTS
                and profile.xtts_embedding is not None
            ):
                return await impl.synthesize(
                    text=text,
                    speaker_embedding=profile.xtts_embedding,
                    gpt_cond_latent=profile.xtts_gpt_cond_latent,
                    language=language,
                    output_path=output_path,
                    **kwargs,
                )
            elif profile.reference_audio:
                reference_audio = profile.reference_audio

        # Handle reference audio (zero-shot)
        if reference_audio and selected_backend == TTSBackend.COQUI_XTTS:
            return await impl.synthesize(
                text=text,
                reference_audio=reference_audio,
                language=language,
                output_path=output_path,
                **kwargs,
            )

        # Use preset voice
        if selected_backend == TTSBackend.KOKORO_ONNX:
            return await impl.synthesize(
                text=text,
                voice=voice or DEFAULT_KOKORO_VOICE,
                output_path=output_path,
                speed=speed,
            )
        else:
            # XTTS with built-in speaker (if no cloning)
            return await impl.synthesize(
                text=text,
                speaker=voice,
                language=language,
                output_path=output_path,
                **kwargs,
            )

    async def clone_and_speak(
        self,
        text: str,
        reference_audio: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Zero-shot voice cloning: clone from any audio and speak

        This is a convenience method for one-off cloning without saving a profile.
        """
        return await self.synthesize(
            text=text,
            reference_audio=reference_audio,
            language=language,
            output_path=output_path,
            backend=TTSBackend.COQUI_XTTS,
        )


# ============================================================================
# Module-level helpers
# ============================================================================

_cloner: Optional[VoiceCloner] = None


def get_cloner() -> VoiceCloner:
    """Get or create global VoiceCloner instance"""
    global _cloner
    if _cloner is None:
        _cloner = VoiceCloner()
    return _cloner


async def quick_tts(
    text: str,
    voice: str = DEFAULT_KOKORO_VOICE,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Quick TTS with default settings"""
    cloner = get_cloner()
    return await cloner.synthesize(text=text, voice=voice, output_path=output_path)


async def clone_voice(
    reference_audio: str,
    text: str,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Quick voice cloning"""
    cloner = get_cloner()
    return await cloner.clone_and_speak(
        text=text, reference_audio=reference_audio, output_path=output_path
    )


# ============================================================================
# Main (Testing)
# ============================================================================

if __name__ == "__main__":

    async def main():
        print("=" * 60)
        print("Voice Cloning Integration Test")
        print("=" * 60)

        cloner = VoiceCloner()

        print("\n[Status]")
        status = cloner.get_status()
        print(json.dumps(status, indent=2))

        print("\n[Available Voices]")
        voices = cloner.get_voices()
        print(f"Total voices: {len(voices)}")
        for v in voices[:5]:
            print(f"  - {v['id']}: {v['name']} ({v['language']})")
        if len(voices) > 5:
            print(f"  ... and {len(voices) - 5} more")

        # Test Kokoro synthesis if available
        kokoro = cloner.backends.get(TTSBackend.KOKORO_ONNX)
        if kokoro and kokoro.available:
            print("\n[Testing Kokoro-ONNX TTS]")
            result = await cloner.synthesize(
                text="Hello, this is a test of the Kokoro text to speech system.",
                voice="af_heart",
                output_path="test_kokoro.wav",
            )
            print(
                json.dumps({k: v for k, v in result.items() if k != "audio"}, indent=2)
            )

        # Test XTTS if available
        xtts = cloner.backends.get(TTSBackend.COQUI_XTTS)
        if xtts and xtts.available:
            print("\n[Testing Coqui XTTS]")
            print("XTTS is available for voice cloning")
            print("To test: provide a reference audio file")

        print("\n[Done]")

    asyncio.run(main())
