#!/usr/bin/env python3
"""
Content Editing Agent - Real Implementation
Provides content creation and editing capabilities with media processing.

Uses FFmpeg for actual media analysis and processing when available.
Falls back to basic file inspection when FFmpeg is not installed.

Usage:
    from agents.content_editing.content_editing_agent import ContentEditingAgent
    
    agent = ContentEditingAgent()
    
    # Analyze media file
    analysis = agent.analyze_content('/path/to/video.mp4')
    
    # Optimize media (reduce file size)
    result = agent.optimize_media('/path/to/video.mp4', target_quality=28)
    
    # Apply edits
    result = agent.edit_content('/path/to/video.mp4', [
        {'type': 'trim', 'start': '00:00:10', 'end': '00:01:00'},
        {'type': 'resize', 'width': 1280, 'height': 720}
    ])
"""

import os
import json
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for FFmpeg availability
FFMPEG_AVAILABLE = shutil.which('ffmpeg') is not None
FFPROBE_AVAILABLE = shutil.which('ffprobe') is not None

if FFMPEG_AVAILABLE:
    logger.info("FFmpeg available for media processing")
else:
    logger.warning("FFmpeg not found - some features will use fallback mode")


class ContentEditingAgent:
    """
    Agent for content creation and editing tasks with real FFmpeg integration.
    
    This agent provides:
    - Media file analysis with FFprobe
    - Video/audio optimization with FFmpeg
    - Content editing operations (trim, resize, convert)
    - Transcript generation framework
    
    Attributes:
        ffmpeg_available: Whether FFmpeg is available
        ffprobe_available: Whether FFprobe is available
        output_dir: Directory for output files
    """
    
    def __init__(self, output_dir: str = 'data/content_editing'):
        """
        Initialize the Content Editing Agent.
        
        Args:
            output_dir: Directory for storing output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.ffmpeg_available = FFMPEG_AVAILABLE
        self.ffprobe_available = FFPROBE_AVAILABLE
        self.edit_history: List[Dict] = []
        
        logger.info(f"ContentEditingAgent initialized (FFmpeg={self.ffmpeg_available}, FFprobe={self.ffprobe_available})")
    
    def analyze_content(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze content file (video, audio, text, image).
        
        Uses FFprobe for media analysis when available, falls back to
        basic file inspection otherwise.
        
        Args:
            file_path: Path to the content file
            
        Returns:
            Dictionary with analysis results including metadata and suggestions
        """
        path = Path(file_path)
        file_type = self._detect_file_type(file_path)
        
        analysis = {
            'file': file_path,
            'type': file_type,
            'exists': path.exists(),
            'status': 'analyzed',
            'metadata': {},
            'suggestions': [],
            'real_analysis': False,
            'timestamp': datetime.now().isoformat()
        }
        
        if not path.exists():
            analysis['status'] = 'error'
            analysis['error'] = 'File not found'
            return analysis
        
        # Get basic file info
        stat = path.stat()
        analysis['metadata']['size_bytes'] = stat.st_size
        analysis['metadata']['size_mb'] = round(stat.st_size / (1024 * 1024), 2)
        analysis['metadata']['modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        # Use FFprobe for detailed media analysis
        if file_type in ['video', 'audio'] and self.ffprobe_available:
            ffprobe_data = self._get_media_info_ffprobe(file_path)
            if ffprobe_data:
                analysis['real_analysis'] = True
                analysis['metadata'].update(ffprobe_data)
                
                # Generate intelligent suggestions based on analysis
                analysis['suggestions'] = self._generate_suggestions(analysis['metadata'], file_type)
        else:
            # Fallback suggestions for demo mode
            if file_type == 'video':
                analysis['suggestions'] = [
                    'Consider adding captions for accessibility',
                    'Optimize file size for web delivery',
                    'Extract thumbnail at key frames'
                ]
            elif file_type == 'audio':
                analysis['suggestions'] = [
                    'Normalize audio levels',
                    'Remove background noise',
                    'Add chapter markers'
                ]
            elif file_type == 'image':
                analysis['suggestions'] = [
                    'Compress for web delivery',
                    'Generate multiple resolutions',
                    'Add watermark if needed'
                ]
        
        return analysis
    
    def _get_media_info_ffprobe(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get media information using FFprobe.
        
        Args:
            file_path: Path to media file
            
        Returns:
            Dictionary with media metadata or None on failure
        """
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(file_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.warning(f"FFprobe failed for {file_path}")
                return None
            
            probe_data = json.loads(result.stdout)
            metadata = {}
            
            # Extract format info
            if 'format' in probe_data:
                fmt = probe_data['format']
                metadata['duration'] = float(fmt.get('duration', 0))
                metadata['duration_formatted'] = self._format_duration(metadata['duration'])
                metadata['bitrate'] = int(fmt.get('bit_rate', 0))
                metadata['format_name'] = fmt.get('format_name', '')
            
            # Extract stream info
            for stream in probe_data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    metadata['video_codec'] = stream.get('codec_name', '')
                    metadata['width'] = stream.get('width', 0)
                    metadata['height'] = stream.get('height', 0)
                    metadata['resolution'] = f"{metadata['width']}x{metadata['height']}"
                    metadata['fps'] = self._parse_fps(stream.get('r_frame_rate', '0/1'))
                elif stream.get('codec_type') == 'audio':
                    metadata['audio_codec'] = stream.get('codec_name', '')
                    metadata['sample_rate'] = int(stream.get('sample_rate', 0))
                    metadata['channels'] = stream.get('channels', 0)
            
            return metadata
            
        except subprocess.TimeoutExpired:
            logger.error(f"FFprobe timeout for {file_path}")
            return None
        except Exception as e:
            logger.error(f"FFprobe error: {e}")
            return None
    
    def _generate_suggestions(self, metadata: Dict, file_type: str) -> List[str]:
        """
        Generate optimization suggestions based on actual metadata.
        
        Args:
            metadata: File metadata from analysis
            file_type: Type of file
            
        Returns:
            List of suggestion strings
        """
        suggestions = []
        
        if file_type == 'video':
            # Resolution suggestions
            width = metadata.get('width', 0)
            if width > 1920:
                suggestions.append(f'Consider downscaling from {width}p to 1080p for smaller file size')
            
            # Bitrate suggestions
            bitrate = metadata.get('bitrate', 0)
            if bitrate > 10_000_000:  # 10 Mbps
                suggestions.append(f'High bitrate detected ({bitrate//1_000_000}Mbps) - consider compression')
            
            # Codec suggestions
            codec = metadata.get('video_codec', '')
            if codec.lower() not in ['h264', 'hevc', 'av1']:
                suggestions.append(f'Consider converting from {codec} to H.264/H.265 for better compatibility')
            
            # Duration-based suggestions
            duration = metadata.get('duration', 0)
            if duration > 300:  # 5 minutes
                suggestions.append('Long video - consider adding chapter markers')
            
            # Always suggest captions
            suggestions.append('Add captions for accessibility')
            
        elif file_type == 'audio':
            sample_rate = metadata.get('sample_rate', 0)
            if sample_rate > 48000:
                suggestions.append(f'High sample rate ({sample_rate}Hz) - 44.1kHz or 48kHz is usually sufficient')
            
            channels = metadata.get('channels', 0)
            if channels == 1:
                suggestions.append('Mono audio detected - consider stereo for better listening experience')
        
        return suggestions
    
    def edit_content(self, file_path: str, edits: List[Dict]) -> Dict[str, Any]:
        """
        Apply edits to content file.
        
        Supported edit types:
        - trim: {start: "HH:MM:SS", end: "HH:MM:SS"}
        - resize: {width: int, height: int}
        - convert: {format: "mp4"|"webm"|"mp3"}
        - compress: {quality: 18-28}
        
        Args:
            file_path: Path to source file
            edits: List of edit operations
            
        Returns:
            Dictionary with edit results
        """
        path = Path(file_path)
        
        result = {
            'original': file_path,
            'edited': None,
            'edits_requested': len(edits),
            'edits_applied': 0,
            'status': 'success',
            'timestamp': datetime.now().isoformat()
        }
        
        if not path.exists():
            result['status'] = 'error'
            result['error'] = 'Source file not found'
            return result
        
        if not self.ffmpeg_available:
            result['status'] = 'simulated'
            result['note'] = 'FFmpeg not available - edits simulated'
            result['edited'] = str(self.output_dir / f"{path.stem}_edited{path.suffix}")
            result['edits_applied'] = len(edits)
            return result
        
        # Build FFmpeg command based on edits
        output_path = self.output_dir / f"{path.stem}_edited{path.suffix}"
        cmd = ['ffmpeg', '-y', '-i', str(path)]
        filters = []
        
        for edit in edits:
            edit_type = edit.get('type', '')
            
            if edit_type == 'trim':
                if 'start' in edit:
                    cmd.extend(['-ss', edit['start']])
                if 'end' in edit:
                    cmd.extend(['-to', edit['end']])
                result['edits_applied'] += 1
                
            elif edit_type == 'resize':
                width = edit.get('width')
                height = edit.get('height')
                # Only add scale filter if we have valid dimensions
                if width and height and isinstance(width, int) and isinstance(height, int) and width > 0 and height > 0:
                    filters.append(f'scale={width}:{height}')
                    result['edits_applied'] += 1
                elif width or height:
                    # Allow -1 for auto-scaling if at least one dimension is valid
                    w = width if isinstance(width, int) and width > 0 else -1
                    h = height if isinstance(height, int) and height > 0 else -1
                    if w > 0 or h > 0:
                        filters.append(f'scale={w}:{h}')
                        result['edits_applied'] += 1
                
            elif edit_type == 'convert':
                new_format = edit.get('format', 'mp4')
                output_path = output_path.with_suffix(f'.{new_format}')
                result['edits_applied'] += 1
                
            elif edit_type == 'compress':
                quality = edit.get('quality', 23)
                cmd.extend(['-crf', str(quality)])
                result['edits_applied'] += 1
        
        if filters:
            cmd.extend(['-vf', ','.join(filters)])
        
        cmd.append(str(output_path))
        
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if proc.returncode == 0:
                result['edited'] = str(output_path)
                result['status'] = 'success'
                
                # Record in history
                self.edit_history.append({
                    'original': file_path,
                    'edited': str(output_path),
                    'edits': edits,
                    'timestamp': result['timestamp']
                })
            else:
                result['status'] = 'error'
                result['error'] = proc.stderr[:500] if proc.stderr else 'FFmpeg failed'
                
        except subprocess.TimeoutExpired:
            result['status'] = 'error'
            result['error'] = 'Processing timeout (5 minutes)'
        except Exception as e:
            result['status'] = 'error'
            result['error'] = self._truncate_error(e)
        
        return result
    
    def generate_transcript(self, audio_file: str) -> Dict[str, Any]:
        """
        Generate transcript from audio/video file.
        
        Note: Full transcription requires external speech-to-text service.
        This method provides the framework for integration with services
        like Whisper, Google Speech-to-Text, or AWS Transcribe.
        
        Args:
            audio_file: Path to audio or video file
            
        Returns:
            Dictionary with transcript data
        """
        path = Path(audio_file)
        
        transcript = {
            'file': audio_file,
            'text': '',
            'timestamps': [],
            'status': 'framework',
            'timestamp': datetime.now().isoformat()
        }
        
        if not path.exists():
            transcript['status'] = 'error'
            transcript['error'] = 'File not found'
            return transcript
        
        # Get duration if available
        if self.ffprobe_available:
            metadata = self._get_media_info_ffprobe(audio_file)
            if metadata:
                transcript['duration'] = metadata.get('duration', 0)
        
        # Framework note for integration
        transcript['integration_options'] = [
            'OpenAI Whisper (local or API)',
            'Google Cloud Speech-to-Text',
            'AWS Transcribe',
            'Azure Speech Services'
        ]
        transcript['note'] = 'Transcription requires external STT service integration'
        
        return transcript
    
    def optimize_media(self, file_path: str, target_quality: int = 23) -> Dict[str, Any]:
        """
        Optimize media file for size/quality balance.
        
        Uses FFmpeg CRF (Constant Rate Factor) for quality-based encoding.
        Lower CRF = higher quality, larger file (range: 18-28 recommended).
        
        Args:
            file_path: Path to source file
            target_quality: CRF value (18=high quality, 28=smaller file)
            
        Returns:
            Dictionary with optimization results
        """
        path = Path(file_path)
        
        result = {
            'original': file_path,
            'optimized': None,
            'original_size': 0,
            'new_size': 0,
            'compression_ratio': 0,
            'quality_setting': target_quality,
            'status': 'success',
            'timestamp': datetime.now().isoformat()
        }
        
        if not path.exists():
            result['status'] = 'error'
            result['error'] = 'File not found'
            return result
        
        result['original_size'] = path.stat().st_size
        
        if not self.ffmpeg_available:
            result['status'] = 'simulated'
            result['note'] = 'FFmpeg not available - optimization simulated'
            result['optimized'] = str(self.output_dir / f"{path.stem}_optimized{path.suffix}")
            result['new_size'] = int(result['original_size'] * 0.6)  # Estimated 40% reduction
            result['compression_ratio'] = 0.6
            return result
        
        output_path = self.output_dir / f"{path.stem}_optimized{path.suffix}"
        
        cmd = [
            'ffmpeg', '-y', '-i', str(path),
            '-c:v', 'libx264', '-crf', str(target_quality),
            '-c:a', 'aac', '-b:a', '128k',
            '-preset', 'medium',
            str(output_path)
        ]
        
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if proc.returncode == 0 and output_path.exists():
                result['optimized'] = str(output_path)
                result['new_size'] = output_path.stat().st_size
                result['compression_ratio'] = round(result['new_size'] / result['original_size'], 2)
                result['size_reduction'] = f"{(1 - result['compression_ratio']) * 100:.1f}%"
            else:
                result['status'] = 'error'
                result['error'] = proc.stderr[:500] if proc.stderr else 'FFmpeg optimization failed'
                
        except subprocess.TimeoutExpired:
            result['status'] = 'error'
            result['error'] = 'Optimization timeout (10 minutes)'
        except Exception as e:
            result['status'] = 'error'
            result['error'] = self._truncate_error(e)
        
        return result
    
    def get_edit_history(self) -> List[Dict]:
        """
        Get the history of edit operations.
        
        Returns:
            List of edit operation records
        """
        return self.edit_history.copy()
    
    @staticmethod
    def _detect_file_type(file_path: str) -> str:
        """
        Detect file type from extension.
        
        Args:
            file_path: Path to file
            
        Returns:
            File type string
        """
        ext = Path(file_path).suffix.lower().lstrip('.')
        
        video_exts = {'mp4', 'avi', 'mkv', 'mov', 'webm', 'wmv', 'flv'}
        audio_exts = {'mp3', 'wav', 'flac', 'aac', 'm4a', 'ogg', 'wma'}
        text_exts = {'txt', 'md', 'doc', 'docx', 'pdf', 'rtf'}
        image_exts = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg', 'tiff'}
        
        if ext in video_exts:
            return 'video'
        elif ext in audio_exts:
            return 'audio'
        elif ext in text_exts:
            return 'text'
        elif ext in image_exts:
            return 'image'
        else:
            return 'unknown'
    
    @staticmethod
    def _truncate_error(error: Exception, max_length: int = 500) -> str:
        """Truncate error message for consistent logging."""
        msg = str(error)
        return msg[:max_length] if msg else 'Unknown error'
    
    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration in seconds to HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
    
    @staticmethod
    def _parse_fps(fps_str: str) -> float:
        """Parse FFprobe frame rate string."""
        try:
            if '/' in fps_str:
                parts = fps_str.split('/', 1)
                if len(parts) == 2:
                    num, den = parts
                    return round(float(num) / float(den), 2)
                return 0.0
            return float(fps_str)
        except (ValueError, ZeroDivisionError):
            return 0.0


def main():
    """Main entry point for the agent"""
    agent = ContentEditingAgent()
    
    print("=" * 60)
    print("CONTENT EDITING AGENT - Real Implementation")
    print("=" * 60)
    print(f"FFmpeg Available: {agent.ffmpeg_available}")
    print(f"FFprobe Available: {agent.ffprobe_available}")
    print(f"Output Directory: {agent.output_dir}")
    print()
    
    # Example analysis
    analysis = agent.analyze_content('example.mp4')
    print("Content Analysis:")
    print(json.dumps(analysis, indent=2))


if __name__ == '__main__':
    main()
