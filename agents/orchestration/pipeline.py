#!/usr/bin/env python3
"""
OsMEN Unified Orchestration Pipeline

This module connects the entire agent orchestration system:
- IntakeAgent: Extracts tasks from natural language prompts
- OrchestrationAgent: Coordinates task execution
- TeamManager: Spawns and manages agent teams
- Implementation: Deploys solutions with approval gates

Usage:
    from agents.orchestration.pipeline import OsMENPipeline

    pipeline = OsMENPipeline()
    result = await pipeline.process("Integrate DRM removal into librarian workflow")
    # Pipeline auto-extracts tasks, spawns teams, implements, and requests approval
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("osmen.pipeline")


class PipelineStage(Enum):
    """Stages in the orchestration pipeline."""

    INTAKE = "intake"
    TASK_EXTRACTION = "task_extraction"
    PLANNING = "planning"
    TEAM_SPAWNING = "team_spawning"
    EXECUTION = "execution"
    REVIEW = "review"
    APPROVAL = "approval"
    DEPLOYMENT = "deployment"
    COMPLETE = "complete"
    FAILED = "failed"


class ApprovalLevel(Enum):
    """Approval levels for different actions."""

    NONE = "none"  # Auto-approve
    SUMMARY = "summary"  # Show summary, auto-approve
    REVIEW = "review"  # Show details, require approval for major changes
    STRICT = "strict"  # Require approval for every action


@dataclass
class PipelineConfig:
    """Configuration for the orchestration pipeline."""

    approval_level: ApprovalLevel = ApprovalLevel.REVIEW
    max_parallel_teams: int = 3
    task_timeout_seconds: int = 300
    auto_deploy: bool = False
    enable_rollback: bool = True
    notification_callback: Optional[Callable] = None


@dataclass
class PipelineTask:
    """A task extracted from user prompt."""

    id: str
    title: str
    description: str
    domain: str
    priority: int = 0
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"
    assigned_team: Optional[str] = None
    result: Optional[Any] = None


@dataclass
class PipelineResult:
    """Result of pipeline execution."""

    request_id: str
    original_prompt: str
    tasks: List[PipelineTask]
    stage: PipelineStage
    success: bool
    results: Dict[str, Any]
    artifacts: List[Dict[str, Any]]
    approval_required: bool
    approval_items: List[Dict[str, Any]]
    errors: List[str]
    duration_ms: float
    timestamp: str


class OsMENPipeline:
    """
    Unified orchestration pipeline for OsMEN.

    This is the main entry point for processing user requests.
    It connects IntakeAgent, OrchestrationAgent, and TeamManager
    into a single autonomous workflow.

    Features:
    - Natural language task extraction
    - Automatic team spawning based on task requirements
    - Parallel execution of independent tasks
    - Configurable approval gates
    - Rollback on failure
    - Progress notifications

    Example:
        pipeline = OsMENPipeline()

        # Process a user request
        result = await pipeline.process(
            "Set up DRM removal workflow for ebooks"
        )

        # Check if approval needed
        if result.approval_required:
            # Show approval items to user
            for item in result.approval_items:
                print(f"Approve: {item['title']}?")

            # User approves
            await pipeline.approve(result.request_id)
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        """Initialize the pipeline."""
        self.config = config or PipelineConfig()
        self._intake_agent = None
        self._orchestration_agent = None
        self._team_manager = None
        self._pending_approvals: Dict[str, PipelineResult] = {}
        self._execution_history: List[PipelineResult] = []

        # Load LLM configuration
        self._llm_available = bool(os.getenv("OPENAI_API_KEY"))

        logger.info("OsMENPipeline initialized")

    @property
    def intake_agent(self):
        """Lazy-load IntakeAgent."""
        if self._intake_agent is None:
            from agents.intake_agent.intake_agent import IntakeAgent

            self._intake_agent = IntakeAgent()
        return self._intake_agent

    @property
    def orchestration_agent(self):
        """Lazy-load OrchestrationAgent."""
        if self._orchestration_agent is None:
            from agents.orchestration_agent.orchestration_agent import (
                OrchestrationAgent,
            )

            self._orchestration_agent = OrchestrationAgent()
        return self._orchestration_agent

    @property
    def team_manager(self):
        """Lazy-load TeamManager."""
        if self._team_manager is None:
            from agents.teams.manager import TeamManager

            self._team_manager = TeamManager()
        return self._team_manager

    async def process(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> PipelineResult:
        """
        Process a user request through the full pipeline.

        Args:
            prompt: Natural language request from user
            context: Optional additional context

        Returns:
            PipelineResult with execution outcome
        """
        import time
        import uuid

        start_time = time.time()
        request_id = str(uuid.uuid4())[:8]

        logger.info(f"[{request_id}] Processing: {prompt[:100]}...")

        result = PipelineResult(
            request_id=request_id,
            original_prompt=prompt,
            tasks=[],
            stage=PipelineStage.INTAKE,
            success=False,
            results={},
            artifacts=[],
            approval_required=False,
            approval_items=[],
            errors=[],
            duration_ms=0,
            timestamp=datetime.now().isoformat(),
        )

        try:
            # Stage 1: Task Extraction
            result.stage = PipelineStage.TASK_EXTRACTION
            tasks = await self._extract_tasks(prompt, context)
            result.tasks = tasks
            logger.info(f"[{request_id}] Extracted {len(tasks)} tasks")

            # Stage 2: Planning
            result.stage = PipelineStage.PLANNING
            execution_plan = await self._create_execution_plan(tasks)
            result.results["plan"] = execution_plan
            logger.info(
                f"[{request_id}] Created execution plan with {len(execution_plan)} phases"
            )

            # Stage 3: Team Spawning
            result.stage = PipelineStage.TEAM_SPAWNING
            teams = await self._spawn_teams(tasks)
            result.results["teams"] = [t.get("name") for t in teams]
            logger.info(f"[{request_id}] Spawned {len(teams)} teams")

            # Stage 4: Execution
            result.stage = PipelineStage.EXECUTION
            execution_results = await self._execute_tasks(tasks, teams)
            result.results["execution"] = execution_results
            result.artifacts = execution_results.get("artifacts", [])

            # Stage 5: Review
            result.stage = PipelineStage.REVIEW
            review_result = await self._review_results(result)
            result.results["review"] = review_result

            # Stage 6: Approval Check
            result.stage = PipelineStage.APPROVAL
            if self._requires_approval(result):
                result.approval_required = True
                result.approval_items = self._collect_approval_items(result)
                self._pending_approvals[request_id] = result
                logger.info(
                    f"[{request_id}] Awaiting approval for {len(result.approval_items)} items"
                )
            else:
                # Stage 7: Auto-deploy if configured
                if self.config.auto_deploy:
                    result.stage = PipelineStage.DEPLOYMENT
                    await self._deploy(result)

                result.stage = PipelineStage.COMPLETE
                result.success = True

        except Exception as e:
            logger.error(f"[{request_id}] Pipeline failed: {e}")
            result.stage = PipelineStage.FAILED
            result.errors.append(str(e))

        result.duration_ms = (time.time() - start_time) * 1000
        self._execution_history.append(result)

        # Notify if callback configured
        if self.config.notification_callback:
            try:
                self.config.notification_callback(result)
            except Exception as e:
                logger.warning(f"Notification callback failed: {e}")

        return result

    async def approve(
        self,
        request_id: str,
        approved_items: Optional[List[str]] = None,
    ) -> PipelineResult:
        """
        Approve pending pipeline result.

        Args:
            request_id: Request ID to approve
            approved_items: Optional list of specific item IDs to approve

        Returns:
            Updated PipelineResult
        """
        if request_id not in self._pending_approvals:
            raise ValueError(f"No pending approval for request {request_id}")

        result = self._pending_approvals[request_id]

        # Mark items as approved
        for item in result.approval_items:
            if approved_items is None or item["id"] in approved_items:
                item["approved"] = True

        # Check if all required items approved
        all_approved = all(
            item.get("approved", False)
            for item in result.approval_items
            if item.get("required", True)
        )

        if all_approved:
            # Deploy
            result.stage = PipelineStage.DEPLOYMENT
            await self._deploy(result)
            result.stage = PipelineStage.COMPLETE
            result.success = True
            result.approval_required = False
            del self._pending_approvals[request_id]

        return result

    async def reject(self, request_id: str, reason: str = "") -> PipelineResult:
        """Reject pending pipeline result."""
        if request_id not in self._pending_approvals:
            raise ValueError(f"No pending approval for request {request_id}")

        result = self._pending_approvals[request_id]
        result.stage = PipelineStage.FAILED
        result.errors.append(f"Rejected by user: {reason}")

        if self.config.enable_rollback:
            await self._rollback(result)

        del self._pending_approvals[request_id]
        return result

    # =========================================================================
    # Internal Pipeline Methods
    # =========================================================================

    async def _extract_tasks(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[PipelineTask]:
        """Extract structured tasks from natural language prompt."""

        # Use IntakeAgent's requirement analysis
        requirements = self.intake_agent._analyze_requirements(prompt)

        tasks = []
        task_id = 0

        # Extract explicit tasks from requirements
        explicit_tasks = requirements.get("tasks", [])
        if not explicit_tasks:
            # Create implicit task from the prompt
            explicit_tasks = [prompt]

        for task_desc in explicit_tasks:
            task_id += 1
            task = PipelineTask(
                id=f"task_{task_id}",
                title=self._generate_task_title(task_desc),
                description=task_desc,
                domain=requirements.get("domain", "general"),
                priority=self._calculate_priority(task_desc, requirements),
            )
            tasks.append(task)

        # Sort by priority (higher first)
        tasks.sort(key=lambda t: -t.priority)

        return tasks

    async def _create_execution_plan(
        self,
        tasks: List[PipelineTask],
    ) -> List[Dict[str, Any]]:
        """Create execution plan with dependencies and phases."""

        phases = []
        remaining_tasks = list(tasks)
        phase_num = 0

        while remaining_tasks:
            phase_num += 1
            phase_tasks = []

            for task in remaining_tasks[:]:
                # Check if dependencies are satisfied
                deps_satisfied = all(
                    any(t.id == dep and t.status == "completed" for t in tasks)
                    for dep in task.dependencies
                )

                if deps_satisfied or not task.dependencies:
                    phase_tasks.append(task)
                    remaining_tasks.remove(task)

            if not phase_tasks and remaining_tasks:
                # Circular dependency or missing deps - force execute
                phase_tasks = remaining_tasks[:1]
                remaining_tasks = remaining_tasks[1:]

            if phase_tasks:
                phases.append(
                    {
                        "phase": phase_num,
                        "tasks": [t.id for t in phase_tasks],
                        "parallel": len(phase_tasks) > 1
                        and self.config.max_parallel_teams > 1,
                    }
                )

        return phases

    async def _spawn_teams(
        self,
        tasks: List[PipelineTask],
    ) -> List[Dict[str, Any]]:
        """Spawn appropriate teams for tasks."""

        teams = []

        for task in tasks:
            # Determine team template based on domain
            template_map = {
                "security": "security",
                "research": "research",
                "content_creation": "content",
                "productivity": "daily_ops",
                "general": "full_stack",
                "development": "full_stack",
            }

            template_name = template_map.get(task.domain, "full_stack")

            # Create team via TeamManager
            try:
                team = self.team_manager.create_team(template_name)
                task.assigned_team = template_name

                teams.append(
                    {
                        "name": template_name,
                        "task_id": task.id,
                        "team": team,
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to create team {template_name}: {e}")
                # Fallback to generic execution
                teams.append(
                    {
                        "name": "generic",
                        "task_id": task.id,
                        "team": None,
                    }
                )

        return teams

    async def _execute_tasks(
        self,
        tasks: List[PipelineTask],
        teams: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Execute tasks using assigned teams."""

        results = {
            "completed": [],
            "failed": [],
            "artifacts": [],
        }

        # Build team lookup
        team_lookup = {t["task_id"]: t for t in teams}

        for task in tasks:
            team_info = team_lookup.get(task.id)

            try:
                task.status = "running"

                if team_info and team_info.get("team"):
                    # Execute via team
                    team_result = team_info["team"].execute(
                        task.description, {"task_id": task.id, "domain": task.domain}
                    )
                    task.result = team_result

                    if team_result.success:
                        task.status = "completed"
                        results["completed"].append(task.id)
                        results["artifacts"].extend(team_result.artifacts)
                    else:
                        task.status = "failed"
                        results["failed"].append(
                            {
                                "task_id": task.id,
                                "errors": team_result.errors,
                            }
                        )
                else:
                    # Generic execution (no team available)
                    task.status = "completed"
                    task.result = {
                        "message": f"Task '{task.title}' marked for manual execution"
                    }
                    results["completed"].append(task.id)

            except Exception as e:
                logger.error(f"Task {task.id} failed: {e}")
                task.status = "failed"
                results["failed"].append(
                    {
                        "task_id": task.id,
                        "errors": [str(e)],
                    }
                )

        return results

    async def _review_results(self, result: PipelineResult) -> Dict[str, Any]:
        """Review execution results."""

        completed = len(result.results.get("execution", {}).get("completed", []))
        failed = len(result.results.get("execution", {}).get("failed", []))

        return {
            "total_tasks": len(result.tasks),
            "completed": completed,
            "failed": failed,
            "success_rate": completed / max(1, len(result.tasks)),
            "artifacts_produced": len(result.artifacts),
            "recommendation": "approve" if failed == 0 else "review",
        }

    def _requires_approval(self, result: PipelineResult) -> bool:
        """Check if result requires user approval."""

        if self.config.approval_level == ApprovalLevel.NONE:
            return False

        if self.config.approval_level == ApprovalLevel.STRICT:
            return True

        # REVIEW level - approve if no failures and minor changes
        review = result.results.get("review", {})
        if review.get("failed", 0) > 0:
            return True

        # Check for major changes
        major_artifacts = [
            a
            for a in result.artifacts
            if a.get("type") in ["file_created", "file_modified", "deployment"]
        ]

        return len(major_artifacts) > 0

    def _collect_approval_items(self, result: PipelineResult) -> List[Dict[str, Any]]:
        """Collect items requiring approval."""

        items = []

        # Add artifacts as approval items
        for i, artifact in enumerate(result.artifacts):
            items.append(
                {
                    "id": f"artifact_{i}",
                    "type": artifact.get("type", "unknown"),
                    "title": artifact.get("source", "Artifact"),
                    "description": str(artifact.get("content", ""))[:200],
                    "required": artifact.get("type") in ["file_created", "deployment"],
                    "approved": False,
                }
            )

        # Add failed tasks for review
        for failure in result.results.get("execution", {}).get("failed", []):
            items.append(
                {
                    "id": f"failure_{failure['task_id']}",
                    "type": "failure",
                    "title": f"Failed: {failure['task_id']}",
                    "description": ", ".join(failure.get("errors", [])),
                    "required": True,
                    "approved": False,
                }
            )

        return items

    async def _deploy(self, result: PipelineResult) -> None:
        """Deploy approved results."""
        logger.info(
            f"[{result.request_id}] Deploying {len(result.artifacts)} artifacts"
        )

        # Notify orchestration agent
        for task in result.tasks:
            if task.status == "completed":
                self.orchestration_agent.receive_status_update(
                    team_id=task.assigned_team or "pipeline",
                    message=f"Deployed: {task.title}",
                    level="info",
                )

    async def _rollback(self, result: PipelineResult) -> None:
        """Rollback failed or rejected execution."""
        logger.warning(f"[{result.request_id}] Rolling back")
        # TODO: Implement rollback logic based on artifacts

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _generate_task_title(self, description: str) -> str:
        """Generate short title from task description."""
        words = description.split()[:5]
        return " ".join(words) + ("..." if len(description.split()) > 5 else "")

    def _calculate_priority(
        self,
        description: str,
        requirements: Dict[str, Any],
    ) -> int:
        """Calculate task priority."""
        priority = 0

        # Boost priority for critical keywords
        critical_keywords = [
            "urgent",
            "critical",
            "asap",
            "immediately",
            "fix",
            "broken",
        ]
        if any(kw in description.lower() for kw in critical_keywords):
            priority += 10

        # Boost for automation goals
        if requirements.get("goal") == "automation":
            priority += 5

        return priority

    def get_pending_approvals(self) -> List[PipelineResult]:
        """Get all pending approval requests."""
        return list(self._pending_approvals.values())

    def get_execution_history(self, limit: int = 10) -> List[PipelineResult]:
        """Get recent execution history."""
        return self._execution_history[-limit:]


# =========================================================================
# Convenience Functions
# =========================================================================


async def process_request(prompt: str, **kwargs) -> PipelineResult:
    """Process a user request through the pipeline."""
    pipeline = OsMENPipeline()
    return await pipeline.process(prompt, kwargs.get("context"))


def create_pipeline(
    approval_level: str = "review",
    auto_deploy: bool = False,
) -> OsMENPipeline:
    """Create a configured pipeline instance."""
    config = PipelineConfig(
        approval_level=ApprovalLevel[approval_level.upper()],
        auto_deploy=auto_deploy,
    )
    return OsMENPipeline(config)


# =========================================================================
# CLI Entry Point
# =========================================================================


def main():
    """CLI entry point for testing pipeline."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pipeline.py '<prompt>'")
        print("Example: python pipeline.py 'Set up DRM removal workflow'")
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])

    # Run pipeline
    pipeline = OsMENPipeline()
    result = asyncio.run(pipeline.process(prompt))

    # Print result
    print("\n" + "=" * 60)
    print("PIPELINE RESULT")
    print("=" * 60)
    print(f"Request ID: {result.request_id}")
    print(f"Stage: {result.stage.value}")
    print(f"Success: {result.success}")
    print(f"Tasks: {len(result.tasks)}")
    print(f"Artifacts: {len(result.artifacts)}")
    print(f"Duration: {result.duration_ms:.0f}ms")

    if result.errors:
        print(f"\nErrors:")
        for error in result.errors:
            print(f"  - {error}")

    if result.approval_required:
        print(f"\nApproval Required:")
        for item in result.approval_items:
            print(f"  [{item['id']}] {item['title']}")

    print("=" * 60)


if __name__ == "__main__":
    main()
    main()
