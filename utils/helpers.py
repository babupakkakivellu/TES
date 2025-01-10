import time
import math
import logging
from typing import Union, Dict, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class TimeFormatter:
    @staticmethod
    def format_duration(seconds: Union[int, float]) -> str:
        """Format seconds into HH:MM:SS"""
        try:
            seconds = int(seconds)
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except:
            return "00:00:00"

    @staticmethod
    def get_readable_time(seconds: Union[int, float]) -> str:
        """Get human readable time"""
        result = ""
        try:
            seconds = int(seconds)
            days = seconds // (24 * 3600)
            seconds = seconds % (24 * 3600)
            hours = seconds // 3600
            seconds %= 3600
            minutes = seconds // 60
            seconds %= 60
            
            if days > 0:
                result += f"{days}d "
            if hours > 0:
                result += f"{hours}h "
            if minutes > 0:
                result += f"{minutes}m "
            if seconds > 0:
                result += f"{seconds}s"
                
            return result.strip()
        except:
            return "0s"

class SizeFormatter:
    @staticmethod
    def format_size(size: Union[int, float]) -> str:
        """Format size in bytes to human readable format"""
        try:
            if not size:
                return "0B"
            units = ('B', 'KB', 'MB', 'GB', 'TB')
            i = math.floor(math.log(size, 1024))
            size = size / math.pow(1024, i)
            return f"{size:.2f}{units[i]}"
        except:
            return "0B"

    @staticmethod
    def parse_size(size_str: str) -> Optional[int]:
        """Parse size string to bytes"""
        try:
            units = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
            number = float(''.join(filter(str.isdigit, size_str)))
            unit = ''.join(filter(str.isalpha, size_str.upper()))
            return int(number * units[unit])
        except:
            return None

class MediaInfo:
    def __init__(self, info_dict: Dict):
        self.info = info_dict

    def get_duration(self) -> Optional[float]:
        """Get media duration in seconds"""
        try:
            return float(self.info['format']['duration'])
        except:
            return None

    def get_size(self) -> Optional[int]:
        """Get file size in bytes"""
        try:
            return int(self.info['format']['size'])
        except:
            return None

    def get_video_codec(self) -> Optional[str]:
        """Get video codec"""
        try:
            for stream in self.info['streams']:
                if stream['codec_type'] == 'video':
                    return stream['codec_name']
        except:
            return None

    def get_audio_tracks(self) -> List[Dict]:
        """Get audio track information"""
        tracks = []
        try:
            for stream in self.info['streams']:
                if stream['codec_type'] == 'audio':
                    tracks.append({
                        'index': stream['index'],
                        'codec': stream['codec_name'],
                        'language': stream.get('tags', {}).get('language', 'unknown'),
                        'title': stream.get('tags', {}).get('title', f'Track {len(tracks)+1}')
                    })
        except Exception as e:
            logger.error(f"Error getting audio tracks: {e}")
        return tracks

    def format_info(self) -> str:
        """Format media information for display"""
        try:
            info_text = "**📊 Media Information**\n\n"
            
            # Format information
            if 'format' in self.info:
                fmt = self.info['format']
                info_text += "**General:**\n"
                info_text += f"Format: {fmt.get('format_name', 'N/A')}\n"
                info_text += f"Duration: {TimeFormatter.format_duration(float(fmt.get('duration', 0)))}\n"
                info_text += f"Size: {SizeFormatter.format_size(int(fmt.get('size', 0)))}\n"
                if 'bit_rate' in fmt:
                    info_text += f"Bitrate: {int(fmt['bit_rate'])/1000:.1f} kb/s\n"
                info_text += "\n"

            # Stream information
            if 'streams' in self.info:
                for stream in self.info['streams']:
                    codec_type = stream.get('codec_type', 'unknown')
                    
                    if codec_type == 'video':
                        info_text += "**Video:**\n"
                        info_text += f"Codec: {stream.get('codec_name', 'N/A')}\n"
                        info_text += f"Resolution: {stream.get('width', 'N/A')}x{stream.get('height', 'N/A')}\n"
                        if 'r_frame_rate' in stream:
                            fps = eval(stream['r_frame_rate'])
                            info_text += f"FPS: {fps:.2f}\n"
                        info_text += f"Pixel Format: {stream.get('pix_fmt', 'N/A')}\n"
                        info_text += "\n"
                    
                    elif codec_type == 'audio':
                        info_text += f"**Audio Track {stream.get('index')}:**\n"
                        info_text += f"Codec: {stream.get('codec_name', 'N/A')}\n"
                        info_text += f"Channels: {stream.get('channels', 'N/A')}\n"
                        info_text += f"Sample Rate: {stream.get('sample_rate', 'N/A')} Hz\n"
                        info_text += f"Language: {stream.get('tags', {}).get('language', 'N/A')}\n"
                        info_text += "\n"
                    
                    elif codec_type == 'subtitle':
                        info_text += f"**Subtitle Track {stream.get('index')}:**\n"
                        info_text += f"Codec: {stream.get('codec_name', 'N/A')}\n"
                        info_text += f"Language: {stream.get('tags', {}).get('language', 'N/A')}\n"
                        info_text += "\n"

            return info_text
            
        except Exception as e:
            logger.error(f"Error formatting media info: {e}")
            return "❌ Error getting media information"
