#!/usr/bin/env python3
"""
User Notification System

Sends notifications about innovation discoveries and approvals.
Part of v1.3.0 Innovation Agent Framework.
"""

import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List
import os


class NotificationManager:
    """Manage user notifications"""
    
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent.parent
        self.memory_path = self.repo_root / ".copilot" / "memory.json"
        self.smtp_config = self._load_smtp_config()
        self.user_email = self._load_user_email()
    
    def _load_smtp_config(self) -> Dict[str, str]:
        """Load SMTP configuration from environment"""
        return {
            "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "username": os.getenv("SMTP_USERNAME", ""),
            "password": os.getenv("SMTP_PASSWORD", ""),
            "from_email": os.getenv("SMTP_FROM", "osmen@localhost")
        }
    
    def _load_user_email(self) -> str:
        """Load user email from memory.json"""
        if self.memory_path.exists():
            with open(self.memory_path, 'r') as f:
                memory = json.load(f)
                return memory.get("user_profile", {}).get("email", "")
        return ""
    
    def send_weekly_digest(self, digest_content: str) -> bool:
        """
        Send weekly innovation digest email
        
        Args:
            digest_content: Markdown content of digest
        
        Returns:
            True if sent successfully
        """
        if not self.user_email:
            print("⚠️  No user email configured in memory.json")
            return False
        
        if not self.smtp_config["username"] or not self.smtp_config["password"]:
            print("⚠️  SMTP credentials not configured")
            print("   Set SMTP_USERNAME and SMTP_PASSWORD environment variables")
            return False
        
        # Create email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Weekly Innovation Digest - {datetime.now().strftime('%Y-%m-%d')}"
        msg['From'] = self.smtp_config["from_email"]
        msg['To'] = self.user_email
        
        # Convert markdown to plain text (basic)
        text_content = self._markdown_to_text(digest_content)
        
        # Attach text part
        text_part = MIMEText(text_content, 'plain')
        msg.attach(text_part)
        
        # Send email
        try:
            with smtplib.SMTP(self.smtp_config["host"], self.smtp_config["port"]) as server:
                server.starttls()
                server.login(self.smtp_config["username"], self.smtp_config["password"])
                server.send_message(msg)
            
            print(f"✅ Weekly digest sent to {self.user_email}")
            return True
        
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    
    def send_approval_request(self, innovations: List[Dict[str, Any]]) -> bool:
        """
        Send approval request for new innovations
        
        Args:
            innovations: List of innovations requiring approval
        
        Returns:
            True if sent successfully
        """
        if not innovations:
            return True  # Nothing to send
        
        if not self.user_email:
            print("⚠️  No user email configured")
            return False
        
        # Create email content
        subject = f"🔔 {len(innovations)} New Innovation(s) Require Approval"
        
        body = f"OsMEN Innovation Agent has discovered {len(innovations)} new innovations requiring your review:\n\n"
        
        for i, innovation in enumerate(innovations, 1):
            body += f"{i}. {innovation.get('title', 'Untitled')}\n"
            body += f"   Relevance: {innovation.get('relevance_score', 'N/A')}/10\n"
            body += f"   Link: {innovation.get('link', 'N/A')}\n\n"
        
        body += "\nPlease review at your earliest convenience.\n"
        body += "Details available in .copilot/weekly_digest_latest.md\n"
        
        # Create and send email
        msg = MIMEText(body, 'plain')
        msg['Subject'] = subject
        msg['From'] = self.smtp_config["from_email"]
        msg['To'] = self.user_email
        
        try:
            if not self.smtp_config["username"]:
                # Just log for now if SMTP not configured
                print(f"📧 Would send: {subject}")
                print(f"   To: {self.user_email}")
                return True
            
            with smtplib.SMTP(self.smtp_config["host"], self.smtp_config["port"]) as server:
                server.starttls()
                server.login(self.smtp_config["username"], self.smtp_config["password"])
                server.send_message(msg)
            
            print(f"✅ Approval request sent to {self.user_email}")
            return True
        
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    
    def send_implementation_complete(self, innovation: Dict[str, Any], 
                                    version: str, pr_url: str = None) -> bool:
        """
        Notify user that an innovation was implemented
        
        Args:
            innovation: Innovation that was implemented
            version: Version it was implemented in
            pr_url: Pull request URL
        
        Returns:
            True if sent successfully
        """
        if not self.user_email:
            return False
        
        subject = f"✅ Innovation Implemented: {innovation.get('title', 'Untitled')}"
        
        body = f"An approved innovation has been implemented:\n\n"
        body += f"Title: {innovation.get('title', 'Untitled')}\n"
        body += f"Version: {version}\n"
        
        if pr_url:
            body += f"Pull Request: {pr_url}\n"
        
        body += f"\nImplemented on: {datetime.now().strftime('%Y-%m-%d')}\n"
        
        msg = MIMEText(body, 'plain')
        msg['Subject'] = subject
        msg['From'] = self.smtp_config["from_email"]
        msg['To'] = self.user_email
        
        try:
            if not self.smtp_config["username"]:
                print(f"📧 Would send: {subject}")
                return True
            
            with smtplib.SMTP(self.smtp_config["host"], self.smtp_config["port"]) as server:
                server.starttls()
                server.login(self.smtp_config["username"], self.smtp_config["password"])
                server.send_message(msg)
            
            print(f"✅ Implementation notification sent")
            return True
        
        except Exception as e:
            print(f"❌ Failed to send notification: {e}")
            return False
    
    def _markdown_to_text(self, markdown: str) -> str:
        """
        Convert markdown to plain text (basic conversion)
        
        Args:
            markdown: Markdown content
        
        Returns:
            Plain text
        """
        text = markdown
        
        # Remove markdown headers
        text = text.replace('#', '')
        
        # Remove markdown links [text](url)
        import re
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # Remove bold/italic
        text = text.replace('**', '').replace('__', '').replace('*', '').replace('_', '')
        
        return text


def main():
    """Test notification system"""
    manager = NotificationManager()
    
    # Test approval request
    test_innovations = [
        {
            "title": "Test Innovation 1",
            "relevance_score": 8,
            "link": "https://example.com/1"
        },
        {
            "title": "Test Innovation 2",
            "relevance_score": 9,
            "link": "https://example.com/2"
        }
    ]
    
    manager.send_approval_request(test_innovations)
    
    print("\n✅ Notification system test complete")
    print("   Configure SMTP_* environment variables for email delivery")


if __name__ == "__main__":
    main()
