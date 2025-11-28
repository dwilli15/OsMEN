#!/usr/bin/env python3
"""
Awesome Generative AI Integration for OsMEN v3.0

Curated integration of top generative AI tools, libraries, and frameworks
based on https://github.com/steven2358/awesome-generative-ai

Categories:
- Text Generation (LLMs, Chat Models)
- Image Generation (Diffusion, GANs)
- Audio Generation (TTS, Music, Voice)
- Video Generation
- Code Generation
- Multimodal Models
- Retrieval and RAG
- Agent Frameworks
- Evaluation and Testing
- Deployment and Serving

Each category includes:
- Recommended tools and libraries
- Integration patterns for OsMEN
- Configuration templates
- Best practices
"""

import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from loguru import logger


class ResourceCategory(Enum):
    """Categories of generative AI resources"""
    TEXT_GENERATION = "text_generation"
    IMAGE_GENERATION = "image_generation"
    AUDIO_GENERATION = "audio_generation"
    VIDEO_GENERATION = "video_generation"
    CODE_GENERATION = "code_generation"
    MULTIMODAL = "multimodal"
    RETRIEVAL_RAG = "retrieval_rag"
    AGENT_FRAMEWORKS = "agent_frameworks"
    EVALUATION = "evaluation"
    DEPLOYMENT = "deployment"


@dataclass
class GenerativeResource:
    """A generative AI resource/tool"""
    name: str
    category: ResourceCategory
    description: str
    url: str
    license: str = "unknown"
    stars: int = 0
    tags: List[str] = field(default_factory=list)
    integration_status: str = "available"  # available, integrated, planned
    config_template: Dict[str, Any] = field(default_factory=dict)
    osmen_compatible: bool = True


class AwesomeGenerativeAI:
    """
    Curated collection of generative AI resources for OsMEN.
    
    Based on steven2358/awesome-generative-ai with OsMEN-specific
    integrations and configurations.
    """
    
    def __init__(self):
        self._resources: Dict[str, GenerativeResource] = {}
        self._load_resources()
        
        logger.info(f"Loaded {len(self._resources)} generative AI resources")
    
    def _load_resources(self):
        """Load the curated resource collection"""
        
        # ====================================================================
        # Text Generation (LLMs)
        # ====================================================================
        
        self._add_resource(GenerativeResource(
            name="OpenAI GPT-4",
            category=ResourceCategory.TEXT_GENERATION,
            description="Most capable GPT model for complex reasoning and generation",
            url="https://platform.openai.com/docs/models/gpt-4",
            license="proprietary",
            tags=["llm", "chat", "reasoning", "production"],
            integration_status="integrated",
            config_template={
                "provider": "openai",
                "model": "gpt-4-turbo-preview",
                "temperature": 0.7,
                "max_tokens": 4096
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="Anthropic Claude",
            category=ResourceCategory.TEXT_GENERATION,
            description="Advanced AI assistant with strong reasoning and safety",
            url="https://www.anthropic.com/claude",
            license="proprietary",
            tags=["llm", "chat", "reasoning", "safety"],
            integration_status="integrated",
            config_template={
                "provider": "anthropic",
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 8192
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="Google Gemini",
            category=ResourceCategory.TEXT_GENERATION,
            description="Multimodal AI model from Google DeepMind",
            url="https://ai.google.dev/gemini-api",
            license="proprietary",
            tags=["llm", "multimodal", "google"],
            integration_status="available",
            config_template={
                "provider": "google",
                "model": "gemini-pro",
                "temperature": 0.7
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="Meta Llama 3",
            category=ResourceCategory.TEXT_GENERATION,
            description="Open-weight large language model from Meta",
            url="https://llama.meta.com/",
            license="llama-3",
            tags=["llm", "open-source", "local"],
            integration_status="integrated",
            config_template={
                "provider": "ollama",
                "model": "llama3:70b",
                "local": True
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="Mistral AI",
            category=ResourceCategory.TEXT_GENERATION,
            description="Efficient open-source LLMs with strong performance",
            url="https://mistral.ai/",
            license="apache-2.0",
            tags=["llm", "open-source", "efficient"],
            integration_status="integrated",
            config_template={
                "provider": "mistral",
                "model": "mistral-large-latest",
                "temperature": 0.7
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="Cohere Command",
            category=ResourceCategory.TEXT_GENERATION,
            description="Enterprise-focused LLMs with RAG capabilities",
            url="https://cohere.com/",
            license="proprietary",
            tags=["llm", "enterprise", "rag"],
            integration_status="available",
            config_template={
                "provider": "cohere",
                "model": "command-r-plus"
            }
        ))
        
        # ====================================================================
        # Image Generation
        # ====================================================================
        
        self._add_resource(GenerativeResource(
            name="DALL-E 3",
            category=ResourceCategory.IMAGE_GENERATION,
            description="Advanced image generation from OpenAI",
            url="https://openai.com/dall-e-3",
            license="proprietary",
            tags=["image", "diffusion", "generation"],
            integration_status="integrated",
            config_template={
                "provider": "openai",
                "model": "dall-e-3",
                "size": "1024x1024",
                "quality": "hd"
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="Stable Diffusion XL",
            category=ResourceCategory.IMAGE_GENERATION,
            description="Open-source diffusion model for high-quality images",
            url="https://stability.ai/stable-diffusion",
            license="openrail++",
            tags=["image", "diffusion", "open-source", "local"],
            integration_status="integrated",
            config_template={
                "provider": "stability",
                "model": "stable-diffusion-xl-1024-v1-0",
                "steps": 30,
                "cfg_scale": 7.0
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="Midjourney",
            category=ResourceCategory.IMAGE_GENERATION,
            description="High-quality artistic image generation",
            url="https://www.midjourney.com/",
            license="proprietary",
            tags=["image", "artistic", "commercial"],
            integration_status="planned"
        ))
        
        self._add_resource(GenerativeResource(
            name="FLUX",
            category=ResourceCategory.IMAGE_GENERATION,
            description="Next-generation image model from Black Forest Labs",
            url="https://blackforestlabs.ai/",
            license="flux-1-dev",
            tags=["image", "diffusion", "state-of-art"],
            integration_status="available",
            config_template={
                "provider": "replicate",
                "model": "black-forest-labs/flux-schnell"
            }
        ))
        
        # ====================================================================
        # Audio Generation
        # ====================================================================
        
        self._add_resource(GenerativeResource(
            name="OpenAI TTS",
            category=ResourceCategory.AUDIO_GENERATION,
            description="High-quality text-to-speech from OpenAI",
            url="https://platform.openai.com/docs/guides/text-to-speech",
            license="proprietary",
            tags=["audio", "tts", "speech"],
            integration_status="integrated",
            config_template={
                "provider": "openai",
                "model": "tts-1-hd",
                "voice": "alloy"
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="ElevenLabs",
            category=ResourceCategory.AUDIO_GENERATION,
            description="Advanced voice synthesis and cloning",
            url="https://elevenlabs.io/",
            license="proprietary",
            tags=["audio", "tts", "voice-cloning"],
            integration_status="integrated",
            config_template={
                "provider": "elevenlabs",
                "model": "eleven_multilingual_v2"
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="Coqui TTS",
            category=ResourceCategory.AUDIO_GENERATION,
            description="Open-source text-to-speech toolkit",
            url="https://github.com/coqui-ai/TTS",
            license="mpl-2.0",
            tags=["audio", "tts", "open-source", "local"],
            integration_status="integrated",
            config_template={
                "provider": "coqui",
                "model": "tts_models/en/ljspeech/tacotron2-DDC",
                "local": True
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="OpenAI Whisper",
            category=ResourceCategory.AUDIO_GENERATION,
            description="Speech recognition and transcription",
            url="https://github.com/openai/whisper",
            license="mit",
            tags=["audio", "stt", "transcription", "open-source"],
            integration_status="integrated",
            config_template={
                "provider": "openai",
                "model": "whisper-1"
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="Suno AI",
            category=ResourceCategory.AUDIO_GENERATION,
            description="AI music generation",
            url="https://www.suno.ai/",
            license="proprietary",
            tags=["audio", "music", "generation"],
            integration_status="available"
        ))
        
        # ====================================================================
        # Video Generation
        # ====================================================================
        
        self._add_resource(GenerativeResource(
            name="Runway Gen-2",
            category=ResourceCategory.VIDEO_GENERATION,
            description="AI video generation and editing",
            url="https://runwayml.com/",
            license="proprietary",
            tags=["video", "generation", "editing"],
            integration_status="available"
        ))
        
        self._add_resource(GenerativeResource(
            name="Pika Labs",
            category=ResourceCategory.VIDEO_GENERATION,
            description="Text-to-video generation platform",
            url="https://pika.art/",
            license="proprietary",
            tags=["video", "generation"],
            integration_status="available"
        ))
        
        self._add_resource(GenerativeResource(
            name="Stable Video Diffusion",
            category=ResourceCategory.VIDEO_GENERATION,
            description="Open-source video generation model",
            url="https://stability.ai/stable-video",
            license="stability-ai-nc",
            tags=["video", "diffusion", "open-source"],
            integration_status="available"
        ))
        
        # ====================================================================
        # Code Generation
        # ====================================================================
        
        self._add_resource(GenerativeResource(
            name="GitHub Copilot",
            category=ResourceCategory.CODE_GENERATION,
            description="AI pair programmer from GitHub",
            url="https://github.com/features/copilot",
            license="proprietary",
            tags=["code", "completion", "ide"],
            integration_status="integrated",
            config_template={
                "provider": "github",
                "model": "copilot"
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="Codex/GPT-4 Code",
            category=ResourceCategory.CODE_GENERATION,
            description="OpenAI models optimized for code",
            url="https://platform.openai.com/docs/guides/code",
            license="proprietary",
            tags=["code", "generation", "understanding"],
            integration_status="integrated",
            config_template={
                "provider": "openai",
                "model": "gpt-4-turbo-preview"
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="Amazon CodeWhisperer",
            category=ResourceCategory.CODE_GENERATION,
            description="AWS AI coding assistant",
            url="https://aws.amazon.com/codewhisperer/",
            license="proprietary",
            tags=["code", "aws", "completion"],
            integration_status="available"
        ))
        
        self._add_resource(GenerativeResource(
            name="StarCoder 2",
            category=ResourceCategory.CODE_GENERATION,
            description="Open-source code LLM from BigCode",
            url="https://github.com/bigcode-project/starcoder2",
            license="bigcode-openrail-m",
            tags=["code", "open-source", "local"],
            integration_status="available",
            config_template={
                "provider": "ollama",
                "model": "starcoder2",
                "local": True
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="DeepSeek Coder",
            category=ResourceCategory.CODE_GENERATION,
            description="Code-focused LLM with strong performance",
            url="https://github.com/deepseek-ai/DeepSeek-Coder",
            license="mit",
            tags=["code", "open-source", "local"],
            integration_status="available"
        ))
        
        # ====================================================================
        # Multimodal Models
        # ====================================================================
        
        self._add_resource(GenerativeResource(
            name="GPT-4 Vision",
            category=ResourceCategory.MULTIMODAL,
            description="Multimodal GPT model with image understanding",
            url="https://platform.openai.com/docs/guides/vision",
            license="proprietary",
            tags=["multimodal", "vision", "understanding"],
            integration_status="integrated",
            config_template={
                "provider": "openai",
                "model": "gpt-4-vision-preview"
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="Claude 3 Vision",
            category=ResourceCategory.MULTIMODAL,
            description="Anthropic's multimodal capabilities",
            url="https://www.anthropic.com/claude",
            license="proprietary",
            tags=["multimodal", "vision", "understanding"],
            integration_status="integrated",
            config_template={
                "provider": "anthropic",
                "model": "claude-sonnet-4-20250514"
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="LLaVA",
            category=ResourceCategory.MULTIMODAL,
            description="Open-source multimodal LLM",
            url="https://llava-vl.github.io/",
            license="apache-2.0",
            tags=["multimodal", "vision", "open-source"],
            integration_status="available",
            config_template={
                "provider": "ollama",
                "model": "llava",
                "local": True
            }
        ))
        
        # ====================================================================
        # Retrieval and RAG
        # ====================================================================
        
        self._add_resource(GenerativeResource(
            name="LangChain",
            category=ResourceCategory.RETRIEVAL_RAG,
            description="Framework for LLM applications and RAG",
            url="https://www.langchain.com/",
            license="mit",
            tags=["rag", "framework", "orchestration"],
            integration_status="integrated",
            config_template={
                "provider": "langchain",
                "retriever": "vectorstore",
                "embeddings": "openai"
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="LlamaIndex",
            category=ResourceCategory.RETRIEVAL_RAG,
            description="Data framework for LLM applications",
            url="https://www.llamaindex.ai/",
            license="mit",
            tags=["rag", "indexing", "retrieval"],
            integration_status="integrated",
            config_template={
                "provider": "llamaindex",
                "index_type": "vector"
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="Qdrant",
            category=ResourceCategory.RETRIEVAL_RAG,
            description="High-performance vector database",
            url="https://qdrant.tech/",
            license="apache-2.0",
            tags=["vector-db", "retrieval", "storage"],
            integration_status="integrated",
            config_template={
                "provider": "qdrant",
                "host": "localhost",
                "port": 6333
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="Pinecone",
            category=ResourceCategory.RETRIEVAL_RAG,
            description="Managed vector database for AI",
            url="https://www.pinecone.io/",
            license="proprietary",
            tags=["vector-db", "managed", "scalable"],
            integration_status="available"
        ))
        
        self._add_resource(GenerativeResource(
            name="Chroma",
            category=ResourceCategory.RETRIEVAL_RAG,
            description="Open-source embedding database",
            url="https://www.trychroma.com/",
            license="apache-2.0",
            tags=["vector-db", "open-source", "embedded"],
            integration_status="integrated",
            config_template={
                "provider": "chroma",
                "persist_directory": "./.copilot/chroma"
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="Cohere Rerank",
            category=ResourceCategory.RETRIEVAL_RAG,
            description="Neural reranking for better retrieval",
            url="https://cohere.com/rerank",
            license="proprietary",
            tags=["reranking", "retrieval", "quality"],
            integration_status="available"
        ))
        
        # ====================================================================
        # Agent Frameworks
        # ====================================================================
        
        self._add_resource(GenerativeResource(
            name="LangGraph",
            category=ResourceCategory.AGENT_FRAMEWORKS,
            description="Stateful multi-actor orchestration",
            url="https://langchain-ai.github.io/langgraph/",
            license="mit",
            tags=["agents", "orchestration", "stateful"],
            integration_status="integrated",
            config_template={
                "provider": "langgraph",
                "checkpointer": "memory"
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="DeepAgents",
            category=ResourceCategory.AGENT_FRAMEWORKS,
            description="Long-horizon task planning agents",
            url="https://github.com/langchain-ai/deepagents",
            license="mit",
            tags=["agents", "planning", "delegation"],
            integration_status="integrated",
            config_template={
                "provider": "deepagents",
                "model": "claude-sonnet-4.5"
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="AutoGPT",
            category=ResourceCategory.AGENT_FRAMEWORKS,
            description="Autonomous GPT-4 agent",
            url="https://github.com/Significant-Gravitas/AutoGPT",
            license="mit",
            tags=["agents", "autonomous", "planning"],
            integration_status="available"
        ))
        
        self._add_resource(GenerativeResource(
            name="CrewAI",
            category=ResourceCategory.AGENT_FRAMEWORKS,
            description="Multi-agent orchestration framework",
            url="https://www.crewai.com/",
            license="mit",
            tags=["agents", "multi-agent", "roles"],
            integration_status="available"
        ))
        
        self._add_resource(GenerativeResource(
            name="OpenGPTs",
            category=ResourceCategory.AGENT_FRAMEWORKS,
            description="Open-source GPTs implementation",
            url="https://github.com/langchain-ai/opengpts",
            license="mit",
            tags=["agents", "configurable", "assistants"],
            integration_status="integrated",
            config_template={
                "provider": "opengpts",
                "architecture": "openai-functions"
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="OpenDeepResearch",
            category=ResourceCategory.AGENT_FRAMEWORKS,
            description="Deep research agent framework",
            url="https://github.com/langchain-ai/open_deep_research",
            license="mit",
            tags=["agents", "research", "analysis"],
            integration_status="integrated"
        ))
        
        self._add_resource(GenerativeResource(
            name="LocalDeepResearcher",
            category=ResourceCategory.AGENT_FRAMEWORKS,
            description="Local research agent capabilities",
            url="https://github.com/langchain-ai/local-deep-researcher",
            license="mit",
            tags=["agents", "research", "local"],
            integration_status="integrated"
        ))
        
        # ====================================================================
        # Evaluation
        # ====================================================================
        
        self._add_resource(GenerativeResource(
            name="LangSmith",
            category=ResourceCategory.EVALUATION,
            description="LLM application observability and evaluation",
            url="https://smith.langchain.com/",
            license="proprietary",
            tags=["evaluation", "observability", "tracing"],
            integration_status="integrated",
            config_template={
                "provider": "langsmith",
                "project": "osmen-v3"
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="Weights & Biases",
            category=ResourceCategory.EVALUATION,
            description="ML experiment tracking and evaluation",
            url="https://wandb.ai/",
            license="proprietary",
            tags=["evaluation", "tracking", "experiments"],
            integration_status="available"
        ))
        
        self._add_resource(GenerativeResource(
            name="Promptfoo",
            category=ResourceCategory.EVALUATION,
            description="Open-source prompt testing framework",
            url="https://github.com/promptfoo/promptfoo",
            license="mit",
            tags=["evaluation", "testing", "prompts"],
            integration_status="available"
        ))
        
        # ====================================================================
        # Deployment
        # ====================================================================
        
        self._add_resource(GenerativeResource(
            name="Ollama",
            category=ResourceCategory.DEPLOYMENT,
            description="Run LLMs locally with simple deployment",
            url="https://ollama.ai/",
            license="mit",
            tags=["deployment", "local", "inference"],
            integration_status="integrated",
            config_template={
                "provider": "ollama",
                "host": "http://localhost:11434"
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="vLLM",
            category=ResourceCategory.DEPLOYMENT,
            description="High-throughput LLM inference engine",
            url="https://vllm.ai/",
            license="apache-2.0",
            tags=["deployment", "inference", "performance"],
            integration_status="available"
        ))
        
        self._add_resource(GenerativeResource(
            name="LM Studio",
            category=ResourceCategory.DEPLOYMENT,
            description="Desktop app for local LLM inference",
            url="https://lmstudio.ai/",
            license="proprietary",
            tags=["deployment", "local", "desktop"],
            integration_status="integrated",
            config_template={
                "provider": "lmstudio",
                "host": "http://localhost:1234/v1"
            }
        ))
        
        self._add_resource(GenerativeResource(
            name="Text Generation Inference (TGI)",
            category=ResourceCategory.DEPLOYMENT,
            description="HuggingFace inference server",
            url="https://github.com/huggingface/text-generation-inference",
            license="apache-2.0",
            tags=["deployment", "inference", "huggingface"],
            integration_status="available"
        ))
    
    def _add_resource(self, resource: GenerativeResource):
        """Add a resource to the collection"""
        self._resources[resource.name] = resource
    
    def get_resource(self, name: str) -> Optional[GenerativeResource]:
        """Get a resource by name"""
        return self._resources.get(name)
    
    def list_resources(
        self,
        category: ResourceCategory = None,
        integration_status: str = None,
        tag: str = None
    ) -> List[GenerativeResource]:
        """List resources with optional filtering"""
        resources = list(self._resources.values())
        
        if category:
            resources = [r for r in resources if r.category == category]
        
        if integration_status:
            resources = [r for r in resources if r.integration_status == integration_status]
        
        if tag:
            resources = [r for r in resources if tag in r.tags]
        
        return resources
    
    def get_categories(self) -> List[ResourceCategory]:
        """Get all categories"""
        return list(ResourceCategory)
    
    def get_integrated_resources(self) -> List[GenerativeResource]:
        """Get all integrated resources"""
        return self.list_resources(integration_status="integrated")
    
    def get_config_template(self, name: str) -> Dict[str, Any]:
        """Get configuration template for a resource"""
        resource = self._resources.get(name)
        if resource:
            return resource.config_template
        return {}
    
    def export_catalog(self) -> Dict[str, Any]:
        """Export the full resource catalog"""
        return {
            'resources': [
                {
                    'name': r.name,
                    'category': r.category.value,
                    'description': r.description,
                    'url': r.url,
                    'license': r.license,
                    'tags': r.tags,
                    'integration_status': r.integration_status,
                    'osmen_compatible': r.osmen_compatible
                }
                for r in self._resources.values()
            ],
            'total': len(self._resources),
            'by_category': {
                cat.value: len(self.list_resources(category=cat))
                for cat in ResourceCategory
            },
            'integrated': len(self.get_integrated_resources()),
            'exported_at': datetime.now().isoformat()
        }


# ============================================================================
# Integration with OsMEN
# ============================================================================

class GenerativeAIIntegration:
    """
    Integration layer connecting awesome-generative-ai resources
    with OsMEN workflows and agents.
    """
    
    def __init__(self):
        self.catalog = AwesomeGenerativeAI()
        self._active_providers: Dict[str, Dict] = {}
        
        logger.info("Generative AI integration initialized")
    
    def activate_provider(
        self,
        name: str,
        config_override: Dict[str, Any] = None
    ) -> bool:
        """Activate a resource provider"""
        resource = self.catalog.get_resource(name)
        if not resource:
            logger.error(f"Unknown resource: {name}")
            return False
        
        config = resource.config_template.copy()
        if config_override:
            config.update(config_override)
        
        self._active_providers[name] = {
            'resource': resource,
            'config': config,
            'activated_at': datetime.now().isoformat()
        }
        
        logger.info(f"Activated provider: {name}")
        return True
    
    def deactivate_provider(self, name: str) -> bool:
        """Deactivate a provider"""
        if name in self._active_providers:
            del self._active_providers[name]
            return True
        return False
    
    def get_active_providers(self) -> List[str]:
        """Get list of active providers"""
        return list(self._active_providers.keys())
    
    def get_provider_config(self, name: str) -> Optional[Dict]:
        """Get config for an active provider"""
        if name in self._active_providers:
            return self._active_providers[name]['config']
        return None
    
    def recommend_for_task(
        self,
        task_type: str,
        requirements: Dict[str, Any] = None
    ) -> List[GenerativeResource]:
        """Recommend resources for a task type"""
        requirements = requirements or {}
        
        # Map task types to categories
        task_mapping = {
            'chat': ResourceCategory.TEXT_GENERATION,
            'text': ResourceCategory.TEXT_GENERATION,
            'image': ResourceCategory.IMAGE_GENERATION,
            'audio': ResourceCategory.AUDIO_GENERATION,
            'video': ResourceCategory.VIDEO_GENERATION,
            'code': ResourceCategory.CODE_GENERATION,
            'rag': ResourceCategory.RETRIEVAL_RAG,
            'agent': ResourceCategory.AGENT_FRAMEWORKS,
            'research': ResourceCategory.AGENT_FRAMEWORKS
        }
        
        category = task_mapping.get(task_type.lower())
        if not category:
            return []
        
        resources = self.catalog.list_resources(category=category)
        
        # Filter by requirements
        local_only = requirements.get('local', False)
        if local_only:
            resources = [r for r in resources if 'local' in r.tags]
        
        open_source = requirements.get('open_source', False)
        if open_source:
            resources = [r for r in resources if 'open-source' in r.tags]
        
        # Prioritize integrated resources
        resources.sort(
            key=lambda r: (
                r.integration_status == 'integrated',
                r.stars
            ),
            reverse=True
        )
        
        return resources
    
    def get_status(self) -> Dict[str, Any]:
        """Get integration status"""
        return {
            'total_resources': len(self.catalog._resources),
            'integrated': len(self.catalog.get_integrated_resources()),
            'active_providers': len(self._active_providers),
            'categories': {
                cat.value: len(self.catalog.list_resources(category=cat))
                for cat in ResourceCategory
            }
        }


# ============================================================================
# Convenience Functions
# ============================================================================

_awesome_ai: Optional[AwesomeGenerativeAI] = None
_ai_integration: Optional[GenerativeAIIntegration] = None

def get_awesome_ai() -> AwesomeGenerativeAI:
    """Get the awesome generative AI catalog"""
    global _awesome_ai
    if _awesome_ai is None:
        _awesome_ai = AwesomeGenerativeAI()
    return _awesome_ai


def get_ai_integration() -> GenerativeAIIntegration:
    """Get the AI integration layer"""
    global _ai_integration
    if _ai_integration is None:
        _ai_integration = GenerativeAIIntegration()
    return _ai_integration


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("Awesome Generative AI Integration for OsMEN v3.0")
    print("=" * 70)
    
    catalog = get_awesome_ai()
    
    print(f"\n✅ Loaded {len(catalog._resources)} generative AI resources")
    
    print("\nResources by Category:")
    for category in ResourceCategory:
        count = len(catalog.list_resources(category=category))
        print(f"  - {category.value}: {count}")
    
    integrated = catalog.get_integrated_resources()
    print(f"\nIntegrated with OsMEN: {len(integrated)} resources")
    for r in integrated[:5]:
        print(f"  - {r.name}: {r.description[:50]}...")
    
    print("\n\nUsage:")
    print("  from integrations.awesome_generative_ai import get_ai_integration")
    print("  ai = get_ai_integration()")
    print("  resources = ai.recommend_for_task('chat', {'local': True})")
    print("  ai.activate_provider('Ollama')")
