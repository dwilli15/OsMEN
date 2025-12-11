"""
OsMEN Unified Orchestration Layer
================================

Central configuration and registry for all OsMEN pipelines, agents, and workflows.
This is the SOURCE OF TRUTH that all components reference.

Two-Way Bindings:
- All agents import from this module for configuration
- All workflows reference these constants
- All instruction files point here
- All logging integrates through here

Path Hierarchy:
- integrations/paths.py -> Base path constants (no dependencies)
- integrations/orchestration.py -> This module (imports paths.py)
- integrations/logging_system.py -> Logging (imports paths.py)
- All agents -> Import from orchestration.py

Usage:
    from integrations.orchestration import OsMEN, Paths, Pipelines, get_pipeline

    # Get any pipeline by name
    pipeline = get_pipeline("daily_briefing")

    # Access global config
    config = OsMEN.config

    # Check system state
    state = OsMEN.get_state()
"""

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Import base paths from shared module to avoid circular imports
from integrations.paths import (
    AGENTS_ROOT,
    CONTENT_ROOT,
    HB411_AUDIOBOOKS,
    HB411_OBSIDIAN,
    HB411_RAG,
    HB411_ROOT,
    HB411_SCRIPTS,
    LANGFLOW_FLOWS,
    LOG_AGENT_SESSIONS,
    LOG_AUDIO_GENERATIONS,
    LOG_CHECK_INS,
    LOG_SYSTEM_EVENTS,
    LOGS_ROOT,
    N8N_WORKFLOWS,
    OSMEN_ROOT,
    TEMPLATE_AM_CHECKIN,
    TEMPLATE_BRIEFING,
    TEMPLATE_DAILY_NOTE,
    TEMPLATE_PM_CHECKIN,
    TEMPLATE_PODCAST,
    TEMPLATE_WEEKLY_REVIEW,
    TRACKER_METRICS,
    TRACKER_PROGRESS,
    TRACKER_READINGS,
    VAULT_CHAPTERS,
    VAULT_DAILY,
    VAULT_PROGRESS,
    VAULT_RESOURCES,
    VAULT_ROOT,
    VAULT_TEMPLATES,
    VAULT_WEEKLY,
)

# =============================================================================
# CORE PATHS - Re-export from paths.py with additional paths
# =============================================================================


class Paths:
    """
    Centralized path configuration - ALL components must use these

    Base paths imported from integrations/paths.py
    Extended paths defined here for orchestration-specific needs
    """

    # Re-export from paths.py
    OSMEN_ROOT = OSMEN_ROOT
    CONTENT_ROOT = CONTENT_ROOT
    LOGS_ROOT = LOGS_ROOT
    AGENTS_ROOT = AGENTS_ROOT

    # Course-specific (HB411)
    HB411_ROOT = HB411_ROOT
    HB411_OBSIDIAN = HB411_OBSIDIAN
    HB411_AUDIOBOOKS = HB411_AUDIOBOOKS
    HB411_PODCASTS = HB411_ROOT / "podcasts"
    HB411_PODCAST_SCRIPTS = HB411_ROOT / "podcast_scripts"
    HB411_BRIEFINGS = HB411_ROOT / "daily_briefings"
    HB411_BRIEFING_SCRIPTS = HB411_ROOT / "briefing_scripts"
    HB411_EMBEDDINGS = HB411_ROOT / "embeddings"
    HB411_CALENDAR = HB411_ROOT / "calendar"

    # Obsidian vault structure
    VAULT_TEMPLATES = VAULT_TEMPLATES
    VAULT_JOURNAL = VAULT_ROOT / "journal"
    VAULT_GOALS = VAULT_ROOT / "goals"
    VAULT_WEEKLY = VAULT_WEEKLY
    VAULT_DAILY = VAULT_DAILY
    VAULT_PROGRESS = VAULT_PROGRESS
    VAULT_READINGS = VAULT_ROOT / "readings"
    VAULT_INSTRUCTIONS = VAULT_ROOT / ".obsidian/VAULT_INSTRUCTIONS.md"

    # Agent directories
    DAILY_BRIEF_AGENT = AGENTS_ROOT / "daily_brief"
    LIBRARIAN_AGENT = AGENTS_ROOT / "librarian"
    FOCUS_AGENT = AGENTS_ROOT / "focus_guardrails"
    BOOT_HARDENING_AGENT = AGENTS_ROOT / "boot_hardening"

    # Workflow directories
    LANGFLOW_FLOWS = LANGFLOW_FLOWS
    N8N_WORKFLOWS = N8N_WORKFLOWS

    # Integration directories
    INTEGRATIONS = OSMEN_ROOT / "integrations"
    GATEWAY = OSMEN_ROOT / "gateway"

    # Log directories (re-export)
    LOG_SESSIONS = LOG_AGENT_SESSIONS
    LOG_CHECKINS = LOG_CHECK_INS
    LOG_AUDIO = LOG_AUDIO_GENERATIONS
    LOG_EVENTS = LOG_SYSTEM_EVENTS

    # Template files (re-export)
    TEMPLATE_AM = TEMPLATE_AM_CHECKIN
    TEMPLATE_PM = TEMPLATE_PM_CHECKIN
    TEMPLATE_WEEKLY = TEMPLATE_WEEKLY_REVIEW
    TEMPLATE_DAILY = TEMPLATE_DAILY_NOTE
    TEMPLATE_BRIEFING = TEMPLATE_BRIEFING
    TEMPLATE_PODCAST = TEMPLATE_PODCAST

    # Tracker files (re-export)
    TRACKER_PROGRESS = TRACKER_PROGRESS
    TRACKER_READINGS = TRACKER_READINGS
    TRACKER_METRICS = TRACKER_METRICS

    # Instruction files
    GITHUB_AGENTS = OSMEN_ROOT / ".github/agents"
    COPILOT_INSTRUCTIONS = OSMEN_ROOT / ".github/copilot-instructions.md"

    @classmethod
    def ensure_all(cls):
        """Create all directories if they don't exist"""
        dirs = [
            cls.LOGS_ROOT,
            cls.LOG_SESSIONS,
            cls.LOG_CHECKINS,
            cls.LOG_AUDIO,
            cls.LOG_EVENTS,
            cls.HB411_BRIEFINGS,
            cls.HB411_BRIEFING_SCRIPTS,
            cls.VAULT_JOURNAL / "daily",
            cls.VAULT_JOURNAL / "weekly",
            cls.VAULT_GOALS,
            cls.VAULT_READINGS,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)


# =============================================================================
# SERVICE REGISTRY - All OsMEN services
# =============================================================================


class ServiceStatus(Enum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


@dataclass
class Service:
    """Service definition"""

    name: str
    port: int
    health_endpoint: Optional[str] = None
    description: str = ""
    required: bool = True
    status: ServiceStatus = ServiceStatus.UNKNOWN

    @property
    def url(self) -> str:
        return f"http://localhost:{self.port}"

    @property
    def health_url(self) -> Optional[str]:
        if self.health_endpoint:
            return f"{self.url}{self.health_endpoint}"
        return None


class Services:
    """Registry of all OsMEN services"""

    LANGFLOW = Service("langflow", 7860, None, "Visual LLM flow builder")
    N8N = Service("n8n", 5678, None, "Workflow automation")
    GATEWAY = Service("gateway", 8080, "/health", "FastAPI agent hub")
    MCP_SERVER = Service("mcp-server", 8081, None, "Model Context Protocol")
    QDRANT = Service("qdrant", 6333, "/health", "Vector database")
    CHROMADB = Service("chromadb", 8100, None, "Local vector database")
    POSTGRES = Service("postgres", 5432, None, "Persistent storage")
    REDIS = Service("redis", 6379, None, "Caching")
    CONVERTX = Service("convertx", 3000, None, "File conversion")
    LIBRARIAN = Service("librarian", 8200, None, "RAG search", required=False)

    ALL = [
        LANGFLOW,
        N8N,
        GATEWAY,
        MCP_SERVER,
        QDRANT,
        CHROMADB,
        POSTGRES,
        REDIS,
        CONVERTX,
        LIBRARIAN,
    ]

    @classmethod
    def get(cls, name: str) -> Optional[Service]:
        for svc in cls.ALL:
            if svc.name == name:
                return svc
        return None


# =============================================================================
# PIPELINE REGISTRY - All processing pipelines
# =============================================================================


class PipelineType(Enum):
    CHECKIN = "checkin"
    BRIEFING = "briefing"
    PODCAST = "podcast"
    RAG = "rag"
    AUDIO = "audio"
    PROGRESS = "progress"
    MEDITATION = "meditation"
    ADHD = "adhd"


@dataclass
class Pipeline:
    """Pipeline definition with all entry points and dependencies"""

    name: str
    type: PipelineType
    description: str

    # Entry points - multiple ways to trigger this pipeline
    cli_command: Optional[str] = None
    n8n_workflow: Optional[str] = None
    langflow_flow: Optional[str] = None
    python_module: Optional[str] = None
    webhook_path: Optional[str] = None

    # Dependencies
    required_services: List[str] = field(default_factory=list)
    required_files: List[str] = field(default_factory=list)

    # Outputs
    output_paths: List[str] = field(default_factory=list)

    # Logging
    log_category: str = "system_events"

    def validate(self) -> tuple[bool, List[str]]:
        """Validate pipeline can run"""
        errors = []
        for f in self.required_files:
            if not Path(f).exists():
                errors.append(f"Missing file: {f}")
        return len(errors) == 0, errors


class Pipelines:
    """Registry of all OsMEN pipelines"""

    AM_CHECKIN = Pipeline(
        name="am_checkin",
        type=PipelineType.CHECKIN,
        description="Morning check-in: energy, priorities, ADHD, meditation, course status",
        cli_command="osmen checkin am",
        n8n_workflow="checkin_reminder.json",
        python_module="agents.daily_brief.checkin_handler",
        webhook_path="/api/checkin/am",
        required_services=["gateway"],
        required_files=[str(Paths.VAULT_TEMPLATES / "AM Check-In Template.md")],
        output_paths=[str(Paths.VAULT_JOURNAL / "daily")],
        log_category="check_ins",
    )

    PM_CHECKIN = Pipeline(
        name="pm_checkin",
        type=PipelineType.CHECKIN,
        description="Evening check-in: review, reflection, tomorrow planning",
        cli_command="osmen checkin pm",
        n8n_workflow="checkin_reminder.json",
        python_module="agents.daily_brief.checkin_handler",
        webhook_path="/api/checkin/pm",
        required_services=["gateway"],
        required_files=[str(Paths.VAULT_TEMPLATES / "PM Check-In Template.md")],
        output_paths=[str(Paths.VAULT_JOURNAL / "daily")],
        log_category="check_ins",
    )

    DAILY_BRIEFING = Pipeline(
        name="daily_briefing",
        type=PipelineType.BRIEFING,
        description="Generate 90-second personalized audio briefing from check-in data",
        cli_command="osmen briefing generate",
        n8n_workflow="checkin_triggered_briefing.json",
        langflow_flow="daily_brief_specialist.json",
        python_module="agents.daily_brief.daily_briefing_generator",
        webhook_path="/api/briefing/generate",
        required_services=["gateway", "chromadb"],
        required_files=[
            str(Paths.VAULT_TEMPLATES / "Daily Briefing Script Template.md"),
        ],
        output_paths=[
            str(Paths.HB411_BRIEFINGS),
            str(Paths.HB411_BRIEFING_SCRIPTS),
        ],
        log_category="audio_generations",
    )

    WEEKLY_PODCAST = Pipeline(
        name="weekly_podcast",
        type=PipelineType.PODCAST,
        description="Generate 20-minute weekly course podcast",
        cli_command="osmen podcast generate",
        n8n_workflow="hb411_weekly_podcast.json",
        langflow_flow="hb411_podcast_specialist.json",
        python_module="scripts.generate_podcast_scripts",
        required_services=["gateway", "chromadb"],
        required_files=[],
        output_paths=[
            str(Paths.HB411_PODCASTS),
            str(Paths.HB411_PODCAST_SCRIPTS),
        ],
        log_category="audio_generations",
    )

    RAG_QUERY = Pipeline(
        name="rag_query",
        type=PipelineType.RAG,
        description="Query course content via ChromaDB RAG",
        cli_command="osmen librarian search",
        python_module="integrations.rag_pipeline",
        webhook_path="/api/rag/query",
        required_services=["chromadb", "gateway"],
        log_category="system_events",
    )

    COURSE_PROGRESS = Pipeline(
        name="course_progress",
        type=PipelineType.PROGRESS,
        description="Track HB411 course progress",
        cli_command="osmen progress hb411",
        python_module="agents.daily_brief.progress_tracker",
        required_files=[str(Paths.VAULT_GOALS / "hb411_progress.md")],
        output_paths=[str(Paths.VAULT_GOALS)],
        log_category="system_events",
    )

    ADHD_TRACKING = Pipeline(
        name="adhd_tracking",
        type=PipelineType.ADHD,
        description="ADHD executive functioning tracking and analysis",
        cli_command="osmen progress adhd",
        python_module="agents.daily_brief.adhd_tracker",
        required_files=[str(Paths.VAULT_GOALS / "adhd_dashboard.md")],
        output_paths=[str(Paths.VAULT_GOALS)],
        log_category="system_events",
    )

    MEDITATION_LOG = Pipeline(
        name="meditation_log",
        type=PipelineType.MEDITATION,
        description="Vajrayana meditation practice tracking",
        cli_command="osmen progress meditation",
        python_module="agents.daily_brief.meditation_tracker",
        required_files=[str(Paths.VAULT_GOALS / "meditation_log.md")],
        output_paths=[str(Paths.VAULT_GOALS)],
        log_category="system_events",
    )

    ALL = [
        AM_CHECKIN,
        PM_CHECKIN,
        DAILY_BRIEFING,
        WEEKLY_PODCAST,
        RAG_QUERY,
        COURSE_PROGRESS,
        ADHD_TRACKING,
        MEDITATION_LOG,
    ]

    # Registry dict for iteration - auto-generated from ALL
    _registry = {}

    @classmethod
    def _build_registry(cls):
        """Build registry from ALL list"""
        cls._registry = {p.name: p for p in cls.ALL}

    @classmethod
    def get(cls, name: str) -> Optional[Pipeline]:
        if not cls._registry:
            cls._build_registry()
        return cls._registry.get(name)

    @classmethod
    def by_type(cls, ptype: PipelineType) -> List[Pipeline]:
        return [p for p in cls.ALL if p.type == ptype]

    @classmethod
    def get_agents(cls, pipeline_name: str) -> List["Agent"]:
        """Get all agents that handle this pipeline (Pipeline → Agent binding)"""
        return Agents.for_pipeline(pipeline_name)

    @classmethod
    def get_workflows(cls, pipeline_name: str) -> List["Workflow"]:
        """Get all workflows for this pipeline (Pipeline → Workflow binding)"""
        return Workflows.for_pipeline(pipeline_name)

    @classmethod
    def get_templates(cls, pipeline_name: str) -> List["Template"]:
        """Get all templates used by this pipeline (Pipeline → Template binding)"""
        return [t for t in Templates.ALL if t.pipeline == pipeline_name]

    @classmethod
    def get_trackers(cls, pipeline_name: str) -> List["Tracker"]:
        """Get trackers that sync with this pipeline"""
        # Map pipeline types to trackers
        pipeline = cls.get(pipeline_name)
        if not pipeline:
            return []
        type_tracker_map = {
            PipelineType.ADHD: ["adhd_dashboard", "time_tracker"],
            PipelineType.MEDITATION: ["meditation_log"],
            PipelineType.PROGRESS: ["hb411_progress"],
            PipelineType.CHECKIN: ["adhd_dashboard", "hb411_progress"],
        }
        tracker_names = type_tracker_map.get(pipeline.type, [])
        return [t for t in Trackers.ALL if t.name in tracker_names]


# Build registry on module load
Pipelines._build_registry()


# =============================================================================
# AGENT REGISTRY - All OsMEN agents
# =============================================================================


@dataclass
class Agent:
    """Agent definition"""

    name: str
    path: str
    description: str
    instruction_file: Optional[str] = None
    pipelines: List[str] = field(default_factory=list)
    status: str = "operational"

    @property
    def module(self) -> str:
        return self.path.replace("/", ".").replace("\\", ".")


class Agents:
    """Registry of all OsMEN agents"""

    DAILY_BRIEF = Agent(
        name="daily_brief",
        path="agents/daily_brief",
        description="Morning briefings, check-ins, progress tracking",
        instruction_file=".github/agents/osmen-dev.agent.md",
        pipelines=["am_checkin", "pm_checkin", "daily_briefing", "course_progress"],
        status="operational",
    )

    LIBRARIAN = Agent(
        name="librarian",
        path="agents/librarian",
        description="RAG search, document ingestion, semantic queries",
        pipelines=["rag_query"],
        status="operational",
    )

    FOCUS_GUARDRAILS = Agent(
        name="focus_guardrails",
        path="agents/focus_guardrails",
        description="Pomodoro, distraction blocking, time tracking",
        pipelines=["adhd_tracking"],
        status="operational",
    )

    BOOT_HARDENING = Agent(
        name="boot_hardening",
        path="agents/boot_hardening",
        description="Security, firewall, system hardening",
        status="operational",
    )

    KNOWLEDGE_MANAGEMENT = Agent(
        name="knowledge_management",
        path="agents/knowledge_management",
        description="Obsidian integration, note management",
        status="development",
    )

    ALL = [
        DAILY_BRIEF,
        LIBRARIAN,
        FOCUS_GUARDRAILS,
        BOOT_HARDENING,
        KNOWLEDGE_MANAGEMENT,
    ]

    # Registry for fast lookups
    _registry: Dict[str, "Agent"] = {}
    _pipeline_map: Dict[str, List["Agent"]] = {}  # pipeline_name -> [agents]

    @classmethod
    def _build_registry(cls):
        """Build lookup registries for agents"""
        cls._registry = {a.name: a for a in cls.ALL}
        cls._pipeline_map = {}
        for agent in cls.ALL:
            for pipeline_name in agent.pipelines:
                if pipeline_name not in cls._pipeline_map:
                    cls._pipeline_map[pipeline_name] = []
                cls._pipeline_map[pipeline_name].append(agent)

    @classmethod
    def get(cls, name: str) -> Optional["Agent"]:
        """Get agent by name"""
        if not cls._registry:
            cls._build_registry()
        return cls._registry.get(name)

    @classmethod
    def for_pipeline(cls, pipeline_name: str) -> List["Agent"]:
        """Get all agents that handle a specific pipeline (Agent → Pipeline binding)"""
        if not cls._pipeline_map:
            cls._build_registry()
        return cls._pipeline_map.get(pipeline_name, [])

    @classmethod
    def get_pipelines(cls, agent_name: str) -> List["Pipeline"]:
        """Get all pipelines an agent handles (Pipeline → Agent binding)"""
        agent = cls.get(agent_name)
        if not agent:
            return []
        return [Pipelines.get(p) for p in agent.pipelines if Pipelines.get(p)]

    @classmethod
    def get_workflows(cls, agent_name: str) -> List["Workflow"]:
        """Get all workflows associated with an agent's pipelines"""
        pipelines = cls.get_pipelines(agent_name)
        workflows = []
        for pipeline in pipelines:
            workflows.extend(Workflows.for_pipeline(pipeline.name))
        return workflows

    @classmethod
    def get_templates(cls, agent_name: str) -> List["Template"]:
        """Get all templates used by an agent's pipelines"""
        pipelines = cls.get_pipelines(agent_name)
        templates = []
        for pipeline in pipelines:
            for template in Templates.ALL:
                if template.pipeline == pipeline.name:
                    templates.append(template)
        return templates


# Build agent registry on module load
Agents._build_registry()


# =============================================================================
# WORKFLOW REGISTRY - n8n and Langflow workflows
# =============================================================================


@dataclass
class Workflow:
    """Workflow definition"""

    name: str
    file: str
    system: str  # "n8n" or "langflow"
    trigger: str
    description: str
    pipeline: Optional[str] = None
    active: bool = True


class Workflows:
    """Registry of all workflows"""

    N8N = [
        Workflow(
            "checkin_triggered_briefing",
            "checkin_triggered_briefing.json",
            "n8n",
            "POST /webhook/checkin-complete",
            "Generate briefing on AM check-in",
            "daily_briefing",
            True,
        ),
        Workflow(
            "hb411_weekly_podcast",
            "hb411_weekly_podcast.json",
            "n8n",
            "Cron: Sunday 6PM",
            "Generate weekly podcast",
            "weekly_podcast",
            True,
        ),
        Workflow(
            "daily_90sec_briefing",
            "daily_90sec_briefing.json",
            "n8n",
            "Cron: Daily 7AM",
            "Adaptive daily briefing",
            "daily_briefing",
            True,
        ),
    ]

    LANGFLOW = [
        Workflow(
            "daily_brief_specialist",
            "daily_brief_specialist.json",
            "langflow",
            "API call",
            "Process check-ins, generate briefing script",
            "daily_briefing",
            True,
        ),
        Workflow(
            "hb411_podcast_specialist",
            "hb411_podcast_specialist.json",
            "langflow",
            "API call",
            "Generate podcast scripts from RAG",
            "weekly_podcast",
            True,
        ),
    ]

    ALL = N8N + LANGFLOW

    @classmethod
    def get(cls, name: str) -> Optional[Workflow]:
        for w in cls.ALL:
            if w.name == name:
                return w
        return None

    @classmethod
    def for_pipeline(cls, pipeline_name: str) -> List[Workflow]:
        """Get workflows for a pipeline (Workflow → Pipeline binding)"""
        return [w for w in cls.ALL if w.pipeline == pipeline_name]

    @classmethod
    def by_system(cls, system: str) -> List[Workflow]:
        """Get workflows by system (n8n or langflow)"""
        return [w for w in cls.ALL if w.system == system]

    @classmethod
    def get_pipeline(cls, workflow_name: str) -> Optional["Pipeline"]:
        """Get the pipeline this workflow serves (Workflow → Pipeline binding)"""
        workflow = cls.get(workflow_name)
        if workflow and workflow.pipeline:
            return Pipelines.get(workflow.pipeline)
        return None

    @classmethod
    def get_agents(cls, workflow_name: str) -> List["Agent"]:
        """Get agents that handle this workflow's pipeline"""
        pipeline = cls.get_pipeline(workflow_name)
        if pipeline:
            return Agents.for_pipeline(pipeline.name)
        return []


# =============================================================================
# TEMPLATE REGISTRY - Obsidian templates
# =============================================================================


@dataclass
class Template:
    """Template definition"""

    name: str
    file: str
    purpose: str
    pipeline: Optional[str] = None
    variables: List[str] = field(default_factory=list)


class Templates:
    """Registry of all Obsidian templates"""

    AM_CHECKIN = Template(
        "AM Check-In",
        "AM Check-In Template.md",
        "Morning check-in with ADHD, meditation, course sections",
        "am_checkin",
        ["date", "time", "energy", "focus", "priorities", "meditation_planned"],
    )

    PM_CHECKIN = Template(
        "PM Check-In",
        "PM Check-In Template.md",
        "Evening reflection with productivity review",
        "pm_checkin",
        ["date", "time", "productivity_rate", "mood", "carryover"],
    )

    DAILY_NOTE = Template(
        "Daily Note",
        "Daily Note Template.md",
        "Daily journal and task tracking",
        None,
        ["date", "day_of_week", "energy", "tasks"],
    )

    WEEKLY_REVIEW = Template(
        "Weekly Review",
        "Weekly Review Template.md",
        "Weekly progress review and planning",
        None,
        ["week_number", "wins", "challenges", "next_week"],
    )

    BRIEFING_SCRIPT = Template(
        "Briefing Script",
        "Daily Briefing Script Template.md",
        "90-sec audio script generation template",
        "daily_briefing",
        ["am_energy", "priorities", "adhd_tip", "boundary_reminder", "course_week"],
    )

    # Alias for backward compatibility
    DAILY_BRIEFING = BRIEFING_SCRIPT

    PODCAST_SCRIPT = Template(
        "Podcast Script",
        "Podcast Script Template.md",
        "20-minute weekly podcast script template",
        "weekly_podcast",
        ["week_number", "topic", "outline", "rag_context"],
    )

    WEEKLY_NOTE = Template(
        "Weekly Note",
        "Weekly Note Template.md",
        "Course weekly notes and study guide",
        None,
        ["week_number", "topic", "readings", "themes"],
    )

    READING_NOTE = Template(
        "Reading Note",
        "Reading Note Template.md",
        "Book/chapter reading notes",
        None,
        ["title", "author", "chroma_doc_ids"],
    )

    JOURNAL_ENTRY = Template(
        "Journal Entry",
        "Journal Entry Template.md",
        "General journal entries",
        None,
        ["date", "mood", "reflection"],
    )

    ALL = [
        AM_CHECKIN,
        PM_CHECKIN,
        DAILY_NOTE,
        WEEKLY_REVIEW,
        BRIEFING_SCRIPT,
        PODCAST_SCRIPT,
        WEEKLY_NOTE,
        READING_NOTE,
        JOURNAL_ENTRY,
    ]

    @classmethod
    def get(cls, name: str) -> Optional[Template]:
        for t in cls.ALL:
            if t.name == name:
                return t
        return None

    @classmethod
    def for_pipeline(cls, pipeline_name: str) -> List["Template"]:
        """Get templates for a pipeline (Template → Pipeline binding)"""
        return [t for t in cls.ALL if t.pipeline == pipeline_name]

    @classmethod
    def get_pipeline(cls, template_name: str) -> Optional["Pipeline"]:
        """Get the pipeline this template serves (Template → Pipeline binding)"""
        template = cls.get(template_name)
        if template and template.pipeline:
            return Pipelines.get(template.pipeline)
        return None

    @classmethod
    def get_agents(cls, template_name: str) -> List["Agent"]:
        """Get agents that use this template's pipeline"""
        pipeline = cls.get_pipeline(template_name)
        if pipeline:
            return Agents.for_pipeline(pipeline.name)
        return []

    @classmethod
    def get_full_path(cls, template_name: str) -> Optional[Path]:
        """Get the full filesystem path to a template"""
        template = cls.get(template_name)
        if template:
            return Paths.VAULT_TEMPLATES / template.file
        return None


# =============================================================================
# TRACKER REGISTRY - Live goal trackers
# =============================================================================


@dataclass
@dataclass(frozen=True)
class Tracker:
    """Live tracker definition"""

    name: str
    file: str
    purpose: str
    sync_targets: tuple = field(default_factory=tuple)  # Tuple for hashability
    update_frequency: str = "daily"


class Trackers:
    """Registry of live trackers"""

    ADHD_DASHBOARD = Tracker(
        "adhd_dashboard",
        "goals/adhd_dashboard.md",
        "ADHD executive functioning patterns and strategies",
        ("chromadb", "gateway_api"),
        "daily",
    )

    MEDITATION_LOG = Tracker(
        "meditation_log",
        "goals/meditation_log.md",
        "Trekchö & Tummo practice tracking",
        ("chromadb", "gateway_api"),
        "daily",
    )

    HB411_PROGRESS = Tracker(
        "hb411_progress",
        "goals/hb411_progress.md",
        "Course readings, assignments, weekly status",
        ("chromadb", "gateway_api"),
        "daily",
    )

    TIME_TRACKER = Tracker(
        "time_tracker",
        "goals/time_tracker.md",
        "Pomodoros, deep work, time audits",
        ("chromadb", "gateway_api"),
        "hourly",
    )

    ALL = [ADHD_DASHBOARD, MEDITATION_LOG, HB411_PROGRESS, TIME_TRACKER]

    @classmethod
    def get(cls, name: str) -> Optional["Tracker"]:
        """Get tracker by name"""
        for t in cls.ALL:
            if t.name == name:
                return t
        return None

    @classmethod
    def for_pipeline(cls, pipeline_name: str) -> List["Tracker"]:
        """Get trackers associated with a pipeline type"""
        return Pipelines.get_trackers(pipeline_name)


# =============================================================================
# CONNECTION GRAPH - Bidirectional relationship traversal
# =============================================================================


class ConnectionGraph:
    """
    Provides bidirectional traversal across all OsMEN components.

    This class enables navigation in ANY direction:
    - Agent → Pipelines → Workflows → Templates → Trackers
    - Template → Pipeline → Agent
    - Workflow → Pipeline → Agent
    - Any component → All related components

    Usage:
        from integrations.orchestration import ConnectionGraph

        # Get everything related to an agent
        graph = ConnectionGraph.for_agent("daily_brief")
        print(graph.pipelines)   # All pipelines
        print(graph.workflows)   # All workflows
        print(graph.templates)   # All templates

        # Get everything related to a pipeline
        graph = ConnectionGraph.for_pipeline("daily_briefing")
        print(graph.agents)      # Agents handling this
        print(graph.workflows)   # n8n + langflow workflows
        print(graph.templates)   # Obsidian templates
    """

    def __init__(self):
        self.agents: List[Agent] = []
        self.pipelines: List[Pipeline] = []
        self.workflows: List[Workflow] = []
        self.templates: List[Template] = []
        self.trackers: List[Tracker] = []
        self.services: List[Service] = []

    @classmethod
    def for_agent(cls, agent_name: str) -> "ConnectionGraph":
        """Build connection graph starting from an agent"""
        graph = cls()
        agent = Agents.get(agent_name)
        if not agent:
            return graph

        graph.agents = [agent]
        graph.pipelines = Agents.get_pipelines(agent_name)
        graph.workflows = Agents.get_workflows(agent_name)
        graph.templates = Agents.get_templates(agent_name)

        # Collect services from pipelines
        service_names = set()
        for pipeline in graph.pipelines:
            service_names.update(pipeline.required_services)
        graph.services = [s for s in Services.ALL if s.name in service_names]

        # Collect trackers
        for pipeline in graph.pipelines:
            graph.trackers.extend(Pipelines.get_trackers(pipeline.name))
        graph.trackers = list(set(graph.trackers))  # Dedupe

        return graph

    @classmethod
    def for_pipeline(cls, pipeline_name: str) -> "ConnectionGraph":
        """Build connection graph starting from a pipeline"""
        graph = cls()
        pipeline = Pipelines.get(pipeline_name)
        if not pipeline:
            return graph

        graph.pipelines = [pipeline]
        graph.agents = Pipelines.get_agents(pipeline_name)
        graph.workflows = Pipelines.get_workflows(pipeline_name)
        graph.templates = Pipelines.get_templates(pipeline_name)
        graph.trackers = Pipelines.get_trackers(pipeline_name)

        # Get required services
        graph.services = [
            s for s in Services.ALL if s.name in pipeline.required_services
        ]

        return graph

    @classmethod
    def for_workflow(cls, workflow_name: str) -> "ConnectionGraph":
        """Build connection graph starting from a workflow"""
        graph = cls()
        workflow = Workflows.get(workflow_name)
        if not workflow:
            return graph

        graph.workflows = [workflow]
        pipeline = Workflows.get_pipeline(workflow_name)
        if pipeline:
            graph.pipelines = [pipeline]
            graph.agents = Agents.for_pipeline(pipeline.name)
            graph.templates = Templates.for_pipeline(pipeline.name)
            graph.trackers = Pipelines.get_trackers(pipeline.name)
            graph.services = [
                s for s in Services.ALL if s.name in pipeline.required_services
            ]

        return graph

    @classmethod
    def for_template(cls, template_name: str) -> "ConnectionGraph":
        """Build connection graph starting from a template"""
        graph = cls()
        template = Templates.get(template_name)
        if not template:
            return graph

        graph.templates = [template]
        pipeline = Templates.get_pipeline(template_name)
        if pipeline:
            graph.pipelines = [pipeline]
            graph.agents = Agents.for_pipeline(pipeline.name)
            graph.workflows = Workflows.for_pipeline(pipeline.name)
            graph.services = [
                s for s in Services.ALL if s.name in pipeline.required_services
            ]

        return graph

    def to_dict(self) -> Dict:
        """Export graph as dictionary"""
        return {
            "agents": [a.name for a in self.agents],
            "pipelines": [p.name for p in self.pipelines],
            "workflows": [w.name for w in self.workflows],
            "templates": [t.name for t in self.templates],
            "trackers": [t.name for t in self.trackers],
            "services": [s.name for s in self.services],
        }

    def __repr__(self) -> str:
        return (
            f"ConnectionGraph(agents={len(self.agents)}, pipelines={len(self.pipelines)}, "
            f"workflows={len(self.workflows)}, templates={len(self.templates)}, "
            f"trackers={len(self.trackers)}, services={len(self.services)})"
        )


# =============================================================================
# OSMEN MASTER CLASS - Central orchestration point
# =============================================================================


class OsMEN:
    """
    Master orchestration class - the single entry point for all OsMEN operations.

    Usage:
        from integrations.orchestration import OsMEN

        # Initialize (ensures all paths exist)
        OsMEN.initialize()

        # Get system state
        state = OsMEN.get_state()

        # Execute a pipeline
        result = OsMEN.execute("daily_briefing")

        # Get configuration for any component
        config = OsMEN.config
    """

    # Static configuration
    paths = Paths
    services = Services
    pipelines = Pipelines
    agents = Agents
    workflows = Workflows
    templates = Templates
    trackers = Trackers

    # Runtime state
    _initialized = False
    _state_file = Paths.OSMEN_ROOT / ".osmen_state.json"

    @classmethod
    def initialize(cls):
        """Initialize OsMEN - ensure all paths exist and state is loaded"""
        if cls._initialized:
            return

        # Ensure all directories exist
        Paths.ensure_all()

        # Load or create state
        cls._load_state()

        cls._initialized = True

    @classmethod
    def _load_state(cls):
        """Load persistent state"""
        if cls._state_file.exists():
            with open(cls._state_file) as f:
                return json.load(f)
        return {"last_initialized": None, "sessions": []}

    @classmethod
    def _save_state(cls, state: Dict):
        """Save persistent state"""
        with open(cls._state_file, "w") as f:
            json.dump(state, f, indent=2, default=str)

    @classmethod
    def get_state(cls) -> Dict:
        """Get current system state"""
        from integrations.logging_system import CheckInTracker, get_recent_context

        tracker = CheckInTracker()
        context = get_recent_context(days=3)

        return {
            "timestamp": datetime.now().isoformat(),
            "date": date.today().isoformat(),
            "initialized": cls._initialized,
            "checkin_status": tracker.get_status(),
            "recent_context": context,
            "services": {s.name: s.status.value for s in Services.ALL},
            "pipelines": {p.name: p.type.value for p in Pipelines.ALL},
            "agents": {a.name: a.status for a in Agents.ALL},
        }

    @classmethod
    def get_pipeline(cls, name: str) -> Optional[Pipeline]:
        """Get a pipeline by name"""
        return Pipelines.get(name)

    @classmethod
    def execute(cls, pipeline_name: str, **kwargs) -> Dict:
        """
        Execute a pipeline by name.
        This is the unified entry point for all pipeline executions.
        """
        from integrations.logging_system import AgentLogger, SystemEventLog

        pipeline = cls.get_pipeline(pipeline_name)
        if not pipeline:
            return {"error": f"Unknown pipeline: {pipeline_name}"}

        # Validate
        valid, errors = pipeline.validate()
        if not valid:
            return {"error": "Validation failed", "details": errors}

        # Log start
        logger = AgentLogger(f"pipeline-{pipeline_name}")
        logger.log(
            action="pipeline_start",
            inputs={"pipeline": pipeline_name, "kwargs": kwargs},
            outputs={},
            status="started",
        )

        try:
            # Execute based on pipeline type
            if pipeline.python_module:
                import importlib

                module = importlib.import_module(pipeline.python_module)
                if hasattr(module, "main"):
                    result = module.main(**kwargs)
                elif hasattr(module, "run"):
                    result = module.run(**kwargs)
                else:
                    result = {
                        "status": "module_loaded",
                        "module": pipeline.python_module,
                    }
            else:
                result = {"status": "no_executor", "pipeline": pipeline_name}

            logger.log(
                action="pipeline_complete",
                inputs={},
                outputs=result if isinstance(result, dict) else {"result": str(result)},
                status="completed",
            )

            return result

        except Exception as e:
            logger.log(
                action="pipeline_error",
                inputs={},
                outputs={"error": str(e)},
                status="error",
                level="error",
            )
            return {"error": str(e)}

        finally:
            logger.end_session(f"Pipeline {pipeline_name} execution")

    @classmethod
    def get_instruction_context(cls) -> str:
        """
        Generate instruction context for agents.
        This ensures all agents have consistent knowledge of the system.
        """
        return f"""
# OsMEN System Context

## Paths
- OSMEN_ROOT: {Paths.OSMEN_ROOT}
- HB411_ROOT: {Paths.HB411_ROOT}
- OBSIDIAN_ROOT: {Paths.HB411_OBSIDIAN}
- LOGS_ROOT: {Paths.LOGS_ROOT}

## Active Pipelines
{chr(10).join(f'- {p.name}: {p.description}' for p in Pipelines.ALL)}

## Active Agents
{chr(10).join(f'- {a.name}: {a.description} ({a.status})' for a in Agents.ALL)}

## Key Files
- Vault Instructions: {Paths.VAULT_INSTRUCTIONS}
- Copilot Instructions: {Paths.COPILOT_INSTRUCTIONS}
- Agent Definitions: {Paths.GITHUB_AGENTS}

## Check-In System
- AM Check-In: Complete by 9 AM, triggers daily briefing
- PM Check-In: Complete by 10 PM, feeds next day's briefing
- Briefing Generation: Automated after AM check-in

## Logging
All actions logged to {Paths.LOGS_ROOT}:
- agent_sessions/: Per-session logs
- check_ins/: Daily check-in status
- audio_generations/: Briefing/podcast logs
- system_events/: System events
"""


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def get_pipeline(name: str) -> Optional[Pipeline]:
    """Get a pipeline by name"""
    return OsMEN.get_pipeline(name)


def execute_pipeline(name: str, **kwargs) -> Dict:
    """Execute a pipeline by name"""
    return OsMEN.execute(name, **kwargs)


def get_state() -> Dict:
    """Get current system state"""
    return OsMEN.get_state()


def initialize():
    """Initialize OsMEN"""
    OsMEN.initialize()


# Initialize on import
initialize()


if __name__ == "__main__":
    print("OsMEN Unified Orchestration Layer")
    print("=" * 60)

    # Show all pipelines
    print("\n📋 PIPELINES:")
    for p in Pipelines.ALL:
        print(f"  • {p.name}: {p.description}")
        if p.cli_command:
            print(f"    CLI: {p.cli_command}")
        if p.n8n_workflow:
            print(f"    n8n: {p.n8n_workflow}")

    # Show all agents
    print("\n🤖 AGENTS:")
    for a in Agents.ALL:
        print(f"  • {a.name}: {a.description} [{a.status}]")

    # Show state
    print("\n📊 SYSTEM STATE:")
    state = get_state()
    print(f"  Date: {state['date']}")
    print(
        f"  Check-in: AM={state['checkin_status']['am_completed']}, PM={state['checkin_status']['pm_completed']}"
    )
