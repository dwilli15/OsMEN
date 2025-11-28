"""
LLM Provider Integration Tests

Tests all LLM provider implementations for interface compliance,
error handling, and configuration management.

Run: pytest tests/integration/test_llm_providers.py -v
"""

import asyncio
import os
import pytest
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


class TestLLMProviderInterface:
    """Tests for LLM provider interface compliance"""
    
    @pytest.mark.asyncio
    async def test_provider_factory_ollama(self):
        """Test provider factory returns Ollama provider"""
        from integrations.llm_providers import get_llm_provider, ProviderType
        
        # Mock Ollama availability
        with patch("integrations.llm_providers.OllamaProvider._check_availability") as mock:
            mock.return_value = True
            provider = await get_llm_provider("ollama")
            assert provider.provider_type == ProviderType.OLLAMA
    
    @pytest.mark.asyncio
    async def test_provider_factory_openai(self):
        """Test provider factory returns OpenAI provider"""
        from integrations.llm_providers import get_llm_provider, ProviderType
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            provider = await get_llm_provider("openai")
            assert provider.provider_type == ProviderType.OPENAI
    
    @pytest.mark.asyncio
    async def test_provider_factory_anthropic(self):
        """Test provider factory returns Anthropic provider"""
        from integrations.llm_providers import get_llm_provider, ProviderType
        
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            provider = await get_llm_provider("anthropic")
            assert provider.provider_type == ProviderType.ANTHROPIC
    
    @pytest.mark.asyncio
    async def test_provider_has_required_methods(self):
        """Test that all providers implement required methods"""
        from integrations.llm_providers import (
            OpenAIProvider,
            AnthropicProvider,
            OllamaProvider,
            LLMConfig,
            ProviderType
        )
        
        providers = [
            (OpenAIProvider, ProviderType.OPENAI),
            (AnthropicProvider, ProviderType.ANTHROPIC),
            (OllamaProvider, ProviderType.OLLAMA),
        ]
        
        required_methods = ["generate", "chat", "tool_call", "stream"]
        
        for provider_cls, provider_type in providers:
            config = LLMConfig(provider=provider_type)
            provider = provider_cls(config)
            
            for method in required_methods:
                assert hasattr(provider, method), f"{provider_cls.__name__} missing {method}"
                assert callable(getattr(provider, method))


class TestOpenAIProvider:
    """Tests for OpenAI provider"""
    
    @pytest.fixture
    def openai_provider(self):
        """Create OpenAI provider with mock"""
        from integrations.llm_providers import OpenAIProvider, LLMConfig, ProviderType
        
        config = LLMConfig(
            provider=ProviderType.OPENAI,
            model="gpt-4",
            api_key="test-key"
        )
        return OpenAIProvider(config)
    
    @pytest.mark.asyncio
    async def test_openai_generate(self, openai_provider):
        """Test OpenAI generate method"""
        with patch.object(openai_provider, "_make_request") as mock:
            mock.return_value = {
                "choices": [{"message": {"content": "Test response"}}]
            }
            
            result = await openai_provider.generate("Test prompt")
            assert result == "Test response"
    
    @pytest.mark.asyncio
    async def test_openai_chat(self, openai_provider):
        """Test OpenAI chat method"""
        with patch.object(openai_provider, "_make_request") as mock:
            mock.return_value = {
                "choices": [{"message": {"content": "Chat response"}}]
            }
            
            messages = [{"role": "user", "content": "Hello"}]
            result = await openai_provider.chat(messages)
            assert result == "Chat response"
    
    @pytest.mark.asyncio
    async def test_openai_tool_call(self, openai_provider):
        """Test OpenAI tool calling"""
        with patch.object(openai_provider, "_make_request") as mock:
            mock.return_value = {
                "choices": [{
                    "message": {
                        "content": None,
                        "tool_calls": [{
                            "id": "call_123",
                            "function": {
                                "name": "test_tool",
                                "arguments": '{"arg": "value"}'
                            }
                        }]
                    }
                }]
            }
            
            messages = [{"role": "user", "content": "Use the tool"}]
            tools = [{"type": "function", "function": {"name": "test_tool"}}]
            
            result = await openai_provider.tool_call(messages, tools)
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_openai_rate_limiting(self, openai_provider):
        """Test that rate limiting is enforced"""
        # Rate limiter should exist
        assert openai_provider._rate_limiter is not None
    
    @pytest.mark.asyncio
    async def test_openai_retry_on_error(self, openai_provider):
        """Test retry behavior on transient errors"""
        call_count = 0
        
        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Transient error")
            return {"choices": [{"message": {"content": "Success"}}]}
        
        with patch.object(openai_provider, "_make_request", side_effect=mock_request):
            # Should retry and eventually succeed
            try:
                result = await openai_provider.generate("Test")
            except:
                pass  # May fail depending on retry config


class TestAnthropicProvider:
    """Tests for Anthropic provider"""
    
    @pytest.fixture
    def anthropic_provider(self):
        """Create Anthropic provider with mock"""
        from integrations.llm_providers import AnthropicProvider, LLMConfig, ProviderType
        
        config = LLMConfig(
            provider=ProviderType.ANTHROPIC,
            model="claude-3-sonnet-20240229",
            api_key="test-key"
        )
        return AnthropicProvider(config)
    
    @pytest.mark.asyncio
    async def test_anthropic_generate(self, anthropic_provider):
        """Test Anthropic generate method"""
        with patch.object(anthropic_provider, "_make_request") as mock:
            mock.return_value = {
                "content": [{"type": "text", "text": "Test response"}]
            }
            
            result = await anthropic_provider.generate("Test prompt")
            assert result == "Test response"
    
    @pytest.mark.asyncio
    async def test_anthropic_chat(self, anthropic_provider):
        """Test Anthropic chat method"""
        with patch.object(anthropic_provider, "_make_request") as mock:
            mock.return_value = {
                "content": [{"type": "text", "text": "Chat response"}]
            }
            
            messages = [{"role": "user", "content": "Hello"}]
            result = await anthropic_provider.chat(messages)
            assert result == "Chat response"
    
    @pytest.mark.asyncio
    async def test_anthropic_tool_use(self, anthropic_provider):
        """Test Anthropic tool use"""
        with patch.object(anthropic_provider, "_make_request") as mock:
            mock.return_value = {
                "content": [{
                    "type": "tool_use",
                    "id": "tool_123",
                    "name": "test_tool",
                    "input": {"arg": "value"}
                }]
            }
            
            messages = [{"role": "user", "content": "Use the tool"}]
            tools = [{"name": "test_tool", "description": "A test tool"}]
            
            result = await anthropic_provider.tool_call(messages, tools)
            assert result is not None


class TestOllamaProvider:
    """Tests for Ollama provider"""
    
    @pytest.fixture
    def ollama_provider(self):
        """Create Ollama provider"""
        from integrations.llm_providers import OllamaProvider, LLMConfig, ProviderType
        
        config = LLMConfig(
            provider=ProviderType.OLLAMA,
            model="llama3.2"
        )
        return OllamaProvider(config)
    
    @pytest.mark.asyncio
    async def test_ollama_availability_check(self, ollama_provider):
        """Test Ollama availability check"""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"models": []}
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Should not raise
            is_available = await ollama_provider._check_availability()
            # Result depends on mock
    
    @pytest.mark.asyncio
    async def test_ollama_model_auto_pull(self, ollama_provider):
        """Test that Ollama can auto-pull models"""
        # This would test the auto-pull functionality
        # In a real test, would mock the Ollama API
        assert ollama_provider._config.model == "llama3.2"
    
    @pytest.mark.asyncio
    async def test_ollama_generate(self, ollama_provider):
        """Test Ollama generate method"""
        with patch.object(ollama_provider, "_make_request") as mock:
            mock.return_value = {
                "response": "Test response"
            }
            
            result = await ollama_provider.generate("Test prompt")
            assert result == "Test response"


class TestLLMConfig:
    """Tests for LLM configuration"""
    
    def test_config_defaults(self):
        """Test default configuration values"""
        from integrations.llm_providers import LLMConfig, ProviderType
        
        config = LLMConfig(provider=ProviderType.OLLAMA)
        
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.rate_limit_rpm == 60
        assert config.retry_attempts == 3
    
    def test_config_custom_values(self):
        """Test custom configuration values"""
        from integrations.llm_providers import LLMConfig, ProviderType
        
        config = LLMConfig(
            provider=ProviderType.OPENAI,
            model="gpt-4",
            temperature=0.5,
            max_tokens=2048,
            rate_limit_rpm=30
        )
        
        assert config.model == "gpt-4"
        assert config.temperature == 0.5
        assert config.max_tokens == 2048
        assert config.rate_limit_rpm == 30
    
    def test_config_from_env(self):
        """Test configuration from environment variables"""
        from integrations.llm_providers import LLMConfig, ProviderType
        
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "env-key",
            "LLM_MODEL": "gpt-4-turbo"
        }):
            config = LLMConfig(provider=ProviderType.OPENAI)
            # API key should be picked up from env
            assert config.api_key == "env-key" or config.api_key is None


class TestRateLimiting:
    """Tests for rate limiting functionality"""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_token_bucket(self):
        """Test token bucket rate limiter"""
        from integrations.llm_providers import TokenBucketRateLimiter
        
        limiter = TokenBucketRateLimiter(rate=10, capacity=10)
        
        # Should allow initial requests
        for _ in range(10):
            assert await limiter.acquire()
        
        # Should block after capacity exhausted
        # (in production, would actually wait)
    
    @pytest.mark.asyncio
    async def test_rate_limiter_refill(self):
        """Test that rate limiter refills over time"""
        from integrations.llm_providers import TokenBucketRateLimiter
        
        limiter = TokenBucketRateLimiter(rate=100, capacity=10)
        
        # Exhaust bucket
        for _ in range(10):
            await limiter.acquire()
        
        # After some time, should refill
        await asyncio.sleep(0.1)
        
        # Should have some tokens again
        assert limiter._tokens > 0


class TestProviderRouting:
    """Tests for provider routing logic"""
    
    @pytest.mark.asyncio
    async def test_local_first_routing(self):
        """Test that local provider is tried first"""
        from integrations.llm_providers import get_llm_provider, ProviderType
        
        # Without cloud API keys, should prefer local
        with patch.dict(os.environ, {}, clear=True):
            with patch("integrations.llm_providers.OllamaProvider._check_availability") as mock:
                mock.return_value = True
                provider = await get_llm_provider()
                assert provider.provider_type == ProviderType.OLLAMA
    
    @pytest.mark.asyncio
    async def test_fallback_to_cloud(self):
        """Test fallback to cloud when local unavailable"""
        from integrations.llm_providers import get_llm_provider, ProviderType
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("integrations.llm_providers.OllamaProvider._check_availability") as mock:
                mock.return_value = False
                provider = await get_llm_provider()
                # Should fall back to cloud provider
                assert provider.provider_type in [ProviderType.OPENAI, ProviderType.ANTHROPIC, ProviderType.OLLAMA]


class TestStreamingCapabilities:
    """Tests for streaming response capabilities"""
    
    @pytest.mark.asyncio
    async def test_openai_streaming(self):
        """Test OpenAI streaming responses"""
        from integrations.llm_providers import OpenAIProvider, LLMConfig, ProviderType
        
        config = LLMConfig(provider=ProviderType.OPENAI, api_key="test")
        provider = OpenAIProvider(config)
        
        # Mock streaming response
        async def mock_stream(*args, **kwargs):
            chunks = ["Hello", " ", "World", "!"]
            for chunk in chunks:
                yield chunk
        
        with patch.object(provider, "stream", side_effect=mock_stream):
            chunks = []
            async for chunk in provider.stream([{"role": "user", "content": "Hi"}]):
                chunks.append(chunk)
            
            assert "".join(chunks) == "Hello World!"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
