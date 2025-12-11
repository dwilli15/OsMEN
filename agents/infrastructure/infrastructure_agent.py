#!/usr/bin/env python3
"""
Infrastructure Agent for OsMEN Workspace

Central intelligence for workspace infrastructure management:
- Node registry with service discovery
- Tool inventory with capability manifests
- Connection graph (agents↔tools↔nodes↔pipelines)
- Dynamic context injection for agent awareness
- Expectations verification on startup
- Infrastructure-aware query handling
"""

import asyncio
import importlib
import importlib.util
import json
import logging
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Types of infrastructure nodes"""

    WORKFLOW_ENGINE = "workflow_engine"
    WORKFLOW_AUTOMATION = "workflow_automation"
    LLM_INFERENCE = "llm_inference"
    VECTOR_DATABASE = "vector_database"
    DATABASE = "database"
    CACHE = "cache"
    API_GATEWAY = "api_gateway"
    PROTOCOL_SERVER = "protocol_server"
    FILE_CONVERTER = "file_converter"
    RAG_ENGINE = "rag_engine"


class ToolType(Enum):
    """Types of tools"""

    SYSTEM_TOOLS = "system_tools"
    FIREWALL = "firewall"
    MEDIA_PROCESSING = "media_processing"
    AI_ASSISTANT = "ai_assistant"
    KNOWLEDGE_MANAGEMENT = "knowledge_management"
    FILE_CONVERTER = "file_converter"
    DOCUMENT_PARSER = "document_parser"


@dataclass
class NodeInfo:
    """Information about an infrastructure node"""

    node_id: str
    name: str
    node_type: str
    endpoint: str
    port: int
    status: str
    capabilities: List[str]
    dependencies: List[str]
    last_verified: Optional[str] = None


@dataclass
class ToolInfo:
    """Information about a tool"""

    tool_id: str
    name: str
    tool_type: str
    path: str
    status: str
    capabilities: Dict[str, Any]
    health_check: Optional[str] = None
    last_verified: Optional[str] = None


@dataclass
class AgentInfo:
    """Information about an agent"""

    agent_id: str
    name: str
    path: str
    uses_tools: List[str]
    uses_nodes: List[str]
    provides: List[str]
    consumes: List[str]
    context_requirements: Dict[str, Any]


@dataclass
class PipelineInfo:
    """Information about a pipeline"""

    pipeline_id: str
    name: str
    description: str
    stages: List[Dict[str, Any]]
    triggers: List[str]
    requires_approval: bool = False
    # New fields for Langflow/n8n pipelines
    pipeline_type: str = "native"  # "native", "langflow", "n8n"
    path: Optional[str] = None
    port: Optional[int] = None
    connected_agent: Optional[str] = None
    connected_langflow: Optional[str] = None
    connected_service: Optional[str] = None
    connected_pipeline: Optional[str] = None
    autonomous: bool = False
    requires_auth: bool = False


@dataclass
class ContextInjection:
    """Context injection for an agent"""

    agent_id: str
    timestamp: str
    injected_context: Dict[str, Any]
    token_estimate: int
    sources: List[str]


class InfrastructureAgent:
    """
    Infrastructure Agent - The workspace's "tech admin".

    Responsibilities:
    - Maintain and query node registry
    - Track tool inventory with capability manifests
    - Manage connection graph between components
    - Provide dynamic context injection for agents
    - Verify expectations on startup
    - Answer infrastructure queries from other agents
    - Load and expose workspace map for full workspace awareness
    """

    def __init__(self):
        """Initialize the Infrastructure Agent."""
        self.base_path = Path(__file__).parent.parent.parent
        self.infrastructure_path = self.base_path / "infrastructure"
        self.knowledge_path = self.base_path / "knowledge"
        self.workspace_path = self.base_path / "workspace"

        # Registries
        self.nodes: Dict[str, NodeInfo] = {}
        self.tools: Dict[str, ToolInfo] = {}
        self.agents: Dict[str, AgentInfo] = {}
        self.pipelines: Dict[str, PipelineInfo] = {}

        # Workspace map (dynamic workspace awareness)
        self.workspace_map: Optional[Dict[str, Any]] = None
        self._workspace_map_path = self.infrastructure_path / "workspace_map.json"

        # Context injection tracking
        self.injection_history: List[ContextInjection] = []

        # Load all registries
        self._load_registries()

        # Load workspace map
        self._load_workspace_map()

        logger.info("InfrastructureAgent initialized")

    def _load_registries(self):
        """Load all registry data from infrastructure files."""
        self._load_node_registry()
        self._load_tool_inventory()
        self._load_connection_graph()

        # Count pipelines by type
        langflow_count = sum(
            1 for p in self.pipelines.values() if p.pipeline_type == "langflow"
        )
        n8n_count = sum(1 for p in self.pipelines.values() if p.pipeline_type == "n8n")
        native_count = len(self.pipelines) - langflow_count - n8n_count

        logger.info(
            f"Loaded {len(self.nodes)} nodes, {len(self.tools)} tools, {len(self.agents)} agents, "
            f"{len(self.pipelines)} pipelines (native: {native_count}, langflow: {langflow_count}, n8n: {n8n_count})"
        )

    def _load_workspace_map(self):
        """Load the dynamic workspace map from the scanner agent."""
        if self._workspace_map_path.exists():
            try:
                with open(self._workspace_map_path, "r") as f:
                    self.workspace_map = json.load(f)

                # Log summary - use top-level keys
                if self.workspace_map:
                    logger.info(
                        f"Loaded workspace map: {self.workspace_map.get('total_files', 0)} files, "
                        f"{self.workspace_map.get('total_directories', 0)} dirs, "
                        f"{self.workspace_map.get('total_agents', 0)} agents, "
                        f"{self.workspace_map.get('total_capabilities', 0)} capabilities"
                    )
            except Exception as e:
                logger.warning(f"Failed to load workspace map: {e}")
                self.workspace_map = None
        else:
            logger.info(
                "Workspace map not found - run workspace_scanner_agent to generate"
            )
            self.workspace_map = None

    def reload_workspace_map(self) -> bool:
        """
        Reload the workspace map from disk.

        Returns:
            True if successful, False otherwise
        """
        self._load_workspace_map()
        return self.workspace_map is not None

    def get_workspace_map(self) -> Optional[Dict[str, Any]]:
        """
        Get the current workspace map.

        Returns:
            The workspace map dictionary or None if not loaded
        """
        return self.workspace_map

    def get_workspace_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the workspace map.

        Returns:
            Dictionary with workspace summary stats
        """
        if not self.workspace_map:
            return {"error": "Workspace map not loaded"}

        # The workspace map has summary fields at the top level
        return {
            "total_files": self.workspace_map.get("total_files", 0),
            "total_dirs": self.workspace_map.get("total_directories", 0),
            "total_agents": self.workspace_map.get("total_agents", 0),
            "total_pipelines": self.workspace_map.get("total_pipelines", 0),
            "total_capabilities": self.workspace_map.get("total_capabilities", 0),
            "generated_at": self.workspace_map.get("generated_at", "unknown"),
            "last_updated": self.workspace_map.get("last_updated", "unknown"),
            "version": self.workspace_map.get("version", "unknown"),
        }

    def get_workspace_capabilities(self) -> Dict[str, List[str]]:
        """
        Get all detected capabilities and their associated files.

        Returns:
            Dictionary mapping capability names to file lists
        """
        if not self.workspace_map:
            return {}

        return self.workspace_map.get("capabilities", {})

    def find_files_by_capability(self, capability: str) -> List[str]:
        """
        Find all files that have a specific capability.

        Args:
            capability: The capability name to search for

        Returns:
            List of file paths with the capability
        """
        if not self.workspace_map:
            return []

        capabilities = self.workspace_map.get("capabilities", {})
        return capabilities.get(capability, [])

    def get_all_workspace_agents(self) -> Dict[str, Any]:
        """
        Get all agents discovered in the workspace.

        Returns:
            Dictionary of agent IDs to agent info from workspace map
        """
        if not self.workspace_map:
            return {}

        return self.workspace_map.get("agents", {})

    def get_instruction_files(self) -> Dict[str, Any]:
        """
        Get all agent instruction files (.agent.md) from the workspace map.

        Returns:
            Dictionary of instruction file paths to their metadata
        """
        if not self.workspace_map:
            return {}

        return self.workspace_map.get("instruction_files", {})

    def _load_node_registry(self):
        """Load node registry from JSON."""
        registry_path = self.infrastructure_path / "nodes" / "registry.json"

        if not registry_path.exists():
            logger.warning("Node registry not found")
            return

        with open(registry_path, "r") as f:
            data = json.load(f)

        for node_id, node_data in data.get("nodes", {}).items():
            self.nodes[node_id] = NodeInfo(
                node_id=node_id,
                name=node_data.get("name", node_id),
                node_type=node_data.get("type", "unknown"),
                endpoint=node_data.get("endpoint", ""),
                port=node_data.get("port", 0),
                status=node_data.get("status", "unknown"),
                capabilities=node_data.get("capabilities", []),
                dependencies=node_data.get("dependencies", []),
                last_verified=node_data.get("last_health_check"),
            )

    def _load_tool_inventory(self):
        """Load tool inventory from JSON."""
        inventory_path = self.infrastructure_path / "tools" / "inventory.json"

        if not inventory_path.exists():
            logger.warning("Tool inventory not found")
            return

        with open(inventory_path, "r") as f:
            data = json.load(f)

        for tool_id, tool_data in data.get("tools", {}).items():
            self.tools[tool_id] = ToolInfo(
                tool_id=tool_id,
                name=tool_data.get("name", tool_id),
                tool_type=tool_data.get("type", "unknown"),
                path=tool_data.get("path", ""),
                status=tool_data.get("status", "unknown"),
                capabilities=tool_data.get("capabilities", {}),
                health_check=tool_data.get("health_check"),
            )

        # Also load parsers
        for parser_id, parser_data in data.get("parsers", {}).items():
            self.tools[parser_id] = ToolInfo(
                tool_id=parser_id,
                name=parser_data.get("name", parser_id),
                tool_type="document_parser",
                path=parser_data.get("path", ""),
                status=parser_data.get("status", "unknown"),
                capabilities={"features": parser_data.get("capabilities", [])},
            )

    def _load_connection_graph(self):
        """Load connection graph (agents, pipelines, data flows)."""
        graph_path = self.infrastructure_path / "graph" / "connections.json"

        if not graph_path.exists():
            logger.warning("Connection graph not found")
            return

        with open(graph_path, "r") as f:
            data = json.load(f)

        # Load agents
        for agent_id, agent_data in data.get("agents", {}).items():
            self.agents[agent_id] = AgentInfo(
                agent_id=agent_id,
                name=agent_data.get("name", agent_id),
                path=agent_data.get("path", ""),
                uses_tools=agent_data.get("uses_tools", []),
                uses_nodes=agent_data.get("uses_nodes", []),
                provides=agent_data.get("provides", []),
                consumes=agent_data.get("consumes", []),
                context_requirements=agent_data.get("context_requirements", {}),
            )

        # Load pipelines (native, Langflow, and n8n)
        for pipeline_id, pipeline_data in data.get("pipelines", {}).items():
            # Skip comment entries
            if pipeline_id.startswith("_comment"):
                continue

            self.pipelines[pipeline_id] = PipelineInfo(
                pipeline_id=pipeline_id,
                name=pipeline_data.get("name", pipeline_id),
                description=pipeline_data.get("description", ""),
                stages=pipeline_data.get("stages", []),
                triggers=pipeline_data.get("triggers", []),
                requires_approval=pipeline_data.get("requires_approval", False),
                pipeline_type=pipeline_data.get("type", "native"),
                path=pipeline_data.get("path"),
                port=pipeline_data.get("port"),
                connected_agent=pipeline_data.get("connected_agent"),
                connected_langflow=pipeline_data.get("connected_langflow"),
                connected_service=pipeline_data.get("connected_service"),
                connected_pipeline=pipeline_data.get("connected_pipeline"),
                autonomous=pipeline_data.get("autonomous", False),
                requires_auth=pipeline_data.get("requires_auth", False),
            )

    # =========================================================================
    # Verification and Discovery
    # =========================================================================

    async def verify_expectations(self) -> Dict[str, Any]:
        """
        Verify expected tools and nodes are available on startup.

        Returns:
            Dictionary with verification results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "nodes": {},
            "tools": {},
            "new_discoveries": [],
            "missing": [],
            "status": "ok",
        }

        # Load expected tools list
        inventory_path = self.infrastructure_path / "tools" / "inventory.json"
        if inventory_path.exists():
            with open(inventory_path, "r") as f:
                inventory_data = json.load(f)
            expected_tools = inventory_data.get("expected_tools", [])
        else:
            expected_tools = []

        # Verify tools
        for tool_id in expected_tools:
            tool = self.tools.get(tool_id)
            if tool:
                # Try to verify the tool exists
                verified = await self._verify_tool(tool)
                results["tools"][tool_id] = {
                    "status": "verified" if verified else "unavailable",
                    "path": tool.path,
                }
                if not verified:
                    results["missing"].append(f"tool:{tool_id}")
            else:
                results["tools"][tool_id] = {"status": "not_found"}
                results["missing"].append(f"tool:{tool_id}")

        # Scan for new tools
        new_tools = await self._discover_new_tools()
        results["new_discoveries"].extend(new_tools)

        # Update status
        if results["missing"]:
            results["status"] = "degraded"

        # Save verification timestamp
        await self._update_verification_timestamp()

        logger.info(
            f"Verification complete: {len(results['missing'])} missing, {len(results['new_discoveries'])} new"
        )
        return results

    async def _verify_tool(self, tool: ToolInfo) -> bool:
        """Verify a tool exists and is accessible."""
        tool_path = self.base_path / tool.path

        if tool_path.exists():
            tool.status = "available"
            tool.last_verified = datetime.now().isoformat()
            return True

        # Try importing if it's a Python module
        if tool.path.endswith(".py"):
            module_path = tool.path.replace("/", ".").replace("\\", ".").rstrip(".py")
            try:
                importlib.import_module(module_path)
                tool.status = "available"
                tool.last_verified = datetime.now().isoformat()
                return True
            except ImportError:
                pass

        tool.status = "unavailable"
        return False

    async def _discover_new_tools(self) -> List[str]:
        """Discover new tools not in inventory."""
        new_tools = []
        tools_dir = self.base_path / "tools"

        if not tools_dir.exists():
            return new_tools

        for tool_dir in tools_dir.iterdir():
            if tool_dir.is_dir() and not tool_dir.name.startswith("_"):
                tool_id = tool_dir.name
                if tool_id not in self.tools:
                    # Check for integration file
                    integration_file = tool_dir / f"{tool_id}_integration.py"
                    if integration_file.exists():
                        new_tools.append(f"tool:{tool_id}")
                        logger.info(f"Discovered new tool: {tool_id}")

        return new_tools

    async def _update_verification_timestamp(self):
        """Update verification timestamp in inventory."""
        inventory_path = self.infrastructure_path / "tools" / "inventory.json"

        if inventory_path.exists():
            with open(inventory_path, "r") as f:
                data = json.load(f)

            data["verified_at"] = datetime.now().isoformat()

            with open(inventory_path, "w") as f:
                json.dump(data, f, indent=2)

    # =========================================================================
    # Query Interface
    # =========================================================================

    def get_node(self, node_id: str) -> Optional[NodeInfo]:
        """Get information about a specific node."""
        return self.nodes.get(node_id)

    def get_tool(self, tool_id: str) -> Optional[ToolInfo]:
        """Get information about a specific tool."""
        return self.tools.get(tool_id)

    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get information about a specific agent."""
        return self.agents.get(agent_id)

    def get_pipeline(self, pipeline_id: str) -> Optional[PipelineInfo]:
        """Get information about a specific pipeline."""
        return self.pipelines.get(pipeline_id)

    def find_nodes_by_capability(self, capability: str) -> List[NodeInfo]:
        """Find nodes that have a specific capability."""
        return [node for node in self.nodes.values() if capability in node.capabilities]

    def find_tools_by_capability(self, capability: str) -> List[ToolInfo]:
        """Find tools that have a specific capability."""
        return [
            tool
            for tool in self.tools.values()
            if capability in tool.capabilities
            or any(capability in str(cap) for cap in tool.capabilities.values())
        ]

    def find_agents_providing(self, service: str) -> List[AgentInfo]:
        """Find agents that provide a specific service."""
        return [agent for agent in self.agents.values() if service in agent.provides]

    def find_agents_consuming(self, resource: str) -> List[AgentInfo]:
        """Find agents that consume a specific resource."""
        return [agent for agent in self.agents.values() if resource in agent.consumes]

    def get_agent_dependencies(self, agent_id: str) -> Dict[str, Any]:
        """Get all dependencies for an agent."""
        agent = self.agents.get(agent_id)
        if not agent:
            return {}

        return {
            "tools": [self.tools.get(t) for t in agent.uses_tools if t in self.tools],
            "nodes": [self.nodes.get(n) for n in agent.uses_nodes if n in self.nodes],
            "context": agent.context_requirements,
        }

    def get_pipeline_for_task(self, task_type: str) -> Optional[PipelineInfo]:
        """Find a pipeline suitable for a given task type."""
        task_to_pipeline = {
            "syllabus": "syllabus_to_calendar",
            "calendar": "syllabus_to_calendar",
            "media": "media_processing",
            "video": "media_processing",
            "audio": "media_processing",
            "research": "research_workflow",
            "document": "research_workflow",
            "daily_brief": "daily_brief_workflow",
            "notes": "note_integration",
            "class_notes": "note_integration",
        }

        pipeline_id = task_to_pipeline.get(task_type.lower())
        return self.pipelines.get(pipeline_id) if pipeline_id else None

    def get_pipelines_by_type(self, pipeline_type: str) -> List[PipelineInfo]:
        """
        Get all pipelines of a specific type.

        Args:
            pipeline_type: "native", "langflow", or "n8n"

        Returns:
            List of pipelines matching the type
        """
        return [p for p in self.pipelines.values() if p.pipeline_type == pipeline_type]

    def get_langflow_flows(self) -> List[PipelineInfo]:
        """Get all Langflow flows registered as pipelines."""
        return self.get_pipelines_by_type("langflow")

    def get_n8n_workflows(self) -> List[PipelineInfo]:
        """Get all n8n workflows registered as pipelines."""
        return self.get_pipelines_by_type("n8n")

    def get_native_pipelines(self) -> List[PipelineInfo]:
        """Get all native (non-Langflow/n8n) pipelines."""
        return self.get_pipelines_by_type("native")

    def get_pipeline_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all pipelines by type.

        Returns:
            Dictionary with pipeline counts and lists by type
        """
        langflow = self.get_langflow_flows()
        n8n = self.get_n8n_workflows()
        native = self.get_native_pipelines()

        return {
            "total": len(self.pipelines),
            "native": {
                "count": len(native),
                "pipelines": [p.pipeline_id for p in native],
            },
            "langflow": {
                "count": len(langflow),
                "port": 7860,
                "flows": [p.pipeline_id for p in langflow],
            },
            "n8n": {
                "count": len(n8n),
                "port": 5678,
                "workflows": [p.pipeline_id for p in n8n],
            },
        }

    def get_connected_pipelines(self, agent_id: str) -> Dict[str, List[PipelineInfo]]:
        """
        Get all pipelines connected to a specific agent.

        Args:
            agent_id: The agent ID to search for

        Returns:
            Dictionary with langflow and n8n pipelines connected to the agent
        """
        result = {"langflow": [], "n8n": []}

        for pipeline in self.pipelines.values():
            if pipeline.connected_agent == agent_id:
                if pipeline.pipeline_type == "langflow":
                    result["langflow"].append(pipeline)
                elif pipeline.pipeline_type == "n8n":
                    result["n8n"].append(pipeline)

        return result

    # =========================================================================
    # Dynamic Context Injection
    # =========================================================================

    def generate_context_for_agent(
        self,
        agent_id: str,
        task_description: Optional[str] = None,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        """
        Generate infrastructure context to inject into an agent's prompt.

        Args:
            agent_id: ID of the agent requesting context
            task_description: Optional description of the current task
            max_tokens: Maximum token budget for context

        Returns:
            Dictionary with context to inject
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return self._generate_minimal_context()

        context = {
            "workspace_awareness": self._generate_workspace_awareness(),
            "capabilities": self._generate_capability_context(agent),
            "constraints": self._generate_constraint_context(agent),
            "available_pipelines": self._generate_pipeline_context(task_description),
            "data_sources": self._generate_data_source_context(agent),
        }

        # Estimate tokens and trim if necessary
        token_estimate = self._estimate_tokens(context)
        if token_estimate > max_tokens:
            context = self._trim_context(context, max_tokens)
            token_estimate = self._estimate_tokens(context)

        # Log injection
        injection = ContextInjection(
            agent_id=agent_id,
            timestamp=datetime.now().isoformat(),
            injected_context=context,
            token_estimate=token_estimate,
            sources=["nodes", "tools", "pipelines", "policies"],
        )
        self.injection_history.append(injection)

        # Keep only last 100 injections
        if len(self.injection_history) > 100:
            self.injection_history = self.injection_history[-100:]

        return context

    def _generate_minimal_context(self) -> Dict[str, Any]:
        """Generate minimal context for unknown agents."""
        return {
            "workspace_awareness": {
                "description": "OsMEN Workspace Infrastructure",
                "available_nodes": list(self.nodes.keys()),
                "available_tools": list(self.tools.keys()),
            }
        }

    def _generate_workspace_awareness(self) -> Dict[str, Any]:
        """Generate workspace awareness context."""
        healthy_nodes = [n for n in self.nodes.values() if n.status == "healthy"]
        available_tools = [t for t in self.tools.values() if t.status == "available"]

        return {
            "description": "OsMEN local-first agent orchestration workspace",
            "infrastructure_status": {
                "total_nodes": len(self.nodes),
                "healthy_nodes": len(healthy_nodes),
                "total_tools": len(self.tools),
                "available_tools": len(available_tools),
            },
            "directories": {
                "knowledge": "Embeddings, memories, RAG corpus, Obsidian vault",
                "workspace": "Incoming files, staging, pending review",
                "infrastructure": "Node registry, tool inventory, connection graph",
            },
        }

    def _generate_capability_context(self, agent: AgentInfo) -> Dict[str, Any]:
        """Generate capability context for an agent."""
        capabilities = {
            "agent_provides": agent.provides,
            "available_tools": {},
            "available_nodes": {},
        }

        # Add tool capabilities
        for tool_id in agent.uses_tools:
            tool = self.tools.get(tool_id)
            if tool and tool.status == "available":
                capabilities["available_tools"][tool_id] = {
                    "name": tool.name,
                    "capabilities": list(tool.capabilities.keys()),
                }

        # Add node capabilities
        for node_id in agent.uses_nodes:
            node = self.nodes.get(node_id)
            if node:
                capabilities["available_nodes"][node_id] = {
                    "name": node.name,
                    "endpoint": node.endpoint,
                    "capabilities": node.capabilities,
                }

        return capabilities

    def _generate_constraint_context(self, agent: AgentInfo) -> Dict[str, Any]:
        """Generate constraint context for an agent."""
        # Load policies
        policies_path = self.infrastructure_path / "profiles" / "policies.json"
        constraints = {}

        if policies_path.exists():
            with open(policies_path, "r") as f:
                policies = json.load(f)

            # Get agent role constraints
            agent_role = agent.agent_id.replace("_agent", "")
            role_config = policies.get("agent_roles", {}).get(agent_role, {})

            constraints["permissions"] = role_config.get("permissions", [])
            constraints["restricted"] = role_config.get("restricted", [])

            # Add knowledge write policies
            write_policies = policies.get("workspace_policies", {}).get(
                "knowledge_write", {}
            )
            constraints["write_approval_rules"] = [
                rule["pattern"] for rule in write_policies.get("rules", [])
            ]

        # Add context requirements
        constraints["context_requirements"] = agent.context_requirements

        return constraints

    def _generate_pipeline_context(
        self, task_description: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Generate relevant pipeline context based on task."""
        if not task_description:
            # Return all pipelines
            return [
                {"id": p.pipeline_id, "name": p.name, "triggers": p.triggers}
                for p in self.pipelines.values()
            ]

        # Find relevant pipelines based on task keywords
        relevant = []
        task_lower = task_description.lower()

        for pipeline in self.pipelines.values():
            if any(keyword in task_lower for keyword in pipeline.name.lower().split()):
                relevant.append(
                    {
                        "id": pipeline.pipeline_id,
                        "name": pipeline.name,
                        "description": pipeline.description,
                        "stages": [s["name"] for s in pipeline.stages],
                        "triggers": pipeline.triggers,
                    }
                )

        return (
            relevant
            if relevant
            else [
                {"id": p.pipeline_id, "name": p.name}
                for p in list(self.pipelines.values())[:3]
            ]
        )

    def _generate_data_source_context(self, agent: AgentInfo) -> Dict[str, Any]:
        """Generate data source context for an agent."""
        sources = {"consumes": agent.consumes, "available_locations": {}}

        # Map data types to locations
        data_locations = {
            "embeddings": "knowledge/embeddings",
            "documents": "knowledge/rag",
            "memories": "knowledge/memories",
            "user_input": "runtime",
            "calendar": "integrations/calendars",
            "tasks": "data/personal_assistant",
            "emails": "integrations/email",
            "vault_content": "knowledge/obsidian",
        }

        for data_type in agent.consumes:
            if data_type in data_locations:
                sources["available_locations"][data_type] = data_locations[data_type]

        return sources

    def _estimate_tokens(self, context: Dict[str, Any]) -> int:
        """Estimate token count for context (rough estimate: 4 chars per token)."""
        text = json.dumps(context)
        return len(text) // 4

    def _trim_context(self, context: Dict[str, Any], max_tokens: int) -> Dict[str, Any]:
        """Trim context to fit within token budget."""
        # Remove less important sections first
        priority = [
            "capabilities",
            "constraints",
            "workspace_awareness",
            "available_pipelines",
            "data_sources",
        ]

        trimmed = {}
        current_tokens = 0

        for key in priority:
            if key in context:
                section_tokens = self._estimate_tokens({key: context[key]})
                if current_tokens + section_tokens <= max_tokens:
                    trimmed[key] = context[key]
                    current_tokens += section_tokens

        return trimmed

    def format_context_as_prompt(self, context: Dict[str, Any]) -> str:
        """
        Format context dictionary as a prompt-ready string.

        Args:
            context: Context dictionary from generate_context_for_agent

        Returns:
            Formatted string for system prompt injection
        """
        lines = ["## Workspace Infrastructure Context\n"]

        if "workspace_awareness" in context:
            wa = context["workspace_awareness"]
            lines.append(f"**Workspace:** {wa.get('description', 'OsMEN')}")
            status = wa.get("infrastructure_status", {})
            if status:
                lines.append(
                    f"- Nodes: {status.get('healthy_nodes', 0)}/{status.get('total_nodes', 0)} healthy"
                )
                lines.append(
                    f"- Tools: {status.get('available_tools', 0)}/{status.get('total_tools', 0)} available"
                )

        if "capabilities" in context:
            caps = context["capabilities"]
            if caps.get("agent_provides"):
                lines.append(f"\n**You Provide:** {', '.join(caps['agent_provides'])}")
            if caps.get("available_tools"):
                tools = [f"{t['name']}" for t in caps["available_tools"].values()]
                lines.append(f"**Available Tools:** {', '.join(tools)}")
            if caps.get("available_nodes"):
                nodes = [f"{n['name']}" for n in caps["available_nodes"].values()]
                lines.append(f"**Available Services:** {', '.join(nodes)}")

        if "constraints" in context:
            cons = context["constraints"]
            if cons.get("restricted"):
                lines.append(f"\n**Restrictions:** {', '.join(cons['restricted'])}")

        if "available_pipelines" in context:
            pipelines = context["available_pipelines"]
            if pipelines:
                pipeline_names = [p.get("name", p.get("id", "")) for p in pipelines]
                lines.append(f"\n**Available Pipelines:** {', '.join(pipeline_names)}")

        return "\n".join(lines)

    # =========================================================================
    # Status and Reporting
    # =========================================================================

    def get_status(self) -> Dict[str, Any]:
        """Get current infrastructure agent status."""
        return {
            "timestamp": datetime.now().isoformat(),
            "nodes": {
                "total": len(self.nodes),
                "by_status": self._count_by_status(self.nodes),
            },
            "tools": {
                "total": len(self.tools),
                "by_status": self._count_by_status(self.tools),
            },
            "agents": {"total": len(self.agents), "list": list(self.agents.keys())},
            "pipelines": {
                "total": len(self.pipelines),
                "list": list(self.pipelines.keys()),
            },
            "injection_history_count": len(self.injection_history),
        }

    def _count_by_status(self, items: Dict[str, Any]) -> Dict[str, int]:
        """Count items by status."""
        counts = {}
        for item in items.values():
            status = getattr(item, "status", "unknown")
            counts[status] = counts.get(status, 0) + 1
        return counts

    def get_full_graph(self) -> Dict[str, Any]:
        """Get the complete connection graph for visualization."""
        return {
            "nodes": [asdict(n) for n in self.nodes.values()],
            "tools": [asdict(t) for t in self.tools.values()],
            "agents": [asdict(a) for a in self.agents.values()],
            "pipelines": [asdict(p) for p in self.pipelines.values()],
            "connections": self._compute_connections(),
        }

    def _compute_connections(self) -> List[Dict[str, str]]:
        """Compute all connections for graph visualization."""
        connections = []

        for agent in self.agents.values():
            # Agent -> Tool connections
            for tool_id in agent.uses_tools:
                connections.append(
                    {
                        "from": f"agent:{agent.agent_id}",
                        "to": f"tool:{tool_id}",
                        "type": "uses",
                    }
                )

            # Agent -> Node connections
            for node_id in agent.uses_nodes:
                connections.append(
                    {
                        "from": f"agent:{agent.agent_id}",
                        "to": f"node:{node_id}",
                        "type": "uses",
                    }
                )

        # Node dependencies
        for node in self.nodes.values():
            for dep_id in node.dependencies:
                connections.append(
                    {
                        "from": f"node:{node.node_id}",
                        "to": f"node:{dep_id}",
                        "type": "depends_on",
                    }
                )

        return connections

    def export_context_summary(self) -> str:
        """
        Export a compact summary of the entire infrastructure.
        This is the "low-token context" for basic instructions.
        """
        summary = """# OsMEN Infrastructure Summary

## Services
- **LLM**: Ollama (local inference), vLLM (high-throughput)
- **Vectors**: ChromaDB, Qdrant (embeddings, RAG)
- **Workflows**: Langflow (visual), n8n (automation)
- **Gateway**: Agent Gateway (8080), MCP Server (8081)
- **Convert**: ConvertX (1000+ formats)

## Directories
- `knowledge/` - Embeddings, memories, RAG, Obsidian vault
- `workspace/` - Incoming files, staging, pending review  
- `infrastructure/` - Node registry, tools, connections

## Key Agents
- Librarian: RAG retrieval, fact-checking
- Research Intel: Document analysis, synthesis
- Personal Assistant: Tasks, reminders, NLU
- Health Monitor: Service health, auto-repair

## Pipelines
- Syllabus → Calendar: Parse, normalize, sync
- Media Processing: Convert, compress, transcribe
- Research Workflow: Ingest, chunk, embed, index
- Note Integration: Analyze, link, integrate

## Permissions
- Knowledge writes require approval (interactive/queue/rule)
- Workspace files: 10-day review, 90-day archive prompt
- Destructive fixes: Checkpoint required, user approval

## Query Infrastructure
Use InfrastructureAgent methods:
- `find_nodes_by_capability(cap)` - Find services
- `find_tools_by_capability(cap)` - Find tools
- `get_agent_dependencies(agent_id)` - Get deps
- `get_pipeline_for_task(task_type)` - Find workflow
"""
        return summary


# =============================================================================
# CLI Entry Point
# =============================================================================


async def main():
    """Main entry point for infrastructure agent."""
    agent = InfrastructureAgent()

    print("Infrastructure Agent Status:")
    print(json.dumps(agent.get_status(), indent=2))

    print("\n--- Verification ---")
    results = await agent.verify_expectations()
    print(json.dumps(results, indent=2))

    print("\n--- Context for Librarian ---")
    context = agent.generate_context_for_agent("librarian")
    print(agent.format_context_as_prompt(context))


if __name__ == "__main__":
    asyncio.run(main())
