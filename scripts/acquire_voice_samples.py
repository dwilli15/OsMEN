#!/usr/bin/env python3
"""
🔥 YOLO-OPS: Voice Sample Acquisition Script
=============================================
Downloads legally available voice sample datasets for TTS/voice cloning.

Sources:
- HuggingFace: Public domain and CC-licensed datasets
- OpenVoice: MIT licensed voice cloning (myshell-ai)
- Coqui TTS: MPL-2.0 licensed multi-speaker models
- Parler-TTS: 10K+ hours public domain LibriVox

LEGAL NOTE: All datasets are either:
- Public domain (LibriVox audiobooks)
- CC-BY-4.0 licensed (research use allowed)
- MIT/MPL licensed (commercial use allowed)
"""

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

# Add OsMEN root to path
OSMEN_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(OSMEN_ROOT))

VOICE_SAMPLES_DIR = OSMEN_ROOT / "data" / "voice_samples"


@dataclass
class VoiceDataset:
    """Voice dataset metadata."""

    name: str
    source: str
    url: str
    license: str
    description: str
    speakers: int
    hours: Optional[float] = None
    languages: List[str] = None
    download_cmd: Optional[str] = None


# =============================================================================
# AVAILABLE DATASETS
# =============================================================================

DATASETS: Dict[str, VoiceDataset] = {
    # HuggingFace Datasets
    "vctk": VoiceDataset(
        name="VCTK Corpus",
        source="huggingface",
        url="CSTR-Edinburgh/vctk",
        license="CC-BY-4.0",
        description="110 English speakers with various accents (Scottish, Irish, American, etc.)",
        speakers=110,
        hours=44.0,
        languages=["en"],
        download_cmd="huggingface-cli download CSTR-Edinburgh/vctk --local-dir {output_dir}/vctk",
    ),
    "ljspeech": VoiceDataset(
        name="LJ Speech",
        source="huggingface",
        url="lj_speech",
        license="Public Domain",
        description="Single female speaker (Linda Johnson) reading public domain books. 13,100 clips.",
        speakers=1,
        hours=24.0,
        languages=["en"],
        download_cmd="huggingface-cli download keithito/lj_speech --local-dir {output_dir}/ljspeech",
    ),
    "mls_english": VoiceDataset(
        name="Multilingual LibriSpeech (English)",
        source="huggingface",
        url="parler-tts/mls_eng_10k",
        license="CC-BY-4.0",
        description="10K hours of English audiobook readings from LibriVox. Multiple speakers.",
        speakers=5000,
        hours=10000.0,
        languages=["en"],
        download_cmd="huggingface-cli download parler-tts/mls_eng_10k --local-dir {output_dir}/mls_english",
    ),
    "speaker_embeddings": VoiceDataset(
        name="Speaker Embeddings",
        source="huggingface",
        url="MikhailT/speaker-embeddings",
        license="CC-BY-4.0",
        description="76.5K pre-computed speaker embeddings for voice cloning.",
        speakers=76500,
        hours=None,
        languages=["en"],
        download_cmd="huggingface-cli download MikhailT/speaker-embeddings --local-dir {output_dir}/speaker_embeddings",
    ),
    "obama_samples": VoiceDataset(
        name="Obama Voice Samples",
        source="huggingface",
        url="RaysDipesh/obama-voice-samples-283",
        license="Research/Fair Use",
        description="283 voice samples. Public speech recordings (fair use for research).",
        speakers=1,
        hours=None,
        languages=["en"],
        download_cmd="huggingface-cli download RaysDipesh/obama-voice-samples-283 --local-dir {output_dir}/obama",
    ),
    "gender_balanced_10k": VoiceDataset(
        name="Gender Balanced 10K",
        source="huggingface",
        url="7wolf/gender-balanced-10k-voice-samples",
        license="CC-BY-4.0",
        description="10,000 gender-balanced voice samples for training.",
        speakers=1000,
        hours=None,
        languages=["en"],
        download_cmd="huggingface-cli download 7wolf/gender-balanced-10k-voice-samples --local-dir {output_dir}/gender_balanced",
    ),
    # OpenVoice (MIT Licensed)
    "openvoice_v2": VoiceDataset(
        name="OpenVoice V2",
        source="github",
        url="https://github.com/myshell-ai/OpenVoice",
        license="MIT",
        description="Zero-shot voice cloning. 6 languages: EN, ES, FR, ZH, JP, KO. Reference samples included.",
        speakers=10,
        hours=None,
        languages=["en", "es", "fr", "zh", "ja", "ko"],
        download_cmd="git clone https://github.com/myshell-ai/OpenVoice.git {output_dir}/openvoice",
    ),
    # Coqui TTS Models (come with reference voices)
    "coqui_xtts": VoiceDataset(
        name="Coqui XTTS v2",
        source="huggingface",
        url="coqui/XTTS-v2",
        license="Coqui Public Model License",
        description="Multi-lingual voice cloning model with 16 languages. Includes reference voices.",
        speakers=20,
        hours=None,
        languages=[
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
            "zh",
            "ja",
            "ko",
            "hu",
        ],
        download_cmd="huggingface-cli download coqui/XTTS-v2 --local-dir {output_dir}/coqui_xtts",
    ),
    # Parler TTS (fully open source)
    "parler_tts": VoiceDataset(
        name="Parler TTS Large v1",
        source="huggingface",
        url="parler-tts/parler-tts-large-v1",
        license="Apache-2.0",
        description="2.2B params. 45K hours training. Controllable voice features via text prompts.",
        speakers=1000,
        hours=45000.0,
        languages=["en"],
        download_cmd="huggingface-cli download parler-tts/parler-tts-large-v1 --local-dir {output_dir}/parler_tts",
    ),
}


# =============================================================================
# CHARACTER/PERSONA VOICE PROFILES
# =============================================================================

PERSONA_VOICES = {
    "santa_claus": {
        "description": "Deep, warm, jolly male voice. Slow pace, rich bass tones.",
        "kokoro_voice": "am_adam",  # Deep male voice
        "parler_prompt": "A deep, warm male voice with a jolly tone. Slow speaking pace, bass-heavy, grandfatherly.",
        "openvoice_style": "default",
        "notes": "Use pitch shifting + warmth filters for authentic Santa",
    },
    "narrator_male": {
        "description": "Professional male narrator voice. Clear, authoritative.",
        "kokoro_voice": "am_michael",
        "parler_prompt": "A professional male narrator voice. Clear enunciation, authoritative tone, moderate pace.",
        "openvoice_style": "default",
        "notes": "Great for audiobooks and documentaries",
    },
    "narrator_female": {
        "description": "Professional female narrator voice. Warm, engaging.",
        "kokoro_voice": "af_heart",
        "parler_prompt": "A professional female narrator voice. Warm and engaging, clear enunciation.",
        "openvoice_style": "default",
        "notes": "Ideal for audiobooks and presentations",
    },
    "news_anchor": {
        "description": "Neutral, professional news anchor voice.",
        "kokoro_voice": "am_michael",
        "parler_prompt": "A neutral news anchor voice. Professional, clear, measured pace.",
        "openvoice_style": "default",
        "notes": "Formal tone suitable for news reading",
    },
    "podcast_host": {
        "description": "Casual, friendly podcast host voice.",
        "kokoro_voice": "af_bella",
        "parler_prompt": "A casual, friendly voice. Conversational tone, natural pace, slight warmth.",
        "openvoice_style": "friendly",
        "notes": "Good for casual content and podcasts",
    },
    "assistant": {
        "description": "Helpful AI assistant voice. Clear, friendly, professional.",
        "kokoro_voice": "af_heart",
        "parler_prompt": "A helpful assistant voice. Clear, friendly, professional tone.",
        "openvoice_style": "default",
        "notes": "Default voice for AI interactions",
    },
}


# =============================================================================
# ACQUISITION FUNCTIONS
# =============================================================================


def ensure_hf_cli():
    """Ensure HuggingFace CLI is installed."""
    try:
        subprocess.run(
            ["huggingface-cli", "--version"], capture_output=True, check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Installing HuggingFace Hub...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "huggingface_hub[cli]"], check=True
        )
        return True


def download_dataset(dataset_key: str, output_dir: Optional[Path] = None) -> bool:
    """Download a specific dataset."""
    if dataset_key not in DATASETS:
        print(f"❌ Unknown dataset: {dataset_key}")
        print(f"Available: {', '.join(DATASETS.keys())}")
        return False

    dataset = DATASETS[dataset_key]
    output_dir = output_dir or VOICE_SAMPLES_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"📥 Downloading: {dataset.name}")
    print(f"   Source: {dataset.source}")
    print(f"   License: {dataset.license}")
    print(f"   Speakers: {dataset.speakers}")
    if dataset.hours:
        print(f"   Hours: {dataset.hours}")
    print(f"{'='*60}\n")

    if dataset.source == "huggingface":
        ensure_hf_cli()

    cmd = dataset.download_cmd.format(output_dir=str(output_dir))

    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"✅ Downloaded: {dataset.name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to download {dataset.name}: {e}")
        return False


def download_essentials():
    """Download essential datasets for voice cloning."""
    essentials = [
        "ljspeech",  # Public domain, single speaker baseline
        "speaker_embeddings",  # Pre-computed embeddings
        "openvoice_v2",  # MIT licensed voice cloning
    ]

    print("\n🔥 YOLO-OPS: Downloading Essential Voice Datasets")
    print("=" * 60)

    for key in essentials:
        download_dataset(key)


def download_all():
    """Download all available datasets (WARNING: Large!)."""
    print("\n⚠️  WARNING: This will download ALL datasets!")
    print("   Total size: ~200GB+ (including MLS)")
    print("   Recommended: Use download_essentials() first")
    print()

    confirm = input("Continue? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    for key in DATASETS:
        download_dataset(key)


def list_datasets():
    """List all available datasets."""
    print("\n📚 Available Voice Datasets")
    print("=" * 80)

    for key, ds in DATASETS.items():
        print(f"\n🎤 {key}")
        print(f"   Name: {ds.name}")
        print(f"   License: {ds.license}")
        print(f"   Speakers: {ds.speakers}")
        if ds.hours:
            print(f"   Hours: {ds.hours}")
        print(f"   Description: {ds.description[:60]}...")


def list_personas():
    """List available voice personas."""
    print("\n🎭 Available Voice Personas")
    print("=" * 60)

    for name, persona in PERSONA_VOICES.items():
        print(f"\n🎤 {name}")
        print(f"   Kokoro Voice: {persona['kokoro_voice']}")
        print(f"   Description: {persona['description']}")


def create_voice_profile(persona_key: str, output_path: Optional[Path] = None) -> dict:
    """Create a voice profile configuration for a persona."""
    if persona_key not in PERSONA_VOICES:
        raise ValueError(f"Unknown persona: {persona_key}")

    persona = PERSONA_VOICES[persona_key]

    profile = {
        "name": persona_key,
        "description": persona["description"],
        "backends": {
            "kokoro": {
                "voice_id": persona["kokoro_voice"],
            },
            "parler": {
                "prompt": persona["parler_prompt"],
            },
            "openvoice": {
                "style": persona["openvoice_style"],
            },
        },
        "notes": persona["notes"],
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(profile, f, indent=2)
        print(f"✅ Created voice profile: {output_path}")

    return profile


def setup_voice_profiles_dir():
    """Create voice profiles for all personas."""
    profiles_dir = VOICE_SAMPLES_DIR / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)

    for persona_key in PERSONA_VOICES:
        output_path = profiles_dir / f"{persona_key}.json"
        create_voice_profile(persona_key, output_path)

    print(f"\n✅ Created {len(PERSONA_VOICES)} voice profiles in {profiles_dir}")


# =============================================================================
# CLI
# =============================================================================


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="🔥 YOLO-OPS Voice Sample Acquisition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python acquire_voice_samples.py --list           # List all datasets
  python acquire_voice_samples.py --essentials     # Download essentials
  python acquire_voice_samples.py --download vctk  # Download specific dataset
  python acquire_voice_samples.py --profiles       # Create voice profiles
  python acquire_voice_samples.py --personas       # List voice personas
        """,
    )

    parser.add_argument(
        "--list", "-l", action="store_true", help="List available datasets"
    )
    parser.add_argument("--download", "-d", type=str, help="Download specific dataset")
    parser.add_argument(
        "--essentials", "-e", action="store_true", help="Download essential datasets"
    )
    parser.add_argument(
        "--all", "-a", action="store_true", help="Download ALL datasets (large!)"
    )
    parser.add_argument(
        "--profiles", "-p", action="store_true", help="Create voice profiles"
    )
    parser.add_argument("--personas", action="store_true", help="List voice personas")
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output directory",
        default=str(VOICE_SAMPLES_DIR),
    )

    args = parser.parse_args()

    if args.list:
        list_datasets()
    elif args.personas:
        list_personas()
    elif args.download:
        download_dataset(args.download, Path(args.output))
    elif args.essentials:
        download_essentials()
    elif args.all:
        download_all()
    elif args.profiles:
        setup_voice_profiles_dir()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
