
import os
import asyncio
import json
from typing import Dict, List, Optional, Union
from pyrogram.types import Message

async def get_mediainfo(file_path: str) -> dict:
    cmd = [
        "ffprobe", "-v", "quiet",
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
    stdout, _ = await process.communicate()
    return json.loads(stdout)

async def format_mediainfo(info: dict) -> str:
    formatted = "📊 **MediaInfo**\n\n"
    
    if "format" in info:
        fmt = info["format"]
        formatted += "**General**\n"
        formatted += f"Format: {fmt.get('format_name', 'N/A')}\n"
        formatted += f"Duration: {float(fmt.get('duration', 0)):.2f}s\n"
        formatted += f"Size: {int(fmt.get('size', 0)) / 1024 / 1024:.2f} MB\n\n"
    
    if "streams" in info:
        for stream in info["streams"]:
            codec_type = stream.get("codec_type", "unknown")
            if codec_type == "video":
                formatted += "**Video**\n"
                formatted += f"Codec: {stream.get('codec_name', 'N/A')}\n"
                formatted += f"Resolution: {stream.get('width', 'N/A')}x{stream.get('height', 'N/A')}\n"
                formatted += f"FPS: {stream.get('r_frame_rate', 'N/A')}\n\n"
            elif codec_type == "audio":
                formatted += f"**Audio Track {stream.get('index')}**\n"
                formatted += f"Codec: {stream.get('codec_name', 'N/A')}\n"
                formatted += f"Channels: {stream.get('channels', 'N/A')}\n"
                formatted += f"Language: {stream.get('tags', {}).get('language', 'N/A')}\n"
                formatted += f"Title: {stream.get('tags', {}).get('title', 'N/A')}\n\n"
            elif codec_type == "subtitle":
                formatted += f"**Subtitle Track {stream.get('index')}**\n"
                formatted += f"Codec: {stream.get('codec_name', 'N/A')}\n"
                formatted += f"Language: {stream.get('tags', {}).get('language', 'N/A')}\n\n"
    
    return formatted

async def create_progress_bar(current: int, total: int) -> str:
    percentage = current * 100 // total
    filled = int(percentage / 10)
    bar = "█" * filled + "░" * (10 - filled)
    return f"[{bar}] {percentage}%"

async def format_bytes(size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

def clean_filename(filename: str) -> str:
    return "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
