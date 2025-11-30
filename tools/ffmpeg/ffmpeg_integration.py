#!/usr/bin/env python3
"""
FFmpeg Integration - Real Implementation
Provides media processing capabilities for content editing.

Uses subprocess to execute real FFmpeg commands when available.
Falls back to simulated results when FFmpeg is not installed.

Usage:
    from tools.ffmpeg.ffmpeg_integration import FFmpegIntegration
    
    ffmpeg = FFmpegIntegration()
    
    # Get media info
    info = ffmpeg.get_media_info('/path/to/video.mp4')
    
    # Convert video
    result = ffmpeg.convert_video('/path/to/input.mp4', '/path/to/output.webm', codec='vp9')
    
    # Extract audio
    result = ffmpeg.extract_audio('/path/to/video.mp4', '/path/to/audio.mp3')
"""

import os
import subprocess
import json
import shutil
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for FFmpeg availability
FFMPEG_AVAILABLE = shutil.which('ffmpeg') is not None
FFPROBE_AVAILABLE = shutil.which('ffprobe') is not None


class FFmpegIntegration:
    """
    Integration with FFmpeg for real media processing.
    
    This class provides:
    - Media file analysis using FFprobe
    - Video format conversion
    - Audio extraction
    - Thumbnail generation
    - Video compression
    - Batch processing
    
    Attributes:
        ffmpeg_available: Whether FFmpeg is available
        ffprobe_available: Whether FFprobe is available
    """
    
    def __init__(self):
        """Initialize FFmpeg integration."""
        self.ffmpeg_available = FFMPEG_AVAILABLE
        self.ffprobe_available = FFPROBE_AVAILABLE
        
        if self.ffmpeg_available:
            logger.info("FFmpeg integration initialized with real FFmpeg")
        else:
            logger.warning("FFmpeg not found - operations will be simulated")
    
    def get_media_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed information about a media file.
        
        Uses FFprobe to extract format and stream information.
        
        Args:
            file_path: Path to the media file
            
        Returns:
            Dictionary with media metadata
        """
        path = Path(file_path)
        
        info = {
            'file': file_path,
            'exists': path.exists(),
            'real_info': False,
            'format': 'unknown',
            'duration': 0,
            'duration_formatted': '00:00',
            'video_codec': 'unknown',
            'audio_codec': 'unknown',
            'resolution': 'unknown',
            'timestamp': datetime.now().isoformat()
        }
        
        if not path.exists():
            info['error'] = 'File not found'
            return info
        
        # Get basic file info
        stat = path.stat()
        info['size_bytes'] = stat.st_size
        info['size_mb'] = round(stat.st_size / (1024 * 1024), 2)
        
        if not self.ffprobe_available:
            info['note'] = 'FFprobe not available - basic info only'
            return info
        
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
                    info['format'] = fmt.get('format_name', 'unknown')
                    info['duration'] = float(fmt.get('duration', 0))
                    info['duration_formatted'] = self._format_duration(info['duration'])
                    info['bitrate'] = int(fmt.get('bit_rate', 0))
                
                # Extract stream info
                for stream in probe_data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        info['video_codec'] = stream.get('codec_name', 'unknown')
                        info['width'] = stream.get('width', 0)
                        info['height'] = stream.get('height', 0)
                        info['resolution'] = f"{info['width']}x{info['height']}"
                        info['fps'] = self._parse_fps(stream.get('r_frame_rate', '0/1'))
                    elif stream.get('codec_type') == 'audio':
                        info['audio_codec'] = stream.get('codec_name', 'unknown')
                        info['sample_rate'] = int(stream.get('sample_rate', 0))
                        info['channels'] = stream.get('channels', 0)
            else:
                info['error'] = 'FFprobe failed to analyze file'
                
        except subprocess.TimeoutExpired:
            info['error'] = 'FFprobe timeout'
        except json.JSONDecodeError:
            info['error'] = 'Failed to parse FFprobe output'
        except Exception as e:
            info['error'] = str(e)
        
        return info
    
    def convert_video(self, input_file: str, output_file: str, codec: str = 'h264') -> Dict[str, Any]:
        """
        Convert video to different format/codec.
        
        Args:
            input_file: Path to source video
            output_file: Path for output video
            codec: Target codec (h264, hevc, vp9, av1)
            
        Returns:
            Dictionary with conversion results
        """
        input_path = Path(input_file)
        output_path = Path(output_file)
        
        result = {
            'input': input_file,
            'output': output_file,
            'codec': codec,
            'status': 'success',
            'real_conversion': False,
            'timestamp': datetime.now().isoformat()
        }
        
        if not input_path.exists():
            result['status'] = 'error'
            result['error'] = 'Input file not found'
            return result
        
        if not self.ffmpeg_available:
            result['status'] = 'simulated'
            result['note'] = 'FFmpeg not available - conversion simulated'
            return result
        
        # Map codec names to FFmpeg encoders
        codec_map = {
            'h264': 'libx264',
            'hevc': 'libx265',
            'h265': 'libx265',
            'vp9': 'libvpx-vp9',
            'av1': 'libaom-av1'
        }
        encoder = codec_map.get(codec.lower(), 'libx264')
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            'ffmpeg', '-y', '-i', str(input_path),
            '-c:v', encoder, '-c:a', 'aac',
            '-preset', 'medium',
            str(output_path)
        ]
        
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if proc.returncode == 0 and output_path.exists():
                result['real_conversion'] = True
                result['output_size'] = output_path.stat().st_size
            else:
                result['status'] = 'error'
                result['error'] = proc.stderr[:500] if proc.stderr else 'FFmpeg conversion failed'
                
        except subprocess.TimeoutExpired:
            result['status'] = 'error'
            result['error'] = 'Conversion timeout (10 minutes)'
        except Exception as e:
            result['status'] = 'error'
            result['error'] = self._truncate_error(e)
        
        return result
    
    def extract_audio(self, video_file: str, audio_file: str, codec: str = 'mp3') -> Dict[str, Any]:
        """
        Extract audio track from video file.
        
        Args:
            video_file: Path to source video
            audio_file: Path for output audio
            codec: Audio codec (mp3, aac, flac, wav)
            
        Returns:
            Dictionary with extraction results
        """
        video_path = Path(video_file)
        audio_path = Path(audio_file)
        
        result = {
            'video_file': video_file,
            'audio_file': audio_file,
            'codec': codec,
            'status': 'success',
            'real_extraction': False,
            'timestamp': datetime.now().isoformat()
        }
        
        if not video_path.exists():
            result['status'] = 'error'
            result['error'] = 'Video file not found'
            return result
        
        if not self.ffmpeg_available:
            result['status'] = 'simulated'
            result['note'] = 'FFmpeg not available - extraction simulated'
            return result
        
        # Map codec names to FFmpeg encoders
        codec_map = {
            'mp3': ('libmp3lame', '192k'),
            'aac': ('aac', '192k'),
            'flac': ('flac', None),
            'wav': ('pcm_s16le', None)
        }
        encoder, bitrate = codec_map.get(codec.lower(), ('libmp3lame', '192k'))
        
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = ['ffmpeg', '-y', '-i', str(video_path), '-vn', '-c:a', encoder]
        if bitrate:
            cmd.extend(['-b:a', bitrate])
        cmd.append(str(audio_path))
        
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if proc.returncode == 0 and audio_path.exists():
                result['real_extraction'] = True
                result['audio_size'] = audio_path.stat().st_size
            else:
                result['status'] = 'error'
                result['error'] = proc.stderr[:500] if proc.stderr else 'Audio extraction failed'
                
        except subprocess.TimeoutExpired:
            result['status'] = 'error'
            result['error'] = 'Extraction timeout (5 minutes)'
        except Exception as e:
            result['status'] = 'error'
            result['error'] = self._truncate_error(e)
        
        return result
    
    def create_thumbnail(self, video_file: str, thumbnail_file: str, timestamp: str = '00:00:01') -> Dict[str, Any]:
        """
        Create thumbnail image from video at specified timestamp.
        
        Args:
            video_file: Path to source video
            thumbnail_file: Path for output image
            timestamp: Timestamp to capture (HH:MM:SS format)
            
        Returns:
            Dictionary with thumbnail creation results
        """
        video_path = Path(video_file)
        thumb_path = Path(thumbnail_file)
        
        result = {
            'video_file': video_file,
            'thumbnail': thumbnail_file,
            'timestamp': timestamp,
            'status': 'success',
            'real_thumbnail': False,
            'created_at': datetime.now().isoformat()
        }
        
        if not video_path.exists():
            result['status'] = 'error'
            result['error'] = 'Video file not found'
            return result
        
        if not self.ffmpeg_available:
            result['status'] = 'simulated'
            result['note'] = 'FFmpeg not available - thumbnail creation simulated'
            return result
        
        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            'ffmpeg', '-y', '-ss', timestamp,
            '-i', str(video_path),
            '-vframes', '1',
            '-q:v', '2',
            str(thumb_path)
        ]
        
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if proc.returncode == 0 and thumb_path.exists():
                result['real_thumbnail'] = True
                result['thumbnail_size'] = thumb_path.stat().st_size
            else:
                result['status'] = 'error'
                result['error'] = proc.stderr[:500] if proc.stderr else 'Thumbnail creation failed'
                
        except subprocess.TimeoutExpired:
            result['status'] = 'error'
            result['error'] = 'Thumbnail creation timeout'
        except Exception as e:
            result['status'] = 'error'
            result['error'] = self._truncate_error(e)
        
        return result
    
    def compress_video(self, input_file: str, output_file: str, quality: int = 23) -> Dict[str, Any]:
        """
        Compress video file using CRF-based encoding.
        
        Args:
            input_file: Path to source video
            output_file: Path for compressed output
            quality: CRF value (18=high quality, 28=smaller file)
            
        Returns:
            Dictionary with compression results
        """
        input_path = Path(input_file)
        output_path = Path(output_file)
        
        result = {
            'input': input_file,
            'output': output_file,
            'quality': quality,
            'status': 'success',
            'real_compression': False,
            'original_size': 0,
            'compressed_size': 0,
            'compression_ratio': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        if not input_path.exists():
            result['status'] = 'error'
            result['error'] = 'Input file not found'
            return result
        
        result['original_size'] = input_path.stat().st_size
        
        if not self.ffmpeg_available:
            result['status'] = 'simulated'
            result['note'] = 'FFmpeg not available - compression simulated'
            result['compressed_size'] = int(result['original_size'] * 0.6)
            result['compression_ratio'] = 0.6
            return result
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            'ffmpeg', '-y', '-i', str(input_path),
            '-c:v', 'libx264', '-crf', str(quality),
            '-c:a', 'aac', '-b:a', '128k',
            '-preset', 'medium',
            str(output_path)
        ]
        
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if proc.returncode == 0 and output_path.exists():
                result['real_compression'] = True
                result['compressed_size'] = output_path.stat().st_size
                result['compression_ratio'] = round(result['compressed_size'] / result['original_size'], 2)
                result['size_reduction'] = f"{(1 - result['compression_ratio']) * 100:.1f}%"
            else:
                result['status'] = 'error'
                result['error'] = proc.stderr[:500] if proc.stderr else 'Compression failed'
                
        except subprocess.TimeoutExpired:
            result['status'] = 'error'
            result['error'] = 'Compression timeout (10 minutes)'
        except Exception as e:
            result['status'] = 'error'
            result['error'] = self._truncate_error(e)
        
        return result
    
    def batch_process(self, files: List[str], operation: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Batch process multiple media files.
        
        Args:
            files: List of file paths
            operation: Operation to perform (info, compress, convert, thumbnail)
            **kwargs: Additional arguments for the operation
            
        Returns:
            List of result dictionaries
        """
        results = []
        
        for file_path in files:
            if operation == 'info':
                result = self.get_media_info(file_path)
            elif operation == 'compress':
                output = kwargs.get('output_pattern', '{stem}_compressed{suffix}')
                path = Path(file_path)
                output_file = str(path.parent / output.format(stem=path.stem, suffix=path.suffix))
                result = self.compress_video(file_path, output_file, kwargs.get('quality', 23))
            elif operation == 'thumbnail':
                output = kwargs.get('output_pattern', '{stem}_thumb.jpg')
                path = Path(file_path)
                output_file = str(path.parent / output.format(stem=path.stem))
                result = self.create_thumbnail(file_path, output_file, kwargs.get('timestamp', '00:00:01'))
            else:
                result = {
                    'file': file_path,
                    'operation': operation,
                    'status': 'error',
                    'error': f'Unknown operation: {operation}'
                }
            
            results.append(result)
        
        return results
    
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
                parts = fps_str.split('/', 1)  # Split only on first slash
                if len(parts) == 2:
                    num, den = parts
                    return round(float(num) / float(den), 2)
                return 0.0
            return float(fps_str)
        except (ValueError, ZeroDivisionError):
            return 0.0


def main():
    """Test the integration"""
    integration = FFmpegIntegration()
    
    print("=" * 60)
    print("FFMPEG INTEGRATION - Real Implementation")
    print("=" * 60)
    print(f"FFmpeg Available: {integration.ffmpeg_available}")
    print(f"FFprobe Available: {integration.ffprobe_available}")
    print()
    
    # Get media info example
    info = integration.get_media_info('example.mp4')
    print("Media Info:")
    print(json.dumps(info, indent=2))


if __name__ == '__main__':
    main()
