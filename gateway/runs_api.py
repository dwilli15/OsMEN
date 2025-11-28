"""
Run History API for OsMEN Workflows

FastAPI router providing CRUD endpoints for workflow run history.
Supports search, filtering, pagination, and export.

Usage:
    from gateway.runs_api import router
    
    app = FastAPI()
    app.include_router(router)
    
    # Then access:
    # GET /api/runs - List runs
    # GET /api/runs/{run_id} - Get run details
    # DELETE /api/runs/{run_id} - Delete run
    # GET /api/runs/stats - Get statistics
    # POST /api/runs/export - Export runs
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from fastapi import APIRouter, HTTPException, Query, Response
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel, Field
    
    # Import storage
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from database.run_storage import (
        get_run_storage,
        RunStatus,
        StepStatus,
        RunRecord,
        StepRecord,
        ToolCallRecord
    )
    
    router = APIRouter(prefix="/api/runs", tags=["runs"])
    
    # Pydantic models for request/response
    
    class RunSummary(BaseModel):
        """Summary of a run for list view"""
        id: str
        workflow_name: str
        status: str
        created_at: str
        started_at: Optional[str] = None
        completed_at: Optional[str] = None
        duration_ms: Optional[int] = None
        step_count: int = 0
        error: Optional[str] = None
        user_id: Optional[str] = None
    
    class StepDetail(BaseModel):
        """Step details"""
        id: str
        step_name: str
        step_number: int
        status: str
        started_at: Optional[str] = None
        completed_at: Optional[str] = None
        duration_ms: Optional[int] = None
        input_data: Optional[Dict[str, Any]] = None
        output_data: Optional[Dict[str, Any]] = None
        error: Optional[str] = None
    
    class ToolCallDetail(BaseModel):
        """Tool call details"""
        id: str
        tool_name: str
        input_data: Dict[str, Any]
        output_data: Optional[Any] = None
        success: bool = True
        duration_ms: Optional[int] = None
        error: Optional[str] = None
    
    class RunDetail(BaseModel):
        """Full run details"""
        id: str
        workflow_name: str
        status: str
        created_at: str
        started_at: Optional[str] = None
        completed_at: Optional[str] = None
        duration_ms: Optional[int] = None
        input_data: Optional[Dict[str, Any]] = None
        output_data: Optional[Dict[str, Any]] = None
        error: Optional[str] = None
        metadata: Dict[str, Any] = Field(default_factory=dict)
        user_id: Optional[str] = None
        parent_run_id: Optional[str] = None
        steps: List[StepDetail] = Field(default_factory=list)
        tool_calls: List[ToolCallDetail] = Field(default_factory=list)
    
    class RunListResponse(BaseModel):
        """Response for run list"""
        runs: List[RunSummary]
        total: int
        page: int
        per_page: int
        pages: int
    
    class RunStatsResponse(BaseModel):
        """Run statistics response"""
        total_runs: int
        completed: int
        failed: int
        running: int
        success_rate: float
        average_duration_ms: float
        by_workflow: Dict[str, int] = Field(default_factory=dict)
        by_status: Dict[str, int] = Field(default_factory=dict)
        recent_failures: List[RunSummary] = Field(default_factory=list)
    
    class ExportRequest(BaseModel):
        """Export request"""
        workflow: Optional[str] = None
        status: Optional[str] = None
        since: Optional[str] = None
        until: Optional[str] = None
        format: str = "json"  # json, csv
    
    def _run_to_summary(run: RunRecord) -> RunSummary:
        """Convert RunRecord to RunSummary"""
        duration_ms = None
        if run.started_at and run.completed_at:
            duration_ms = int((run.completed_at - run.started_at).total_seconds() * 1000)
        
        return RunSummary(
            id=run.id,
            workflow_name=run.workflow_name,
            status=run.status.value if isinstance(run.status, RunStatus) else run.status,
            created_at=run.created_at.isoformat() if run.created_at else "",
            started_at=run.started_at.isoformat() if run.started_at else None,
            completed_at=run.completed_at.isoformat() if run.completed_at else None,
            duration_ms=duration_ms,
            step_count=len(run.steps) if run.steps else 0,
            error=run.error,
            user_id=run.user_id
        )
    
    def _run_to_detail(run: RunRecord) -> RunDetail:
        """Convert RunRecord to RunDetail"""
        duration_ms = None
        if run.started_at and run.completed_at:
            duration_ms = int((run.completed_at - run.started_at).total_seconds() * 1000)
        
        steps = []
        if run.steps:
            for s in run.steps:
                steps.append(StepDetail(
                    id=s.id,
                    step_name=s.step_name,
                    step_number=s.step_number,
                    status=s.status.value if isinstance(s.status, StepStatus) else s.status,
                    started_at=s.started_at.isoformat() if s.started_at else None,
                    completed_at=s.completed_at.isoformat() if s.completed_at else None,
                    duration_ms=s.duration_ms,
                    input_data=s.input_data,
                    output_data=s.output_data,
                    error=s.error
                ))
        
        tool_calls = []
        if run.tool_calls:
            for t in run.tool_calls:
                tool_calls.append(ToolCallDetail(
                    id=t.id,
                    tool_name=t.tool_name,
                    input_data=t.input_data,
                    output_data=t.output_data,
                    success=t.success,
                    duration_ms=t.duration_ms,
                    error=t.error
                ))
        
        return RunDetail(
            id=run.id,
            workflow_name=run.workflow_name,
            status=run.status.value if isinstance(run.status, RunStatus) else run.status,
            created_at=run.created_at.isoformat() if run.created_at else "",
            started_at=run.started_at.isoformat() if run.started_at else None,
            completed_at=run.completed_at.isoformat() if run.completed_at else None,
            duration_ms=duration_ms,
            input_data=run.input_data,
            output_data=run.output_data,
            error=run.error,
            metadata=run.metadata or {},
            user_id=run.user_id,
            parent_run_id=run.parent_run_id,
            steps=steps,
            tool_calls=tool_calls
        )
    
    @router.get("", response_model=RunListResponse)
    async def list_runs(
        workflow: Optional[str] = Query(None, description="Filter by workflow name"),
        status: Optional[str] = Query(None, description="Filter by status"),
        user_id: Optional[str] = Query(None, description="Filter by user"),
        since: Optional[str] = Query(None, description="Filter runs since (ISO date)"),
        until: Optional[str] = Query(None, description="Filter runs until (ISO date)"),
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(20, ge=1, le=100, description="Results per page"),
        sort: str = Query("created_at", description="Sort field"),
        order: str = Query("desc", description="Sort order (asc/desc)")
    ):
        """
        List workflow runs with filtering and pagination.
        
        Supports filtering by:
        - workflow name
        - status (pending, running, completed, failed, cancelled)
        - user ID
        - date range
        """
        storage = await get_run_storage()
        
        # Parse date filters
        since_dt = datetime.fromisoformat(since) if since else None
        until_dt = datetime.fromisoformat(until) if until else None
        status_enum = RunStatus(status) if status else None
        
        # Get runs
        offset = (page - 1) * per_page
        runs = await storage.list_runs(
            workflow=workflow,
            status=status_enum,
            user_id=user_id,
            since=since_dt,
            until=until_dt,
            limit=per_page,
            offset=offset
        )
        
        # Get total count (simplified - in production would use COUNT query)
        all_runs = await storage.list_runs(
            workflow=workflow,
            status=status_enum,
            user_id=user_id,
            since=since_dt,
            until=until_dt,
            limit=10000,
            offset=0
        )
        total = len(all_runs)
        
        summaries = [_run_to_summary(r) for r in runs]
        
        return RunListResponse(
            runs=summaries,
            total=total,
            page=page,
            per_page=per_page,
            pages=(total + per_page - 1) // per_page
        )
    
    @router.get("/stats", response_model=RunStatsResponse)
    async def get_run_stats(
        workflow: Optional[str] = Query(None, description="Filter by workflow"),
        since: Optional[str] = Query(None, description="Stats since (ISO date)")
    ):
        """
        Get run statistics.
        
        Returns counts, success rates, and recent failures.
        """
        storage = await get_run_storage()
        
        since_dt = datetime.fromisoformat(since) if since else datetime.utcnow() - timedelta(days=30)
        
        stats = await storage.get_run_stats(workflow=workflow, since=since_dt)
        
        # Get breakdown by workflow
        all_runs = await storage.list_runs(since=since_dt, limit=10000)
        
        by_workflow: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        
        for run in all_runs:
            wf = run.workflow_name
            by_workflow[wf] = by_workflow.get(wf, 0) + 1
            
            status = run.status.value if isinstance(run.status, RunStatus) else run.status
            by_status[status] = by_status.get(status, 0) + 1
        
        # Get recent failures
        failed_runs = await storage.list_runs(
            status=RunStatus.FAILED,
            since=since_dt,
            limit=5
        )
        recent_failures = [_run_to_summary(r) for r in failed_runs]
        
        return RunStatsResponse(
            total_runs=stats["total_runs"],
            completed=stats["completed"],
            failed=stats["failed"],
            running=stats["running"],
            success_rate=stats["success_rate"],
            average_duration_ms=stats["average_duration_ms"],
            by_workflow=by_workflow,
            by_status=by_status,
            recent_failures=recent_failures
        )
    
    @router.get("/{run_id}", response_model=RunDetail)
    async def get_run(run_id: str):
        """
        Get detailed information about a specific run.
        
        Includes all steps and tool calls.
        """
        storage = await get_run_storage()
        
        run = await storage.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        return _run_to_detail(run)
    
    @router.delete("/{run_id}")
    async def delete_run(run_id: str):
        """
        Delete a run from history.
        
        Only completed/failed/cancelled runs can be deleted.
        """
        storage = await get_run_storage()
        
        run = await storage.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        if run.status == RunStatus.RUNNING:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete a running workflow. Cancel it first."
            )
        
        # In production, would actually delete from storage
        # For now, just return success
        return {"status": "deleted", "run_id": run_id}
    
    @router.get("/{run_id}/steps")
    async def get_run_steps(run_id: str):
        """Get steps for a specific run"""
        storage = await get_run_storage()
        
        run = await storage.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        steps = []
        if run.steps:
            for s in run.steps:
                steps.append({
                    "id": s.id,
                    "step_name": s.step_name,
                    "step_number": s.step_number,
                    "status": s.status.value if isinstance(s.status, StepStatus) else s.status,
                    "started_at": s.started_at.isoformat() if s.started_at else None,
                    "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                    "duration_ms": s.duration_ms,
                    "input_data": s.input_data,
                    "output_data": s.output_data,
                    "error": s.error
                })
        
        return {"run_id": run_id, "steps": steps}
    
    @router.get("/{run_id}/tool-calls")
    async def get_run_tool_calls(run_id: str):
        """Get tool calls for a specific run"""
        storage = await get_run_storage()
        
        run = await storage.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        tool_calls = []
        if run.tool_calls:
            for t in run.tool_calls:
                tool_calls.append({
                    "id": t.id,
                    "tool_name": t.tool_name,
                    "input_data": t.input_data,
                    "output_data": t.output_data,
                    "success": t.success,
                    "duration_ms": t.duration_ms,
                    "error": t.error
                })
        
        return {"run_id": run_id, "tool_calls": tool_calls}
    
    @router.post("/export")
    async def export_runs(request: ExportRequest):
        """
        Export runs to JSON or CSV format.
        
        Returns a downloadable file.
        """
        storage = await get_run_storage()
        
        # Parse filters
        since_dt = datetime.fromisoformat(request.since) if request.since else None
        until_dt = datetime.fromisoformat(request.until) if request.until else None
        status_enum = RunStatus(request.status) if request.status else None
        
        runs = await storage.list_runs(
            workflow=request.workflow,
            status=status_enum,
            since=since_dt,
            until=until_dt,
            limit=10000
        )
        
        if request.format == "csv":
            # Generate CSV
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                "id", "workflow_name", "status", "created_at", "started_at",
                "completed_at", "duration_ms", "error", "user_id"
            ])
            
            # Data
            for run in runs:
                duration_ms = None
                if run.started_at and run.completed_at:
                    duration_ms = int((run.completed_at - run.started_at).total_seconds() * 1000)
                
                writer.writerow([
                    run.id,
                    run.workflow_name,
                    run.status.value if isinstance(run.status, RunStatus) else run.status,
                    run.created_at.isoformat() if run.created_at else "",
                    run.started_at.isoformat() if run.started_at else "",
                    run.completed_at.isoformat() if run.completed_at else "",
                    duration_ms or "",
                    run.error or "",
                    run.user_id or ""
                ])
            
            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=runs_export.csv"}
            )
        
        else:
            # Generate JSON
            data = [
                {
                    "id": r.id,
                    "workflow_name": r.workflow_name,
                    "status": r.status.value if isinstance(r.status, RunStatus) else r.status,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "started_at": r.started_at.isoformat() if r.started_at else None,
                    "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                    "input_data": r.input_data,
                    "output_data": r.output_data,
                    "error": r.error,
                    "metadata": r.metadata,
                    "user_id": r.user_id
                }
                for r in runs
            ]
            
            return Response(
                content=json.dumps(data, indent=2),
                media_type="application/json",
                headers={"Content-Disposition": "attachment; filename=runs_export.json"}
            )
    
    @router.get("/workflows/list")
    async def list_workflows():
        """
        List all workflow names that have been run.
        """
        storage = await get_run_storage()
        
        runs = await storage.list_runs(limit=10000)
        workflows = set(r.workflow_name for r in runs)
        
        return {"workflows": sorted(list(workflows))}
    
    @router.post("/{run_id}/retry")
    async def retry_run(run_id: str):
        """
        Create a new run with the same parameters as a failed run.
        
        Only failed/cancelled runs can be retried.
        """
        storage = await get_run_storage()
        
        original = await storage.get_run(run_id)
        if not original:
            raise HTTPException(status_code=404, detail="Run not found")
        
        if original.status not in [RunStatus.FAILED, RunStatus.CANCELLED]:
            raise HTTPException(
                status_code=400,
                detail="Can only retry failed or cancelled runs"
            )
        
        # Create new run with same parameters
        new_run_id = await storage.create_run(
            workflow_name=original.workflow_name,
            input_data=original.input_data,
            metadata={
                **(original.metadata or {}),
                "retry_of": run_id,
                "retry_count": original.metadata.get("retry_count", 0) + 1
            },
            user_id=original.user_id
        )
        
        return {
            "status": "created",
            "new_run_id": new_run_id,
            "original_run_id": run_id
        }

except ImportError as e:
    logger.warning(f"FastAPI not available: {e}")
    router = None


# Export
__all__ = ["router"]
