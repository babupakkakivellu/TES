import asyncio
import json
import logging
import os
from typing import Dict, List, Optional, Tuple
from pyrogram.types import Message
from config import Config

logger = logging.getLogger(__name__)

class FFmpegProcessor:
    def __init__(self):
        self.config = Config()

    async def probe_video(self, file_path: str) -> Dict:
        """Get video information using FFprobe"""
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                file_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"FFprobe failed: {stderr.decode()}")
                
            return json.loads(stdout.decode())
            
        except Exception as e:
            logger.error(f"Error probing video: {e}")
            raise

    async def build_ffmpeg_command(
        self,
        input_path: str,
        output_path: str,
        options: Dict
    ) -> List[str]:
        """Build FFmpeg command with advanced options"""
        cmd = ["ffmpeg", "-i", input_path]

        # Video options
        if options.get('video', True):
            if options.get('resolution'):
                scale_params = self.config.RESOLUTION_PRESETS[options['resolution']]
                cmd.extend([
                    "-vf", (
                        f"scale={scale_params['width']}:{scale_params['height']}"
                        ":force_original_aspect_ratio=decrease,"
                        "pad=ceil(iw/2)*2:ceil(ih/2)*2"
                    )
                ])

            if options.get('codec'):
                cmd.extend(["-c:v", options['codec']])
                
                if options['codec'] == 'libx265':
                    preset = self.config.COMPRESSION_PRESETS[options.get('quality', 'medium')]
                    cmd.extend([
                        "-crf", str(preset['crf']),
                        "-preset", preset['preset'],
                        "-tune", preset['tune'],
                        "-x265-params", preset['x265-params']
                    ])
            else:
                cmd.extend(["-c:v", "copy"])
        else:
            cmd.extend(["-vn"])

        # Audio options
        if options.get('audio', True):
            if options.get('audio_codec'):
                cmd.extend(["-c:a", options['audio_codec']])
                if options.get('audio_bitrate'):
                    cmd.extend(["-b:a", options['audio_bitrate']])
            else:
                cmd.extend(["-c:a", "copy"])
        else:
            cmd.extend(["-an"])

        # Subtitle options
        if options.get('subtitles', True):
            cmd.extend(["-c:s", "copy"])
        else:
            cmd.extend(["-sn"])

        # Additional options
        if options.get('start_time'):
            cmd.extend(["-ss", str(options['start_time'])])
        if options.get('duration'):
            cmd.extend(["-t", str(options['duration'])])
        if options.get('faststart', True):
            cmd.extend(["-movflags", "+faststart"])

        # Output options
        cmd.extend(["-y", output_path])

        return cmd

    async def process_video(
        self,
        input_path: str,
        output_path: str,
        options: Dict,
        progress_callback: Optional[callable] = None,
        message: Optional[Message] = None
    ) -> bool:
        """Process video with FFmpeg"""
        try:
            cmd = await self.build_ffmpeg_command(input_path, output_path, options)
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            if progress_callback and message:
                # Get video duration
                probe_data = await self.probe_video(input_path)
                duration = float(probe_data['format']['duration'])

                while True:
                    line = await process.stderr.readline()
                    if not line:
                        break
                        
                    line_text = line.decode('utf-8')
                    if "time=" in line_text:
                        await progress_callback(line_text, duration, message)

            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"FFmpeg error: {stderr.decode()}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error processing video: {e}")
            return False

    async def extract_audio(
        self,
        input_path: str,
        output_path: str,
        track_index: int = 0,
        codec: str = 'aac',
        bitrate: str = '128k'
    ) -> bool:
        """Extract audio track from video"""
        try:
            cmd = [
                "ffmpeg",
                "-i", input_path,
                "-map", f"0:a:{track_index}",
                "-c:a", codec,
                "-b:a", bitrate,
                "-y",
                output_path
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            await process.communicate()
            return process.returncode == 0

        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            return False

    async def merge_videos(
        self,
        video_paths: List[str],
        output_path: str,
        progress_callback: Optional[callable] = None,
        message: Optional[Message] = None
    ) -> bool:
        """Merge multiple videos"""
        try:
            # Create concat file
            concat_file = os.path.join(
                self.config.TEMP_DIR,
                f"concat_{int(time.time())}.txt"
            )
            
            with open(concat_file, "w", encoding='utf-8') as f:
                for video in video_paths:
                    f.write(f"file '{video}'\n")

            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c", "copy",
                "-y",
                output_path
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            if progress_callback and message:
                # Calculate total duration
                total_duration = 0
                for video in video_paths:
                    probe_data = await self.probe_video(video)
                    total_duration += float(probe_data['format']['duration'])

                while True:
                    line = await process.stderr.readline()
                    if not line:
                        break
                    line_text = line.decode('utf-8')
                    if "time=" in line_text:
                        await progress_callback(line_text, total_duration, message)

            stdout, stderr = await process.communicate()
            
            # Cleanup concat file
            if os.path.exists(concat_file):
                os.remove(concat_file)

            if process.returncode != 0:
                logger.error(f"FFmpeg error: {stderr.decode()}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error merging videos: {e}")
            return False
