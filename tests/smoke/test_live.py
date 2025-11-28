"""
Live Smoke Tests for OsMEN

Selective tests against real APIs for production confidence.
Only run when LIVE_TESTS=true environment variable is set.

Run: LIVE_TESTS=true pytest tests/smoke/ -v
"""

import asyncio
import os
import pytest
from datetime import datetime

# Only run if LIVE_TESTS is enabled
pytestmark = [
    pytest.mark.smoke,
    pytest.mark.skipif(
        os.getenv("LIVE_TESTS", "false").lower() != "true",
        reason="Live tests disabled. Set LIVE_TESTS=true to run."
    )
]


class TestLiveOllama:
    """Live tests for Ollama provider"""
    
    @pytest.mark.asyncio
    async def test_ollama_availability(self):
        """Test Ollama is available"""
        from integrations.llm_providers import OllamaProvider, LLMConfig, ProviderType
        
        config = LLMConfig(provider=ProviderType.OLLAMA, model="llama3.2")
        provider = OllamaProvider(config)
        
        is_available = await provider._check_availability()
        
        if is_available:
            print("✓ Ollama is available")
        else:
            pytest.skip("Ollama not available")
    
    @pytest.mark.asyncio
    async def test_ollama_generate(self):
        """Test Ollama text generation"""
        from integrations.llm_providers import OllamaProvider, LLMConfig, ProviderType
        
        config = LLMConfig(provider=ProviderType.OLLAMA, model="llama3.2")
        provider = OllamaProvider(config)
        
        if not await provider._check_availability():
            pytest.skip("Ollama not available")
        
        response = await provider.generate("Say 'Hello Test' and nothing else")
        
        assert response is not None
        assert len(response) > 0
        print(f"✓ Ollama response: {response[:100]}...")
    
    @pytest.mark.asyncio
    async def test_ollama_chat(self):
        """Test Ollama chat completion"""
        from integrations.llm_providers import OllamaProvider, LLMConfig, ProviderType
        
        config = LLMConfig(provider=ProviderType.OLLAMA, model="llama3.2")
        provider = OllamaProvider(config)
        
        if not await provider._check_availability():
            pytest.skip("Ollama not available")
        
        messages = [
            {"role": "user", "content": "What is 2+2? Reply with just the number."}
        ]
        
        response = await provider.chat(messages)
        
        assert response is not None
        assert "4" in response
        print(f"✓ Ollama chat: {response}")


class TestLiveOpenAI:
    """Live tests for OpenAI provider"""
    
    @pytest.fixture
    def openai_provider(self):
        """Get OpenAI provider if API key available"""
        from integrations.llm_providers import OpenAIProvider, LLMConfig, ProviderType
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")
        
        config = LLMConfig(
            provider=ProviderType.OPENAI,
            model="gpt-3.5-turbo",
            api_key=api_key
        )
        return OpenAIProvider(config)
    
    @pytest.mark.asyncio
    async def test_openai_generate(self, openai_provider):
        """Test OpenAI text generation"""
        response = await openai_provider.generate("Say 'Hello Test' and nothing else")
        
        assert response is not None
        assert len(response) > 0
        print(f"✓ OpenAI response: {response}")
    
    @pytest.mark.asyncio
    async def test_openai_chat(self, openai_provider):
        """Test OpenAI chat completion"""
        messages = [
            {"role": "user", "content": "What is 2+2? Reply with just the number."}
        ]
        
        response = await openai_provider.chat(messages)
        
        assert response is not None
        assert "4" in response
        print(f"✓ OpenAI chat: {response}")
    
    @pytest.mark.asyncio
    async def test_openai_tool_call(self, openai_provider):
        """Test OpenAI tool calling"""
        messages = [
            {"role": "user", "content": "What's the weather in San Francisco?"}
        ]
        
        tools = [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    },
                    "required": ["location"]
                }
            }
        }]
        
        response = await openai_provider.tool_call(messages, tools)
        
        # Should either call the tool or respond with text
        assert response is not None
        print(f"✓ OpenAI tool call response: {response}")


class TestLiveAnthropic:
    """Live tests for Anthropic provider"""
    
    @pytest.fixture
    def anthropic_provider(self):
        """Get Anthropic provider if API key available"""
        from integrations.llm_providers import AnthropicProvider, LLMConfig, ProviderType
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")
        
        config = LLMConfig(
            provider=ProviderType.ANTHROPIC,
            model="claude-3-haiku-20240307",
            api_key=api_key
        )
        return AnthropicProvider(config)
    
    @pytest.mark.asyncio
    async def test_anthropic_generate(self, anthropic_provider):
        """Test Anthropic text generation"""
        response = await anthropic_provider.generate("Say 'Hello Test' and nothing else")
        
        assert response is not None
        assert len(response) > 0
        print(f"✓ Anthropic response: {response}")
    
    @pytest.mark.asyncio
    async def test_anthropic_chat(self, anthropic_provider):
        """Test Anthropic chat completion"""
        messages = [
            {"role": "user", "content": "What is 2+2? Reply with just the number."}
        ]
        
        response = await anthropic_provider.chat(messages)
        
        assert response is not None
        assert "4" in response
        print(f"✓ Anthropic chat: {response}")


class TestLiveWorkflows:
    """Live workflow smoke tests"""
    
    @pytest.mark.asyncio
    async def test_daily_brief_live(self):
        """Live test Daily Brief workflow"""
        from workflows.daily_brief import DailyBriefWorkflow, DailyBriefConfig
        
        # Use mock data but real LLM if available
        config = DailyBriefConfig(use_mock_data=True)
        workflow = DailyBriefWorkflow(config)
        
        result = await workflow.run()
        
        assert result is not None
        assert result.status.value == "completed"
        print(f"✓ Daily Brief completed in {result.duration_ms}ms")
        print(f"  Brief preview: {result.brief[:200]}...")
    
    @pytest.mark.asyncio
    async def test_research_live(self):
        """Live test Research workflow"""
        from workflows.research import ResearchWorkflow
        
        workflow = ResearchWorkflow()
        result = await workflow.run(
            topic="Python programming best practices",
            depth="quick"
        )
        
        assert result is not None
        assert len(result.sections) > 0
        print(f"✓ Research completed: {len(result.sections)} sections, {len(result.citations)} citations")
    
    @pytest.mark.asyncio
    async def test_content_live(self):
        """Live test Content workflow"""
        from workflows.content import ContentWorkflow
        
        workflow = ContentWorkflow()
        result = await workflow.generate_blog(
            topic="Getting Started with AI",
            tone="friendly",
            length="short"
        )
        
        assert result is not None
        assert result.word_count > 50
        print(f"✓ Content generated: {result.word_count} words")
        print(f"  Title: {result.title}")


class TestLiveIntegration:
    """Live integration smoke tests"""
    
    @pytest.mark.asyncio
    async def test_streaming_server_health(self):
        """Test streaming server health"""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8085/runs", timeout=5) as resp:
                    if resp.status == 200:
                        print("✓ Streaming server is healthy")
                    else:
                        pytest.skip("Streaming server not healthy")
        except:
            pytest.skip("Streaming server not available")
    
    @pytest.mark.asyncio
    async def test_gateway_health(self):
        """Test gateway health endpoint"""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8080/health", timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"✓ Gateway healthy: {data}")
                    else:
                        pytest.skip("Gateway not healthy")
        except:
            pytest.skip("Gateway not available")


class TestPerformanceBenchmarks:
    """Performance benchmarks for smoke testing"""
    
    @pytest.mark.asyncio
    async def test_research_performance(self):
        """Benchmark research workflow performance"""
        from workflows.research import ResearchWorkflow
        import time
        
        workflow = ResearchWorkflow()
        
        start = time.time()
        result = await workflow.run(
            topic="Performance Test",
            depth="quick",
            sources=["web"]
        )
        duration = (time.time() - start) * 1000
        
        print(f"✓ Research (quick) completed in {duration:.0f}ms")
        
        # Should complete within reasonable time
        assert duration < 5000, f"Research took too long: {duration}ms"
    
    @pytest.mark.asyncio
    async def test_content_performance(self):
        """Benchmark content workflow performance"""
        from workflows.content import ContentWorkflow
        import time
        
        workflow = ContentWorkflow()
        
        start = time.time()
        result = await workflow.generate_blog(
            topic="Performance Test",
            length="short"
        )
        duration = (time.time() - start) * 1000
        
        print(f"✓ Content (short blog) completed in {duration:.0f}ms")
        
        # Should complete within reasonable time
        assert duration < 2000, f"Content generation took too long: {duration}ms"
    
    @pytest.mark.asyncio
    async def test_daily_brief_performance(self):
        """Benchmark daily brief workflow performance"""
        from workflows.daily_brief import DailyBriefWorkflow, DailyBriefConfig
        import time
        
        config = DailyBriefConfig(use_mock_data=True)
        workflow = DailyBriefWorkflow(config)
        
        start = time.time()
        result = await workflow.run()
        duration = (time.time() - start) * 1000
        
        print(f"✓ Daily Brief completed in {duration:.0f}ms")
        
        # Should complete within reasonable time (with mock data)
        assert duration < 5000, f"Daily Brief took too long: {duration}ms"


def run_smoke_tests():
    """Run smoke tests manually"""
    import sys
    
    os.environ["LIVE_TESTS"] = "true"
    
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x",  # Stop on first failure
    ])


if __name__ == "__main__":
    run_smoke_tests()
