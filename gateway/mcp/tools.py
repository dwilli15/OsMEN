"""
OsMEN MCP Tool Registry
Centralized tool definitions with full schema validation
"""

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ToolCategory(str, Enum):
    """Tool categories for organization"""

    SYSTEM = "system"
    KNOWLEDGE = "knowledge"
    WORKFLOW = "workflow"
    MEMORY = "memory"
    MEDIA = "media"
    SECURITY = "security"
    PRODUCTIVITY = "productivity"
    INTEGRATION = "integration"
    AGENT = "agent"


@dataclass
class ParameterSchema:
    """JSON Schema for a tool parameter"""

    type: str
    description: str
    required: bool = False
    default: Any = None
    enum: Optional[List[Any]] = None
    items: Optional[Dict[str, Any]] = None  # For array types
    properties: Optional[Dict[str, Any]] = None  # For object types
    minimum: Optional[Union[int, float]] = None
    maximum: Optional[Union[int, float]] = None
    pattern: Optional[str] = None

    def to_json_schema(self) -> Dict[str, Any]:
        """Convert to JSON Schema format"""
        schema = {"type": self.type, "description": self.description}
        if self.default is not None:
            schema["default"] = self.default
        if self.enum:
            schema["enum"] = self.enum
        if self.items:
            schema["items"] = self.items
        if self.properties:
            schema["properties"] = self.properties
        if self.minimum is not None:
            schema["minimum"] = self.minimum
        if self.maximum is not None:
            schema["maximum"] = self.maximum
        if self.pattern:
            schema["pattern"] = self.pattern
        return schema


@dataclass
class ToolDefinition:
    """Complete MCP tool definition"""

    name: str
    description: str
    category: ToolCategory
    parameters: Dict[str, ParameterSchema] = field(default_factory=dict)
    handler: Optional[str] = None  # Method name or import path
    requires_confirmation: bool = False
    timeout_seconds: int = 300
    rate_limit_per_minute: Optional[int] = None
    enabled: bool = True
    tags: List[str] = field(default_factory=list)

    def to_mcp_schema(self) -> Dict[str, Any]:
        """Convert to MCP tool schema format"""
        properties = {}
        required = []

        for name, param in self.parameters.items():
            properties[name] = param.to_json_schema()
            if param.required:
                required.append(name)

        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "parameters": {k: v.to_json_schema() for k, v in self.parameters.items()},
            "handler": self.handler,
            "requires_confirmation": self.requires_confirmation,
            "timeout_seconds": self.timeout_seconds,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "enabled": self.enabled,
            "tags": self.tags,
        }


class ToolRegistry:
    """
    Centralized registry for all MCP tools.

    Features:
    - Single source of truth for tool definitions
    - Category-based organization
    - Schema validation
    - Handler registration
    - Export to multiple formats (MCP, JSON, OpenAPI)
    """

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._handlers: Dict[str, Callable] = {}
        self._initialize_default_tools()

    def _initialize_default_tools(self) -> None:
        """Register all default OsMEN tools"""

        # =========================================================================
        # SYSTEM TOOLS
        # =========================================================================

        self.register(
            ToolDefinition(
                name="execute_command",
                description="Execute a shell command on the local system. Supports PowerShell on Windows, bash on Linux/Mac.",
                category=ToolCategory.SYSTEM,
                requires_confirmation=True,
                parameters={
                    "command": ParameterSchema(
                        type="string",
                        description="The shell command to execute",
                        required=True,
                    ),
                    "working_dir": ParameterSchema(
                        type="string",
                        description="Working directory for command execution",
                        default=None,
                    ),
                    "timeout": ParameterSchema(
                        type="integer",
                        description="Command timeout in seconds",
                        default=300,
                        minimum=1,
                        maximum=3600,
                    ),
                    "capture_output": ParameterSchema(
                        type="boolean",
                        description="Whether to capture stdout/stderr",
                        default=True,
                    ),
                },
                handler="system.execute_command",
                tags=["shell", "terminal", "cli"],
            )
        )

        self.register(
            ToolDefinition(
                name="check_services",
                description="Check health status of all OsMEN connected services (n8n, Langflow, Qdrant, etc.)",
                category=ToolCategory.SYSTEM,
                parameters={
                    "services": ParameterSchema(
                        type="array",
                        description="Specific services to check (empty for all)",
                        items={"type": "string"},
                        default=[],
                    ),
                    "timeout": ParameterSchema(
                        type="integer",
                        description="Health check timeout per service",
                        default=5,
                    ),
                },
                handler="system.check_services",
                tags=["health", "monitoring", "infrastructure"],
            )
        )

        self.register(
            ToolDefinition(
                name="get_system_info",
                description="Get system information including OS, CPU, memory, and disk usage",
                category=ToolCategory.SYSTEM,
                parameters={
                    "include_processes": ParameterSchema(
                        type="boolean",
                        description="Include top processes by resource usage",
                        default=False,
                    ),
                },
                handler="system.get_system_info",
                tags=["monitoring", "diagnostics"],
            )
        )

        # =========================================================================
        # KNOWLEDGE MANAGEMENT TOOLS
        # =========================================================================

        self.register(
            ToolDefinition(
                name="obsidian_create_note",
                description="Create a new note in the Obsidian vault with optional tags and folder",
                category=ToolCategory.KNOWLEDGE,
                parameters={
                    "title": ParameterSchema(
                        type="string",
                        description="Note title (will become filename)",
                        required=True,
                    ),
                    "content": ParameterSchema(
                        type="string",
                        description="Note content in Markdown format",
                        required=True,
                    ),
                    "folder": ParameterSchema(
                        type="string",
                        description="Folder path within vault",
                        default="",
                    ),
                    "tags": ParameterSchema(
                        type="array",
                        description="Tags to add to frontmatter",
                        items={"type": "string"},
                        default=[],
                    ),
                    "template": ParameterSchema(
                        type="string",
                        description="Template to use for note creation",
                        default=None,
                    ),
                },
                handler="obsidian.create_note",
                tags=["notes", "obsidian", "markdown"],
            )
        )

        self.register(
            ToolDefinition(
                name="obsidian_read_note",
                description="Read a note from the Obsidian vault by path or title",
                category=ToolCategory.KNOWLEDGE,
                parameters={
                    "path": ParameterSchema(
                        type="string",
                        description="Note path relative to vault root",
                        required=True,
                    ),
                    "include_frontmatter": ParameterSchema(
                        type="boolean",
                        description="Include YAML frontmatter in response",
                        default=True,
                    ),
                },
                handler="obsidian.read_note",
                tags=["notes", "obsidian"],
            )
        )

        self.register(
            ToolDefinition(
                name="obsidian_search",
                description="Search notes in Obsidian vault using full-text search",
                category=ToolCategory.KNOWLEDGE,
                parameters={
                    "query": ParameterSchema(
                        type="string",
                        description="Search query (supports Obsidian search syntax)",
                        required=True,
                    ),
                    "folder": ParameterSchema(
                        type="string",
                        description="Limit search to specific folder",
                        default=None,
                    ),
                    "tags": ParameterSchema(
                        type="array",
                        description="Filter by tags",
                        items={"type": "string"},
                        default=[],
                    ),
                    "limit": ParameterSchema(
                        type="integer",
                        description="Maximum results to return",
                        default=10,
                        minimum=1,
                        maximum=100,
                    ),
                },
                handler="obsidian.search_notes",
                tags=["search", "obsidian"],
            )
        )

        self.register(
            ToolDefinition(
                name="obsidian_list_notes",
                description="List all notes in the Obsidian vault or a specific folder",
                category=ToolCategory.KNOWLEDGE,
                parameters={
                    "folder": ParameterSchema(
                        type="string",
                        description="Folder to list (empty for root)",
                        default="",
                    ),
                    "recursive": ParameterSchema(
                        type="boolean",
                        description="Include notes in subfolders",
                        default=True,
                    ),
                    "include_metadata": ParameterSchema(
                        type="boolean",
                        description="Include frontmatter metadata",
                        default=False,
                    ),
                },
                handler="obsidian.list_notes",
                tags=["obsidian", "files"],
            )
        )

        self.register(
            ToolDefinition(
                name="obsidian_update_note",
                description="Update an existing note in Obsidian vault",
                category=ToolCategory.KNOWLEDGE,
                parameters={
                    "path": ParameterSchema(
                        type="string",
                        description="Note path relative to vault root",
                        required=True,
                    ),
                    "content": ParameterSchema(
                        type="string",
                        description="New content (replaces existing)",
                        required=True,
                    ),
                    "append": ParameterSchema(
                        type="boolean",
                        description="Append instead of replace",
                        default=False,
                    ),
                },
                handler="obsidian.update_note",
                tags=["notes", "obsidian"],
            )
        )

        self.register(
            ToolDefinition(
                name="obsidian_delete_note",
                description="Delete a note from Obsidian vault",
                category=ToolCategory.KNOWLEDGE,
                requires_confirmation=True,
                parameters={
                    "path": ParameterSchema(
                        type="string",
                        description="Note path relative to vault root",
                        required=True,
                    ),
                    "trash": ParameterSchema(
                        type="boolean",
                        description="Move to trash instead of permanent delete",
                        default=True,
                    ),
                },
                handler="obsidian.delete_note",
                tags=["notes", "obsidian"],
            )
        )

        self.register(
            ToolDefinition(
                name="librarian_search",
                description="Search documents using Librarian RAG system with lateral thinking",
                category=ToolCategory.KNOWLEDGE,
                parameters={
                    "query": ParameterSchema(
                        type="string",
                        description="Search query for semantic retrieval",
                        required=True,
                    ),
                    "collection": ParameterSchema(
                        type="string",
                        description="Document collection to search",
                        default="default",
                    ),
                    "mode": ParameterSchema(
                        type="string",
                        description="Search mode: standard, lateral, or hybrid",
                        enum=["standard", "lateral", "hybrid"],
                        default="lateral",
                    ),
                    "limit": ParameterSchema(
                        type="integer",
                        description="Maximum results",
                        default=10,
                        minimum=1,
                        maximum=50,
                    ),
                },
                handler="librarian.search",
                tags=["rag", "search", "semantic"],
            )
        )

        self.register(
            ToolDefinition(
                name="librarian_ingest",
                description="Ingest a document or text into Librarian for RAG retrieval",
                category=ToolCategory.KNOWLEDGE,
                parameters={
                    "content": ParameterSchema(
                        type="string",
                        description="Content to ingest",
                        required=True,
                    ),
                    "source": ParameterSchema(
                        type="string",
                        description="Source identifier (filename, URL, etc.)",
                        required=True,
                    ),
                    "collection": ParameterSchema(
                        type="string",
                        description="Target collection",
                        default="default",
                    ),
                    "metadata": ParameterSchema(
                        type="object",
                        description="Additional metadata",
                        default={},
                    ),
                },
                handler="librarian.ingest",
                tags=["rag", "ingestion"],
            )
        )

        # =========================================================================
        # MEMORY TOOLS
        # =========================================================================

        self.register(
            ToolDefinition(
                name="memory_store",
                description="Store information in persistent vector memory (Qdrant)",
                category=ToolCategory.MEMORY,
                parameters={
                    "content": ParameterSchema(
                        type="string",
                        description="Content to store",
                        required=True,
                    ),
                    "collection": ParameterSchema(
                        type="string",
                        description="Memory collection name",
                        default="default_memory",
                    ),
                    "metadata": ParameterSchema(
                        type="object",
                        description="Associated metadata (tags, source, etc.)",
                        default={},
                    ),
                    "importance": ParameterSchema(
                        type="number",
                        description="Importance score (0-1) for retrieval ranking",
                        default=0.5,
                        minimum=0,
                        maximum=1,
                    ),
                },
                handler="memory.store",
                tags=["memory", "vector", "qdrant"],
            )
        )

        self.register(
            ToolDefinition(
                name="memory_recall",
                description="Recall information from persistent vector memory",
                category=ToolCategory.MEMORY,
                parameters={
                    "query": ParameterSchema(
                        type="string",
                        description="What to recall (semantic search)",
                        required=True,
                    ),
                    "collection": ParameterSchema(
                        type="string",
                        description="Memory collection name",
                        default="default_memory",
                    ),
                    "limit": ParameterSchema(
                        type="integer",
                        description="Maximum memories to recall",
                        default=10,
                        minimum=1,
                        maximum=50,
                    ),
                    "score_threshold": ParameterSchema(
                        type="number",
                        description="Minimum similarity score (0-1)",
                        default=0.7,
                        minimum=0,
                        maximum=1,
                    ),
                    "time_range": ParameterSchema(
                        type="string",
                        description="Time filter (e.g., 'last 7 days', 'today')",
                        default=None,
                    ),
                },
                handler="memory.recall",
                tags=["memory", "vector", "qdrant", "search"],
            )
        )

        self.register(
            ToolDefinition(
                name="memory_forget",
                description="Remove specific memories from vector storage",
                category=ToolCategory.MEMORY,
                requires_confirmation=True,
                parameters={
                    "ids": ParameterSchema(
                        type="array",
                        description="Memory IDs to remove",
                        items={"type": "string"},
                        required=True,
                    ),
                    "collection": ParameterSchema(
                        type="string",
                        description="Memory collection name",
                        default="default_memory",
                    ),
                },
                handler="memory.forget",
                tags=["memory", "deletion"],
            )
        )

        self.register(
            ToolDefinition(
                name="memory_collections",
                description="List all memory collections and their statistics",
                category=ToolCategory.MEMORY,
                parameters={},
                handler="memory.list_collections",
                tags=["memory", "admin"],
            )
        )

        # =========================================================================
        # WORKFLOW TOOLS
        # =========================================================================

        self.register(
            ToolDefinition(
                name="workflow_trigger",
                description="Trigger an n8n workflow by name, ID, or webhook",
                category=ToolCategory.WORKFLOW,
                parameters={
                    "workflow": ParameterSchema(
                        type="string",
                        description="Workflow name or ID",
                        required=True,
                    ),
                    "webhook_path": ParameterSchema(
                        type="string",
                        description="Webhook path (if webhook-triggered)",
                        default=None,
                    ),
                    "payload": ParameterSchema(
                        type="object",
                        description="Data to pass to workflow",
                        default={},
                    ),
                    "wait_for_completion": ParameterSchema(
                        type="boolean",
                        description="Wait for workflow to complete",
                        default=False,
                    ),
                },
                handler="workflow.trigger",
                timeout_seconds=600,
                tags=["n8n", "automation", "workflow"],
            )
        )

        self.register(
            ToolDefinition(
                name="workflow_list",
                description="List available n8n workflows",
                category=ToolCategory.WORKFLOW,
                parameters={
                    "active_only": ParameterSchema(
                        type="boolean",
                        description="Only show active workflows",
                        default=True,
                    ),
                    "tag": ParameterSchema(
                        type="string",
                        description="Filter by tag",
                        default=None,
                    ),
                },
                handler="workflow.list",
                tags=["n8n", "automation"],
            )
        )

        self.register(
            ToolDefinition(
                name="workflow_status",
                description="Get status of a workflow execution",
                category=ToolCategory.WORKFLOW,
                parameters={
                    "execution_id": ParameterSchema(
                        type="string",
                        description="Workflow execution ID",
                        required=True,
                    ),
                },
                handler="workflow.status",
                tags=["n8n", "monitoring"],
            )
        )

        self.register(
            ToolDefinition(
                name="langflow_run",
                description="Execute a Langflow agent/flow",
                category=ToolCategory.WORKFLOW,
                parameters={
                    "flow_id": ParameterSchema(
                        type="string",
                        description="Langflow flow ID or name",
                        required=True,
                    ),
                    "input": ParameterSchema(
                        type="string",
                        description="Input message for the flow",
                        required=True,
                    ),
                    "tweaks": ParameterSchema(
                        type="object",
                        description="Runtime configuration overrides",
                        default={},
                    ),
                    "session_id": ParameterSchema(
                        type="string",
                        description="Session ID for conversation continuity",
                        default=None,
                    ),
                },
                handler="langflow.run",
                timeout_seconds=120,
                tags=["langflow", "llm", "agent"],
            )
        )

        self.register(
            ToolDefinition(
                name="langflow_list",
                description="List available Langflow flows",
                category=ToolCategory.WORKFLOW,
                parameters={},
                handler="langflow.list",
                tags=["langflow"],
            )
        )

        # =========================================================================
        # SECURITY TOOLS
        # =========================================================================

        self.register(
            ToolDefinition(
                name="firewall_block",
                description="Block a domain or IP using Simplewall",
                category=ToolCategory.SECURITY,
                requires_confirmation=True,
                parameters={
                    "target": ParameterSchema(
                        type="string",
                        description="Domain or IP to block",
                        required=True,
                    ),
                    "rule_name": ParameterSchema(
                        type="string",
                        description="Name for the firewall rule",
                        default=None,
                    ),
                    "direction": ParameterSchema(
                        type="string",
                        description="Traffic direction",
                        enum=["inbound", "outbound", "both"],
                        default="both",
                    ),
                },
                handler="simplewall.block",
                tags=["firewall", "security", "simplewall"],
            )
        )

        self.register(
            ToolDefinition(
                name="firewall_unblock",
                description="Remove a firewall block rule",
                category=ToolCategory.SECURITY,
                parameters={
                    "target": ParameterSchema(
                        type="string",
                        description="Domain or IP to unblock",
                        required=True,
                    ),
                },
                handler="simplewall.unblock",
                tags=["firewall", "security"],
            )
        )

        self.register(
            ToolDefinition(
                name="firewall_list_rules",
                description="List current Simplewall firewall rules",
                category=ToolCategory.SECURITY,
                parameters={
                    "filter": ParameterSchema(
                        type="string",
                        description="Filter rules by name or target",
                        default=None,
                    ),
                },
                handler="simplewall.list_rules",
                tags=["firewall", "security"],
            )
        )

        self.register(
            ToolDefinition(
                name="sysinternals_autoruns",
                description="Run Autoruns to analyze startup programs and services",
                category=ToolCategory.SECURITY,
                parameters={
                    "output_file": ParameterSchema(
                        type="string",
                        description="Output file path for results",
                        default=None,
                    ),
                    "scan_type": ParameterSchema(
                        type="string",
                        description="What to scan",
                        enum=["all", "logon", "services", "drivers", "scheduled"],
                        default="all",
                    ),
                },
                handler="sysinternals.autoruns",
                timeout_seconds=600,
                tags=["sysinternals", "security", "startup"],
            )
        )

        self.register(
            ToolDefinition(
                name="sysinternals_procmon",
                description="Capture system activity with Process Monitor",
                category=ToolCategory.SECURITY,
                parameters={
                    "duration_seconds": ParameterSchema(
                        type="integer",
                        description="Capture duration",
                        default=30,
                        minimum=5,
                        maximum=300,
                    ),
                    "process_filter": ParameterSchema(
                        type="string",
                        description="Filter by process name",
                        default=None,
                    ),
                    "output_file": ParameterSchema(
                        type="string",
                        description="Output file for capture",
                        default=None,
                    ),
                },
                handler="sysinternals.procmon",
                timeout_seconds=600,
                tags=["sysinternals", "monitoring"],
            )
        )

        self.register(
            ToolDefinition(
                name="system_health",
                description="Comprehensive system health analysis using Sysinternals",
                category=ToolCategory.SECURITY,
                parameters={
                    "include_network": ParameterSchema(
                        type="boolean",
                        description="Include network diagnostics",
                        default=True,
                    ),
                    "include_processes": ParameterSchema(
                        type="boolean",
                        description="Include process analysis",
                        default=True,
                    ),
                },
                handler="sysinternals.health_check",
                timeout_seconds=300,
                tags=["health", "security", "diagnostics"],
            )
        )

        # =========================================================================
        # MEDIA TOOLS
        # =========================================================================

        self.register(
            ToolDefinition(
                name="media_info",
                description="Get detailed information about a media file",
                category=ToolCategory.MEDIA,
                parameters={
                    "file_path": ParameterSchema(
                        type="string",
                        description="Path to media file",
                        required=True,
                    ),
                    "format": ParameterSchema(
                        type="string",
                        description="Output format",
                        enum=["json", "text", "summary"],
                        default="json",
                    ),
                },
                handler="ffmpeg.get_info",
                tags=["ffmpeg", "media", "video", "audio"],
            )
        )

        self.register(
            ToolDefinition(
                name="media_convert",
                description="Convert media file to different format",
                category=ToolCategory.MEDIA,
                parameters={
                    "input_file": ParameterSchema(
                        type="string",
                        description="Input file path",
                        required=True,
                    ),
                    "output_file": ParameterSchema(
                        type="string",
                        description="Output file path",
                        required=True,
                    ),
                    "codec": ParameterSchema(
                        type="string",
                        description="Video codec (h264, h265, vp9, etc.)",
                        default=None,
                    ),
                    "audio_codec": ParameterSchema(
                        type="string",
                        description="Audio codec (aac, mp3, opus, etc.)",
                        default=None,
                    ),
                    "quality": ParameterSchema(
                        type="string",
                        description="Quality preset",
                        enum=["low", "medium", "high", "lossless"],
                        default="medium",
                    ),
                },
                handler="ffmpeg.convert",
                timeout_seconds=3600,
                tags=["ffmpeg", "conversion"],
            )
        )

        self.register(
            ToolDefinition(
                name="media_extract_audio",
                description="Extract audio track from video file",
                category=ToolCategory.MEDIA,
                parameters={
                    "input_file": ParameterSchema(
                        type="string",
                        description="Input video file",
                        required=True,
                    ),
                    "output_file": ParameterSchema(
                        type="string",
                        description="Output audio file",
                        required=True,
                    ),
                    "format": ParameterSchema(
                        type="string",
                        description="Output audio format",
                        enum=["mp3", "aac", "flac", "wav", "opus"],
                        default="mp3",
                    ),
                },
                handler="ffmpeg.extract_audio",
                timeout_seconds=600,
                tags=["ffmpeg", "audio", "extraction"],
            )
        )

        self.register(
            ToolDefinition(
                name="media_thumbnail",
                description="Generate thumbnail from video",
                category=ToolCategory.MEDIA,
                parameters={
                    "input_file": ParameterSchema(
                        type="string",
                        description="Input video file",
                        required=True,
                    ),
                    "output_file": ParameterSchema(
                        type="string",
                        description="Output image file",
                        required=True,
                    ),
                    "timestamp": ParameterSchema(
                        type="string",
                        description="Timestamp to capture (HH:MM:SS or seconds)",
                        default="00:00:01",
                    ),
                    "size": ParameterSchema(
                        type="string",
                        description="Output size (e.g., 320x240)",
                        default=None,
                    ),
                },
                handler="ffmpeg.thumbnail",
                tags=["ffmpeg", "video", "image"],
            )
        )

        # =========================================================================
        # PRODUCTIVITY TOOLS
        # =========================================================================

        self.register(
            ToolDefinition(
                name="task_create",
                description="Create a new task in the Personal Assistant",
                category=ToolCategory.PRODUCTIVITY,
                parameters={
                    "title": ParameterSchema(
                        type="string",
                        description="Task title",
                        required=True,
                    ),
                    "description": ParameterSchema(
                        type="string",
                        description="Task description",
                        default="",
                    ),
                    "priority": ParameterSchema(
                        type="string",
                        description="Priority level",
                        enum=["low", "medium", "high", "urgent"],
                        default="medium",
                    ),
                    "due_date": ParameterSchema(
                        type="string",
                        description="Due date (ISO format)",
                        default=None,
                    ),
                    "tags": ParameterSchema(
                        type="array",
                        description="Task tags",
                        items={"type": "string"},
                        default=[],
                    ),
                },
                handler="personal_assistant.create_task",
                tags=["tasks", "productivity"],
            )
        )

        self.register(
            ToolDefinition(
                name="task_list",
                description="List tasks with optional filters",
                category=ToolCategory.PRODUCTIVITY,
                parameters={
                    "status": ParameterSchema(
                        type="string",
                        description="Filter by status",
                        enum=["pending", "in_progress", "completed", "all"],
                        default="pending",
                    ),
                    "priority": ParameterSchema(
                        type="string",
                        description="Filter by priority",
                        default=None,
                    ),
                    "due_today": ParameterSchema(
                        type="boolean",
                        description="Only show tasks due today",
                        default=False,
                    ),
                },
                handler="personal_assistant.list_tasks",
                tags=["tasks", "productivity"],
            )
        )

        self.register(
            ToolDefinition(
                name="task_update",
                description="Update an existing task",
                category=ToolCategory.PRODUCTIVITY,
                parameters={
                    "task_id": ParameterSchema(
                        type="integer",
                        description="Task ID to update",
                        required=True,
                    ),
                    "status": ParameterSchema(
                        type="string",
                        description="New status",
                        enum=["pending", "in_progress", "completed"],
                        default=None,
                    ),
                    "priority": ParameterSchema(
                        type="string",
                        description="New priority",
                        default=None,
                    ),
                    "due_date": ParameterSchema(
                        type="string",
                        description="New due date",
                        default=None,
                    ),
                },
                handler="personal_assistant.update_task",
                tags=["tasks", "productivity"],
            )
        )

        self.register(
            ToolDefinition(
                name="reminder_set",
                description="Set a reminder",
                category=ToolCategory.PRODUCTIVITY,
                parameters={
                    "title": ParameterSchema(
                        type="string",
                        description="Reminder title",
                        required=True,
                    ),
                    "time": ParameterSchema(
                        type="string",
                        description="Reminder time (ISO format or natural language)",
                        required=True,
                    ),
                    "message": ParameterSchema(
                        type="string",
                        description="Reminder message",
                        default="",
                    ),
                    "recurring": ParameterSchema(
                        type="string",
                        description="Recurrence pattern (daily, weekly, monthly)",
                        default=None,
                    ),
                },
                handler="personal_assistant.set_reminder",
                tags=["reminders", "productivity"],
            )
        )

        self.register(
            ToolDefinition(
                name="daily_summary",
                description="Get daily summary of tasks, events, and reminders",
                category=ToolCategory.PRODUCTIVITY,
                parameters={
                    "date": ParameterSchema(
                        type="string",
                        description="Date for summary (ISO format, defaults to today)",
                        default=None,
                    ),
                    "include_completed": ParameterSchema(
                        type="boolean",
                        description="Include completed tasks",
                        default=False,
                    ),
                },
                handler="personal_assistant.daily_summary",
                tags=["productivity", "summary"],
            )
        )

        # =========================================================================
        # AGENT TOOLS
        # =========================================================================

        self.register(
            ToolDefinition(
                name="agent_spawn",
                description="Spawn a specialized subagent for a specific task",
                category=ToolCategory.AGENT,
                parameters={
                    "agent_type": ParameterSchema(
                        type="string",
                        description="Type of subagent to spawn",
                        enum=[
                            "file-ops",
                            "security-audit",
                            "research",
                            "code-gen",
                            "system-admin",
                            "data-analyst",
                            "devops",
                            "qa-tester",
                            "docs-writer",
                            "api-integrator",
                        ],
                        required=True,
                    ),
                    "task": ParameterSchema(
                        type="string",
                        description="Task description for the subagent",
                        required=True,
                    ),
                    "priority": ParameterSchema(
                        type="string",
                        description="Task priority",
                        enum=["P1", "P2", "P3"],
                        default="P2",
                    ),
                    "context": ParameterSchema(
                        type="object",
                        description="Additional context for the agent",
                        default={},
                    ),
                },
                handler="orchestration.spawn_agent",
                tags=["agent", "orchestration"],
            )
        )

        self.register(
            ToolDefinition(
                name="agent_status",
                description="Get status of a running agent",
                category=ToolCategory.AGENT,
                parameters={
                    "session_id": ParameterSchema(
                        type="string",
                        description="Agent session ID",
                        required=True,
                    ),
                },
                handler="orchestration.agent_status",
                tags=["agent", "monitoring"],
            )
        )

        self.register(
            ToolDefinition(
                name="agent_list",
                description="List active agents and their status",
                category=ToolCategory.AGENT,
                parameters={
                    "include_completed": ParameterSchema(
                        type="boolean",
                        description="Include completed agents",
                        default=False,
                    ),
                },
                handler="orchestration.list_agents",
                tags=["agent", "monitoring"],
            )
        )

        # =========================================================================
        # INTEGRATION TOOLS
        # =========================================================================

        self.register(
            ToolDefinition(
                name="log_action",
                description="Log an action to the OsMEN audit trail",
                category=ToolCategory.INTEGRATION,
                parameters={
                    "action": ParameterSchema(
                        type="string",
                        description="Action description",
                        required=True,
                    ),
                    "result": ParameterSchema(
                        type="string",
                        description="Action result",
                        default="",
                    ),
                    "severity": ParameterSchema(
                        type="string",
                        description="Log severity",
                        enum=["debug", "info", "warning", "error", "critical"],
                        default="info",
                    ),
                    "metadata": ParameterSchema(
                        type="object",
                        description="Additional metadata",
                        default={},
                    ),
                },
                handler="logging.log_action",
                tags=["logging", "audit"],
            )
        )

        self.register(
            ToolDefinition(
                name="vector_search",
                description="Direct Qdrant vector search for advanced use cases",
                category=ToolCategory.INTEGRATION,
                parameters={
                    "query": ParameterSchema(
                        type="string",
                        description="Search query to vectorize",
                        required=True,
                    ),
                    "collection": ParameterSchema(
                        type="string",
                        description="Qdrant collection name",
                        required=True,
                    ),
                    "limit": ParameterSchema(
                        type="integer",
                        description="Number of results",
                        default=5,
                        minimum=1,
                        maximum=100,
                    ),
                    "filter": ParameterSchema(
                        type="object",
                        description="Qdrant filter conditions",
                        default=None,
                    ),
                    "with_vectors": ParameterSchema(
                        type="boolean",
                        description="Include vectors in response",
                        default=False,
                    ),
                },
                handler="qdrant.search",
                tags=["vector", "qdrant", "search"],
            )
        )

        # =========================================================================
        # CONVERTX - UNIVERSAL FILE FORMAT CONVERTER (1000+ formats)
        # =========================================================================

        self.register(
            ToolDefinition(
                name="convert_file",
                description="Convert ANY file to ANY format using ConvertX. Supports 1000+ formats: video (mp4, mkv, webm, avi), audio (mp3, wav, flac, ogg), images (jpg, png, webp, heic, avif, svg), documents (pdf, docx, md, html), ebooks (epub, mobi), 3D models (obj, stl, fbx, gltf), and more. Powered by FFmpeg, Pandoc, Vips, Calibre, Assimp, Inkscape.",
                category=ToolCategory.MEDIA,
                parameters={
                    "input_file": ParameterSchema(
                        type="string",
                        description="Path to the input file to convert",
                        required=True,
                    ),
                    "target_format": ParameterSchema(
                        type="string",
                        description="Target format extension (e.g., 'pdf', 'mp4', 'png', 'epub', 'webm', 'docx')",
                        required=True,
                    ),
                    "output_file": ParameterSchema(
                        type="string",
                        description="Optional output file path. If not provided, uses input filename with new extension",
                        default=None,
                    ),
                },
                handler="convertx.convert_file",
                timeout_seconds=3600,  # Large files can take time
                tags=[
                    "convertx",
                    "conversion",
                    "video",
                    "audio",
                    "image",
                    "document",
                    "ebook",
                    "3d",
                    "universal",
                ],
            )
        )

        self.register(
            ToolDefinition(
                name="convert_batch",
                description="Convert multiple files to a target format in batch. Ideal for converting entire folders of media, documents, or images.",
                category=ToolCategory.MEDIA,
                parameters={
                    "input_files": ParameterSchema(
                        type="array",
                        description="List of file paths to convert",
                        items={"type": "string"},
                        required=True,
                    ),
                    "target_format": ParameterSchema(
                        type="string",
                        description="Target format for all files",
                        required=True,
                    ),
                    "output_dir": ParameterSchema(
                        type="string",
                        description="Output directory for converted files",
                        default=None,
                    ),
                },
                handler="convertx.convert_batch",
                timeout_seconds=7200,
                tags=["convertx", "batch", "conversion"],
            )
        )

        self.register(
            ToolDefinition(
                name="get_conversion_options",
                description="Get available output formats for a given input file or format. Shows what a file can be converted to.",
                category=ToolCategory.MEDIA,
                parameters={
                    "input_format": ParameterSchema(
                        type="string",
                        description="Input format extension (e.g., 'mp4', 'docx', 'png')",
                        required=True,
                    ),
                },
                handler="convertx.get_conversion_options",
                tags=["convertx", "formats", "info"],
            )
        )

        self.register(
            ToolDefinition(
                name="convertx_health",
                description="Check ConvertX service health and available converters (FFmpeg, Pandoc, Vips, Calibre, etc.)",
                category=ToolCategory.MEDIA,
                parameters={},
                handler="convertx.health_check",
                tags=["convertx", "health", "status"],
            )
        )

        # =========================================================================
        # COURSE MANAGEMENT TOOLS - Academic Knowledge Base
        # =========================================================================

        self.register(
            ToolDefinition(
                name="course_import_syllabus",
                description="Import a course syllabus (PDF/DOCX) and create complete course structure with calendar events and Obsidian notes. Extracts course info, assignments, exams, and deadlines automatically.",
                category=ToolCategory.KNOWLEDGE,
                parameters={
                    "file_path": ParameterSchema(
                        type="string",
                        description="Path to syllabus file (PDF or DOCX)",
                        required=True,
                    ),
                    "semester": ParameterSchema(
                        type="string",
                        description="Semester name (Fall, Spring, Summer) - auto-detected if not provided",
                        default=None,
                    ),
                    "year": ParameterSchema(
                        type="integer",
                        description="Academic year - auto-detected if not provided",
                        default=None,
                    ),
                    "sync_calendar": ParameterSchema(
                        type="boolean",
                        description="Sync extracted events to Google/Outlook calendar",
                        default=True,
                    ),
                    "create_obsidian_notes": ParameterSchema(
                        type="boolean",
                        description="Create course notes structure in Obsidian vault",
                        default=True,
                    ),
                },
                handler="courses.import_syllabus",
                tags=["courses", "syllabus", "academic", "import"],
            )
        )

        self.register(
            ToolDefinition(
                name="course_list",
                description="List all courses, optionally filtered by semester and year",
                category=ToolCategory.KNOWLEDGE,
                parameters={
                    "semester": ParameterSchema(
                        type="string",
                        description="Filter by semester (Fall, Spring, Summer)",
                        default=None,
                    ),
                    "year": ParameterSchema(
                        type="integer",
                        description="Filter by academic year",
                        default=None,
                    ),
                },
                handler="courses.list_courses",
                tags=["courses", "academic", "list"],
            )
        )

        self.register(
            ToolDefinition(
                name="course_semester_overview",
                description="Get comprehensive overview of current or specified semester including all courses, upcoming events, exams, assignments, and scheduling conflicts",
                category=ToolCategory.KNOWLEDGE,
                parameters={
                    "semester": ParameterSchema(
                        type="string",
                        description="Semester name (defaults to current semester)",
                        default=None,
                    ),
                    "year": ParameterSchema(
                        type="integer",
                        description="Academic year (defaults to current year)",
                        default=None,
                    ),
                },
                handler="courses.semester_overview",
                tags=["courses", "semester", "overview", "academic"],
            )
        )

        self.register(
            ToolDefinition(
                name="course_bulk_import",
                description="Import multiple syllabi at once for semester setup. Ideal for beginning-of-semester course load configuration.",
                category=ToolCategory.KNOWLEDGE,
                parameters={
                    "file_paths": ParameterSchema(
                        type="array",
                        description="List of paths to syllabus files",
                        items={"type": "string"},
                        required=True,
                    ),
                    "semester": ParameterSchema(
                        type="string",
                        description="Semester name for all courses",
                        default=None,
                    ),
                    "year": ParameterSchema(
                        type="integer",
                        description="Academic year for all courses",
                        default=None,
                    ),
                },
                handler="courses.bulk_import",
                tags=["courses", "bulk", "semester", "setup"],
            )
        )

        self.register(
            ToolDefinition(
                name="course_sync_calendar",
                description="Sync a specific course's events to calendar (Google/Outlook)",
                category=ToolCategory.KNOWLEDGE,
                parameters={
                    "course_id": ParameterSchema(
                        type="string",
                        description="Course ID to sync",
                        required=True,
                    ),
                },
                handler="courses.sync_calendar",
                tags=["courses", "calendar", "sync"],
            )
        )

        self.register(
            ToolDefinition(
                name="course_sync_obsidian",
                description="Create or update Obsidian notes for a specific course",
                category=ToolCategory.KNOWLEDGE,
                parameters={
                    "course_id": ParameterSchema(
                        type="string",
                        description="Course ID to sync",
                        required=True,
                    ),
                },
                handler="courses.sync_obsidian",
                tags=["courses", "obsidian", "sync", "notes"],
            )
        )

        logger.info(f"Initialized {len(self._tools)} tools")

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool"""
        self._tools[tool.name] = tool

    def register_handler(self, tool_name: str, handler: Callable) -> None:
        """Register a handler function for a tool"""
        if tool_name not in self._tools:
            raise ValueError(f"Tool not found: {tool_name}")
        self._handlers[tool_name] = handler

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name"""
        return self._tools.get(name)

    def list(
        self,
        category: Optional[ToolCategory] = None,
        enabled_only: bool = True,
        tags: Optional[List[str]] = None,
    ) -> List[ToolDefinition]:
        """List tools with optional filtering"""
        tools = list(self._tools.values())

        if enabled_only:
            tools = [t for t in tools if t.enabled]

        if category:
            tools = [t for t in tools if t.category == category]

        if tags:
            tools = [t for t in tools if any(tag in t.tags for tag in tags)]

        return tools

    def get_handler(self, name: str) -> Optional[Callable]:
        """Get the handler for a tool"""
        return self._handlers.get(name)

    def to_mcp_format(self) -> List[Dict[str, Any]]:
        """Export all tools in MCP format"""
        return [tool.to_mcp_schema() for tool in self.list(enabled_only=True)]

    def to_json(self, indent: int = 2) -> str:
        """Export tool registry to JSON"""
        data = {
            "version": "2.0.0",
            "tools": [tool.to_dict() for tool in self._tools.values()],
            "categories": [c.value for c in ToolCategory],
        }
        return json.dumps(data, indent=indent)

    def save_config(self, path: Path) -> None:
        """Save tool configuration to file"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(self.to_json())
        logger.info(f"Saved tool config to {path}")

    def load_config(self, path: Path) -> None:
        """Load additional tools from config file"""
        if not path.exists():
            logger.warning(f"Config file not found: {path}")
            return

        with open(path) as f:
            data = json.load(f)

        for tool_data in data.get("tools", []):
            params = {}
            for name, param_data in tool_data.get("parameters", {}).items():
                params[name] = ParameterSchema(
                    type=param_data.get("type", "string"),
                    description=param_data.get("description", ""),
                    required=param_data.get("required", False),
                    default=param_data.get("default"),
                    enum=param_data.get("enum"),
                )

            tool = ToolDefinition(
                name=tool_data["name"],
                description=tool_data["description"],
                category=ToolCategory(tool_data.get("category", "integration")),
                parameters=params,
                handler=tool_data.get("handler"),
                requires_confirmation=tool_data.get("requires_confirmation", False),
                timeout_seconds=tool_data.get("timeout_seconds", 300),
                enabled=tool_data.get("enabled", True),
                tags=tool_data.get("tags", []),
            )
            self.register(tool)

        logger.info(f"Loaded {len(data.get('tools', []))} tools from {path}")


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry"""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
