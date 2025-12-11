#!/usr/bin/env python3
"""
🔥 Voice Sample Library Integration for OsMEN VoiceCloner
=========================================================

Provides access to downloaded voice samples for TTS/voice cloning.
Works with:
- OpenVoice (MIT licensed)
- Obama samples (283 files)
- Gender Balanced 10K (parquet format)
- Custom voice profiles

Usage:
    from integrations.voice_library import VoiceLibrary

    lib = VoiceLibrary()
    lib.list_available()

    # Get a sample for cloning
    sample = lib.get_sample("obama", index=0)

    # Use with VoiceCloner
    from integrations.voice_cloning import VoiceCloner
    cloner = VoiceCloner()
    audio = cloner.synthesize("Hello!", reference_audio=sample)
"""

import json
import os
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add OsMEN root to path
OSMEN_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(OSMEN_ROOT))

VOICE_SAMPLES_DIR = OSMEN_ROOT / "data" / "voice_samples"


@dataclass
class VoiceSample:
    """A voice sample with metadata."""

    path: Path
    name: str
    collection: str
    format: str
    duration: Optional[float] = None
    metadata: Optional[Dict] = None


class VoiceLibrary:
    """Manages downloaded voice samples for cloning."""

    def __init__(self, samples_dir: Optional[Path] = None):
        self.samples_dir = samples_dir or VOICE_SAMPLES_DIR
        self._collections: Dict[str, List[VoiceSample]] = {}
        self._profiles: Dict[str, Dict] = {}
        self._load_collections()
        self._load_profiles()

    def _load_collections(self):
        """Scan and load all voice sample collections."""
        if not self.samples_dir.exists():
            return

        # Obama samples - check multiple possible paths
        obama_paths = [
            self.samples_dir / "obama" / "data",
            self.samples_dir / "obama" / "obama-voice-samples-283" / "wavs",
            self.samples_dir / "obama",
        ]
        for obama_dir in obama_paths:
            if obama_dir.exists():
                wavs = list(obama_dir.glob("*.wav"))
                if wavs:
                    self._collections["obama"] = []
                    for wav in sorted(wavs):
                        self._collections["obama"].append(
                            VoiceSample(
                                path=wav,
                                name=wav.stem,
                                collection="obama",
                                format="wav",
                            )
                        )
                    break

        # OpenVoice reference samples
        openvoice_dir = self.samples_dir / "openvoice" / "resources"
        if openvoice_dir.exists():
            self._collections["openvoice"] = []
            for audio in sorted(openvoice_dir.glob("*.mp3")):
                self._collections["openvoice"].append(
                    VoiceSample(
                        path=audio,
                        name=audio.stem,
                        collection="openvoice",
                        format="mp3",
                    )
                )

        # Check for custom samples
        custom_dir = self.samples_dir / "custom"
        if custom_dir.exists():
            self._collections["custom"] = []
            for audio in custom_dir.glob("*.wav"):
                self._collections["custom"].append(
                    VoiceSample(
                        path=audio, name=audio.stem, collection="custom", format="wav"
                    )
                )
            for audio in custom_dir.glob("*.mp3"):
                self._collections["custom"].append(
                    VoiceSample(
                        path=audio, name=audio.stem, collection="custom", format="mp3"
                    )
                )

    def _load_profiles(self):
        """Load voice profiles."""
        profiles_dir = self.samples_dir / "profiles"
        if not profiles_dir.exists():
            return

        for profile_file in profiles_dir.glob("*.json"):
            with open(profile_file) as f:
                self._profiles[profile_file.stem] = json.load(f)

    def list_collections(self) -> List[str]:
        """List available voice sample collections."""
        return list(self._collections.keys())

    def list_profiles(self) -> List[str]:
        """List available voice profiles."""
        return list(self._profiles.keys())

    def get_collection(self, name: str) -> List[VoiceSample]:
        """Get all samples from a collection."""
        return self._collections.get(name, [])

    def get_profile(self, name: str) -> Optional[Dict]:
        """Get a voice profile configuration."""
        return self._profiles.get(name)

    def get_sample(self, collection: str, index: int = 0) -> Optional[Path]:
        """Get a specific sample by index from a collection."""
        samples = self._collections.get(collection, [])
        if 0 <= index < len(samples):
            return samples[index].path
        return None

    def get_random_sample(self, collection: str) -> Optional[Path]:
        """Get a random sample from a collection."""
        samples = self._collections.get(collection, [])
        if samples:
            return random.choice(samples).path
        return None

    def search_samples(self, query: str) -> List[VoiceSample]:
        """Search for samples by name across all collections."""
        results = []
        query_lower = query.lower()

        for collection_name, samples in self._collections.items():
            for sample in samples:
                if query_lower in sample.name.lower():
                    results.append(sample)

        return results

    def get_sample_count(self, collection: Optional[str] = None) -> int:
        """Get count of samples in a collection or total."""
        if collection:
            return len(self._collections.get(collection, []))
        return sum(len(samples) for samples in self._collections.values())

    def summary(self) -> Dict[str, int]:
        """Get summary of all collections."""
        return {name: len(samples) for name, samples in self._collections.items()}

    def __repr__(self):
        total = self.get_sample_count()
        collections = len(self._collections)
        profiles = len(self._profiles)
        return f"VoiceLibrary({collections} collections, {total} samples, {profiles} profiles)"


# =============================================================================
# PERSONA MAPPING
# =============================================================================

KOKORO_VOICE_MAP = {
    # American Female
    "af_heart": "Heart - American Female (warm, expressive)",
    "af_bella": "Bella - American Female (casual, friendly)",
    "af_nicole": "Nicole - American Female (professional)",
    "af_sarah": "Sarah - American Female (young, energetic)",
    "af_sky": "Sky - American Female (calm, soothing)",
    # American Male
    "am_adam": "Adam - American Male (deep, authoritative)",
    "am_michael": "Michael - American Male (professional, clear)",
    # British Female
    "bf_emma": "Emma - British Female (refined)",
    "bf_isabella": "Isabella - British Female (warm)",
    # British Male
    "bm_george": "George - British Male (distinguished)",
    "bm_lewis": "Lewis - British Male (casual)",
}


def get_voice_for_persona(persona: str) -> Tuple[str, str]:
    """
    Get recommended Kokoro voice for a persona type.

    Returns:
        Tuple of (voice_id, description)
    """
    persona_mapping = {
        # Character Types
        "santa": ("am_adam", "Deep, warm male - use pitch down + warmth"),
        "narrator": ("af_heart", "Professional narration voice"),
        "news": ("am_michael", "Clear, professional news anchor"),
        "podcast": ("af_bella", "Casual, friendly host"),
        "assistant": ("af_heart", "Helpful AI voice"),
        "teacher": ("af_nicole", "Clear, educational"),
        "storyteller": ("bf_emma", "Engaging, expressive"),
        # Tone Types
        "authoritative": ("am_adam", "Deep, commanding"),
        "friendly": ("af_bella", "Warm, approachable"),
        "professional": ("am_michael", "Clear, business-like"),
        "calm": ("af_sky", "Soothing, peaceful"),
        "energetic": ("af_sarah", "Bright, dynamic"),
        # Language/Accent
        "british": ("bf_emma", "British accent"),
        "american": ("af_heart", "American accent"),
    }

    persona_lower = persona.lower()

    # Direct match
    if persona_lower in persona_mapping:
        return persona_mapping[persona_lower]

    # Partial match
    for key, value in persona_mapping.items():
        if key in persona_lower or persona_lower in key:
            return value

    # Default
    return ("af_heart", "Default voice")


# =============================================================================
# CLI
# =============================================================================


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Voice Sample Library")
    parser.add_argument(
        "--list", "-l", action="store_true", help="List all collections"
    )
    parser.add_argument("--summary", "-s", action="store_true", help="Show summary")
    parser.add_argument(
        "--collection", "-c", type=str, help="List samples in collection"
    )
    parser.add_argument("--profiles", "-p", action="store_true", help="List profiles")
    parser.add_argument(
        "--voices", "-v", action="store_true", help="List Kokoro voices"
    )

    args = parser.parse_args()

    lib = VoiceLibrary()

    if args.list:
        print(f"\n📚 Voice Sample Collections")
        print("=" * 40)
        for name in lib.list_collections():
            count = lib.get_sample_count(name)
            print(f"  🎤 {name}: {count} samples")

    elif args.summary:
        print(f"\n{lib}")
        print("\n📊 Collection Summary:")
        for name, count in lib.summary().items():
            print(f"  {name}: {count}")

    elif args.collection:
        samples = lib.get_collection(args.collection)
        if not samples:
            print(f"❌ Collection not found: {args.collection}")
            return
        print(f"\n🎤 {args.collection} ({len(samples)} samples)")
        print("=" * 40)
        for i, sample in enumerate(samples[:20]):
            print(f"  [{i}] {sample.name}")
        if len(samples) > 20:
            print(f"  ... and {len(samples) - 20} more")

    elif args.profiles:
        print("\n🎭 Voice Profiles")
        print("=" * 40)
        for name in lib.list_profiles():
            profile = lib.get_profile(name)
            print(f"\n  {name}:")
            print(f"    Description: {profile.get('description', 'N/A')}")
            if "backends" in profile and "kokoro" in profile["backends"]:
                print(f"    Kokoro Voice: {profile['backends']['kokoro']['voice_id']}")

    elif args.voices:
        print("\n🎤 Kokoro Voice Map")
        print("=" * 50)
        for voice_id, description in KOKORO_VOICE_MAP.items():
            print(f"  {voice_id}: {description}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
