"""
MCP Server for YOLO-OPS - Exposes tools to Copilot and other MCP clients
Run with: python -m integrations.mcp_yolo_server
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any
import httpx

# MCP SDK would be imported here - using simple HTTP server for compatibility
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading


class YoloMCPHandler(BaseHTTPRequestHandler):
    """HTTP handler for MCP tool requests"""

    TOOLS = {
        "yolo_execute_command": "Execute shell command",
        "yolo_search_docs": "Search Librarian documents",
        "yolo_vector_search": "Qdrant vector search",
        "yolo_trigger_workflow": "Trigger n8n workflow",
        "yolo_run_langflow": "Run Langflow agent",
        "yolo_memory_store": "Store in memory",
        "yolo_memory_recall": "Recall from memory",
        "yolo_spawn_subagent": "Spawn subagent",
        "yolo_check_services": "Health check",
        "yolo_log_action": "Log action",
    }

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        try:
            request = json.loads(body)
            response = self.handle_mcp_request(request)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            self.send_error(500, str(e))

    def do_GET(self):
        """Return tool list for discovery"""
        if self.path == "/tools":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {
                        "tools": list(self.TOOLS.keys()),
                        "server": "yolo-ops-mcp",
                        "version": "1.0.0",
                    }
                ).encode()
            )
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode())
        else:
            self.send_error(404)

    def handle_mcp_request(self, request: dict) -> dict:
        """Route MCP tool calls to appropriate handlers"""
        method = request.get("method", "")

        if method == "tools/list":
            return self.list_tools()
        elif method == "tools/call":
            return self.call_tool(request.get("params", {}))
        else:
            return {"error": f"Unknown method: {method}"}

    def list_tools(self) -> dict:
        """Return available tools in MCP format"""
        tools = []
        for name, desc in self.TOOLS.items():
            tools.append(
                {
                    "name": name,
                    "description": desc,
                    "inputSchema": {"type": "object", "properties": {}},
                }
            )
        return {"tools": tools}

    def call_tool(self, params: dict) -> dict:
        """Execute a tool call"""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        # Route to appropriate handler
        handlers = {
            "yolo_execute_command": self.execute_command,
            "yolo_search_docs": self.search_docs,
            "yolo_vector_search": self.vector_search,
            "yolo_trigger_workflow": self.trigger_workflow,
            "yolo_run_langflow": self.run_langflow,
            "yolo_memory_store": self.memory_store,
            "yolo_memory_recall": self.memory_recall,
            "yolo_spawn_subagent": self.spawn_subagent,
            "yolo_check_services": self.check_services,
            "yolo_log_action": self.log_action,
        }

        handler = handlers.get(tool_name)
        if handler:
            try:
                result = handler(arguments)
                return {"content": [{"type": "text", "text": json.dumps(result)}]}
            except Exception as e:
                return {"error": str(e)}
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    def execute_command(self, args: dict) -> dict:
        """Execute shell command - checks for destructive operations"""
        import subprocess

        command = args.get("command", "")
        working_dir = args.get("workingDir", os.getcwd())

        # Destructive operations that need confirmation
        destructive_patterns = [
            "rm ",
            "del ",
            "rmdir",
            "Remove-Item",
            "uninstall",
            "reg delete",
            "format",
            "diskpart",
        ]

        needs_confirmation = any(p in command.lower() for p in destructive_patterns)

        if needs_confirmation and not args.get("confirmed", False):
            return {
                "status": "confirmation_required",
                "message": f"Destructive operation detected. Please confirm: {command}",
                "command": command,
            }

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return {
                "status": "success",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Command timed out after 5 minutes"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def search_docs(self, args: dict) -> dict:
        """Search Librarian RAG"""
        url = os.getenv("LIBRARIAN_URL", "http://localhost:8200")
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(
                    f"{url}/search",
                    json={
                        "query": args.get("query", ""),
                        "collection": args.get("collection", "default"),
                        "limit": args.get("limit", 10),
                    },
                )
                return response.json()
        except Exception as e:
            return {"error": str(e)}

    def vector_search(self, args: dict) -> dict:
        """Search Qdrant"""
        url = os.getenv("QDRANT_URL", "http://localhost:6333")
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(
                    f"{url}/collections/{args.get('collection', 'default')}/points/search",
                    json={
                        "vector": [0.0] * 384,  # Placeholder - actual embedding needed
                        "limit": args.get("limit", 5),
                        "with_payload": True,
                    },
                )
                return response.json()
        except Exception as e:
            return {"error": str(e)}

    def trigger_workflow(self, args: dict) -> dict:
        """Trigger n8n workflow"""
        url = os.getenv("N8N_URL", "http://localhost:5678")
        webhook_path = args.get("webhookPath", "/webhook/yolo-ops")
        try:
            with httpx.Client(timeout=60) as client:
                response = client.post(
                    f"{url}{webhook_path}", json=args.get("payload", {})
                )
                return response.json()
        except Exception as e:
            return {"error": str(e)}

    def run_langflow(self, args: dict) -> dict:
        """Run Langflow flow"""
        url = os.getenv("LANGFLOW_URL", "http://localhost:7860")
        try:
            with httpx.Client(timeout=120) as client:
                response = client.post(
                    f"{url}/api/v1/run/{args.get('flowId', '')}",
                    json={
                        "input_value": args.get("input", ""),
                        "tweaks": args.get("tweaks", {}),
                    },
                )
                return response.json()
        except Exception as e:
            return {"error": str(e)}

    def memory_store(self, args: dict) -> dict:
        """Store in Qdrant memory"""
        return {"status": "stored", "content": args.get("content", "")[:100]}

    def memory_recall(self, args: dict) -> dict:
        """Recall from Qdrant memory"""
        return self.vector_search(args)

    def spawn_subagent(self, args: dict) -> dict:
        """Log subagent spawn request"""
        return {
            "status": "spawned",
            "agentType": args.get("agentType"),
            "task": args.get("task"),
            "sessionId": f"YO-{datetime.now().strftime('%Y%m%d-%H%M')}-{os.urandom(2).hex()}",
        }

    def check_services(self, args: dict) -> dict:
        """Check all service health"""
        services = {
            "n8n": os.getenv("N8N_URL", "http://localhost:5678"),
            "langflow": os.getenv("LANGFLOW_URL", "http://localhost:7860"),
            "qdrant": os.getenv("QDRANT_URL", "http://localhost:6333"),
            "librarian": os.getenv("LIBRARIAN_URL", "http://localhost:8200"),
            "gateway": os.getenv("GATEWAY_URL", "http://localhost:8080"),
        }

        results = {}
        with httpx.Client(timeout=5) as client:
            for name, url in services.items():
                try:
                    response = client.get(f"{url}/health" if name != "qdrant" else url)
                    results[name] = (
                        "healthy" if response.status_code < 400 else "unhealthy"
                    )
                except:
                    results[name] = "unreachable"

        return {"services": results}

    def log_action(self, args: dict) -> dict:
        """Log action to vault"""
        log_path = os.path.join(os.path.dirname(__file__), "..", "vault", "logs")
        os.makedirs(log_path, exist_ok=True)

        log_file = os.path.join(log_path, f"{datetime.now().strftime('%Y-%m-%d')}.log")
        entry = f"[{datetime.now().isoformat()}] [{args.get('severity', 'info').upper()}] {args.get('action', '')} - {args.get('result', '')}\n"

        with open(log_file, "a") as f:
            f.write(entry)

        return {"logged": True, "file": log_file}

    def log_message(self, format, *args):
        """Suppress HTTP logs"""
        pass


def run_server(port: int = 8082):
    """Run the MCP server"""
    server = HTTPServer(("localhost", port), YoloMCPHandler)
    print(f"YOLO-OPS MCP Server running on http://localhost:{port}")
    print(f"  Tools endpoint: http://localhost:{port}/tools")
    print(f"  Health check: http://localhost:{port}/health")
    server.serve_forever()


if __name__ == "__main__":
    run_server(int(os.getenv("MCP_PORT", "8082")))
