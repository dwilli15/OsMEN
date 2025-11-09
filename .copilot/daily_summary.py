#!/usr/bin/env python3
"""
Daily Summary Generator
Creates and sends daily email summaries of system activity
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

from conversation_store import ConversationStore


class DailySummaryGenerator:
    """Generates daily summaries of system activity"""
    
    def __init__(self, config_path: str = ".copilot/memory.json"):
        self.config_path = Path(config_path)
        self.conversation_store = ConversationStore()
        self.load_config()
    
    def load_config(self):
        """Load configuration from memory.json"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {}
    
    def generate_daily_summary(self, date: datetime = None) -> Dict[str, Any]:
        """Generate summary for specified date (defaults to yesterday)"""
        if date is None:
            date = datetime.utcnow() - timedelta(days=1)
        
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Get conversations for the day
        conversations = self.conversation_store.get_conversations(
            start_date=start_of_day,
            end_date=end_of_day,
            limit=1000
        )
        
        # Analyze system state
        system_state = self._analyze_system_state()
        
        # Get pending tasks
        pending_tasks = self._get_pending_tasks()
        
        # Get autonomous actions
        autonomous_actions = self._get_autonomous_actions(start_of_day, end_of_day)
        
        summary = {
            "date": date.strftime("%Y-%m-%d"),
            "generated_at": datetime.utcnow().isoformat(),
            "conversations": {
                "count": len(conversations),
                "highlights": self._extract_highlights(conversations)
            },
            "system_state": system_state,
            "pending_tasks": pending_tasks,
            "autonomous_actions": autonomous_actions,
            "requires_review": self._identify_review_items(conversations, autonomous_actions)
        }
        
        return summary
    
    def _analyze_system_state(self) -> Dict[str, Any]:
        """Analyze current system state from memory.json"""
        state = {
            "current_phase": self.config.get("system_state", {}).get("current_phase", "Unknown"),
            "active_priorities": self.config.get("system_state", {}).get("active_priorities", []),
            "integrations_enabled": len(self.config.get("integrations", {}).get("enabled", [])),
            "health": "operational"
        }
        return state
    
    def _get_pending_tasks(self) -> List[Dict[str, str]]:
        """Extract pending tasks from progress tracking"""
        # Read from PROGRESS.md if it exists
        progress_file = Path("PROGRESS.md")
        pending = []
        
        if progress_file.exists():
            content = progress_file.read_text()
            lines = content.split('\n')
            
            for line in lines:
                if line.strip().startswith('- [ ]'):
                    task = line.strip()[6:].strip()
                    pending.append({
                        "task": task,
                        "status": "pending"
                    })
        
        return pending[:10]  # Top 10 pending tasks
    
    def _get_autonomous_actions(self, start: datetime, end: datetime) -> List[Dict]:
        """Get autonomous actions executed during the period"""
        # Read from pre_approved_tasks.json execution log
        tasks_file = Path(".copilot/pre_approved_tasks.json")
        actions = []
        
        if tasks_file.exists():
            with open(tasks_file, 'r') as f:
                tasks_data = json.load(f)
                execution_log = tasks_data.get("execution_log", [])
                
                for log_entry in execution_log:
                    exec_time = datetime.fromisoformat(log_entry.get("timestamp", ""))
                    if start <= exec_time <= end:
                        actions.append(log_entry)
        
        return actions
    
    def _extract_highlights(self, conversations: List[Dict]) -> List[str]:
        """Extract key highlights from conversations"""
        highlights = []
        
        # Group by topics
        topics = {}
        for conv in conversations:
            user_msg = conv.get("user_message", "").lower()
            
            # Simple topic detection
            if "implement" in user_msg or "create" in user_msg:
                topics.setdefault("implementations", []).append(conv)
            elif "plan" in user_msg or "roadmap" in user_msg:
                topics.setdefault("planning", []).append(conv)
            elif "error" in user_msg or "fix" in user_msg:
                topics.setdefault("issues", []).append(conv)
        
        # Create highlights
        for topic, convs in topics.items():
            highlights.append(f"{topic.title()}: {len(convs)} conversations")
        
        return highlights
    
    def _identify_review_items(self, conversations: List, actions: List) -> List[Dict]:
        """Identify items requiring user review"""
        review_items = []
        
        # Check for autonomous actions needing approval
        if actions:
            review_items.append({
                "type": "autonomous_actions",
                "count": len(actions),
                "description": f"{len(actions)} autonomous actions executed"
            })
        
        # Check for decisions made
        decision_keywords = ["implement", "create", "add", "remove", "change"]
        decision_convs = [
            c for c in conversations 
            if any(kw in c.get("agent_response", "").lower() for kw in decision_keywords)
        ]
        
        if decision_convs:
            review_items.append({
                "type": "decisions",
                "count": len(decision_convs),
                "description": f"{len(decision_convs)} decisions made"
            })
        
        return review_items
    
    def format_email_html(self, summary: Dict) -> str:
        """Format summary as HTML email"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; }}
                .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #4CAF50; }}
                .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
                .metric-label {{ font-size: 12px; color: #666; }}
                .action-item {{ background-color: #fff3cd; padding: 10px; margin: 5px 0; border-left: 4px solid #ffc107; }}
                .footer {{ margin-top: 30px; padding: 20px; background-color: #f5f5f5; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 OsMEN Daily Summary</h1>
                <p>Summary for {summary['date']}</p>
            </div>
            
            <div class="section">
                <h2>📊 Daily Metrics</h2>
                <div class="metric">
                    <div class="metric-value">{summary['conversations']['count']}</div>
                    <div class="metric-label">Conversations</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{summary['system_state']['integrations_enabled']}</div>
                    <div class="metric-label">Active Integrations</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{len(summary['autonomous_actions'])}</div>
                    <div class="metric-label">Autonomous Actions</div>
                </div>
            </div>
            
            <div class="section">
                <h2>🎯 System Status</h2>
                <p><strong>Phase:</strong> {summary['system_state']['current_phase']}</p>
                <p><strong>Health:</strong> ✅ {summary['system_state']['health'].title()}</p>
                <p><strong>Priorities:</strong> {', '.join(summary['system_state']['active_priorities'])}</p>
            </div>
        """
        
        # Add highlights
        if summary['conversations']['highlights']:
            html += """
            <div class="section">
                <h2>💡 Highlights</h2>
                <ul>
            """
            for highlight in summary['conversations']['highlights']:
                html += f"<li>{highlight}</li>"
            html += "</ul></div>"
        
        # Add review items
        if summary['requires_review']:
            html += """
            <div class="section">
                <h2>⚠️ Requires Your Review</h2>
            """
            for item in summary['requires_review']:
                html += f"""
                <div class="action-item">
                    <strong>{item['type'].replace('_', ' ').title()}</strong>: {item['description']}
                </div>
                """
            html += "</div>"
        
        # Add pending tasks
        if summary['pending_tasks']:
            html += """
            <div class="section">
                <h2>📋 Top Pending Tasks</h2>
                <ul>
            """
            for task in summary['pending_tasks'][:5]:
                html += f"<li>{task['task']}</li>"
            html += "</ul></div>"
        
        # Footer
        html += f"""
            <div class="footer">
                <p>Generated at {summary['generated_at']}</p>
                <p>View live dashboard: <a href="http://localhost:8080/dashboard">http://localhost:8080/dashboard</a></p>
                <p>This is an automated summary from your OsMEN AI assistant.</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_email_summary(self, summary: Dict, recipient: str, smtp_config: Dict = None):
        """Send summary via email"""
        if smtp_config is None:
            smtp_config = {
                "server": os.getenv("SMTP_SERVER", "localhost"),
                "port": int(os.getenv("SMTP_PORT", "587")),
                "username": os.getenv("SMTP_USERNAME", ""),
                "password": os.getenv("SMTP_PASSWORD", ""),
                "from_addr": os.getenv("SMTP_FROM", "osmen@localhost")
            }
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"OsMEN Daily Summary - {summary['date']}"
        msg["From"] = smtp_config["from_addr"]
        msg["To"] = recipient
        
        # Plain text version
        text_content = self.format_email_text(summary)
        html_content = self.format_email_html(summary)
        
        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))
        
        # Send email
        try:
            with smtplib.SMTP(smtp_config["server"], smtp_config["port"]) as server:
                if smtp_config.get("username"):
                    server.starttls()
                    server.login(smtp_config["username"], smtp_config["password"])
                
                server.send_message(msg)
                print(f"Email sent successfully to {recipient}")
        except Exception as e:
            print(f"Failed to send email: {e}")
            # Save to file as backup
            self.save_summary_to_file(summary)
    
    def format_email_text(self, summary: Dict) -> str:
        """Format summary as plain text email"""
        text = f"""
OsMEN Daily Summary - {summary['date']}
{'=' * 50}

Daily Metrics:
- Conversations: {summary['conversations']['count']}
- Active Integrations: {summary['system_state']['integrations_enabled']}
- Autonomous Actions: {len(summary['autonomous_actions'])}

System Status:
- Phase: {summary['system_state']['current_phase']}
- Health: {summary['system_state']['health'].title()}
- Priorities: {', '.join(summary['system_state']['active_priorities'])}
"""
        
        if summary['conversations']['highlights']:
            text += "\nHighlights:\n"
            for highlight in summary['conversations']['highlights']:
                text += f"- {highlight}\n"
        
        if summary['requires_review']:
            text += "\n⚠️ Requires Your Review:\n"
            for item in summary['requires_review']:
                text += f"- {item['type'].replace('_', ' ').title()}: {item['description']}\n"
        
        if summary['pending_tasks']:
            text += "\nTop Pending Tasks:\n"
            for task in summary['pending_tasks'][:5]:
                text += f"- {task['task']}\n"
        
        text += f"\n---\nGenerated at {summary['generated_at']}\n"
        text += "View live dashboard: http://localhost:8080/dashboard\n"
        
        return text
    
    def save_summary_to_file(self, summary: Dict):
        """Save summary to file for archival"""
        summaries_dir = Path(".copilot/daily_summaries")
        summaries_dir.mkdir(exist_ok=True)
        
        filename = summaries_dir / f"summary_{summary['date']}.json"
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"Summary saved to {filename}")


if __name__ == "__main__":
    # Generate and display today's summary
    generator = DailySummaryGenerator()
    summary = generator.generate_daily_summary()
    
    print(json.dumps(summary, indent=2))
    
    # Save to file
    generator.save_summary_to_file(summary)
    
    # Optionally send email (requires SMTP configuration)
    # recipient_email = "user@example.com"
    # generator.send_email_summary(summary, recipient_email)
