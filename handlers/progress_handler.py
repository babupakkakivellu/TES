import time
import math
import logging
from typing import Dict, Optional, Union
from pyrogram.types import Message
from datetime import datetime

logger = logging.getLogger(__name__)

class ProgressHandler:
    def __init__(self):
        self.start_time: float = time.time()
        self.last_update_time: float = 0
        self.last_text: str = ""
        self.update_interval: float = 1.0  # Update interval in seconds

    def reset(self):
        """Reset progress handler"""
        self.start_time = time.time()
        self.last_update_time = 0
        self.last_text = ""

    async def update_progress(
        self,
        current: int,
        total: int,
        message: Message,
        action: str,
        extra_info: Optional[Dict] = None
    ) -> None:
        """
        Update progress with detailed information
        
        Parameters:
            current (int): Current progress value
            total (int): Total value
            message (Message): Telegram message to update
            action (str): Current action description
            extra_info (Dict): Additional information to display
        """
        try:
            now = time.time()
            
            # Update only if enough time has passed
            if now - self.last_update_time < self.update_interval:
                return

            # Calculate progress metrics
            elapsed_time = now - self.start_time
            percentage = (current * 100) / total if total > 0 else 0
            speed = current / elapsed_time if elapsed_time > 0 else 0
            eta = (total - current) / speed if speed > 0 else 0

            # Create progress bar
            bar_length = 20
            filled_length = int(bar_length * current / total)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)

            # Format basic info
            progress_text = (
                f"**{action}**\n\n"
                f"{bar} {percentage:.1f}%\n\n"
                f"💾 Size: {self.format_size(current)} / {self.format_size(total)}\n"
                f"⚡ Speed: {self.format_size(speed)}/s\n"
                f"⏱ Elapsed: {self.format_time(elapsed_time)}\n"
                f"⏳ ETA: {self.format_time(eta)}"
            )

            # Add extra information if provided
            if extra_info:
                extra_text = "\n\n**Additional Info:**\n"
                for key, value in extra_info.items():
                    if value is not None:
                        extra_text += f"• {key}: {value}\n"
                progress_text += extra_text

            # Update message if text has changed
            if progress_text != self.last_text:
                await message.edit_text(progress_text)
                self.last_text = progress_text
                self.last_update_time = now

        except Exception as e:
            logger.error(f"Error updating progress: {e}")

    @staticmethod
    def format_size(size: Union[int, float]) -> str:
        """
        Format size in bytes to human readable format
        
        Parameters:
            size (Union[int, float]): Size in bytes
            
        Returns:
            str: Formatted size string
        """
        if not size:
            return "0B"
        
        units = ('B', 'KB', 'MB', 'GB', 'TB')
        i = math.floor(math.log(size, 1024))
        size = size / math.pow(1024, i)
        
        return f"{size:.2f}{units[i]}"

    @staticmethod
    def format_time(seconds: Union[int, float]) -> str:
        """
        Format seconds to HH:MM:SS
        
        Parameters:
            seconds (Union[int, float]): Time in seconds
            
        Returns:
            str: Formatted time string
        """
        if not seconds or seconds < 0:
            return "00:00:00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    async def handle_ffmpeg_progress(
        self,
        line: str,
        duration: float,
        message: Message,
        action: str
    ) -> None:
        """
        Handle FFmpeg progress output
        
        Parameters:
            line (str): FFmpeg output line
            duration (float): Total video duration
            message (Message): Telegram message to update
            action (str): Current action description
        """
        try:
            if "time=" in line:
                # Extract current time
                time_str = line.split("time=")[1].split()[0]
                current_time = sum(
                    float(x) * 60 ** i 
                    for i, x in enumerate(reversed(time_str.split(":")))
                )

                # Extract additional info
                fps = self.extract_value(line, "fps=")
                speed = self.extract_value(line, "speed=")
                bitrate = self.extract_value(line, "bitrate=")

                # Update progress
                await self.update_progress(
                    int(current_time),
                    int(duration),
                    message,
                    action,
                    {
                        "FPS": f"{fps:.1f}" if fps else None,
                        "Speed": f"{speed}x" if speed else None,
                        "Bitrate": bitrate
                    }
                )

        except Exception as e:
            logger.error(f"Error handling FFmpeg progress: {e}")

    @staticmethod
    def extract_value(line: str, key: str) -> Optional[float]:
        """
        Extract numeric value from FFmpeg output line
        
        Parameters:
            line (str): FFmpeg output line
            key (str): Key to search for
            
        Returns:
            Optional[float]: Extracted value or None
        """
        try:
            if key in line:
                value_str = line.split(key)[1].split()[0]
                if value_str.endswith('x'):  # For speed
                    return float(value_str[:-1])
                elif value_str.endswith('kbits/s'):  # For bitrate
                    return float(value_str[:-7])
                return float(value_str)
        except:
            return None
        return None

    def estimate_time(self, current: int, total: int) -> str:
        """
        Estimate remaining time based on current progress
        
        Parameters:
            current (int): Current progress value
            total (int): Total value
            
        Returns:
            str: Estimated time remaining
        """
        try:
            elapsed_time = time.time() - self.start_time
            speed = current / elapsed_time if elapsed_time > 0 else 0
            remaining = (total - current) / speed if speed > 0 else 0
            
            return self.format_time(remaining)
        except:
            return "--:--:--"
