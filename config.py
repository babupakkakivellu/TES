

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()

class Config:
    # Bot Configuration
    API_ID = os.getenv('API_ID')
    API_HASH = os.getenv('API_HASH')
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Directory Settings
    BASE_DIR = Path(__file__).parent
    TEMP_DIR = BASE_DIR / "temp_downloads"
    THUMB_DIR = BASE_DIR / "thumbnails"
    
    # File Settings
    MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
    CHUNK_SIZE = 1024 * 1024  # 1MB chunks for downloads
    
    # Video Settings
    SUPPORTED_FORMATS = {
        'video': ['.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.m4v'],
        'audio': ['.mp3', '.m4a', '.aac', '.wav', '.flac', '.ogg'],
        'subtitle': ['.srt', '.ass', '.ssa']
    }
    
    # FFmpeg Settings
    COMPRESSION_PRESETS = {
        "high": {
            "crf": 18,
            "preset": "slow",
            "tune": "film",
            "x265-params": "bframes=8:psy-rd=1:aq-mode=3:aq-strength=0.8:deblock=1,1"
        },
        "medium": {
            "crf": 23,
            "preset": "medium",
            "tune": "film",
            "x265-params": "bframes=6:psy-rd=1:aq-mode=3:aq-strength=0.9:deblock=1,1"
        },
        "low": {
            "crf": 28,
            "preset": "fast",
            "tune": "film",
            "x265-params": "bframes=4:psy-rd=1:aq-mode=3:aq-strength=1:deblock=1,1"
        }
    }
    
    RESOLUTION_PRESETS = {
        "2160p": {"width": 3840, "height": 2160},
        "1080p": {"width": 1920, "height": 1080},
        "720p": {"width": 1280, "height": 720},
        "480p": {"width": 854, "height": 480},
        "360p": {"width": 640, "height": 360}
    }
    
    # Progress Update Settings
    PROGRESS_UPDATE_DELAY = 1  # seconds
