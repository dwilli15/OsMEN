#!/usr/bin/env python3
"""
CLI Bridge Manager
Unified interface for Codex and Copilot CLI bridges
"""

import logging
from typing import Dict, Optional, Any

from .codex_bridge import CodexBridge
from .copilot_bridge import CopilotBridge

logger = logging.getLogger(__name__)


class CLIBridgeManager:
    """
    Manages Codex and Copilot CLI bridges
    
    Provides unified interface for:
    - Code generation and assistance
    - Command-line help
    - Git workflows
    - Context-aware suggestions
    """
    
    def __init__(
        self,
        openai_key: Optional[str] = None,
        github_token: Optional[str] = None
    ):
        """Initialize CLI Bridge Manager
        
        Args:
            openai_key: OpenAI API key for Codex
            github_token: GitHub token for Copilot
        """
        self.codex = CodexBridge(api_key=openai_key)
        self.copilot = CopilotBridge(github_token=github_token)
        
        logger.info("CLIBridgeManager initialized")
    
    def generate_code(
        self,
        prompt: str,
        language: str = 'python',
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """Generate code using Codex
        
        Args:
            prompt: Natural language description
            language: Programming language
            max_tokens: Maximum tokens
            
        Returns:
            Generated code result
        """
        return self.codex.generate_code(prompt, language, max_tokens)
    
    def suggest_command(self, description: str) -> Dict[str, Any]:
        """Suggest shell command using Copilot
        
        Args:
            description: Task description
            
        Returns:
            Command suggestion result
        """
        return self.copilot.suggest_command(description)
    
    def explain_code(self, code: str, language: str = 'python') -> Dict[str, Any]:
        """Explain code using Codex
        
        Args:
            code: Code to explain
            language: Programming language
            
        Returns:
            Code explanation result
        """
        return self.codex.explain_code(code, language)
    
    def explain_command(self, command: str) -> Dict[str, Any]:
        """Explain shell command using Copilot
        
        Args:
            command: Command to explain
            
        Returns:
            Command explanation result
        """
        return self.copilot.explain_command(command)
    
    def review_code(self, code: str, language: str = 'python') -> Dict[str, Any]:
        """Review code using Codex
        
        Args:
            code: Code to review
            language: Programming language
            
        Returns:
            Code review result
        """
        return self.codex.review_code(code, language)
    
    def get_git_help(self, task: str) -> Dict[str, Any]:
        """Get git command help using Copilot
        
        Args:
            task: Git task description
            
        Returns:
            Git command suggestion
        """
        return self.copilot.get_git_help(task)
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all CLI bridges
        
        Returns:
            Combined status information
        """
        codex_status = self.codex.get_status()
        copilot_status = self.copilot.get_status()
        
        return {
            'codex': codex_status,
            'copilot': copilot_status,
            'operational': (
                codex_status['operational'] or 
                copilot_status['operational']
            )
        }
    
    def assist_with_task(self, task: str, task_type: str = 'auto') -> Dict[str, Any]:
        """Get assistance with a task (auto-routes to appropriate bridge)
        
        Args:
            task: Task description
            task_type: Type of task ('code', 'command', 'auto')
            
        Returns:
            Assistance result
        """
        if task_type == 'auto':
            # Auto-detect task type
            if any(word in task.lower() for word in ['function', 'class', 'code', 'python', 'java']):
                task_type = 'code'
            else:
                task_type = 'command'
        
        if task_type == 'code':
            return self.generate_code(task)
        else:
            return self.suggest_command(task)


def main():
    """Test CLI Bridge Manager"""
    manager = CLIBridgeManager()
    
    print("\n" + "="*80)
    print("CLI Bridge Manager Test")
    print("="*80)
    
    # Check status
    status = manager.get_status()
    print(f"\nStatus:")
    print(f"  Codex Operational: {status['codex']['operational']}")
    print(f"  Copilot Operational: {status['copilot']['operational']}")
    print(f"  Overall Operational: {status['operational']}")
    
    # Test auto-routing
    if status['operational']:
        print("\nTesting auto-routing...")
        
        # Code task
        result = manager.assist_with_task("Create a function to sort a list")
        print(f"\nCode task result: {result.get('success', False)}")
        
        # Command task
        result = manager.assist_with_task("list all Python files")
        print(f"Command task result: {result.get('success', False)}")
    
    print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    main()
