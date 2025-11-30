#!/usr/bin/env python3
"""
Content Creator Agent - Real Implementation
Handles image generation, video processing, and multimedia content creation.

This agent integrates with:
- FFmpeg for video processing (real command execution)
- LLM providers for content prompts and descriptions
- Optional: DALL-E/Stable Diffusion for image generation (when configured)

Usage:
    from agents.content_creator.content_creator_agent import ContentCreatorAgent
    
    agent = ContentCreatorAgent()
    
    # Video processing (requires FFmpeg)
    result = agent.process_video("/path/to/video.mp4", ["trim:0:30", "resize:1280x720"])
    
    # Thumbnail extraction (requires FFmpeg)
    result = agent.create_thumbnail("/path/to/video.mp4", "00:01:30")
    
    # Image generation (requires LLM with image capability)
    result = await agent.generate_image_async("sunset over mountains", style="artistic")
"""

import os
import sys
import json
import asyncio
import logging
import subprocess
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for FFmpeg
FFMPEG_AVAILABLE = shutil.which('ffmpeg') is not None
FFPROBE_AVAILABLE = shutil.which('ffprobe') is not None

if FFMPEG_AVAILABLE:
    logger.info("FFmpeg available for video processing")
else:
    logger.warning("FFmpeg not found - video processing will be simulated")

# Try to import LLM providers
LLM_AVAILABLE = False
try:
    from integrations.llm_providers import get_llm_provider, LLMConfig
    LLM_AVAILABLE = True
    logger.info("LLM providers available for content generation")
except ImportError as e:
    logger.warning(f"LLM providers not available: {e}")


class ContentCreatorAgent:
    """
    Content Creator Agent for image and video generation/processing.
    
    Real implementation that:
    - Uses FFmpeg for actual video processing
    - Integrates with LLM for content generation
    - Manages output directories
    - Tracks job history
    
    Attributes:
        ffmpeg_available: Whether FFmpeg is available
        llm_available: Whether LLM is available
        output_dir: Directory for output files
    """
    
    def __init__(self, output_dir: str = "data/content_creator"):
        """
        Initialize the Content Creator Agent.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.created_content = []
        self.processing_queue = []
        
        self.ffmpeg_available = FFMPEG_AVAILABLE
        self.ffprobe_available = FFPROBE_AVAILABLE
        self.llm_available = LLM_AVAILABLE
        self.llm = None
        
        logger.info(f"ContentCreatorAgent initialized (FFmpeg={self.ffmpeg_available}, LLM={self.llm_available})")
    
    async def _get_llm(self):
        """Get LLM provider (lazy initialization)."""
        if self.llm is None and LLM_AVAILABLE:
            try:
                self.llm = await get_llm_provider("ollama")
            except Exception as e:
                logger.warning(f"Failed to get LLM: {e}")
        return self.llm
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get video file information using FFprobe.
        
        Args:
            video_path: Path to video file
        
        Returns:
            Dictionary with video metadata
        """
        info = {
            'path': video_path,
            'exists': False,
            'real_info': False
        }
        
        path = Path(video_path)
        if not path.exists():
            info['error'] = 'File not found'
            return info
        
        info['exists'] = True
        info['size_bytes'] = path.stat().st_size
        info['size_mb'] = round(path.stat().st_size / (1024 * 1024), 2)
        
        if self.ffprobe_available:
            try:
                cmd = [
                    'ffprobe', '-v', 'quiet', '-print_format', 'json',
                    '-show_format', '-show_streams', str(path)
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    probe_data = json.loads(result.stdout)
                    info['real_info'] = True
                    
                    # Extract format info
                    if 'format' in probe_data:
                        fmt = probe_data['format']
                        info['duration'] = float(fmt.get('duration', 0))
                        info['bitrate'] = int(fmt.get('bit_rate', 0))
                        info['format_name'] = fmt.get('format_name', '')
                    
                    # Extract stream info
                    for stream in probe_data.get('streams', []):
                        if stream['codec_type'] == 'video':
                            info['width'] = stream.get('width')
                            info['height'] = stream.get('height')
                            info['codec'] = stream.get('codec_name')
                            info['fps'] = eval(stream.get('r_frame_rate', '0/1'))
                        elif stream['codec_type'] == 'audio':
                            info['audio_codec'] = stream.get('codec_name')
                            info['audio_channels'] = stream.get('channels')
                            
            except Exception as e:
                info['probe_error'] = str(e)
        
        return info
    
    def process_video(
        self,
        input_file: str,
        operations: List[str],
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a video file with specified operations using FFmpeg.
        
        Args:
            input_file: Path to input video
            operations: List of operations:
                - "trim:START:END" - Trim video (e.g., "trim:0:30" for first 30 seconds)
                - "resize:WIDTHxHEIGHT" - Resize video (e.g., "resize:1280x720")
                - "audio_extract" - Extract audio track
                - "mute" - Remove audio
                - "fps:VALUE" - Change frame rate
            output_file: Optional output path (auto-generated if not provided)
        
        Returns:
            Dictionary with processing details and result
        """
        job = {
            "id": len(self.processing_queue) + 1,
            "type": "video_processing",
            "input_file": input_file,
            "operations": operations,
            "status": "pending",
            "started_at": datetime.now().isoformat(),
            "ffmpeg_used": False
        }
        
        # Check input file
        input_path = Path(input_file)
        if not input_path.exists():
            job['status'] = 'error'
            job['error'] = f'Input file not found: {input_file}'
            self.processing_queue.append(job)
            return job
        
        # Generate output filename
        if output_file:
            output_path = Path(output_file)
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.output_dir / f"processed_{timestamp}{input_path.suffix}"
        
        job['output_file'] = str(output_path)
        
        if not self.ffmpeg_available:
            job['status'] = 'simulated'
            job['note'] = 'FFmpeg not available - operation simulated'
            self.processing_queue.append(job)
            return job
        
        # Build FFmpeg command
        try:
            cmd = ['ffmpeg', '-y', '-i', str(input_path)]
            
            for op in operations:
                if op.startswith('trim:'):
                    parts = op.split(':')
                    if len(parts) >= 2:
                        cmd.extend(['-ss', parts[1]])
                    if len(parts) >= 3:
                        cmd.extend(['-t', str(float(parts[2]) - float(parts[1]))])
                
                elif op.startswith('resize:'):
                    size = op.split(':')[1]
                    cmd.extend(['-vf', f'scale={size.replace("x", ":")}'])
                
                elif op == 'audio_extract':
                    output_path = output_path.with_suffix('.mp3')
                    job['output_file'] = str(output_path)
                    cmd.extend(['-vn', '-acodec', 'libmp3lame'])
                
                elif op == 'mute':
                    cmd.extend(['-an'])
                
                elif op.startswith('fps:'):
                    fps = op.split(':')[1]
                    cmd.extend(['-r', fps])
            
            cmd.append(str(output_path))
            
            job['ffmpeg_command'] = ' '.join(cmd)
            job['status'] = 'processing'
            
            # Execute FFmpeg
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                job['status'] = 'completed'
                job['ffmpeg_used'] = True
                
                # Get output file info
                if output_path.exists():
                    job['output_size_mb'] = round(output_path.stat().st_size / (1024 * 1024), 2)
            else:
                job['status'] = 'error'
                job['error'] = result.stderr[:500]
            
        except subprocess.TimeoutExpired:
            job['status'] = 'error'
            job['error'] = 'FFmpeg timeout (>300s)'
        except Exception as e:
            job['status'] = 'error'
            job['error'] = str(e)
        
        job['completed_at'] = datetime.now().isoformat()
        self.processing_queue.append(job)
        logger.info(f"Video processing {job['status']}: {input_file}")
        
        return job
    
    def create_thumbnail(
        self,
        video_path: str,
        timestamp: str = "00:00:05",
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create thumbnail from video at specified timestamp using FFmpeg.
        
        Args:
            video_path: Path to video file
            timestamp: Timestamp for thumbnail (HH:MM:SS)
            output_file: Optional output path
        
        Returns:
            Dictionary with thumbnail details
        """
        content = {
            "id": len(self.created_content) + 1,
            "type": "thumbnail",
            "source_video": video_path,
            "timestamp": timestamp,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "ffmpeg_used": False
        }
        
        video_path = Path(video_path)
        if not video_path.exists():
            content['status'] = 'error'
            content['error'] = f'Video not found: {video_path}'
            self.created_content.append(content)
            return content
        
        # Generate output path
        if output_file:
            output_path = Path(output_file)
        else:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.output_dir / f"thumb_{video_path.stem}_{ts}.jpg"
        
        content['output_file'] = str(output_path)
        
        if not self.ffmpeg_available:
            content['status'] = 'simulated'
            content['note'] = 'FFmpeg not available - thumbnail extraction simulated'
            self.created_content.append(content)
            return content
        
        try:
            cmd = [
                'ffmpeg', '-y', '-ss', timestamp, '-i', str(video_path),
                '-vframes', '1', '-q:v', '2', str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and output_path.exists():
                content['status'] = 'created'
                content['ffmpeg_used'] = True
                content['size_bytes'] = output_path.stat().st_size
            else:
                content['status'] = 'error'
                content['error'] = result.stderr[:200]
                
        except Exception as e:
            content['status'] = 'error'
            content['error'] = str(e)
        
        self.created_content.append(content)
        logger.info(f"Thumbnail {content['status']}: {video_path}")
        
        return content
    
    def convert_format(
        self,
        input_file: str,
        output_format: str,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convert media file to different format using FFmpeg.
        
        Args:
            input_file: Path to input file
            output_format: Desired output format (mp4, webm, gif, mp3, etc.)
            output_file: Optional output path
        
        Returns:
            Dictionary with conversion details
        """
        job = {
            "id": len(self.processing_queue) + 1,
            "type": "format_conversion",
            "input_file": input_file,
            "output_format": output_format,
            "status": "pending",
            "started_at": datetime.now().isoformat(),
            "ffmpeg_used": False
        }
        
        input_path = Path(input_file)
        if not input_path.exists():
            job['status'] = 'error'
            job['error'] = f'Input file not found: {input_file}'
            self.processing_queue.append(job)
            return job
        
        # Generate output path
        if output_file:
            output_path = Path(output_file)
        else:
            output_path = self.output_dir / f"{input_path.stem}_converted.{output_format}"
        
        job['output_file'] = str(output_path)
        
        if not self.ffmpeg_available:
            job['status'] = 'simulated'
            job['note'] = 'FFmpeg not available - conversion simulated'
            self.processing_queue.append(job)
            return job
        
        try:
            cmd = ['ffmpeg', '-y', '-i', str(input_path)]
            
            # Format-specific options
            if output_format == 'gif':
                cmd.extend(['-vf', 'fps=10,scale=320:-1:flags=lanczos'])
            elif output_format == 'mp3':
                cmd.extend(['-vn', '-acodec', 'libmp3lame', '-q:a', '2'])
            elif output_format == 'webm':
                cmd.extend(['-c:v', 'libvpx-vp9', '-crf', '30', '-b:v', '0'])
            
            cmd.append(str(output_path))
            
            job['ffmpeg_command'] = ' '.join(cmd)
            job['status'] = 'converting'
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0 and output_path.exists():
                job['status'] = 'completed'
                job['ffmpeg_used'] = True
                job['output_size_mb'] = round(output_path.stat().st_size / (1024 * 1024), 2)
            else:
                job['status'] = 'error'
                job['error'] = result.stderr[:500]
                
        except Exception as e:
            job['status'] = 'error'
            job['error'] = str(e)
        
        job['completed_at'] = datetime.now().isoformat()
        self.processing_queue.append(job)
        logger.info(f"Format conversion {job['status']}: {input_file} -> {output_format}")
        
        return job
    
    async def generate_image_async(
        self,
        prompt: str,
        style: str = "realistic",
        resolution: str = "1024x1024"
    ) -> Dict[str, Any]:
        """
        Generate an image from text prompt using LLM.
        
        Note: This requires an LLM with image generation capability (e.g., DALL-E).
        For local models, this generates a detailed prompt for use with Stable Diffusion.
        
        Args:
            prompt: Text description of desired image
            style: Image style (realistic, artistic, cartoon, etc.)
            resolution: Image resolution
        
        Returns:
            Dictionary with generation details
        """
        content = {
            "id": len(self.created_content) + 1,
            "type": "image",
            "prompt": prompt,
            "style": style,
            "resolution": resolution,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "llm_used": False
        }
        
        llm = await self._get_llm()
        if llm:
            try:
                # Generate enhanced prompt
                enhance_prompt = f"""Create a detailed image generation prompt for the following concept:
Concept: {prompt}
Style: {style}
Resolution: {resolution}

Provide:
1. A detailed prompt suitable for image generation (Stable Diffusion/DALL-E format)
2. Suggested negative prompt
3. Recommended settings"""
                
                response = await llm.chat([
                    {"role": "system", "content": "You are an expert at creating prompts for AI image generation."},
                    {"role": "user", "content": enhance_prompt}
                ])
                
                content['enhanced_prompt'] = response.content
                content['llm_used'] = True
                content['status'] = 'prompt_ready'
                content['note'] = 'Enhanced prompt generated. Use with Stable Diffusion or DALL-E.'
                
            except Exception as e:
                content['llm_error'] = str(e)
                content['status'] = 'prompt_only'
        else:
            content['status'] = 'prompt_only'
            content['note'] = 'LLM not available for prompt enhancement'
        
        self.created_content.append(content)
        logger.info(f"Image prompt generated: {prompt[:50]}...")
        
        return content
    
    def generate_image(
        self,
        prompt: str,
        style: str = "realistic",
        resolution: str = "1024x1024"
    ) -> Dict[str, Any]:
        """
        Generate an image prompt (synchronous version).
        
        Args:
            prompt: Text description of desired image
            style: Image style
            resolution: Image resolution
        
        Returns:
            Dictionary with generation details
        """
        content = {
            "id": len(self.created_content) + 1,
            "type": "image",
            "prompt": prompt,
            "style": style,
            "resolution": resolution,
            "status": "prompt_ready",
            "created_at": datetime.now().isoformat(),
            "note": "Prompt ready for external image generator"
        }
        self.created_content.append(content)
        logger.info(f"Image prompt created: {prompt[:50]}...")
        return content
    
    def generate_creator_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive content creator report.
        
        Returns:
            Dictionary with creator status and statistics
        """
        completed_jobs = [j for j in self.processing_queue if j.get('status') == 'completed']
        failed_jobs = [j for j in self.processing_queue if j.get('status') == 'error']
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "operational",
            "capabilities": {
                "ffmpeg": self.ffmpeg_available,
                "ffprobe": self.ffprobe_available,
                "llm": self.llm_available
            },
            "output_dir": str(self.output_dir),
            "statistics": {
                "total_content_created": len(self.created_content),
                "images_generated": len([c for c in self.created_content if c["type"] == "image"]),
                "thumbnails_created": len([c for c in self.created_content if c["type"] == "thumbnail"]),
                "processing_jobs_total": len(self.processing_queue),
                "jobs_completed": len(completed_jobs),
                "jobs_failed": len(failed_jobs),
                "ffmpeg_jobs": len([j for j in self.processing_queue if j.get('ffmpeg_used')])
            }
        }


if __name__ == "__main__":
    # Test the agent
    logging.basicConfig(level=logging.INFO)
    
    agent = ContentCreatorAgent()
    
    print("=" * 60)
    print("CONTENT CREATOR AGENT - Real Implementation")
    print("=" * 60)
    print(f"FFmpeg Available: {agent.ffmpeg_available}")
    print(f"FFprobe Available: {agent.ffprobe_available}")
    print(f"LLM Available: {agent.llm_available}")
    print(f"Output Directory: {agent.output_dir}")
    print()
    
    # Generate sample content (prompts only without actual generation)
    agent.generate_image("A serene mountain landscape at sunset", style="artistic")
    agent.generate_image("Modern office interior design", style="realistic")
    
    # Video operations would work if FFmpeg is installed
    # agent.create_thumbnail("/videos/presentation.mp4", "00:01:30")
    # agent.process_video("/videos/raw_footage.mp4", ["trim:0:30", "resize:1280x720"])
    # agent.convert_format("/videos/demo.avi", "mp4")
    
    # Generate report
    report = agent.generate_creator_report()
    print("\nCreator Report:")
    print(json.dumps(report, indent=2))
