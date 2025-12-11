#!/usr/bin/env python3
"""
OsMEN Voice/Audio Integration

Provides:
- Speech-to-Text via faster-whisper (local) or OpenAI Whisper API
- Text-to-Speech via multiple engines:
  - Kokoro-ONNX: Fast, lightweight, 54 preset voices
  - Coqui XTTS: Zero-shot voice cloning, 16 languages
  - pyttsx3: Local, always available
  - ElevenLabs: Premium cloud TTS
  - Edge TTS: Free Microsoft cloud TTS
- Voice Cloning via integrations.voice_cloning

Usage:
    from integrations.voice_audio import VoiceIntegration

    voice = VoiceIntegration()

    # Speech to Text
    text = await voice.transcribe("audio.wav")

    # Text to Speech (preset voice)
    audio_path = await voice.speak("Hello world", voice="af_heart", output="greeting.wav")

    # Voice Cloning
    from integrations.voice_cloning import VoiceCloner
    cloner = VoiceCloner()
    await cloner.clone_and_speak("Hello", "reference.wav", "cloned_output.wav")
"""

import asyncio
import io
import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================


class STTProvider(Enum):
    """Speech-to-Text providers"""

    FASTER_WHISPER = "faster_whisper"
    OPENAI_WHISPER = "openai_whisper"


class TTSProvider(Enum):
    """Text-to-Speech providers"""

    PYTTSX3 = "pyttsx3"
    ELEVENLABS = "elevenlabs"
    COQUI = "coqui"
    EDGE_TTS = "edge_tts"
    KOKORO_ONNX = "kokoro_onnx"  # Fast, 54 preset voices
    COQUI_XTTS = "coqui_xtts"  # Zero-shot voice cloning


@dataclass
class VoiceConfig:
    """Voice integration configuration"""

    # STT settings
    stt_provider: STTProvider = STTProvider.FASTER_WHISPER
    whisper_model: str = "base"  # tiny, base, small, medium, large-v3
    whisper_device: str = "cuda"  # cuda, cpu
    whisper_compute_type: str = "float16"  # float16, int8, float32

    # TTS settings
    tts_provider: TTSProvider = TTSProvider.PYTTSX3
    tts_voice_id: Optional[str] = None
    tts_rate: int = 150  # words per minute
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel

    # General
    audio_format: str = "wav"
    sample_rate: int = 16000


# ============================================================================
# Speech-to-Text
# ============================================================================


class FasterWhisperSTT:
    """Local STT using faster-whisper"""

    def __init__(self, config: VoiceConfig):
        self.config = config
        self.model = None
        self.available = False
        self._initialize()

    def _initialize(self):
        """Initialize faster-whisper model"""
        try:
            from faster_whisper import WhisperModel

            logger.info(f"Loading Whisper model: {self.config.whisper_model}")
            self.model = WhisperModel(
                self.config.whisper_model,
                device=self.config.whisper_device,
                compute_type=self.config.whisper_compute_type,
            )
            self.available = True
            logger.info("Faster-whisper model loaded")

        except ImportError:
            logger.warning("faster-whisper not installed")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")

    async def transcribe(
        self,
        audio_path: Union[str, Path],
        language: Optional[str] = None,
        task: str = "transcribe",  # transcribe or translate
    ) -> Dict[str, Any]:
        """Transcribe audio file"""
        if not self.available:
            return {"error": "Faster-whisper not available"}

        try:
            segments, info = self.model.transcribe(
                str(audio_path), language=language, task=task, vad_filter=True
            )

            # Collect segments
            text_segments = []
            full_text = []

            for segment in segments:
                text_segments.append(
                    {
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text.strip(),
                    }
                )
                full_text.append(segment.text.strip())

            return {
                "text": " ".join(full_text),
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration,
                "segments": text_segments,
            }

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return {"error": str(e)}


class OpenAIWhisperSTT:
    """STT using OpenAI Whisper API"""

    def __init__(self, config: VoiceConfig):
        self.config = config
        self.client = None
        self.available = False
        self._initialize()

    def _initialize(self):
        """Initialize OpenAI client"""
        try:
            from openai import AsyncOpenAI

            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = AsyncOpenAI(api_key=api_key)
                self.available = True
                logger.info("OpenAI Whisper API ready")
            else:
                logger.warning("OPENAI_API_KEY not set")

        except ImportError:
            logger.warning("openai package not installed")

    async def transcribe(
        self,
        audio_path: Union[str, Path],
        language: Optional[str] = None,
        task: str = "transcribe",
    ) -> Dict[str, Any]:
        """Transcribe audio using OpenAI API"""
        if not self.available:
            return {"error": "OpenAI Whisper not available"}

        try:
            with open(audio_path, "rb") as f:
                if task == "translate":
                    response = await self.client.audio.translations.create(
                        model="whisper-1", file=f
                    )
                else:
                    response = await self.client.audio.transcriptions.create(
                        model="whisper-1", file=f, language=language
                    )

            return {"text": response.text, "language": language, "segments": []}

        except Exception as e:
            logger.error(f"OpenAI transcription failed: {e}")
            return {"error": str(e)}


# ============================================================================
# Text-to-Speech
# ============================================================================


class Pyttsx3TTS:
    """Local TTS using pyttsx3"""

    def __init__(self, config: VoiceConfig):
        self.config = config
        self.engine = None
        self.available = False
        self._initialize()

    def _initialize(self):
        """Initialize pyttsx3 engine"""
        try:
            import pyttsx3

            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", self.config.tts_rate)

            # Set voice if specified
            if self.config.tts_voice_id:
                self.engine.setProperty("voice", self.config.tts_voice_id)

            self.available = True
            logger.info("pyttsx3 TTS ready")

        except ImportError:
            logger.warning("pyttsx3 not installed")
        except Exception as e:
            logger.error(f"pyttsx3 init failed: {e}")

    def get_voices(self) -> List[Dict[str, str]]:
        """Get available voices"""
        if not self.available:
            return []

        voices = []
        for voice in self.engine.getProperty("voices"):
            voices.append(
                {"id": voice.id, "name": voice.name, "languages": voice.languages}
            )
        return voices

    async def speak(
        self, text: str, output_path: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """Convert text to speech"""
        if not self.available:
            return {"error": "pyttsx3 not available"}

        try:
            if output_path:
                self.engine.save_to_file(text, str(output_path))
                self.engine.runAndWait()
                return {"output_path": str(output_path), "text": text}
            else:
                self.engine.say(text)
                self.engine.runAndWait()
                return {"spoken": True, "text": text}

        except Exception as e:
            logger.error(f"TTS failed: {e}")
            return {"error": str(e)}


class ElevenLabsTTS:
    """TTS using ElevenLabs API"""

    def __init__(self, config: VoiceConfig):
        self.config = config
        self.client = None
        self.available = False
        self._initialize()

    def _initialize(self):
        """Initialize ElevenLabs client"""
        api_key = self.config.elevenlabs_api_key or os.getenv("ELEVENLABS_API_KEY")

        if api_key:
            try:
                from elevenlabs import ElevenLabs

                self.client = ElevenLabs(api_key=api_key)
                self.available = True
                logger.info("ElevenLabs TTS ready")
            except ImportError:
                logger.warning("elevenlabs package not installed")
        else:
            logger.warning("ELEVENLABS_API_KEY not set")

    async def speak(
        self,
        text: str,
        output_path: Optional[Union[str, Path]] = None,
        voice_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Convert text to speech using ElevenLabs"""
        if not self.available:
            return {"error": "ElevenLabs not available"}

        voice = voice_id or self.config.elevenlabs_voice_id

        try:
            audio = self.client.generate(
                text=text, voice=voice, model="eleven_monolingual_v1"
            )

            if output_path:
                with open(output_path, "wb") as f:
                    for chunk in audio:
                        f.write(chunk)
                return {"output_path": str(output_path), "text": text, "voice": voice}
            else:
                # Return audio bytes
                audio_bytes = b"".join(audio)
                return {"audio_bytes": audio_bytes, "text": text, "voice": voice}

        except Exception as e:
            logger.error(f"ElevenLabs TTS failed: {e}")
            return {"error": str(e)}


class EdgeTTS:
    """TTS using edge-tts (free, good quality)"""

    def __init__(self, config: VoiceConfig):
        self.config = config
        self.available = False
        self._check_availability()

    def _check_availability(self):
        """Check if edge-tts is available"""
        try:
            import edge_tts

            self.available = True
            logger.info("edge-tts ready")
        except ImportError:
            logger.warning("edge-tts not installed")

    async def get_voices(self) -> List[Dict[str, str]]:
        """Get available voices"""
        if not self.available:
            return []

        import edge_tts

        voices = await edge_tts.list_voices()
        return [
            {
                "id": v["ShortName"],
                "name": v["FriendlyName"],
                "locale": v["Locale"],
                "gender": v["Gender"],
            }
            for v in voices
        ]

    async def speak(
        self, text: str, output_path: Union[str, Path], voice: str = "en-US-AriaNeural"
    ) -> Dict[str, Any]:
        """Convert text to speech"""
        if not self.available:
            return {"error": "edge-tts not available"}

        try:
            import edge_tts

            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(output_path))

            return {"output_path": str(output_path), "text": text, "voice": voice}

        except Exception as e:
            logger.error(f"edge-tts failed: {e}")
            return {"error": str(e)}


# ============================================================================
# Unified Voice Integration
# ============================================================================


class VoiceIntegration:
    """Unified voice integration"""

    def __init__(self, config: Optional[VoiceConfig] = None):
        self.config = config or VoiceConfig()

        # Initialize STT providers
        self.stt_providers = {}
        self._init_stt()

        # Initialize TTS providers
        self.tts_providers = {}
        self._init_tts()

    def _init_stt(self):
        """Initialize STT providers"""
        # Always try to init faster-whisper first
        faster = FasterWhisperSTT(self.config)
        if faster.available:
            self.stt_providers[STTProvider.FASTER_WHISPER] = faster

        # OpenAI as fallback
        openai = OpenAIWhisperSTT(self.config)
        if openai.available:
            self.stt_providers[STTProvider.OPENAI_WHISPER] = openai

    def _init_tts(self):
        """Initialize TTS providers"""
        # Kokoro ONNX (fast, 54 preset voices - preferred for audiobooks)
        try:
            from integrations.voice_cloning import KokoroONNXBackend

            kokoro = KokoroONNXBackend()
            if kokoro.available:
                self.tts_providers[TTSProvider.KOKORO_ONNX] = kokoro
                logger.info("Kokoro-ONNX TTS ready (54 voices)")
        except ImportError:
            logger.debug("voice_cloning module not available for Kokoro")

        # Coqui XTTS (voice cloning)
        try:
            from integrations.voice_cloning import CoquiXTTSBackend

            xtts = CoquiXTTSBackend()
            if xtts.available:
                self.tts_providers[TTSProvider.COQUI_XTTS] = xtts
                logger.info("Coqui XTTS ready (voice cloning)")
        except ImportError:
            logger.debug("voice_cloning module not available for XTTS")

        # Edge TTS (best free option)
        edge = EdgeTTS(self.config)
        if edge.available:
            self.tts_providers[TTSProvider.EDGE_TTS] = edge

        # pyttsx3 (local, always works)
        pyttsx = Pyttsx3TTS(self.config)
        if pyttsx.available:
            self.tts_providers[TTSProvider.PYTTSX3] = pyttsx

        # ElevenLabs (premium)
        eleven = ElevenLabsTTS(self.config)
        if eleven.available:
            self.tts_providers[TTSProvider.ELEVENLABS] = eleven

    def get_status(self) -> Dict[str, Any]:
        """Get integration status"""
        return {
            "stt_providers": {p.value: True for p in self.stt_providers},
            "tts_providers": {p.value: True for p in self.tts_providers},
            "default_stt": self.config.stt_provider.value,
            "default_tts": self.config.tts_provider.value,
        }

    async def transcribe(
        self,
        audio_path: Union[str, Path],
        provider: Optional[STTProvider] = None,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Transcribe audio to text"""
        provider = provider or self.config.stt_provider

        if provider not in self.stt_providers:
            # Fallback to any available
            if not self.stt_providers:
                return {"error": "No STT providers available"}
            provider = list(self.stt_providers.keys())[0]

        return await self.stt_providers[provider].transcribe(
            audio_path, language=language
        )

    async def speak(
        self,
        text: str,
        output_path: Optional[Union[str, Path]] = None,
        provider: Optional[TTSProvider] = None,
        voice: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Convert text to speech"""
        provider = provider or self.config.tts_provider

        if provider not in self.tts_providers:
            # Fallback order: edge-tts -> pyttsx3 -> elevenlabs
            fallback_order = [
                TTSProvider.EDGE_TTS,
                TTSProvider.PYTTSX3,
                TTSProvider.ELEVENLABS,
            ]
            for p in fallback_order:
                if p in self.tts_providers:
                    provider = p
                    break
            else:
                return {"error": "No TTS providers available"}

        tts = self.tts_providers[provider]

        # Generate output path if not provided
        if output_path is None:
            output_path = Path(tempfile.gettempdir()) / f"tts_{hash(text)}.wav"

        if isinstance(tts, EdgeTTS):
            return await tts.speak(text, output_path, voice or "en-US-AriaNeural")
        elif isinstance(tts, ElevenLabsTTS):
            return await tts.speak(text, output_path, voice)
        else:
            return await tts.speak(text, output_path)

    async def get_voices(
        self, provider: Optional[TTSProvider] = None
    ) -> List[Dict[str, str]]:
        """Get available TTS voices"""
        if provider and provider in self.tts_providers:
            tts = self.tts_providers[provider]
            if hasattr(tts, "get_voices"):
                result = tts.get_voices()
                if asyncio.iscoroutine(result):
                    return await result
                return result

        # Return voices from all providers
        all_voices = []
        for p, tts in self.tts_providers.items():
            if hasattr(tts, "get_voices"):
                result = tts.get_voices()
                if asyncio.iscoroutine(result):
                    voices = await result
                else:
                    voices = result
                for v in voices:
                    v["provider"] = p.value
                    all_voices.append(v)

        return all_voices


# ============================================================================
# MCP Tool Handlers
# ============================================================================

_voice: Optional[VoiceIntegration] = None


def get_voice() -> VoiceIntegration:
    """Get or create voice integration"""
    global _voice
    if _voice is None:
        _voice = VoiceIntegration()
    return _voice


async def handle_transcribe(params: Dict[str, Any]) -> Dict[str, Any]:
    """MCP handler for transcription"""
    voice = get_voice()

    audio_path = params.get("audio_path")
    if not audio_path:
        return {"error": "audio_path required"}

    language = params.get("language")
    provider = params.get("provider")

    if provider:
        provider = STTProvider(provider)

    return await voice.transcribe(audio_path, provider=provider, language=language)


async def handle_speak(params: Dict[str, Any]) -> Dict[str, Any]:
    """MCP handler for text-to-speech"""
    voice = get_voice()

    text = params.get("text")
    if not text:
        return {"error": "text required"}

    output_path = params.get("output_path")
    provider = params.get("provider")
    voice_id = params.get("voice")

    if provider:
        provider = TTSProvider(provider)

    return await voice.speak(text, output_path, provider=provider, voice=voice_id)


async def handle_voice_status(params: Dict[str, Any]) -> Dict[str, Any]:
    """MCP handler for voice status"""
    voice = get_voice()
    return voice.get_status()


async def handle_list_voices(params: Dict[str, Any]) -> Dict[str, Any]:
    """MCP handler for listing voices"""
    voice = get_voice()
    provider = params.get("provider")

    if provider:
        provider = TTSProvider(provider)

    voices = await voice.get_voices(provider)
    return {"voices": voices}


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":

    async def main():
        voice = VoiceIntegration()
        print("Voice Integration Status:")
        print(json.dumps(voice.get_status(), indent=2))

        # Test TTS if available
        if voice.tts_providers:
            result = await voice.speak(
                "Hello, this is a test of the voice integration.", "test_output.wav"
            )
            print("\nTTS Test Result:")
            print(json.dumps(result, indent=2, default=str))

    asyncio.run(main())
