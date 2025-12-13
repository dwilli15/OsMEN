#!/usr/bin/env python3
"""
Copilot CLI Bridge
Provides integration with GitHub Copilot CLI for command assistance
"""

import os
import logging
import subprocess
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class CopilotBridge:
    """
    Bridge to GitHub Copilot CLI
    
    Provides:
    - Command-line assistance
    - Shell command suggestions
    - Git workflow help
    - Context-aware code suggestions
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize Copilot CLI Bridge
        
        Args:
            github_token: GitHub token (defaults to GITHUB_TOKEN env var)
        """
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.cli_available = self._check_cli_availability()
        
        if not self.github_token:
            logger.warning("No GitHub token provided for Copilot CLI")
        
        logger.info("CopilotBridge initialized")
    
    def _check_cli_availability(self) -> bool:
        """Check if GitHub Copilot CLI is available"""
        try:
            # Check if gh copilot is available
            result = subprocess.run(
                ['gh', 'copilot', '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def suggest_command(self, description: str) -> Dict[str, Any]:
        """Suggest a shell command based on description
        
        Args:
            description: Natural language description of desired command
            
        Returns:
            Dictionary with command suggestion
        """
        if not self.cli_available:
            logger.warning("Copilot CLI not available, using fallback")
            return self._fallback_suggest_command(description)
        
        try:
            # Prefer non-interactive shell output.
            cmd = ['gh', 'copilot', 'suggest', '--shell-out', description]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
                ,
                env={
                    **{k: v for k, v in os.environ.items() if k not in {"GITHUB_TOKEN", "GH_TOKEN"}},
                    "GH_PROMPT": "disable",
                }
            )
            
            if result.returncode == 0:
                # gh-copilot can emit extra lines; return the last non-empty line.
                stdout = (result.stdout or "").strip()
                lines = [ln.strip() for ln in stdout.splitlines() if ln.strip()]
                command = lines[-1] if lines else ""
                return {
                    'success': True,
                    'command': command,
                    'description': description
                }
            else:
                logger.error(f"Copilot CLI error: {result.stderr}")
                return self._fallback_suggest_command(description)
                
        except Exception as e:
            logger.error(f"Failed to suggest command: {e}")
            return self._fallback_suggest_command(description)
    
    def _fallback_suggest_command(self, description: str) -> Dict[str, Any]:
        """Fallback command suggestion using Copilot integration"""
        try:
            from tools.copilot_cli.copilot_integration import CopilotCLIIntegration
            
            integration = CopilotCLIIntegration(github_token=self.github_token)
            result = integration.suggest_command(description)
            
            return {
                'success': True,
                'command': result.get('suggestion', ''),
                'description': description,
                'method': 'api_fallback'
            }
        except Exception as e:
            logger.error(f"Fallback command suggestion failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def explain_command(self, command: str) -> Dict[str, Any]:
        """Explain what a command does
        
        Args:
            command: Shell command to explain
            
        Returns:
            Dictionary with explanation
        """
        if not self.cli_available:
            return self._fallback_explain_command(command)
        
        try:
            cmd = ['gh', 'copilot', 'explain', command]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'explanation': result.stdout.strip(),
                    'command': command
                }
            else:
                return self._fallback_explain_command(command)
                
        except Exception as e:
            logger.error(f"Failed to explain command: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _fallback_explain_command(self, command: str) -> Dict[str, Any]:
        """Fallback command explanation"""
        try:
            from tools.copilot_cli.copilot_integration import CopilotCLIIntegration
            
            integration = CopilotCLIIntegration(github_token=self.github_token)
            result = integration.explain_command(command)
            
            return {
                'success': True,
                'explanation': result.get('explanation', ''),
                'command': command
            }
        except Exception as e:
            logger.error(f"Fallback command explanation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_git_help(self, task: str) -> Dict[str, Any]:
        """Get help with a git task
        
        Args:
            task: Description of git task
            
        Returns:
            Dictionary with git command suggestions
        """
        description = f"git: {task}"
        return self.suggest_command(description)
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of Copilot CLI bridge
        
        Returns:
            Dictionary with status information
        """
        return {
            'cli_available': self.cli_available,
            'token_configured': bool(self.github_token),
            'operational': self.cli_available or bool(self.github_token)
        }


def main():
    """Test Copilot CLI Bridge"""
    bridge = CopilotBridge()
    
    print("\n" + "="*80)
    print("Copilot CLI Bridge Test")
    print("="*80)
    
    # Check status
    status = bridge.get_status()
    print(f"\nStatus:")
    print(f"  CLI Available: {status['cli_available']}")
    print(f"  Token Configured: {status['token_configured']}")
    print(f"  Operational: {status['operational']}")
    
    # Test command suggestion
    if status['operational']:
        print("\nSuggesting command...")
        result = bridge.suggest_command("list all files in current directory")
        
        if result['success']:
            print(f"Suggested command: {result['command']}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
    
    print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    main()
