"""Tests for the OsMEN intake agent orchestration pipeline."""

from pathlib import Path
import sys

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT_DIR / "agents"
if str(AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_DIR))

from intake_agent.intake_agent import IntakeAgent


@pytest.fixture
def intake_agent_tmp(tmp_path, monkeypatch):
    """Provide an intake agent wired to a temporary project root."""

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    agent = IntakeAgent(project_root=tmp_path)
    agent._llm_available = False  # Force heuristic fallbacks for deterministic tests
    return agent


def test_intake_agent_end_to_end_flow(intake_agent_tmp: IntakeAgent, tmp_path: Path):
    """The intake agent should gather requirements and deploy files via fallbacks."""

    agent = intake_agent_tmp
    context = {'stage': 'initial'}
    history = []

    first = agent.process_message(
        "I need to monitor firewall alerts and automate the response steps.",
        context,
        history,
    )

    requirements = first['context']['requirements']
    assert requirements['domain'] == 'security'
    assert 'monitor' in requirements['keywords']
    assert first['context']['stage'] == 'gathering_requirements'

    second = agent.process_message(
        "Please automate it daily but keep approvals in the loop.",
        first['context'],
        history,
    )

    proposed = second['context']['proposedAgents']
    assert second['context']['stage'] == 'confirming'
    assert len(proposed) >= 2

    deployment = agent.deploy_team(second['context'])
    created = deployment['agentsCreated']
    assert deployment['context']['stage'] == 'complete'
    assert created, "Expected at least one agent to be created"

    flows_dir = tmp_path / "langflow" / "flows"
    workflows_dir = tmp_path / "n8n" / "workflows"

    for agent_info in created:
        slug = agent_info['name'].lower().replace(' ', '_')
        assert (flows_dir / f"{slug}.json").exists()
        if agent_info.get('type') != 'coordinator':
            assert (workflows_dir / f"{slug}_trigger.json").exists()


def test_apply_structured_modifications_allows_updates(intake_agent_tmp: IntakeAgent):
    """Structured UI modifications should update and extend the proposed team."""

    agent = intake_agent_tmp
    context = {
        'stage': 'confirming',
        'requirements': {'domain': 'security'},
        'proposedAgents': [
            {
                'name': 'Security Coordinator',
                'type': 'coordinator',
                'purpose': 'Routes requests',
                'capabilities': ['task_routing'],
            },
            {
                'name': 'Security Monitor',
                'type': 'specialist',
                'purpose': 'Tracks alerts',
                'capabilities': ['monitoring'],
            },
        ],
    }

    modifications = {
        'action': 'update',
        'agents': [
            {
                'index': 1,
                'name': 'Security Sentinel',
                'capabilities': ['threat_detection', 'alerting'],
                'keep': True,
            },
            {
                'index': 'new',
                'type': 'analyst',
                'purpose': 'Generates weekly summaries',
                'capabilities': ['reporting'],
                'keep': True,
                'action': 'add',
            },
        ],
    }

    result = agent.apply_structured_modifications(context, modifications)
    updated_agents = result['context']['proposedAgents']

    assert any(agent['name'] == 'Security Sentinel' for agent in updated_agents)
    assert any(agent['type'] == 'analyst' for agent in updated_agents)
    assert len(updated_agents) == 3
    assert result['review']['agents'] == updated_agents
    assert 'teamSummary' in result['context']
