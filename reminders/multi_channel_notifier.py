#!/usr/bin/env python3
"""
Multi-Channel Notification Manager

Sends notifications across multiple channels (email, dashboard, push).
Part of v1.6.0 - Adaptive Reminders & Health Integration.
"""

import os
from datetime import datetime
from typing import List, Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

# Try to import Firebase Admin SDK for push notifications
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False


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
        
        # Firebase push notification setup
        self.firebase_initialized = False
        self.device_tokens = []
        self._initialize_firebase()
    
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
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK for push notifications"""
        if not FIREBASE_AVAILABLE:
            print("⚠️  Firebase Admin SDK not available")
            print("   Install: pip install firebase-admin")
            return
        
        try:
            # Load Firebase credentials from environment or file
            cred_path = os.getenv("FIREBASE_CREDENTIALS", "firebase_credentials.json")
            
            if not os.path.exists(cred_path):
                print(f"⚠️  Firebase credentials not found: {cred_path}")
                print("   Download from Firebase Console > Project Settings > Service Accounts")
                return
            
            # Initialize Firebase app
            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            
            # Load device tokens from config
            token_file = os.getenv("FCM_DEVICE_TOKENS", ".copilot/fcm_device_tokens.json")
            if os.path.exists(token_file):
                with open(token_file, 'r') as f:
                    self.device_tokens = json.load(f).get("tokens", [])
            
            self.firebase_initialized = True
            print(f"✅ Firebase initialized with {len(self.device_tokens)} device(s)")
            
        except Exception as e:
            print(f"⚠️  Firebase initialization failed: {e}")
    
    def add_device_token(self, token: str):
        """Add FCM device token for push notifications"""
        if token not in self.device_tokens:
            self.device_tokens.append(token)
            
            # Save to file
            token_file = os.getenv("FCM_DEVICE_TOKENS", ".copilot/fcm_device_tokens.json")
            os.makedirs(os.path.dirname(token_file) if os.path.dirname(token_file) else ".", exist_ok=True)
            with open(token_file, 'w') as f:
                json.dump({"tokens": self.device_tokens}, f, indent=2)
            
            print(f"✅ Device token added ({len(self.device_tokens)} total)")
    
    def _send_push_notification(self, reminder: Dict[str, Any]) -> bool:
        """
        Send push notification via Firebase Cloud Messaging
        
        Sends to all registered device tokens
        
        Args:
            reminder: Reminder data with task_title, due_date, etc.
            
        Returns:
            bool: True if sent successfully to at least one device
        """
        if not FIREBASE_AVAILABLE:
            print("⚠️  Firebase not available, skipping push notification")
            return False
        
        if not self.firebase_initialized:
            print("⚠️  Firebase not initialized, skipping push notification")
            return False
        
        if not self.device_tokens:
            print("⚠️  No device tokens registered, skipping push notification")
            return False
        
        try:
            # Prepare notification content
            title = "📚 Task Reminder"
            body = f"{reminder['task_title']}"
            
            if 'due_date' in reminder:
                body += f" - Due: {reminder['due_date']}"
            
            # Add escalation emoji
            escalation_emoji = {
                "gentle": "📌",
                "moderate": "⚠️",
                "urgent": "🔔",
                "critical": "🚨"
            }
            emoji = escalation_emoji.get(reminder.get("escalation_level", "moderate"), "📌")
            title = f"{emoji} Task Reminder"
            
            # Create FCM message
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data={
                    "task_id": str(reminder.get("id", "")),
                    "task_title": reminder["task_title"],
                    "escalation_level": reminder.get("escalation_level", "moderate"),
                    "click_action": "OPEN_TASK"
                },
                tokens=self.device_tokens,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        color='#FF6B35'
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1
                        )
                    )
                )
            )
            
            # Send to all devices
            response = messaging.send_multicast(message)
            
            success_count = response.success_count
            failure_count = response.failure_count
            
            # Remove invalid tokens
            if failure_count > 0:
                invalid_tokens = []
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        if resp.exception and 'registration-token-not-registered' in str(resp.exception):
                            invalid_tokens.append(self.device_tokens[idx])
                
                # Remove invalid tokens
                for token in invalid_tokens:
                    self.device_tokens.remove(token)
                    print(f"⚠️  Removed invalid device token")
            
            print(f"🔔 [Push] Sent to {success_count} device(s), {failure_count} failed")
            return success_count > 0
            
        except Exception as e:
            print(f"❌ Push notification failed: {e}")
            return False
    
    def get_dashboard_notifications(self) -> List[Dict[str, Any]]:
        """Get unread dashboard notifications"""
        return [n for n in self.dashboard_notifications if n["status"] == "unread"]


def main():
    print("Multi-Channel Notifier - Ready")


if __name__ == "__main__":
    main()
