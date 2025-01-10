from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, List, Optional

class Keyboard:
    @staticmethod
    def get_main_keyboard() -> InlineKeyboardMarkup:
        """Get main menu keyboard"""
        buttons = [
            [
                InlineKeyboardButton("🔊 Audio", callback_data="audio_menu"),
                InlineKeyboardButton("🔄 Convert", callback_data="convert_menu")
            ],
            [
                InlineKeyboardButton("🔗 Merge", callback_data="merge_menu"),
                InlineKeyboardButton("✂️ Cut", callback_data="cut_menu")
            ],
            [
                InlineKeyboardButton("🎯 Compress", callback_data="compress_menu"),
                InlineKeyboardButton("📝 Subtitle", callback_data="subtitle_menu")
            ],
            [
                InlineKeyboardButton("ℹ️ MediaInfo", callback_data="mediainfo"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel")
            ]
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def get_compression_keyboard(settings: Dict) -> InlineKeyboardMarkup:
        """Get compression settings keyboard"""
        buttons = [
            [
                InlineKeyboardButton(
                    "2160p (4K) ✓" if settings.get('resolution') == '2160p' else "2160p (4K)",
                    callback_data="res_2160"
                ),
                InlineKeyboardButton(
                    "1080p (FHD) ✓" if settings.get('resolution') == '1080p' else "1080p (FHD)",
                    callback_data="res_1080"
                )
            ],
            [
                InlineKeyboardButton(
                    "720p (HD) ✓" if settings.get('resolution') == '720p' else "720p (HD)",
                    callback_data="res_720"
                ),
                InlineKeyboardButton(
                    "480p (SD) ✓" if settings.get('resolution') == '480p' else "480p (SD)",
                    callback_data="res_480"
                )
            ],
            [
                InlineKeyboardButton(
                    "High Quality ✓" if settings.get('quality') == 'high' else "High Quality",
                    callback_data="quality_high"
                ),
                InlineKeyboardButton(
                    "Medium Quality ✓" if settings.get('quality') == 'medium' else "Medium Quality",
                    callback_data="quality_medium"
                ),
                InlineKeyboardButton(
                    "Low Quality ✓" if settings.get('quality') == 'low' else "Low Quality",
                    callback_data="quality_low"
                )
            ],
            [
                InlineKeyboardButton("⚙️ Custom Settings", callback_data="compress_custom")
            ],
            [
                InlineKeyboardButton("✅ Start Compression", callback_data="compress_start"),
                InlineKeyboardButton("⬅️ Back", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def get_audio_keyboard(tracks: List[Dict], selected: List[int]) -> InlineKeyboardMarkup:
        """Get audio tracks keyboard"""
        buttons = []
        
        # Add buttons for each audio track
        for track in tracks:
            track_index = track['index']
            is_selected = track_index in selected
            buttons.append([
                InlineKeyboardButton(
                    f"{'✅' if is_selected else '☐'} {track['title']} ({track['language']})",
                    callback_data=f"audio_select_{track_index}"
                )
            ])

        # Add control buttons
        buttons.extend([
            [
                InlineKeyboardButton("📤 Extract Selected", callback_data="audio_extract"),
                InlineKeyboardButton("🗑 Remove Selected", callback_data="audio_remove")
            ],
            [
                InlineKeyboardButton("✅ Process", callback_data="audio_process"),
                InlineKeyboardButton("⬅️ Back", callback_data="main_menu")
            ]
        ])

        return InlineKeyboardMarkup(buttons)
