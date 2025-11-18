#!/usr/bin/env python3
"""
Codex CLI Bridge
Provides integration with OpenAI Codex CLI for code generation and assistance
"""

import os
import logging
import subprocess
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class CodexBridge:
    """
    Bridge to OpenAI Codex CLI
    
    Provides:
    - Code generation from natural language
    - Code completion and suggestions
    - Code explanation and documentation
    - Code review and quality checks
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Codex CLI Bridge
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.cli_available = self._check_cli_availability()
        
        if not self.api_key:
            logger.warning("No OpenAI API key provided for Codex CLI")
        
        logger.info("CodexBridge initialized")
    
    def _check_cli_availability(self) -> bool:
        """Check if Codex CLI is available"""
        try:
            # Check if codex command exists
            result = subprocess.run(
                ['which', 'codex'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def generate_code(
        self,
        prompt: str,
        language: str = 'python',
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """Generate code from natural language prompt
        
        Args:
            prompt: Natural language description of desired code
            language: Programming language
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary with generated code and metadata
        """
        if not self.cli_available:
            logger.warning("Codex CLI not available, using fallback")
            return self._fallback_generate_code(prompt, language)
        
        try:
            # Use Codex CLI to generate code
            cmd = [
                'codex',
                'generate',
                '--language', language,
                '--max-tokens', str(max_tokens),
                '--prompt', prompt
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'code': result.stdout,
                    'language': language,
                    'prompt': prompt
                }
            else:
                logger.error(f"Codex CLI error: {result.stderr}")
                return self._fallback_generate_code(prompt, language)
                
        except Exception as e:
            logger.error(f"Failed to generate code: {e}")
            return self._fallback_generate_code(prompt, language)
    
    def _fallback_generate_code(
        self,
        prompt: str,
        language: str
    ) -> Dict[str, Any]:
        """Fallback code generation using OpenAI API directly"""
        if not self.api_key:
            return {
                'success': False,
                'error': 'No Codex CLI or API key available'
            }
        
        try:
            from tools.codex_cli.codex_integration import CodexCLIIntegration
            
            integration = CodexCLIIntegration(api_key=self.api_key)
            result = integration.generate_code(prompt, language)
            
            return {
                'success': True,
                'code': result.get('code', ''),
                'language': language,
                'prompt': prompt,
                'method': 'api_fallback'
            }
        except Exception as e:
            logger.error(f"Fallback code generation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def explain_code(self, code: str, language: str = 'python') -> Dict[str, Any]:
        """Explain what a piece of code does
        
        Args:
            code: Code to explain
            language: Programming language
            
        Returns:
            Dictionary with explanation
        """
        prompt = f"Explain this {language} code:\n\n{code}"
        
        try:
            if self.cli_available:
                cmd = [
                    'codex',
                    'explain',
                    '--language', language,
                    '--code', code
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    return {
                        'success': True,
                        'explanation': result.stdout,
                        'code': code,
                        'language': language
                    }
            
            # Fallback to API
            return self._api_explain_code(code, language)
            
        except Exception as e:
            logger.error(f"Failed to explain code: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _api_explain_code(self, code: str, language: str) -> Dict[str, Any]:
        """Explain code using OpenAI API"""
        try:
            from tools.codex_cli.codex_integration import CodexCLIIntegration
            
            integration = CodexCLIIntegration(api_key=self.api_key)
            result = integration.explain_code(code)
            
            return {
                'success': True,
                'explanation': result.get('explanation', ''),
                'code': code,
                'language': language
            }
        except Exception as e:
            logger.error(f"API code explanation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def review_code(self, code: str, language: str = 'python') -> Dict[str, Any]:
        """Review code for quality and best practices
        
        Args:
            code: Code to review
            language: Programming language
            
        Returns:
            Dictionary with review results
        """
        try:
            if self.cli_available:
                cmd = [
                    'codex',
                    'review',
                    '--language', language,
                    '--code', code
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    return {
                        'success': True,
                        'review': result.stdout,
                        'code': code,
                        'language': language
                    }
            
            # Fallback
            return {
                'success': True,
                'review': 'Code review functionality requires Codex CLI',
                'code': code,
                'language': language
            }
            
        except Exception as e:
            logger.error(f"Failed to review code: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def complete_code(
        self,
        partial_code: str,
        language: str = 'python',
        max_tokens: int = 100
    ) -> Dict[str, Any]:
        """Complete partial code
        
        Args:
            partial_code: Incomplete code to complete
            language: Programming language
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary with completed code
        """
        try:
            from tools.codex_cli.codex_integration import CodexCLIIntegration
            
            integration = CodexCLIIntegration(api_key=self.api_key)
            result = integration.complete_code(partial_code)
            
            return {
                'success': True,
                'completion': result.get('completion', ''),
                'original': partial_code,
                'language': language
            }
        except Exception as e:
            logger.error(f"Failed to complete code: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of Codex CLI bridge
        
        Returns:
            Dictionary with status information
        """
        return {
            'cli_available': self.cli_available,
            'api_key_configured': bool(self.api_key),
            'operational': self.cli_available or bool(self.api_key)
        }


def main():
    """Test Codex CLI Bridge"""
    bridge = CodexBridge()
    
    print("\n" + "="*80)
    print("Codex CLI Bridge Test")
    print("="*80)
    
    # Check status
    status = bridge.get_status()
    print(f"\nStatus:")
    print(f"  CLI Available: {status['cli_available']}")
    print(f"  API Key Configured: {status['api_key_configured']}")
    print(f"  Operational: {status['operational']}")
    
    # Test code generation
    if status['operational']:
        print("\nGenerating code...")
        result = bridge.generate_code(
            "Create a function to calculate fibonacci numbers",
            language='python'
        )
        
        if result['success']:
            print(f"Generated code:\n{result['code']}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
    
    print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    main()
