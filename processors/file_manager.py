import os
import time
import shutil
import logging
import asyncio
from typing import Optional, List
from datetime import datetime
from pathlib import Path
from config import Config

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self):
        self.config = Config()
        self.create_directories()

    def create_directories(self):
        """Create necessary directories"""
        try:
            os.makedirs(self.config.TEMP_DIR, exist_ok=True)
            os.makedirs(self.config.THUMB_DIR, exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating directories: {e}")
            raise

    async def save_file(self, file_path: str, data: bytes) -> bool:
        """Save file to disk"""
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(data)
            return True
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return False

    async def cleanup_old_files(self, max_age: int = 3600):
        """Clean up files older than max_age seconds"""
        try:
            current_time = time.time()
            
            # Cleanup temp directory
            for file_path in Path(self.config.TEMP_DIR).glob('*'):
                if current_time - file_path.stat().st_mtime > max_age:
                    try:
                        if file_path.is_file():
                            file_path.unlink()
                        elif file_path.is_dir():
                            shutil.rmtree(file_path)
                    except Exception as e:
                        logger.error(f"Error removing {file_path}: {e}")

            # Cleanup thumbnails
            for file_path in Path(self.config.THUMB_DIR).glob('*'):
                if current_time - file_path.stat().st_mtime > max_age:
                    try:
                        file_path.unlink()
                    except Exception as e:
                        logger.error(f"Error removing thumbnail {file_path}: {e}")

        except Exception as e:
            logger.error(f"Error cleaning up files: {e}")

    async def generate_thumbnail(
        self,
        video_path: str,
        time_offset: int = 1,
        size: tuple = (320, 320)
    ) -> Optional[str]:
        """Generate thumbnail from video"""
        try:
            thumb_path = os.path.join(
                self.config.THUMB_DIR,
                f"thumb_{int(time.time())}.jpg"
            )
            
            cmd = [
                "ffmpeg",
                "-ss", str(time_offset),
                "-i", video_path,
                "-vframes", "1",
                "-vf", f"scale={size[0]}:{size[1]}:force_original_aspect_ratio=decrease",
                "-y",
                thumb_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            if os.path.exists(thumb_path):
                return thumb_path
            return None

        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            return None

    async def ensure_space_available(self, required_size: int) -> bool:
        """Check if enough space is available"""
        try:
            total, used, free = shutil.disk_usage(self.config.TEMP_DIR)
            return free > required_size * 1.5  # 50% buffer
        except Exception as e:
            logger.error(f"Error checking disk space: {e}")
            return False

    async def get_file_info(self, file_path: str) -> dict:
        """Get file information"""
        try:
            stat = os.stat(file_path)
            return {
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'extension': os.path.splitext(file_path)[1].lower()
            }
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {}

    async def create_temp_file(self, prefix: str = "", suffix: str = "") -> str:
        """Create a temporary file path"""
        return os.path.join(
            self.config.TEMP_DIR,
            f"{prefix}{int(time.time())}{suffix}"
        )

    async def cleanup_user_files(self, user_id: int):
        """Clean up user's temporary files"""
        try:
            pattern = f"*{user_id}*"
            for file_path in Path(self.config.TEMP_DIR).glob(pattern):
                try:
                    if file_path.is_file():
                        file_path.unlink()
                    elif file_path.is_dir():
                        shutil.rmtree(file_path)
                except Exception as e:
                    logger.error(f"Error removing {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error cleaning up user files: {e}")

    @staticmethod
    def format_size(size: int) -> str:
        """Format size to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f}{unit}"
            size /= 1024
        return f"{size:.2f}TB"
