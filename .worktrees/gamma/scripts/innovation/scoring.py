#!/usr/bin/env python3
"""
Innovation Scoring Algorithm

Evaluates discovered innovations against OsMEN criteria.
Part of v1.3.0 Innovation Agent Framework.
"""

from typing import Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class ScoringCriteria:
    """Scoring thresholds from innovation guidelines"""
    relevance_threshold: int = 7
    complexity_threshold: int = 6
    impact_threshold: int = 6
    risk_threshold: str = "medium"
    requires_no_code: bool = True


class InnovationScorer:
    """Score and evaluate innovations"""
    
    def __init__(self):
        self.criteria = ScoringCriteria()
        self.risk_levels = ["low", "medium", "high"]
    
    def score_relevance(self, discovery: Dict[str, Any]) -> int:
        """
        Score relevance to grad school workflows (1-10)
        
        High relevance (8-10):
        - Direct agent framework improvements
        - Calendar/scheduling features
        - No-code automation tools
        
        Medium relevance (5-7):
        - General LLM improvements
        - Workflow orchestration
        - Memory/context systems
        
        Low relevance (1-4):
        - Tangentially related
        - Research-only
        - Not applicable to use case
        """
        title = discovery.get('title', '').lower()
        summary = discovery.get('summary', '').lower()
        content = f"{title} {summary}"
        
        score = 5  # Base score
        
        # High priority keywords (+2 each)
        high_keywords = [
            "grad school", "student", "academic",
            "calendar", "scheduling", "syllabus",
            "no-code", "low-code", "visual",
            "autonomous agent", "multi-agent"
        ]
        
        # Medium priority keywords (+1 each)
        medium_keywords = [
            "workflow", "automation", "orchestration",
            "memory", "context", "planning",
            "task management", "reminder"
        ]
        
        for keyword in high_keywords:
            if keyword in content:
                score += 2
        
        for keyword in medium_keywords:
            if keyword in content:
                score += 1
        
        return min(score, 10)
    
    def score_complexity(self, discovery: Dict[str, Any], metadata: Dict[str, Any] = None) -> int:
        """
        Score integration complexity (1-10, lower is better)
        
        Low complexity (1-3):
        - Drop-in replacement
        - Well-documented API
        - Existing Python bindings
        
        Medium complexity (4-6):
        - Requires new dependencies
        - Some refactoring needed
        - Documentation available
        
        High complexity (7-10):
        - Major architectural changes
        - Poor documentation
        - Unstable/experimental
        """
        if metadata is None:
            return 5  # Default medium complexity
        
        score = 5
        
        # Check for complexity indicators
        if metadata.get('has_python_sdk', False):
            score -= 2
        
        if metadata.get('well_documented', False):
            score -= 1
        
        if metadata.get('requires_refactor', False):
            score += 2
        
        if metadata.get('experimental', False):
            score += 2
        
        if metadata.get('breaking_changes', False):
            score += 3
        
        return max(min(score, 10), 1)
    
    def score_impact(self, discovery: Dict[str, Any], metadata: Dict[str, Any] = None) -> int:
        """
        Score expected impact on user experience (1-10)
        
        High impact (8-10):
        - Significantly reduces manual work
        - Enables new capabilities
        - Major time savings
        
        Medium impact (5-7):
        - Incremental improvements
        - Better user experience
        - Modest time savings
        
        Low impact (1-4):
        - Minor optimization
        - Edge case improvement
        - Negligible impact
        """
        if metadata is None:
            return 5  # Default medium impact
        
        score = 5
        
        # Impact indicators
        if metadata.get('enables_new_capability', False):
            score += 3
        
        if metadata.get('time_savings_hours_per_week', 0) > 2:
            score += 2
        elif metadata.get('time_savings_hours_per_week', 0) > 0:
            score += 1
        
        if metadata.get('improves_accuracy', False):
            score += 1
        
        if metadata.get('reduces_errors', False):
            score += 1
        
        return min(score, 10)
    
    def assess_risk(self, discovery: Dict[str, Any], metadata: Dict[str, Any] = None) -> str:
        """
        Assess risk level (low/medium/high)
        
        Low risk:
        - Mature, stable technology
        - No security concerns
        - Easy rollback
        
        Medium risk:
        - Some uncertainty
        - Minor security considerations
        - Rollback possible with effort
        
        High risk:
        - Experimental/unstable
        - Security/privacy concerns
        - Difficult rollback
        """
        if metadata is None:
            return "medium"  # Default medium risk
        
        risk_factors = []
        
        if metadata.get('experimental', False):
            risk_factors.append('experimental')
        
        if metadata.get('security_concerns', False):
            risk_factors.append('security')
        
        if metadata.get('privacy_concerns', False):
            risk_factors.append('privacy')
        
        if metadata.get('breaking_changes', False):
            risk_factors.append('breaking')
        
        if metadata.get('immature', False):
            risk_factors.append('immature')
        
        # Assess overall risk
        if len(risk_factors) >= 3:
            return "high"
        elif len(risk_factors) >= 1:
            return "medium"
        else:
            return "low"
    
    def check_no_code_compatible(self, discovery: Dict[str, Any], metadata: Dict[str, Any] = None) -> bool:
        """
        Check if innovation is compatible with no-code requirement
        
        Compatible if:
        - Has visual interface or dashboard
        - Configuration via UI/web
        - No code changes required for basic use
        
        Not compatible if:
        - Requires code modification
        - CLI-only interface
        - Complex configuration files
        """
        if metadata is None:
            return False  # Default to not compatible (needs verification)
        
        if metadata.get('has_web_ui', False):
            return True
        
        if metadata.get('visual_config', False):
            return True
        
        if metadata.get('requires_coding', True):  # Default to requiring code
            return False
        
        return False
    
    def evaluate(self, discovery: Dict[str, Any], metadata: Dict[str, Any] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Evaluate discovery against all criteria
        
        Returns:
            (passes_threshold, evaluation_details)
        """
        # Score each dimension
        relevance = self.score_relevance(discovery)
        complexity = self.score_complexity(discovery, metadata)
        impact = self.score_impact(discovery, metadata)
        risk = self.assess_risk(discovery, metadata)
        no_code = self.check_no_code_compatible(discovery, metadata)
        
        evaluation = {
            "relevance_score": relevance,
            "complexity_score": complexity,
            "impact_score": impact,
            "risk_level": risk,
            "no_code_compatible": no_code,
            "passes_threshold": False,
            "recommendation": "reject"
        }
        
        # Check against thresholds
        passes = (
            relevance >= self.criteria.relevance_threshold and
            complexity <= self.criteria.complexity_threshold and
            impact >= self.criteria.impact_threshold and
            self._risk_acceptable(risk) and
            (no_code if self.criteria.requires_no_code else True)
        )
        
        evaluation["passes_threshold"] = passes
        
        # Generate recommendation
        if passes:
            evaluation["recommendation"] = "approve"
        elif relevance >= self.criteria.relevance_threshold:
            evaluation["recommendation"] = "research_more"
        else:
            evaluation["recommendation"] = "reject"
        
        return passes, evaluation
    
    def _risk_acceptable(self, risk: str) -> bool:
        """Check if risk level is acceptable"""
        risk_order = {"low": 0, "medium": 1, "high": 2}
        threshold_order = risk_order[self.criteria.risk_threshold]
        risk_level_order = risk_order[risk]
        return risk_level_order <= threshold_order


def main():
    """Test scoring algorithm"""
    scorer = InnovationScorer()
    
    # Test discovery
    test_discovery = {
        "title": "New Autonomous Agent Framework for Academic Task Management",
        "summary": "A no-code framework for building multi-agent systems with built-in calendar integration"
    }
    
    test_metadata = {
        "has_python_sdk": True,
        "well_documented": True,
        "requires_refactor": False,
        "experimental": False,
        "breaking_changes": False,
        "enables_new_capability": True,
        "time_savings_hours_per_week": 3,
        "has_web_ui": True,
        "requires_coding": False
    }
    
    passes, evaluation = scorer.evaluate(test_discovery, test_metadata)
    
    print("Test Evaluation:")
    print(f"  Relevance: {evaluation['relevance_score']}/10")
    print(f"  Complexity: {evaluation['complexity_score']}/10")
    print(f"  Impact: {evaluation['impact_score']}/10")
    print(f"  Risk: {evaluation['risk_level']}")
    print(f"  No-Code: {evaluation['no_code_compatible']}")
    print(f"  Passes: {passes}")
    print(f"  Recommendation: {evaluation['recommendation']}")


if __name__ == "__main__":
    main()
