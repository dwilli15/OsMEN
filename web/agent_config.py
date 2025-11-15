"""
Agent Configuration Manager for Web Dashboard

Provides no-code interface to configure:
- LangFlow workflows
- n8n automations
- Agent personalities and behaviors
- Tool integrations
- Memory settings
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class AgentConfigManager:
    """Manages agent configuration without code editing"""

    def __init__(self, config_dir: str = ".copilot"):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "agent_config.json"
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load existing configuration or create default"""
        if self.config_file.exists():
            with open(self.config_file, "r") as f:
                return json.load(f)
        return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Default agent configuration"""
        return {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "agents": {
                "research_agent": {
                    "enabled": True,
                    "personality": "helpful",
                    "llm_provider": "openai",
                    "model": "gpt-4-turbo-preview",
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "system_prompt": "You are a helpful research assistant...",
                    "tools": ["web_search", "arxiv", "google_scholar"],
                },
                "scheduler_agent": {
                    "enabled": True,
                    "personality": "organized",
                    "llm_provider": "openai",
                    "model": "gpt-4-turbo-preview",
                    "temperature": 0.5,
                    "max_tokens": 1500,
                    "system_prompt": "You are an efficient scheduling assistant...",
                    "tools": ["google_calendar", "outlook", "priority_ranker"],
                },
                "writing_agent": {
                    "enabled": True,
                    "personality": "academic",
                    "llm_provider": "claude",
                    "model": "claude-3-opus-20240229",
                    "temperature": 0.6,
                    "max_tokens": 4000,
                    "system_prompt": "You are an academic writing assistant...",
                    "tools": [
                        "grammar_check",
                        "citation_formatter",
                        "outline_generator",
                    ],
                },
            },
            "langflow": {
                "enabled": True,
                "base_url": "http://localhost:7860",
                "api_key": os.getenv("LANGFLOW_API_KEY", ""),
                "workflows": [],
            },
            "n8n": {
                "enabled": True,
                "base_url": "http://localhost:5678",
                "api_key": os.getenv("N8N_API_KEY", ""),
                "workflows": [],
            },
            "memory": {
                "conversation_retention_days": 45,
                "summary_retention_months": 12,
                "auto_summarize": True,
                "context_window_size": 8000,
            },
            "notifications": {
                "email_enabled": True,
                "push_enabled": True,
                "dashboard_enabled": True,
                "quiet_hours": {"start": "22:00", "end": "08:00"},
            },
        }

    def save_config(self):
        """Save configuration to file"""
        self.config["last_updated"] = datetime.now().isoformat()
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=2)

    def get_agent(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get specific agent configuration"""
        return self.config.get("agents", {}).get(agent_name)

    def update_agent(self, agent_name: str, updates: Dict[str, Any]):
        """Update agent configuration"""
        if "agents" not in self.config:
            self.config["agents"] = {}
        if agent_name not in self.config["agents"]:
            self.config["agents"][agent_name] = self._default_agent_config()

        self.config["agents"][agent_name].update(updates)
        self.save_config()

    def register_agent(
        self, agent_name: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create or update an agent entry and ensure it's enabled.

        Args:
            agent_name: Unique identifier for the agent (slug format).
            metadata: Agent configuration including name, purpose, capabilities, etc.

        Returns:
            The complete agent configuration after registration.
        """

        if "agents" not in self.config:
            self.config["agents"] = {}

        agent_config = self.config["agents"].get(
            agent_name, self._default_agent_config()
        )
        agent_config = self._deep_merge(agent_config, metadata)
        agent_config["enabled"] = metadata.get(
            "enabled", agent_config.get("enabled", True)
        )

        self.config["agents"][agent_name] = agent_config
        self.save_config()

        return agent_config

    def _default_agent_config(self) -> Dict[str, Any]:
        """Default config for new agent"""
        return {
            "enabled": True,
            "personality": "helpful",
            "llm_provider": "openai",
            "model": "gpt-4-turbo-preview",
            "temperature": 0.7,
            "max_tokens": 2000,
            "system_prompt": "You are a helpful assistant.",
            "tools": [],
        }

    @staticmethod
    def _deep_merge(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge ``updates`` into ``base`` without clobbering nested dicts."""

        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                AgentConfigManager._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    def toggle_agent(self, agent_name: str, enabled: bool):
        """Enable or disable an agent"""
        if agent_name in self.config.get("agents", {}):
            self.config["agents"][agent_name]["enabled"] = enabled
            self.save_config()

    def add_langflow_workflow(self, workflow: Dict[str, Any]):
        """Add LangFlow workflow configuration"""
        if "langflow" not in self.config:
            self.config["langflow"] = {"workflows": []}
        self.config["langflow"]["workflows"].append(
            {
                "id": workflow.get("id"),
                "name": workflow.get("name"),
                "description": workflow.get("description", ""),
                "enabled": workflow.get("enabled", True),
                "trigger": workflow.get("trigger", "manual"),
                "added_at": datetime.now().isoformat(),
            }
        )
        self.save_config()

    def register_langflow_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Upsert a LangFlow workflow configuration entry.

        Args:
            workflow: Workflow configuration dictionary containing keys such as
                ``id``, ``name``, ``description``, ``enabled``, and ``trigger``.

        Returns:
            Dict[str, Any]: The registered workflow record with metadata, including
            the ``added_at`` timestamp.
        """

        if "langflow" not in self.config:
            self.config["langflow"] = {"workflows": []}

        workflows = self.config["langflow"].setdefault("workflows", [])
        self.config["langflow"]["workflows"] = [
            w for w in workflows if w.get("id") != workflow.get("id")
        ]
        workflows = self.config["langflow"]["workflows"]
        record = {
            "id": workflow.get("id"),
            "name": workflow.get("name"),
            "description": workflow.get("description", ""),
            "enabled": workflow.get("enabled", True),
            "trigger": workflow.get("trigger", "manual"),
            "added_at": datetime.now().isoformat(),
        }
        workflows.append(record)
        self.config["langflow"]["workflows"] = workflows
        self.save_config()

        return record

    def add_n8n_workflow(self, workflow: Dict[str, Any]):
        """Add n8n workflow configuration"""
        if "n8n" not in self.config:
            self.config["n8n"] = {"workflows": []}
        self.config["n8n"]["workflows"].append(
            {
                "id": workflow.get("id"),
                "name": workflow.get("name"),
                "description": workflow.get("description", ""),
                "enabled": workflow.get("enabled", True),
                "trigger": workflow.get("trigger", "manual"),
                "added_at": datetime.now().isoformat(),
            }
        )
        self.save_config()

    def register_n8n_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Upsert an n8n workflow configuration entry.

        Args:
            workflow: Workflow configuration dictionary containing keys:
                - ``id``: Unique workflow identifier
                - ``name``: Workflow name
                - ``description``: Optional description of the workflow
                - ``enabled``: Optional boolean indicating if the workflow is enabled
                - ``trigger``: Optional trigger type (e.g., ``manual``, ``cron``)

        Returns:
            Dict[str, Any]: The registered workflow record with metadata, including
            the ``added_at`` timestamp.
        """

        if "n8n" not in self.config:
            self.config["n8n"] = {"workflows": []}

        workflows = self.config["n8n"].setdefault("workflows", [])
        self.config["n8n"]["workflows"] = [
            w for w in workflows if w.get("id") != workflow.get("id")
        ]
        workflows = self.config["n8n"]["workflows"]
        record = {
            "id": workflow.get("id"),
            "name": workflow.get("name"),
            "description": workflow.get("description", ""),
            "enabled": workflow.get("enabled", True),
            "trigger": workflow.get("trigger", "manual"),
            "added_at": datetime.now().isoformat(),
        }
        workflows.append(record)
        self.config["n8n"]["workflows"] = workflows
        self.save_config()

        return record

    def update_memory_settings(self, settings: Dict[str, Any]):
        """Update memory system settings"""
        if "memory" not in self.config:
            self.config["memory"] = {}
        self.config["memory"].update(settings)
        self.save_config()

    def update_notification_settings(self, settings: Dict[str, Any]):
        """Update notification settings"""
        if "notifications" not in self.config:
            self.config["notifications"] = {}
        self.config["notifications"].update(settings)
        self.save_config()

    def get_all_agents(self) -> Dict[str, Any]:
        """Get all agent configurations"""
        return self.config.get("agents", {})

    def get_enabled_agents(self) -> List[str]:
        """Get list of enabled agent names"""
        agents = self.config.get("agents", {})
        return [name for name, config in agents.items() if config.get("enabled", False)]

    def get_langflow_workflows(self) -> List[Dict[str, Any]]:
        """Get LangFlow workflows"""
        return self.config.get("langflow", {}).get("workflows", [])

    def get_n8n_workflows(self) -> List[Dict[str, Any]]:
        """Get n8n workflows"""
        return self.config.get("n8n", {}).get("workflows", [])

    def get_memory_settings(self) -> Dict[str, Any]:
        """Get memory system settings"""
        return self.config.get("memory", {})

    def get_notification_settings(self) -> Dict[str, Any]:
        """Get notification settings"""
        return self.config.get("notifications", {})

    def export_config(self) -> str:
        """Export configuration as JSON string"""
        return json.dumps(self.config, indent=2)

    def import_config(self, config_json: str):
        """Import configuration from JSON string"""
        self.config = json.loads(config_json)
        self.save_config()

    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config = self._default_config()
        self.save_config()

    def validate_config(self) -> Dict[str, List[str]]:
        """Validate configuration and return issues"""
        issues = {}

        # Validate agents
        for agent_name, agent_config in self.config.get("agents", {}).items():
            agent_issues = []

            if not agent_config.get("llm_provider"):
                agent_issues.append("Missing LLM provider")

            if not agent_config.get("model"):
                agent_issues.append("Missing model specification")

            temp = agent_config.get("temperature", 0.7)
            if not (0 <= temp <= 2):
                agent_issues.append(f"Temperature {temp} out of range [0, 2]")

            max_tokens = agent_config.get("max_tokens", 2000)
            if max_tokens < 1 or max_tokens > 128000:
                agent_issues.append(f"Max tokens {max_tokens} out of range")

            if agent_issues:
                issues[agent_name] = agent_issues

        # Validate memory settings
        memory = self.config.get("memory", {})
        if memory.get("conversation_retention_days", 45) < 1:
            issues["memory"] = ["Conversation retention must be >= 1 day"]

        return issues
