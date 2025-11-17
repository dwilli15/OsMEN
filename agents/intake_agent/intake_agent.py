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

from requests.exceptions import JSONDecodeError

from web.agent_config import AgentConfigManager

try:
    import requests
except ImportError:  # pragma: no cover - requests is an optional runtime dependency
    requests = None

try:
    import requests
except ImportError:  # pragma: no cover - requests is an optional runtime dependency
    requests = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntakeAgent:
    """
    Intake agent that interviews users and creates custom agent teams.
    Uses natural language to understand requirements and coordinates
    agent creation, goal setting, and team cohesion.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """Create a new intake agent.

        Args:
            project_root: Optional override for the repository root. This is
                primarily useful for tests so we can point the agent at a
                temporary directory when generating Langflow and n8n assets.
        """

        base_root = Path(project_root) if project_root is not None else Path(__file__).parent.parent.parent
        self.project_root = base_root
        self.agents_dir = self.project_root / "agents"
        self.langflow_dir = self.project_root / "langflow" / "flows"
        self.n8n_dir = self.project_root / "n8n" / "workflows"

        # Ensure directories exist so deployments never fail because of missing folders
        self.langflow_dir.mkdir(parents=True, exist_ok=True)
        self.n8n_dir.mkdir(parents=True, exist_ok=True)

        # LLM configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.llm_model = os.getenv("INTAKE_AGENT_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
        self._llm_available = bool(self.openai_api_key)
        self.system_prompt = (
            "You are the OsMEN intake coordinator. You translate natural language "
            "requests into structured agent orchestration plans. Always respond "
            "with concise JSON data that the platform can use directly."
        )

        # Expanded domain catalogue for richer agent proposals
        self.domain_specialists = {
            "general": {
                "name": "Operations Specialist",
                "purpose": "Handles general automations and ensures smooth execution",
                "capabilities": ["task_management", "workflow_automation", "status_reporting"],
            },
            "security": {
                "name": "Security Monitor",
                "purpose": "Monitors system security and detects threats",
                "capabilities": ["security_scanning", "threat_detection", "firewall_management"],
            },
            "productivity": {
                "name": "Productivity Manager",
                "purpose": "Manages tasks, schedules, and workflows",
                "capabilities": ["task_management", "scheduling", "reminder_system"],
            },
            "research": {
                "name": "Research Analyst",
                "purpose": "Gathers and analyzes information",
                "capabilities": ["web_research", "data_analysis", "summarization"],
            },
            "content_creation": {
                "name": "Content Creator",
                "purpose": "Creates and edits content",
                "capabilities": ["content_generation", "media_editing", "optimization"],
            },
            "marketing": {
                "name": "Marketing Strategist",
                "purpose": "Plans campaigns and tracks engagement metrics",
                "capabilities": ["campaign_planning", "audience_research", "performance_reporting"],
            },
            "finance": {
                "name": "Finance Analyst",
                "purpose": "Monitors budgets and financial KPIs",
                "capabilities": ["budget_tracking", "forecasting", "variance_analysis"],
            },
            "development": {
                "name": "DevOps Specialist",
                "purpose": "Automates build, test, and deployment workflows",
                "capabilities": ["ci_cd", "infrastructure_as_code", "release_management"],
            },
        }
        
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

    # ------------------------------------------------------------------
    # LLM + Fallback Utilities
    # ------------------------------------------------------------------

    def _call_llm(self, prompt: str, *, expect_json: bool = False, temperature: float = 0.2) -> Optional[str]:
        """Call configured LLM provider and return response text."""

        if not self._llm_available or requests is None:
            logger.debug("LLM not configured; skipping call")
            return None

        try:
            payload = {
                "model": self.llm_model,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
            }

            if expect_json:
                payload["response_format"] = {"type": "json_object"}

            response = requests.post(
                f"{self.openai_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            if expect_json:
                content = self._clean_json_block(content)

            return content.strip() if content else None
        except Exception as exc:
            logger.warning(f"LLM call failed: {exc}")
            return None

    @staticmethod
    def _clean_json_block(content: str) -> str:
        """Remove Markdown code fences from JSON responses."""

        text = content.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
            if text.lower().startswith("json"):
                text = text[4:].strip()
        return text

    def _fallback_requirements(self, message: str) -> Dict[str, Any]:
        """Fallback keyword-based requirement parsing."""

        requirements = {
            'domain': 'general',
            'domain_label': 'General',
            'keywords': [],
        }

        message_lower = message.lower()
        domain_keywords = {
            'security': ['security', 'firewall', 'protect', 'monitor', 'scan'],
            'productivity': ['schedule', 'calendar', 'plan', 'organize', 'manage'],
            'research': ['research', 'learn', 'study', 'analyze', 'investigate'],
            'content_creation': ['content', 'video', 'media', 'edit', 'create'],
            'marketing': ['campaign', 'marketing', 'audience', 'social', 'brand'],
            'finance': ['budget', 'finance', 'expense', 'invoice', 'cash'],
            'development': ['deploy', 'build', 'devops', 'release', 'codebase'],
        }

        for domain, keywords in domain_keywords.items():
            if any(word in message_lower for word in keywords):
                requirements['domain'] = domain
                requirements['domain_label'] = domain.replace('_', ' ').title()
                break

        important_words = ['automate', 'monitor', 'analyze', 'create', 'manage', 'track', 'notify', 'report']
        requirements['keywords'] = [word for word in important_words if word in message_lower]

        return requirements

    def _fallback_answer_parse(self, message: str) -> Dict[str, Any]:
        """Heuristic interpretation of follow-up answers."""

        info: Dict[str, Any] = {}
        message_lower = message.lower()

        if any(word in message_lower for word in ['automate', 'automation', 'automatic']):
            info['goal'] = 'automation'
        elif any(word in message_lower for word in ['monitor', 'observe', 'watch', 'track']):
            info['goal'] = 'monitoring'
        elif any(word in message_lower for word in ['analyze', 'report', 'audit', 'summarize']):
            info['goal'] = 'analysis'

        if any(word in message_lower for word in ['continuous', 'always', '24/7', 'realtime']):
            info['frequency'] = 'continuous'
        elif any(word in message_lower for word in ['hourly', 'every hour']):
            info['frequency'] = 'hourly'
        elif any(word in message_lower for word in ['daily', 'every day']):
            info['frequency'] = 'daily'
        elif any(word in message_lower for word in ['weekly', 'every week']):
            info['frequency'] = 'weekly'
        elif any(word in message_lower for word in ['on-demand', 'when i ask', 'manual']):
            info['frequency'] = 'on-demand'

        if any(word in message_lower for word in ['full automation', 'fully automatic', 'hands-off']):
            info['automation_level'] = 'full'
        elif any(word in message_lower for word in ['approval', 'semi', 'review first']):
            info['automation_level'] = 'semi'
        elif 'manual' in message_lower:
            info['automation_level'] = 'manual'

        return info

    def _fallback_team_design(self, requirements: Dict) -> List[Dict[str, Any]]:
        """Fallback deterministic team design."""

        domain = requirements.get('domain', 'general')
        goal = requirements.get('goal', 'automation')
        frequency = requirements.get('frequency', 'daily')

        domain_specialist = self.domain_specialists.get(domain, self.domain_specialists['general'])
        agents: List[Dict[str, Any]] = [
            {
                'name': f"{requirements.get('domain_label', domain.replace('_', ' ').title())} Coordinator",
                'type': 'coordinator',
                'purpose': f"Routes tasks and coordinates the {domain.replace('_', ' ')} team",
                'capabilities': ['task_routing', 'team_coordination', 'conflict_resolution'],
                'priority': 1,
            }
        ]

        agents.append({
            'name': domain_specialist['name'],
            'type': 'specialist',
            'purpose': domain_specialist['purpose'],
            'capabilities': domain_specialist['capabilities'],
            'priority': 2,
        })

        if goal == 'automation':
            agents.append({
                'name': 'Automation Specialist',
                'type': 'automation',
                'purpose': 'Automates repetitive tasks and orchestrates triggers',
                'capabilities': ['workflow_automation', 'trigger_management', 'task_execution'],
                'priority': 3,
            })

        if goal == 'monitoring' and frequency in ['continuous', 'hourly']:
            agents.append({
                'name': 'Continuous Monitor',
                'type': 'monitor',
                'purpose': 'Continuously monitors systems and escalates anomalies',
                'capabilities': ['real_time_monitoring', 'alerting', 'logging'],
                'priority': 4,
            })

        return agents

    def _fallback_modification_parse(self, message: str) -> Dict[str, Any]:
        """Heuristic parsing of modification feedback."""

        message_lower = message.lower()
        result: Dict[str, Any] = {'agents': []}

        if any(word in message_lower for word in ['remove', 'drop', 'no longer need']):
            result['action'] = 'remove'
        elif any(word in message_lower for word in ['add', 'include', 'another']):
            result['action'] = 'add'
        elif any(word in message_lower for word in ['change', 'modify', 'adjust', 'rename']):
            result['action'] = 'update'
        else:
            result['action'] = 'none'

        return result

    def _generate_agent_name(self, agent_type: str) -> str:
        """Generate a friendly agent name based on type."""

        base_names = {
            'coordinator': 'Coordination Lead',
            'specialist': 'Specialist',
            'monitor': 'Monitoring Agent',
            'analyst': 'Insight Analyst',
            'automation': 'Automation Specialist',
        }
        base = base_names.get(agent_type, 'Specialist')
        suffix = datetime.utcnow().strftime('%H%M%S')
        return f"{base} {suffix}"

    def _is_affirmative(self, message: str) -> bool:
        """Determine if message indicates approval."""

        normalized = message.strip().lower()
        positive_phrases = ['yes', 'looks good', 'sounds good', 'approved', 'ship it', 'go ahead', 'do it', 'deploy']
        negative_phrases = ['no', 'not yet', 'wait', 'hold on', 'change', 'adjust', 'tweak']

        if any(phrase in normalized for phrase in positive_phrases):
            return True
        if any(phrase in normalized for phrase in negative_phrases):
            return False

        llm_prompt = (
            "Decide if the following message means the user approves proceeding with deployment. "
            "Respond with JSON {\"approve\": true|false}.\n\n"
            f"Message: {message}"
        )

        structured = self._call_llm(llm_prompt, expect_json=True)
        if structured:
            try:
                data = json.loads(structured)
                return bool(data.get('approve'))
            except json.JSONDecodeError:
                logger.debug("Affirmation parsing failed; defaulting to False")

        return False
    
    def _handle_initial(self, message: str, context: Dict, history: List[Dict]) -> Dict[str, Any]:
        """Handle the initial user description of needs"""

        # Analyze the user's needs
        requirements = self._analyze_requirements(message)

        # Update context
        context["stage"] = "gathering_requirements"
        context["requirements"] = requirements
        context["original_request"] = message

        # Ask clarifying questions
        questions = self._generate_clarifying_questions(requirements)
        context['clarifyingQuestions'] = questions

        question_html = ''.join(
            f"<strong>{idx + 1}. {item['question']}</strong><br>"
            f"<span style=\"color: #6b7280;\">{item['helper']}</span><br><br>"
            for idx, item in enumerate(questions)
        )

        response = (
            "Great! I understand you need help with: "
            f"<strong>{requirements.get('domain_label', requirements.get('domain', 'general tasks').title())}</strong>."
            "<br><br>"
            "To create the perfect team for you, I'd like to ask a few quick questions:<br><br>"
            f"{question_html}"
            "Just answer naturally - I'll take it from here! 😊"
        )
        
        return {
            'response': response,
            'context': context,
            'isHtml': True
        }
    
    def _handle_gathering(self, message: str, context: Dict, history: List[Dict]) -> Dict[str, Any]:
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
            
            summary_html = self._create_team_summary(proposed_agents)
            context['teamSummary'] = summary_html

            return {
                'response': response,
                'context': context,
                'isHtml': True,
                'review': {
                    'agents': proposed_agents,
                    'requirements': requirements,
                    'summaryHtml': summary_html
                }
            }
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

        if self._is_affirmative(message_lower):
            # User approved - deploy agents
            context["stage"] = "deploying"
            return self._deploy_agents(context)
        else:
            # User wants modifications
            proposed_agents = context.get('proposedAgents', [])

            # Modify based on feedback
            modifications = self._parse_modifications(message)
            updated_agents = self._apply_modifications(proposed_agents, modifications)

            context['proposedAgents'] = updated_agents
            summary_html = self._create_team_summary(updated_agents)
            context['teamSummary'] = summary_html

            response = f"""I've updated your team based on your feedback:<br><br>

{summary_html}

<strong>How does this look now?</strong> Reply "yes" to create these agents!"""

            return {
                'response': response,
                'context': context,
                'isHtml': True,
                'review': {
                    'agents': updated_agents,
                    'requirements': context.get('requirements', {}),
                    'summaryHtml': summary_html
                }
            }

    def _handle_deploying(self, message: str, context: Dict, history: List[Dict]) -> Dict[str, Any]:
        """Deploy the agent team"""
        return self._deploy_agents(context)
    
    def _handle_complete(self, message: str, context: Dict, history: List[Dict]) -> Dict[str, Any]:
        """Handle post-deployment conversation"""

        response = """Your agents are up and running! You can:<br><br>

• <strong>View them in Langflow:</strong> <a href="http://localhost:7860" target="_blank">http://localhost:7860</a><br>
• <strong>Manage workflows in n8n:</strong> <a href="http://localhost:5678" target="_blank">http://localhost:5678</a><br>
• <strong>Create another team:</strong> Just tell me what you need!<br><br>

What would you like to do next?"""

        return {
            'response': response,
            'context': context,
            'isHtml': True
        }

    # ------------------------------------------------------------------
    # Structured UI entry points
    # ------------------------------------------------------------------

    def apply_structured_modifications(self, context: Dict, modifications: Dict[str, Any]) -> Dict[str, Any]:
        """Apply modifications coming from structured UI controls."""

        proposed_agents = context.get('proposedAgents', [])
        updated_agents = self._apply_modifications(proposed_agents, modifications)
        context['proposedAgents'] = updated_agents
        summary_html = self._create_team_summary(updated_agents)
        context['teamSummary'] = summary_html

        return {
            'response': "I've updated your team configuration based on the changes you selected.",
            'context': context,
            'isHtml': True,
            'review': {
                'agents': updated_agents,
                'requirements': context.get('requirements', {}),
                'summaryHtml': summary_html
            }
        }

    def deploy_team(self, context: Dict) -> Dict[str, Any]:
        """Deploy agents directly from structured UI confirmation."""

        context['stage'] = 'deploying'
        return self._deploy_agents(context)
    
    def _analyze_requirements(self, message: str) -> Dict[str, Any]:
        """Analyze user's initial requirements"""
        
        llm_prompt = (
            "Analyze the following user request and extract structured requirements for an automation "
            "agent team. Respond with JSON containing: domain (snake_case), domain_label (title case), "
            "goal (short phrase), frequency (continuous|daily|weekly|monthly|on-demand|adhoc), "
            "automation_level (manual|semi|full), tasks (list of strings), success_metrics (list of strings), "
            "and notes (string). If something is unclear, leave it empty instead of guessing.\n\n"
            f"Request: {message}"
        )

        structured = self._call_llm(llm_prompt, expect_json=True)
        if structured:
            try:
                data = json.loads(structured)
                data.setdefault('domain', data.get('domain', 'general'))
                data.setdefault('domain_label', data.get('domain_label', data['domain'].replace('_', ' ').title()))
                data.setdefault('tasks', data.get('tasks', []))
                data.setdefault('notes', data.get('notes', ''))
                data.setdefault('keywords', data.get('keywords', []))
                return data
            except json.JSONDecodeError:
                logger.warning("LLM returned invalid JSON for requirements; using heuristic fallback")

        return self._fallback_requirements(message)
    
    def _generate_clarifying_questions(self, requirements: Dict) -> List[Dict[str, str]]:
        """Generate questions based on initial requirements"""

        questions: List[Dict[str, str]] = [
            {
                'question': "What's your main goal?",
                'helper': 'Feel free to describe the outcome you expect in natural language.',
            },
            {
                'question': "How often should this run?",
                'helper': 'For example: continuously, daily, weekly, or only when you ask.',
            },
            {
                'question': "How hands-off do you want it to be?",
                'helper': 'Choose between full automation, approval required, or manual triggers.',
            },
        ]

        llm_prompt = (
            "You are collecting clarification questions for an automation project. Suggest up to two "
            "additional follow-up questions tailored to this requirement summary. Respond with JSON "
            "array under key 'questions', each item having 'question' and 'helper'.\n\n"
            f"Requirements: {json.dumps(requirements)}"
        )

        structured = self._call_llm(llm_prompt, expect_json=True)
        if structured:
            try:
                data = json.loads(structured)
                extras = data.get('questions', [])
                for item in extras[:2]:
                    if isinstance(item, dict) and 'question' in item and 'helper' in item:
                        questions.append({
                            'question': item['question'],
                            'helper': item['helper'],
                        })
            except json.JSONDecodeError:
                logger.debug("Failed to parse LLM-generated questions; using defaults")

        return questions

    def _parse_user_answers(self, message: str) -> Dict[str, Any]:
        """Parse user's answers to questions"""
        
        llm_prompt = (
            "Interpret the user's response while gathering requirements for an automation agent team. "
            "Return JSON with keys: goal, frequency, automation_level, tasks (list of strings), "
            "success_metrics (list of strings), blockers (list of strings). Leave entries empty if not provided.\n\n"
            f"Response: {message}"
        )

        structured = self._call_llm(llm_prompt, expect_json=True)
        if structured:
            try:
                data = json.loads(structured)
                return {k: v for k, v in data.items() if v}
            except json.JSONDecodeError:
                logger.debug("Failed to parse LLM interpretation; using heuristic fallback")

        return self._fallback_answer_parse(message)
    
    def _has_sufficient_info(self, requirements: Dict) -> bool:
        """Check if we have enough info to design a team"""
        
        required_fields = ['domain', 'goal', 'frequency']
        return all(requirements.get(field) for field in required_fields)
    
    def _design_agent_team(self, requirements: Dict) -> List[Dict[str, Any]]:
        """Design a custom agent team based on requirements"""
        
        llm_prompt = (
            "Design a specialized multi-agent team for the OsMEN automation platform. "
            "Given the structured requirements below, propose between two and four agents (always include a coordinator). "
            "Return JSON with an 'agents' array. Each agent must include: name, type "
            "(coordinator|specialist|monitor|analyst|automation), purpose, capabilities (list of strings), and priority (int).\n\n"
            f"Requirements: {json.dumps(requirements)}"
        )

        structured = self._call_llm(llm_prompt, expect_json=True)
        if structured:
            try:
                data = json.loads(structured)
                agents = data.get('agents', [])
                cleaned: List[Dict[str, Any]] = []
                for agent in agents:
                    if not isinstance(agent, dict):
                        continue
                    if not {'name', 'type', 'purpose'} <= agent.keys():
                        continue
                    capabilities = agent.get('capabilities') or []
                    if isinstance(capabilities, str):
                        capabilities = [cap.strip() for cap in capabilities.split(',') if cap.strip()]

                    cleaned.append({
                        'name': agent['name'],
                        'type': agent.get('type', 'specialist'),
                        'purpose': agent['purpose'],
                        'capabilities': capabilities,
                        'priority': agent.get('priority', len(cleaned) + 1)
                    })

                if cleaned:
                    cleaned.sort(key=lambda item: item.get('priority', 999))
                    return cleaned
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM-designed team; using fallback templates")

        return self._fallback_team_design(requirements)
    
    def _create_team_summary(self, agents: List[Dict]) -> str:
        """Create HTML summary of proposed agent team"""

        summary = '<div style="background: #f0f4ff; padding: 15px; border-radius: 8px; margin: 10px 0;">'

        for i, agent in enumerate(agents, 1):
            capabilities = agent.get('capabilities', [])
            if isinstance(capabilities, str):
                capabilities = [capabilities]
            summary += f'<div style="margin: 10px 0;"><strong>{i}. {agent["name"]}</strong><br>'
            summary += f'<span style="color: #666;">Purpose: {agent["purpose"]}</span><br>'
            summary += (
                f'<span style="color: #667eea; font-size: 0.9em;">Capabilities: '
                f"{', '.join(capabilities)}</span></div>"
            )
        
        summary += '</div>'
        
        return summary

    def _parse_modifications(self, message: str) -> Dict[str, Any]:
        """Parse user's modification requests"""
        
        llm_prompt = (
            "The user is providing feedback about a proposed multi-agent team. "
            "Summarize the requested changes in JSON. Use keys: action (add|remove|update|approve|none), "
            "agents (list). Each agent entry should include: name (if referenced), index (if provided), "
            "type, purpose, capabilities (list of strings), keep (boolean), and action (add|remove|update). "
            "Also include approval true/false if the user explicitly approves deployment.\n\n"
            f"Feedback: {message}"
        )

        structured = self._call_llm(llm_prompt, expect_json=True)
        if structured:
            try:
                data = json.loads(structured)
                if data.get('approval') is True:
                    return {'action': 'approve'}
                return data
            except json.JSONDecodeError:
                logger.debug("Failed to parse modification feedback; using fallback")

        return self._fallback_modification_parse(message)

    def _apply_modifications(self, agents: List[Dict], modifications: Dict) -> List[Dict]:
        """Apply user's requested modifications to agent team"""

        if not modifications:
            return agents

        if modifications.get('action') == 'approve':
            return agents

        updated_agents: List[Dict[str, Any]] = []
        lookup = {idx: agent for idx, agent in enumerate(agents)}

        structured_agents = modifications.get('agents') or []

        for idx, agent in lookup.items():
            directive = next(
                (
                    item
                    for item in structured_agents
                    if item.get('index') == idx or item.get('name') == agent.get('name')
                ),
                None,
            )

            if directive:
                if directive.get('keep') is False or directive.get('action') == 'remove':
                    continue

                updated_agent = agent.copy()
                for field in ['name', 'type', 'purpose']:
                    if directive.get(field):
                        updated_agent[field] = directive[field]

                capabilities = directive.get('capabilities')
                if isinstance(capabilities, list) and capabilities:
                    updated_agent['capabilities'] = capabilities

                updated_agents.append(updated_agent)
            else:
                updated_agents.append(agent)

        # Add new agents requested by the user
        for directive in structured_agents:
            if directive.get('action') == 'add' or directive.get('index') in (None, 'new'):
                if directive.get('keep') is False:
                    continue
                name = directive.get('name') or self._generate_agent_name(directive.get('type', 'specialist'))
                new_agent = {
                    'name': name,
                    'type': directive.get('type', 'specialist'),
                    'purpose': directive.get('purpose', 'Assists the coordinator'),
                    'capabilities': directive.get('capabilities', ['task_execution']),
                }
                updated_agents.append(new_agent)

        if not updated_agents:
            return agents

        return updated_agents
    
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
