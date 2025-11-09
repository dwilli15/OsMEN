#!/usr/bin/env python3
"""
Conversation History Storage System
Stores AI agent conversations with 45-day retention and permanent summaries
"""

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Optional, Any
import hashlib


class ConversationStore:
    """Manages conversation history with retention policies"""
    
    def __init__(self, db_path: str = ".copilot/conversations.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    timestamp DATETIME NOT NULL,
                    user_message TEXT NOT NULL,
                    agent_response TEXT NOT NULL,
                    agent_name TEXT DEFAULT 'copilot',
                    context TEXT,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Summaries table (permanent storage)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS summaries (
                    id TEXT PRIMARY KEY,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    summary TEXT NOT NULL,
                    conversation_count INTEGER,
                    key_topics TEXT,
                    decisions_made TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conv_timestamp 
                ON conversations(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_summary_dates 
                ON summaries(start_date, end_date)
            """)
            
            conn.commit()
    
    def add_conversation(
        self,
        user_message: str,
        agent_response: str,
        agent_name: str = "copilot",
        context: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """Add a conversation to storage"""
        timestamp = datetime.now(timezone.utc)
        conv_id = self._generate_id(user_message, timestamp)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversations 
                (id, timestamp, user_message, agent_response, agent_name, context, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                conv_id,
                timestamp,
                user_message,
                agent_response,
                agent_name,
                json.dumps(context) if context else None,
                json.dumps(metadata) if metadata else None
            ))
            conn.commit()
        
        return conv_id
    
    def get_conversations(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Retrieve conversations within date range"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM conversations WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def cleanup_old_conversations(self, days: int = 45) -> int:
        """Archive conversations older than specified days and create summaries"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get conversations to archive
            cursor.execute("""
                SELECT * FROM conversations 
                WHERE timestamp < ? 
                ORDER BY timestamp
            """, (cutoff_date,))
            
            old_conversations = cursor.fetchall()
            
            if old_conversations:
                # Create summary before deleting
                self._create_summary_from_conversations(old_conversations, conn)
                
                # Delete old conversations
                cursor.execute("""
                    DELETE FROM conversations WHERE timestamp < ?
                """, (cutoff_date,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                return deleted_count
            
            return 0
    
    def _create_summary_from_conversations(
        self, 
        conversations: List[Any],
        conn: sqlite3.Connection
    ):
        """Create a summary from a batch of conversations"""
        if not conversations:
            return
        
        # Extract key information
        start_date = min(conv[1] for conv in conversations)  # timestamp
        end_date = max(conv[1] for conv in conversations)
        
        # Collect topics and decisions
        topics = set()
        decisions = []
        
        for conv in conversations:
            user_msg = conv[2]
            agent_resp = conv[3]
            
            # Simple topic extraction (could be enhanced with NLP)
            if "calendar" in user_msg.lower() or "calendar" in agent_resp.lower():
                topics.add("calendar_management")
            if "syllabus" in user_msg.lower() or "syllabus" in agent_resp.lower():
                topics.add("syllabus_parsing")
            if "task" in user_msg.lower() or "todo" in user_msg.lower():
                topics.add("task_management")
            if "implement" in agent_resp.lower() or "created" in agent_resp.lower():
                decisions.append(f"Action taken on {conv[1]}")
        
        # Create summary text
        summary_text = self._generate_summary_text(conversations, topics)
        
        summary_id = self._generate_id(summary_text, datetime.now(timezone.utc))
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO summaries 
            (id, start_date, end_date, summary, conversation_count, key_topics, decisions_made)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            summary_id,
            start_date,
            end_date,
            summary_text,
            len(conversations),
            json.dumps(list(topics)),
            json.dumps(decisions)
        ))
    
    def _generate_summary_text(self, conversations: List[Any], topics: set) -> str:
        """Generate human-readable summary text"""
        summary = f"Period: {conversations[0][1]} to {conversations[-1][1]}\n"
        summary += f"Total conversations: {len(conversations)}\n"
        summary += f"Key topics: {', '.join(topics)}\n\n"
        
        # Add highlights (first and last few conversations)
        summary += "Highlights:\n"
        for conv in conversations[:3]:  # First 3
            summary += f"- User: {conv[2][:100]}...\n"
        
        if len(conversations) > 6:
            summary += "...\n"
        
        for conv in conversations[-3:]:  # Last 3
            summary += f"- User: {conv[2][:100]}...\n"
        
        return summary
    
    def get_summaries(self, start_date: Optional[datetime] = None) -> List[Dict]:
        """Retrieve conversation summaries"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM summaries WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND start_date >= ?"
                params.append(start_date)
            
            query += " ORDER BY start_date DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def search_conversations(self, query: str, limit: int = 50) -> List[Dict]:
        """Search conversations by keyword"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM conversations 
                WHERE user_message LIKE ? OR agent_response LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def _generate_id(self, text: str, timestamp: datetime) -> str:
        """Generate unique ID for conversation or summary"""
        content = f"{text}{timestamp.isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


if __name__ == "__main__":
    # Example usage
    store = ConversationStore()
    
    # Add a test conversation
    conv_id = store.add_conversation(
        user_message="How do I set up the calendar integration?",
        agent_response="To set up calendar integration, you need to...",
        context={"session": "planning", "phase": "v1.4.0"}
    )
    
    print(f"Added conversation: {conv_id}")
    
    # Retrieve recent conversations
    recent = store.get_conversations(limit=10)
    print(f"\nRecent conversations: {len(recent)}")
    
    # Cleanup old conversations (would normally run daily)
    deleted = store.cleanup_old_conversations(days=45)
    print(f"\nCleaned up {deleted} old conversations")
    
    # Get summaries
    summaries = store.get_summaries()
    print(f"\nPermanent summaries: {len(summaries)}")
