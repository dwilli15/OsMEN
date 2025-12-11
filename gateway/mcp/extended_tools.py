#!/usr/bin/env python3
"""
OsMEN Extended MCP Tools

Additional MCP tool definitions for new integrations:
- System Monitor (GPU, RAM, Task Scheduler, Startup Apps)
- Voice/Audio (STT, TTS)
- Media Entertainment (TMDB, Subtitles)
- Creative Tools (InvokeAI, ComfyUI, Text-to-3D)
"""

from typing import Any, Dict, List

# ============================================================================
# System Monitor Tools
# ============================================================================

SYSTEM_MONITOR_TOOLS = [
    {
        "name": "system_status",
        "description": "Get comprehensive system status including GPU, CPU, RAM, disks, and alerts",
        "inputSchema": {
            "type": "object",
            "properties": {
                "include": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "all",
                            "gpu",
                            "resources",
                            "tasks",
                            "startup",
                            "alerts",
                        ],
                    },
                    "description": "What to include in status (default: all)",
                }
            },
        },
        "category": "system",
    },
    {
        "name": "gpu_status",
        "description": "Get NVIDIA GPU status (VRAM usage, temperature, utilization)",
        "inputSchema": {"type": "object", "properties": {}},
        "category": "system",
    },
    {
        "name": "task_scheduler",
        "description": "Monitor Windows Task Scheduler (list tasks, check failures)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["status", "list", "failed"],
                    "description": "Action: status (summary), list (all tasks), failed (failed tasks only)",
                }
            },
        },
        "category": "system",
    },
    {
        "name": "startup_apps",
        "description": "List Windows startup applications from registry and startup folders",
        "inputSchema": {"type": "object", "properties": {}},
        "category": "system",
    },
    {
        "name": "resource_monitor",
        "description": "Get CPU, memory, disk usage and top processes",
        "inputSchema": {
            "type": "object",
            "properties": {
                "include": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["cpu", "memory", "disks", "processes"],
                    },
                    "description": "What to include (default: all)",
                }
            },
        },
        "category": "system",
    },
]


# ============================================================================
# Voice/Audio Tools
# ============================================================================

VOICE_AUDIO_TOOLS = [
    {
        "name": "voice_transcribe",
        "description": "Transcribe audio to text using Whisper (local or API)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "audio_path": {
                    "type": "string",
                    "description": "Path to audio file (wav, mp3, etc.)",
                },
                "language": {
                    "type": "string",
                    "description": "Language code (e.g., 'en', 'es') or auto-detect",
                },
                "provider": {
                    "type": "string",
                    "enum": ["faster_whisper", "openai_whisper"],
                    "description": "STT provider (default: faster_whisper)",
                },
            },
            "required": ["audio_path"],
        },
        "category": "voice",
    },
    {
        "name": "voice_speak",
        "description": "Convert text to speech audio",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to speak"},
                "output_path": {
                    "type": "string",
                    "description": "Path to save audio (optional, generates temp file if not provided)",
                },
                "provider": {
                    "type": "string",
                    "enum": ["edge_tts", "pyttsx3", "elevenlabs"],
                    "description": "TTS provider (default: edge_tts)",
                },
                "voice": {
                    "type": "string",
                    "description": "Voice ID (provider-specific)",
                },
            },
            "required": ["text"],
        },
        "category": "voice",
    },
    {
        "name": "voice_list_voices",
        "description": "List available TTS voices",
        "inputSchema": {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "enum": ["edge_tts", "pyttsx3", "elevenlabs"],
                    "description": "TTS provider to list voices for",
                }
            },
        },
        "category": "voice",
    },
    {
        "name": "voice_status",
        "description": "Get voice integration status (available providers)",
        "inputSchema": {"type": "object", "properties": {}},
        "category": "voice",
    },
]


# ============================================================================
# Media Entertainment Tools
# ============================================================================

MEDIA_ENTERTAINMENT_TOOLS = [
    {
        "name": "tmdb_search_movies",
        "description": "Search for movies on TMDB",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Movie title to search"},
                "year": {"type": "integer", "description": "Filter by release year"},
                "page": {"type": "integer", "description": "Page number (default: 1)"},
            },
            "required": ["query"],
        },
        "category": "media",
    },
    {
        "name": "tmdb_search_tv",
        "description": "Search for TV shows on TMDB",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "TV show title to search"},
                "year": {"type": "integer", "description": "Filter by first air year"},
                "page": {"type": "integer", "description": "Page number (default: 1)"},
            },
            "required": ["query"],
        },
        "category": "media",
    },
    {
        "name": "tmdb_get_movie",
        "description": "Get detailed movie information from TMDB",
        "inputSchema": {
            "type": "object",
            "properties": {
                "movie_id": {"type": "integer", "description": "TMDB movie ID"},
                "imdb_id": {
                    "type": "string",
                    "description": "IMDB ID (e.g., tt1375666)",
                },
            },
        },
        "category": "media",
    },
    {
        "name": "tmdb_trending",
        "description": "Get trending movies or TV shows",
        "inputSchema": {
            "type": "object",
            "properties": {
                "media_type": {
                    "type": "string",
                    "enum": ["movie", "tv", "all"],
                    "description": "Type of media (default: movie)",
                },
                "time_window": {
                    "type": "string",
                    "enum": ["day", "week"],
                    "description": "Time window (default: week)",
                },
            },
        },
        "category": "media",
    },
    {
        "name": "subtitle_search",
        "description": "Search for subtitles on OpenSubtitles",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Movie/show title to search",
                },
                "imdb_id": {"type": "string", "description": "IMDB ID for exact match"},
                "tmdb_id": {
                    "type": "integer",
                    "description": "TMDB ID for exact match",
                },
                "languages": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Language codes (default: ['en'])",
                },
                "season": {
                    "type": "integer",
                    "description": "Season number for TV shows",
                },
                "episode": {
                    "type": "integer",
                    "description": "Episode number for TV shows",
                },
            },
        },
        "category": "media",
    },
    {
        "name": "subtitle_download",
        "description": "Download a subtitle file from OpenSubtitles",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "integer",
                    "description": "Subtitle file ID from search results",
                },
                "output_path": {
                    "type": "string",
                    "description": "Path to save the subtitle file",
                },
            },
            "required": ["file_id", "output_path"],
        },
        "category": "media",
    },
    {
        "name": "media_status",
        "description": "Get media integration status (TMDB, OpenSubtitles)",
        "inputSchema": {"type": "object", "properties": {}},
        "category": "media",
    },
]


# ============================================================================
# Creative Tools
# ============================================================================

CREATIVE_TOOLS = [
    {
        "name": "generate_image",
        "description": "Generate image using Stable Diffusion (InvokeAI or ComfyUI)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Text description of image to generate",
                },
                "negative_prompt": {
                    "type": "string",
                    "description": "What to avoid in the image",
                },
                "output_path": {
                    "type": "string",
                    "description": "Path to save the image",
                },
                "width": {
                    "type": "integer",
                    "description": "Image width (default: 1024)",
                },
                "height": {
                    "type": "integer",
                    "description": "Image height (default: 1024)",
                },
                "steps": {
                    "type": "integer",
                    "description": "Number of inference steps (default: 30)",
                },
                "cfg_scale": {
                    "type": "number",
                    "description": "Classifier-free guidance scale (default: 7.5)",
                },
                "seed": {
                    "type": "integer",
                    "description": "Random seed (-1 for random)",
                },
            },
            "required": ["prompt"],
        },
        "category": "creative",
    },
    {
        "name": "generate_3d_model",
        "description": "Generate 3D model from text description (requires Shap-E or Meshy.ai)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Text description of 3D model to generate",
                },
                "output_path": {
                    "type": "string",
                    "description": "Path to save the 3D model",
                },
                "format": {
                    "type": "string",
                    "enum": ["stl", "obj", "ply", "glb"],
                    "description": "Output format (default: stl)",
                },
            },
            "required": ["prompt", "output_path"],
        },
        "category": "creative",
    },
    {
        "name": "creative_status",
        "description": "Get creative tools status (InvokeAI, ComfyUI, Text-to-3D)",
        "inputSchema": {"type": "object", "properties": {}},
        "category": "creative",
    },
    {
        "name": "list_sd_models",
        "description": "List available Stable Diffusion models",
        "inputSchema": {"type": "object", "properties": {}},
        "category": "creative",
    },
]


# ============================================================================
# All Extended Tools
# ============================================================================

EXTENDED_TOOLS = (
    SYSTEM_MONITOR_TOOLS
    + VOICE_AUDIO_TOOLS
    + MEDIA_ENTERTAINMENT_TOOLS
    + CREATIVE_TOOLS
)


def get_extended_tools() -> List[Dict[str, Any]]:
    """Get all extended tool definitions"""
    return EXTENDED_TOOLS


def get_tools_by_category(category: str) -> List[Dict[str, Any]]:
    """Get tools by category"""
    return [t for t in EXTENDED_TOOLS if t.get("category") == category]


def get_categories() -> List[str]:
    """Get all tool categories"""
    return list(set(t.get("category", "other") for t in EXTENDED_TOOLS))


# ============================================================================
# Tool Dispatcher
# ============================================================================


async def dispatch_tool(name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch tool call to appropriate handler"""

    # System Monitor tools
    if name == "system_status":
        from integrations.system_monitor import handle_system_status

        return await handle_system_status(params)

    elif name == "gpu_status":
        from integrations.system_monitor import handle_gpu_status

        return await handle_gpu_status(params)

    elif name == "task_scheduler":
        from integrations.system_monitor import handle_task_scheduler

        return await handle_task_scheduler(params)

    elif name == "startup_apps":
        from integrations.system_monitor import handle_startup_apps

        return await handle_startup_apps(params)

    elif name == "resource_monitor":
        from integrations.system_monitor import handle_system_status

        params["include"] = params.get(
            "include", ["cpu", "memory", "disks", "processes"]
        )
        return await handle_system_status(params)

    # Voice tools
    elif name == "voice_transcribe":
        from integrations.voice_audio import handle_transcribe

        return await handle_transcribe(params)

    elif name == "voice_speak":
        from integrations.voice_audio import handle_speak

        return await handle_speak(params)

    elif name == "voice_list_voices":
        from integrations.voice_audio import handle_list_voices

        return await handle_list_voices(params)

    elif name == "voice_status":
        from integrations.voice_audio import handle_voice_status

        return await handle_voice_status(params)

    # Media tools
    elif name == "tmdb_search_movies":
        from integrations.media_entertainment import handle_search_movies

        return await handle_search_movies(params)

    elif name == "tmdb_search_tv":
        from integrations.media_entertainment import handle_search_tv

        return await handle_search_tv(params)

    elif name == "tmdb_get_movie":
        from integrations.media_entertainment import handle_get_movie

        return await handle_get_movie(params)

    elif name == "tmdb_trending":
        from integrations.media_entertainment import handle_search_movies

        # Use trending endpoint
        params["trending"] = True
        return await handle_search_movies(params)

    elif name == "subtitle_search":
        from integrations.media_entertainment import handle_search_subtitles

        return await handle_search_subtitles(params)

    elif name == "subtitle_download":
        from integrations.media_entertainment import handle_download_subtitle

        return await handle_download_subtitle(params)

    elif name == "media_status":
        from integrations.media_entertainment import handle_media_status

        return await handle_media_status(params)

    # Creative tools
    elif name == "generate_image":
        from integrations.creative_tools import handle_generate_image

        return await handle_generate_image(params)

    elif name == "generate_3d_model":
        from integrations.creative_tools import handle_generate_3d

        return await handle_generate_3d(params)

    elif name == "creative_status":
        from integrations.creative_tools import handle_creative_status

        return await handle_creative_status(params)

    elif name == "list_sd_models":
        from integrations.creative_tools import handle_list_models

        return await handle_list_models(params)

    else:
        return {"error": f"Unknown tool: {name}"}


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import json

    print("Extended MCP Tools")
    print("=" * 50)

    for category in get_categories():
        tools = get_tools_by_category(category)
        print(f"\n{category.upper()} ({len(tools)} tools):")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description'][:60]}...")

    print(f"\nTotal: {len(EXTENDED_TOOLS)} tools")
