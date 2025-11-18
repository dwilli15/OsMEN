#!/usr/bin/env python3
"""
Performance testing script for OsMEN.
Tests agent response times and resource usage.
"""

import time
import sys
import statistics
from pathlib import Path
from typing import List, Dict
import subprocess


class PerformanceTester:
    """Run performance tests on OsMEN agents."""
    
    def __init__(self):
        self.results: List[Dict] = []
        
    def test_agent(self, agent_name: str, iterations: int = 5) -> Dict:
        """
        Test an agent's performance.
        
        Args:
            agent_name: Name of the agent to test
            iterations: Number of test iterations
            
        Returns:
            Dict with performance metrics
        """
        durations = []
        successes = 0
        
        print(f"Testing {agent_name}...")
        
        for i in range(iterations):
            start_time = time.time()
            
            try:
                # Try to run the agent
                agent_path = Path(f"agents/{agent_name}/{agent_name}_agent.py")
                
                if agent_path.exists():
                    result = subprocess.run(
                        ['python3', str(agent_path)],
                        capture_output=True,
                        timeout=30,
                        check=False
                    )
                    
                    duration = time.time() - start_time
                    durations.append(duration)
                    
                    if result.returncode == 0:
                        successes += 1
                else:
                    print(f"  ⚠️  Agent file not found: {agent_path}")
                    return {}
                    
            except subprocess.TimeoutExpired:
                print(f"  ⚠️  Iteration {i+1} timed out")
            except Exception as e:
                print(f"  ⚠️  Error in iteration {i+1}: {e}")
        
        if not durations:
            return {}
        
        metrics = {
            'agent': agent_name,
            'iterations': iterations,
            'successes': successes,
            'success_rate': (successes / iterations) * 100,
            'min_time': min(durations),
            'max_time': max(durations),
            'mean_time': statistics.mean(durations),
            'median_time': statistics.median(durations),
        }
        
        if len(durations) > 1:
            metrics['stdev'] = statistics.stdev(durations)
        
        return metrics
    
    def print_results(self, metrics: Dict):
        """Print formatted test results."""
        if not metrics:
            return
            
        print(f"\n  Agent: {metrics['agent']}")
        print(f"  Success Rate: {metrics['success_rate']:.1f}% ({metrics['successes']}/{metrics['iterations']})")
        print(f"  Mean Time: {metrics['mean_time']:.3f}s")
        print(f"  Median Time: {metrics['median_time']:.3f}s")
        print(f"  Min Time: {metrics['min_time']:.3f}s")
        print(f"  Max Time: {metrics['max_time']:.3f}s")
        if 'stdev' in metrics:
            print(f"  Std Dev: {metrics['stdev']:.3f}s")


def main():
    """Main entry point."""
    print("🚀 OsMEN Performance Testing")
    print("=" * 70)
    print()
    
    # List of agents to test
    agents_to_test = [
        'daily_brief',
        'focus_guardrails',
        'boot_hardening',
    ]
    
    tester = PerformanceTester()
    all_results = []
    
    for agent in agents_to_test:
        metrics = tester.test_agent(agent, iterations=3)
        if metrics:
            tester.print_results(metrics)
            all_results.append(metrics)
    
    print()
    print("=" * 70)
    print()
    
    if not all_results:
        print("❌ No agents could be tested")
        sys.exit(1)
    
    # Summary statistics
    print("📊 Summary:")
    print()
    
    avg_response_time = statistics.mean([r['mean_time'] for r in all_results])
    avg_success_rate = statistics.mean([r['success_rate'] for r in all_results])
    
    print(f"  Average Response Time: {avg_response_time:.3f}s")
    print(f"  Average Success Rate: {avg_success_rate:.1f}%")
    print()
    
    # Performance recommendations
    print("💡 Recommendations:")
    print()
    
    if avg_response_time > 10:
        print("  ⚠️  Response times are high (>10s)")
        print("     - Consider using faster LLM models (e.g., GPT-3.5 instead of GPT-4)")
        print("     - Check network latency to LLM APIs")
        print("     - Review agent prompt complexity")
    elif avg_response_time > 5:
        print("  ℹ️  Response times are moderate (5-10s)")
        print("     - Acceptable for most use cases")
        print("     - Can be improved with caching or local LLMs")
    else:
        print("  ✅ Response times are good (<5s)")
    
    print()
    
    if avg_success_rate < 80:
        print("  ⚠️  Success rate is low (<80%)")
        print("     - Check agent configurations")
        print("     - Verify LLM API keys are valid")
        print("     - Review error logs")
    elif avg_success_rate < 95:
        print("  ℹ️  Success rate is acceptable (80-95%)")
        print("     - Some occasional failures are normal")
    else:
        print("  ✅ Success rate is excellent (>95%)")
    
    print()
    print("=" * 70)
    print()
    print("✅ Performance testing complete")
    print()
    print("Note: For comprehensive performance testing, see docs/PERFORMANCE.md")
    
    sys.exit(0)


if __name__ == '__main__':
    main()
