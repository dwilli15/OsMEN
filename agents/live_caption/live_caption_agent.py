#!/usr/bin/env python3
"""
Live Caption Agent
Provides real-time transcription and captioning for Zoom and other meetings
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)


class LiveCaptionAgent:
    """Live Caption Agent for real-time meeting transcription."""
    
    def __init__(self):
        """Initialize the Live Caption Agent."""
        logger.info("LiveCaptionAgent initialized successfully")
        self.sessions = []
        self.transcripts = []
    
    def start_caption_session(self, meeting_id: str, meeting_title: str = "", 
                             language: str = "en") -> Dict:
        """Start a live captioning session.
        
        Args:
            meeting_id: Unique meeting identifier
            meeting_title: Meeting title/description
            language: Language code for transcription
            
        Returns:
            Dictionary with session details
        """
        session = {
            "id": len(self.sessions) + 1,
            "meeting_id": meeting_id,
            "meeting_title": meeting_title,
            "language": language,
            "status": "active",
            "started_at": datetime.now().isoformat(),
            "captions": []
        }
        self.sessions.append(session)
        logger.info(f"Started caption session for meeting: {meeting_title or meeting_id}")
        return session
    
    def add_caption(self, session_id: int, speaker: str, text: str, 
                   timestamp: Optional[str] = None) -> Dict:
        """Add a caption to an active session.
        
        Args:
            session_id: Session ID
            speaker: Speaker name/identifier
            text: Transcribed text
            timestamp: Optional timestamp
            
        Returns:
            Dictionary with caption details
        """
        caption = {
            "speaker": speaker,
            "text": text,
            "timestamp": timestamp or datetime.now().isoformat()
        }
        
        # Find session and add caption
        for session in self.sessions:
            if session["id"] == session_id:
                session["captions"].append(caption)
                logger.info(f"Added caption from {speaker}")
                break
        
        return caption
    
    def end_caption_session(self, session_id: int) -> Dict:
        """End a captioning session and save transcript.
        
        Args:
            session_id: Session ID to end
            
        Returns:
            Dictionary with session summary
        """
        for session in self.sessions:
            if session["id"] == session_id and session["status"] == "active":
                session["status"] = "completed"
                session["ended_at"] = datetime.now().isoformat()
                
                # Create transcript
                transcript = {
                    "session_id": session_id,
                    "meeting_id": session["meeting_id"],
                    "meeting_title": session["meeting_title"],
                    "started_at": session["started_at"],
                    "ended_at": session["ended_at"],
                    "total_captions": len(session["captions"]),
                    "transcript_text": "\n\n".join([
                        f"[{c['timestamp']}] {c['speaker']}: {c['text']}"
                        for c in session["captions"]
                    ])
                }
                self.transcripts.append(transcript)
                
                logger.info(f"Ended caption session {session_id}")
                return transcript
        
        return {"error": "Session not found or already ended"}
    
    def get_transcript(self, session_id: int) -> Optional[Dict]:
        """Get saved transcript for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Transcript dictionary or None
        """
        for transcript in self.transcripts:
            if transcript["session_id"] == session_id:
                return transcript
        return None
    
    def generate_caption_report(self) -> Dict:
        """Generate comprehensive live caption report.
        
        Returns:
            Dictionary with caption agent status and statistics
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "operational",
            "statistics": {
                "total_sessions": len(self.sessions),
                "active_sessions": len([s for s in self.sessions if s["status"] == "active"]),
                "completed_sessions": len([s for s in self.sessions if s["status"] == "completed"]),
                "total_transcripts": len(self.transcripts),
                "total_captions": sum(len(s.get("captions", [])) for s in self.sessions)
            }
        }


if __name__ == "__main__":
    # Test the agent
    logging.basicConfig(level=logging.INFO)
    
    agent = LiveCaptionAgent()
    
    # Start a session
    session = agent.start_caption_session("zoom-123456", "Team Standup", "en")
    session_id = session["id"]
    
    # Add captions
    agent.add_caption(session_id, "Alice", "Good morning everyone!")
    agent.add_caption(session_id, "Bob", "Hi team, let me share my updates.")
    agent.add_caption(session_id, "Alice", "Thanks Bob. Anyone have blockers?")
    agent.add_caption(session_id, "Charlie", "No blockers on my end.")
    
    # End session
    transcript = agent.end_caption_session(session_id)
    
    # Generate report
    report = agent.generate_caption_report()
    print(json.dumps(report, indent=2))
    print("\nTranscript:")
    print(transcript.get("transcript_text", ""))
