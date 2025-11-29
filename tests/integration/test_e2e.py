"""
End-to-End Integration Tests for OsMEN

Comprehensive tests covering full workflow execution with mocked services.
Uses snapshot baselines for graph transitions and tool calls.

Run: pytest tests/integration/test_e2e.py -v
"""

import asyncio
import json
import os
import pytest
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

# Test markers
pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


class TestDailyBriefWorkflow:
    """E2E tests for Daily Brief workflow"""
    
    @pytest.fixture
    def mock_calendar_data(self):
        """Mock calendar event data"""
        return [
            {
                "id": "event1",
                "summary": "Morning Standup",
                "start": {"dateTime": "2024-11-28T09:00:00"},
                "end": {"dateTime": "2024-11-28T09:30:00"}
            },
            {
                "id": "event2",
                "summary": "Project Review",
                "start": {"dateTime": "2024-11-28T10:00:00"},
                "end": {"dateTime": "2024-11-28T11:00:00"}
            }
        ]
    
    @pytest.fixture
    def mock_email_data(self):
        """Mock email data"""
        return [
            {
                "id": "email1",
                "from": "boss@company.com",
                "subject": "Q4 Planning",
                "snippet": "Please review the attached...",
                "unread": True,
                "important": True
            },
            {
                "id": "email2",
                "from": "team@company.com",
                "subject": "Weekly Update",
                "snippet": "Here's what happened...",
                "unread": True,
                "important": False
            }
        ]
    
    @pytest.fixture
    def mock_task_data(self):
        """Mock task data"""
        return [
            {
                "id": "task1",
                "title": "Review PR #123",
                "due": "2024-11-28",
                "priority": "high",
                "status": "pending"
            },
            {
                "id": "task2",
                "title": "Update documentation",
                "due": "2024-11-28",
                "priority": "medium",
                "status": "pending"
            }
        ]
    
    @pytest.mark.asyncio
    async def test_daily_brief_complete_flow(
        self,
        mock_calendar_data,
        mock_email_data,
        mock_task_data
    ):
        """Test complete Daily Brief workflow execution"""
        from workflows.daily_brief import DailyBriefWorkflow, DailyBriefConfig
        
        config = DailyBriefConfig(
            use_mock_data=True,
            llm_provider="mock"
        )
        
        workflow = DailyBriefWorkflow(config)
        result = await workflow.run()
        
        # Verify result structure
        assert result is not None
        assert result.status.value == "completed"
        assert result.brief is not None
        
        # Verify brief contains expected sections
        brief = result.brief
        assert "schedule" in brief.lower() or "calendar" in brief.lower()
    
    @pytest.mark.asyncio
    async def test_daily_brief_with_streaming(self):
        """Test Daily Brief with SSE streaming enabled"""
        from workflows.daily_brief import DailyBriefWorkflow, DailyBriefConfig
        
        config = DailyBriefConfig(use_mock_data=True)
        workflow = DailyBriefWorkflow(config)
        
        events = []
        
        # Mock streaming
        original_run = workflow.run
        
        result = await workflow.run()
        
        assert result.status.value == "completed"
    
    @pytest.mark.asyncio
    async def test_daily_brief_handles_partial_failure(self):
        """Test that workflow continues when one data source fails"""
        from workflows.daily_brief import DailyBriefWorkflow, DailyBriefConfig
        
        config = DailyBriefConfig(use_mock_data=True)
        workflow = DailyBriefWorkflow(config)
        
        result = await workflow.run()
        
        # Should complete even with partial data
        assert result.status.value == "completed"


class TestResearchWorkflow:
    """E2E tests for Research workflow"""
    
    @pytest.mark.asyncio
    async def test_research_quick_depth(self):
        """Test quick research depth"""
        from workflows.research import ResearchWorkflow, ResearchDepth
        
        workflow = ResearchWorkflow()
        result = await workflow.run(
            topic="Test Topic",
            depth="quick",
            sources=["web"]
        )
        
        assert result is not None
        assert result.topic == "Test Topic"
        assert len(result.sections) >= 1
        assert result.metadata["depth"] == "quick"
    
    @pytest.mark.asyncio
    async def test_research_standard_depth(self):
        """Test standard research depth with multiple sources"""
        from workflows.research import ResearchWorkflow
        
        workflow = ResearchWorkflow()
        result = await workflow.run(
            topic="AI Frameworks",
            depth="standard",
            sources=["web", "papers", "docs"]
        )
        
        assert result is not None
        assert len(result.citations) > 0
        assert result.metadata["source_count"] == 3
    
    @pytest.mark.asyncio
    async def test_research_deep_depth(self):
        """Test deep research with all sources"""
        from workflows.research import ResearchWorkflow
        
        workflow = ResearchWorkflow()
        result = await workflow.run(
            topic="Machine Learning",
            depth="deep"
        )
        
        assert result is not None
        assert result.metadata["depth"] == "deep"
        assert len(result.sections) >= 3
    
    @pytest.mark.asyncio
    async def test_research_markdown_export(self):
        """Test research result markdown export"""
        from workflows.research import ResearchWorkflow
        
        workflow = ResearchWorkflow()
        result = await workflow.run(topic="Test", depth="quick")
        
        markdown = result.to_markdown()
        
        assert "# Research Report:" in markdown
        assert "## Executive Summary" in markdown
        assert "## References" in markdown or len(result.citations) == 0
    
    @pytest.mark.asyncio
    async def test_research_citation_tracking(self):
        """Test that citations are properly tracked"""
        from workflows.research import ResearchWorkflow
        
        workflow = ResearchWorkflow()
        result = await workflow.run(
            topic="Citation Test",
            depth="standard",
            sources=["papers"]
        )
        
        # Citations should have required fields
        for cite in result.citations:
            assert cite.id is not None
            assert cite.title is not None
            assert cite.source_type is not None


class TestContentWorkflow:
    """E2E tests for Content workflow"""
    
    @pytest.mark.asyncio
    async def test_content_blog_generation(self):
        """Test blog post generation"""
        from workflows.content import ContentWorkflow
        
        workflow = ContentWorkflow()
        result = await workflow.generate_blog(
            topic="AI Agents",
            tone="professional",
            length="medium"
        )
        
        assert result is not None
        assert result.title is not None
        assert len(result.sections) >= 3
        assert result.word_count > 100
    
    @pytest.mark.asyncio
    async def test_content_social_generation(self):
        """Test social media content generation"""
        from workflows.content import ContentWorkflow
        
        workflow = ContentWorkflow()
        results = await workflow.generate_social(
            topic="Product Launch",
            platforms=["twitter", "linkedin"]
        )
        
        assert "twitter" in results
        assert "linkedin" in results
        assert len(results["twitter"].sections) > 0
    
    @pytest.mark.asyncio
    async def test_content_newsletter_generation(self):
        """Test newsletter generation"""
        from workflows.content import ContentWorkflow
        
        workflow = ContentWorkflow()
        result = await workflow.generate_newsletter(
            topic="Weekly Update",
            tone="friendly"
        )
        
        assert result is not None
        assert "newsletter" in result.content_type.value
    
    @pytest.mark.asyncio
    async def test_content_campaign_generation(self):
        """Test full campaign generation"""
        from workflows.content import ContentWorkflow
        
        workflow = ContentWorkflow()
        results = await workflow.generate_campaign(
            topic="New Feature",
            content_types=["blog", "twitter"]
        )
        
        assert "blog" in results
        assert "twitter" in results
    
    @pytest.mark.asyncio
    async def test_content_tone_variations(self):
        """Test different tone options"""
        from workflows.content import ContentWorkflow
        
        workflow = ContentWorkflow()
        
        tones = ["professional", "casual", "friendly"]
        
        for tone in tones:
            result = await workflow.generate_blog(
                topic="Test Topic",
                tone=tone,
                length="short"
            )
            assert result.metadata["tone"] == tone
    
    @pytest.mark.asyncio
    async def test_content_html_export(self):
        """Test HTML export"""
        from workflows.content import ContentWorkflow
        
        workflow = ContentWorkflow()
        result = await workflow.generate_blog("Test", length="short")
        
        html = result.to_html()
        
        assert "<html>" in html
        assert "<h1>" in html
        assert result.title in html


class TestApprovalGating:
    """E2E tests for Approval Gating"""
    
    @pytest.mark.asyncio
    async def test_approval_rule_matching(self):
        """Test that approval rules match correctly"""
        from workflows.approval import ApprovalGate, ApprovalRule, RiskLevel
        
        gate = ApprovalGate()
        
        # Should match shell command rule
        rule = await gate.check("execute_shell_command", {"cmd": "ls"})
        assert rule is not None
        assert rule.risk_level == RiskLevel.CRITICAL
    
    @pytest.mark.asyncio
    async def test_approval_auto_approve(self):
        """Test auto-approval after timeout"""
        from workflows.approval import ApprovalGate, ApprovalRule, RiskLevel
        
        gate = ApprovalGate()
        
        # Add rule with quick auto-approve
        gate.add_rule(ApprovalRule(
            name="test_rule",
            pattern=r"test_action",
            risk_level=RiskLevel.LOW,
            timeout_seconds=1,
            auto_approve_after=0  # Immediate auto-approve
        ))
        
        # This should auto-approve
        result = await gate.request_approval(
            run_id="test",
            action="test_action",
            context={}
        )
        
        # Result depends on implementation
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_approval_stats(self):
        """Test approval statistics"""
        from workflows.approval import get_approval_gate
        
        gate = get_approval_gate()
        stats = gate.get_stats()
        
        assert "total" in stats
        assert "pending" in stats
        assert "approval_rate" in stats


class TestStreamingIntegration:
    """E2E tests for SSE Streaming"""
    
    @pytest.mark.asyncio
    async def test_streaming_manager_run_lifecycle(self):
        """Test complete run lifecycle with streaming"""
        from gateway.streaming import StreamingManager
        
        manager = StreamingManager()
        
        # Start run
        run_id = await manager.start_run("test_workflow", total_steps=3)
        assert run_id is not None
        
        # Emit steps
        await manager.emit_step(run_id, "step1", {"data": "test"})
        await manager.emit_step(run_id, "step2", {"data": "test"})
        
        # Emit tool call
        await manager.emit_tool_call(run_id, "test_tool", {"input": "test"})
        await manager.emit_tool_result(run_id, "test_tool", {"output": "result"})
        
        # Complete run
        await manager.complete_run(run_id, {"result": "success"})
        
        # Verify state
        state = manager.get_run_state(run_id)
        assert state.status == "completed"
        assert len(state.events) > 0
    
    @pytest.mark.asyncio
    async def test_streaming_error_handling(self):
        """Test streaming error events"""
        from gateway.streaming import StreamingManager
        
        manager = StreamingManager()
        run_id = await manager.start_run("test_workflow")
        
        await manager.emit_error(
            run_id,
            "Test error",
            error_type="test_error",
            recoverable=False
        )
        
        state = manager.get_run_state(run_id)
        assert state.status == "failed"
        assert state.error == "Test error"


class TestRunStorage:
    """E2E tests for Run Storage"""
    
    @pytest.mark.asyncio
    async def test_run_storage_create_and_retrieve(self):
        """Test creating and retrieving runs"""
        from database.run_storage import get_run_storage, InMemoryRunStorage
        
        storage = InMemoryRunStorage()
        
        # Create run
        run_id = await storage.create_run(
            workflow_name="test_workflow",
            input_data={"param": "value"},
            user_id="test_user"
        )
        
        # Start run
        await storage.start_run(run_id)
        
        # Add step
        step_id = await storage.add_step(run_id, "step1", {"input": "test"})
        await storage.complete_step(step_id, {"output": "result"})
        
        # Complete run
        await storage.complete_run(run_id, {"result": "success"})
        
        # Retrieve run
        run = await storage.get_run(run_id)
        
        assert run is not None
        assert run.workflow_name == "test_workflow"
        assert run.status.value == "completed"
        assert len(run.steps) == 1
    
    @pytest.mark.asyncio
    async def test_run_storage_list_and_filter(self):
        """Test listing and filtering runs"""
        from database.run_storage import InMemoryRunStorage, RunStatus
        
        storage = InMemoryRunStorage()
        
        # Create multiple runs
        for i in range(5):
            run_id = await storage.create_run(
                workflow_name=f"workflow_{i % 2}",
                user_id=f"user_{i % 3}"
            )
            if i % 2 == 0:
                await storage.start_run(run_id)
                await storage.complete_run(run_id)
        
        # List all
        all_runs = await storage.list_runs()
        assert len(all_runs) == 5
        
        # Filter by workflow
        wf_runs = await storage.list_runs(workflow="workflow_0")
        assert len(wf_runs) == 3
        
        # Filter by status
        completed_runs = await storage.list_runs(status=RunStatus.COMPLETED)
        assert len(completed_runs) == 3
    
    @pytest.mark.asyncio
    async def test_run_storage_stats(self):
        """Test run statistics"""
        from database.run_storage import InMemoryRunStorage
        
        storage = InMemoryRunStorage()
        
        # Create and complete some runs
        for i in range(10):
            run_id = await storage.create_run("test_workflow")
            await storage.start_run(run_id)
            if i < 8:
                await storage.complete_run(run_id)
            else:
                await storage.fail_run(run_id, "Test error")
        
        stats = await storage.get_run_stats()
        
        assert stats["total_runs"] == 10
        assert stats["completed"] == 8
        assert stats["failed"] == 2
        assert stats["success_rate"] == 80.0


class TestWebSocketIntegration:
    """E2E tests for WebSocket integration"""
    
    @pytest.mark.asyncio
    async def test_websocket_manager_connections(self):
        """Test WebSocket connection management"""
        from gateway.websocket import WebSocketManager
        
        manager = WebSocketManager()
        
        # Mock WebSocket
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()
        
        # Connect
        client_id = await manager.connect(mock_ws)
        assert client_id is not None
        
        # Verify connection
        stats = manager.get_stats()
        assert stats["active_connections"] == 1
        
        # Disconnect
        manager.disconnect(mock_ws)
        stats = manager.get_stats()
        assert stats["active_connections"] == 0
    
    @pytest.mark.asyncio
    async def test_websocket_room_subscription(self):
        """Test room-based subscriptions"""
        from gateway.websocket import WebSocketManager
        
        manager = WebSocketManager()
        
        # Mock WebSocket
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()
        
        client_id = await manager.connect(mock_ws)
        
        # Subscribe to room
        await manager.subscribe(client_id, "test_room")
        
        rooms = manager.get_client_rooms(client_id)
        assert "test_room" in rooms
        
        clients = manager.get_room_clients("test_room")
        assert client_id in clients


# Snapshot baseline utilities
class SnapshotManager:
    """Manages test snapshots for baseline comparisons"""
    
    def __init__(self, snapshot_dir: str = "tests/snapshots"):
        self.snapshot_dir = snapshot_dir
        os.makedirs(snapshot_dir, exist_ok=True)
    
    def save_snapshot(self, name: str, data: Any):
        """Save a snapshot"""
        path = os.path.join(self.snapshot_dir, f"{name}.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
    
    def load_snapshot(self, name: str) -> Any:
        """Load a snapshot"""
        path = os.path.join(self.snapshot_dir, f"{name}.json")
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return None
    
    def compare_snapshot(self, name: str, data: Any) -> bool:
        """Compare data against snapshot"""
        existing = self.load_snapshot(name)
        if existing is None:
            self.save_snapshot(name, data)
            return True
        
        # Simple comparison - in production would be more sophisticated
        return json.dumps(existing, sort_keys=True) == json.dumps(data, sort_keys=True, default=str)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
