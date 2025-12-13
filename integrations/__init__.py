"""OsMEN integrations.

Important: keep package import *lightweight*.

This repository has optional, heavyweight integrations (e.g., embedding models,
LLM SDKs, media tools). Historically, importing `integrations` eagerly imported
many of them. That creates real failures:

- `from integrations.paths import ...` first imports `integrations/__init__.py`,
  so eager imports can break the gateway container if optional deps aren't
  installed.
- Startup can appear to “hang” locally while importing torch/transformers/etc.

To avoid that, this package now lazily resolves top-level exports via
`__getattr__` (PEP 562). Import the specific submodule directly when you can:

    from integrations.paths import get_vault_root
    from integrations.orchestration import OsMEN
"""

from __future__ import annotations

import importlib
from typing import Any, Dict, Tuple

_LAZY_EXPORTS: Dict[str, Tuple[str, str]] = {
    # Orchestration
    "OsMEN": ("integrations.orchestration", "OsMEN"),
    "Paths": ("integrations.orchestration", "Paths"),
    "Pipelines": ("integrations.orchestration", "Pipelines"),
    "Services": ("integrations.orchestration", "Services"),
    "Agents": ("integrations.orchestration", "Agents"),
    "Workflows": ("integrations.orchestration", "Workflows"),
    "Templates": ("integrations.orchestration", "Templates"),
    "Trackers": ("integrations.orchestration", "Trackers"),
    "get_pipeline": ("integrations.orchestration", "get_pipeline"),
    # Paths
    "OSMEN_ROOT": ("integrations.paths", "OSMEN_ROOT"),
    "CONTENT_ROOT": ("integrations.paths", "CONTENT_ROOT"),
    "LOGS_ROOT": ("integrations.paths", "LOGS_ROOT"),
    "HB411_ROOT": ("integrations.paths", "HB411_ROOT"),
    "HB411_OBSIDIAN": ("integrations.paths", "HB411_OBSIDIAN"),
    # Logging
    "AgentLogger": ("integrations.logging_system", "AgentLogger"),
    "CheckInTracker": ("integrations.logging_system", "CheckInTracker"),
    "AudioGenerationLog": ("integrations.logging_system", "AudioGenerationLog"),
    "SystemEventLog": ("integrations.logging_system", "SystemEventLog"),
    "agent_startup_check": ("integrations.logging_system", "agent_startup_check"),
    "get_recent_context": ("integrations.logging_system", "get_recent_context"),
    # LLM
    "LLMConfig": ("integrations.llm_providers", "LLMConfig"),
    "ProviderType": ("integrations.llm_providers", "ProviderType"),
    "get_llm_provider": ("integrations.llm_providers", "get_llm_provider"),
    # System monitoring
    "SystemMonitor": ("integrations.system_monitor", "SystemMonitor"),
    "GPUMonitor": ("integrations.system_monitor", "GPUMonitor"),
    "ResourceMonitor": ("integrations.system_monitor", "ResourceMonitor"),
    "TaskSchedulerMonitor": ("integrations.system_monitor", "TaskSchedulerMonitor"),
    "StartupAppsMonitor": ("integrations.system_monitor", "StartupAppsMonitor"),
    # Voice/audio
    "VoiceIntegration": ("integrations.voice_audio", "VoiceIntegration"),
    "VoiceConfig": ("integrations.voice_audio", "VoiceConfig"),
    "STTProvider": ("integrations.voice_audio", "STTProvider"),
    "TTSProvider": ("integrations.voice_audio", "TTSProvider"),
    # Media/entertainment
    "MediaIntegration": ("integrations.media_entertainment", "MediaIntegration"),
    "MediaConfig": ("integrations.media_entertainment", "MediaConfig"),
    "TMDBClient": ("integrations.media_entertainment", "TMDBClient"),
    "OpenSubtitlesClient": ("integrations.media_entertainment", "OpenSubtitlesClient"),
    # Creative tools
    "CreativeIntegration": ("integrations.creative_tools", "CreativeIntegration"),
    "CreativeConfig": ("integrations.creative_tools", "CreativeConfig"),
    "InvokeAIClient": ("integrations.creative_tools", "InvokeAIClient"),
    # Obsidian enhanced
    "EnhancedObsidianIntegration": (
        "integrations.obsidian_enhanced",
        "EnhancedObsidianIntegration",
    ),
    "ObsidianConfig": ("integrations.obsidian_enhanced", "ObsidianConfig"),
    "ObsidianNote": ("integrations.obsidian_enhanced", "ObsidianNote"),
    # Embeddings
    "EmbeddingProvider": ("integrations.embedding_optimizer", "EmbeddingProvider"),
    "EmbeddingModel": ("integrations.embedding_optimizer", "EmbeddingModel"),
    "EmbeddingCache": ("integrations.embedding_optimizer", "EmbeddingCache"),
    "ChromaDBEmbeddingFunction": (
        "integrations.embedding_optimizer",
        "ChromaDBEmbeddingFunction",
    ),
    # RAG pipeline
    "EnhancedRAGPipeline": ("integrations.rag_pipeline", "EnhancedRAGPipeline"),
    "RAGConfig": ("integrations.rag_pipeline", "RAGConfig"),
    "RetrievalResult": ("integrations.rag_pipeline", "RetrievalResult"),
    "BM25Retriever": ("integrations.rag_pipeline", "BM25Retriever"),
    "CrossEncoderReranker": ("integrations.rag_pipeline", "CrossEncoderReranker"),
    "QueryExpander": ("integrations.rag_pipeline", "QueryExpander"),
    "create_chromadb_rag_pipeline": (
        "integrations.rag_pipeline",
        "create_chromadb_rag_pipeline",
    ),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_EXPORTS.get(name)
    if not target:
        raise AttributeError(f"module 'integrations' has no attribute '{name}'")
    module_name, attr_name = target
    module = importlib.import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


__all__ = list(_LAZY_EXPORTS.keys())
