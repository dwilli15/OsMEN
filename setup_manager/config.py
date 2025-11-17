#!/usr/bin/env python3
"""
Configuration Manager for OsMEN
Centralized configuration handling with environment variable support
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages OsMEN configuration from environment variables and config files
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager
        
        Args:
            config_path: Path to .env file
        """
        self.config_path = config_path or Path.cwd() / '.env'
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from environment"""
        if self.config_path.exists():
            load_dotenv(self.config_path)
            logger.info(f"Loaded configuration from {self.config_path}")
        else:
            logger.warning(f"Configuration file not found: {self.config_path}")
        
        # Load all environment variables
        self.config = dict(os.environ)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, os.getenv(key, default))
    
    def set(self, key: str, value: Any):
        """Set configuration value
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value
        os.environ[key] = str(value)
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for a specific agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dictionary of agent configuration
        """
        prefix = f"{agent_name.upper()}_"
        agent_config = {}
        
        for key, value in self.config.items():
            if key.startswith(prefix):
                # Remove prefix from key
                config_key = key[len(prefix):].lower()
                agent_config[config_key] = value
        
        return agent_config
    
    def get_enabled_agents(self) -> List[str]:
        """Get list of enabled agents
        
        Returns:
            List of agent names
        """
        enabled = self.get('ENABLED_AGENTS', '')
        if enabled:
            return [a.strip() for a in enabled.split(',')]
        
        # Default to all agents if not specified
        return [
            'boot_hardening',
            'daily_brief',
            'focus_guardrails',
            'personal_assistant',
            'content_creator',
            'email_manager',
            'live_caption',
            'audiobook_creator',
            'podcast_creator',
            'os_optimizer',
            'security_ops',
            'knowledge_management'
        ]
    
    def validate(self) -> bool:
        """Validate configuration
        
        Returns:
            True if configuration is valid
        """
        required_keys = [
            'N8N_BASIC_AUTH_PASSWORD',
            'WEB_SECRET_KEY'
        ]
        
        for key in required_keys:
            if not self.get(key):
                logger.error(f"Missing required configuration: {key}")
                return False
        
        # Check at least one LLM provider is configured
        llm_providers = [
            'OPENAI_API_KEY',
            'ANTHROPIC_API_KEY',
            'LM_STUDIO_URL',
            'OLLAMA_URL'
        ]
        
        if not any(self.get(key) for key in llm_providers):
            logger.warning("No LLM provider configured")
        
        return True
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM provider configuration
        
        Returns:
            Dictionary of LLM configuration
        """
        return {
            'openai_key': self.get('OPENAI_API_KEY'),
            'anthropic_key': self.get('ANTHROPIC_API_KEY'),
            'github_token': self.get('GITHUB_TOKEN'),
            'aws_access_key': self.get('AWS_ACCESS_KEY_ID'),
            'aws_secret_key': self.get('AWS_SECRET_ACCESS_KEY'),
            'lm_studio_url': self.get('LM_STUDIO_URL', 'http://localhost:1234/v1'),
            'ollama_url': self.get('OLLAMA_URL', 'http://localhost:11434')
        }
    
    def get_service_urls(self) -> Dict[str, str]:
        """Get service URLs
        
        Returns:
            Dictionary of service URLs
        """
        return {
            'langflow': self.get('LANGFLOW_URL', 'http://localhost:7860'),
            'n8n': self.get('N8N_URL', 'http://localhost:5678'),
            'qdrant': self.get('QDRANT_URL', 'http://localhost:6333'),
            'postgres': f"postgresql://{self.get('POSTGRES_USER', 'postgres')}:{self.get('POSTGRES_PASSWORD', 'postgres')}@{self.get('POSTGRES_HOST', 'localhost')}:{self.get('POSTGRES_PORT', '5432')}/{self.get('POSTGRES_DB', 'postgres')}",
            'redis': f"redis://{self.get('REDIS_HOST', 'localhost')}:{self.get('REDIS_PORT', '6379')}"
        }
