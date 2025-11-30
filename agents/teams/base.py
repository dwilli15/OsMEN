"""
Base types and data structures for Agent Teams.

Provides:
- TeamRole: Defines an agent's role within a team
- TeamState: Shared state for team coordination (LangGraph pattern)
- TeamConfig: Configuration for team behavior
- TeamResult: Container for team execution results
- TeamStatus: Execution status enum
- AgentCapability: What an agent can do
"""

from typing import (
    TypedDict, Annotated, List, Dict, Any, Optional, Literal, Callable
)
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import operator
import uuid


class TeamStatus(Enum):
    """Status of a team execution."""
    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentCapability(Enum):
    """What an agent can do."""
    RESEARCH = "research"
    RETRIEVAL = "retrieval"
    GENERATION = "generation"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    EXECUTION = "execution"
    MONITORING = "monitoring"
    COMMUNICATION = "communication"
    PERSISTENCE = "persistence"
    MEDIA_PROCESSING = "media_processing"


@dataclass
class TeamRole:
    """
    Defines an agent's role within a team.
    
    Attributes:
        agent_type: Type of agent (maps to agents/ directory)
        role: Role within the team (lead, researcher, writer, reviewer, etc.)
        capabilities: What this agent can do
        priority: Execution priority (higher = executes first)
        required: Whether this role is required for team to function
        config: Additional configuration for this role
    """
    agent_type: str
    role: Literal["lead", "researcher", "analyst", "writer", "reviewer", "executor", "monitor"]
    capabilities: List[AgentCapability] = field(default_factory=list)
    priority: int = 0
    required: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # Set default capabilities based on agent type
        if not self.capabilities:
            capability_map = {
                "research_intel": [AgentCapability.RESEARCH, AgentCapability.ANALYSIS],
                "librarian": [AgentCapability.RETRIEVAL, AgentCapability.SYNTHESIS],
                "content_creator": [AgentCapability.GENERATION, AgentCapability.MEDIA_PROCESSING],
                "daily_brief": [AgentCapability.MONITORING, AgentCapability.SYNTHESIS],
                "personal_assistant": [AgentCapability.PERSISTENCE, AgentCapability.COMMUNICATION],
                "security_ops": [AgentCapability.MONITORING, AgentCapability.ANALYSIS],
                "knowledge_management": [AgentCapability.PERSISTENCE, AgentCapability.RETRIEVAL],
            }
            self.capabilities = capability_map.get(self.agent_type, [])


class TeamState(TypedDict):
    """
    Shared state for team coordination.
    
    Uses LangGraph pattern with annotated fields for accumulation.
    
    Fields:
        task_id: Unique task identifier
        task: Current task description
        status: Current execution status
        messages: Communication history between agents (accumulated)
        artifacts: Produced artifacts/results (accumulated)
        current_agent: Which agent is currently active
        agent_outputs: Individual agent outputs (accumulated)
        context: Shared context data
        plan: Execution plan steps
        current_step: Current step in plan
        errors: Any errors encountered (accumulated)
        metadata: Additional metadata
    """
    task_id: str
    task: str
    status: str  # TeamStatus value
    messages: Annotated[List[Dict[str, Any]], operator.add]
    artifacts: Annotated[List[Dict[str, Any]], operator.add]
    current_agent: Optional[str]
    agent_outputs: Annotated[Dict[str, Any], lambda x, y: {**x, **y}]
    context: Dict[str, Any]
    plan: List[Dict[str, Any]]
    current_step: int
    errors: Annotated[List[str], operator.add]
    metadata: Dict[str, Any]


@dataclass
class TeamConfig:
    """
    Configuration for team behavior.
    
    Attributes:
        name: Team name
        description: What this team does
        max_iterations: Maximum execution iterations
        timeout_seconds: Execution timeout
        parallel_execution: Whether agents can run in parallel
        require_approval: Whether to require human approval at checkpoints
        checkpoint_steps: Steps where to checkpoint state
        error_handling: How to handle errors (continue, stop, retry)
        llm_provider: Which LLM provider to use
        llm_model: Which model to use
        trace_enabled: Whether to enable LangSmith tracing
        metadata: Additional configuration
    """
    name: str
    description: str = ""
    max_iterations: int = 10
    timeout_seconds: float = 300.0
    parallel_execution: bool = False
    require_approval: bool = False
    checkpoint_steps: List[str] = field(default_factory=list)
    error_handling: Literal["continue", "stop", "retry"] = "continue"
    llm_provider: str = "ollama"
    llm_model: str = "llama3.2"
    trace_enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TeamResult:
    """
    Container for team execution results.
    
    Attributes:
        task_id: Task identifier
        team_name: Name of the team
        status: Final status
        result: Primary result/output
        artifacts: All produced artifacts
        agent_outputs: Individual agent outputs
        duration_ms: Execution duration in milliseconds
        iterations: Number of iterations
        errors: Any errors encountered
        metadata: Additional metadata
    """
    task_id: str
    team_name: str
    status: TeamStatus
    result: Optional[str] = None
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    agent_outputs: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0
    iterations: int = 0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "team_name": self.team_name,
            "status": self.status.value,
            "result": self.result,
            "artifacts": self.artifacts,
            "agent_outputs": self.agent_outputs,
            "duration_ms": self.duration_ms,
            "iterations": self.iterations,
            "errors": self.errors,
            "metadata": self.metadata,
        }
    
    @property
    def success(self) -> bool:
        """Whether execution was successful."""
        return self.status == TeamStatus.COMPLETED


def create_initial_state(task: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create initial team state for a task.
    
    Args:
        task: Task description
        metadata: Optional metadata
        
    Returns:
        Initial state dictionary compatible with TeamState
    """
    return {
        "task_id": str(uuid.uuid4())[:8],
        "task": task,
        "status": TeamStatus.PENDING.value,
        "messages": [],
        "artifacts": [],
        "current_agent": None,
        "agent_outputs": {},
        "context": {},
        "plan": [],
        "current_step": 0,
        "errors": [],
        "metadata": metadata or {},
    }
