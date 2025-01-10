import logging
import os
import time
from typing import Dict, List, Optional
from pyrogram.types import Message
from .ffmpeg_processor import FFmpegProcessor
from .file_manager import FileManager
from config import Config

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        self.config = Config()
        self.ffmpeg = FFmpegProcessor()
        self.file_manager = FileManager()

    async def process_video(
        self,
        input_path: str,
        options: Dict,
        message: Message
    ) -> Optional[str]:
        """Process video with given options"""
        try:
            # Generate output path
            output_path = await self.file_manager.create_temp_file(
                prefix="processed_",
                suffix=os.path.splitext(input_path)[1]
            )

            # Check disk space
            input_size = os.path.getsize(input_path)
            if not await self.file_manager.ensure_space_available(input_size * 2):
                await message.edit_text("❌ Not enough disk space available!")
                return None

            # Process video
            success = await self.ffmpeg.process_video(
                input_path,
                output_path,
                options,
                self.handle_progress,
                message
            )

            if success:
                return output_path
            return None

        except Exception as e:
            logger.error(f"Error processing video: {e}")
            await message.edit_text("❌ Error processing video!")
            return None

    async def compress_video(
        self,
        input_path: str,
        settings: Dict,
        message: Message
    ) -> Optional[str]:
        """Compress video with specified settings"""
        try:
            options = {
                'video': True,
                'audio': True,
                'codec': 'libx265',
                'resolution': settings['resolution'],
                'quality': settings['quality'],
                'faststart': True
            }

            return await self.process_video(input_path, options, message)

        except Exception as e:
            logger.error(f"Error compressing video: {e}")
            await message.edit_text("❌ Error compressing video!")
            return None

    async def extract_audio(
        self,
        input_path: str,
        track_indices: List[int],
        message: Message
    ) -> List[str]:
        """Extract audio tracks from video"""
        try:
            output_files = []
            for index in track_indices:
                output_path = await self.file_manager.create_temp_file(
                    prefix=f"audio_{index}_",
                    suffix=".m4a"
                )
                
                success = await self.ffmpeg.extract_audio(
                    input_path,
                    output_path,
                    track_index=index
                )
                
                if success:
                    output_files.append(output_path)

            return output_files

        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            await message.edit_text("❌ Error extracting audio!")
            return []

    async def merge_videos(
        self,
        video_paths: List[str],
        message: Message
    ) -> Optional[str]:
        """Merge multiple videos"""
        try:
            output_path = await self.file_manager.create_temp_file(
                prefix="merged_",
                suffix=".mp4"
            )

            success = await self.ffmpeg.merge_videos(
                video_paths,
                output_path,
                self.handle_progress,
                message
            )

            if success:
                return output_path
            return None

        except Exception as e:
            logger.error(f"Error merging videos: {e}")
            await message.edit_text("❌ Error merging videos!")
            return None

    async def handle_progress(self, line: str, duration: float, message: Message):
        """Handle FFmpeg progress output"""
        try:
            if "time=" in line:
                # Extract current time
                time_str = line.split("time=")[1].split()[0]
                current_time = sum(
                    float(x) * 60 ** i 
                    for i, x in enumerate(reversed(time_str.split(":")))
                )
                
                # Calculate progress percentage
                progress = min(100, int((current_time / duration) * 100))
                
                # Extract additional info
                fps = self.extract_value(line, "fps=")
                speed = self.extract_value(line, "speed=")
                size = self.extract_value(line, "size=")
                
                # Update progress message
                await message.edit_text(
                    f"**🔄 Processing Video**\n\n"
                    f"Progress: {progress}%\n"
                    f"FPS: {fps:.1f}\n"
                    f"Speed: {speed}x\n"
                    f"Size: {self.file_manager.format_size(size)}\n"
                    f"⏳ Please wait..."
                )

        except Exception as e:
            logger.error(f"Error handling progress: {e}")

    @staticmethod
    def extract_value(line: str, key: str) -> Optional[float]:
        """Extract numeric value from FFmpeg output"""
        try:
            if key in line:
                value_str = line.split(key)[1].split()[0]
                if value_str.endswith('x'):
                    return float(value_str[:-1])
                elif value_str.endswith('kbits/s'):
                    return float(value_str[:-7])
                return float(value_str)
        except:
            return None
