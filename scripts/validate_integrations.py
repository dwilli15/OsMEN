#!/usr/bin/env python3
"""
OsMEN Integration Validation Script

Validates all new integrations and reports their status.

Usage:
    python scripts/validate_integrations.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_header(title: str):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print("=" * 60)


def print_status(name: str, available: bool, details: str = ""):
    """Print status line"""
    icon = "✅" if available else "❌"
    detail_str = f" - {details}" if details else ""
    print(f"  {icon} {name}{detail_str}")


async def validate_system_monitor():
    """Validate system monitor integration"""
    print_header("System Monitor")

    try:
        from integrations.system_monitor import SystemMonitor

        monitor = SystemMonitor()

        # GPU
        gpu_info = monitor.gpu.to_dict()
        print_status(
            "GPU Monitor (NVML)",
            gpu_info["available"],
            (
                f"{gpu_info['gpu_count']} GPU(s)"
                if gpu_info["available"]
                else "pynvml not installed"
            ),
        )

        # Resources (psutil)
        res_info = monitor.resources.get_cpu_info()
        print_status(
            "Resource Monitor (psutil)",
            res_info.get("available", False),
            (
                f"{res_info.get('cores_logical', 0)} cores"
                if res_info.get("available")
                else "psutil not installed"
            ),
        )

        # Task Scheduler
        ts_info = monitor.task_scheduler.to_dict()
        print_status(
            "Task Scheduler (Windows)",
            ts_info["available"],
            (
                f"{ts_info.get('total_tasks', 0)} tasks"
                if ts_info["available"]
                else "pywin32 required"
            ),
        )

        # Startup Apps
        sa_info = monitor.startup_apps.to_dict()
        print_status(
            "Startup Apps (Windows)",
            sa_info["available"],
            (
                f"{sa_info.get('total_entries', 0)} entries"
                if sa_info["available"]
                else "Windows only"
            ),
        )

        return True

    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False


async def validate_voice_audio():
    """Validate voice/audio integration"""
    print_header("Voice/Audio")

    try:
        from integrations.voice_audio import VoiceIntegration

        voice = VoiceIntegration()
        status = voice.get_status()

        # STT providers
        print("\n  Speech-to-Text:")
        for provider, available in status["stt_providers"].items():
            print_status(f"    {provider}", available)

        if not status["stt_providers"]:
            print("    ℹ️  Install faster-whisper: pip install faster-whisper")

        # TTS providers
        print("\n  Text-to-Speech:")
        for provider, available in status["tts_providers"].items():
            print_status(f"    {provider}", available)

        if not status["tts_providers"]:
            print("    ℹ️  Install edge-tts: pip install edge-tts")

        return bool(status["stt_providers"]) or bool(status["tts_providers"])

    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False


async def validate_media():
    """Validate media entertainment integration"""
    print_header("Media Entertainment")

    try:
        from integrations.media_entertainment import MediaIntegration

        media = MediaIntegration()
        status = media.get_status()

        # TMDB
        print_status(
            "TMDB API",
            status["tmdb"]["configured"],
            (
                "API key configured"
                if status["tmdb"]["configured"]
                else "Set TMDB_API_KEY"
            ),
        )

        # Test TMDB if configured
        if status["tmdb"]["configured"]:
            result = await media.search_movies("Test")
            tmdb_working = "error" not in result
            print_status("  └─ API Connection", tmdb_working)

        # OpenSubtitles
        print_status(
            "OpenSubtitles API",
            status["opensubtitles"]["configured"],
            (
                "API key configured"
                if status["opensubtitles"]["configured"]
                else "Set OPENSUBTITLES_API_KEY"
            ),
        )

        return status["tmdb"]["configured"]

    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False


async def validate_creative():
    """Validate creative tools integration"""
    print_header("Creative Tools")

    try:
        from integrations.creative_tools import CreativeIntegration

        creative = CreativeIntegration()
        status = await creative.get_status()

        # InvokeAI
        print_status(
            "InvokeAI",
            status["invokeai"]["available"],
            (
                status["invokeai"]["url"]
                if status["invokeai"]["available"]
                else "Not running"
            ),
        )

        # ComfyUI
        print_status(
            "ComfyUI",
            status["comfyui"]["available"],
            (
                status["comfyui"]["url"]
                if status["comfyui"]["available"]
                else "Not running"
            ),
        )

        # Text-to-3D
        print_status(
            "Text-to-3D",
            status["text_to_3d"]["available"],
            (
                f"Backend: {status['text_to_3d']['backend']}"
                if status["text_to_3d"]["available"]
                else "Install shap-e"
            ),
        )

        await creative.close()
        return status["invokeai"]["available"] or status["comfyui"]["available"]

    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False


async def validate_llm_providers():
    """Validate LLM providers"""
    print_header("LLM Providers")

    try:
        from integrations.llm_providers import LLMConfig, ProviderType

        providers = [
            ("OpenAI", "OPENAI_API_KEY"),
            ("Anthropic", "ANTHROPIC_API_KEY"),
            ("Ollama", "OLLAMA_URL"),
        ]

        available_count = 0
        for name, env_var in providers:
            if env_var == "OLLAMA_URL":
                configured = bool(os.getenv(env_var, "http://localhost:11434"))
            else:
                configured = bool(os.getenv(env_var))

            print_status(
                name, configured, f"${env_var} set" if configured else f"Set {env_var}"
            )

            if configured:
                available_count += 1

        return available_count > 0

    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False


async def validate_mcp_tools():
    """Validate MCP extended tools"""
    print_header("MCP Extended Tools")

    try:
        from gateway.mcp.extended_tools import get_categories, get_extended_tools

        tools = get_extended_tools()
        categories = get_categories()

        print(f"\n  Total tools defined: {len(tools)}")
        print(f"  Categories: {', '.join(categories)}")

        print("\n  Tool distribution:")
        from gateway.mcp.extended_tools import get_tools_by_category

        for cat in categories:
            cat_tools = get_tools_by_category(cat)
            print(f"    {cat}: {len(cat_tools)} tools")

        return len(tools) > 0

    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False


async def main():
    """Run all validations"""
    print("\n" + "=" * 60)
    print(" OsMEN Integration Validation")
    print("=" * 60)

    results = {
        "system_monitor": await validate_system_monitor(),
        "voice_audio": await validate_voice_audio(),
        "media": await validate_media(),
        "creative": await validate_creative(),
        "llm_providers": await validate_llm_providers(),
        "mcp_tools": await validate_mcp_tools(),
    }

    # Summary
    print_header("Summary")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, passed_val in results.items():
        print_status(name.replace("_", " ").title(), passed_val)

    print(f"\n  {passed}/{total} integrations ready")

    if passed < total:
        print("\n  ℹ️  Some integrations need configuration:")
        print("     See .env.example for required API keys")
        print("     Run: pip install -r requirements.txt for dependencies")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
    sys.exit(0 if success else 1)
    sys.exit(0 if success else 1)
