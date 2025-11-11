#!/usr/bin/env python3
"""
Productivity Monitor Integration
Tracks time, focus, and productivity metrics
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import sqlite3

logger = logging.getLogger(__name__)


class ProductivityMonitor:
    """Monitor and track productivity metrics"""
    
    def __init__(self):
        self.db_path = Path(__file__).parent / "productivity.db"
        self._init_database()
    
    def _init_database(self):
        """Initialize productivity tracking database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Focus sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS focus_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_minutes INTEGER,
                session_type TEXT,
                productivity_score INTEGER,
                distractions_count INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT FALSE,
                notes TEXT
            )
        """)
        
        # Application usage table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                application TEXT NOT NULL,
                category TEXT,
                duration_seconds INTEGER,
                is_productive BOOLEAN
            )
        """)
        
        # Daily metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                focus_time_minutes INTEGER DEFAULT 0,
                productive_time_minutes INTEGER DEFAULT 0,
                distraction_time_minutes INTEGER DEFAULT 0,
                sessions_completed INTEGER DEFAULT 0,
                average_productivity_score REAL,
                energy_level INTEGER,
                notes TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def start_focus_session(self, session_type: str = "pomodoro", duration: int = 25) -> Dict[str, Any]:
        """Start a new focus session"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        start_time = datetime.now(timezone.utc).isoformat()
        
        cursor.execute("""
            INSERT INTO focus_sessions (start_time, session_type, duration_minutes)
            VALUES (?, ?, ?)
        """, (start_time, session_type, duration))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Started focus session {session_id} ({session_type}, {duration}min)")
        
        return {
            "status": "started",
            "session_id": session_id,
            "start_time": start_time,
            "duration_minutes": duration,
            "session_type": session_type
        }
    
    def end_focus_session(self, session_id: int, productivity_score: int = 7, 
                         distractions: int = 0, notes: str = "") -> Dict[str, Any]:
        """End a focus session"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        end_time = datetime.now(timezone.utc).isoformat()
        
        # Get session start time
        cursor.execute("SELECT start_time FROM focus_sessions WHERE id = ?", (session_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return {"status": "error", "message": "Session not found"}
        
        start_time = datetime.fromisoformat(result[0])
        duration = int((datetime.now(timezone.utc) - start_time).total_seconds() / 60)
        
        cursor.execute("""
            UPDATE focus_sessions
            SET end_time = ?, duration_minutes = ?, productivity_score = ?,
                distractions_count = ?, completed = TRUE, notes = ?
            WHERE id = ?
        """, (end_time, duration, productivity_score, distractions, notes, session_id))
        
        conn.commit()
        conn.close()
        
        # Update daily metrics
        self._update_daily_metrics(datetime.now(timezone.utc).date(), duration, productivity_score)
        
        logger.info(f"Ended focus session {session_id} ({duration}min, score: {productivity_score}/10)")
        
        return {
            "status": "completed",
            "session_id": session_id,
            "duration_minutes": duration,
            "productivity_score": productivity_score,
            "distractions": distractions
        }
    
    def log_app_usage(self, application: str, duration_seconds: int, 
                      category: str = "unknown", is_productive: bool = True) -> Dict[str, Any]:
        """Log application usage"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        timestamp = datetime.now(timezone.utc).isoformat()
        
        cursor.execute("""
            INSERT INTO app_usage (timestamp, application, category, duration_seconds, is_productive)
            VALUES (?, ?, ?, ?, ?)
        """, (timestamp, application, category, duration_seconds, is_productive))
        
        conn.commit()
        conn.close()
        
        return {
            "status": "logged",
            "application": application,
            "duration_seconds": duration_seconds,
            "is_productive": is_productive
        }
    
    def get_daily_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get daily productivity summary"""
        if not date:
            date = datetime.now(timezone.utc).date().isoformat()
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Get sessions for the day
        cursor.execute("""
            SELECT COUNT(*), SUM(duration_minutes), AVG(productivity_score)
            FROM focus_sessions
            WHERE DATE(start_time) = ? AND completed = TRUE
        """, (date,))
        
        session_data = cursor.fetchone()
        sessions_count = session_data[0] or 0
        focus_time = session_data[1] or 0
        avg_score = session_data[2] or 0
        
        # Get app usage
        cursor.execute("""
            SELECT SUM(duration_seconds) / 60, category
            FROM app_usage
            WHERE DATE(timestamp) = ?
            GROUP BY category
        """, (date,))
        
        app_usage = {}
        for row in cursor.fetchall():
            app_usage[row[1]] = int(row[0])
        
        conn.close()
        
        return {
            "date": date,
            "sessions_completed": sessions_count,
            "focus_time_minutes": int(focus_time),
            "average_productivity_score": round(avg_score, 1),
            "app_usage_by_category": app_usage
        }
    
    def get_weekly_trends(self) -> Dict[str, Any]:
        """Get weekly productivity trends"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Last 7 days
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=7)
        
        cursor.execute("""
            SELECT DATE(start_time), COUNT(*), SUM(duration_minutes), AVG(productivity_score)
            FROM focus_sessions
            WHERE DATE(start_time) >= ? AND completed = TRUE
            GROUP BY DATE(start_time)
            ORDER BY DATE(start_time)
        """, (start_date.isoformat(),))
        
        daily_data = []
        for row in cursor.fetchall():
            daily_data.append({
                "date": row[0],
                "sessions": row[1],
                "focus_time": row[2],
                "avg_score": round(row[3], 1)
            })
        
        conn.close()
        
        # Calculate totals
        total_sessions = sum(d["sessions"] for d in daily_data)
        total_focus = sum(d["focus_time"] for d in daily_data)
        avg_score = sum(d["avg_score"] for d in daily_data) / len(daily_data) if daily_data else 0
        
        return {
            "period": "last_7_days",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_sessions": total_sessions,
            "total_focus_time_minutes": total_focus,
            "average_productivity_score": round(avg_score, 1),
            "daily_breakdown": daily_data
        }
    
    def _update_daily_metrics(self, date, focus_time: int, productivity_score: int):
        """Update daily metrics"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        date_str = date.isoformat()
        
        # Check if entry exists
        cursor.execute("SELECT id FROM daily_metrics WHERE date = ?", (date_str,))
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute("""
                UPDATE daily_metrics
                SET focus_time_minutes = focus_time_minutes + ?,
                    sessions_completed = sessions_completed + 1,
                    average_productivity_score = 
                        (average_productivity_score * sessions_completed + ?) / (sessions_completed + 1)
                WHERE date = ?
            """, (focus_time, productivity_score, date_str))
        else:
            cursor.execute("""
                INSERT INTO daily_metrics (date, focus_time_minutes, sessions_completed, average_productivity_score)
                VALUES (?, ?, 1, ?)
            """, (date_str, focus_time, productivity_score))
        
        conn.commit()
        conn.close()


def test_productivity_monitor():
    """Test productivity monitor"""
    monitor = ProductivityMonitor()
    
    # Start session
    result = monitor.start_focus_session("pomodoro", 25)
    session_id = result["session_id"]
    print(f"Started session: {result}")
    
    # End session
    import time
    time.sleep(1)
    result = monitor.end_focus_session(session_id, productivity_score=8, distractions=2)
    print(f"Ended session: {result}")
    
    # Get daily summary
    summary = monitor.get_daily_summary()
    print(f"Daily summary: {summary}")
    
    # Get weekly trends
    trends = monitor.get_weekly_trends()
    print(f"Weekly trends: {trends}")
    
    print("\n✅ Productivity Monitor Test Passed")


if __name__ == "__main__":
    test_productivity_monitor()
