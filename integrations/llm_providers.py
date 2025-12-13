#!/usr/bin/env python3
"""
LLM Provider Adapters for OsMEN v3.0

Unified interface for multiple LLM providers:
- OpenAI (GPT-4, GPT-4o, GPT-3.5)
- Anthropic (Claude 3.5, Claude 3 Opus/Sonnet/Haiku)
- Ollama (Local models: Llama 3, Mistral, etc.)

Common interface with identical tool-call semantics so templates don't care
which backend is active.

Usage:
    from integrations.llm_providers import get_llm_provider, LLMConfig

    # Get provider with automatic fallback
    llm = get_llm_provider()

    # Or specify provider
    llm = get_llm_provider("openai")

    # Use unified interface
    response = await llm.chat([{"role": "user", "content": "Hello"}])
    response = await llm.generate("Complete this: The weather is")
    response = await llm.tool_call(tools=[...], messages=[...])

    # Stream responses
    async for chunk in llm.stream([{"role": "user", "content": "Hello"}]):
        print(chunk, end="")
"""

import asyncio
import json
import os
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    TypedDict,
    Union,
)

import aiohttp
from loguru import logger

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ============================================================================
# Configuration
# ============================================================================


class ProviderType(Enum):
    """Supported LLM providers"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class ModelCapability(Enum):
    """Model capabilities"""

    CHAT = "chat"
    COMPLETION = "completion"
    TOOL_USE = "tool_use"
    VISION = "vision"
    JSON_MODE = "json_mode"
    STREAMING = "streaming"


@dataclass
class LLMConfig:
    """
    Configuration for LLM providers.

    Attributes:
        provider: Which provider to use (openai, anthropic, ollama)
        model: Model identifier
        temperature: Sampling temperature (0.0-2.0)
        max_tokens: Maximum tokens in response
        json_mode: Whether to force JSON output
        rate_limit_rpm: Rate limit (requests per minute)
        rate_limit_tpm: Rate limit (tokens per minute)
        retry_attempts: Number of retry attempts on failure
        retry_delay: Delay between retries (seconds)
        timeout: Request timeout (seconds)
        api_key: API key (will read from env if not provided)
        base_url: Base URL for API (for Ollama or custom endpoints)
    """

    provider: ProviderType = ProviderType.OLLAMA  # Local-first default
    model: str = "llama3.2"
    temperature: float = 0.7
    max_tokens: int = 4096
    json_mode: bool = False
    rate_limit_rpm: int = 60
    rate_limit_tpm: int = 100000
    retry_attempts: int = 3
    retry_delay: float = 1.0
    timeout: float = 120.0
    api_key: Optional[str] = None
    base_url: Optional[str] = None

    # Provider-specific settings
    openai_organization: Optional[str] = None
    anthropic_version: str = "2024-01-01"
    ollama_keep_alive: str = "5m"

    def __post_init__(self):
        """Load API keys from environment if not provided"""
        if self.api_key is None:
            if self.provider == ProviderType.OPENAI:
                self.api_key = os.getenv("OPENAI_API_KEY")
            elif self.provider == ProviderType.ANTHROPIC:
                self.api_key = os.getenv("ANTHROPIC_API_KEY")
            # Ollama doesn't need an API key

        # Set default base URLs
        if self.base_url is None:
            if self.provider == ProviderType.OPENAI:
                self.base_url = "https://api.openai.com/v1"
            elif self.provider == ProviderType.ANTHROPIC:
                self.base_url = "https://api.anthropic.com"
            elif self.provider == ProviderType.OLLAMA:
                self.base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")


# ============================================================================
# Message and Response Types
# ============================================================================


class MessageRole(Enum):
    """Message roles"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """A chat message"""

    role: MessageRole
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls"""
        d = {"role": self.role.value, "content": self.content}
        if self.name:
            d["name"] = self.name
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        if self.tool_calls:
            d["tool_calls"] = self.tool_calls
        return d


@dataclass
class ToolDefinition:
    """Tool definition for function calling"""

    name: str
    description: str
    parameters: Dict[str, Any]
    strict: bool = False

    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
                "strict": self.strict,
            },
        }

    def to_anthropic_format(self) -> Dict[str, Any]:
        """Convert to Anthropic tool use format"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }


@dataclass
class ToolCall:
    """A tool call from the model"""

    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class LLMResponse:
    """Response from LLM provider"""

    content: str
    model: str
    provider: ProviderType
    finish_reason: str
    tool_calls: Optional[List[ToolCall]] = None
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Dict] = None
    latency_ms: float = 0.0


# ============================================================================
# Rate Limiter
# ============================================================================


class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self, requests_per_minute: int, tokens_per_minute: int):
        self.rpm = requests_per_minute
        self.tpm = tokens_per_minute
        self.request_tokens = requests_per_minute
        self.token_tokens = tokens_per_minute
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire permission to make a request"""
        async with self._lock:
            self._refill()

            if self.request_tokens >= 1 and self.token_tokens >= tokens:
                self.request_tokens -= 1
                self.token_tokens -= tokens
                return True
            return False

    async def wait_and_acquire(self, tokens: int = 1):
        """Wait until rate limit allows, then acquire"""
        while not await self.acquire(tokens):
            await asyncio.sleep(0.1)

    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill

        # Refill at rate of X per minute
        request_refill = (elapsed / 60) * self.rpm
        token_refill = (elapsed / 60) * self.tpm

        self.request_tokens = min(self.rpm, self.request_tokens + request_refill)
        self.token_tokens = min(self.tpm, self.token_tokens + token_refill)
        self.last_refill = now


# ============================================================================
# Base Provider
# ============================================================================


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All providers implement the same interface:
    - generate(): Text completion
    - chat(): Chat completion
    - tool_call(): Chat with tool/function calling
    - stream(): Streaming chat completion
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self.rate_limiter = RateLimiter(config.rate_limit_rpm, config.rate_limit_tpm)
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Close the provider session"""
        if self._session and not self._session.closed:
            await self._session.close()

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate text completion"""
        pass

    @abstractmethod
    async def chat(
        self, messages: List[Union[Message, Dict[str, Any]]], **kwargs
    ) -> LLMResponse:
        """Chat completion"""
        pass

    @abstractmethod
    async def tool_call(
        self,
        messages: List[Union[Message, Dict[str, Any]]],
        tools: List[Union[ToolDefinition, Dict[str, Any]]],
        **kwargs,
    ) -> LLMResponse:
        """Chat with tool/function calling"""
        pass

    @abstractmethod
    async def stream(
        self, messages: List[Union[Message, Dict[str, Any]]], **kwargs
    ) -> AsyncGenerator[str, None]:
        """Streaming chat completion"""
        pass

    def _normalize_messages(
        self, messages: List[Union[Message, Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Normalize messages to dictionary format"""
        normalized = []
        for msg in messages:
            if isinstance(msg, Message):
                normalized.append(msg.to_dict())
            elif isinstance(msg, dict):
                normalized.append(msg)
            else:
                raise ValueError(f"Invalid message type: {type(msg)}")
        return normalized

    def _normalize_tools(
        self, tools: List[Union[ToolDefinition, Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Normalize tools to dictionary format"""
        return [
            t.to_openai_format() if isinstance(t, ToolDefinition) else t for t in tools
        ]

    async def _retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry and exponential backoff"""
        last_error = None

        for attempt in range(self.config.retry_attempts):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.config.retry_attempts - 1:
                    delay = self.config.retry_delay * (2**attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)

        raise last_error


# ============================================================================
# OpenAI Provider
# ============================================================================


class OpenAIProvider(LLMProvider):
    """
    OpenAI API provider.

    Supports:
    - GPT-4, GPT-4o, GPT-4 Turbo
    - GPT-3.5 Turbo
    - Function/tool calling
    - JSON mode
    - Streaming
    """

    MODELS = {
        "gpt-4o": {
            "context": 128000,
            "capabilities": [
                ModelCapability.CHAT,
                ModelCapability.TOOL_USE,
                ModelCapability.VISION,
                ModelCapability.JSON_MODE,
                ModelCapability.STREAMING,
            ],
        },
        "gpt-4o-mini": {
            "context": 128000,
            "capabilities": [
                ModelCapability.CHAT,
                ModelCapability.TOOL_USE,
                ModelCapability.VISION,
                ModelCapability.JSON_MODE,
                ModelCapability.STREAMING,
            ],
        },
        "gpt-4-turbo": {
            "context": 128000,
            "capabilities": [
                ModelCapability.CHAT,
                ModelCapability.TOOL_USE,
                ModelCapability.VISION,
                ModelCapability.JSON_MODE,
                ModelCapability.STREAMING,
            ],
        },
        "gpt-4": {
            "context": 8192,
            "capabilities": [
                ModelCapability.CHAT,
                ModelCapability.TOOL_USE,
                ModelCapability.STREAMING,
            ],
        },
        "gpt-3.5-turbo": {
            "context": 16385,
            "capabilities": [
                ModelCapability.CHAT,
                ModelCapability.TOOL_USE,
                ModelCapability.JSON_MODE,
                ModelCapability.STREAMING,
            ],
        },
    }

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        if not config.api_key:
            raise ValueError("OpenAI API key required")

        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }
        if config.openai_organization:
            self.headers["OpenAI-Organization"] = config.openai_organization

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Text generation via chat endpoint"""
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, **kwargs)

    async def chat(
        self, messages: List[Union[Message, Dict[str, Any]]], **kwargs
    ) -> LLMResponse:
        """Chat completion"""
        await self.rate_limiter.wait_and_acquire()

        normalized = self._normalize_messages(messages)

        payload = {
            "model": kwargs.get("model", self.config.model),
            "messages": normalized,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }

        if self.config.json_mode or kwargs.get("json_mode"):
            payload["response_format"] = {"type": "json_object"}

        start_time = time.time()

        async def _make_request():
            session = await self._get_session()
            async with session.post(
                f"{self.config.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"OpenAI API error {resp.status}: {error_text}")
                return await resp.json()

        response = await self._retry_with_backoff(_make_request)
        latency = (time.time() - start_time) * 1000

        choice = response["choices"][0]

        return LLMResponse(
            content=choice["message"].get("content", ""),
            model=response["model"],
            provider=ProviderType.OPENAI,
            finish_reason=choice["finish_reason"],
            tool_calls=self._parse_tool_calls(choice["message"].get("tool_calls")),
            usage=response.get("usage"),
            raw_response=response,
            latency_ms=latency,
        )

    async def tool_call(
        self,
        messages: List[Union[Message, Dict[str, Any]]],
        tools: List[Union[ToolDefinition, Dict[str, Any]]],
        **kwargs,
    ) -> LLMResponse:
        """Chat with tool calling"""
        await self.rate_limiter.wait_and_acquire()

        normalized_messages = self._normalize_messages(messages)
        normalized_tools = self._normalize_tools(tools)

        payload = {
            "model": kwargs.get("model", self.config.model),
            "messages": normalized_messages,
            "tools": normalized_tools,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }

        if kwargs.get("tool_choice"):
            payload["tool_choice"] = kwargs["tool_choice"]

        start_time = time.time()

        async def _make_request():
            session = await self._get_session()
            async with session.post(
                f"{self.config.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"OpenAI API error {resp.status}: {error_text}")
                return await resp.json()

        response = await self._retry_with_backoff(_make_request)
        latency = (time.time() - start_time) * 1000

        choice = response["choices"][0]

        return LLMResponse(
            content=choice["message"].get("content", ""),
            model=response["model"],
            provider=ProviderType.OPENAI,
            finish_reason=choice["finish_reason"],
            tool_calls=self._parse_tool_calls(choice["message"].get("tool_calls")),
            usage=response.get("usage"),
            raw_response=response,
            latency_ms=latency,
        )

    async def stream(
        self, messages: List[Union[Message, Dict[str, Any]]], **kwargs
    ) -> AsyncGenerator[str, None]:
        """Streaming chat completion"""
        await self.rate_limiter.wait_and_acquire()

        normalized = self._normalize_messages(messages)

        payload = {
            "model": kwargs.get("model", self.config.model),
            "messages": normalized,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "stream": True,
        }

        session = await self._get_session()
        async with session.post(
            f"{self.config.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
        ) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise Exception(f"OpenAI API error {resp.status}: {error_text}")

            async for line in resp.content:
                line = line.decode("utf-8").strip()
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk["choices"][0]["delta"]
                        if "content" in delta:
                            yield delta["content"]
                    except json.JSONDecodeError:
                        continue

    def _parse_tool_calls(
        self, tool_calls: Optional[List[Dict]]
    ) -> Optional[List[ToolCall]]:
        """Parse OpenAI tool calls to common format"""
        if not tool_calls:
            return None

        return [
            ToolCall(
                id=tc["id"],
                name=tc["function"]["name"],
                arguments=json.loads(tc["function"]["arguments"]),
            )
            for tc in tool_calls
        ]


# ============================================================================
# Anthropic Provider
# ============================================================================


class AnthropicProvider(LLMProvider):
    """
    Anthropic API provider.

    Supports:
    - Claude 3.5 Sonnet
    - Claude 3 Opus, Sonnet, Haiku
    - Tool use
    - Streaming
    """

    MODELS = {
        "claude-3-5-sonnet-20241022": {
            "context": 200000,
            "capabilities": [
                ModelCapability.CHAT,
                ModelCapability.TOOL_USE,
                ModelCapability.VISION,
                ModelCapability.STREAMING,
            ],
        },
        "claude-3-opus-20240229": {
            "context": 200000,
            "capabilities": [
                ModelCapability.CHAT,
                ModelCapability.TOOL_USE,
                ModelCapability.VISION,
                ModelCapability.STREAMING,
            ],
        },
        "claude-3-sonnet-20240229": {
            "context": 200000,
            "capabilities": [
                ModelCapability.CHAT,
                ModelCapability.TOOL_USE,
                ModelCapability.VISION,
                ModelCapability.STREAMING,
            ],
        },
        "claude-3-haiku-20240307": {
            "context": 200000,
            "capabilities": [
                ModelCapability.CHAT,
                ModelCapability.TOOL_USE,
                ModelCapability.VISION,
                ModelCapability.STREAMING,
            ],
        },
    }

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        if not config.api_key:
            raise ValueError("Anthropic API key required")

        self.headers = {
            "x-api-key": config.api_key,
            "anthropic-version": config.anthropic_version,
            "Content-Type": "application/json",
        }

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Text generation via messages endpoint"""
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, **kwargs)

    async def chat(
        self, messages: List[Union[Message, Dict[str, Any]]], **kwargs
    ) -> LLMResponse:
        """Chat completion"""
        await self.rate_limiter.wait_and_acquire()

        normalized = self._normalize_messages(messages)

        # Extract system message if present
        system = None
        chat_messages = []
        for msg in normalized:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                chat_messages.append(msg)

        payload = {
            "model": kwargs.get("model", self.config.model),
            "messages": chat_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }

        if system:
            payload["system"] = system

        start_time = time.time()

        async def _make_request():
            session = await self._get_session()
            async with session.post(
                f"{self.config.base_url}/v1/messages",
                headers=self.headers,
                json=payload,
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"Anthropic API error {resp.status}: {error_text}")
                return await resp.json()

        response = await self._retry_with_backoff(_make_request)
        latency = (time.time() - start_time) * 1000

        # Extract content
        content = ""
        tool_calls = []
        for block in response.get("content", []):
            if block["type"] == "text":
                content += block["text"]
            elif block["type"] == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block["id"], name=block["name"], arguments=block["input"]
                    )
                )

        return LLMResponse(
            content=content,
            model=response["model"],
            provider=ProviderType.ANTHROPIC,
            finish_reason=response["stop_reason"],
            tool_calls=tool_calls if tool_calls else None,
            usage={
                "prompt_tokens": response["usage"]["input_tokens"],
                "completion_tokens": response["usage"]["output_tokens"],
                "total_tokens": (
                    response["usage"]["input_tokens"]
                    + response["usage"]["output_tokens"]
                ),
            },
            raw_response=response,
            latency_ms=latency,
        )

    async def tool_call(
        self,
        messages: List[Union[Message, Dict[str, Any]]],
        tools: List[Union[ToolDefinition, Dict[str, Any]]],
        **kwargs,
    ) -> LLMResponse:
        """Chat with tool use"""
        await self.rate_limiter.wait_and_acquire()

        normalized = self._normalize_messages(messages)

        # Convert tools to Anthropic format
        anthropic_tools = []
        for tool in tools:
            if isinstance(tool, ToolDefinition):
                anthropic_tools.append(tool.to_anthropic_format())
            elif isinstance(tool, dict) and "function" in tool:
                # Convert from OpenAI format
                func = tool["function"]
                anthropic_tools.append(
                    {
                        "name": func["name"],
                        "description": func["description"],
                        "input_schema": func["parameters"],
                    }
                )
            else:
                anthropic_tools.append(tool)

        # Extract system message
        system = None
        chat_messages = []
        for msg in normalized:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                chat_messages.append(msg)

        payload = {
            "model": kwargs.get("model", self.config.model),
            "messages": chat_messages,
            "tools": anthropic_tools,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }

        if system:
            payload["system"] = system

        start_time = time.time()

        async def _make_request():
            session = await self._get_session()
            async with session.post(
                f"{self.config.base_url}/v1/messages",
                headers=self.headers,
                json=payload,
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"Anthropic API error {resp.status}: {error_text}")
                return await resp.json()

        response = await self._retry_with_backoff(_make_request)
        latency = (time.time() - start_time) * 1000

        # Extract content and tool calls
        content = ""
        tool_calls = []
        for block in response.get("content", []):
            if block["type"] == "text":
                content += block["text"]
            elif block["type"] == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block["id"], name=block["name"], arguments=block["input"]
                    )
                )

        return LLMResponse(
            content=content,
            model=response["model"],
            provider=ProviderType.ANTHROPIC,
            finish_reason=response["stop_reason"],
            tool_calls=tool_calls if tool_calls else None,
            usage={
                "prompt_tokens": response["usage"]["input_tokens"],
                "completion_tokens": response["usage"]["output_tokens"],
                "total_tokens": (
                    response["usage"]["input_tokens"]
                    + response["usage"]["output_tokens"]
                ),
            },
            raw_response=response,
            latency_ms=latency,
        )

    async def stream(
        self, messages: List[Union[Message, Dict[str, Any]]], **kwargs
    ) -> AsyncGenerator[str, None]:
        """Streaming chat completion"""
        await self.rate_limiter.wait_and_acquire()

        normalized = self._normalize_messages(messages)

        # Extract system message
        system = None
        chat_messages = []
        for msg in normalized:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                chat_messages.append(msg)

        payload = {
            "model": kwargs.get("model", self.config.model),
            "messages": chat_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "stream": True,
        }

        if system:
            payload["system"] = system

        session = await self._get_session()
        async with session.post(
            f"{self.config.base_url}/v1/messages", headers=self.headers, json=payload
        ) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise Exception(f"Anthropic API error {resp.status}: {error_text}")

            async for line in resp.content:
                line = line.decode("utf-8").strip()
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        if data["type"] == "content_block_delta":
                            delta = data["delta"]
                            if delta["type"] == "text_delta":
                                yield delta["text"]
                    except json.JSONDecodeError:
                        continue


# ============================================================================
# Ollama Provider (Local-First)
# ============================================================================


class OllamaProvider(LLMProvider):
    """
    Ollama provider for local LLM inference.

    Supports:
    - Llama 3, Llama 3.2
    - Mistral, Mixtral
    - CodeLlama
    - And many more via Ollama

    Features:
    - Pre-flight model availability check
    - Auto-pull models with version pinning
    - Local-first, no API key required
    """

    RECOMMENDED_MODELS = {
        "llama3.2": {
            "size": "3B",
            "capabilities": [ModelCapability.CHAT, ModelCapability.STREAMING],
        },
        "llama3.2:1b": {
            "size": "1B",
            "capabilities": [ModelCapability.CHAT, ModelCapability.STREAMING],
        },
        "llama3.1": {
            "size": "8B",
            "capabilities": [
                ModelCapability.CHAT,
                ModelCapability.TOOL_USE,
                ModelCapability.STREAMING,
            ],
        },
        "llama3.1:70b": {
            "size": "70B",
            "capabilities": [
                ModelCapability.CHAT,
                ModelCapability.TOOL_USE,
                ModelCapability.STREAMING,
            ],
        },
        "mistral": {
            "size": "7B",
            "capabilities": [ModelCapability.CHAT, ModelCapability.STREAMING],
        },
        "mixtral": {
            "size": "47B",
            "capabilities": [ModelCapability.CHAT, ModelCapability.STREAMING],
        },
        "codellama": {
            "size": "7B",
            "capabilities": [
                ModelCapability.CHAT,
                ModelCapability.COMPLETION,
                ModelCapability.STREAMING,
            ],
        },
        "deepseek-coder-v2": {
            "size": "16B",
            "capabilities": [
                ModelCapability.CHAT,
                ModelCapability.COMPLETION,
                ModelCapability.STREAMING,
            ],
        },
    }

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.headers = {"Content-Type": "application/json"}

    async def check_available(self) -> bool:
        """Check if Ollama server is available"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.config.base_url}/api/tags") as resp:
                return resp.status == 200
        except Exception:
            return False

    async def list_models(self) -> List[str]:
        """List available models"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.config.base_url}/api/tags") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.warning(f"Failed to list Ollama models: {e}")
        return []

    async def pull_model(self, model: str) -> bool:
        """Pull a model if not available"""
        try:
            session = await self._get_session()
            async with session.post(
                f"{self.config.base_url}/api/pull",
                json={"name": model, "stream": False},
            ) as resp:
                return resp.status == 200
        except Exception as e:
            logger.error(f"Failed to pull model {model}: {e}")
            return False

    async def ensure_model(self, model: str) -> bool:
        """Ensure model is available, pulling if necessary"""
        models = await self.list_models()

        # Check if model is available (handle tags like llama3.2:latest)
        model_base = model.split(":")[0]
        for m in models:
            if m.startswith(model_base):
                return True

        logger.info(f"Model {model} not found, attempting to pull...")
        return await self.pull_model(model)

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Text generation"""
        model = kwargs.get("model", self.config.model)

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
            },
        }

        start_time = time.time()

        async def _make_request():
            session = await self._get_session()
            async with session.post(
                f"{self.config.base_url}/api/generate",
                headers=self.headers,
                json=payload,
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"Ollama API error {resp.status}: {error_text}")
                return await resp.json()

        response = await self._retry_with_backoff(_make_request)
        latency = (time.time() - start_time) * 1000

        return LLMResponse(
            content=response.get("response", ""),
            model=model,
            provider=ProviderType.OLLAMA,
            finish_reason="stop" if response.get("done") else "length",
            usage={
                "prompt_tokens": response.get("prompt_eval_count", 0),
                "completion_tokens": response.get("eval_count", 0),
                "total_tokens": (
                    response.get("prompt_eval_count", 0) + response.get("eval_count", 0)
                ),
            },
            raw_response=response,
            latency_ms=latency,
        )

    async def chat(
        self, messages: List[Union[Message, Dict[str, Any]]], **kwargs
    ) -> LLMResponse:
        """Chat completion"""
        model = kwargs.get("model", self.config.model)
        normalized = self._normalize_messages(messages)

        payload = {
            "model": model,
            "messages": normalized,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
            },
        }

        if self.config.json_mode or kwargs.get("json_mode"):
            payload["format"] = "json"

        start_time = time.time()

        async def _make_request():
            session = await self._get_session()
            async with session.post(
                f"{self.config.base_url}/api/chat", headers=self.headers, json=payload
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"Ollama API error {resp.status}: {error_text}")
                return await resp.json()

        response = await self._retry_with_backoff(_make_request)
        latency = (time.time() - start_time) * 1000

        return LLMResponse(
            content=response.get("message", {}).get("content", ""),
            model=model,
            provider=ProviderType.OLLAMA,
            finish_reason="stop" if response.get("done") else "length",
            usage={
                "prompt_tokens": response.get("prompt_eval_count", 0),
                "completion_tokens": response.get("eval_count", 0),
                "total_tokens": (
                    response.get("prompt_eval_count", 0) + response.get("eval_count", 0)
                ),
            },
            raw_response=response,
            latency_ms=latency,
        )

    async def tool_call(
        self,
        messages: List[Union[Message, Dict[str, Any]]],
        tools: List[Union[ToolDefinition, Dict[str, Any]]],
        **kwargs,
    ) -> LLMResponse:
        """
        Chat with tool calling.

        Note: Ollama tool calling support varies by model.
        For models without native tool support, we use prompt engineering.
        """
        model = kwargs.get("model", self.config.model)
        normalized = self._normalize_messages(messages)

        # Build tool descriptions for prompt
        tool_descriptions = []
        for tool in tools:
            if isinstance(tool, ToolDefinition):
                tool_descriptions.append(
                    f"- {tool.name}: {tool.description}\n"
                    f"  Parameters: {json.dumps(tool.parameters, indent=2)}"
                )
            elif isinstance(tool, dict) and "function" in tool:
                func = tool["function"]
                tool_descriptions.append(
                    f"- {func['name']}: {func['description']}\n"
                    f"  Parameters: {json.dumps(func['parameters'], indent=2)}"
                )

        # Add tool calling instructions to system message
        tool_prompt = (
            "You have access to the following tools:\n\n"
            + "\n\n".join(tool_descriptions)
            + "\n\nTo use a tool, respond with a JSON object in this format:\n"
            '{"tool_call": {"name": "tool_name", "arguments": {...}}}\n\n'
            "If you don't need to use a tool, respond normally."
        )

        # Prepend or update system message
        has_system = False
        for i, msg in enumerate(normalized):
            if msg["role"] == "system":
                normalized[i]["content"] = msg["content"] + "\n\n" + tool_prompt
                has_system = True
                break

        if not has_system:
            normalized.insert(0, {"role": "system", "content": tool_prompt})

        payload = {
            "model": model,
            "messages": normalized,
            "stream": False,
            "format": "json",  # Request JSON output
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
            },
        }

        start_time = time.time()

        async def _make_request():
            session = await self._get_session()
            async with session.post(
                f"{self.config.base_url}/api/chat", headers=self.headers, json=payload
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"Ollama API error {resp.status}: {error_text}")
                return await resp.json()

        response = await self._retry_with_backoff(_make_request)
        latency = (time.time() - start_time) * 1000

        content = response.get("message", {}).get("content", "")
        tool_calls = None

        # Try to parse tool call from response
        try:
            parsed = json.loads(content)
            if "tool_call" in parsed:
                tc = parsed["tool_call"]
                tool_calls = [
                    ToolCall(
                        id=f"call_{datetime.now().timestamp()}",
                        name=tc["name"],
                        arguments=tc.get("arguments", {}),
                    )
                ]
                content = ""  # Clear content when tool call is made
        except json.JSONDecodeError:
            pass  # Not a JSON response, keep content as-is

        return LLMResponse(
            content=content,
            model=model,
            provider=ProviderType.OLLAMA,
            finish_reason="tool_calls" if tool_calls else "stop",
            tool_calls=tool_calls,
            usage={
                "prompt_tokens": response.get("prompt_eval_count", 0),
                "completion_tokens": response.get("eval_count", 0),
                "total_tokens": (
                    response.get("prompt_eval_count", 0) + response.get("eval_count", 0)
                ),
            },
            raw_response=response,
            latency_ms=latency,
        )

    async def stream(
        self, messages: List[Union[Message, Dict[str, Any]]], **kwargs
    ) -> AsyncGenerator[str, None]:
        """Streaming chat completion"""
        model = kwargs.get("model", self.config.model)
        normalized = self._normalize_messages(messages)

        payload = {
            "model": model,
            "messages": normalized,
            "stream": True,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
            },
        }

        session = await self._get_session()
        async with session.post(
            f"{self.config.base_url}/api/chat", headers=self.headers, json=payload
        ) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise Exception(f"Ollama API error {resp.status}: {error_text}")

            async for line in resp.content:
                try:
                    data = json.loads(line.decode("utf-8"))
                    message = data.get("message", {})
                    if "content" in message:
                        yield message["content"]
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    continue


# ============================================================================
# Provider Factory
# ============================================================================


class ProviderRouter:
    """
    Routes requests to appropriate LLM provider.

    Features:
    - Automatic fallback: local → cloud
    - Provider selection based on capability
    - Load balancing (future)
    """

    def __init__(self, config: LLMConfig = None):
        self.config = config or LLMConfig()
        self._providers: Dict[ProviderType, LLMProvider] = {}
        self._default_provider: Optional[ProviderType] = None

    async def initialize(self):
        """Initialize providers based on availability"""
        # Try local first (Ollama)
        ollama = None
        try:
            ollama_config = LLMConfig(provider=ProviderType.OLLAMA)
            ollama = OllamaProvider(ollama_config)
            if await ollama.check_available():
                self._providers[ProviderType.OLLAMA] = ollama
                self._default_provider = ProviderType.OLLAMA
                logger.info("Ollama provider initialized (local-first)")
            else:
                await ollama.close()
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            if ollama is not None:
                try:
                    await ollama.close()
                except Exception:
                    pass

        # Try OpenAI
        try:
            openai_config = LLMConfig(provider=ProviderType.OPENAI)
            if openai_config.api_key:
                self._providers[ProviderType.OPENAI] = OpenAIProvider(openai_config)
                if self._default_provider is None:
                    self._default_provider = ProviderType.OPENAI
                logger.info("OpenAI provider initialized")
        except Exception as e:
            logger.debug(f"OpenAI not available: {e}")

        # Try Anthropic
        try:
            anthropic_config = LLMConfig(provider=ProviderType.ANTHROPIC)
            if anthropic_config.api_key:
                self._providers[ProviderType.ANTHROPIC] = AnthropicProvider(
                    anthropic_config
                )
                if self._default_provider is None:
                    self._default_provider = ProviderType.ANTHROPIC
                logger.info("Anthropic provider initialized")
        except Exception as e:
            logger.debug(f"Anthropic not available: {e}")

        if not self._providers:
            logger.warning("No LLM providers available!")

    def get_provider(self, provider_type: ProviderType = None) -> Optional[LLMProvider]:
        """Get a specific provider or the default"""
        if provider_type:
            return self._providers.get(provider_type)
        if self._default_provider:
            return self._providers.get(self._default_provider)
        return None

    def list_providers(self) -> List[ProviderType]:
        """List available providers"""
        return list(self._providers.keys())

    async def close(self):
        """Close all providers"""
        for provider in self._providers.values():
            await provider.close()


# ============================================================================
# Convenience Functions
# ============================================================================

_router_instance: Optional[ProviderRouter] = None


async def get_llm_provider(provider: Union[str, ProviderType] = None) -> LLMProvider:
    """
    Get an LLM provider instance.

    Args:
        provider: Provider type (openai, anthropic, ollama) or None for default

    Returns:
        LLMProvider instance

    Raises:
        ValueError: If requested provider is not available
    """
    global _router_instance

    if _router_instance is None:
        _router_instance = ProviderRouter()
        await _router_instance.initialize()

    if provider is None:
        llm = _router_instance.get_provider()
    else:
        if isinstance(provider, str):
            provider = ProviderType(provider)
        llm = _router_instance.get_provider(provider)

    if llm is None:
        available = _router_instance.list_providers()
        raise ValueError(
            f"Provider {provider} not available. "
            f"Available: {[p.value for p in available]}"
        )

    return llm


def create_llm_provider(config: LLMConfig) -> LLMProvider:
    """
    Create an LLM provider with specific configuration.

    Args:
        config: LLMConfig instance

    Returns:
        LLMProvider instance
    """
    if config.provider == ProviderType.OPENAI:
        return OpenAIProvider(config)
    elif config.provider == ProviderType.ANTHROPIC:
        return AnthropicProvider(config)
    elif config.provider == ProviderType.OLLAMA:
        return OllamaProvider(config)
    else:
        raise ValueError(f"Unknown provider: {config.provider}")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("LLM Provider Adapters for OsMEN v3.0")
    print("=" * 70)

    async def demo():
        # Initialize router
        router = ProviderRouter()
        await router.initialize()

        print(f"\nAvailable providers: {[p.value for p in router.list_providers()]}")

        # Get default provider
        llm = router.get_provider()
        if llm:
            print(f"\nDefault provider: {llm.config.provider.value}")
            print(f"Model: {llm.config.model}")

            # Test chat
            print("\nTesting chat...")
            try:
                response = await llm.chat(
                    [{"role": "user", "content": "Say hello in one sentence."}]
                )
                print(f"Response: {response.content}")
                print(f"Latency: {response.latency_ms:.1f}ms")
            except Exception as e:
                print(f"Chat failed: {e}")

        await router.close()

    asyncio.run(demo())
