#!/usr/bin/env python3
"""
Innovation Validation and Audit Trail

Validates innovation proposals and maintains audit trail.
Part of v1.3.0 Innovation Agent Framework.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Tuple


class InnovationValidator:
    """Validate innovation proposals"""
    
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent.parent
        self.audit_log_path = self.repo_root / ".copilot" / "innovation_audit.jsonl"
    
    def validate_discovery(self, discovery: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a discovery dict has all required fields
        
        Returns:
            (is_valid, list_of_errors)
        """
        required_fields = ["id", "title", "source", "link", "relevance_score"]
        errors = []
        
        for field in required_fields:
            if field not in discovery:
                errors.append(f"Missing required field: {field}")
        
        # Validate relevance score
        if "relevance_score" in discovery:
            score = discovery["relevance_score"]
            if not isinstance(score, (int, float)):
                errors.append("relevance_score must be a number")
            elif score < 1 or score > 10:
                errors.append("relevance_score must be between 1 and 10")
        
        return len(errors) == 0, errors
    
    def validate_evaluation(self, evaluation: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate an evaluation dict
        
        Returns:
            (is_valid, list_of_errors)
        """
        required_fields = [
            "relevance_score", "complexity_score", "impact_score",
            "risk_level", "no_code_compatible"
        ]
        errors = []
        
        for field in required_fields:
            if field not in evaluation:
                errors.append(f"Missing required field: {field}")
        
        # Validate scores
        for score_field in ["relevance_score", "complexity_score", "impact_score"]:
            if score_field in evaluation:
                score = evaluation[score_field]
                if score is not None and not isinstance(score, (int, float)):
                    errors.append(f"{score_field} must be a number or null")
                elif score is not None and (score < 1 or score > 10):
                    errors.append(f"{score_field} must be between 1 and 10")
        
        # Validate risk level
        if "risk_level" in evaluation:
            risk = evaluation["risk_level"]
            if risk is not None and risk not in ["low", "medium", "high"]:
                errors.append("risk_level must be 'low', 'medium', or 'high'")
        
        # Validate no_code_compatible
        if "no_code_compatible" in evaluation:
            no_code = evaluation["no_code_compatible"]
            if no_code is not None and not isinstance(no_code, bool):
                errors.append("no_code_compatible must be boolean or null")
        
        return len(errors) == 0, errors
    
    def log_action(self, action_type: str, data: Dict[str, Any], user: str = "system"):
        """
        Log action to audit trail
        
        Args:
            action_type: Type of action (discovered, evaluated, approved, rejected, implemented)
            data: Action data
            user: Who performed action
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action_type": action_type,
            "user": user,
            "data": data
        }
        
        # Append to JSONL file
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.audit_log_path, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_audit_trail(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent audit trail entries
        
        Args:
            limit: Maximum number of entries to return
        
        Returns:
            List of audit entries (newest first)
        """
        if not self.audit_log_path.exists():
            return []
        
        entries = []
        with open(self.audit_log_path, 'r') as f:
            for line in f:
                try:
                    entries.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
        
        # Return newest first
        return list(reversed(entries[-limit:]))
    
    def generate_audit_report(self, days: int = 30) -> str:
        """
        Generate audit report for last N days
        
        Args:
            days: Number of days to include
        
        Returns:
            Markdown report
        """
        cutoff = datetime.now(timezone.utc).timestamp() - (days * 24 * 60 * 60)
        
        entries = self.get_audit_trail(limit=1000)
        
        # Filter by date
        recent_entries = [
            e for e in entries
            if datetime.fromisoformat(e["timestamp"]).timestamp() > cutoff
        ]
        
        # Count by action type
        action_counts = {}
        for entry in recent_entries:
            action = entry["action_type"]
            action_counts[action] = action_counts.get(action, 0) + 1
        
        report = f"# Innovation Audit Report\n\n"
        report += f"**Period:** Last {days} days\n"
        report += f"**Total Actions:** {len(recent_entries)}\n\n"
        
        report += "## Activity Summary\n\n"
        for action, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True):
            report += f"- **{action.capitalize()}:** {count}\n"
        report += "\n"
        
        if recent_entries:
            report += "## Recent Activity\n\n"
            for entry in recent_entries[:20]:  # Show last 20
                timestamp = entry["timestamp"][:19].replace('T', ' ')
                action = entry["action_type"]
                user = entry.get("user", "unknown")
                
                report += f"- **{timestamp}** - {action} by {user}\n"
                
                # Add details based on action type
                data = entry.get("data", {})
                if "title" in data:
                    report += f"  - {data['title']}\n"
        
        return report


class InnovationLogger:
    """Centralized logging for innovation framework"""
    
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent.parent
        self.log_path = self.repo_root / ".copilot" / "innovation.log"
    
    def log(self, level: str, message: str, **kwargs):
        """
        Log message
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR)
            message: Log message
            **kwargs: Additional context
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        log_line = f"[{timestamp}] {level:8s} {message}"
        
        if kwargs:
            context = " ".join(f"{k}={v}" for k, v in kwargs.items())
            log_line += f" | {context}"
        
        # Append to log file
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, 'a') as f:
            f.write(log_line + '\n')
        
        # Also print for visibility
        print(log_line)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.log("DEBUG", message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.log("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.log("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.log("ERROR", message, **kwargs)


def main():
    """Test validation and logging"""
    validator = InnovationValidator()
    logger = InnovationLogger()
    
    # Test discovery validation
    test_discovery = {
        "id": "test_001",
        "title": "Test Discovery",
        "source": "github",
        "link": "https://example.com",
        "relevance_score": 8
    }
    
    is_valid, errors = validator.validate_discovery(test_discovery)
    logger.info(f"Discovery validation: {is_valid}", errors=errors)
    
    # Test evaluation validation
    test_evaluation = {
        "relevance_score": 8,
        "complexity_score": 5,
        "impact_score": 7,
        "risk_level": "medium",
        "no_code_compatible": True
    }
    
    is_valid, errors = validator.validate_evaluation(test_evaluation)
    logger.info(f"Evaluation validation: {is_valid}", errors=errors)
    
    # Test audit logging
    validator.log_action("discovered", test_discovery)
    validator.log_action("evaluated", test_evaluation)
    
    # Generate report
    report = validator.generate_audit_report(days=30)
    print("\n" + report)


if __name__ == "__main__":
    main()
