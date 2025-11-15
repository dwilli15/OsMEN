#!/usr/bin/env python3
"""
OsMEN Intake Agent - Natural Language Agent Team Creator

This agent interviews users to understand their needs and creates
custom agent teams with coordinated specialists.
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.exceptions import JSONDecodeError

from web.agent_config import AgentConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntakeAgent:
    """
    Intake agent that interviews users and creates custom agent teams.
    Uses natural language to understand requirements and coordinates
    agent creation, goal setting, and team cohesion.
    """

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.agents_dir = self.project_root / "agents"
        self.langflow_dir = self.project_root / "langflow" / "flows"
        self.n8n_dir = self.project_root / "n8n" / "workflows"

        self.langflow_dir.mkdir(parents=True, exist_ok=True)
        self.n8n_dir.mkdir(parents=True, exist_ok=True)

        self.config_manager = AgentConfigManager()

        # Conversation stages
        self.STAGES = {
            "initial": self._handle_initial,
            "gathering_requirements": self._handle_gathering,
            "confirming": self._handle_confirming,
            "deploying": self._handle_deploying,
            "complete": self._handle_complete,
        }

    def process_message(
        self, message: str, context: Dict, history: List[Dict]
    ) -> Dict[str, Any]:
        """
        Process a user message and return the agent's response.

        Args:
            message: User's message
            context: Current conversation context
            history: Conversation history

        Returns:
            Dictionary with response, updated context, and any created agents
        """
        stage = context.get("stage", "initial")
        handler = self.STAGES.get(stage, self._handle_initial)

        return handler(message, context, history)

    def _handle_initial(
        self, message: str, context: Dict, history: List[Dict]
    ) -> Dict[str, Any]:
        """Handle the initial user description of needs"""

        # Analyze the user's needs
        requirements = self._analyze_requirements(message)

        # Update context
        context["stage"] = "gathering_requirements"
        context["requirements"] = requirements
        context["original_request"] = message

        # Ask clarifying questions
        questions = self._generate_clarifying_questions(requirements)

        response = f"""Great! I understand you need help with: <strong>{requirements.get('domain', 'general tasks')}</strong>.<br><br>

To create the perfect team for you, I'd like to ask a few questions:<br><br>

<strong>1. What's your main goal?</strong> (e.g., "automate my daily workflow", "monitor my system security", "manage my projects")<br><br>

<strong>2. How often do you need this done?</strong> (e.g., "continuously", "daily", "on-demand")<br><br>

<strong>3. What level of automation do you want?</strong> (e.g., "fully automatic", "semi-automatic with my approval", "manual trigger only")<br><br>

Just answer naturally - I'll understand! 😊"""

        return {"response": response, "context": context, "isHtml": True}

    def _handle_gathering(
        self, message: str, context: Dict, history: List[Dict]
    ) -> Dict[str, Any]:
        """Gather additional requirements from user"""

        # Extract additional information
        requirements = context.get("requirements", {})

        # Parse user's answers
        parsed_info = self._parse_user_answers(message)
        requirements.update(parsed_info)

        context["requirements"] = requirements

        # Check if we have enough information
        if self._has_sufficient_info(requirements):
            # Generate agent team proposal
            proposed_agents = self._design_agent_team(requirements)
            context["proposedAgents"] = proposed_agents
            context["stage"] = "confirming"

            # Create summary
            summary_html = self._create_team_summary(proposed_agents)

            response = f"""Perfect! Based on your needs, I've designed a custom agent team for you:<br><br>

{summary_html}

<strong>Does this team look good to you?</strong><br>
Reply "yes" to create these agents, or tell me what you'd like to change!"""

            return {"response": response, "context": context, "isHtml": True}
        else:
            # Ask for more information
            response = """Thanks for that information! A few more quick questions:<br><br>

What specific tasks should the agents handle? (Be as detailed as you like - I can handle it! 😊)"""

            return {"response": response, "context": context, "isHtml": True}

    def _handle_confirming(
        self, message: str, context: Dict, history: List[Dict]
    ) -> Dict[str, Any]:
        """Handle user confirmation or modification requests"""

        message_lower = message.lower()

        if any(
            word in message_lower
            for word in ["yes", "looks good", "perfect", "do it", "create"]
        ):
            # User approved - deploy agents
            context["stage"] = "deploying"
            return self._deploy_agents(context)
        else:
            # User wants modifications
            proposed_agents = context.get("proposedAgents", [])

            # Modify based on feedback
            modifications = self._parse_modifications(message)
            updated_agents = self._apply_modifications(proposed_agents, modifications)

            context["proposedAgents"] = updated_agents
            summary_html = self._create_team_summary(updated_agents)

            response = f"""I've updated your team based on your feedback:<br><br>

{summary_html}

<strong>How does this look now?</strong> Reply "yes" to create these agents!"""

            return {"response": response, "context": context, "isHtml": True}

    def _handle_deploying(
        self, message: str, context: Dict, history: List[Dict]
    ) -> Dict[str, Any]:
        """Deploy the agent team"""
        # This method is called directly from _handle_confirming
        return self._deploy_agents(context)

    def _handle_complete(
        self, message: str, context: Dict, history: List[Dict]
    ) -> Dict[str, Any]:
        """Handle post-deployment conversation"""

        response = """Your agents are up and running! You can:<br><br>

• <strong>View them in Langflow:</strong> <a href="http://localhost:7860" target="_blank">http://localhost:7860</a><br>
• <strong>Manage workflows in n8n:</strong> <a href="http://localhost:5678" target="_blank">http://localhost:5678</a><br>
• <strong>Create another team:</strong> Just tell me what you need!<br><br>

What would you like to do next?"""

        return {"response": response, "context": context, "isHtml": True}

    def _analyze_requirements(self, message: str) -> Dict[str, Any]:
        """Analyze user's initial requirements"""

        # Simple keyword-based analysis (in production, use LLM)
        requirements = {"domain": "general", "keywords": []}

        message_lower = message.lower()

        # Detect domain
        if any(
            word in message_lower
            for word in ["security", "firewall", "protect", "monitor", "scan"]
        ):
            requirements["domain"] = "security"
        elif any(
            word in message_lower
            for word in ["schedule", "calendar", "plan", "organize", "manage"]
        ):
            requirements["domain"] = "productivity"
        elif any(
            word in message_lower
            for word in ["research", "learn", "study", "analyze", "investigate"]
        ):
            requirements["domain"] = "research"
        elif any(
            word in message_lower
            for word in ["content", "video", "media", "edit", "create"]
        ):
            requirements["domain"] = "content_creation"

        # Extract keywords
        important_words = [
            "automate",
            "monitor",
            "analyze",
            "create",
            "manage",
            "track",
            "notify",
        ]
        requirements["keywords"] = [
            word for word in important_words if word in message_lower
        ]

        return requirements

    def _generate_clarifying_questions(self, requirements: Dict) -> List[str]:
        """Generate questions based on initial requirements"""

        questions = [
            "What's your main goal?",
            "How often do you need this?",
            "What level of automation do you want?",
        ]

        return questions

    def _parse_user_answers(self, message: str) -> Dict[str, Any]:
        """Parse user's answers to questions"""

        info = {}
        message_lower = message.lower()

        # Detect goal
        if "automate" in message_lower or "automatic" in message_lower:
            info["goal"] = "automation"
        elif "monitor" in message_lower or "track" in message_lower:
            info["goal"] = "monitoring"
        elif "analyze" in message_lower or "report" in message_lower:
            info["goal"] = "analysis"

        # Detect frequency
        if (
            "continuous" in message_lower
            or "always" in message_lower
            or "24/7" in message_lower
        ):
            info["frequency"] = "continuous"
        elif "daily" in message_lower or "every day" in message_lower:
            info["frequency"] = "daily"
        elif "hourly" in message_lower or "every hour" in message_lower:
            info["frequency"] = "hourly"
        elif (
            "on-demand" in message_lower
            or "when I ask" in message_lower
            or "manual" in message_lower
        ):
            info["frequency"] = "on-demand"

        # Detect automation level
        if "fully automatic" in message_lower or "complete" in message_lower:
            info["automation_level"] = "full"
        elif "semi" in message_lower or "approval" in message_lower:
            info["automation_level"] = "semi"
        elif "manual" in message_lower:
            info["automation_level"] = "manual"

        return info

    def _has_sufficient_info(self, requirements: Dict) -> bool:
        """Check if we have enough info to design a team"""

        required_fields = ["domain", "goal", "frequency"]
        return all(field in requirements for field in required_fields)

    def _design_agent_team(self, requirements: Dict) -> List[Dict[str, Any]]:
        """Design a custom agent team based on requirements"""

        agents = []
        domain = requirements.get("domain", "general")
        goal = requirements.get("goal", "automation")
        frequency = requirements.get("frequency", "daily")

        # Create coordinator agent (always needed)
        agents.append(
            {
                "name": f"{domain.title()} Coordinator",
                "type": "coordinator",
                "purpose": f"Routes tasks and coordinates the {domain} team",
                "capabilities": [
                    "task_routing",
                    "team_coordination",
                    "conflict_resolution",
                ],
            }
        )

        # Add domain-specific specialist
        if domain == "security":
            agents.append(
                {
                    "name": "Security Monitor",
                    "type": "specialist",
                    "purpose": "Monitors system security and detects threats",
                    "capabilities": [
                        "security_scanning",
                        "threat_detection",
                        "firewall_management",
                    ],
                }
            )
        elif domain == "productivity":
            agents.append(
                {
                    "name": "Productivity Manager",
                    "type": "specialist",
                    "purpose": "Manages tasks, schedules, and workflows",
                    "capabilities": [
                        "task_management",
                        "scheduling",
                        "reminder_system",
                    ],
                }
            )
        elif domain == "research":
            agents.append(
                {
                    "name": "Research Assistant",
                    "type": "specialist",
                    "purpose": "Gathers and analyzes information",
                    "capabilities": ["web_research", "data_analysis", "summarization"],
                }
            )
        elif domain == "content_creation":
            agents.append(
                {
                    "name": "Content Creator",
                    "type": "specialist",
                    "purpose": "Creates and edits content",
                    "capabilities": [
                        "content_generation",
                        "media_editing",
                        "optimization",
                    ],
                }
            )

        # Add automation agent if needed
        if goal == "automation":
            agents.append(
                {
                    "name": "Automation Specialist",
                    "type": "specialist",
                    "purpose": "Automates repetitive tasks",
                    "capabilities": [
                        "workflow_automation",
                        "trigger_management",
                        "task_execution",
                    ],
                }
            )

        # Add monitoring agent if needed
        if goal == "monitoring" and frequency in ["continuous", "hourly"]:
            agents.append(
                {
                    "name": "Continuous Monitor",
                    "type": "monitor",
                    "purpose": "Continuously monitors and alerts",
                    "capabilities": ["real_time_monitoring", "alerting", "logging"],
                }
            )

        return agents

    def _create_team_summary(self, agents: List[Dict]) -> str:
        """Create HTML summary of proposed agent team"""

        summary = '<div style="background: #f0f4ff; padding: 15px; border-radius: 8px; margin: 10px 0;">'

        for i, agent in enumerate(agents, 1):
            summary += f'<div style="margin: 10px 0;"><strong>{i}. {agent["name"]}</strong><br>'
            summary += (
                f'<span style="color: #666;">Purpose: {agent["purpose"]}</span><br>'
            )
            summary += f'<span style="color: #667eea; font-size: 0.9em;">Capabilities: {", ".join(agent["capabilities"])}</span></div>'

        summary += "</div>"

        return summary

    def _parse_modifications(self, message: str) -> Dict[str, Any]:
        """Parse user's modification requests"""

        modifications = {}
        message_lower = message.lower()

        if "add" in message_lower or "need" in message_lower or "want" in message_lower:
            modifications["action"] = "add"
        elif "remove" in message_lower or "don't need" in message_lower:
            modifications["action"] = "remove"
        elif "change" in message_lower or "modify" in message_lower:
            modifications["action"] = "modify"

        return modifications

    def _apply_modifications(
        self, agents: List[Dict], modifications: Dict
    ) -> List[Dict]:
        """Apply user's requested modifications to agent team"""

        # Simple implementation - in production, use LLM to understand modifications
        return agents

    @staticmethod
    def _slugify_agent_name(name: str) -> str:
        """Return a filesystem-safe slug for an agent name."""

        slug = name.lower().strip().replace(" ", "_")
        slug = re.sub(r"[^a-z0-9_-]", "", slug)
        slug = re.sub(r"_+", "_", slug).strip("_")
        if not slug:
            raise ValueError(f"Invalid agent name: {name}")
        return slug

    def deploy_agents(self, context: Dict) -> Dict[str, Any]:
        """Public wrapper for deploying agents.

        Args:
            context (Dict): Deployment context containing a ``proposedAgents`` list and related metadata.

        Returns:
            Dict[str, Any]: Structured deployment results with the following keys:
                - ``response``: User-facing status message.
                - ``context``: Updated deployment context with stage/results metadata.
                - ``agentsCreated``: List of successfully created agents.
                - ``deploymentResults``: Per-agent deployment details.
                - ``deploymentStatus``: Overall status string (``success``, ``failed``, ``partial``, ``skipped``).
        """

        if not isinstance(context, dict):
            raise ValueError("context must be a dictionary")

        proposed_agents = context.get("proposedAgents", [])
        if not isinstance(proposed_agents, list):
            raise ValueError("context['proposedAgents'] must be a list")

        logger.info("Deploying %d proposed agent(s)", len(proposed_agents))

        return self._deploy_agents(context)

    def _deploy_agents(self, context: Dict) -> Dict[str, Any]:
        """Deploy the designed agent team and synchronize services."""

        proposed_agents = context.get("proposedAgents", [])

        deployment_results: List[Dict[str, Any]] = []
        created_agents: List[Dict[str, Any]] = []

        for agent in proposed_agents:
            agent_slug = self._slugify_agent_name(agent["name"])
            result: Dict[str, Any] = {
                "name": agent["name"],
                "slug": agent_slug,
            }

            try:
                files, artifacts = self._create_agent_files(agent)
                result["files"] = files

                registration_status = self._register_agent_with_dashboard(
                    agent_slug, agent, artifacts
                )
                result["registration"] = registration_status

                sync_status = self._synchronize_services(agent_slug, artifacts)
                result["synchronization"] = sync_status

                if (
                    registration_status.get("status") == "success"
                    and sync_status.get("status") == "success"
                ):
                    created_agents.append(agent)
                    result["status"] = "success"
                    logger.info(f"Successfully deployed agent: {agent['name']}")
                else:
                    result["status"] = "partial"
                    logger.warning(f"Agent {agent['name']} deployed with warnings")
            except Exception as exc:
                result["status"] = "error"
                result["error"] = str(exc)
                logger.error(
                    f"Failed to deploy agent %s: %s", agent["name"], exc, exc_info=True
                )

            deployment_results.append(result)

        success_count = len(
            [r for r in deployment_results if r.get("status") == "success"]
        )
        error_count = len([r for r in deployment_results if r.get("status") == "error"])

        if error_count == 0 and success_count == len(deployment_results):
            overall_status = "success"
            response_message = f"🎉 Success! I've created {success_count} agent(s) for your team. They're synchronized and ready to help!"
        elif success_count == 0 and deployment_results:
            overall_status = "failed"
            response_message = "⚠️ I wasn't able to deploy any agents. Please review the errors and try again."
        elif not deployment_results:
            overall_status = "skipped"
            response_message = "ℹ️ No agents were provided for deployment."
        else:
            overall_status = "partial"
            response_message = (
                f"⚠️ I deployed {success_count} agent(s), but some steps need attention."
            )

        context["stage"] = "complete"
        context["createdAgents"] = created_agents
        context["deploymentResults"] = deployment_results
        context["deploymentStatus"] = overall_status

        return {
            "response": response_message,
            "context": context,
            "agentsCreated": created_agents,
            "deploymentResults": deployment_results,
            "deploymentStatus": overall_status,
        }

    def _create_agent_files(self, agent: Dict) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """Create the actual agent files (Langflow flow + n8n workflow)."""

        agent_slug = self._slugify_agent_name(agent["name"])

        # Create Langflow flow
        langflow_flow = self._generate_langflow_flow(agent)
        langflow_file = self.langflow_dir / f"{agent_slug}.json"

        with open(langflow_file, "w") as f:
            json.dump(langflow_flow, f, indent=2)

        files = {"langflow": str(langflow_file)}
        artifacts = {"langflow": langflow_flow}

        # Create n8n workflow if needed
        if agent.get("type") != "coordinator":
            n8n_workflow = self._generate_n8n_workflow(agent)
            n8n_file = self.n8n_dir / f"{agent_slug}_trigger.json"

            with open(n8n_file, "w") as f:
                json.dump(n8n_workflow, f, indent=2)

            files["n8n"] = str(n8n_file)
            artifacts["n8n"] = n8n_workflow

        logger.info(f"Created files for agent: {agent['name']}")

        return files, artifacts

    def _generate_langflow_flow(self, agent: Dict) -> Dict:
        """Generate Langflow flow definition for an agent"""

        agent_slug = self._slugify_agent_name(agent["name"])

        flow = {
            "id": agent_slug,
            "name": agent["name"],
            "description": agent["purpose"],
            "nodes": [
                {"id": "input", "type": "ChatInput", "data": {"message": "User input"}},
                {
                    "id": "llm",
                    "type": "ChatOllama",
                    "data": {
                        "model": os.getenv("OLLAMA_MODEL", "llama2"),
                        "base_url": "http://ollama:11434",
                        "temperature": 0.7,
                        "system_message": f"You are {agent['name']}. {agent['purpose']}. Your capabilities include: {', '.join(agent.get('capabilities', []))}.",
                    },
                },
                {
                    "id": "memory",
                    "type": "VectorStoreRetriever",
                    "data": {
                        "vector_store": "qdrant",
                        "collection_name": f"{agent_slug}_memory",
                        "host": "http://qdrant:6333",
                    },
                },
                {
                    "id": "output",
                    "type": "ChatOutput",
                    "data": {"message": "Agent response"},
                },
            ],
            "edges": [
                {"source": "input", "target": "llm"},
                {"source": "llm", "target": "memory"},
                {"source": "memory", "target": "output"},
            ],
        }

        return flow

    def _register_agent_with_dashboard(
        self, agent_slug: str, agent: Dict, artifacts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Register agent configuration so it appears in the dashboard.

        Args:
            agent_slug (str): URL-safe identifier for the agent.
            agent (Dict): Agent configuration containing name, purpose, and capabilities.
            artifacts (Dict[str, Any]): Generated artifacts including langflow and n8n definitions.

        Returns:
            Dict[str, Any]: Status dictionary with 'status' key ('success' or 'error') and
                optional 'error' message.
        """
        try:
            agent_metadata = {
                "name": agent["name"],
                "purpose": agent.get("purpose", ""),
                "capabilities": agent.get("capabilities", []),
                "enabled": True,
            }
            self.config_manager.register_agent(agent_slug, agent_metadata)

            langflow_record = {
                "id": agent_slug,
                "name": artifacts["langflow"].get("name", agent["name"]),
                "description": artifacts["langflow"].get(
                    "description", agent.get("purpose", "")
                ),
                "enabled": True,
                "trigger": "manual",
            }
            self.config_manager.register_langflow_workflow(langflow_record)

            if "n8n" in artifacts:
                n8n_record = {
                    "id": f"{agent_slug}_trigger",
                    "name": artifacts["n8n"].get("name", f"{agent['name']} Trigger"),
                    "description": artifacts["n8n"].get(
                        "description", agent.get("purpose", "Automated workflow")
                    ),
                    "enabled": True,
                    "trigger": "schedule",
                }
                self.config_manager.register_n8n_workflow(n8n_record)

            return {"status": "success"}
        except Exception as exc:
            logger.error(
                f"Failed to register agent {agent['name']} with dashboard: {exc}"
            )
            return {"status": "error", "error": str(exc)}

    def _synchronize_services(
        self, agent_slug: str, artifacts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Import generated definitions into Langflow and n8n services.

        Args:
            agent_slug: URL-safe identifier for the agent.
            artifacts: Dictionary containing Langflow and optional n8n artifacts to import.

        Returns:
            Dictionary with individual service statuses (``langflow``/``n8n``) plus an overall
            ``status`` key set to ``success``, ``partial``, or ``error``.
        """

        langflow_status = self._sync_langflow_flow(
            agent_slug, artifacts.get("langflow")
        )
        n8n_status = self._sync_n8n_workflow(agent_slug, artifacts.get("n8n"))

        statuses = {"langflow": langflow_status}
        if n8n_status:
            statuses["n8n"] = n8n_status

        if any(s.get("status") == "error" for s in statuses.values()):
            statuses["status"] = "error"
        elif any(s.get("status") == "partial" for s in statuses.values()):
            statuses["status"] = "partial"
        else:
            statuses["status"] = "success"

        return statuses

    def _sync_langflow_flow(
        self, agent_slug: str, flow: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Import Langflow flow via API when available."""

        if not flow:
            return {"status": "error", "error": "Missing Langflow flow definition"}

        langflow_cfg = self.config_manager.config.get("langflow", {})
        if not langflow_cfg.get("enabled", True):
            return {"status": "skipped", "reason": "Langflow disabled"}

        base_url = os.getenv("LANGFLOW_API_URL") or langflow_cfg.get("base_url")
        api_key = os.getenv("LANGFLOW_API_KEY") or langflow_cfg.get("api_key")

        if not base_url:
            return {"status": "skipped", "reason": "Langflow URL not configured"}

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["x-api-key"] = api_key

        flow_payload = dict(flow)
        flow_payload.setdefault("id", agent_slug)

        endpoints = [
            (
                "POST",
                f"{base_url.rstrip('/')}/api/v1/flows/import",
                {"flows": [flow_payload]},
            ),
            ("POST", f"{base_url.rstrip('/')}/api/v1/flows/", flow_payload),
            ("PUT", f"{base_url.rstrip('/')}/api/v1/flows/{agent_slug}", flow_payload),
        ]

        timeout = int(os.getenv("LANGFLOW_API_TIMEOUT", "30"))
        last_error = None
        for method, url, payload in endpoints:
            try:
                logger.debug("Langflow sync attempting %s %s", method, url)
                response = requests.request(
                    method, url, json=payload, headers=headers, timeout=timeout
                )
                if response.status_code < 400:
                    try:
                        data = response.json()
                    except JSONDecodeError:
                        data = {}
                    logger.info("Langflow sync succeeded via %s %s", method, url)
                    return {"status": "success", "endpoint": url, "response": data}

                logger.warning(
                    "Langflow API error %s %s: %s", method, url, response.status_code
                )
                logger.debug("Langflow API response body: %s", response.text)
                last_error = f"{response.status_code}: Langflow import failed"
            except requests.RequestException as exc:
                logger.error("Langflow request %s %s failed: %s", method, url, exc)
                last_error = str(exc)

        return {"status": "error", "error": last_error or "Langflow import failed"}

    def _sync_n8n_workflow(
        self, agent_slug: str, workflow: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Import n8n workflow via API when available."""

        if workflow is None:
            return None

        n8n_cfg = self.config_manager.config.get("n8n", {})
        if not n8n_cfg.get("enabled", True):
            return {"status": "skipped", "reason": "n8n disabled"}

        base_url = os.getenv("N8N_API_URL") or n8n_cfg.get("base_url")
        api_key = os.getenv("N8N_API_KEY") or n8n_cfg.get("api_key")

        if not base_url:
            return {"status": "skipped", "reason": "n8n URL not configured"}

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-N8N-API-KEY"] = api_key

        workflow_payload = dict(workflow)
        workflow_payload.setdefault("active", True)
        workflow_payload.setdefault("settings", {})
        workflow_payload.setdefault("connections", {})

        url = f"{base_url.rstrip('/')}/rest/workflows"

        try:
            timeout = int(os.getenv("N8N_API_TIMEOUT", "30"))
            logger.debug("n8n sync attempting POST %s", url)
            response = requests.post(
                url, json=workflow_payload, headers=headers, timeout=timeout
            )
            if response.status_code < 400:
                try:
                    data = response.json()
                except JSONDecodeError:
                    data = {}
                logger.info("n8n sync succeeded for %s", agent_slug)
                return {"status": "success", "endpoint": url, "response": data}

            logger.warning("n8n API error POST %s: %s", url, response.status_code)
            logger.debug("n8n API response body: %s", response.text)
            return {
                "status": "error",
                "error": f"{response.status_code}: n8n import failed",
            }
        except requests.RequestException as exc:
            logger.error("n8n sync request failed for %s: %s", agent_slug, exc)
            return {"status": "error", "error": str(exc)}

    def _generate_n8n_workflow(self, agent: Dict) -> Dict:
        """Generate n8n workflow definition for an agent"""

        agent_name_slug = self._slugify_agent_name(agent["name"])

        workflow = {
            "id": f"{agent_name_slug}_trigger",
            "name": f"{agent['name']} Trigger",
            "description": agent.get("purpose", "Automated workflow"),
            "nodes": [
                {
                    "parameters": {
                        "rule": {
                            "interval": [
                                {
                                    "field": "cronExpression",
                                    "expression": "0 * * * *",  # Hourly by default
                                }
                            ]
                        }
                    },
                    "name": "Schedule Trigger",
                    "type": "n8n-nodes-base.scheduleTrigger",
                    "typeVersion": 1,
                    "position": [250, 300],
                },
                {
                    "parameters": {
                        "url": f"http://langflow:7860/api/v1/run/{agent_name_slug}",
                        "method": "POST",
                        "jsonParameters": True,
                        "bodyParametersJson": json.dumps(
                            {"input": f"Execute {agent['name']} task", "tweaks": {}}
                        ),
                    },
                    "name": f"Call {agent['name']}",
                    "type": "n8n-nodes-base.httpRequest",
                    "typeVersion": 1,
                    "position": [450, 300],
                },
                {
                    "parameters": {
                        "functionCode": f"// Log {agent['name']} execution\nconst result = $input.first().json;\nconsole.log('{agent['name']} executed:', result);\nreturn [{{ json: {{ status: 'completed' }} }}];"
                    },
                    "name": "Log Result",
                    "type": "n8n-nodes-base.function",
                    "typeVersion": 1,
                    "position": [650, 300],
                },
            ],
            "connections": {
                "Schedule Trigger": {
                    "main": [
                        [{"node": f"Call {agent['name']}", "type": "main", "index": 0}]
                    ]
                },
                f"Call {agent['name']}": {
                    "main": [[{"node": "Log Result", "type": "main", "index": 0}]]
                },
            },
            "active": True,
            "settings": {},
        }

        return workflow


if __name__ == "__main__":
    # Test the intake agent
    agent = IntakeAgent()

    # Simulate conversation
    context = {"stage": "initial"}
    history = []

    result1 = agent.process_message(
        "I need help with system security", context, history
    )
    print("Agent:", result1["response"])

    context = result1["context"]
    result2 = agent.process_message(
        "I want to monitor continuously and get alerts", context, history
    )
    print("Agent:", result2["response"])
