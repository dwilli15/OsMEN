"""OsMEN Integrations Package

This package contains integrations with external services and APIs.

=============================================================================
ORCHESTRATION LAYER - SINGLE SOURCE OF TRUTH
=============================================================================

The orchestration module is the central configuration hub for all OsMEN components.
ALL agents and workflows should import from here for consistency.

    from integrations.orchestration import OsMEN, Paths, Pipelines, Services

Path Hierarchy (to avoid circular imports):
1. integrations/paths.py - Base path constants (no dependencies)
2. integrations/orchestration.py - Full orchestration layer (imports paths.py)
3. integrations/logging_system.py - Logging system (imports paths.py)
4. All agents - Import from orchestration.py

=============================================================================

Modules:
- paths: Base path constants (imported by orchestration and logging)
- orchestration: Central configuration, pipelines, agents, services
- logging_system: Agent logging, check-in tracking, audio generation logs
- system_monitor: GPU, CPU, RAM, Task Scheduler, Startup Apps monitoring
- voice_audio: STT (Whisper) and TTS (Edge TTS, pyttsx3, ElevenLabs)
- media_entertainment: TMDB API, OpenSubtitles
- creative_tools: InvokeAI, ComfyUI, Text-to-3D
- llm_providers: Unified LLM interface (OpenAI, Anthropic, Ollama)
- obsidian_enhanced: Enhanced Obsidian with ChromaDB sync, semantic search
- embedding_optimizer: Multi-model embedding with caching
- yolo: YOLO Tools unified interface
"""

# =============================================================================
# ORCHESTRATION - Import first for configuration
# =============================================================================

# Creative Tools
from integrations.creative_tools import (
    CreativeConfig,
    CreativeIntegration,
    InvokeAIClient,
)

# Embeddings
from integrations.embedding_optimizer import (
    ChromaDBEmbeddingFunction,
    EmbeddingCache,
    EmbeddingModel,
    EmbeddingProvider,
)

# Core integrations
from integrations.llm_providers import LLMConfig, ProviderType, get_llm_provider
from integrations.logging_system import (
    AgentLogger,
    AudioGenerationLog,
    CheckInTracker,
    SystemEventLog,
    agent_startup_check,
    get_recent_context,
)

# Media/Entertainment
from integrations.media_entertainment import (
    MediaConfig,
    MediaIntegration,
    OpenSubtitlesClient,
    TMDBClient,
)

# Obsidian Enhanced
from integrations.obsidian_enhanced import (
    EnhancedObsidianIntegration,
    ObsidianConfig,
    ObsidianNote,
)
from integrations.orchestration import (
    Agents,
    OsMEN,
    Paths,
    Pipelines,
    Services,
    Templates,
    Trackers,
    Workflows,
    get_pipeline,
)
from integrations.paths import (
    CONTENT_ROOT,
    HB411_OBSIDIAN,
    HB411_ROOT,
    LOGS_ROOT,
    OSMEN_ROOT,
)

# RAG Pipeline
from integrations.rag_pipeline import (
    BM25Retriever,
    CrossEncoderReranker,
    EnhancedRAGPipeline,
    QueryExpander,
    RAGConfig,
    RetrievalResult,
    create_chromadb_rag_pipeline,
)

# System monitoring
from integrations.system_monitor import (
    GPUMonitor,
    ResourceMonitor,
    StartupAppsMonitor,
    SystemMonitor,
    TaskSchedulerMonitor,
)

# Voice/Audio
from integrations.voice_audio import (
    STTProvider,
    TTSProvider,
    VoiceConfig,
    VoiceIntegration,
)

__all__ = [
    # Orchestration (NEW - Primary exports)
    "OsMEN",
    "Paths",
    "Pipelines",
    "Services",
    "Agents",
    "Workflows",
    "Templates",
    "Trackers",
    "get_pipeline",
    # Logging
    "AgentLogger",
    "CheckInTracker",
    "AudioGenerationLog",
    "SystemEventLog",
    "agent_startup_check",
    "get_recent_context",
    # Path constants
    "OSMEN_ROOT",
    "CONTENT_ROOT",
    "LOGS_ROOT",
    "HB411_ROOT",
    "HB411_OBSIDIAN",
    # LLM
    "LLMConfig",
    "ProviderType",
    "get_llm_provider",
    # System
    "SystemMonitor",
    "GPUMonitor",
    "ResourceMonitor",
    "TaskSchedulerMonitor",
    "StartupAppsMonitor",
    # Voice
    "VoiceIntegration",
    "VoiceConfig",
    "STTProvider",
    "TTSProvider",
    # Media
    "MediaIntegration",
    "MediaConfig",
    "TMDBClient",
    "OpenSubtitlesClient",
    # Creative
    "CreativeIntegration",
    "CreativeConfig",
    "InvokeAIClient",
    # Obsidian
    "EnhancedObsidianIntegration",
    "ObsidianConfig",
    "ObsidianNote",
    # Embeddings
    "EmbeddingProvider",
    "EmbeddingModel",
    "EmbeddingCache",
    "ChromaDBEmbeddingFunction",
    # RAG Pipeline
    "EnhancedRAGPipeline",
    "RAGConfig",
    "RetrievalResult",
    "BM25Retriever",
    "CrossEncoderReranker",
    "QueryExpander",
    "create_chromadb_rag_pipeline",
]
