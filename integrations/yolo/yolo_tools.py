"""
YOLO-OPS Tool Integration Layer

Unified interface connecting YOLO-OPS to:
- n8n (workflow automation)
- Langflow (LLM agent builder)
- Qdrant (vector database)
- ChromaDB (local vector store)
- Librarian (RAG service)
- MCP Server (Model Context Protocol)
- Copilot CLI/Chat (via MCP)
"""

import os
import json
import httpx
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

# Service endpoints
ENDPOINTS = {
    "n8n": os.getenv("N8N_URL", "http://localhost:5678"),
    "langflow": os.getenv("LANGFLOW_URL", "http://localhost:7860"),
    "qdrant": os.getenv("QDRANT_URL", "http://localhost:6333"),
    "chroma": os.getenv("CHROMA_URL", "http://localhost:8100"),
    "librarian": os.getenv("LIBRARIAN_URL", "http://localhost:8200"),
    "mcp": os.getenv("MCP_URL", "http://localhost:8081"),
    "gateway": os.getenv("GATEWAY_URL", "http://localhost:8080"),
}

TIMEOUT = 30.0


class YoloTools:
    """YOLO-OPS unified tool interface."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        self.session_id = (
            f"YO-{datetime.now().strftime('%Y%m%d-%H%M')}-{os.urandom(2).hex().upper()}"
        )

    async def close(self):
        await self.client.aclose()

    # =========================================================================
    # N8N - Workflow Automation
    # =========================================================================

    async def n8n_trigger_webhook(
        self, webhook_path: str, payload: Dict[str, Any]
    ) -> Dict:
        """Trigger an n8n webhook workflow."""
        url = f"{ENDPOINTS['n8n']}/webhook/{webhook_path}"
        response = await self.client.post(url, json=payload)
        return {
            "status": response.status_code,
            "data": response.json() if response.is_success else response.text,
        }

    async def n8n_list_workflows(self) -> List[Dict]:
        """List all n8n workflows (requires API key)."""
        url = f"{ENDPOINTS['n8n']}/api/v1/workflows"
        headers = {"X-N8N-API-KEY": os.getenv("N8N_API_KEY", "")}
        response = await self.client.get(url, headers=headers)
        return response.json() if response.is_success else []

    async def n8n_execute_workflow(self, workflow_id: str, data: Dict = None) -> Dict:
        """Execute a specific n8n workflow by ID."""
        url = f"{ENDPOINTS['n8n']}/api/v1/workflows/{workflow_id}/execute"
        headers = {"X-N8N-API-KEY": os.getenv("N8N_API_KEY", "")}
        response = await self.client.post(
            url, headers=headers, json={"data": data or {}}
        )
        return response.json() if response.is_success else {"error": response.text}

    # =========================================================================
    # LANGFLOW - Visual LLM Agent Builder
    # =========================================================================

    async def langflow_list_flows(self) -> List[Dict]:
        """List all Langflow flows."""
        url = f"{ENDPOINTS['langflow']}/api/v1/flows"
        response = await self.client.get(url)
        return response.json() if response.is_success else []

    async def langflow_run_flow(
        self, flow_id: str, input_text: str, tweaks: Dict = None
    ) -> Dict:
        """Run a Langflow flow with input."""
        url = f"{ENDPOINTS['langflow']}/api/v1/run/{flow_id}"
        payload = {
            "input_value": input_text,
            "output_type": "chat",
            "input_type": "chat",
            "tweaks": tweaks or {},
        }
        response = await self.client.post(url, json=payload)
        return response.json() if response.is_success else {"error": response.text}

    async def langflow_upload_flow(self, flow_json: Dict) -> Dict:
        """Upload a new flow to Langflow."""
        url = f"{ENDPOINTS['langflow']}/api/v1/flows"
        response = await self.client.post(url, json=flow_json)
        return response.json() if response.is_success else {"error": response.text}

    # =========================================================================
    # QDRANT - Vector Database
    # =========================================================================

    async def qdrant_list_collections(self) -> List[str]:
        """List all Qdrant collections."""
        url = f"{ENDPOINTS['qdrant']}/collections"
        response = await self.client.get(url)
        if response.is_success:
            data = response.json()
            return [c["name"] for c in data.get("result", {}).get("collections", [])]
        return []

    async def qdrant_create_collection(
        self, name: str, vector_size: int = 1536
    ) -> Dict:
        """Create a new Qdrant collection."""
        url = f"{ENDPOINTS['qdrant']}/collections/{name}"
        payload = {"vectors": {"size": vector_size, "distance": "Cosine"}}
        response = await self.client.put(url, json=payload)
        return response.json() if response.is_success else {"error": response.text}

    async def qdrant_search(
        self, collection: str, vector: List[float], limit: int = 10
    ) -> List[Dict]:
        """Search Qdrant collection by vector."""
        url = f"{ENDPOINTS['qdrant']}/collections/{collection}/points/search"
        payload = {"vector": vector, "limit": limit, "with_payload": True}
        response = await self.client.post(url, json=payload)
        return response.json().get("result", []) if response.is_success else []

    async def qdrant_upsert(self, collection: str, points: List[Dict]) -> Dict:
        """Upsert points into Qdrant collection."""
        url = f"{ENDPOINTS['qdrant']}/collections/{collection}/points"
        payload = {"points": points}
        response = await self.client.put(url, json=payload)
        return response.json() if response.is_success else {"error": response.text}

    # =========================================================================
    # CHROMA - Local Vector Store
    # =========================================================================

    async def chroma_list_collections(self) -> List[str]:
        """List all ChromaDB collections."""
        url = f"{ENDPOINTS['chroma']}/api/v1/collections"
        try:
            response = await self.client.get(url)
            return [c["name"] for c in response.json()] if response.is_success else []
        except Exception:
            return []

    async def chroma_create_collection(self, name: str, metadata: Dict = None) -> Dict:
        """Create a ChromaDB collection."""
        url = f"{ENDPOINTS['chroma']}/api/v1/collections"
        payload = {"name": name, "metadata": metadata or {}}
        try:
            response = await self.client.post(url, json=payload)
            return response.json() if response.is_success else {"error": response.text}
        except Exception as e:
            return {"error": str(e)}

    async def chroma_query(
        self, collection: str, query_texts: List[str], n_results: int = 10
    ) -> Dict:
        """Query ChromaDB collection."""
        url = f"{ENDPOINTS['chroma']}/api/v1/collections/{collection}/query"
        payload = {"query_texts": query_texts, "n_results": n_results}
        try:
            response = await self.client.post(url, json=payload)
            return response.json() if response.is_success else {"error": response.text}
        except Exception as e:
            return {"error": str(e)}

    # =========================================================================
    # LIBRARIAN - RAG Service
    # =========================================================================

    async def librarian_health(self) -> Dict:
        """Check Librarian service health."""
        url = f"{ENDPOINTS['librarian']}/health"
        response = await self.client.get(url)
        return response.json() if response.is_success else {"status": "unavailable"}

    async def librarian_index_document(
        self, content: str, metadata: Dict = None
    ) -> Dict:
        """Index a document in Librarian."""
        url = f"{ENDPOINTS['librarian']}/index"
        payload = {"content": content, "metadata": metadata or {}}
        response = await self.client.post(url, json=payload)
        return response.json() if response.is_success else {"error": response.text}

    async def librarian_search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search indexed documents via Librarian."""
        url = f"{ENDPOINTS['librarian']}/search"
        payload = {"query": query, "limit": limit}
        response = await self.client.post(url, json=payload)
        return response.json() if response.is_success else []

    async def librarian_index_file(self, file_path: str) -> Dict:
        """Index a file via Librarian."""
        url = f"{ENDPOINTS['librarian']}/index/file"
        with open(file_path, "rb") as f:
            files = {"file": (Path(file_path).name, f)}
            response = await self.client.post(url, files=files)
        return response.json() if response.is_success else {"error": response.text}

    # =========================================================================
    # MCP - Model Context Protocol
    # =========================================================================

    async def mcp_list_tools(self) -> List[Dict]:
        """List available MCP tools."""
        url = f"{ENDPOINTS['mcp']}/tools"
        response = await self.client.get(url)
        return response.json() if response.is_success else []

    async def mcp_call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """Call an MCP tool."""
        url = f"{ENDPOINTS['mcp']}/tools/{tool_name}"
        response = await self.client.post(url, json=arguments)
        return response.json() if response.is_success else {"error": response.text}

    async def mcp_get_resources(self) -> List[Dict]:
        """Get MCP resources."""
        url = f"{ENDPOINTS['mcp']}/resources"
        response = await self.client.get(url)
        return response.json() if response.is_success else []

    # =========================================================================
    # GATEWAY - Unified Agent API
    # =========================================================================

    async def gateway_chat(self, message: str, agent: str = "coordinator") -> Dict:
        """Send a message through the agent gateway."""
        url = f"{ENDPOINTS['gateway']}/chat"
        payload = {"message": message, "agent": agent, "session_id": self.session_id}
        response = await self.client.post(url, json=payload)
        return response.json() if response.is_success else {"error": response.text}

    async def gateway_health(self) -> Dict:
        """Check gateway health."""
        url = f"{ENDPOINTS['gateway']}/health"
        response = await self.client.get(url)
        return response.json() if response.is_success else {"status": "unavailable"}

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    async def check_all_services(self) -> Dict[str, str]:
        """Check health of all connected services."""
        results = {}

        checks = [
            ("n8n", f"{ENDPOINTS['n8n']}/healthz"),
            ("langflow", f"{ENDPOINTS['langflow']}/health"),
            ("qdrant", f"{ENDPOINTS['qdrant']}/"),
            ("librarian", f"{ENDPOINTS['librarian']}/health"),
            ("mcp", f"{ENDPOINTS['mcp']}/health"),
            ("gateway", f"{ENDPOINTS['gateway']}/health"),
        ]

        for name, url in checks:
            try:
                response = await self.client.get(url, timeout=5.0)
                results[name] = (
                    "healthy"
                    if response.is_success
                    else f"unhealthy ({response.status_code})"
                )
            except Exception as e:
                results[name] = f"unreachable ({type(e).__name__})"

        return results


# Synchronous wrapper for non-async contexts
class YoloToolsSync:
    """Synchronous wrapper for YoloTools."""

    def __init__(self):
        self._async_tools = YoloTools()

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def check_all_services(self) -> Dict[str, str]:
        return self._run(self._async_tools.check_all_services())

    def n8n_trigger_webhook(self, webhook_path: str, payload: Dict) -> Dict:
        return self._run(self._async_tools.n8n_trigger_webhook(webhook_path, payload))

    def langflow_run_flow(self, flow_id: str, input_text: str) -> Dict:
        return self._run(self._async_tools.langflow_run_flow(flow_id, input_text))

    def qdrant_search(
        self, collection: str, vector: List[float], limit: int = 10
    ) -> List:
        return self._run(self._async_tools.qdrant_search(collection, vector, limit))

    def librarian_search(self, query: str, limit: int = 10) -> List:
        return self._run(self._async_tools.librarian_search(query, limit))

    def gateway_chat(self, message: str, agent: str = "coordinator") -> Dict:
        return self._run(self._async_tools.gateway_chat(message, agent))


# Quick access functions
def get_tools() -> YoloTools:
    """Get async tools instance."""
    return YoloTools()


def get_tools_sync() -> YoloToolsSync:
    """Get sync tools instance."""
    return YoloToolsSync()


if __name__ == "__main__":
    # Quick test
    async def main():
        tools = YoloTools()
        print("Checking services...")
        status = await tools.check_all_services()
        for service, health in status.items():
            print(f"  {service}: {health}")
        await tools.close()

    asyncio.run(main())
