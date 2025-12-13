#!/usr/bin/env python3
"""
OsMEN Workspace Scanner Agent

Creates and maintains a dynamic, living map of the entire OsMEN workspace.
This is the "tech admin" that knows every node, pipeline, file, and capability.

Features:
- Deep recursive directory scanning
- Agent instruction file extraction
- Capability mapping (TTS, STT, calendar, email, image gen, etc.)
- File change monitoring with automatic map updates
- Integration with Infrastructure Agent for context distribution
- Langflow/n8n workflow integration for automated analysis

All components of the workspace are known at all times to any agents running within it.
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import sys
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

# Add parent paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("workspace_scanner")


# ============================================================================
# Enums and Data Classes
# ============================================================================


class ComponentType(Enum):
    """Types of workspace components"""

    AGENT = "agent"
    TOOL = "tool"
    INTEGRATION = "integration"
    PIPELINE = "pipeline"
    WORKFLOW = "workflow"
    FLOW = "flow"
    PARSER = "parser"
    CONFIG = "config"
    DOCUMENTATION = "documentation"
    INSTRUCTION = "instruction"
    TEST = "test"
    SCRIPT = "script"
    TEMPLATE = "template"
    DATA = "data"
    KNOWLEDGE = "knowledge"
    INFRASTRUCTURE = "infrastructure"
    GATEWAY = "gateway"
    WEB = "web"
    UNKNOWN = "unknown"


class Capability(Enum):
    """Workspace capabilities"""

    # Voice/Audio
    TTS = "text_to_speech"
    STT = "speech_to_text"
    AUDIOBOOK = "audiobook_generation"
    LIVE_CAPTION = "live_captioning"
    VOICE_CLONING = "voice_cloning"

    # Scheduling/Calendar
    CALENDAR_SYNC = "calendar_sync"
    GOOGLE_CALENDAR = "google_calendar"
    OUTLOOK_CALENDAR = "outlook_calendar"
    SCHEDULING = "scheduling_optimization"
    REMINDERS = "reminders"

    # Email/Communications
    EMAIL = "email_management"
    OUTLOOK_EMAIL = "outlook_email"
    GMAIL = "gmail"
    NOTIFICATIONS = "notifications"

    # Creative/Media
    IMAGE_GEN = "image_generation"
    VIDEO_PROCESSING = "video_processing"
    AUDIO_PROCESSING = "audio_processing"
    CONTENT_CREATION = "content_creation"
    MEDIA_CONVERSION = "media_conversion"
    DRM_LIBERATION = "drm_liberation"

    # Social/Marketing
    SOCIAL_MEDIA = "social_media_management"
    CAMPAIGN_CREATION = "campaign_creation"

    # Research/Knowledge
    RAG = "retrieval_augmented_generation"
    RESEARCH = "research_intelligence"
    KNOWLEDGE_MANAGEMENT = "knowledge_management"
    OBSIDIAN = "obsidian_integration"
    LIBRARIAN = "document_library"
    DZOGCHEN_RESEARCH = "dzogchen_research"
    TUMMO_RESEARCH = "tummo_research"

    # System/Security
    BOOT_HARDENING = "boot_hardening"
    SECURITY_OPS = "security_operations"
    OS_OPTIMIZATION = "os_optimization"
    FOCUS_GUARDRAILS = "focus_guardrails"
    FIREWALL = "firewall_management"

    # Sync/Integration
    MOBILE_SYNC = "mobile_device_sync"
    HEALTH_SYNC = "health_data_sync"
    CLOUD_SYNC = "cloud_sync"

    # AI/Agents
    LLM_INFERENCE = "llm_inference"
    AGENT_ORCHESTRATION = "agent_orchestration"
    WORKFLOW_AUTOMATION = "workflow_automation"
    LANGFLOW = "langflow_flows"
    N8N = "n8n_workflows"
    DEEPAGENTS = "deepagents_integration"

    # OAuth/Auth
    OAUTH = "oauth_authentication"
    GOOGLE_AUTH = "google_oauth"
    MICROSOFT_AUTH = "microsoft_oauth"

    # Parsing/Processing
    SYLLABUS_PARSING = "syllabus_parsing"
    DOCUMENT_PARSING = "document_parsing"

    # Other
    CONVERTX = "universal_conversion"
    DAILY_BRIEF = "daily_briefing"
    PERSONAL_ASSISTANT = "personal_assistant"


@dataclass
class FileInfo:
    """Information about a file"""

    path: str
    name: str
    extension: str
    size: int
    modified: str
    hash: str
    component_type: str
    language: Optional[str] = None
    description: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)


@dataclass
class DirectoryInfo:
    """Information about a directory"""

    path: str
    name: str
    file_count: int
    subdirs: List[str]
    component_type: str
    description: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)


@dataclass
class AgentInstructionFile:
    """Agent instruction file metadata"""

    path: str
    name: str
    agent_name: str
    description: str
    capabilities: List[str]
    tools: List[str]
    content_hash: str
    last_modified: str


@dataclass
class WorkspaceMap:
    """Complete workspace map"""

    version: str
    generated_at: str
    last_updated: str
    root_path: str

    # Stats
    total_files: int
    total_directories: int
    total_agents: int
    total_pipelines: int
    total_capabilities: int

    # Components
    directories: Dict[str, DirectoryInfo]
    files: Dict[str, FileInfo]
    agents: Dict[str, Dict[str, Any]]
    instruction_files: Dict[str, AgentInstructionFile]

    # Capabilities
    capabilities: Dict[str, List[str]]  # capability -> list of files providing it

    # Pipelines and flows
    langflow_flows: Dict[str, Dict[str, Any]]
    n8n_workflows: Dict[str, Dict[str, Any]]
    native_pipelines: Dict[str, Dict[str, Any]]

    # Integration points
    integrations: Dict[str, Dict[str, Any]]
    tools: Dict[str, Dict[str, Any]]

    # Metadata
    file_hashes: Dict[str, str]  # path -> hash for change detection


# ============================================================================
# Capability Detection
# ============================================================================

# Keywords to capability mapping
CAPABILITY_KEYWORDS = {
    # Voice/Audio
    Capability.TTS: [
        "tts",
        "text_to_speech",
        "text-to-speech",
        "pyttsx",
        "elevenlabs",
        "coqui",
        "edge_tts",
        "speak",
        "voice_synth",
    ],
    Capability.STT: [
        "stt",
        "speech_to_text",
        "speech-to-text",
        "whisper",
        "transcribe",
        "transcription",
        "faster_whisper",
    ],
    Capability.AUDIOBOOK: [
        "audiobook",
        "audio_book",
        "book_audio",
        "chapter_audio",
        "narration",
    ],
    Capability.LIVE_CAPTION: [
        "live_caption",
        "caption",
        "subtitle",
        "subtitles",
        "closed_caption",
    ],
    # Calendar
    Capability.CALENDAR_SYNC: ["calendar", "schedule", "event", "appointment"],
    Capability.GOOGLE_CALENDAR: ["google_calendar", "gcal", "googleapis.calendar"],
    Capability.OUTLOOK_CALENDAR: [
        "outlook_calendar",
        "outlook.calendar",
        "microsoft.calendar",
    ],
    Capability.SCHEDULING: [
        "schedule_optim",
        "priority_rank",
        "study_session",
        "procrastination",
    ],
    Capability.REMINDERS: ["reminder", "notify", "alert", "snooze", "escalation"],
    # Email
    Capability.EMAIL: ["email", "mail", "smtp", "imap", "inbox", "compose"],
    Capability.OUTLOOK_EMAIL: ["outlook.mail", "microsoft.mail", "o365.mail"],
    Capability.GMAIL: ["gmail", "google.mail"],
    # Creative/Media
    Capability.IMAGE_GEN: [
        "image_gen",
        "stable_diffusion",
        "dall-e",
        "invokeai",
        "comfyui",
        "midjourney",
        "txt2img",
    ],
    Capability.VIDEO_PROCESSING: [
        "ffmpeg",
        "video",
        "mp4",
        "mkv",
        "webm",
        "encode",
        "transcode",
    ],
    Capability.AUDIO_PROCESSING: ["audio", "mp3", "wav", "flac", "audio_process"],
    Capability.CONTENT_CREATION: ["content_creat", "podcast", "creative_tool"],
    Capability.MEDIA_CONVERSION: [
        "convertx",
        "media_convert",
        "format_convert",
        "pandoc",
        "calibre",
    ],
    Capability.DRM_LIBERATION: ["drm", "dedrm", "acsm", "liberation", "deacsm"],
    # Social
    Capability.SOCIAL_MEDIA: [
        "social_media",
        "twitter",
        "instagram",
        "linkedin",
        "facebook",
    ],
    Capability.CAMPAIGN_CREATION: ["campaign", "marketing", "social_campaign"],
    # Research/Knowledge
    Capability.RAG: [
        "rag",
        "retrieval",
        "embedding",
        "vector",
        "chromadb",
        "qdrant",
        "semantic_search",
    ],
    Capability.RESEARCH: ["research", "paper", "arxiv", "scholar", "citation"],
    Capability.KNOWLEDGE_MANAGEMENT: [
        "knowledge",
        "obsidian",
        "note",
        "vault",
        "markdown",
    ],
    Capability.OBSIDIAN: ["obsidian", "vault", "wikilink", "backlink"],
    Capability.LIBRARIAN: ["librarian", "document", "library", "index", "catalog"],
    Capability.DZOGCHEN_RESEARCH: [
        "dzogchen",
        "rigpa",
        "tibetan_buddhism",
        "nature_of_mind",
    ],
    Capability.TUMMO_RESEARCH: ["tummo", "inner_heat", "chandali", "gtum-mo"],
    # System/Security
    Capability.BOOT_HARDENING: [
        "boot_harden",
        "security_scan",
        "integrity",
        "secure_boot",
    ],
    Capability.SECURITY_OPS: ["security_ops", "vulnerability", "audit", "codeql"],
    Capability.OS_OPTIMIZATION: ["os_optim", "system_optim", "performance_tune"],
    Capability.FOCUS_GUARDRAILS: [
        "focus",
        "guardrail",
        "distraction",
        "pomodoro",
        "block",
    ],
    Capability.FIREWALL: ["firewall", "simplewall", "network_rule", "port_block"],
    # Sync
    Capability.MOBILE_SYNC: ["mobile_sync", "android", "ios", "phone_sync"],
    Capability.HEALTH_SYNC: ["health_sync", "google_fit", "health_connect", "fitness"],
    Capability.CLOUD_SYNC: ["cloud_sync", "dropbox", "onedrive", "gdrive"],
    # AI/Agents
    Capability.LLM_INFERENCE: [
        "llm",
        "openai",
        "anthropic",
        "ollama",
        "lm_studio",
        "gpt",
        "claude",
    ],
    Capability.AGENT_ORCHESTRATION: [
        "orchestrat",
        "coordinator",
        "delegate",
        "multi_agent",
    ],
    Capability.WORKFLOW_AUTOMATION: ["workflow", "automation", "trigger", "webhook"],
    Capability.LANGFLOW: ["langflow", "flow_builder", "visual_llm"],
    Capability.N8N: ["n8n", "workflow_engine"],
    Capability.DEEPAGENTS: ["deepagent", "sub_agent", "computer_access"],
    # OAuth
    Capability.OAUTH: ["oauth", "token", "authorization", "bearer"],
    Capability.GOOGLE_AUTH: ["google_oauth", "googleapis.auth"],
    Capability.MICROSOFT_AUTH: ["microsoft_oauth", "azure_ad", "msal"],
    # Parsing
    Capability.SYLLABUS_PARSING: ["syllabus", "course_schedule", "semester"],
    Capability.DOCUMENT_PARSING: ["doc_parse", "pdf_parse", "docx", "pptx"],
    # Other
    Capability.CONVERTX: ["convertx", "universal_convert", "1000_formats"],
    Capability.DAILY_BRIEF: ["daily_brief", "morning_brief", "daily_summary"],
    Capability.PERSONAL_ASSISTANT: ["personal_assist", "task_manage", "todo"],
}


def detect_capabilities(content: str, filename: str) -> List[str]:
    """Detect capabilities from file content and name."""
    capabilities = set()
    content_lower = content.lower()
    filename_lower = filename.lower()

    for cap, keywords in CAPABILITY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in content_lower or keyword in filename_lower:
                capabilities.add(cap.value)
                break

    return list(capabilities)


# Table-driven component type detection (PHOENIX Protocol: complexity 40 → ~5)
# Maps directory names to component types (without slashes for flexible matching)
_COMPONENT_TYPE_MAP: Dict[str, ComponentType] = {
    "tools": ComponentType.TOOL,
    "integrations": ComponentType.INTEGRATION,
    "langflow": ComponentType.FLOW,
    "n8n": ComponentType.WORKFLOW,
    "parsers": ComponentType.PARSER,
    "config": ComponentType.CONFIG,
    "docs": ComponentType.DOCUMENTATION,
    "tests": ComponentType.TEST,
    "scripts": ComponentType.SCRIPT,
    "infrastructure": ComponentType.INFRASTRUCTURE,
    "gateway": ComponentType.GATEWAY,
    "web": ComponentType.WEB,
    "knowledge": ComponentType.KNOWLEDGE,
    "workflows": ComponentType.PIPELINE,
    "templates": ComponentType.TEMPLATE,
    "data": ComponentType.DATA,
}


def _path_contains_dir(path_str: str, dir_name: str) -> bool:
    """Check if path contains a directory name (cross-platform)."""
    patterns = [
        f"/{dir_name}/",
        f"\\{dir_name}\\",
        f"/{dir_name}\\",
        f"\\{dir_name}/",
        # Also match at start of relative paths
        f"{dir_name}/",
        f"{dir_name}\\",
    ]
    return any(p in path_str for p in patterns)


def detect_component_type(path: Path, content: Optional[str] = None) -> ComponentType:
    """Detect the type of component from path and content.

    Uses table-driven dispatch for path pattern matching.
    Refactored from complexity 40 to ~8 (PHOENIX Protocol compliance).

    Args:
        path: Path to the file being analyzed
        content: Optional file content for deeper analysis

    Returns:
        ComponentType enum value
    """
    path_str = str(path).lower()
    name = path.name.lower()

    # Special handling for agents directory (has sub-types)
    if _path_contains_dir(path_str, "agents"):
        if "_agent.py" in name:
            return ComponentType.AGENT
        if ".agent.md" in name:
            return ComponentType.INSTRUCTION
        return ComponentType.AGENT

    # Table-driven lookup for other directories
    for dir_name, component_type in _COMPONENT_TYPE_MAP.items():
        if _path_contains_dir(path_str, dir_name):
            return component_type

    # Filename-based fallbacks
    if name.startswith("test_"):
        return ComponentType.TEST
    if "instruction" in name or ".agent.md" in name:
        return ComponentType.INSTRUCTION

    return ComponentType.UNKNOWN


def get_file_language(extension: str) -> Optional[str]:
    """Get programming language from file extension."""
    lang_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".md": "markdown",
        ".html": "html",
        ".css": "css",
        ".sh": "bash",
        ".bat": "batch",
        ".ps1": "powershell",
        ".sql": "sql",
        ".toml": "toml",
        ".xml": "xml",
    }
    return lang_map.get(extension.lower())


def compute_file_hash(content: str) -> str:
    """Compute SHA256 hash of file content."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


# ============================================================================
# Workspace Scanner Agent
# ============================================================================


class WorkspaceScannerAgent:
    """
    Agent that creates and maintains the dynamic workspace map.

    This is the "tech admin who is familiar with every node, every pipeline,
    every framework" - providing complete workspace awareness to all agents.
    """

    # Directories to skip
    SKIP_DIRS = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        ".mypy_cache",
        ".pytest_cache",
        ".coverage",
        "htmlcov",
        "dist",
        "build",
        "*.egg-info",
        ".tox",
        ".eggs",
    }

    # File extensions to scan
    SCAN_EXTENSIONS = {
        ".py",
        ".js",
        ".ts",
        ".json",
        ".yaml",
        ".yml",
        ".md",
        ".html",
        ".css",
        ".sh",
        ".bat",
        ".ps1",
        ".sql",
        ".toml",
        ".xml",
    }

    def __init__(self, workspace_root: Optional[str] = None):
        """Initialize the workspace scanner."""
        self.workspace_root = Path(
            workspace_root or Path(__file__).parent.parent.parent
        )
        self.map_path = self.workspace_root / "infrastructure" / "workspace_map.json"
        self.map_path.parent.mkdir(parents=True, exist_ok=True)

        self.workspace_map: Optional[WorkspaceMap] = None
        self.observer: Optional[Observer] = None
        self._lock = threading.Lock()

        logger.info(f"WorkspaceScannerAgent initialized at {self.workspace_root}")

    def scan_workspace(self) -> WorkspaceMap:
        """
        Perform a deep recursive scan of the entire workspace.

        Returns:
            Complete WorkspaceMap with all components
        """
        logger.info("Starting deep workspace scan...")

        directories: Dict[str, DirectoryInfo] = {}
        files: Dict[str, FileInfo] = {}
        agents: Dict[str, Dict[str, Any]] = {}
        instruction_files: Dict[str, AgentInstructionFile] = {}
        capabilities: Dict[str, List[str]] = {}
        langflow_flows: Dict[str, Dict[str, Any]] = {}
        n8n_workflows: Dict[str, Dict[str, Any]] = {}
        native_pipelines: Dict[str, Dict[str, Any]] = {}
        integrations: Dict[str, Dict[str, Any]] = {}
        tools: Dict[str, Dict[str, Any]] = {}
        file_hashes: Dict[str, str] = {}

        # Walk the entire workspace
        for root, dirs, filenames in os.walk(self.workspace_root):
            root_path = Path(root)
            relative_root = root_path.relative_to(self.workspace_root)

            # Skip excluded directories
            dirs[:] = [
                d for d in dirs if d not in self.SKIP_DIRS and not d.startswith(".")
            ]

            # Process directory
            dir_info = self._process_directory(root_path, dirs, filenames)
            directories[str(relative_root)] = dir_info

            # Process files
            for filename in filenames:
                file_path = root_path / filename
                ext = file_path.suffix.lower()

                # Only process certain file types
                if ext not in self.SCAN_EXTENSIONS:
                    continue

                try:
                    file_info = self._process_file(file_path)
                    if file_info:
                        rel_path = str(file_path.relative_to(self.workspace_root))
                        files[rel_path] = file_info
                        file_hashes[rel_path] = file_info.hash

                        # Track capabilities
                        for cap in file_info.capabilities:
                            if cap not in capabilities:
                                capabilities[cap] = []
                            capabilities[cap].append(rel_path)

                        # Categorize by type
                        if file_info.component_type == ComponentType.AGENT.value:
                            agents[rel_path] = self._extract_agent_info(
                                file_path, file_info
                            )
                        elif (
                            file_info.component_type == ComponentType.INSTRUCTION.value
                        ):
                            instr = self._parse_instruction_file(file_path)
                            if instr:
                                instruction_files[rel_path] = instr
                        elif file_info.component_type == ComponentType.FLOW.value:
                            flow_info = self._parse_langflow_flow(file_path)
                            if flow_info:
                                langflow_flows[rel_path] = flow_info
                        elif file_info.component_type == ComponentType.WORKFLOW.value:
                            workflow_info = self._parse_n8n_workflow(file_path)
                            if workflow_info:
                                n8n_workflows[rel_path] = workflow_info
                        elif (
                            file_info.component_type == ComponentType.INTEGRATION.value
                        ):
                            integrations[rel_path] = self._extract_integration_info(
                                file_path, file_info
                            )
                        elif file_info.component_type == ComponentType.TOOL.value:
                            tools[rel_path] = self._extract_tool_info(
                                file_path, file_info
                            )

                except Exception as e:
                    logger.warning(f"Error processing {file_path}: {e}")

        # Load native pipelines from connections.json
        native_pipelines = self._load_native_pipelines()

        # Build the complete workspace map
        now = datetime.now().isoformat()
        self.workspace_map = WorkspaceMap(
            version="1.0.0",
            generated_at=now,
            last_updated=now,
            root_path=str(self.workspace_root),
            total_files=len(files),
            total_directories=len(directories),
            total_agents=len(agents),
            total_pipelines=len(langflow_flows)
            + len(n8n_workflows)
            + len(native_pipelines),
            total_capabilities=len(capabilities),
            directories={k: asdict(v) for k, v in directories.items()},
            files={k: asdict(v) for k, v in files.items()},
            agents=agents,
            instruction_files={k: asdict(v) for k, v in instruction_files.items()},
            capabilities=capabilities,
            langflow_flows=langflow_flows,
            n8n_workflows=n8n_workflows,
            native_pipelines=native_pipelines,
            integrations=integrations,
            tools=tools,
            file_hashes=file_hashes,
        )

        logger.info(
            f"Scan complete: {len(files)} files, {len(directories)} dirs, "
            f"{len(agents)} agents, {len(capabilities)} capabilities"
        )

        return self.workspace_map

    def _process_directory(
        self, path: Path, subdirs: List[str], files: List[str]
    ) -> DirectoryInfo:
        """Process a directory and extract metadata."""
        relative = path.relative_to(self.workspace_root)
        component_type = detect_component_type(path)

        return DirectoryInfo(
            path=str(relative),
            name=path.name,
            file_count=len(files),
            subdirs=subdirs,
            component_type=component_type.value,
            description=self._get_directory_description(path),
            capabilities=[],
        )

    def _process_file(self, path: Path) -> Optional[FileInfo]:
        """Process a file and extract metadata."""
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None

        relative = path.relative_to(self.workspace_root)
        component_type = detect_component_type(path, content)
        capabilities = detect_capabilities(content, path.name)

        # Extract description from docstring or first comment
        description = self._extract_description(content, path.suffix)

        return FileInfo(
            path=str(relative),
            name=path.name,
            extension=path.suffix,
            size=path.stat().st_size,
            modified=datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            hash=compute_file_hash(content),
            component_type=component_type.value,
            language=get_file_language(path.suffix),
            description=description,
            capabilities=capabilities,
            dependencies=[],
            exports=[],
        )

    def _extract_description(self, content: str, extension: str) -> Optional[str]:
        """Extract description from file content."""
        if extension == ".py":
            # Extract Python docstring
            match = re.search(r'^"""([^"]+?)"""', content, re.MULTILINE | re.DOTALL)
            if match:
                return match.group(1).strip()[:200]
        elif extension == ".md":
            # Extract first heading or paragraph
            lines = content.split("\n")
            for line in lines[:10]:
                line = line.strip()
                if line and not line.startswith("#"):
                    return line[:200]
                if line.startswith("# "):
                    return line[2:][:200]
        elif extension == ".json":
            try:
                data = json.loads(content)
                return data.get("description", data.get("name", None))
            except:
                pass
        return None

    def _get_directory_description(self, path: Path) -> Optional[str]:
        """Get description from README or __init__.py in directory."""
        readme = path / "README.md"
        if readme.exists():
            try:
                content = readme.read_text()[:500]
                lines = content.split("\n")
                for line in lines[:5]:
                    if line.strip() and not line.startswith("#"):
                        return line.strip()[:200]
            except:
                pass

        init_py = path / "__init__.py"
        if init_py.exists():
            return self._extract_description(init_py.read_text(), ".py")

        return None

    def _extract_agent_info(self, path: Path, file_info: FileInfo) -> Dict[str, Any]:
        """Extract detailed agent information."""
        content = path.read_text(encoding="utf-8", errors="ignore")

        # Find class name
        class_match = re.search(r"class\s+(\w+(?:Agent)?)\s*[:(]", content)
        class_name = class_match.group(1) if class_match else path.stem

        return {
            "name": class_name,
            "path": file_info.path,
            "description": file_info.description,
            "capabilities": file_info.capabilities,
            "status": "active",
            "has_langflow_flow": self._check_langflow_flow_exists(path),
            "has_n8n_workflow": self._check_n8n_workflow_exists(path),
        }

    def _parse_instruction_file(self, path: Path) -> Optional[AgentInstructionFile]:
        """Parse an agent instruction file (.agent.md, etc.)."""
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")

            # Extract agent name from content or filename
            name_match = re.search(r"name:\s*([^\n]+)", content, re.IGNORECASE)
            agent_name = (
                name_match.group(1).strip()
                if name_match
                else path.stem.replace(".agent", "")
            )

            # Extract description
            desc_match = re.search(
                r"description:\s*[|>]?\s*([^\n]+(?:\n\s+[^\n]+)*)",
                content,
                re.IGNORECASE,
            )
            description = desc_match.group(1).strip()[:500] if desc_match else ""

            # Extract capabilities/tools
            capabilities = detect_capabilities(content, path.name)

            # Extract tools
            tools = []
            tools_match = re.search(
                r"tools(?:_used)?:\s*\n((?:\s+-\s+[^\n]+\n?)+)", content, re.IGNORECASE
            )
            if tools_match:
                tools = [
                    t.strip("- \n")
                    for t in tools_match.group(1).split("\n")
                    if t.strip("- \n")
                ]

            return AgentInstructionFile(
                path=str(path.relative_to(self.workspace_root)),
                name=path.name,
                agent_name=agent_name,
                description=description,
                capabilities=capabilities,
                tools=tools,
                content_hash=compute_file_hash(content),
                last_modified=datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            )
        except Exception as e:
            logger.warning(f"Error parsing instruction file {path}: {e}")
            return None

    def _parse_langflow_flow(self, path: Path) -> Optional[Dict[str, Any]]:
        """Parse a Langflow flow JSON file."""
        if not path.suffix == ".json":
            return None

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            data = json.loads(content)

            # Count nodes
            node_count = 0
            if isinstance(data, dict):
                if "nodes" in data:
                    node_count = len(data.get("nodes", []))
                elif "data" in data:
                    node_count = len(data.get("data", {}).get("nodes", []))

            return {
                "name": path.stem,
                "path": str(path.relative_to(self.workspace_root)),
                "description": data.get("description", ""),
                "node_count": node_count,
                "type": "coordinator" if "coordinator" in path.stem else "specialist",
            }
        except Exception as e:
            logger.warning(f"Error parsing Langflow flow {path}: {e}")
            return None

    def _parse_n8n_workflow(self, path: Path) -> Optional[Dict[str, Any]]:
        """Parse an n8n workflow JSON file."""
        if not path.suffix == ".json":
            return None

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            data = json.loads(content)

            nodes = data.get("nodes", [])

            # Determine trigger type
            trigger_type = "manual"
            for node in nodes:
                node_type = node.get("type", "").lower()
                if "cron" in node_type or "schedule" in node_type:
                    trigger_type = "scheduled"
                    break
                elif "webhook" in node_type:
                    trigger_type = "webhook"
                    break

            return {
                "name": path.stem,
                "path": str(path.relative_to(self.workspace_root)),
                "description": data.get("description", ""),
                "node_count": len(nodes),
                "trigger_type": trigger_type,
            }
        except Exception as e:
            logger.warning(f"Error parsing n8n workflow {path}: {e}")
            return None

    def _load_native_pipelines(self) -> Dict[str, Dict[str, Any]]:
        """Load native pipelines from connections.json."""
        connections_path = (
            self.workspace_root / "infrastructure" / "graph" / "connections.json"
        )

        if not connections_path.exists():
            return {}

        try:
            data = json.loads(connections_path.read_text())
            pipelines = {}

            for pid, pdata in data.get("pipelines", {}).items():
                if pid.startswith("_comment"):
                    continue
                if pdata.get("type", "native") == "native":
                    pipelines[pid] = {
                        "name": pdata.get("name", pid),
                        "description": pdata.get("description", ""),
                        "stages": len(pdata.get("stages", [])),
                        "triggers": pdata.get("triggers", []),
                    }

            return pipelines
        except Exception as e:
            logger.warning(f"Error loading native pipelines: {e}")
            return {}

    def _extract_integration_info(
        self, path: Path, file_info: FileInfo
    ) -> Dict[str, Any]:
        """Extract integration information."""
        return {
            "name": path.stem,
            "path": file_info.path,
            "description": file_info.description,
            "capabilities": file_info.capabilities,
            "language": file_info.language,
        }

    def _extract_tool_info(self, path: Path, file_info: FileInfo) -> Dict[str, Any]:
        """Extract tool information."""
        return {
            "name": path.stem,
            "path": file_info.path,
            "description": file_info.description,
            "capabilities": file_info.capabilities,
        }

    def _check_langflow_flow_exists(self, agent_path: Path) -> bool:
        """Check if a Langflow flow exists for this agent."""
        agent_name = agent_path.stem.replace("_agent", "")
        flows_dir = self.workspace_root / "langflow" / "flows"

        if flows_dir.exists():
            for flow in flows_dir.glob("*.json"):
                if agent_name in flow.stem:
                    return True
        return False

    def _check_n8n_workflow_exists(self, agent_path: Path) -> bool:
        """Check if an n8n workflow exists for this agent."""
        agent_name = agent_path.stem.replace("_agent", "")
        workflows_dir = self.workspace_root / "n8n" / "workflows"

        if workflows_dir.exists():
            for workflow in workflows_dir.glob("*.json"):
                if agent_name in workflow.stem:
                    return True
        return False

    def save_map(self, path: Optional[Path] = None) -> None:
        """Save the workspace map to JSON file."""
        save_path = path or self.map_path

        if not self.workspace_map:
            raise ValueError("No workspace map to save. Run scan_workspace() first.")

        with self._lock:
            data = asdict(self.workspace_map)
            save_path.write_text(json.dumps(data, indent=2, default=str))

        logger.info(f"Workspace map saved to {save_path}")

    def load_map(self, path: Optional[Path] = None) -> Optional[WorkspaceMap]:
        """Load workspace map from JSON file."""
        load_path = path or self.map_path

        if not load_path.exists():
            return None

        try:
            data = json.loads(load_path.read_text())
            # Convert dict back to WorkspaceMap (simplified)
            self.workspace_map = WorkspaceMap(**data)
            return self.workspace_map
        except Exception as e:
            logger.error(f"Error loading workspace map: {e}")
            return None

    def get_map(self) -> Optional[WorkspaceMap]:
        """Get the current workspace map."""
        return self.workspace_map

    def get_capabilities_summary(self) -> Dict[str, Any]:
        """Get a summary of all capabilities."""
        if not self.workspace_map:
            return {}

        return {
            "total": self.workspace_map.total_capabilities,
            "capabilities": {
                k: len(v) for k, v in self.workspace_map.capabilities.items()
            },
        }

    def find_by_capability(self, capability: str) -> List[str]:
        """Find all files providing a specific capability."""
        if not self.workspace_map:
            return []

        return self.workspace_map.capabilities.get(capability, [])

    def get_agent_instruction_files(self) -> Dict[str, AgentInstructionFile]:
        """Get all agent instruction files."""
        if not self.workspace_map:
            return {}

        return self.workspace_map.instruction_files

    def has_file_changed(self, path: str) -> bool:
        """Check if a file has changed since last scan."""
        if not self.workspace_map:
            return True

        full_path = self.workspace_root / path
        if not full_path.exists():
            return True

        try:
            current_hash = compute_file_hash(full_path.read_text())
            stored_hash = self.workspace_map.file_hashes.get(path)
            return current_hash != stored_hash
        except:
            return True

    # =========================================================================
    # File Watching
    # =========================================================================

    def start_watching(self, callback: Optional[Callable[[str, str], None]] = None):
        """Start watching the workspace for changes."""
        if self.observer:
            logger.warning("Observer already running")
            return

        event_handler = _WorkspaceChangeHandler(self, callback)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.workspace_root), recursive=True)
        self.observer.start()
        logger.info("Started watching workspace for changes")

    def stop_watching(self):
        """Stop watching the workspace."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("Stopped watching workspace")

    def update_file(self, path: str, event_type: str = "modified"):
        """Update the map for a single file change."""
        with self._lock:
            full_path = self.workspace_root / path

            if event_type == "deleted":
                if self.workspace_map and path in self.workspace_map.files:
                    del self.workspace_map.files[path]
                    self.workspace_map.total_files -= 1
                    logger.info(f"Removed {path} from workspace map")
                return

            if not full_path.exists():
                return

            file_info = self._process_file(full_path)
            if file_info and self.workspace_map:
                self.workspace_map.files[path] = asdict(file_info)
                self.workspace_map.file_hashes[path] = file_info.hash
                self.workspace_map.last_updated = datetime.now().isoformat()
                logger.info(f"Updated {path} in workspace map")


class _WorkspaceChangeHandler(FileSystemEventHandler):
    """Handle file system events for the workspace."""

    def __init__(
        self, scanner: WorkspaceScannerAgent, callback: Optional[Callable] = None
    ):
        self.scanner = scanner
        self.callback = callback
        self._debounce: Dict[str, float] = {}
        self._debounce_seconds = 1.0

    def _should_process(self, path: str) -> bool:
        """Check if we should process this file."""
        # Skip hidden and excluded paths
        parts = Path(path).parts
        for part in parts:
            if part.startswith(".") or part in WorkspaceScannerAgent.SKIP_DIRS:
                return False

        # Only process certain extensions
        ext = Path(path).suffix.lower()
        return ext in WorkspaceScannerAgent.SCAN_EXTENSIONS

    def _debounce_event(self, path: str) -> bool:
        """Debounce rapid file events."""
        now = time.time()
        last = self._debounce.get(path, 0)

        if now - last < self._debounce_seconds:
            return False

        self._debounce[path] = now
        return True

    def on_modified(self, event: FileSystemEvent):
        if event.is_directory:
            return

        if not self._should_process(event.src_path):
            return

        if not self._debounce_event(event.src_path):
            return

        try:
            rel_path = str(
                Path(event.src_path).relative_to(self.scanner.workspace_root)
            )
            self.scanner.update_file(rel_path, "modified")

            if self.callback:
                self.callback(rel_path, "modified")
        except Exception as e:
            logger.warning(f"Error handling file modification: {e}")

    def on_created(self, event: FileSystemEvent):
        if event.is_directory:
            return

        if not self._should_process(event.src_path):
            return

        try:
            rel_path = str(
                Path(event.src_path).relative_to(self.scanner.workspace_root)
            )
            self.scanner.update_file(rel_path, "created")

            if self.callback:
                self.callback(rel_path, "created")
        except Exception as e:
            logger.warning(f"Error handling file creation: {e}")

    def on_deleted(self, event: FileSystemEvent):
        if event.is_directory:
            return

        try:
            rel_path = str(
                Path(event.src_path).relative_to(self.scanner.workspace_root)
            )
            self.scanner.update_file(rel_path, "deleted")

            if self.callback:
                self.callback(rel_path, "deleted")
        except Exception as e:
            logger.warning(f"Error handling file deletion: {e}")


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """Run the workspace scanner."""
    import argparse

    parser = argparse.ArgumentParser(description="OsMEN Workspace Scanner")
    parser.add_argument("--workspace", "-w", help="Workspace root path")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--watch", action="store_true", help="Watch for changes")
    parser.add_argument("--summary", action="store_true", help="Print summary only")

    args = parser.parse_args()

    scanner = WorkspaceScannerAgent(args.workspace)
    workspace_map = scanner.scan_workspace()

    if args.summary:
        print("\n" + "=" * 60)
        print("WORKSPACE SCAN SUMMARY")
        print("=" * 60)
        print(f"Root: {workspace_map.root_path}")
        print(f"Files: {workspace_map.total_files}")
        print(f"Directories: {workspace_map.total_directories}")
        print(f"Agents: {workspace_map.total_agents}")
        print(f"Pipelines: {workspace_map.total_pipelines}")
        print(f"Capabilities: {workspace_map.total_capabilities}")
        print("\n--- Capabilities ---")
        for cap, files in sorted(
            workspace_map.capabilities.items(), key=lambda x: -len(x[1])
        ):
            print(f"  {cap}: {len(files)} files")
        print("\n--- Agent Instructions ---")
        for path, instr in workspace_map.instruction_files.items():
            if isinstance(instr, dict):
                print(f"  {instr.get('agent_name', 'unknown')}: {path}")
            else:
                print(f"  {instr.agent_name}: {path}")
        print("\n--- Langflow Flows ---")
        for name, flow in workspace_map.langflow_flows.items():
            if isinstance(flow, dict):
                print(f"  {flow.get('name', name)}: {flow.get('node_count', 0)} nodes")
            else:
                print(f"  {flow.name}: {flow.node_count} nodes")
        print("\n--- n8n Workflows ---")
        for name, workflow in workspace_map.n8n_workflows.items():
            if isinstance(workflow, dict):
                print(
                    f"  {workflow.get('name', name)}: {workflow.get('trigger_type', 'unknown')}"
                )
            else:
                print(f"  {workflow.name}: {workflow.trigger_type}")
    else:
        output_path = Path(args.output) if args.output else None
        scanner.save_map(output_path)
        print(f"Workspace map saved to {scanner.map_path}")

    if args.watch:
        print("\nWatching for changes (Ctrl+C to stop)...")

        def on_change(path, event_type):
            print(f"  [{event_type}] {path}")

        scanner.start_watching(on_change)

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            scanner.stop_watching()
            scanner.save_map()
            print("\nStopped watching. Map saved.")


if __name__ == "__main__":
    main()
    main()
