#!/usr/bin/env python3
"""
OsMEN LLM Provider Smoke Tests
Tests connectivity and basic functionality of all configured LLM providers
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import Dict, Tuple, Optional
from datetime import datetime


class LLMProviderTester:
    def __init__(self):
        self.results = []
        self.project_root = Path(__file__).parent.parent.parent
        self.load_env()
        
    def load_env(self):
        """Load environment variables from .env file"""
        env_file = self.project_root / ".env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
                        
    def add_result(self, provider: str, status: bool, message: str, response_time: float = 0):
        """Add test result"""
        self.results.append({
            "provider": provider,
            "status": status,
            "message": message,
            "response_time": response_time
        })
        
    def test_openai(self) -> bool:
        """Test OpenAI API connectivity"""
        api_key = os.getenv("OPENAI_API_KEY", "")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        if not api_key or api_key == "your_openai_api_key_here":
            self.add_result("OpenAI", False, "API key not configured")
            return False
            
        try:
            start_time = datetime.now()
            response = requests.get(
                f"{base_url}/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                models = response.json().get("data", [])
                self.add_result(
                    "OpenAI", 
                    True, 
                    f"Connected successfully. {len(models)} models available",
                    elapsed
                )
                return True
            else:
                self.add_result(
                    "OpenAI", 
                    False, 
                    f"API error: {response.status_code} - {response.text[:100]}"
                )
                return False
        except Exception as e:
            self.add_result("OpenAI", False, f"Connection failed: {str(e)}")
            return False
            
    def test_anthropic(self) -> bool:
        """Test Anthropic Claude API connectivity"""
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        
        if not api_key or api_key == "your_anthropic_api_key_here":
            self.add_result("Anthropic Claude", False, "API key not configured")
            return False
            
        try:
            start_time = datetime.now()
            # Test with a minimal completion request
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-opus-20240229",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "Hi"}]
                },
                timeout=30
            )
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if response.status_code in [200, 201]:
                self.add_result(
                    "Anthropic Claude", 
                    True, 
                    "Connected successfully. API responding",
                    elapsed
                )
                return True
            else:
                self.add_result(
                    "Anthropic Claude", 
                    False, 
                    f"API error: {response.status_code} - {response.text[:100]}"
                )
                return False
        except Exception as e:
            self.add_result("Anthropic Claude", False, f"Connection failed: {str(e)}")
            return False
            
    def test_lm_studio(self) -> bool:
        """Test LM Studio local API connectivity"""
        url = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
        
        try:
            start_time = datetime.now()
            response = requests.get(f"{url}/models", timeout=5)
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                models = response.json().get("data", [])
                if models:
                    model_names = [m.get("id", "unknown") for m in models[:3]]
                    self.add_result(
                        "LM Studio", 
                        True, 
                        f"Connected. Models: {', '.join(model_names)}",
                        elapsed
                    )
                else:
                    self.add_result(
                        "LM Studio", 
                        False, 
                        "Connected but no models loaded"
                    )
                return len(models) > 0
            else:
                self.add_result(
                    "LM Studio", 
                    False, 
                    f"API error: {response.status_code}"
                )
                return False
        except requests.exceptions.ConnectionError:
            self.add_result(
                "LM Studio", 
                False, 
                "Not running. Download from lmstudio.ai and start server"
            )
            return False
        except Exception as e:
            self.add_result("LM Studio", False, f"Connection failed: {str(e)}")
            return False
            
    def test_ollama(self) -> bool:
        """Test Ollama API connectivity"""
        url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        
        try:
            start_time = datetime.now()
            response = requests.get(f"{url}/api/tags", timeout=5)
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                if models:
                    model_names = [m.get("name", "unknown") for m in models[:3]]
                    self.add_result(
                        "Ollama", 
                        True, 
                        f"Connected. Models: {', '.join(model_names)}",
                        elapsed
                    )
                else:
                    self.add_result(
                        "Ollama", 
                        False, 
                        "Connected but no models installed. Run: make pull-models"
                    )
                return len(models) > 0
            else:
                self.add_result(
                    "Ollama", 
                    False, 
                    f"API error: {response.status_code}"
                )
                return False
        except requests.exceptions.ConnectionError:
            self.add_result(
                "Ollama", 
                False, 
                "Not running. Start with: docker compose --profile ollama up -d"
            )
            return False
        except Exception as e:
            self.add_result("Ollama", False, f"Connection failed: {str(e)}")
            return False
            
    def test_github_copilot(self) -> bool:
        """Test GitHub Copilot API (limited availability)"""
        token = os.getenv("GITHUB_TOKEN", "")
        
        if not token or token == "your_github_token_here":
            self.add_result(
                "GitHub Copilot", 
                False, 
                "Token not configured (GitHub Copilot has limited API access)"
            )
            return False
            
        # Note: GitHub Copilot doesn't have a public API for completion requests
        # This is just a placeholder check
        self.add_result(
            "GitHub Copilot", 
            False, 
            "API validation not available (use through IDE integration)"
        )
        return False
        
    def test_amazon_q(self) -> bool:
        """Test Amazon Q connectivity (limited availability)"""
        access_key = os.getenv("AWS_ACCESS_KEY_ID", "")
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        
        if not access_key or access_key == "your_aws_access_key_here":
            self.add_result(
                "Amazon Q", 
                False, 
                "AWS credentials not configured"
            )
            return False
            
        # Note: Amazon Q is primarily IDE-integrated, not a direct API
        self.add_result(
            "Amazon Q", 
            False, 
            "API validation not available (use through AWS IDE integration)"
        )
        return False
        
    def print_results(self):
        """Print test results"""
        print("\n" + "="*70)
        print("OsMEN LLM Provider Smoke Tests")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70 + "\n")
        
        # Group by category
        production_providers = ["OpenAI", "Anthropic Claude", "GitHub Copilot", "Amazon Q"]
        local_providers = ["LM Studio", "Ollama"]
        
        print("📡 Production LLM Providers:")
        for result in self.results:
            if result["provider"] in production_providers:
                self._print_result(result)
                
        print("\n🏠 Local LLM Providers:")
        for result in self.results:
            if result["provider"] in local_providers:
                self._print_result(result)
                
        # Summary
        passed = sum(1 for r in self.results if r["status"])
        total = len(self.results)
        
        print("\n" + "="*70)
        print(f"Summary: {passed}/{total} providers operational")
        print("="*70)
        
        if passed == 0:
            print("\n⚠️  No LLM providers available!")
            print("Configure at least one provider in .env to use OsMEN agents.")
            print("\nRecommended: LM Studio (local) or OpenAI (cloud)")
            return 1
        elif passed < len(production_providers + local_providers):
            print(f"\n✅ {passed} provider(s) operational")
            print("This is sufficient to run OsMEN. Configure more for redundancy.")
            return 0
        else:
            print("\n✅ All configured providers operational!")
            return 0
            
    def _print_result(self, result: dict):
        """Print a single result"""
        status_icon = "✅" if result["status"] else "❌"
        print(f"{status_icon} {result['provider']:<20} {result['message']}")
        if result.get("response_time", 0) > 0:
            print(f"   Response time: {result['response_time']:.2f}s")


def main():
    """Run all LLM provider smoke tests"""
    tester = LLMProviderTester()
    
    print("🔍 Testing LLM Provider Connectivity...\n")
    
    # Test all providers
    tester.test_openai()
    tester.test_anthropic()
    tester.test_github_copilot()
    tester.test_amazon_q()
    tester.test_lm_studio()
    tester.test_ollama()
    
    # Print results
    return tester.print_results()


if __name__ == "__main__":
    sys.exit(main())
