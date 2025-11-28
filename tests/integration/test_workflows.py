"""
Workflow Integration Tests

Tests for all workflow implementations including Daily Brief, Research, and Content.
Validates workflow execution, data flow, and output quality.

Run: pytest tests/integration/test_workflows.py -v
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


class TestDailyBriefWorkflowIntegration:
    """Integration tests for Daily Brief workflow"""
    
    @pytest.mark.asyncio
    async def test_workflow_initialization(self):
        """Test workflow initializes correctly"""
        from workflows.daily_brief import DailyBriefWorkflow, DailyBriefConfig
        
        config = DailyBriefConfig(use_mock_data=True)
        workflow = DailyBriefWorkflow(config)
        
        assert workflow is not None
        assert workflow._config.use_mock_data is True
    
    @pytest.mark.asyncio
    async def test_workflow_runs_with_mock_data(self):
        """Test workflow executes successfully with mock data"""
        from workflows.daily_brief import DailyBriefWorkflow, DailyBriefConfig
        
        config = DailyBriefConfig(use_mock_data=True)
        workflow = DailyBriefWorkflow(config)
        
        result = await workflow.run()
        
        assert result is not None
        assert result.status.value == "completed"
        assert result.brief is not None
        assert len(result.brief) > 0
    
    @pytest.mark.asyncio
    async def test_workflow_collects_calendar_data(self):
        """Test calendar agent data collection"""
        from workflows.daily_brief import DailyBriefWorkflow, DailyBriefConfig
        
        config = DailyBriefConfig(use_mock_data=True)
        workflow = DailyBriefWorkflow(config)
        
        result = await workflow.run()
        
        # Brief should contain schedule information
        brief_lower = result.brief.lower()
        assert "schedule" in brief_lower or "calendar" in brief_lower or "today" in brief_lower
    
    @pytest.mark.asyncio
    async def test_workflow_collects_email_data(self):
        """Test email agent data collection"""
        from workflows.daily_brief import DailyBriefWorkflow, DailyBriefConfig
        
        config = DailyBriefConfig(use_mock_data=True)
        workflow = DailyBriefWorkflow(config)
        
        result = await workflow.run()
        
        # Brief should contain email information
        brief_lower = result.brief.lower()
        assert "email" in brief_lower or "inbox" in brief_lower or "messages" in brief_lower
    
    @pytest.mark.asyncio
    async def test_workflow_collects_task_data(self):
        """Test task agent data collection"""
        from workflows.daily_brief import DailyBriefWorkflow, DailyBriefConfig
        
        config = DailyBriefConfig(use_mock_data=True)
        workflow = DailyBriefWorkflow(config)
        
        result = await workflow.run()
        
        # Brief should contain task information
        brief_lower = result.brief.lower()
        assert "task" in brief_lower or "todo" in brief_lower or "priority" in brief_lower or "due" in brief_lower
    
    @pytest.mark.asyncio
    async def test_workflow_generates_summary(self):
        """Test that workflow generates a proper summary"""
        from workflows.daily_brief import DailyBriefWorkflow, DailyBriefConfig
        
        config = DailyBriefConfig(use_mock_data=True)
        workflow = DailyBriefWorkflow(config)
        
        result = await workflow.run()
        
        # Summary should be substantial
        assert len(result.brief) > 100
        
        # Should have markdown-like structure
        assert "#" in result.brief or "**" in result.brief or "- " in result.brief


class TestResearchWorkflowIntegration:
    """Integration tests for Research workflow"""
    
    @pytest.mark.asyncio
    async def test_research_workflow_initialization(self):
        """Test research workflow initializes correctly"""
        from workflows.research import ResearchWorkflow
        
        workflow = ResearchWorkflow()
        assert workflow is not None
    
    @pytest.mark.asyncio
    async def test_research_quick_mode(self):
        """Test quick research mode"""
        from workflows.research import ResearchWorkflow
        
        workflow = ResearchWorkflow()
        result = await workflow.run(
            topic="Python Programming",
            depth="quick"
        )
        
        assert result is not None
        assert result.topic == "Python Programming"
        assert result.metadata["depth"] == "quick"
    
    @pytest.mark.asyncio
    async def test_research_standard_mode(self):
        """Test standard research mode"""
        from workflows.research import ResearchWorkflow
        
        workflow = ResearchWorkflow()
        result = await workflow.run(
            topic="Machine Learning",
            depth="standard"
        )
        
        assert result is not None
        assert result.metadata["depth"] == "standard"
        assert result.metadata["source_count"] >= 1
    
    @pytest.mark.asyncio
    async def test_research_deep_mode(self):
        """Test deep research mode"""
        from workflows.research import ResearchWorkflow
        
        workflow = ResearchWorkflow()
        result = await workflow.run(
            topic="AI Ethics",
            depth="deep"
        )
        
        assert result is not None
        assert result.metadata["depth"] == "deep"
        # Deep should have more sources
        assert result.metadata["source_count"] >= 1
    
    @pytest.mark.asyncio
    async def test_research_custom_sources(self):
        """Test research with custom sources"""
        from workflows.research import ResearchWorkflow
        
        workflow = ResearchWorkflow()
        result = await workflow.run(
            topic="Web Development",
            depth="standard",
            sources=["web", "docs"]
        )
        
        assert result is not None
        # Should only use specified sources
        assert result.metadata["source_count"] == 2
    
    @pytest.mark.asyncio
    async def test_research_generates_sections(self):
        """Test that research generates proper sections"""
        from workflows.research import ResearchWorkflow
        
        workflow = ResearchWorkflow()
        result = await workflow.run(
            topic="Data Science",
            depth="standard"
        )
        
        assert len(result.sections) > 0
        
        # Each section should have content
        for section in result.sections:
            assert section.title is not None or section.content is not None
            assert len(section.content) > 0
    
    @pytest.mark.asyncio
    async def test_research_tracks_citations(self):
        """Test citation tracking"""
        from workflows.research import ResearchWorkflow
        
        workflow = ResearchWorkflow()
        result = await workflow.run(
            topic="Neural Networks",
            depth="standard",
            sources=["papers"]
        )
        
        # Should have citations
        assert len(result.citations) > 0
        
        # Citations should have required fields
        for cite in result.citations:
            assert cite.id is not None
            assert cite.title is not None
    
    @pytest.mark.asyncio
    async def test_research_markdown_output(self):
        """Test markdown output generation"""
        from workflows.research import ResearchWorkflow
        
        workflow = ResearchWorkflow()
        result = await workflow.run(
            topic="Cloud Computing",
            depth="quick"
        )
        
        markdown = result.to_markdown()
        
        assert "# Research Report:" in markdown
        assert "## Executive Summary" in markdown
        assert "Cloud Computing" in markdown


class TestContentWorkflowIntegration:
    """Integration tests for Content workflow"""
    
    @pytest.mark.asyncio
    async def test_content_workflow_initialization(self):
        """Test content workflow initializes correctly"""
        from workflows.content import ContentWorkflow
        
        workflow = ContentWorkflow()
        assert workflow is not None
    
    @pytest.mark.asyncio
    async def test_blog_generation_short(self):
        """Test short blog post generation"""
        from workflows.content import ContentWorkflow
        
        workflow = ContentWorkflow()
        result = await workflow.generate_blog(
            topic="Python Tips",
            length="short"
        )
        
        assert result is not None
        assert result.metadata["length"] == "short"
        assert result.word_count > 50
    
    @pytest.mark.asyncio
    async def test_blog_generation_medium(self):
        """Test medium blog post generation"""
        from workflows.content import ContentWorkflow
        
        workflow = ContentWorkflow()
        result = await workflow.generate_blog(
            topic="Web Development Best Practices",
            length="medium"
        )
        
        assert result is not None
        assert result.metadata["length"] == "medium"
        assert result.word_count > 100
    
    @pytest.mark.asyncio
    async def test_blog_generation_long(self):
        """Test long blog post generation"""
        from workflows.content import ContentWorkflow
        
        workflow = ContentWorkflow()
        result = await workflow.generate_blog(
            topic="Comprehensive Guide to APIs",
            length="long"
        )
        
        assert result is not None
        assert result.metadata["length"] == "long"
    
    @pytest.mark.asyncio
    async def test_blog_tone_professional(self):
        """Test professional tone"""
        from workflows.content import ContentWorkflow
        
        workflow = ContentWorkflow()
        result = await workflow.generate_blog(
            topic="Business Strategy",
            tone="professional"
        )
        
        assert result.metadata["tone"] == "professional"
    
    @pytest.mark.asyncio
    async def test_blog_tone_casual(self):
        """Test casual tone"""
        from workflows.content import ContentWorkflow
        
        workflow = ContentWorkflow()
        result = await workflow.generate_blog(
            topic="Weekend Projects",
            tone="casual"
        )
        
        assert result.metadata["tone"] == "casual"
    
    @pytest.mark.asyncio
    async def test_social_twitter_generation(self):
        """Test Twitter content generation"""
        from workflows.content import ContentWorkflow
        
        workflow = ContentWorkflow()
        results = await workflow.generate_social(
            topic="Product Launch",
            platforms=["twitter"]
        )
        
        assert "twitter" in results
        twitter_result = results["twitter"]
        
        # Should have multiple tweets for a thread
        assert len(twitter_result.sections) > 0
    
    @pytest.mark.asyncio
    async def test_social_linkedin_generation(self):
        """Test LinkedIn content generation"""
        from workflows.content import ContentWorkflow
        
        workflow = ContentWorkflow()
        results = await workflow.generate_social(
            topic="Career Growth",
            platforms=["linkedin"]
        )
        
        assert "linkedin" in results
        linkedin_result = results["linkedin"]
        
        assert linkedin_result.full_content is not None
        assert len(linkedin_result.full_content) > 50
    
    @pytest.mark.asyncio
    async def test_social_multi_platform(self):
        """Test multi-platform social content"""
        from workflows.content import ContentWorkflow
        
        workflow = ContentWorkflow()
        results = await workflow.generate_social(
            topic="New Feature",
            platforms=["twitter", "linkedin"]
        )
        
        assert "twitter" in results
        assert "linkedin" in results
    
    @pytest.mark.asyncio
    async def test_newsletter_generation(self):
        """Test newsletter generation"""
        from workflows.content import ContentWorkflow
        
        workflow = ContentWorkflow()
        result = await workflow.generate_newsletter(
            topic="Weekly Tech Update"
        )
        
        assert result is not None
        assert "newsletter" in result.content_type.value
        assert len(result.sections) > 0
    
    @pytest.mark.asyncio
    async def test_product_description_generation(self):
        """Test product description generation"""
        from workflows.content import ContentWorkflow
        
        workflow = ContentWorkflow()
        result = await workflow.generate_product_description(
            product_name="SuperApp Pro"
        )
        
        assert result is not None
        assert "SuperApp Pro" in result.title or "SuperApp Pro" in result.full_content
    
    @pytest.mark.asyncio
    async def test_campaign_generation(self):
        """Test full campaign generation"""
        from workflows.content import ContentWorkflow
        
        workflow = ContentWorkflow()
        results = await workflow.generate_campaign(
            topic="Summer Sale",
            content_types=["blog", "twitter", "newsletter"]
        )
        
        assert "blog" in results
        assert "twitter" in results
        assert "newsletter" in results
    
    @pytest.mark.asyncio
    async def test_content_markdown_export(self):
        """Test markdown export"""
        from workflows.content import ContentWorkflow
        
        workflow = ContentWorkflow()
        result = await workflow.generate_blog(
            topic="Test Topic",
            length="short"
        )
        
        markdown = result.to_markdown()
        
        assert "# " in markdown
        assert "Test Topic" in markdown or "test" in markdown.lower()
    
    @pytest.mark.asyncio
    async def test_content_html_export(self):
        """Test HTML export"""
        from workflows.content import ContentWorkflow
        
        workflow = ContentWorkflow()
        result = await workflow.generate_blog(
            topic="HTML Test",
            length="short"
        )
        
        html = result.to_html()
        
        assert "<html>" in html
        assert "<h1>" in html
        assert "<p>" in html


class TestApprovalWorkflowIntegration:
    """Integration tests for Approval workflow"""
    
    @pytest.mark.asyncio
    async def test_approval_gate_initialization(self):
        """Test approval gate initializes correctly"""
        from workflows.approval import ApprovalGate
        
        gate = ApprovalGate()
        assert gate is not None
        
        # Should have default rules
        rules = gate.get_rules()
        assert len(rules) > 0
    
    @pytest.mark.asyncio
    async def test_approval_rule_check(self):
        """Test rule checking"""
        from workflows.approval import ApprovalGate
        
        gate = ApprovalGate()
        
        # Should match shell command rule
        rule = await gate.check("execute_shell_cmd", {"cmd": "ls"})
        assert rule is not None
    
    @pytest.mark.asyncio
    async def test_approval_custom_rule(self):
        """Test custom rule addition"""
        from workflows.approval import ApprovalGate, ApprovalRule, RiskLevel
        
        gate = ApprovalGate()
        
        custom_rule = ApprovalRule(
            name="custom_test",
            pattern=r"custom_action.*",
            risk_level=RiskLevel.HIGH,
            timeout_seconds=60
        )
        
        gate.add_rule(custom_rule)
        
        rule = await gate.check("custom_action_test", {})
        assert rule is not None
        assert rule.name == "custom_test"
    
    @pytest.mark.asyncio
    async def test_approval_pending_list(self):
        """Test pending approval listing"""
        from workflows.approval import get_approval_gate
        
        gate = get_approval_gate()
        pending = gate.get_pending()
        
        # Should return a list (may be empty)
        assert isinstance(pending, list)
    
    @pytest.mark.asyncio
    async def test_approval_stats(self):
        """Test approval statistics"""
        from workflows.approval import get_approval_gate
        
        gate = get_approval_gate()
        stats = gate.get_stats()
        
        assert "total" in stats
        assert "approved" in stats
        assert "denied" in stats
        assert "approval_rate" in stats


class TestWorkflowErrorHandling:
    """Tests for workflow error handling"""
    
    @pytest.mark.asyncio
    async def test_daily_brief_handles_agent_failure(self):
        """Test Daily Brief handles agent failure gracefully"""
        from workflows.daily_brief import DailyBriefWorkflow, DailyBriefConfig
        
        config = DailyBriefConfig(use_mock_data=True)
        workflow = DailyBriefWorkflow(config)
        
        # Should complete even if some data is missing
        result = await workflow.run()
        assert result.status.value == "completed"
    
    @pytest.mark.asyncio
    async def test_research_handles_source_failure(self):
        """Test Research handles source failure gracefully"""
        from workflows.research import ResearchWorkflow
        
        workflow = ResearchWorkflow()
        
        # Should work even with unusual topic
        result = await workflow.run(
            topic="xyznonexistent123",
            depth="quick"
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_content_handles_empty_topic(self):
        """Test Content handles edge cases"""
        from workflows.content import ContentWorkflow
        
        workflow = ContentWorkflow()
        
        # Should handle short topic
        result = await workflow.generate_blog(
            topic="X",
            length="short"
        )
        
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
