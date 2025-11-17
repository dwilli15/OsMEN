#!/usr/bin/env python3
"""
Setup Manager - Centralized initialization for OsMEN
Manages agent lifecycle, configuration, and dependencies
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .config import ConfigManager

logger = logging.getLogger(__name__)


class SetupManager:
    """
    Central manager for OsMEN setup and initialization
    
    Responsibilities:
    - Initialize system configuration
    - Bootstrap agents with proper dependencies
    - Manage service connections (Langflow, n8n, Qdrant, etc.)
    - Provide unified interface for system-wide changes
    - Bridge to Codex CLI and Copilot CLI
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize Setup Manager
        
        Args:
            config_path: Path to configuration file (.env or config.yaml)
        """
        self.config_path = config_path or Path.cwd() / '.env'
        self.config_manager = ConfigManager(self.config_path)
        self.initialized_agents = {}
        self.service_connections = {}
        self._setup_logging()
        
        logger.info("SetupManager initialized")
    
    def _setup_logging(self):
        """Configure logging for setup manager"""
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def validate_environment(self) -> Dict[str, bool]:
        """Validate system environment and dependencies
        
        Returns:
            Dictionary of validation results
        """
        validations = {
            'docker': self._check_docker(),
            'python': self._check_python_version(),
            'config': self._check_config(),
            'directories': self._check_directories(),
            'services': self._check_services()
        }
        
        logger.info(f"Environment validation: {validations}")
        return validations
    
    def _check_docker(self) -> bool:
        """Check if Docker is available"""
        try:
            import subprocess
            result = subprocess.run(
                ['docker', 'info'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def _check_python_version(self) -> bool:
        """Check if Python version is compatible"""
        return sys.version_info >= (3, 12)
    
    def _check_config(self) -> bool:
        """Check if configuration is valid"""
        return self.config_manager.validate()
    
    def _check_directories(self) -> bool:
        """Check if required directories exist"""
        required_dirs = [
            'agents',
            'tools',
            'gateway',
            'web',
            'langflow',
            'n8n'
        ]
        
        for dir_name in required_dirs:
            if not (Path.cwd() / dir_name).exists():
                logger.warning(f"Missing directory: {dir_name}")
                return False
        return True
    
    def _check_services(self) -> bool:
        """Check if required services are accessible"""
        # This will be implemented to check Langflow, n8n, Qdrant, etc.
        # For now, just return True
        return True
    
    def initialize_agent(self, agent_name: str, **kwargs) -> Any:
        """Initialize an agent with proper configuration
        
        Args:
            agent_name: Name of the agent to initialize
            **kwargs: Additional configuration parameters
            
        Returns:
            Initialized agent instance
        """
        if agent_name in self.initialized_agents:
            logger.info(f"Agent {agent_name} already initialized")
            return self.initialized_agents[agent_name]
        
        # Get agent configuration
        agent_config = self.config_manager.get_agent_config(agent_name)
        agent_config.update(kwargs)
        
        # Import and initialize agent
        try:
            agent_module = __import__(
                f'agents.{agent_name}.{agent_name}_agent',
                fromlist=['*']
            )
            
            # Get agent class (assumes class name is AgentNameAgent)
            class_name = ''.join(word.capitalize() for word in agent_name.split('_')) + 'Agent'
            agent_class = getattr(agent_module, class_name)
            
            # Initialize agent
            agent_instance = agent_class(**agent_config)
            self.initialized_agents[agent_name] = agent_instance
            
            logger.info(f"Successfully initialized {agent_name}")
            return agent_instance
            
        except Exception as e:
            logger.error(f"Failed to initialize {agent_name}: {e}")
            raise
    
    def initialize_all_agents(self) -> Dict[str, Any]:
        """Initialize all enabled agents
        
        Returns:
            Dictionary of initialized agents
        """
        enabled_agents = self.config_manager.get_enabled_agents()
        
        for agent_name in enabled_agents:
            try:
                self.initialize_agent(agent_name)
            except Exception as e:
                logger.error(f"Failed to initialize {agent_name}: {e}")
        
        return self.initialized_agents
    
    def connect_to_langflow(self) -> bool:
        """Establish connection to Langflow
        
        Returns:
            True if connection successful
        """
        langflow_url = self.config_manager.get('LANGFLOW_URL', 'http://localhost:7860')
        
        try:
            import requests
            response = requests.get(f"{langflow_url}/health", timeout=5)
            if response.status_code == 200:
                self.service_connections['langflow'] = langflow_url
                logger.info(f"Connected to Langflow at {langflow_url}")
                return True
        except Exception as e:
            logger.warning(f"Failed to connect to Langflow: {e}")
        
        return False
    
    def connect_to_n8n(self) -> bool:
        """Establish connection to n8n
        
        Returns:
            True if connection successful
        """
        n8n_url = self.config_manager.get('N8N_URL', 'http://localhost:5678')
        
        try:
            import requests
            response = requests.get(f"{n8n_url}/healthz", timeout=5)
            if response.status_code == 200:
                self.service_connections['n8n'] = n8n_url
                logger.info(f"Connected to n8n at {n8n_url}")
                return True
        except Exception as e:
            logger.warning(f"Failed to connect to n8n: {e}")
        
        return False
    
    def connect_to_qdrant(self) -> bool:
        """Establish connection to Qdrant vector database
        
        Returns:
            True if connection successful
        """
        qdrant_url = self.config_manager.get('QDRANT_URL', 'http://localhost:6333')
        
        try:
            import requests
            response = requests.get(f"{qdrant_url}/", timeout=5)
            if response.status_code == 200:
                self.service_connections['qdrant'] = qdrant_url
                logger.info(f"Connected to Qdrant at {qdrant_url}")
                return True
        except Exception as e:
            logger.warning(f"Failed to connect to Qdrant: {e}")
        
        return False
    
    def initialize_services(self) -> Dict[str, bool]:
        """Initialize all service connections
        
        Returns:
            Dictionary of service connection statuses
        """
        return {
            'langflow': self.connect_to_langflow(),
            'n8n': self.connect_to_n8n(),
            'qdrant': self.connect_to_qdrant()
        }
    
    def apply_system_change(self, change_type: str, params: Dict[str, Any]) -> bool:
        """Apply a system-wide change
        
        Args:
            change_type: Type of change (config, agent, service, etc.)
            params: Parameters for the change
            
        Returns:
            True if change applied successfully
        """
        logger.info(f"Applying system change: {change_type} with params {params}")
        
        if change_type == 'config':
            return self._apply_config_change(params)
        elif change_type == 'agent':
            return self._apply_agent_change(params)
        elif change_type == 'service':
            return self._apply_service_change(params)
        else:
            logger.error(f"Unknown change type: {change_type}")
            return False
    
    def _apply_config_change(self, params: Dict[str, Any]) -> bool:
        """Apply configuration change"""
        try:
            for key, value in params.items():
                self.config_manager.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Failed to apply config change: {e}")
            return False
    
    def _apply_agent_change(self, params: Dict[str, Any]) -> bool:
        """Apply agent-specific change"""
        agent_name = params.get('agent_name')
        if not agent_name:
            logger.error("No agent_name provided")
            return False
        
        try:
            # Reinitialize agent with new params
            if agent_name in self.initialized_agents:
                del self.initialized_agents[agent_name]
            
            self.initialize_agent(agent_name, **params)
            return True
        except Exception as e:
            logger.error(f"Failed to apply agent change: {e}")
            return False
    
    def _apply_service_change(self, params: Dict[str, Any]) -> bool:
        """Apply service-specific change"""
        # This would trigger service restarts, config updates, etc.
        logger.info(f"Service change requested: {params}")
        return True
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status
        
        Returns:
            Dictionary with system status information
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'initialized_agents': list(self.initialized_agents.keys()),
            'service_connections': self.service_connections,
            'environment_valid': all(self.validate_environment().values()),
            'config_valid': self.config_manager.validate()
        }
    
    def shutdown(self):
        """Gracefully shutdown all agents and connections"""
        logger.info("Shutting down SetupManager")
        
        # Shutdown agents
        for agent_name, agent in self.initialized_agents.items():
            logger.info(f"Shutting down agent: {agent_name}")
            # Call shutdown method if available
            if hasattr(agent, 'shutdown'):
                try:
                    agent.shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down {agent_name}: {e}")
        
        # Clear connections
        self.service_connections.clear()
        self.initialized_agents.clear()
        
        logger.info("SetupManager shutdown complete")


def main():
    """Main entry point for setup manager"""
    manager = SetupManager()
    
    print("\n" + "="*80)
    print("OsMEN Setup Manager")
    print("="*80)
    
    # Validate environment
    print("\nValidating environment...")
    validations = manager.validate_environment()
    for check, status in validations.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {check}")
    
    # Initialize services
    print("\nInitializing services...")
    services = manager.initialize_services()
    for service, status in services.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {service}")
    
    # Get system status
    print("\nSystem Status:")
    status = manager.get_system_status()
    print(f"  Environment Valid: {status['environment_valid']}")
    print(f"  Config Valid: {status['config_valid']}")
    print(f"  Connected Services: {len([s for s in services.values() if s])}/{len(services)}")
    
    print("\n" + "="*80)
    print("Setup Manager Ready")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
