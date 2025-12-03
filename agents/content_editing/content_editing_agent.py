#!/usr/bin/env python3
"""
Content Editing Agent - Real Implementation
Provides content analysis, editing, transcription, and optimization capabilities.

This agent integrates with:
- FFmpeg/FFprobe for media analysis and processing
- Whisper (OpenAI or local) for transcription
- File system for media file handling

Usage:
    from agents.content_editing.content_editing_agent import ContentEditingAgent
    
    agent = ContentEditingAgent()
    
    # Analyze media file
    analysis = agent.analyze_content("/path/to/video.mp4")
    
    # Generate transcript (requires Whisper)
    transcript = await agent.generate_transcript("/path/to/audio.mp3")
    
    # Optimize media
    result = agent.optimize_media("/path/to/large_video.mp4", target_size_mb=50)
"""

import os
import sys
import json
import asyncio
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for FFmpeg
FFMPEG_PATH = shutil.which('ffmpeg')
FFPROBE_PATH = shutil.which('ffprobe')
FFMPEG_AVAILABLE = FFMPEG_PATH is not None
FFPROBE_AVAILABLE = FFPROBE_PATH is not None

if FFMPEG_AVAILABLE:
    logger.info(f"FFmpeg available at: {FFMPEG_PATH}")
else:
    logger.warning("FFmpeg not found - media processing will be limited")

# Check for Whisper
WHISPER_AVAILABLE = False
try:
    import whisper
    WHISPER_AVAILABLE = True
    logger.info("OpenAI Whisper available for transcription")
except ImportError:
    try:
        import openai
        WHISPER_AVAILABLE = True
        logger.info("OpenAI API available for transcription")
    except ImportError:
        logger.warning("Whisper not available - transcription will be limited")


class ContentEditingAgent:
    """
    Agent for content editing tasks with real media processing.
    
    Real implementation features:
    - FFmpeg-based media analysis (duration, codec, resolution, bitrate)
    - Whisper-based transcription (local or API)
    - FFmpeg-based optimization (compression, format conversion)
    - Edit operations (trim, crop, resize, mute, extract audio)
    
    Attributes:
        ffmpeg_available: Whether FFmpeg is available
        whisper_available: Whether Whisper is available
        output_dir: Directory for output files
    """
    
    def __init__(self, output_dir: str = "data/content_editing"):
        """Initialize the Content Editing Agent."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.ffmpeg_available = FFMPEG_AVAILABLE
        self.ffprobe_available = FFPROBE_AVAILABLE
        self.whisper_available = WHISPER_AVAILABLE
        
        self.ffmpeg_path = os.getenv('FFMPEG_PATH', FFMPEG_PATH or 'ffmpeg')
        self.ffprobe_path = os.getenv('FFPROBE_PATH', FFPROBE_PATH or 'ffprobe')
        
        # Whisper model (lazy loaded)
        self._whisper_model = None
        
        logger.info(f"ContentEditingAgent initialized (FFmpeg={self.ffmpeg_available}, Whisper={self.whisper_available})")
    
    def analyze_content(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze content file using FFprobe for real metadata extraction.
        
        Args:
            file_path: Path to media file
            
        Returns:
            Dictionary with file analysis including:
            - type: Detected file type
            - duration: Length in seconds (for media)
            - resolution: Width x Height (for video/images)
            - codec: Audio/video codec
            - bitrate: Bitrate in bps
            - size_bytes: File size
            - suggestions: Optimization suggestions
        """
        analysis = {
            'file': file_path,
            'exists': False,
            'type': self._detect_file_type(file_path),
            'status': 'analyzed',
            'metadata': {},
            'suggestions': [],
            'real_analysis': False
        }
        
        path = Path(file_path)
        if not path.exists():
            analysis['status'] = 'error'
            analysis['error'] = 'File not found'
            return analysis
        
        analysis['exists'] = True
        analysis['size_bytes'] = path.stat().st_size
        analysis['size_mb'] = round(path.stat().st_size / (1024 * 1024), 2)
        
        # Use FFprobe for real media analysis
        if self.ffprobe_available and analysis['type'] in ['video', 'audio']:
            try:
                cmd = [
                    self.ffprobe_path, '-v', 'quiet', '-print_format', 'json',
                    '-show_format', '-show_streams', str(path)
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    probe_data = json.loads(result.stdout)
                    analysis['real_analysis'] = True
                    
                    # Extract format info
                    if 'format' in probe_data:
                        fmt = probe_data['format']
                        analysis['metadata']['duration'] = float(fmt.get('duration', 0))
                        analysis['metadata']['bitrate'] = int(fmt.get('bit_rate', 0))
                        analysis['metadata']['format_name'] = fmt.get('format_name', '')
                        analysis['metadata']['format_long_name'] = fmt.get('format_long_name', '')
                    
                    # Extract stream info
                    video_streams = []
                    audio_streams = []
                    
                    for stream in probe_data.get('streams', []):
                        if stream['codec_type'] == 'video':
                            video_info = {
                                'width': stream.get('width'),
                                'height': stream.get('height'),
                                'codec': stream.get('codec_name'),
                                'codec_long_name': stream.get('codec_long_name'),
                                'fps': self._parse_fps(stream.get('r_frame_rate', '0/1')),
                                'bit_rate': int(stream.get('bit_rate', 0)) if stream.get('bit_rate') else None
                            }
                            video_streams.append(video_info)
                            # Set main video properties
                            analysis['metadata']['width'] = video_info['width']
                            analysis['metadata']['height'] = video_info['height']
                            analysis['metadata']['video_codec'] = video_info['codec']
                            analysis['metadata']['fps'] = video_info['fps']
                            
                        elif stream['codec_type'] == 'audio':
                            audio_info = {
                                'codec': stream.get('codec_name'),
                                'codec_long_name': stream.get('codec_long_name'),
                                'channels': stream.get('channels'),
                                'sample_rate': stream.get('sample_rate'),
                                'bit_rate': int(stream.get('bit_rate', 0)) if stream.get('bit_rate') else None
                            }
                            audio_streams.append(audio_info)
                            analysis['metadata']['audio_codec'] = audio_info['codec']
                            analysis['metadata']['audio_channels'] = audio_info['channels']
                    
                    analysis['metadata']['video_streams'] = video_streams
                    analysis['metadata']['audio_streams'] = audio_streams
                    
                    # Generate real suggestions based on analysis
                    analysis['suggestions'] = self._generate_suggestions(analysis)
                    
            except subprocess.TimeoutExpired:
                analysis['probe_error'] = 'FFprobe timed out'
            except json.JSONDecodeError as e:
                analysis['probe_error'] = f'Failed to parse FFprobe output: {e}'
            except Exception as e:
                analysis['probe_error'] = str(e)
        
        elif analysis['type'] == 'image':
            # For images, use identify (ImageMagick) or PIL if available
            try:
                from PIL import Image
                with Image.open(path) as img:
                    analysis['metadata']['width'] = img.width
                    analysis['metadata']['height'] = img.height
                    analysis['metadata']['format'] = img.format
                    analysis['metadata']['mode'] = img.mode
                    analysis['real_analysis'] = True
                    analysis['suggestions'] = self._generate_image_suggestions(analysis)
            except ImportError:
                analysis['suggestions'].append('Install Pillow for image analysis: pip install Pillow')
            except Exception as e:
                analysis['error'] = f'Image analysis failed: {e}'
        
        return analysis
    
    def _generate_suggestions(self, analysis: Dict) -> List[str]:
        """Generate optimization suggestions based on analysis."""
        suggestions = []
        metadata = analysis.get('metadata', {})
        
        # Size suggestions
        size_mb = analysis.get('size_mb', 0)
        if size_mb > 100:
            suggestions.append(f'Large file ({size_mb}MB) - consider compression')
        
        # Resolution suggestions
        width = metadata.get('width', 0)
        height = metadata.get('height', 0)
        if width and height:
            if width > 1920 or height > 1080:
                suggestions.append(f'High resolution ({width}x{height}) - consider downscaling to 1080p for web')
            if width < 640:
                suggestions.append(f'Low resolution ({width}x{height}) - may appear pixelated')
        
        # Codec suggestions
        video_codec = metadata.get('video_codec', '').lower()
        if video_codec:
            if video_codec not in ['h264', 'h265', 'hevc', 'av1', 'vp9']:
                suggestions.append(f'Codec ({video_codec}) - consider converting to H.264 for compatibility')
            if video_codec in ['h265', 'hevc', 'av1']:
                suggestions.append(f'Modern codec ({video_codec}) - may not play on older devices')
        
        # Bitrate suggestions  
        bitrate = metadata.get('bitrate', 0)
        duration = metadata.get('duration', 0)
        if bitrate > 0 and duration > 0:
            expected_size_mb = (bitrate * duration) / (8 * 1024 * 1024)
            if bitrate > 10_000_000:  # > 10 Mbps
                suggestions.append(f'High bitrate ({bitrate//1000}kbps) - can reduce for smaller files')
        
        # Transcription suggestion
        if analysis.get('type') == 'video' and metadata.get('audio_codec'):
            suggestions.append('Contains audio - transcription available via generate_transcript()')
        
        return suggestions
    
    def _generate_image_suggestions(self, analysis: Dict) -> List[str]:
        """Generate suggestions for images."""
        suggestions = []
        metadata = analysis.get('metadata', {})
        
        width = metadata.get('width', 0)
        height = metadata.get('height', 0)
        
        if width > 4000 or height > 4000:
            suggestions.append('Very high resolution - consider resizing for web use')
        
        size_mb = analysis.get('size_mb', 0)
        if size_mb > 5:
            suggestions.append(f'Large file ({size_mb}MB) - consider compression')
        
        return suggestions
    
    def edit_content(self, file_path: str, edits: List[Dict]) -> Dict[str, Any]:
        """
        Apply edits to content using FFmpeg.
        
        Args:
            file_path: Path to input file
            edits: List of edit operations:
                - {"type": "trim", "start": "00:00:10", "end": "00:01:00"}
                - {"type": "resize", "width": 1280, "height": 720}
                - {"type": "crop", "x": 0, "y": 0, "width": 1920, "height": 1080}
                - {"type": "mute"} - Remove audio
                - {"type": "extract_audio", "format": "mp3"}
                - {"type": "fps", "value": 30}
                - {"type": "convert", "format": "mp4", "codec": "h264"}
        
        Returns:
            Dictionary with edit results
        """
        result = {
            'original': file_path,
            'edited': None,
            'edits_applied': 0,
            'status': 'pending',
            'ffmpeg_used': False,
            'errors': []
        }
        
        input_path = Path(file_path)
        if not input_path.exists():
            result['status'] = 'error'
            result['errors'].append('Input file not found')
            return result
        
        if not self.ffmpeg_available:
            result['status'] = 'error'
            result['errors'].append('FFmpeg not available - install FFmpeg to enable editing')
            return result
        
        # Build FFmpeg command
        ffmpeg_filters = []
        ffmpeg_options = []
        output_ext = input_path.suffix
        
        for edit in edits:
            edit_type = edit.get('type', '')
            
            if edit_type == 'trim':
                start = edit.get('start', '00:00:00')
                end = edit.get('end')
                ffmpeg_options.extend(['-ss', start])
                if end:
                    ffmpeg_options.extend(['-to', end])
            
            elif edit_type == 'resize':
                width = edit.get('width', -1)
                height = edit.get('height', -1)
                ffmpeg_filters.append(f'scale={width}:{height}')
            
            elif edit_type == 'crop':
                x = edit.get('x', 0)
                y = edit.get('y', 0)
                w = edit.get('width')
                h = edit.get('height')
                if w and h:
                    ffmpeg_filters.append(f'crop={w}:{h}:{x}:{y}')
            
            elif edit_type == 'mute':
                ffmpeg_options.extend(['-an'])
            
            elif edit_type == 'extract_audio':
                output_ext = '.' + edit.get('format', 'mp3')
                ffmpeg_options.extend(['-vn'])
            
            elif edit_type == 'fps':
                fps = edit.get('value', 30)
                ffmpeg_filters.append(f'fps={fps}')
            
            elif edit_type == 'convert':
                output_ext = '.' + edit.get('format', 'mp4')
                codec = edit.get('codec')
                if codec:
                    ffmpeg_options.extend(['-c:v', codec])
        
        # Generate output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"{input_path.stem}_edited_{timestamp}{output_ext}"
        output_path = self.output_dir / output_filename
        
        # Build full FFmpeg command
        cmd = [self.ffmpeg_path, '-y']  # -y to overwrite
        cmd.extend(ffmpeg_options)
        cmd.extend(['-i', str(input_path)])
        
        if ffmpeg_filters:
            cmd.extend(['-vf', ','.join(ffmpeg_filters)])
        
        cmd.append(str(output_path))
        
        # Execute FFmpeg
        try:
            logger.info(f"Running FFmpeg: {' '.join(cmd)}")
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if proc.returncode == 0:
                result['status'] = 'success'
                result['edited'] = str(output_path)
                result['edits_applied'] = len(edits)
                result['ffmpeg_used'] = True
                result['output_size_mb'] = round(output_path.stat().st_size / (1024 * 1024), 2)
            else:
                result['status'] = 'error'
                result['errors'].append(f'FFmpeg error: {proc.stderr[:500]}')
                
        except subprocess.TimeoutExpired:
            result['status'] = 'error'
            result['errors'].append('FFmpeg timed out after 5 minutes')
        except Exception as e:
            result['status'] = 'error'
            result['errors'].append(str(e))
        
        return result
    
    async def generate_transcript(self, audio_file: str, language: str = None) -> Dict[str, Any]:
        """
        Generate transcript from audio/video using Whisper.
        
        Args:
            audio_file: Path to audio or video file
            language: Optional language code (auto-detected if not provided)
        
        Returns:
            Dictionary with transcript text and timestamps
        """
        transcript = {
            'file': audio_file,
            'text': '',
            'segments': [],
            'language': None,
            'status': 'pending',
            'whisper_used': False
        }
        
        path = Path(audio_file)
        if not path.exists():
            transcript['status'] = 'error'
            transcript['error'] = 'File not found'
            return transcript
        
        if not self.whisper_available:
            transcript['status'] = 'error'
            transcript['error'] = 'Whisper not available. Install with: pip install openai-whisper'
            return transcript
        
        try:
            # Try local Whisper first
            import whisper
            
            if self._whisper_model is None:
                logger.info("Loading Whisper model (this may take a moment)...")
                self._whisper_model = whisper.load_model("base")
            
            logger.info(f"Transcribing: {audio_file}")
            result = self._whisper_model.transcribe(
                str(path),
                language=language,
                verbose=False
            )
            
            transcript['text'] = result.get('text', '').strip()
            transcript['language'] = result.get('language')
            transcript['segments'] = [
                {
                    'start': seg['start'],
                    'end': seg['end'],
                    'text': seg['text'].strip()
                }
                for seg in result.get('segments', [])
            ]
            transcript['status'] = 'success'
            transcript['whisper_used'] = True
            transcript['model'] = 'whisper-base'
            
        except ImportError:
            # Fall back to OpenAI API
            try:
                import openai
                
                client = openai.OpenAI()
                
                with open(path, 'rb') as f:
                    result = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=f,
                        language=language,
                        response_format="verbose_json"
                    )
                
                transcript['text'] = result.text
                transcript['language'] = result.language
                transcript['segments'] = [
                    {
                        'start': seg.start,
                        'end': seg.end,
                        'text': seg.text
                    }
                    for seg in getattr(result, 'segments', [])
                ]
                transcript['status'] = 'success'
                transcript['whisper_used'] = True
                transcript['model'] = 'whisper-1-api'
                
            except Exception as e:
                transcript['status'] = 'error'
                transcript['error'] = f'Transcription failed: {str(e)}'
        
        except Exception as e:
            transcript['status'] = 'error'
            transcript['error'] = f'Transcription failed: {str(e)}'
        
        return transcript
    
    def optimize_media(
        self,
        file_path: str,
        target_size_mb: Optional[int] = None,
        quality: str = "medium"
    ) -> Dict[str, Any]:
        """
        Optimize media file for size/quality using FFmpeg.
        
        Args:
            file_path: Path to media file
            target_size_mb: Target file size in MB (optional)
            quality: Quality preset - "low", "medium", "high"
        
        Returns:
            Dictionary with optimization results
        """
        result = {
            'original': file_path,
            'optimized': None,
            'original_size_mb': 0,
            'new_size_mb': 0,
            'compression_ratio': 0,
            'status': 'pending',
            'ffmpeg_used': False
        }
        
        input_path = Path(file_path)
        if not input_path.exists():
            result['status'] = 'error'
            result['error'] = 'File not found'
            return result
        
        if not self.ffmpeg_available:
            result['status'] = 'error'
            result['error'] = 'FFmpeg not available'
            return result
        
        original_size = input_path.stat().st_size
        result['original_size_mb'] = round(original_size / (1024 * 1024), 2)
        
        # Quality presets (CRF - lower is better quality, higher file size)
        crf_map = {
            'low': 28,
            'medium': 23,
            'high': 18
        }
        crf = crf_map.get(quality, 23)
        
        # Generate output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"{input_path.stem}_optimized_{timestamp}{input_path.suffix}"
        output_path = self.output_dir / output_filename
        
        # Build FFmpeg command
        cmd = [
            self.ffmpeg_path, '-y',
            '-i', str(input_path),
            '-c:v', 'libx264',
            '-crf', str(crf),
            '-preset', 'medium',
            '-c:a', 'aac',
            '-b:a', '128k',
            str(output_path)
        ]
        
        # If target size specified, calculate bitrate
        if target_size_mb:
            # Get duration
            analysis = self.analyze_content(file_path)
            duration = analysis.get('metadata', {}).get('duration', 0)
            
            if duration > 0:
                # Calculate required bitrate (in kbps)
                # target_size_kb = target_size_mb * 1024
                # bitrate = target_size_kb * 8 / duration (kbps)
                target_bits = target_size_mb * 8 * 1024 * 1024
                target_bitrate = int(target_bits / duration / 1000)  # kbps
                
                # Subtract audio bitrate (128k) and add some buffer
                video_bitrate = max(target_bitrate - 150, 100)
                
                cmd = [
                    self.ffmpeg_path, '-y',
                    '-i', str(input_path),
                    '-c:v', 'libx264',
                    '-b:v', f'{video_bitrate}k',
                    '-maxrate', f'{int(video_bitrate * 1.5)}k',
                    '-bufsize', f'{video_bitrate * 2}k',
                    '-preset', 'slow',
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    str(output_path)
                ]
        
        try:
            logger.info(f"Optimizing: {file_path}")
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if proc.returncode == 0 and output_path.exists():
                new_size = output_path.stat().st_size
                result['status'] = 'success'
                result['optimized'] = str(output_path)
                result['new_size_mb'] = round(new_size / (1024 * 1024), 2)
                result['compression_ratio'] = round(original_size / new_size, 2) if new_size > 0 else 0
                result['savings_mb'] = round((original_size - new_size) / (1024 * 1024), 2)
                result['ffmpeg_used'] = True
            else:
                result['status'] = 'error'
                result['error'] = f'FFmpeg error: {proc.stderr[:500] if proc.stderr else "Unknown error"}'
                
        except subprocess.TimeoutExpired:
            result['status'] = 'error'
            result['error'] = 'Optimization timed out'
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    @staticmethod
    def _detect_file_type(file_path: str) -> str:
        """Detect file type from extension."""
        ext = Path(file_path).suffix.lower().lstrip('.')
        
        video_exts = {'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'm4v'}
        audio_exts = {'mp3', 'wav', 'flac', 'aac', 'm4a', 'ogg', 'wma'}
        text_exts = {'txt', 'md', 'doc', 'docx', 'pdf', 'rtf'}
        image_exts = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'tiff', 'svg'}
        
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
    def _parse_fps(fps_str: str) -> float:
        """Parse FPS from FFprobe format (e.g., '30/1' or '30000/1001')."""
        try:
            if '/' in fps_str:
                num, den = fps_str.split('/')
                return round(float(num) / float(den), 2)
            return float(fps_str)
        except:
            return 0.0


def main():
    """Main entry point for the agent."""
    import asyncio
    
    agent = ContentEditingAgent()
    
    print("\n" + "=" * 60)
    print("Content Editing Agent - Status")
    print("=" * 60)
    print(f"FFmpeg Available: {'✅' if agent.ffmpeg_available else '❌'}")
    print(f"FFprobe Available: {'✅' if agent.ffprobe_available else '❌'}")
    print(f"Whisper Available: {'✅' if agent.whisper_available else '❌'}")
    print(f"Output Directory: {agent.output_dir}")
    print("=" * 60)
    
    # Demo analysis if file provided
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print(f"\nAnalyzing: {file_path}")
        analysis = agent.analyze_content(file_path)
        print(json.dumps(analysis, indent=2))
    else:
        print("\nUsage: python content_editing_agent.py <file_path>")
        print("\nCapabilities:")
        print("  - analyze_content(file_path) - Get media metadata and suggestions")
        print("  - edit_content(file_path, edits) - Apply edits (trim, resize, crop, etc.)")
        print("  - generate_transcript(audio_file) - Transcribe audio/video")
        print("  - optimize_media(file_path, target_size_mb) - Compress media")


if __name__ == '__main__':
    main()
