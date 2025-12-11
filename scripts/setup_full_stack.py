#!/usr/bin/env python3
"""
OsMEN Full Stack Configuration Script

This script configures the entire OsMEN ecosystem to full specification:
- Langflow flows with proper wiring (Coordinator → Specialists)
- n8n workflows with webhooks and triggers
- Librarian RAG with ChromaDB/Stella embeddings
- Obsidian vault integration
- VS Code MCP bridge for AI chat extensions
- Local LLM routing (LM Studio/Ollama)
- Voice/Whisper integration

Usage:
    python scripts/setup_full_stack.py
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

# Configuration
BASE_DIR = Path(__file__).parent.parent
LANGFLOW_URL = os.getenv("LANGFLOW_URL", "http://localhost:7860")
N8N_URL = os.getenv("N8N_URL", "http://localhost:5678")
MCP_URL = os.getenv("MCP_URL", "http://localhost:8081")
LIBRARIAN_URL = os.getenv("LIBRARIAN_URL", "http://localhost:8200")
CHROMADB_URL = os.getenv("CHROMA_URL", "http://localhost:8000")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8080")
LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# n8n credentials (from previous session)
N8N_EMAIL = "armadeus03@hotmail.com"
N8N_PASSWORD = "Dw8533Dw"


class FullStackConfigurator:
    """Configure the entire OsMEN stack"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.langflow_token = None
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "langflow": {},
            "n8n": {},
            "librarian": {},
            "mcp": {},
            "local_llm": {},
        }

    async def close(self):
        await self.client.aclose()

    # =========================================================================
    # Service Health Checks
    # =========================================================================

    async def check_service(self, name: str, url: str, path: str = "/health") -> Dict:
        """Check if a service is healthy"""
        try:
            response = await self.client.get(f"{url}{path}", timeout=5.0)
            healthy = response.status_code < 400
            return {
                "name": name,
                "healthy": healthy,
                "status_code": response.status_code,
            }
        except Exception as e:
            return {"name": name, "healthy": False, "error": str(e)}

    async def check_all_services(self) -> Dict[str, Any]:
        """Check health of all services"""
        print("\n" + "=" * 60)
        print("🔍 Checking Service Health")
        print("=" * 60)

        services = [
            ("langflow", LANGFLOW_URL, "/health"),
            ("n8n", N8N_URL, "/healthz"),
            ("mcp", MCP_URL, "/health"),
            ("librarian", LIBRARIAN_URL, "/health"),
            ("chromadb", CHROMADB_URL, "/api/v1/heartbeat"),
            ("qdrant", QDRANT_URL, "/"),
            ("gateway", GATEWAY_URL, "/health"),
        ]

        results = {}
        for name, url, path in services:
            result = await self.check_service(name, url, path)
            results[name] = result
            status = "✅" if result["healthy"] else "❌"
            print(f"  {status} {name}: {url}")

        self.results["services"] = results
        return results

    # =========================================================================
    # Langflow Configuration
    # =========================================================================

    async def get_langflow_token(self) -> Optional[str]:
        """Get Langflow auth token using auto-login"""
        try:
            response = await self.client.post(f"{LANGFLOW_URL}/api/v1/auto_login")
            if response.status_code == 200:
                data = response.json()
                self.langflow_token = data.get("access_token")
                return self.langflow_token
        except Exception as e:
            print(f"  ⚠️  Langflow auto-login failed: {e}")
        return None

    async def get_langflow_headers(self) -> Dict[str, str]:
        """Get headers for Langflow API"""
        if not self.langflow_token:
            await self.get_langflow_token()
        headers = {"Content-Type": "application/json"}
        if self.langflow_token:
            headers["Authorization"] = f"Bearer {self.langflow_token}"
        return headers

    async def get_langflow_flows(self) -> List[Dict]:
        """Get all Langflow flows"""
        headers = await self.get_langflow_headers()
        try:
            response = await self.client.get(
                f"{LANGFLOW_URL}/api/v1/flows", headers=headers
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"  ⚠️  Failed to get flows: {e}")
        return []

    async def configure_langflow_flows(self):
        """Configure Langflow flows with proper wiring"""
        print("\n" + "=" * 60)
        print("🔗 Configuring Langflow Flows")
        print("=" * 60)

        headers = await self.get_langflow_headers()
        flows = await self.get_langflow_flows()

        osmen_flows = [
            f
            for f in flows
            if "osmen" in f.get("name", "").lower()
            or any(
                tag in f.get("name", "").lower()
                for tag in [
                    "coordinator",
                    "specialist",
                    "knowledge",
                    "security",
                    "brief",
                ]
            )
        ]

        print(f"  📋 Found {len(osmen_flows)} OsMEN flows")

        flow_ids = {}
        for flow in osmen_flows:
            flow_name = flow.get("name", "Unknown")
            flow_id = flow.get("id")
            flow_ids[flow_name] = flow_id
            print(f"    • {flow_name}: {flow_id}")

        # Store flow configuration for n8n webhooks
        self.results["langflow"]["flows"] = flow_ids
        self.results["langflow"]["flow_count"] = len(osmen_flows)

        # Create coordinator routing config
        coordinator_config = {
            "flow_routing": {
                "knowledge": next(
                    (
                        fid
                        for fname, fid in flow_ids.items()
                        if "knowledge" in fname.lower()
                    ),
                    None,
                ),
                "security": next(
                    (
                        fid
                        for fname, fid in flow_ids.items()
                        if "security" in fname.lower()
                    ),
                    None,
                ),
                "daily_brief": next(
                    (
                        fid
                        for fname, fid in flow_ids.items()
                        if "brief" in fname.lower()
                    ),
                    None,
                ),
                "research": next(
                    (
                        fid
                        for fname, fid in flow_ids.items()
                        if "research" in fname.lower()
                    ),
                    None,
                ),
            },
            "tools": {
                "mcp_url": MCP_URL,
                "librarian_url": LIBRARIAN_URL,
                "n8n_webhook_base": f"{N8N_URL}/webhook",
            },
        }

        # Save coordinator config
        config_path = BASE_DIR / "config" / "langflow_routing.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(coordinator_config, f, indent=2)
        print(f"  💾 Saved routing config to {config_path}")

        return flow_ids

    # =========================================================================
    # n8n Configuration
    # =========================================================================

    async def activate_n8n_workflows(self):
        """Activate n8n workflows and configure webhooks"""
        print("\n" + "=" * 60)
        print("⚡ Configuring n8n Workflows")
        print("=" * 60)

        # Get workflows from database via CLI
        try:
            import subprocess

            result = subprocess.run(
                ["docker", "exec", "osmen-n8n", "n8n", "list:workflow", "--active=all"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                print(f"  📋 Workflow list output:")
                for line in result.stdout.strip().split("\n")[:10]:
                    print(f"    {line}")
        except Exception as e:
            print(f"  ⚠️  Could not list workflows: {e}")

        # Activate workflows by updating database
        activate_sql = """
        UPDATE workflow_entity 
        SET active = true 
        WHERE name LIKE '%OsMEN%' OR name LIKE '%osmen%';
        """

        try:
            result = subprocess.run(
                [
                    "docker",
                    "exec",
                    "osmen-postgres",
                    "psql",
                    "-U",
                    "postgres",
                    "-d",
                    "n8n",
                    "-c",
                    activate_sql,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                print(f"  ✅ Activated OsMEN workflows")
            else:
                print(f"  ⚠️  Activation result: {result.stderr}")
        except Exception as e:
            print(f"  ⚠️  Could not activate workflows: {e}")

        # Configure webhook paths
        webhook_config = {
            "coordinator": "/webhook/coordinator",
            "daily_brief": "/webhook/daily-brief",
            "knowledge": "/webhook/knowledge-query",
            "security": "/webhook/security-alert",
            "task": "/webhook/task-create",
            "voice": "/webhook/voice-input",
        }

        webhook_config_path = BASE_DIR / "config" / "n8n_webhooks.json"
        with open(webhook_config_path, "w") as f:
            json.dump(webhook_config, f, indent=2)
        print(f"  💾 Saved webhook config to {webhook_config_path}")

        self.results["n8n"]["webhooks"] = webhook_config

        return webhook_config

    # =========================================================================
    # Librarian RAG Configuration
    # =========================================================================

    async def configure_librarian(self):
        """Configure Librarian RAG with ChromaDB"""
        print("\n" + "=" * 60)
        print("📚 Configuring Librarian RAG")
        print("=" * 60)

        # Check Librarian health
        try:
            response = await self.client.get(f"{LIBRARIAN_URL}/health")
            health = response.json()
            print(f"  📊 Librarian Status: {health.get('status', 'unknown')}")
            print(f"  📊 Embedding Model: {health.get('embedding_model', 'unknown')}")
            print(f"  📊 Documents Indexed: {health.get('documents_indexed', 0)}")
            self.results["librarian"]["health"] = health
        except Exception as e:
            print(f"  ⚠️  Librarian not responding: {e}")
            return

        # Index Obsidian vault if available
        obsidian_vault = BASE_DIR / "obsidian-vault"
        if obsidian_vault.exists():
            print(f"  📁 Found Obsidian vault at {obsidian_vault}")

            # Count markdown files
            md_files = list(obsidian_vault.rglob("*.md"))
            print(f"  📄 Found {len(md_files)} markdown files")

            # Trigger indexing via API
            try:
                response = await self.client.post(
                    f"{LIBRARIAN_URL}/index/directory",
                    json={"path": str(obsidian_vault), "recursive": True},
                )
                if response.status_code == 200:
                    result = response.json()
                    print(
                        f"  ✅ Indexed {result.get('documents_indexed', 0)} documents"
                    )
                    self.results["librarian"]["indexed"] = result
            except Exception as e:
                print(f"  ⚠️  Indexing failed: {e}")
        else:
            print(f"  ℹ️  No Obsidian vault found at {obsidian_vault}")

        # Configure ChromaDB collection
        try:
            # Create OsMEN knowledge collection
            response = await self.client.post(
                f"{CHROMADB_URL}/api/v1/collections",
                json={
                    "name": "osmen_knowledge",
                    "metadata": {
                        "description": "OsMEN knowledge base",
                        "created": datetime.now().isoformat(),
                    },
                },
            )
            if response.status_code in [200, 201]:
                print("  ✅ Created ChromaDB collection: osmen_knowledge")
            elif response.status_code == 409:
                print("  ℹ️  ChromaDB collection already exists")
            else:
                print(f"  ⚠️  ChromaDB response: {response.status_code}")
        except Exception as e:
            print(f"  ⚠️  ChromaDB configuration failed: {e}")

        return self.results["librarian"]

    # =========================================================================
    # MCP Bridge Configuration
    # =========================================================================

    async def configure_mcp_bridge(self):
        """Configure MCP server for VS Code integration"""
        print("\n" + "=" * 60)
        print("🔌 Configuring VS Code MCP Bridge")
        print("=" * 60)

        # Check MCP server
        try:
            response = await self.client.get(f"{MCP_URL}/tools")
            if response.status_code == 200:
                tools = response.json()
                tool_count = tools.get("count", len(tools.get("tools", [])))
                print(f"  🔧 MCP Tools Available: {tool_count}")

                # List categories
                categories = tools.get("categories", [])
                for cat in categories:
                    print(f"    • {cat}")

                self.results["mcp"]["tools"] = tool_count
                self.results["mcp"]["categories"] = categories
        except Exception as e:
            print(f"  ⚠️  MCP server not responding: {e}")

        # Create VS Code MCP settings
        vscode_mcp_config = {
            "mcpServers": {
                "osmen": {
                    "command": "python",
                    "args": ["-m", "gateway.mcp.server"],
                    "env": {
                        "MCP_HOST": "localhost",
                        "MCP_PORT": "8081",
                    },
                },
                "osmen-remote": {
                    "url": MCP_URL,
                    "description": "OsMEN Agent Hub via HTTP",
                },
            },
            "osmen": {
                "primaryDriver": "vscode-copilot",
                "agents": {
                    "coordinator": f"{LANGFLOW_URL}/api/v1/run",
                    "librarian": LIBRARIAN_URL,
                    "mcp": MCP_URL,
                },
                "localLLM": {
                    "lmStudio": LM_STUDIO_URL,
                    "ollama": OLLAMA_URL,
                },
            },
        }

        # Save MCP config for VS Code
        mcp_config_path = BASE_DIR / "config" / "vscode_mcp.json"
        with open(mcp_config_path, "w") as f:
            json.dump(vscode_mcp_config, f, indent=2)
        print(f"  💾 Saved VS Code MCP config to {mcp_config_path}")

        # Create .vscode/settings.json if it doesn't exist
        vscode_dir = BASE_DIR / ".vscode"
        vscode_dir.mkdir(exist_ok=True)

        settings_path = vscode_dir / "settings.json"
        settings = {}
        if settings_path.exists():
            try:
                with open(settings_path) as f:
                    settings = json.load(f)
            except:
                pass

        # Add MCP settings
        settings["github.copilot.chat.experimental.mcp.enabled"] = True
        settings["github.copilot.chat.experimental.mcp.servers"] = {
            "osmen": {
                "command": "python",
                "args": ["-m", "gateway.mcp.server"],
                "cwd": str(BASE_DIR),
            }
        }

        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)
        print(f"  💾 Updated .vscode/settings.json with MCP config")

        return vscode_mcp_config

    # =========================================================================
    # Local LLM Configuration
    # =========================================================================

    async def configure_local_llm(self):
        """Configure local LLM routing (LM Studio/Ollama)"""
        print("\n" + "=" * 60)
        print("🤖 Configuring Local LLM Stack")
        print("=" * 60)

        llm_status = {}

        # Check LM Studio
        try:
            response = await self.client.get(f"{LM_STUDIO_URL}/models", timeout=3.0)
            if response.status_code == 200:
                models = response.json()
                model_list = models.get("data", [])
                print(f"  ✅ LM Studio connected - {len(model_list)} models")
                for model in model_list[:3]:
                    print(f"    • {model.get('id', 'unknown')}")
                llm_status["lm_studio"] = {
                    "available": True,
                    "models": [m.get("id") for m in model_list],
                }
        except Exception as e:
            print(f"  ℹ️  LM Studio not available (start manually if needed)")
            llm_status["lm_studio"] = {"available": False, "error": str(e)}

        # Check Ollama
        try:
            response = await self.client.get(f"{OLLAMA_URL}/api/tags", timeout=3.0)
            if response.status_code == 200:
                models = response.json()
                model_list = models.get("models", [])
                print(f"  ✅ Ollama connected - {len(model_list)} models")
                for model in model_list[:5]:
                    print(f"    • {model.get('name', 'unknown')}")
                llm_status["ollama"] = {
                    "available": True,
                    "models": [m.get("name") for m in model_list],
                }
        except Exception as e:
            print(f"  ℹ️  Ollama not available")
            llm_status["ollama"] = {"available": False, "error": str(e)}

        # Create LLM routing config
        llm_config = {
            "default_provider": (
                "lm_studio"
                if llm_status.get("lm_studio", {}).get("available")
                else "ollama"
            ),
            "providers": {
                "lm_studio": {
                    "url": LM_STUDIO_URL,
                    "available": llm_status.get("lm_studio", {}).get(
                        "available", False
                    ),
                    "use_for": ["code", "analysis", "complex_reasoning"],
                },
                "ollama": {
                    "url": OLLAMA_URL,
                    "available": llm_status.get("ollama", {}).get("available", False),
                    "use_for": ["quick_responses", "embeddings", "classification"],
                },
            },
            "agent_routing": {
                "coordinator": "lm_studio",  # Main reasoning
                "knowledge_specialist": "ollama",  # Quick retrieval
                "security_specialist": "lm_studio",  # Careful analysis
                "daily_brief": "ollama",  # Fast summaries
            },
        }

        llm_config_path = BASE_DIR / "config" / "llm_routing.json"
        with open(llm_config_path, "w") as f:
            json.dump(llm_config, f, indent=2)
        print(f"  💾 Saved LLM routing config to {llm_config_path}")

        self.results["local_llm"] = llm_status
        return llm_config

    # =========================================================================
    # Voice/Whisper Configuration
    # =========================================================================

    async def configure_voice(self):
        """Configure voice input with faster-whisper"""
        print("\n" + "=" * 60)
        print("🎤 Configuring Voice/Whisper Integration")
        print("=" * 60)

        voice_config = {
            "whisper": {
                "model": "small",  # Options: tiny, base, small, medium, large
                "device": "cpu",  # or "cuda" for GPU
                "compute_type": "int8",
                "language": "en",
            },
            "pipeline": {
                "input_webhook": f"{N8N_URL}/webhook/voice-input",
                "transcription_flow": "voice_transcription",
                "command_parser": "voice_command_parser",
            },
            "wake_words": ["hey osmen", "osmen", "computer"],
            "output": {
                "tts_enabled": True,
                "tts_engine": "pyttsx3",  # or "elevenlabs", "coqui"
            },
        }

        voice_config_path = BASE_DIR / "config" / "voice.json"
        with open(voice_config_path, "w") as f:
            json.dump(voice_config, f, indent=2)
        print(f"  💾 Saved voice config to {voice_config_path}")

        # Check if faster-whisper is installed
        try:
            import subprocess

            result = subprocess.run(
                [sys.executable, "-c", "import faster_whisper; print('ok')"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if "ok" in result.stdout:
                print("  ✅ faster-whisper is installed")
            else:
                print("  ℹ️  faster-whisper not installed")
                print("     Install with: pip install faster-whisper")
        except Exception as e:
            print(f"  ℹ️  Could not check faster-whisper: {e}")

        return voice_config

    # =========================================================================
    # Main Configuration
    # =========================================================================

    async def configure_all(self):
        """Run full stack configuration"""
        print("\n" + "=" * 60)
        print("🚀 OsMEN Full Stack Configuration")
        print("=" * 60)
        print(f"Started at: {datetime.now().isoformat()}")

        # 1. Check all services
        await self.check_all_services()

        # 2. Configure Langflow
        await self.configure_langflow_flows()

        # 3. Configure n8n
        await self.activate_n8n_workflows()

        # 4. Configure Librarian
        await self.configure_librarian()

        # 5. Configure MCP Bridge
        await self.configure_mcp_bridge()

        # 6. Configure Local LLM
        await self.configure_local_llm()

        # 7. Configure Voice
        await self.configure_voice()

        # Save final results
        results_path = BASE_DIR / "config" / "full_stack_config.json"
        with open(results_path, "w") as f:
            json.dump(self.results, f, indent=2)

        print("\n" + "=" * 60)
        print("✅ Full Stack Configuration Complete!")
        print("=" * 60)
        print(f"\n📁 Configuration files saved to: {BASE_DIR / 'config'}")
        print(f"\n🔗 Service URLs:")
        print(f"   Langflow:  {LANGFLOW_URL}")
        print(f"   n8n:       {N8N_URL}")
        print(f"   MCP:       {MCP_URL}")
        print(f"   Librarian: {LIBRARIAN_URL}")
        print(f"   Gateway:   {GATEWAY_URL}")
        print(f"\n📋 Next Steps:")
        print("   1. Open Langflow at http://localhost:7860")
        print("   2. Open n8n at http://localhost:5678")
        print("   3. In VS Code, enable MCP in Copilot Chat settings")
        print("   4. Start LM Studio/Ollama for local LLM support")
        print("   5. Run 'python check_operational.py' to verify")

        return self.results


async def main():
    configurator = FullStackConfigurator()
    try:
        results = await configurator.configure_all()
    finally:
        await configurator.close()
    return results


if __name__ == "__main__":
    asyncio.run(main())
