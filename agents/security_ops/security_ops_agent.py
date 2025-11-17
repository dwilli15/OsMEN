#!/usr/bin/env python3
"""
Security Operations Agent
Provides white hat security operations, monitoring, and vulnerability assessment
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)


class SecurityOpsAgent:
    """Security Operations Agent for white hat operations and monitoring."""
    
    def __init__(self):
        """Initialize the Security Operations Agent."""
        logger.info("SecurityOpsAgent initialized successfully")
        self.scan_results = []
        self.security_events = []
        self.vulnerabilities = []
    
    def run_security_scan(self, scan_type: str, targets: List[str]) -> Dict:
        """Run security scan.
        
        Args:
            scan_type: Type of scan (port, vulnerability, compliance, etc.)
            targets: List of scan targets
            
        Returns:
            Dictionary with scan results
        """
        scan = {
            "id": len(self.scan_results) + 1,
            "type": scan_type,
            "targets": targets,
            "status": "completed",
            "findings": [],
            "started_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat()
        }
        self.scan_results.append(scan)
        logger.info(f"Completed {scan_type} scan on {len(targets)} targets")
        return scan
    
    def log_security_event(self, event_type: str, severity: str, 
                          description: str, details: Dict = None) -> Dict:
        """Log a security event.
        
        Args:
            event_type: Event type (intrusion, anomaly, alert, etc.)
            severity: Severity level (low, medium, high, critical)
            description: Event description
            details: Additional event details
            
        Returns:
            Dictionary with event details
        """
        event = {
            "id": len(self.security_events) + 1,
            "type": event_type,
            "severity": severity,
            "description": description,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.security_events.append(event)
        logger.warning(f"Security event ({severity}): {description}")
        return event
    
    def assess_vulnerability(self, component: str, vulnerability_type: str, 
                           cvss_score: float, remediation: str) -> Dict:
        """Assess and log a vulnerability.
        
        Args:
            component: Affected component
            vulnerability_type: Type of vulnerability
            cvss_score: CVSS score (0-10)
            remediation: Remediation steps
            
        Returns:
            Dictionary with vulnerability details
        """
        vulnerability = {
            "id": len(self.vulnerabilities) + 1,
            "component": component,
            "type": vulnerability_type,
            "cvss_score": cvss_score,
            "severity": self._get_severity_from_cvss(cvss_score),
            "remediation": remediation,
            "status": "open",
            "discovered_at": datetime.now().isoformat()
        }
        self.vulnerabilities.append(vulnerability)
        logger.warning(f"Vulnerability found in {component}: {vulnerability_type} (CVSS: {cvss_score})")
        return vulnerability
    
    def _get_severity_from_cvss(self, score: float) -> str:
        """Convert CVSS score to severity level."""
        if score >= 9.0:
            return "critical"
        elif score >= 7.0:
            return "high"
        elif score >= 4.0:
            return "medium"
        else:
            return "low"
    
    def get_security_posture(self) -> Dict:
        """Get overall security posture assessment.
        
        Returns:
            Dictionary with security posture metrics
        """
        open_critical = len([v for v in self.vulnerabilities 
                           if v["status"] == "open" and v["severity"] == "critical"])
        open_high = len([v for v in self.vulnerabilities 
                        if v["status"] == "open" and v["severity"] == "high"])
        
        posture = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": max(0, 100 - (open_critical * 20) - (open_high * 10)),
            "risk_level": "low" if open_critical == 0 and open_high == 0 else 
                         "high" if open_critical > 0 else "medium",
            "open_vulnerabilities": {
                "critical": open_critical,
                "high": open_high,
                "medium": len([v for v in self.vulnerabilities 
                             if v["status"] == "open" and v["severity"] == "medium"]),
                "low": len([v for v in self.vulnerabilities 
                          if v["status"] == "open" and v["severity"] == "low"])
            },
            "recent_events": len([e for e in self.security_events 
                                if e["timestamp"].startswith(datetime.now().date().isoformat())])
        }
        logger.info(f"Security posture: {posture['risk_level']} risk, score {posture['overall_score']}")
        return posture
    
    def generate_security_report(self) -> Dict:
        """Generate comprehensive security operations report.
        
        Returns:
            Dictionary with security status and statistics
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "operational",
            "security_posture": self.get_security_posture(),
            "statistics": {
                "total_scans": len(self.scan_results),
                "total_events": len(self.security_events),
                "total_vulnerabilities": len(self.vulnerabilities),
                "open_vulnerabilities": len([v for v in self.vulnerabilities if v["status"] == "open"]),
                "critical_events_today": len([
                    e for e in self.security_events 
                    if e["severity"] == "critical" and 
                    e["timestamp"].startswith(datetime.now().date().isoformat())
                ])
            }
        }


if __name__ == "__main__":
    # Test the agent
    logging.basicConfig(level=logging.INFO)
    
    agent = SecurityOpsAgent()
    
    # Run scans
    agent.run_security_scan("port", ["192.168.1.1", "192.168.1.100"])
    agent.run_security_scan("vulnerability", ["web_server", "database"])
    
    # Log events
    agent.log_security_event("anomaly", "medium", "Unusual login pattern detected", 
                            {"source_ip": "10.0.0.15", "attempts": 5})
    
    # Assess vulnerabilities
    agent.assess_vulnerability(
        "web_server",
        "SQL Injection",
        7.5,
        "Update to latest version and implement parameterized queries"
    )
    
    # Get posture
    posture = agent.get_security_posture()
    
    # Generate report
    report = agent.generate_security_report()
    print(json.dumps(report, indent=2))
