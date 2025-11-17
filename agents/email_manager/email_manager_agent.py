#!/usr/bin/env python3
"""
Email Manager Agent
Provides email automation, contact management, and communication assistance
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)


class EmailManagerAgent:
    """Email Manager Agent for email and contact management."""
    
    def __init__(self):
        """Initialize the Email Manager Agent."""
        logger.info("EmailManagerAgent initialized successfully")
        self.contacts = []
        self.emails = []
        self.email_rules = []
    
    def add_contact(self, name: str, email: str, phone: str = "", 
                   tags: List[str] = None) -> Dict:
        """Add a new contact.
        
        Args:
            name: Contact name
            email: Email address
            phone: Phone number
            tags: List of tags for categorization
            
        Returns:
            Dictionary with contact details
        """
        contact = {
            "id": len(self.contacts) + 1,
            "name": name,
            "email": email,
            "phone": phone,
            "tags": tags or [],
            "created_at": datetime.now().isoformat()
        }
        self.contacts.append(contact)
        logger.info(f"Added contact: {name} ({email})")
        return contact
    
    def send_email(self, to: str, subject: str, body: str, 
                  cc: List[str] = None, attachments: List[str] = None) -> Dict:
        """Send an email.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            cc: CC recipients
            attachments: List of attachment paths
            
        Returns:
            Dictionary with email details
        """
        email = {
            "id": len(self.emails) + 1,
            "to": to,
            "subject": subject,
            "body": body,
            "cc": cc or [],
            "attachments": attachments or [],
            "status": "sent",
            "sent_at": datetime.now().isoformat()
        }
        self.emails.append(email)
        logger.info(f"Sent email to {to}: {subject}")
        return email
    
    def create_email_rule(self, name: str, condition: str, action: str) -> Dict:
        """Create an email automation rule.
        
        Args:
            name: Rule name
            condition: Condition to match (from, subject, contains, etc.)
            action: Action to take (move, label, forward, etc.)
            
        Returns:
            Dictionary with rule details
        """
        rule = {
            "id": len(self.email_rules) + 1,
            "name": name,
            "condition": condition,
            "action": action,
            "enabled": True,
            "created_at": datetime.now().isoformat()
        }
        self.email_rules.append(rule)
        logger.info(f"Created email rule: {name}")
        return rule
    
    def search_contacts(self, query: str) -> List[Dict]:
        """Search contacts by name, email, or tags.
        
        Args:
            query: Search query
            
        Returns:
            List of matching contacts
        """
        query_lower = query.lower()
        matches = [
            c for c in self.contacts
            if query_lower in c["name"].lower() 
            or query_lower in c["email"].lower()
            or any(query_lower in tag.lower() for tag in c["tags"])
        ]
        logger.info(f"Found {len(matches)} contacts matching '{query}'")
        return matches
    
    def generate_email_report(self) -> Dict:
        """Generate comprehensive email manager report.
        
        Returns:
            Dictionary with email manager status and statistics
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "operational",
            "statistics": {
                "total_contacts": len(self.contacts),
                "total_emails_sent": len(self.emails),
                "active_rules": len([r for r in self.email_rules if r["enabled"]]),
                "emails_today": len([
                    e for e in self.emails 
                    if e["sent_at"].startswith(datetime.now().date().isoformat())
                ])
            }
        }


if __name__ == "__main__":
    # Test the agent
    logging.basicConfig(level=logging.INFO)
    
    agent = EmailManagerAgent()
    
    # Add contacts
    agent.add_contact("John Doe", "john@example.com", "555-1234", ["work", "colleague"])
    agent.add_contact("Jane Smith", "jane@example.com", "555-5678", ["work", "manager"])
    
    # Send emails
    agent.send_email("john@example.com", "Project Update", "Here's the latest on the project...")
    
    # Create automation rule
    agent.create_email_rule("Move Newsletters", "subject:contains:newsletter", "move:folder:newsletters")
    
    # Search contacts
    agent.search_contacts("work")
    
    # Generate report
    report = agent.generate_email_report()
    print(json.dumps(report, indent=2))
