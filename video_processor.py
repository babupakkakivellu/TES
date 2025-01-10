# video_processor.py
import asyncio
import os
from typing import Dict, List, Optional, Callable
from pyrogram.types import Message
from utils import get_mediainfo, create_progress_bar, format_bytes

class VideoProcessor:
    def __init__(self, temp_dir: str):
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)

    async def process_with_progress(
        self,
        cmd: List[str],
        message: Message,
        status_text: str = "Processing"
    ) -> bool:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        progress_msg = await message.reply_text(f"{status_text}: 0%")
        
        while True:
            if process.stderr:
                line = await process.stderr.readline()
                if not line:
                    break
                if b"time=" in line:
                    try:
                        time_str = line.decode().split("time=")[1].split()[0]
                        current_time = sum(float(x) * 60 ** i for i, x in 
                                        enumerate(reversed(time_str.split(":"))))
                        progress = min(100, int(current_time))
                        progress_bar = await create_progress_bar(progress, 100)
                        await progress_msg.edit_text(
                            f"{status_text}...\n{progress_bar}"
                        )
                    except:
                        pass
        
        await process.wait()
        await progress_msg.delete()
        return process.returncode == 0

    async def remove_audio_streams(
        self,
        input_path: str,
        output_path: str,
        streams_to_remove: List[int],
        message: Message
    ) -> bool:
        cmd = ["ffmpeg", "-i", input_path]
        
        info = await get_mediainfo(input_path)
        for stream in info["streams"]:
            index = stream["index"]
            if stream["codec_type"] == "audio" and index in streams_to_remove:
                continue
            cmd.extend(["-map", f"0:{index}"])
        
        cmd.extend(["-c", "copy", output_path])
        
        return await self.process_with_progress(
            cmd, message, "Removing audio streams"
        )

    async def reorder_tracks(
        self,
        input_path: str,
        output_path: str,
        track_order: List[int],
        message: Message
    ) -> bool:
        cmd = ["ffmpeg", "-i", input_path]
        
        # Map video stream first
        cmd.extend(["-map", "0:v:0"])
        
        # Map audio streams in specified order
        for track in track_order:
            cmd.extend(["-map", f"0:a:{track}"])
        
        # Map subtitle streams
        cmd.extend(["-map", "0:s?"])
        
        cmd.extend(["-c", "copy", output_path])
        
        return await self.process_with_progress(
            cmd, message, "Reordering tracks"
        )

    async def merge_videos(
        self,
        video_paths: List[str],
        output_path: str,
        message: Message
    ) -> bool:
        concat_file = os.path.join(self.temp_dir, "concat.txt")
        with open(concat_file, "w") as f:
            for video in video_paths:
                f.write(f"file '{video}'\n")
        
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            output_path
        ]
        
        success = await self.process_with_progress(
            cmd, message, "Merging videos"
        )
        
        os.remove(concat_file)
        return success

    async def compress_video(
        self,
        input_path: str,
        output_path: str,
        resolution: str,
        crf: int,
        message: Message
    ) -> bool:
        scale_params = {
            "1080p": "1920:1080",
            "720p": "1280:720",
            "480p": "854:480"
        }
        
        cmd = [
            "ffmpeg", "-i", input_path,
            "-vf", f"scale={scale_params[resolution]}",
            "-c:v", "libx265",
            "-crf", str(crf),
            "-preset", "medium",
            "-c:a", "copy",
            "-c:s", "copy",
            output_path
        ]
        
        return await self.process_with_progress(
            cmd, message, "Compressing video"
        )
