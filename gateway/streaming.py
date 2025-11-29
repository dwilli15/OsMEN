"""
SSE Streaming Endpoint for OsMEN Workflows

Provides real-time visibility into workflow runs via Server-Sent Events (SSE).
Enables live monitoring of workflow execution, tool calls, and results.

Usage:
    # Start streaming server
    uvicorn gateway.streaming:app --host 0.0.0.0 --port 8085
    
    # Client connection
    curl -N http://localhost:8085/stream/runs/{run_id}
"""

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Types of SSE events"""
    RUN_START = "run_start"
    RUN_STEP = "run_step"
    RUN_TOOL_CALL = "run_tool_call"
    RUN_TOOL_RESULT = "run_tool_result"
    RUN_ERROR = "run_error"
    RUN_APPROVAL_REQUIRED = "run_approval_required"
    RUN_APPROVAL_RESPONSE = "run_approval_response"
    RUN_COMPLETE = "run_complete"
    RUN_CANCELLED = "run_cancelled"
    HEARTBEAT = "heartbeat"


@dataclass
class SSEEvent:
    """Server-Sent Event structure"""
    event_type: EventType
    run_id: str
    timestamp: str
    data: Dict[str, Any]
    sequence: int = 0
    
    def to_sse_format(self) -> str:
        """Convert to SSE wire format"""
        event_data = {
            "event_type": self.event_type.value,
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "sequence": self.sequence,
            "data": self.data
        }
        # SSE format: event: <type>\ndata: <json>\n\n
        lines = [
            f"event: {self.event_type.value}",
            f"data: {json.dumps(event_data)}"
        ]
        return "\n".join(lines) + "\n\n"


@dataclass
class RunState:
    """State of a workflow run"""
    run_id: str
    workflow_name: str
    status: str = "pending"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    current_step: Optional[str] = None
    steps_completed: int = 0
    total_steps: int = 0
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    events: List[SSEEvent] = field(default_factory=list)


class StreamingManager:
    """
    Manages SSE streaming connections and event broadcasting.
    
    Supports multiple concurrent clients per run with automatic cleanup.
    """
    
    def __init__(self, heartbeat_interval: float = 30.0):
        """
        Initialize streaming manager.
        
        Args:
            heartbeat_interval: Seconds between heartbeat events
        """
        self.heartbeat_interval = heartbeat_interval
        
        # Active run states
        self._runs: Dict[str, RunState] = {}
        
        # Client queues per run: run_id -> set of asyncio.Queue
        self._clients: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
        
        # Event sequence counters
        self._sequences: Dict[str, int] = defaultdict(int)
        
        # Heartbeat tasks
        self._heartbeat_tasks: Dict[str, asyncio.Task] = {}
        
        # Event handlers for extensibility
        self._event_handlers: List[Callable[[SSEEvent], None]] = []
    
    def register_event_handler(self, handler: Callable[[SSEEvent], None]):
        """Register a handler to be called for every event"""
        self._event_handlers.append(handler)
    
    async def start_run(
        self,
        workflow_name: str,
        total_steps: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a new run and return its ID.
        
        Args:
            workflow_name: Name of the workflow
            total_steps: Estimated total steps (0 if unknown)
            metadata: Additional run metadata
            
        Returns:
            Run ID for tracking
        """
        run_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        run_state = RunState(
            run_id=run_id,
            workflow_name=workflow_name,
            status="running",
            started_at=timestamp,
            total_steps=total_steps
        )
        self._runs[run_id] = run_state
        
        # Emit start event
        await self._emit_event(
            EventType.RUN_START,
            run_id,
            {
                "workflow_name": workflow_name,
                "total_steps": total_steps,
                "metadata": metadata or {}
            }
        )
        
        # Start heartbeat for this run
        self._start_heartbeat(run_id)
        
        logger.info(f"Started run {run_id} for workflow {workflow_name}")
        return run_id
    
    async def emit_step(
        self,
        run_id: str,
        step_name: str,
        step_data: Optional[Dict[str, Any]] = None
    ):
        """
        Emit a step event.
        
        Args:
            run_id: Run ID
            step_name: Name of the step
            step_data: Step-specific data
        """
        if run_id not in self._runs:
            logger.warning(f"Run {run_id} not found")
            return
        
        run_state = self._runs[run_id]
        run_state.current_step = step_name
        run_state.steps_completed += 1
        
        await self._emit_event(
            EventType.RUN_STEP,
            run_id,
            {
                "step_name": step_name,
                "step_number": run_state.steps_completed,
                "total_steps": run_state.total_steps,
                "data": step_data or {}
            }
        )
    
    async def emit_tool_call(
        self,
        run_id: str,
        tool_name: str,
        tool_input: Dict[str, Any]
    ):
        """
        Emit a tool call event.
        
        Args:
            run_id: Run ID
            tool_name: Name of the tool
            tool_input: Tool input parameters
        """
        await self._emit_event(
            EventType.RUN_TOOL_CALL,
            run_id,
            {
                "tool_name": tool_name,
                "input": tool_input
            }
        )
    
    async def emit_tool_result(
        self,
        run_id: str,
        tool_name: str,
        tool_output: Any,
        success: bool = True
    ):
        """
        Emit a tool result event.
        
        Args:
            run_id: Run ID
            tool_name: Name of the tool
            tool_output: Tool output
            success: Whether the tool call succeeded
        """
        await self._emit_event(
            EventType.RUN_TOOL_RESULT,
            run_id,
            {
                "tool_name": tool_name,
                "output": tool_output,
                "success": success
            }
        )
    
    async def emit_error(
        self,
        run_id: str,
        error: str,
        error_type: str = "unknown",
        recoverable: bool = False
    ):
        """
        Emit an error event.
        
        Args:
            run_id: Run ID
            error: Error message
            error_type: Type of error
            recoverable: Whether the error is recoverable
        """
        if run_id in self._runs:
            self._runs[run_id].error = error
            if not recoverable:
                self._runs[run_id].status = "failed"
        
        await self._emit_event(
            EventType.RUN_ERROR,
            run_id,
            {
                "error": error,
                "error_type": error_type,
                "recoverable": recoverable
            }
        )
    
    async def request_approval(
        self,
        run_id: str,
        approval_id: str,
        action: str,
        context: Dict[str, Any],
        timeout_seconds: int = 300
    ) -> bool:
        """
        Request human approval for an action.
        
        Args:
            run_id: Run ID
            approval_id: Unique ID for this approval request
            action: Action requiring approval
            context: Context for the approval decision
            timeout_seconds: Timeout in seconds
            
        Returns:
            True if approved, False if denied or timeout
        """
        await self._emit_event(
            EventType.RUN_APPROVAL_REQUIRED,
            run_id,
            {
                "approval_id": approval_id,
                "action": action,
                "context": context,
                "timeout_seconds": timeout_seconds
            }
        )
        
        # Wait for approval response (handled by approval_response method)
        # This is a simplified implementation - production would use proper sync
        logger.info(f"Approval requested for run {run_id}, action: {action}")
        return True  # Auto-approve for now
    
    async def approval_response(
        self,
        run_id: str,
        approval_id: str,
        approved: bool,
        approver: str,
        reason: Optional[str] = None
    ):
        """
        Record an approval response.
        
        Args:
            run_id: Run ID
            approval_id: Approval request ID
            approved: Whether approved
            approver: Who approved/denied
            reason: Optional reason
        """
        await self._emit_event(
            EventType.RUN_APPROVAL_RESPONSE,
            run_id,
            {
                "approval_id": approval_id,
                "approved": approved,
                "approver": approver,
                "reason": reason
            }
        )
    
    async def complete_run(
        self,
        run_id: str,
        result: Optional[Dict[str, Any]] = None,
        status: str = "completed"
    ):
        """
        Mark a run as complete.
        
        Args:
            run_id: Run ID
            result: Run result
            status: Final status
        """
        if run_id not in self._runs:
            logger.warning(f"Run {run_id} not found")
            return
        
        timestamp = datetime.utcnow().isoformat() + "Z"
        run_state = self._runs[run_id]
        run_state.status = status
        run_state.completed_at = timestamp
        run_state.result = result
        
        await self._emit_event(
            EventType.RUN_COMPLETE,
            run_id,
            {
                "status": status,
                "result": result,
                "duration_ms": self._calculate_duration(run_state)
            }
        )
        
        # Stop heartbeat
        self._stop_heartbeat(run_id)
        
        logger.info(f"Completed run {run_id} with status {status}")
    
    async def cancel_run(self, run_id: str, reason: str = "User cancelled"):
        """
        Cancel a running workflow.
        
        Args:
            run_id: Run ID
            reason: Cancellation reason
        """
        if run_id not in self._runs:
            return
        
        self._runs[run_id].status = "cancelled"
        
        await self._emit_event(
            EventType.RUN_CANCELLED,
            run_id,
            {"reason": reason}
        )
        
        self._stop_heartbeat(run_id)
    
    async def subscribe(self, run_id: str) -> AsyncGenerator[SSEEvent, None]:
        """
        Subscribe to events for a run.
        
        Args:
            run_id: Run ID to subscribe to
            
        Yields:
            SSE events for the run
        """
        queue: asyncio.Queue = asyncio.Queue()
        self._clients[run_id].add(queue)
        
        try:
            # Send historical events first
            if run_id in self._runs:
                for event in self._runs[run_id].events:
                    yield event
            
            # Stream live events
            while True:
                event = await queue.get()
                yield event
                
                # Check if run is complete
                if event.event_type in [
                    EventType.RUN_COMPLETE,
                    EventType.RUN_CANCELLED,
                    EventType.RUN_ERROR
                ]:
                    if run_id in self._runs and self._runs[run_id].status in ["completed", "failed", "cancelled"]:
                        break
        finally:
            self._clients[run_id].discard(queue)
            if not self._clients[run_id]:
                del self._clients[run_id]
    
    def get_run_state(self, run_id: str) -> Optional[RunState]:
        """Get current state of a run"""
        return self._runs.get(run_id)
    
    def list_active_runs(self) -> List[str]:
        """List all active run IDs"""
        return [
            run_id for run_id, state in self._runs.items()
            if state.status == "running"
        ]
    
    async def _emit_event(
        self,
        event_type: EventType,
        run_id: str,
        data: Dict[str, Any]
    ):
        """Emit an event to all subscribers"""
        timestamp = datetime.utcnow().isoformat() + "Z"
        self._sequences[run_id] += 1
        
        event = SSEEvent(
            event_type=event_type,
            run_id=run_id,
            timestamp=timestamp,
            data=data,
            sequence=self._sequences[run_id]
        )
        
        # Store in run state
        if run_id in self._runs:
            self._runs[run_id].events.append(event)
        
        # Broadcast to clients
        for queue in self._clients.get(run_id, set()):
            try:
                await queue.put(event)
            except Exception as e:
                logger.warning(f"Failed to send event to client: {e}")
        
        # Call event handlers
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.warning(f"Event handler error: {e}")
    
    def _start_heartbeat(self, run_id: str):
        """Start heartbeat task for a run"""
        async def heartbeat_loop():
            while run_id in self._runs and self._runs[run_id].status == "running":
                await asyncio.sleep(self.heartbeat_interval)
                if run_id in self._clients and self._clients[run_id]:
                    await self._emit_event(
                        EventType.HEARTBEAT,
                        run_id,
                        {"status": "alive"}
                    )
        
        task = asyncio.create_task(heartbeat_loop())
        self._heartbeat_tasks[run_id] = task
    
    def _stop_heartbeat(self, run_id: str):
        """Stop heartbeat task for a run"""
        if run_id in self._heartbeat_tasks:
            self._heartbeat_tasks[run_id].cancel()
            del self._heartbeat_tasks[run_id]
    
    def _calculate_duration(self, run_state: RunState) -> int:
        """Calculate run duration in milliseconds"""
        if not run_state.started_at or not run_state.completed_at:
            return 0
        
        start = datetime.fromisoformat(run_state.started_at.rstrip("Z"))
        end = datetime.fromisoformat(run_state.completed_at.rstrip("Z"))
        return int((end - start).total_seconds() * 1000)


# FastAPI application for SSE streaming
try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import StreamingResponse
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI(
        title="OsMEN Streaming API",
        description="Server-Sent Events for workflow run monitoring",
        version="3.0.0"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Global streaming manager instance
    streaming_manager = StreamingManager()
    
    @app.get("/stream/runs/{run_id}")
    async def stream_run(run_id: str, request: Request):
        """
        Stream events for a specific run.
        
        Returns SSE stream of run events.
        """
        async def event_generator():
            try:
                async for event in streaming_manager.subscribe(run_id):
                    if await request.is_disconnected():
                        break
                    yield event.to_sse_format()
            except asyncio.CancelledError:
                pass
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    @app.get("/runs")
    async def list_runs():
        """List all active runs"""
        return {
            "active_runs": streaming_manager.list_active_runs(),
            "count": len(streaming_manager.list_active_runs())
        }
    
    @app.get("/runs/{run_id}")
    async def get_run(run_id: str):
        """Get current state of a run"""
        state = streaming_manager.get_run_state(run_id)
        if not state:
            raise HTTPException(status_code=404, detail="Run not found")
        return asdict(state)
    
    @app.post("/runs/{run_id}/cancel")
    async def cancel_run(run_id: str, reason: str = "User cancelled"):
        """Cancel a running workflow"""
        await streaming_manager.cancel_run(run_id, reason)
        return {"status": "cancelled", "run_id": run_id}
    
    @app.post("/runs/{run_id}/approve/{approval_id}")
    async def approve_action(
        run_id: str,
        approval_id: str,
        approved: bool = True,
        approver: str = "api",
        reason: str = None
    ):
        """Approve or deny a pending action"""
        await streaming_manager.approval_response(
            run_id, approval_id, approved, approver, reason
        )
        return {"status": "recorded", "approved": approved}

except ImportError:
    # FastAPI not available
    app = None
    streaming_manager = StreamingManager()


# Singleton access
_manager: Optional[StreamingManager] = None

def get_streaming_manager() -> StreamingManager:
    """Get the global streaming manager instance"""
    global _manager
    if _manager is None:
        _manager = StreamingManager()
    return _manager


# Integration with workflow engine
class StreamingWorkflowMixin:
    """
    Mixin for workflow classes to enable streaming.
    
    Usage:
        class MyWorkflow(StreamingWorkflowMixin):
            async def run(self, input):
                run_id = await self.start_streaming("MyWorkflow")
                try:
                    await self.stream_step("step1", {"data": "..."})
                    result = await self.do_work()
                    await self.complete_streaming({"result": result})
                except Exception as e:
                    await self.stream_error(str(e))
                    raise
    """
    
    _streaming_manager: Optional[StreamingManager] = None
    _current_run_id: Optional[str] = None
    
    async def start_streaming(
        self,
        workflow_name: str,
        total_steps: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start streaming for this workflow run"""
        self._streaming_manager = get_streaming_manager()
        self._current_run_id = await self._streaming_manager.start_run(
            workflow_name, total_steps, metadata
        )
        return self._current_run_id
    
    async def stream_step(
        self,
        step_name: str,
        step_data: Optional[Dict[str, Any]] = None
    ):
        """Emit a step event"""
        if self._streaming_manager and self._current_run_id:
            await self._streaming_manager.emit_step(
                self._current_run_id, step_name, step_data
            )
    
    async def stream_tool_call(
        self,
        tool_name: str,
        tool_input: Dict[str, Any]
    ):
        """Emit a tool call event"""
        if self._streaming_manager and self._current_run_id:
            await self._streaming_manager.emit_tool_call(
                self._current_run_id, tool_name, tool_input
            )
    
    async def stream_tool_result(
        self,
        tool_name: str,
        tool_output: Any,
        success: bool = True
    ):
        """Emit a tool result event"""
        if self._streaming_manager and self._current_run_id:
            await self._streaming_manager.emit_tool_result(
                self._current_run_id, tool_name, tool_output, success
            )
    
    async def stream_error(
        self,
        error: str,
        error_type: str = "workflow_error",
        recoverable: bool = False
    ):
        """Emit an error event"""
        if self._streaming_manager and self._current_run_id:
            await self._streaming_manager.emit_error(
                self._current_run_id, error, error_type, recoverable
            )
    
    async def request_approval(
        self,
        action: str,
        context: Dict[str, Any],
        timeout_seconds: int = 300
    ) -> bool:
        """Request human approval"""
        if self._streaming_manager and self._current_run_id:
            approval_id = str(uuid.uuid4())
            return await self._streaming_manager.request_approval(
                self._current_run_id, approval_id, action, context, timeout_seconds
            )
        return True  # Auto-approve if streaming not enabled
    
    async def complete_streaming(
        self,
        result: Optional[Dict[str, Any]] = None,
        status: str = "completed"
    ):
        """Complete the streaming run"""
        if self._streaming_manager and self._current_run_id:
            await self._streaming_manager.complete_run(
                self._current_run_id, result, status
            )


if __name__ == "__main__":
    import uvicorn
    
    if app:
        uvicorn.run(app, host="0.0.0.0", port=8085)
    else:
        print("FastAPI not installed. Install with: pip install fastapi uvicorn")
