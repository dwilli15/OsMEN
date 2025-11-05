#!/usr/bin/env python3
"""
OsMEN Agent Gateway
Unified API gateway for production LLM agents (OpenAI, GitHub Copilot, Amazon Q, etc.)
"""

import os
import logging
from typing import Optional, Dict, List, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CompletionRequest(BaseModel):
    """Request model for completions"""
    prompt: str
    agent: str = Field(default="openai", description="Agent to use: openai, copilot, amazonq, claude, lmstudio, ollama")
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = False


class CompletionResponse(BaseModel):
    """Response model for completions"""
    content: str
    agent: str
    model: str
    usage: Optional[Dict[str, int]] = None


class AgentGateway:
    """Gateway for routing requests to different LLM agents"""
    
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.aws_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.lm_studio_url = os.getenv("LM_STUDIO_URL", "http://host.docker.internal:1234/v1")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        
        self.client = httpx.AsyncClient(timeout=120.0)
        
    async def completion(self, request: CompletionRequest) -> CompletionResponse:
        """Route completion request to appropriate agent"""
        agent = request.agent.lower()
        
        if agent == "openai":
            return await self._openai_completion(request)
        elif agent == "copilot":
            return await self._copilot_completion(request)
        elif agent == "amazonq":
            return await self._amazonq_completion(request)
        elif agent == "claude":
            return await self._claude_completion(request)
        elif agent == "lmstudio":
            return await self._lmstudio_completion(request)
        elif agent == "ollama":
            return await self._ollama_completion(request)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown agent: {agent}")
    
    async def _openai_completion(self, request: CompletionRequest) -> CompletionResponse:
        """OpenAI completion"""
        if not self.openai_key:
            raise HTTPException(status_code=401, detail="OpenAI API key not configured")
        
        model = request.model or os.getenv("OPENAI_MODEL", "gpt-4")
        
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        }
        
        response = await self.client.post(
            f"{self.openai_base_url}/chat/completions",
            json=payload,
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        data = response.json()
        return CompletionResponse(
            content=data["choices"][0]["message"]["content"],
            agent="openai",
            model=model,
            usage=data.get("usage")
        )
    
    async def _copilot_completion(self, request: CompletionRequest) -> CompletionResponse:
        """GitHub Copilot completion"""
        if not self.github_token:
            raise HTTPException(status_code=401, detail="GitHub token not configured")
        
        # GitHub Copilot API integration would go here
        # This is a placeholder for the actual implementation
        return CompletionResponse(
            content="GitHub Copilot integration placeholder",
            agent="copilot",
            model="copilot"
        )
    
    async def _amazonq_completion(self, request: CompletionRequest) -> CompletionResponse:
        """Amazon Q completion"""
        if not self.aws_key:
            raise HTTPException(status_code=401, detail="AWS credentials not configured")
        
        # Amazon Q API integration would go here
        # This is a placeholder for the actual implementation
        return CompletionResponse(
            content="Amazon Q integration placeholder",
            agent="amazonq",
            model="amazonq"
        )
    
    async def _claude_completion(self, request: CompletionRequest) -> CompletionResponse:
        """Anthropic Claude completion"""
        if not self.anthropic_key:
            raise HTTPException(status_code=401, detail="Anthropic API key not configured")
        
        model = request.model or os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
        
        headers = {
            "x-api-key": self.anthropic_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": request.prompt}],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature
        }
        
        response = await self.client.post(
            "https://api.anthropic.com/v1/messages",
            json=payload,
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        data = response.json()
        return CompletionResponse(
            content=data["content"][0]["text"],
            agent="claude",
            model=model,
            usage=data.get("usage")
        )
    
    async def _lmstudio_completion(self, request: CompletionRequest) -> CompletionResponse:
        """LM Studio completion (OpenAI-compatible API)"""
        model = request.model or os.getenv("LM_STUDIO_MODEL", "local-model")
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        }
        
        try:
            response = await self.client.post(
                f"{self.lm_studio_url}/chat/completions",
                json=payload
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            
            data = response.json()
            return CompletionResponse(
                content=data["choices"][0]["message"]["content"],
                agent="lmstudio",
                model=model,
                usage=data.get("usage")
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="LM Studio not reachable. Please start LM Studio on host and enable API server."
            )
    
    async def _ollama_completion(self, request: CompletionRequest) -> CompletionResponse:
        """Ollama completion"""
        model = request.model or os.getenv("OLLAMA_MODEL", "llama2")
        
        payload = {
            "model": model,
            "prompt": request.prompt,
            "stream": False
        }
        
        try:
            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json=payload
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            
            data = response.json()
            return CompletionResponse(
                content=data["response"],
                agent="ollama",
                model=model
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Ollama not reachable. Start with: docker-compose --profile ollama up -d"
            )
    
    async def list_agents(self) -> Dict[str, Any]:
        """List available agents and their status"""
        agents = {
            "openai": {
                "available": bool(self.openai_key),
                "models": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo-preview"]
            },
            "copilot": {
                "available": bool(self.github_token),
                "models": ["copilot"]
            },
            "amazonq": {
                "available": bool(self.aws_key),
                "models": ["amazonq"]
            },
            "claude": {
                "available": bool(self.anthropic_key),
                "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229"]
            },
            "lmstudio": {
                "available": True,
                "models": ["local-model"],
                "note": "Requires LM Studio running on host"
            },
            "ollama": {
                "available": True,
                "models": ["llama2", "mistral", "codellama"],
                "note": "Optional, start with --profile ollama"
            }
        }
        return agents


# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    logger.info("Starting OsMEN Agent Gateway")
    yield
    logger.info("Shutting down OsMEN Agent Gateway")


app = FastAPI(
    title="OsMEN Agent Gateway",
    description="Unified API gateway for production LLM agents",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize gateway
gateway = AgentGateway()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "OsMEN Agent Gateway",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/agents")
async def list_agents():
    """List available agents"""
    return await gateway.list_agents()


@app.post("/completion", response_model=CompletionResponse)
async def completion(request: CompletionRequest):
    """Generate completion using specified agent"""
    return await gateway.completion(request)


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
