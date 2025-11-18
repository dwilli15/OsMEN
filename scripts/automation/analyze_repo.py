#!/usr/bin/env python3
"""
Deep repository analysis to identify gaps between documentation and implementation.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Set


class RepositoryAnalyzer:
    """Analyze repository for documentation vs. implementation gaps."""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.gaps: List[Dict] = []
        
    def analyze(self):
        """Run all analysis checks."""
        print("🔍 Deep Repository Analysis")
        print("=" * 70)
        print()
        
        self.check_documented_scripts()
        self.check_documented_apis()
        self.check_documented_configs()
        self.check_documented_features()
        self.check_makefile_targets()
        self.check_docker_services()
        
    def check_documented_scripts(self):
        """Check if documented scripts actually exist."""
        print("📜 Checking documented scripts...")
        
        doc_files = list(self.repo_path.glob('docs/*.md'))
        doc_files.append(self.repo_path / 'README.md')
        
        mentioned_scripts = set()
        
        for doc_file in doc_files:
            content = doc_file.read_text()
            
            # Find script references
            # Pattern: scripts/*.py or python3 scripts/*
            script_patterns = [
                r'scripts/[a-zA-Z0-9_/]+\.py',
                r'scripts/[a-zA-Z0-9_/]+\.sh',
                r'\./scripts/[a-zA-Z0-9_/]+',
            ]
            
            for pattern in script_patterns:
                matches = re.findall(pattern, content)
                mentioned_scripts.update(matches)
        
        # Check if scripts exist
        for script_path in mentioned_scripts:
            script_path = script_path.lstrip('./')
            full_path = self.repo_path / script_path
            
            if not full_path.exists():
                self.gaps.append({
                    'type': 'missing_script',
                    'severity': 'high',
                    'item': script_path,
                    'description': f'Script documented but not found: {script_path}'
                })
        
        print(f"  Found {len(mentioned_scripts)} script references")
        print()
    
    def check_documented_apis(self):
        """Check if documented API endpoints are implemented."""
        print("🌐 Checking documented API endpoints...")
        
        api_doc = self.repo_path / 'docs' / 'API_GUIDE.md'
        
        if not api_doc.exists():
            print("  ⚠️  API_GUIDE.md not found")
            print()
            return
        
        content = api_doc.read_text()
        
        # Find API endpoints
        endpoint_pattern = r'(GET|POST|PUT|DELETE|PATCH)\s+(/[a-zA-Z0-9/_{}]+)'
        endpoints = re.findall(endpoint_pattern, content)
        
        # Check gateway.py for implementations
        gateway_file = self.repo_path / 'gateway' / 'gateway.py'
        
        if gateway_file.exists():
            gateway_content = gateway_file.read_text()
            
            missing_endpoints = []
            for method, endpoint in endpoints:
                # Simple check - look for route definition
                endpoint_simple = endpoint.replace('{', '').replace('}', '')
                if endpoint_simple not in gateway_content and endpoint not in gateway_content:
                    missing_endpoints.append(f"{method} {endpoint}")
            
            if missing_endpoints:
                self.gaps.append({
                    'type': 'missing_api_endpoints',
                    'severity': 'medium',
                    'item': ', '.join(missing_endpoints[:5]),  # First 5
                    'description': f'{len(missing_endpoints)} documented API endpoints may not be implemented'
                })
        
        print(f"  Found {len(endpoints)} documented endpoints")
        print()
    
    def check_documented_configs(self):
        """Check if documented config options are in .env.example."""
        print("⚙️  Checking configuration options...")
        
        env_example = self.repo_path / '.env.example'
        
        if not env_example.exists():
            print("  ⚠️  .env.example not found")
            print()
            return
        
        env_content = env_example.read_text()
        env_keys = set()
        
        for line in env_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key = line.split('=')[0].strip()
                env_keys.add(key)
        
        # Check documentation for mentioned config keys
        doc_files = list(self.repo_path.glob('docs/*.md'))
        doc_files.append(self.repo_path / 'README.md')
        
        mentioned_keys = set()
        for doc_file in doc_files:
            content = doc_file.read_text()
            # Find UPPERCASE_WORDS that might be env vars
            matches = re.findall(r'\b([A-Z][A-Z0-9_]{3,})\b', content)
            mentioned_keys.update(matches)
        
        # Find keys mentioned in docs but not in .env.example
        undocumented = mentioned_keys - env_keys - {
            'TODO', 'FIXME', 'NOTE', 'WARNING', 'ERROR', 'INFO',
            'HTTP', 'HTTPS', 'API', 'URL', 'URI', 'JSON', 'YAML',
            'TRUE', 'FALSE', 'NULL', 'NONE'
        }
        
        if len(undocumented) > 10:
            self.gaps.append({
                'type': 'undocumented_config',
                'severity': 'low',
                'item': f'{len(undocumented)} keys',
                'description': f'{len(undocumented)} config keys mentioned in docs but not in .env.example (may be false positives)'
            })
        
        print(f"  Found {len(env_keys)} config keys in .env.example")
        print()
    
    def check_documented_features(self):
        """Check if documented features have corresponding code."""
        print("✨ Checking documented features...")
        
        # Check agents mentioned in docs vs. actual agent directories
        readme = self.repo_path / 'README.md'
        
        if readme.exists():
            content = readme.read_text()
            
            # Find agent mentions
            agent_patterns = [
                r'`([a-z_]+)` - ',  # Backtick format
                r'\*\*([A-Z][a-zA-Z\s]+)\*\*:',  # Bold format
            ]
            
            mentioned_agents = set()
            for pattern in agent_patterns:
                matches = re.findall(pattern, content)
                mentioned_agents.update([m.lower().replace(' ', '_') for m in matches])
            
            # Find actual agent directories
            agents_dir = self.repo_path / 'agents'
            if agents_dir.exists():
                actual_agents = set()
                for item in agents_dir.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        actual_agents.add(item.name)
                
                # Check for mentioned agents that don't exist
                for agent in mentioned_agents:
                    if agent not in actual_agents and len(agent) > 3:
                        # Only report if it looks like a real agent name
                        if any(keyword in agent for keyword in ['agent', 'manager', 'brief', 'hardening', 'focus']):
                            self.gaps.append({
                                'type': 'missing_agent',
                                'severity': 'medium',
                                'item': agent,
                                'description': f'Agent "{agent}" mentioned in docs but directory not found'
                            })
        
        print("  Analyzed feature documentation")
        print()
    
    def check_makefile_targets(self):
        """Check if Makefile targets are documented."""
        print("🔨 Checking Makefile targets...")
        
        makefile = self.repo_path / 'Makefile'
        
        if not makefile.exists():
            print("  ℹ️  No Makefile found")
            print()
            return
        
        content = makefile.read_text()
        
        # Find make targets
        targets = re.findall(r'^([a-z][a-z0-9-]+):', content, re.MULTILINE)
        
        # Check if these are documented anywhere
        readme = self.repo_path / 'README.md'
        if readme.exists():
            readme_content = readme.read_text()
            
            undocumented = []
            for target in targets:
                if f'make {target}' not in readme_content:
                    undocumented.append(target)
            
            if len(undocumented) > 5:
                self.gaps.append({
                    'type': 'undocumented_make_targets',
                    'severity': 'low',
                    'item': f'{len(undocumented)} targets',
                    'description': f'{len(undocumented)} Makefile targets not documented in README'
                })
        
        print(f"  Found {len(targets)} Makefile targets")
        print()
    
    def check_docker_services(self):
        """Check if docker-compose services are documented."""
        print("🐳 Checking Docker services...")
        
        compose_file = self.repo_path / 'docker-compose.yml'
        
        if not compose_file.exists():
            print("  ℹ️  No docker-compose.yml found")
            print()
            return
        
        content = compose_file.read_text()
        
        # Find services
        services = re.findall(r'^\s{2}([a-z][a-z0-9-]+):', content, re.MULTILINE)
        
        # Check if documented
        readme = self.repo_path / 'README.md'
        if readme.exists():
            readme_content = readme.read_text()
            
            undocumented = []
            for service in services:
                if service not in readme_content:
                    undocumented.append(service)
            
            if undocumented:
                self.gaps.append({
                    'type': 'undocumented_services',
                    'severity': 'medium',
                    'item': ', '.join(undocumented),
                    'description': f'{len(undocumented)} Docker services not documented: {", ".join(undocumented)}'
                })
        
        print(f"  Found {len(services)} Docker services")
        print()
    
    def print_report(self):
        """Print analysis report."""
        print("=" * 70)
        print()
        print("📊 Analysis Results")
        print()
        
        if not self.gaps:
            print("✅ No significant gaps detected!")
            print()
            print("The repository appears to have good alignment between")
            print("documentation and implementation.")
            return
        
        # Group by severity
        critical = [g for g in self.gaps if g['severity'] == 'critical']
        high = [g for g in self.gaps if g['severity'] == 'high']
        medium = [g for g in self.gaps if g['severity'] == 'medium']
        low = [g for g in self.gaps if g['severity'] == 'low']
        
        print(f"Total gaps found: {len(self.gaps)}")
        print(f"  Critical: {len(critical)}")
        print(f"  High: {len(high)}")
        print(f"  Medium: {len(medium)}")
        print(f"  Low: {len(low)}")
        print()
        
        if critical:
            print("🔴 CRITICAL GAPS:")
            for gap in critical:
                print(f"  - {gap['description']}")
            print()
        
        if high:
            print("🟠 HIGH PRIORITY GAPS:")
            for gap in high:
                print(f"  - {gap['description']}")
            print()
        
        if medium:
            print("🟡 MEDIUM PRIORITY GAPS:")
            for gap in medium:
                print(f"  - {gap['description']}")
            print()
        
        if low:
            print("🟢 LOW PRIORITY GAPS:")
            for gap in low:
                print(f"  - {gap['description']}")
            print()


def main():
    """Main entry point."""
    repo_path = Path.cwd()
    
    analyzer = RepositoryAnalyzer(repo_path)
    analyzer.analyze()
    analyzer.print_report()
    
    print("=" * 70)
    print()
    print("Analysis complete. Review gaps above and prioritize fixes.")
    print()


if __name__ == '__main__':
    main()
