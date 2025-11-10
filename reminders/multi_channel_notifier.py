#!/usr/bin/env python3
"""
Multi-Channel Notification Manager

Sends notifications across multiple channels (email, dashboard, SMS).
Part of v1.6.0 - Adaptive Reminders & Health Integration.
"""

import os
from datetime import datetime
from typing import List, Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json


class MultiChannelNotifier:
    """Send notifications across multiple channels"""
    
    def __init__(self):
        self.smtp_config = {
            "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "username": os.getenv("SMTP_USERNAME", ""),
            "password": os.getenv("SMTP_PASSWORD", ""),
            "from_email": os.getenv("SMTP_FROM", "osmen@localhost")
        }
        
        self.user_email = os.getenv("USER_EMAIL", "")
        self.dashboard_notifications = []
    
    def send_notification(self, reminder: Dict[str, Any], channels: List[str] = None) -> Dict[str, bool]:
        """
        Send notification across specified channels
        
        Args:
            reminder: Reminder dict
            channels: List of channels to use
        
        Returns:
            Dict of channel -> success status
        """
        if channels is None:
            channels = reminder.get('channels', ['email'])
        
        results = {}
        
        for channel in channels:
            if channel == 'email':
                results['email'] = self._send_email(reminder)
            elif channel == 'dashboard':
                results['dashboard'] = self._send_to_dashboard(reminder)
            elif channel == 'notification':
                results['notification'] = self._send_push_notification(reminder)
        
        return results
    
    def _send_email(self, reminder: Dict[str, Any]) -> bool:
        """Send email notification"""
        if not self.user_email or not self.smtp_config["username"]:
            print(f"📧 [Email] Would send: {reminder['task_title']}")
            return True
        
        try:
            subject = f"⏰ Reminder: {reminder['task_title']}"
            
            body = f"""
Task Reminder

Task: {reminder['task_title']}
Reminder Time: {reminder['reminder_time'][:19]}
Escalation Level: {reminder.get('escalation_level', 'moderate').upper()}

This is reminder #{reminder.get('sent_count', 0) + 1} for this task.

---
OsMEN Adaptive Reminder System
"""
            
            msg = MIMEText(body, 'plain')
            msg['Subject'] = subject
            msg['From'] = self.smtp_config["from_email"]
            msg['To'] = self.user_email
            
            with smtplib.SMTP(self.smtp_config["host"], self.smtp_config["port"]) as server:
                server.starttls()
                server.login(self.smtp_config["username"], self.smtp_config["password"])
                server.send_message(msg)
            
            print(f"✅ Email sent to {self.user_email}")
            return True
        
        except Exception as e:
            print(f"❌ Email failed: {e}")
            return False
    
    def _send_to_dashboard(self, reminder: Dict[str, Any]) -> bool:
        """Add to dashboard notifications"""
        notification = {
            "id": reminder["id"],
            "task_title": reminder["task_title"],
            "created_at": datetime.now().isoformat(),
            "escalation_level": reminder.get("escalation_level", "moderate"),
            "status": "unread"
        }
        
        self.dashboard_notifications.append(notification)
        print(f"📊 [Dashboard] Added: {reminder['task_title']}")
        return True
    
    def _send_push_notification(self, reminder: Dict[str, Any]) -> bool:
        """Send push notification (placeholder)"""
        print(f"🔔 [Push] Would send: {reminder['task_title']}")
        return True
    
    def get_dashboard_notifications(self) -> List[Dict[str, Any]]:
        """Get unread dashboard notifications"""
        return [n for n in self.dashboard_notifications if n["status"] == "unread"]


def main():
    print("Multi-Channel Notifier - Ready")


if __name__ == "__main__":
    main()
