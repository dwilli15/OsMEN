"""
Run Result Storage for OsMEN Workflows

PostgreSQL persistence for workflow run history, steps, tool calls, and results.
Provides audit trail and historical query capabilities.

Usage:
    from database.run_storage import get_run_storage
    
    storage = await get_run_storage()
    
    # Store a run
    run_id = await storage.create_run("daily_brief", {"user": "alice"})
    await storage.add_step(run_id, "calendar", {"events": 5})
    await storage.complete_run(run_id, {"summary": "..."})
    
    # Query runs
    runs = await storage.list_runs(workflow="daily_brief", limit=10)
    run = await storage.get_run(run_id)
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


class RunStatus(str, Enum):
    """Run status values"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_APPROVAL = "waiting_approval"


class StepStatus(str, Enum):
    """Step status values"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class RunRecord:
    """A workflow run record"""
    id: str
    workflow_name: str
    status: RunStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    parent_run_id: Optional[str] = None
    steps: List["StepRecord"] = field(default_factory=list)
    tool_calls: List["ToolCallRecord"] = field(default_factory=list)


@dataclass
class StepRecord:
    """A workflow step record"""
    id: str
    run_id: str
    step_name: str
    step_number: int
    status: StepStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None


@dataclass
class ToolCallRecord:
    """A tool call record"""
    id: str
    run_id: str
    step_id: Optional[str]
    tool_name: str
    input_data: Dict[str, Any]
    output_data: Optional[Any] = None
    success: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None


@dataclass
class ApprovalRecord:
    """An approval request record"""
    id: str
    run_id: str
    action: str
    context: Dict[str, Any]
    status: str  # pending, approved, denied, timeout
    created_at: datetime
    responded_at: Optional[datetime] = None
    approver: Optional[str] = None
    reason: Optional[str] = None
    timeout_at: Optional[datetime] = None


class RunStorage:
    """
    Abstract run storage interface.
    
    Implementations can use PostgreSQL, SQLite, or in-memory storage.
    """
    
    async def create_run(
        self,
        workflow_name: str,
        input_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        parent_run_id: Optional[str] = None
    ) -> str:
        """Create a new run and return its ID"""
        raise NotImplementedError
    
    async def start_run(self, run_id: str):
        """Mark a run as started"""
        raise NotImplementedError
    
    async def complete_run(
        self,
        run_id: str,
        output_data: Optional[Dict[str, Any]] = None,
        status: RunStatus = RunStatus.COMPLETED
    ):
        """Mark a run as complete"""
        raise NotImplementedError
    
    async def fail_run(self, run_id: str, error: str):
        """Mark a run as failed"""
        raise NotImplementedError
    
    async def get_run(self, run_id: str) -> Optional[RunRecord]:
        """Get a run by ID"""
        raise NotImplementedError
    
    async def list_runs(
        self,
        workflow: Optional[str] = None,
        status: Optional[RunStatus] = None,
        user_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[RunRecord]:
        """List runs with filters"""
        raise NotImplementedError
    
    async def add_step(
        self,
        run_id: str,
        step_name: str,
        input_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a step to a run"""
        raise NotImplementedError
    
    async def complete_step(
        self,
        step_id: str,
        output_data: Optional[Dict[str, Any]] = None,
        status: StepStatus = StepStatus.COMPLETED
    ):
        """Mark a step as complete"""
        raise NotImplementedError
    
    async def add_tool_call(
        self,
        run_id: str,
        tool_name: str,
        input_data: Dict[str, Any],
        step_id: Optional[str] = None
    ) -> str:
        """Record a tool call"""
        raise NotImplementedError
    
    async def complete_tool_call(
        self,
        tool_call_id: str,
        output_data: Any,
        success: bool = True,
        error: Optional[str] = None
    ):
        """Record tool call completion"""
        raise NotImplementedError
    
    async def create_approval(
        self,
        run_id: str,
        action: str,
        context: Dict[str, Any],
        timeout_seconds: int = 300
    ) -> str:
        """Create an approval request"""
        raise NotImplementedError
    
    async def respond_approval(
        self,
        approval_id: str,
        approved: bool,
        approver: str,
        reason: Optional[str] = None
    ):
        """Respond to an approval request"""
        raise NotImplementedError
    
    async def get_pending_approvals(
        self,
        run_id: Optional[str] = None
    ) -> List[ApprovalRecord]:
        """Get pending approval requests"""
        raise NotImplementedError
    
    async def get_run_stats(
        self,
        workflow: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get run statistics"""
        raise NotImplementedError


class InMemoryRunStorage(RunStorage):
    """
    In-memory run storage for development and testing.
    
    Data is lost on restart. Use PostgreSQL for production.
    """
    
    def __init__(self):
        self._runs: Dict[str, RunRecord] = {}
        self._steps: Dict[str, StepRecord] = {}
        self._tool_calls: Dict[str, ToolCallRecord] = {}
        self._approvals: Dict[str, ApprovalRecord] = {}
        self._step_counters: Dict[str, int] = {}
    
    async def create_run(
        self,
        workflow_name: str,
        input_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        parent_run_id: Optional[str] = None
    ) -> str:
        run_id = str(uuid4())
        now = datetime.utcnow()
        
        run = RunRecord(
            id=run_id,
            workflow_name=workflow_name,
            status=RunStatus.PENDING,
            created_at=now,
            input_data=input_data,
            metadata=metadata or {},
            user_id=user_id,
            parent_run_id=parent_run_id
        )
        
        self._runs[run_id] = run
        self._step_counters[run_id] = 0
        
        logger.info(f"Created run {run_id} for workflow {workflow_name}")
        return run_id
    
    async def start_run(self, run_id: str):
        if run_id in self._runs:
            self._runs[run_id].status = RunStatus.RUNNING
            self._runs[run_id].started_at = datetime.utcnow()
    
    async def complete_run(
        self,
        run_id: str,
        output_data: Optional[Dict[str, Any]] = None,
        status: RunStatus = RunStatus.COMPLETED
    ):
        if run_id in self._runs:
            self._runs[run_id].status = status
            self._runs[run_id].completed_at = datetime.utcnow()
            self._runs[run_id].output_data = output_data
    
    async def fail_run(self, run_id: str, error: str):
        if run_id in self._runs:
            self._runs[run_id].status = RunStatus.FAILED
            self._runs[run_id].completed_at = datetime.utcnow()
            self._runs[run_id].error = error
    
    async def get_run(self, run_id: str) -> Optional[RunRecord]:
        run = self._runs.get(run_id)
        if run:
            # Attach steps and tool calls
            run.steps = [s for s in self._steps.values() if s.run_id == run_id]
            run.tool_calls = [t for t in self._tool_calls.values() if t.run_id == run_id]
        return run
    
    async def list_runs(
        self,
        workflow: Optional[str] = None,
        status: Optional[RunStatus] = None,
        user_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[RunRecord]:
        runs = list(self._runs.values())
        
        # Apply filters
        if workflow:
            runs = [r for r in runs if r.workflow_name == workflow]
        if status:
            runs = [r for r in runs if r.status == status]
        if user_id:
            runs = [r for r in runs if r.user_id == user_id]
        if since:
            runs = [r for r in runs if r.created_at >= since]
        if until:
            runs = [r for r in runs if r.created_at <= until]
        
        # Sort by created_at descending
        runs.sort(key=lambda r: r.created_at, reverse=True)
        
        # Apply pagination
        return runs[offset:offset + limit]
    
    async def add_step(
        self,
        run_id: str,
        step_name: str,
        input_data: Optional[Dict[str, Any]] = None
    ) -> str:
        step_id = str(uuid4())
        now = datetime.utcnow()
        
        self._step_counters[run_id] = self._step_counters.get(run_id, 0) + 1
        
        step = StepRecord(
            id=step_id,
            run_id=run_id,
            step_name=step_name,
            step_number=self._step_counters[run_id],
            status=StepStatus.RUNNING,
            created_at=now,
            started_at=now,
            input_data=input_data
        )
        
        self._steps[step_id] = step
        return step_id
    
    async def complete_step(
        self,
        step_id: str,
        output_data: Optional[Dict[str, Any]] = None,
        status: StepStatus = StepStatus.COMPLETED
    ):
        if step_id in self._steps:
            step = self._steps[step_id]
            step.status = status
            step.completed_at = datetime.utcnow()
            step.output_data = output_data
            if step.started_at:
                step.duration_ms = int((step.completed_at - step.started_at).total_seconds() * 1000)
    
    async def add_tool_call(
        self,
        run_id: str,
        tool_name: str,
        input_data: Dict[str, Any],
        step_id: Optional[str] = None
    ) -> str:
        tool_call_id = str(uuid4())
        
        tool_call = ToolCallRecord(
            id=tool_call_id,
            run_id=run_id,
            step_id=step_id,
            tool_name=tool_name,
            input_data=input_data,
            created_at=datetime.utcnow()
        )
        
        self._tool_calls[tool_call_id] = tool_call
        return tool_call_id
    
    async def complete_tool_call(
        self,
        tool_call_id: str,
        output_data: Any,
        success: bool = True,
        error: Optional[str] = None
    ):
        if tool_call_id in self._tool_calls:
            tc = self._tool_calls[tool_call_id]
            tc.output_data = output_data
            tc.success = success
            tc.error = error
            tc.completed_at = datetime.utcnow()
            tc.duration_ms = int((tc.completed_at - tc.created_at).total_seconds() * 1000)
    
    async def create_approval(
        self,
        run_id: str,
        action: str,
        context: Dict[str, Any],
        timeout_seconds: int = 300
    ) -> str:
        approval_id = str(uuid4())
        now = datetime.utcnow()
        
        approval = ApprovalRecord(
            id=approval_id,
            run_id=run_id,
            action=action,
            context=context,
            status="pending",
            created_at=now,
            timeout_at=now + timedelta(seconds=timeout_seconds)
        )
        
        self._approvals[approval_id] = approval
        
        # Update run status
        if run_id in self._runs:
            self._runs[run_id].status = RunStatus.WAITING_APPROVAL
        
        return approval_id
    
    async def respond_approval(
        self,
        approval_id: str,
        approved: bool,
        approver: str,
        reason: Optional[str] = None
    ):
        if approval_id in self._approvals:
            approval = self._approvals[approval_id]
            approval.status = "approved" if approved else "denied"
            approval.responded_at = datetime.utcnow()
            approval.approver = approver
            approval.reason = reason
            
            # Update run status back to running
            if approval.run_id in self._runs:
                self._runs[approval.run_id].status = RunStatus.RUNNING
    
    async def get_pending_approvals(
        self,
        run_id: Optional[str] = None
    ) -> List[ApprovalRecord]:
        approvals = [a for a in self._approvals.values() if a.status == "pending"]
        if run_id:
            approvals = [a for a in approvals if a.run_id == run_id]
        return approvals
    
    async def get_run_stats(
        self,
        workflow: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        runs = list(self._runs.values())
        
        if workflow:
            runs = [r for r in runs if r.workflow_name == workflow]
        if since:
            runs = [r for r in runs if r.created_at >= since]
        
        total = len(runs)
        completed = len([r for r in runs if r.status == RunStatus.COMPLETED])
        failed = len([r for r in runs if r.status == RunStatus.FAILED])
        running = len([r for r in runs if r.status == RunStatus.RUNNING])
        
        # Calculate average duration
        durations = []
        for r in runs:
            if r.started_at and r.completed_at:
                duration = (r.completed_at - r.started_at).total_seconds() * 1000
                durations.append(duration)
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "total_runs": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "success_rate": completed / total * 100 if total > 0 else 0,
            "average_duration_ms": avg_duration
        }


class PostgresRunStorage(RunStorage):
    """
    PostgreSQL run storage for production use.
    
    Requires asyncpg and a PostgreSQL database.
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/osmen"
        )
        self._pool = None
    
    async def _get_pool(self):
        """Get or create connection pool"""
        if self._pool is None:
            try:
                import asyncpg
                self._pool = await asyncpg.create_pool(
                    self.connection_string,
                    min_size=2,
                    max_size=10
                )
                await self._ensure_tables()
            except ImportError:
                raise ImportError("asyncpg required. Install with: pip install asyncpg")
        return self._pool
    
    async def _ensure_tables(self):
        """Create tables if they don't exist"""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id UUID PRIMARY KEY,
                    workflow_name VARCHAR(255) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    started_at TIMESTAMP WITH TIME ZONE,
                    completed_at TIMESTAMP WITH TIME ZONE,
                    input_data JSONB,
                    output_data JSONB,
                    error TEXT,
                    metadata JSONB DEFAULT '{}',
                    user_id VARCHAR(255),
                    parent_run_id UUID REFERENCES runs(id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_runs_workflow ON runs(workflow_name);
                CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
                CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_runs_user ON runs(user_id);
                
                CREATE TABLE IF NOT EXISTS run_steps (
                    id UUID PRIMARY KEY,
                    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                    step_name VARCHAR(255) NOT NULL,
                    step_number INTEGER NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    started_at TIMESTAMP WITH TIME ZONE,
                    completed_at TIMESTAMP WITH TIME ZONE,
                    input_data JSONB,
                    output_data JSONB,
                    error TEXT,
                    duration_ms INTEGER
                );
                
                CREATE INDEX IF NOT EXISTS idx_steps_run ON run_steps(run_id);
                
                CREATE TABLE IF NOT EXISTS tool_calls (
                    id UUID PRIMARY KEY,
                    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                    step_id UUID REFERENCES run_steps(id),
                    tool_name VARCHAR(255) NOT NULL,
                    input_data JSONB NOT NULL,
                    output_data JSONB,
                    success BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    completed_at TIMESTAMP WITH TIME ZONE,
                    duration_ms INTEGER,
                    error TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_tools_run ON tool_calls(run_id);
                
                CREATE TABLE IF NOT EXISTS approvals (
                    id UUID PRIMARY KEY,
                    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                    action VARCHAR(255) NOT NULL,
                    context JSONB NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    responded_at TIMESTAMP WITH TIME ZONE,
                    timeout_at TIMESTAMP WITH TIME ZONE,
                    approver VARCHAR(255),
                    reason TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_approvals_run ON approvals(run_id);
                CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);
            """)
    
    async def create_run(
        self,
        workflow_name: str,
        input_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        parent_run_id: Optional[str] = None
    ) -> str:
        pool = await self._get_pool()
        run_id = str(uuid4())
        now = datetime.utcnow()
        
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO runs (id, workflow_name, status, created_at, input_data, metadata, user_id, parent_run_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, 
                run_id, workflow_name, RunStatus.PENDING.value, now,
                json.dumps(input_data) if input_data else None,
                json.dumps(metadata or {}),
                user_id, parent_run_id
            )
        
        return run_id
    
    async def start_run(self, run_id: str):
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE runs SET status = $1, started_at = $2 WHERE id = $3
            """, RunStatus.RUNNING.value, datetime.utcnow(), run_id)
    
    async def complete_run(
        self,
        run_id: str,
        output_data: Optional[Dict[str, Any]] = None,
        status: RunStatus = RunStatus.COMPLETED
    ):
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE runs SET status = $1, completed_at = $2, output_data = $3 WHERE id = $4
            """, status.value, datetime.utcnow(), 
                json.dumps(output_data) if output_data else None, run_id)
    
    async def fail_run(self, run_id: str, error: str):
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE runs SET status = $1, completed_at = $2, error = $3 WHERE id = $4
            """, RunStatus.FAILED.value, datetime.utcnow(), error, run_id)
    
    async def get_run(self, run_id: str) -> Optional[RunRecord]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM runs WHERE id = $1", run_id)
            if not row:
                return None
            
            # Get steps
            steps = await conn.fetch(
                "SELECT * FROM run_steps WHERE run_id = $1 ORDER BY step_number",
                run_id
            )
            
            # Get tool calls
            tool_calls = await conn.fetch(
                "SELECT * FROM tool_calls WHERE run_id = $1 ORDER BY created_at",
                run_id
            )
            
            return self._row_to_run_record(row, steps, tool_calls)
    
    async def list_runs(
        self,
        workflow: Optional[str] = None,
        status: Optional[RunStatus] = None,
        user_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[RunRecord]:
        pool = await self._get_pool()
        
        conditions = []
        params = []
        param_idx = 1
        
        if workflow:
            conditions.append(f"workflow_name = ${param_idx}")
            params.append(workflow)
            param_idx += 1
        
        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status.value)
            param_idx += 1
        
        if user_id:
            conditions.append(f"user_id = ${param_idx}")
            params.append(user_id)
            param_idx += 1
        
        if since:
            conditions.append(f"created_at >= ${param_idx}")
            params.append(since)
            param_idx += 1
        
        if until:
            conditions.append(f"created_at <= ${param_idx}")
            params.append(until)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT * FROM runs 
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, offset])
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [self._row_to_run_record(row) for row in rows]
    
    def _row_to_run_record(
        self,
        row,
        steps=None,
        tool_calls=None
    ) -> RunRecord:
        """Convert database row to RunRecord"""
        return RunRecord(
            id=str(row["id"]),
            workflow_name=row["workflow_name"],
            status=RunStatus(row["status"]),
            created_at=row["created_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            input_data=json.loads(row["input_data"]) if row["input_data"] else None,
            output_data=json.loads(row["output_data"]) if row["output_data"] else None,
            error=row["error"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            user_id=row["user_id"],
            parent_run_id=str(row["parent_run_id"]) if row["parent_run_id"] else None,
            steps=[self._row_to_step_record(s) for s in (steps or [])],
            tool_calls=[self._row_to_tool_call_record(t) for t in (tool_calls or [])]
        )
    
    def _row_to_step_record(self, row) -> StepRecord:
        """Convert database row to StepRecord"""
        return StepRecord(
            id=str(row["id"]),
            run_id=str(row["run_id"]),
            step_name=row["step_name"],
            step_number=row["step_number"],
            status=StepStatus(row["status"]),
            created_at=row["created_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            input_data=json.loads(row["input_data"]) if row["input_data"] else None,
            output_data=json.loads(row["output_data"]) if row["output_data"] else None,
            error=row["error"],
            duration_ms=row["duration_ms"]
        )
    
    def _row_to_tool_call_record(self, row) -> ToolCallRecord:
        """Convert database row to ToolCallRecord"""
        return ToolCallRecord(
            id=str(row["id"]),
            run_id=str(row["run_id"]),
            step_id=str(row["step_id"]) if row["step_id"] else None,
            tool_name=row["tool_name"],
            input_data=json.loads(row["input_data"]),
            output_data=json.loads(row["output_data"]) if row["output_data"] else None,
            success=row["success"],
            created_at=row["created_at"],
            completed_at=row["completed_at"],
            duration_ms=row["duration_ms"],
            error=row["error"]
        )
    
    # Implement remaining methods similar to InMemoryRunStorage
    # but with PostgreSQL queries...
    
    async def add_step(
        self,
        run_id: str,
        step_name: str,
        input_data: Optional[Dict[str, Any]] = None
    ) -> str:
        pool = await self._get_pool()
        step_id = str(uuid4())
        now = datetime.utcnow()
        
        async with pool.acquire() as conn:
            # Get current step count
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM run_steps WHERE run_id = $1",
                run_id
            )
            
            await conn.execute("""
                INSERT INTO run_steps (id, run_id, step_name, step_number, status, created_at, started_at, input_data)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                step_id, run_id, step_name, count + 1,
                StepStatus.RUNNING.value, now, now,
                json.dumps(input_data) if input_data else None
            )
        
        return step_id
    
    async def complete_step(
        self,
        step_id: str,
        output_data: Optional[Dict[str, Any]] = None,
        status: StepStatus = StepStatus.COMPLETED
    ):
        pool = await self._get_pool()
        now = datetime.utcnow()
        
        async with pool.acquire() as conn:
            # Calculate duration
            started = await conn.fetchval(
                "SELECT started_at FROM run_steps WHERE id = $1",
                step_id
            )
            duration_ms = int((now - started).total_seconds() * 1000) if started else None
            
            await conn.execute("""
                UPDATE run_steps 
                SET status = $1, completed_at = $2, output_data = $3, duration_ms = $4
                WHERE id = $5
            """,
                status.value, now,
                json.dumps(output_data) if output_data else None,
                duration_ms, step_id
            )
    
    async def add_tool_call(
        self,
        run_id: str,
        tool_name: str,
        input_data: Dict[str, Any],
        step_id: Optional[str] = None
    ) -> str:
        pool = await self._get_pool()
        tool_call_id = str(uuid4())
        
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO tool_calls (id, run_id, step_id, tool_name, input_data, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                tool_call_id, run_id, step_id, tool_name,
                json.dumps(input_data), datetime.utcnow()
            )
        
        return tool_call_id
    
    async def complete_tool_call(
        self,
        tool_call_id: str,
        output_data: Any,
        success: bool = True,
        error: Optional[str] = None
    ):
        pool = await self._get_pool()
        now = datetime.utcnow()
        
        async with pool.acquire() as conn:
            created = await conn.fetchval(
                "SELECT created_at FROM tool_calls WHERE id = $1",
                tool_call_id
            )
            duration_ms = int((now - created).total_seconds() * 1000) if created else None
            
            await conn.execute("""
                UPDATE tool_calls 
                SET output_data = $1, success = $2, completed_at = $3, duration_ms = $4, error = $5
                WHERE id = $6
            """,
                json.dumps(output_data), success, now, duration_ms, error, tool_call_id
            )
    
    async def create_approval(
        self,
        run_id: str,
        action: str,
        context: Dict[str, Any],
        timeout_seconds: int = 300
    ) -> str:
        pool = await self._get_pool()
        approval_id = str(uuid4())
        now = datetime.utcnow()
        
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO approvals (id, run_id, action, context, status, created_at, timeout_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                approval_id, run_id, action, json.dumps(context),
                "pending", now, now + timedelta(seconds=timeout_seconds)
            )
            
            # Update run status
            await conn.execute("""
                UPDATE runs SET status = $1 WHERE id = $2
            """, RunStatus.WAITING_APPROVAL.value, run_id)
        
        return approval_id
    
    async def respond_approval(
        self,
        approval_id: str,
        approved: bool,
        approver: str,
        reason: Optional[str] = None
    ):
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            run_id = await conn.fetchval(
                "SELECT run_id FROM approvals WHERE id = $1",
                approval_id
            )
            
            await conn.execute("""
                UPDATE approvals 
                SET status = $1, responded_at = $2, approver = $3, reason = $4
                WHERE id = $5
            """,
                "approved" if approved else "denied",
                datetime.utcnow(), approver, reason, approval_id
            )
            
            # Update run status
            if run_id:
                await conn.execute("""
                    UPDATE runs SET status = $1 WHERE id = $2
                """, RunStatus.RUNNING.value, run_id)
    
    async def get_pending_approvals(
        self,
        run_id: Optional[str] = None
    ) -> List[ApprovalRecord]:
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            if run_id:
                rows = await conn.fetch(
                    "SELECT * FROM approvals WHERE run_id = $1 AND status = 'pending'",
                    run_id
                )
            else:
                rows = await conn.fetch(
                    "SELECT * FROM approvals WHERE status = 'pending'"
                )
            
            return [
                ApprovalRecord(
                    id=str(row["id"]),
                    run_id=str(row["run_id"]),
                    action=row["action"],
                    context=json.loads(row["context"]),
                    status=row["status"],
                    created_at=row["created_at"],
                    timeout_at=row["timeout_at"]
                )
                for row in rows
            ]
    
    async def get_run_stats(
        self,
        workflow: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        pool = await self._get_pool()
        
        conditions = []
        params = []
        param_idx = 1
        
        if workflow:
            conditions.append(f"workflow_name = ${param_idx}")
            params.append(workflow)
            param_idx += 1
        
        if since:
            conditions.append(f"created_at >= ${param_idx}")
            params.append(since)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        async with pool.acquire() as conn:
            stats = await conn.fetchrow(f"""
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed,
                    COUNT(*) FILTER (WHERE status = 'running') as running,
                    AVG(EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000) 
                        FILTER (WHERE completed_at IS NOT NULL) as avg_duration
                FROM runs
                WHERE {where_clause}
            """, *params)
            
            total = stats["total"] or 0
            completed = stats["completed"] or 0
            
            return {
                "total_runs": total,
                "completed": completed,
                "failed": stats["failed"] or 0,
                "running": stats["running"] or 0,
                "success_rate": completed / total * 100 if total > 0 else 0,
                "average_duration_ms": stats["avg_duration"] or 0
            }


# Singleton storage instance
_storage: Optional[RunStorage] = None

async def get_run_storage(use_postgres: bool = None) -> RunStorage:
    """
    Get the global run storage instance.
    
    Args:
        use_postgres: Force PostgreSQL (True) or in-memory (False).
                     If None, auto-detect based on DATABASE_URL.
    
    Returns:
        RunStorage instance
    """
    global _storage
    
    if _storage is None:
        if use_postgres is None:
            use_postgres = bool(os.getenv("DATABASE_URL"))
        
        if use_postgres:
            _storage = PostgresRunStorage()
        else:
            _storage = InMemoryRunStorage()
            logger.info("Using in-memory run storage (data will be lost on restart)")
    
    return _storage


# Export for convenience
__all__ = [
    "RunStorage",
    "InMemoryRunStorage",
    "PostgresRunStorage",
    "RunRecord",
    "StepRecord",
    "ToolCallRecord",
    "ApprovalRecord",
    "RunStatus",
    "StepStatus",
    "get_run_storage"
]
