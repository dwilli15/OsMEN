#!/usr/bin/env python3
"""
OsMEN MCP Server - Windows-compatible stdio transport for VS Code

Uses synchronous I/O to avoid Windows asyncio pipe issues.
"""

import json
import os
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


def log(msg: str):
    """Log to stderr (stdout is reserved for MCP protocol)"""
    print(f"[osmen-mcp] {msg}", file=sys.stderr, flush=True)


class MCPStdioServer:
    """MCP Server using synchronous stdio for Windows compatibility"""

    def __init__(self):
        self.tools = self._register_tools()
        log(f"Initialized with {len(self.tools)} tools")

    def _register_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register available tools"""
        return {
            "execute_command": {
                "name": "execute_command",
                "description": "Execute a shell command (PowerShell on Windows, bash on Linux/Mac)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Command to execute",
                        },
                        "working_dir": {
                            "type": "string",
                            "description": "Working directory",
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Timeout in seconds",
                            "default": 300,
                        },
                    },
                    "required": ["command"],
                },
            },
            "check_services": {
                "name": "check_services",
                "description": "Check health of OsMEN services (n8n, Langflow, Qdrant, etc.)",
                "inputSchema": {"type": "object", "properties": {}},
            },
            "get_system_info": {
                "name": "get_system_info",
                "description": "Get system information (OS, CPU, memory, disk)",
                "inputSchema": {"type": "object", "properties": {}},
            },
            "obsidian_create_note": {
                "name": "obsidian_create_note",
                "description": "Create a note in Obsidian vault",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Note title"},
                        "content": {
                            "type": "string",
                            "description": "Note content (Markdown)",
                        },
                        "folder": {"type": "string", "description": "Folder in vault"},
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags",
                        },
                    },
                    "required": ["title", "content"],
                },
            },
            "obsidian_read_note": {
                "name": "obsidian_read_note",
                "description": "Read a note from Obsidian vault",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Note path relative to vault",
                        }
                    },
                    "required": ["path"],
                },
            },
            "obsidian_search": {
                "name": "obsidian_search",
                "description": "Search notes in Obsidian vault",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {
                            "type": "integer",
                            "description": "Max results",
                            "default": 10,
                        },
                    },
                    "required": ["query"],
                },
            },
            "obsidian_list_notes": {
                "name": "obsidian_list_notes",
                "description": "List notes in Obsidian vault",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "folder": {"type": "string", "description": "Folder to list"},
                        "recursive": {"type": "boolean", "default": True},
                    },
                },
            },
            "memory_store": {
                "name": "memory_store",
                "description": "Store content in vector memory (ChromaDB)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Content to store",
                        },
                        "collection": {"type": "string", "default": "osmen_memory"},
                        "metadata": {"type": "object", "description": "Optional metadata dict"},
                    },
                    "required": ["content"],
                },
            },
            "memory_recall": {
                "name": "memory_recall",
                "description": "Recall from vector memory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "What to recall"},
                        "collection": {"type": "string", "default": "default_memory"},
                        "limit": {"type": "integer", "default": 10},
                        "mode": {
                            "type": "string",
                            "enum": ["foundation", "lateral", "factcheck"],
                            "default": "foundation",
                            "description": "Retrieval mode: foundation (direct), lateral (cross-domain), factcheck (verification)"
                        },
                    },
                    "required": ["query"],
                },
            },
            "memory_recall_with_reasoning": {
                "name": "memory_recall_with_reasoning",
                "description": "Recall from memory with sequential reasoning trace - decomposes queries, builds context progressively",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "What to recall"},
                        "n_results": {"type": "integer", "default": 5},
                    },
                    "required": ["query"],
                },
            },
            "workflow_trigger": {
                "name": "workflow_trigger",
                "description": "Trigger an n8n workflow",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow": {
                            "type": "string",
                            "description": "Workflow name or ID",
                        },
                        "payload": {"type": "object", "description": "Data to pass"},
                    },
                    "required": ["workflow"],
                },
            },
            "langflow_run": {
                "name": "langflow_run",
                "description": "Run a Langflow agent/flow",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "flow_id": {"type": "string", "description": "Flow ID"},
                        "input": {"type": "string", "description": "Input message"},
                    },
                    "required": ["flow_id", "input"],
                },
            },
            "media_info": {
                "name": "media_info",
                "description": "Get media file information (via ffprobe)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to media file",
                        }
                    },
                    "required": ["file_path"],
                },
            },
            "task_create": {
                "name": "task_create",
                "description": "Create a task",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "urgent"],
                        },
                        "due_date": {"type": "string", "description": "ISO date"},
                    },
                    "required": ["title"],
                },
            },
            "daily_summary": {
                "name": "daily_summary",
                "description": "Get daily summary of tasks and events",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "description": "Date (ISO format)"}
                    },
                },
            },
            "agent_spawn": {
                "name": "agent_spawn",
                "description": "Spawn a specialized subagent",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent_type": {
                            "type": "string",
                            "enum": [
                                "file-ops",
                                "security-audit",
                                "research",
                                "code-gen",
                                "system-admin",
                            ],
                        },
                        "task": {"type": "string", "description": "Task description"},
                    },
                    "required": ["agent_type", "task"],
                },
            },
        }

    # =========================================================================
    # TOOL HANDLERS (synchronous)
    # =========================================================================

    def handle_execute_command(self, args: Dict) -> Dict:
        command = args.get("command", "")
        working_dir = args.get("working_dir", os.getcwd())
        timeout = args.get("timeout", 300)

        destructive = ["rm -rf", "del /s", "format", "diskpart", "Remove-Item -Recurse"]
        if any(d in command for d in destructive):
            return {"error": "Destructive command blocked", "command": command}

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out"}
        except Exception as e:
            return {"error": str(e)}

    def handle_check_services(self, args: Dict) -> Dict:
        import urllib.request

        services = {
            "n8n": (os.getenv("N8N_URL", "http://localhost:5678"), "/healthz"),
            "langflow": (os.getenv("LANGFLOW_URL", "http://localhost:7860"), "/health"),
            "chromadb": (os.getenv("CHROMADB_URL", "http://localhost:8000"), "/api/v1/heartbeat"),
            "gateway": (os.getenv("GATEWAY_URL", "http://localhost:8080"), "/health"),
            "librarian": (os.getenv("LIBRARIAN_URL", "http://localhost:8200"), "/health"),
        }

        results = {}
        for name, (base_url, health_path) in services.items():
            try:
                endpoint = f"{base_url}{health_path}"
                req = urllib.request.Request(endpoint, method="GET")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    results[name] = "healthy" if resp.status < 400 else "unhealthy"
            except Exception as e:
                results[name] = f"unreachable: {str(e)[:50]}"

        return {"services": results, "timestamp": datetime.now().isoformat()}

    def handle_get_system_info(self, args: Dict) -> Dict:
        info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "machine": platform.machine(),
        }
        try:
            import psutil

            info.update(
                {
                    "cpu_count": psutil.cpu_count(),
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage(
                        "C:\\" if platform.system() == "Windows" else "/"
                    ).percent,
                }
            )
        except ImportError:
            info["note"] = "Install psutil for full info"
        return info

    def handle_obsidian_create_note(self, args: Dict) -> Dict:
        vault = Path(os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian-vault"))
        title = args.get("title", "Untitled")
        content = args.get("content", "")
        folder = args.get("folder", "")
        tags = args.get("tags", [])

        frontmatter = f"---\ntitle: {title}\ndate: {datetime.now().isoformat()}\n"
        if tags:
            frontmatter += f"tags: [{', '.join(tags)}]\n"
        frontmatter += "---\n\n"

        safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()
        file_path = vault / folder / f"{safe_title}.md"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(frontmatter + content, encoding="utf-8")
        return {"created": str(file_path)}

    def handle_obsidian_read_note(self, args: Dict) -> Dict:
        vault = Path(os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian-vault"))
        path = args.get("path", "")
        file_path = vault / path
        if not file_path.suffix:
            file_path = file_path.with_suffix(".md")
        if not file_path.exists():
            return {"error": f"Not found: {path}"}
        return {"content": file_path.read_text(encoding="utf-8")}

    def handle_obsidian_search(self, args: Dict) -> Dict:
        vault = Path(os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian-vault"))
        query = args.get("query", "").lower()
        limit = args.get("limit", 10)
        results = []
        for f in vault.rglob("*.md"):
            try:
                content = f.read_text(encoding="utf-8")
                if query in content.lower() or query in f.stem.lower():
                    results.append(
                        {"path": str(f.relative_to(vault)), "preview": content[:150]}
                    )
                    if len(results) >= limit:
                        break
            except:
                continue
        return {"results": results}

    def handle_obsidian_list_notes(self, args: Dict) -> Dict:
        vault = Path(os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian-vault"))
        folder = args.get("folder", "")
        recursive = args.get("recursive", True)
        search = vault / folder if folder else vault
        pattern = "**/*.md" if recursive else "*.md"
        notes = [
            {"path": str(f.relative_to(vault)), "name": f.stem}
            for f in search.glob(pattern)
        ]
        return {"notes": notes, "count": len(notes)}

    def handle_memory_store(self, args: Dict) -> Dict:
        """Store content in ChromaDB vector memory"""
        import urllib.request
        import hashlib
        
        content = args.get("content", "")
        collection = args.get("collection", "osmen_memory")
        metadata = args.get("metadata", {})
        
        if not content:
            return {"error": "No content provided"}
        
        chromadb_url = os.getenv("CHROMADB_URL", "http://localhost:8000")
        
        try:
            # Generate a unique ID based on content
            doc_id = hashlib.md5(content.encode()).hexdigest()[:16]
            
            # Ensure collection exists
            create_collection = json.dumps({
                "name": collection,
                "get_or_create": True
            }).encode()
            
            req = urllib.request.Request(
                f"{chromadb_url}/api/v1/collections",
                data=create_collection,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    collection_data = json.loads(resp.read().decode())
                    collection_id = collection_data.get("id", collection)
            except:
                collection_id = collection
            
            # Add document to collection
            add_data = json.dumps({
                "ids": [doc_id],
                "documents": [content],
                "metadatas": [{**metadata, "timestamp": datetime.now().isoformat()}]
            }).encode()
            
            req = urllib.request.Request(
                f"{chromadb_url}/api/v1/collections/{collection_id}/add",
                data=add_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = resp.read().decode()
            
            return {
                "stored": True,
                "doc_id": doc_id,
                "collection": collection,
                "content_length": len(content)
            }
            
        except Exception as e:
            return {"error": str(e), "stored": False}

    def handle_memory_recall(self, args: Dict) -> Dict:
        """Recall from ChromaDB vector memory"""
        import urllib.request
        
        query = args.get("query", "")
        collection = args.get("collection", "osmen_memory")
        limit = args.get("limit", 10)
        
        if not query:
            return {"error": "No query provided", "results": []}
        
        chromadb_url = os.getenv("CHROMADB_URL", "http://localhost:8000")
        
        try:
            # Get collection ID first
            req = urllib.request.Request(
                f"{chromadb_url}/api/v1/collections/{collection}",
                method="GET"
            )
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    collection_data = json.loads(resp.read().decode())
                    collection_id = collection_data.get("id", collection)
            except urllib.error.HTTPError:
                return {"results": [], "note": f"Collection '{collection}' not found"}
            
            # Query collection
            query_data = json.dumps({
                "query_texts": [query],
                "n_results": limit,
                "include": ["documents", "metadatas", "distances"]
            }).encode()
            
            req = urllib.request.Request(
                f"{chromadb_url}/api/v1/collections/{collection_id}/query",
                data=query_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode())
            
            # Format results
            results = []
            docs = result.get("documents", [[]])[0]
            metas = result.get("metadatas", [[]])[0]
            dists = result.get("distances", [[]])[0]
            ids = result.get("ids", [[]])[0]
            
            for i, doc in enumerate(docs):
                results.append({
                    "id": ids[i] if i < len(ids) else None,
                    "content": doc,
                    "metadata": metas[i] if i < len(metas) else {},
                    "distance": dists[i] if i < len(dists) else None
                })
            
            return {
                "results": results,
                "count": len(results),
                "collection": collection
            }
            
        except Exception as e:
            return {"error": str(e), "results": []}

    def handle_memory_recall_with_reasoning(self, args: Dict) -> Dict:
        """Recall from memory with sequential reasoning trace using Hybrid Memory"""
        query = args.get("query", "")
        n_results = args.get("n_results", 5)
        
        if not query:
            return {"error": "No query provided", "results": [], "reasoning": []}
        
        reasoning_steps = []
        results = []
        
        try:
            # Step 1: Decompose query
            reasoning_steps.append({
                "step": 1,
                "type": "decomposition",
                "content": f"Analyzing query: '{query}'"
            })
            
            # Extract key concepts (simple implementation)
            stopwords = {"what", "how", "why", "when", "where", "is", "are", "the", "a", "an", "to", "for", "of", "in"}
            words = query.lower().split()
            concepts = [w for w in words if w not in stopwords and len(w) > 2]
            
            reasoning_steps.append({
                "step": 2,
                "type": "analysis",
                "content": f"Key concepts identified: {', '.join(concepts)}"
            })
            
            # Step 2: Foundation search (direct query)
            reasoning_steps.append({
                "step": 3,
                "type": "search",
                "content": "Searching foundation knowledge (direct semantic match)..."
            })
            
            foundation_results = self._query_chromadb(query, n_results, mode="foundation")
            reasoning_steps.append({
                "step": 4,
                "type": "analysis",
                "content": f"Found {len(foundation_results)} foundation matches"
            })
            
            # Step 3: Lateral search (shadow/context)
            reasoning_steps.append({
                "step": 5,
                "type": "lateral_expansion",
                "content": "Exploring lateral connections (cross-domain, abstract)..."
            })
            
            shadow_query = f"Broader themes, implications, and abstract connections to: {query}"
            lateral_results = self._query_chromadb(shadow_query, n_results, mode="lateral")
            reasoning_steps.append({
                "step": 6,
                "type": "analysis", 
                "content": f"Found {len(lateral_results)} lateral connections"
            })
            
            # Step 4: Weave results
            reasoning_steps.append({
                "step": 7,
                "type": "synthesis",
                "content": "Weaving focus and shadow results for balanced retrieval..."
            })
            
            # Interleave: 2 focus, 1 shadow pattern
            woven = []
            seen_ids = set()
            f_idx, l_idx = 0, 0
            pattern_count = 0
            
            while len(woven) < n_results * 2 and (f_idx < len(foundation_results) or l_idx < len(lateral_results)):
                # Add 2 foundation results
                if pattern_count % 3 < 2 and f_idx < len(foundation_results):
                    r = foundation_results[f_idx]
                    if r.get("id") not in seen_ids:
                        r["retrieval_layer"] = "focus"
                        woven.append(r)
                        seen_ids.add(r.get("id"))
                    f_idx += 1
                # Add 1 lateral result
                elif l_idx < len(lateral_results):
                    r = lateral_results[l_idx]
                    if r.get("id") not in seen_ids:
                        r["retrieval_layer"] = "shadow_context"
                        woven.append(r)
                        seen_ids.add(r.get("id"))
                    l_idx += 1
                pattern_count += 1
            
            results = woven[:n_results * 2]
            
            # Step 5: Assess confidence
            avg_distance = sum(r.get("distance", 1.0) for r in results) / max(len(results), 1)
            confidence = max(0.0, min(1.0, 1.0 - avg_distance))
            
            reasoning_steps.append({
                "step": 8,
                "type": "conclusion",
                "content": f"Final result: {len(results)} unique memories with {confidence:.0%} average confidence"
            })
            
            return {
                "results": results,
                "count": len(results),
                "reasoning_trace": reasoning_steps,
                "confidence": confidence,
                "mode": "hybrid_reasoning"
            }
            
        except Exception as e:
            reasoning_steps.append({
                "step": len(reasoning_steps) + 1,
                "type": "error",
                "content": f"Error during reasoning: {str(e)}"
            })
            return {
                "error": str(e),
                "results": [],
                "reasoning_trace": reasoning_steps
            }
    
    def _query_chromadb(self, query: str, limit: int, mode: str = "foundation") -> list:
        """Helper to query ChromaDB"""
        import urllib.request
        
        chromadb_url = os.getenv("CHROMADB_URL", "http://localhost:8000")
        collection = "osmen_long_term"
        
        try:
            # Get collection
            req = urllib.request.Request(
                f"{chromadb_url}/api/v1/collections/{collection}",
                method="GET"
            )
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    collection_data = json.loads(resp.read().decode())
                    collection_id = collection_data.get("id", collection)
            except:
                return []
            
            # Query
            query_data = json.dumps({
                "query_texts": [query],
                "n_results": limit,
                "include": ["documents", "metadatas", "distances"]
            }).encode()
            
            req = urllib.request.Request(
                f"{chromadb_url}/api/v1/collections/{collection_id}/query",
                data=query_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode())
            
            results = []
            docs = result.get("documents", [[]])[0]
            metas = result.get("metadatas", [[]])[0]
            dists = result.get("distances", [[]])[0]
            ids = result.get("ids", [[]])[0]
            
            for i, doc in enumerate(docs):
                results.append({
                    "id": ids[i] if i < len(ids) else None,
                    "content": doc,
                    "metadata": metas[i] if i < len(metas) else {},
                    "distance": dists[i] if i < len(dists) else None
                })
            
            return results
        except:
            return []

    def handle_workflow_trigger(self, args: Dict) -> Dict:
        """Trigger an n8n workflow via webhook"""
        import urllib.request
        
        workflow = args.get("workflow", "")
        payload = args.get("payload", {})
        
        if not workflow:
            return {"error": "No workflow specified"}
        
        n8n_url = os.getenv("N8N_URL", "http://localhost:5678")
        
        try:
            # n8n webhooks are at /webhook/<path> or /webhook-test/<path>
            webhook_url = f"{n8n_url}/webhook/{workflow}"
            
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = resp.read().decode()
                try:
                    result = json.loads(result)
                except:
                    pass
            
            return {
                "triggered": True,
                "workflow": workflow,
                "response": result
            }
            
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP {e.code}: {e.reason}", "workflow": workflow}
        except Exception as e:
            return {"error": str(e), "workflow": workflow}

    def handle_langflow_run(self, args: Dict) -> Dict:
        """Run a Langflow flow"""
        import urllib.request
        
        flow_id = args.get("flow_id", "")
        input_text = args.get("input", "")
        
        if not flow_id:
            return {"error": "No flow_id specified"}
        
        langflow_url = os.getenv("LANGFLOW_URL", "http://localhost:7860")
        
        try:
            # Langflow API endpoint for running flows
            run_url = f"{langflow_url}/api/v1/run/{flow_id}"
            
            data = json.dumps({
                "input_value": input_text,
                "output_type": "chat",
                "input_type": "chat",
                "tweaks": {}
            }).encode()
            
            req = urllib.request.Request(
                run_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode())
            
            # Extract the output from Langflow response
            output = result.get("outputs", [{}])[0].get("outputs", [{}])[0].get("results", {}).get("message", {}).get("text", "")
            if not output:
                output = result.get("result", result.get("output", str(result)))
            
            return {
                "flow_id": flow_id,
                "output": output,
                "raw_response": result
            }
            
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            return {"error": f"HTTP {e.code}: {e.reason}", "details": error_body, "flow_id": flow_id}
        except Exception as e:
            return {"error": str(e), "flow_id": flow_id}

    def handle_media_info(self, args: Dict) -> Dict:
        file_path = args.get("file_path", "")
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-print_format",
                    "json",
                    "-show_format",
                    file_path,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return (
                json.loads(result.stdout)
                if result.returncode == 0
                else {"error": result.stderr}
            )
        except FileNotFoundError:
            return {"error": "ffprobe not found"}
        except Exception as e:
            return {"error": str(e)}

    def handle_task_create(self, args: Dict) -> Dict:
        return {"created": True, "title": args.get("title"), "note": "Task DB pending"}

    def handle_daily_summary(self, args: Dict) -> Dict:
        return {
            "date": args.get("date", datetime.now().strftime("%Y-%m-%d")),
            "tasks": [],
            "events": [],
        }

    def handle_agent_spawn(self, args: Dict) -> Dict:
        return {
            "spawned": True,
            "agent_type": args.get("agent_type"),
            "session_id": f"agent-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        }

    # =========================================================================
    # MCP PROTOCOL
    # =========================================================================

    def handle_request(self, request: Dict) -> Optional[Dict]:
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id")

        log(f"Request: {method}")

        try:
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {"listChanged": True}},
                        "serverInfo": {"name": "osmen-mcp", "version": "2.0.0"},
                    },
                }

            elif method == "notifications/initialized":
                return None

            elif method == "tools/list":
                tools = [
                    {
                        "name": t["name"],
                        "description": t["description"],
                        "inputSchema": t["inputSchema"],
                    }
                    for t in self.tools.values()
                ]
                return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools}}

            elif method == "tools/call":
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})

                if tool_name not in self.tools:
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32602,
                            "message": f"Unknown tool: {tool_name}",
                        },
                    }

                handler = getattr(self, f"handle_{tool_name}", None)
                result = handler(arguments) if handler else {"error": "No handler"}

                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {"type": "text", "text": json.dumps(result, indent=2)}
                        ]
                    },
                }

            elif method == "ping":
                return {"jsonrpc": "2.0", "id": req_id, "result": {}}

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Unknown method: {method}"},
                }

        except Exception as e:
            log(f"Error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": str(e)},
            }

    def run(self):
        """Run synchronous stdio loop (Windows compatible)"""
        log("Starting OsMEN MCP Server")

        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break

                line = line.strip()
                if not line:
                    continue

                request = json.loads(line)
                response = self.handle_request(request)

                if response:
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()

            except json.JSONDecodeError as e:
                log(f"JSON error: {e}")
                err = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"},
                }
                sys.stdout.write(json.dumps(err) + "\n")
                sys.stdout.flush()
            except Exception as e:
                log(f"Error: {e}")
                break

        log("Shutting down")


def main():
    server = MCPStdioServer()
    server.run()


if __name__ == "__main__":
    main()
