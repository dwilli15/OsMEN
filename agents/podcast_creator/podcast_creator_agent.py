#!/usr/bin/env python3
"""
Podcast Creator Agent
Creates podcasts from personal knowledge database and content
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)


class PodcastCreatorAgent:
    """Podcast Creator Agent for generating podcasts from knowledge base."""
    
    def __init__(self):
        """Initialize the Podcast Creator Agent."""
        logger.info("PodcastCreatorAgent initialized successfully")
        self.episodes = []
        self.series = []
    
    def create_podcast_series(self, title: str, description: str, 
                            category: str = "Education") -> Dict:
        """Create a podcast series.
        
        Args:
            title: Series title
            description: Series description
            category: Podcast category
            
        Returns:
            Dictionary with series details
        """
        series = {
            "id": len(self.series) + 1,
            "title": title,
            "description": description,
            "category": category,
            "episodes": [],
            "created_at": datetime.now().isoformat()
        }
        self.series.append(series)
        logger.info(f"Created podcast series: {title}")
        return series
    
    def generate_episode_from_notes(self, series_id: int, note_paths: List[str], 
                                   episode_title: str, voice_profile_id: int = 1) -> Dict:
        """Generate podcast episode from knowledge base notes.
        
        Args:
            series_id: Series ID
            note_paths: List of note file paths to use as source
            episode_title: Episode title
            voice_profile_id: Voice profile for narration
            
        Returns:
            Dictionary with episode details
        """
        episode = {
            "id": len(self.episodes) + 1,
            "series_id": series_id,
            "title": episode_title,
            "source_notes": note_paths,
            "voice_profile_id": voice_profile_id,
            "status": "generating",
            "created_at": datetime.now().isoformat()
        }
        self.episodes.append(episode)
        
        # Add to series
        for series in self.series:
            if series["id"] == series_id:
                series["episodes"].append(episode["id"])
                break
        
        logger.info(f"Generating episode '{episode_title}' from {len(note_paths)} notes")
        return episode
    
    def add_intro_outro(self, episode_id: int, intro_audio: str, 
                       outro_audio: str) -> Dict:
        """Add intro and outro music to episode.
        
        Args:
            episode_id: Episode ID
            intro_audio: Path to intro audio file
            outro_audio: Path to outro audio file
            
        Returns:
            Updated episode details
        """
        for episode in self.episodes:
            if episode["id"] == episode_id:
                episode["intro_audio"] = intro_audio
                episode["outro_audio"] = outro_audio
                logger.info(f"Added intro/outro to episode {episode_id}")
                return episode
        return {"error": "Episode not found"}
    
    def finalize_episode(self, episode_id: int, output_path: str) -> Dict:
        """Finalize and export podcast episode.
        
        Args:
            episode_id: Episode ID
            output_path: Path for output audio file
            
        Returns:
            Finalized episode details
        """
        for episode in self.episodes:
            if episode["id"] == episode_id:
                episode["status"] = "published"
                episode["output_path"] = output_path
                episode["published_at"] = datetime.now().isoformat()
                logger.info(f"Finalized episode: {episode['title']}")
                return episode
        return {"error": "Episode not found"}
    
    def generate_podcast_report(self) -> Dict:
        """Generate comprehensive podcast creator report.
        
        Returns:
            Dictionary with creator status and statistics
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "operational",
            "statistics": {
                "total_series": len(self.series),
                "total_episodes": len(self.episodes),
                "published_episodes": len([e for e in self.episodes if e["status"] == "published"]),
                "generating_episodes": len([e for e in self.episodes if e["status"] == "generating"])
            }
        }


if __name__ == "__main__":
    # Test the agent
    logging.basicConfig(level=logging.INFO)
    
    agent = PodcastCreatorAgent()
    
    # Create a series
    series = agent.create_podcast_series(
        "Tech Insights",
        "Weekly tech insights from my knowledge base",
        "Technology"
    )
    
    # Generate episode
    episode = agent.generate_episode_from_notes(
        series["id"],
        ["/notes/ai_trends.md", "/notes/machine_learning.md"],
        "Episode 1: AI and ML Trends",
        voice_profile_id=1
    )
    
    # Add intro/outro
    agent.add_intro_outro(episode["id"], "/audio/intro.mp3", "/audio/outro.mp3")
    
    # Finalize
    agent.finalize_episode(episode["id"], "/podcasts/tech_insights_ep1.mp3")
    
    # Generate report
    report = agent.generate_podcast_report()
    print(json.dumps(report, indent=2))
