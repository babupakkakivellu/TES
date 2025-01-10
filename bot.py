from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ForceReply
from video_processor import VideoProcessor
import os
from typing import Dict

class VideoBot:
    def __init__(self, api_id: str, api_hash: str, bot_token: str, temp_dir: str):
        self.app = Client("video_processor_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
        self.processor = VideoProcessor(temp_dir)
        self.temp_dir = temp_dir
        self.user_data: Dict[int, dict] = {}

    async def handle_compress_click(self, callback: CallbackQuery):
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("1080p", callback_data="compress_1080"),
                InlineKeyboardButton("720p", callback_data="compress_720"),
                InlineKeyboardButton("480p", callback_data="compress_480")
            ],
            [
                InlineKeyboardButton("CRF: 18 (High)", callback_data="crf_18"),
                InlineKeyboardButton("CRF: 24 (Medium)", callback_data="crf_24"),
                InlineKeyboardButton("CRF: 28 (Low)", callback_data="crf_28")
            ],
            [InlineKeyboardButton("Custom CRF (16-35)", callback_data="crf_custom")],
            [InlineKeyboardButton("✅ Start Compression", callback_data="compress_start")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ])

        user_id = callback.from_user.id
        settings = self.user_data.get(user_id, {}).get('compress_settings', {
            'resolution': None,
            'crf': 24
        })

        await callback.message.edit_text(
            "**🎯 Compression Settings**\n\n"
            f"Resolution: {settings.get('resolution', 'Not Set')}\n"
            f"CRF Value: {settings.get('crf', 'Not Set')}\n\n"
            "Select your compression settings:",
            reply_markup=keyboard
        )

    async def start(self):
        @self.app.on_message(filters.command("start"))
        async def start_command(_, message: Message):
            await message.reply_text(
                "Welcome! Send me a video to process."
            )

        @self.app.on_message(filters.video | filters.document)
        async def handle_video(_, message: Message):
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔊 Remove Audio", callback_data="remove_audio"),
                    InlineKeyboardButton("🔄 Reorder Tracks", callback_data="reorder_tracks")
                ],
                [
                    InlineKeyboardButton("🔗 Merge Videos", callback_data="merge"),
                    InlineKeyboardButton("📝 Metadata", callback_data="metadata")
                ],
                [
                    InlineKeyboardButton("🎯 Compress", callback_data="compress"),
                    InlineKeyboardButton("ℹ️ MediaInfo", callback_data="mediainfo")
                ],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ])
            
            await message.reply_text(
                "Select an operation:",
                reply_markup=keyboard
            )

        @self.app.on_callback_query()
        async def callback_handler(_, callback: CallbackQuery):
            data = callback.data
            
            if data == "compress":
                await self.handle_compress_click(callback)
            elif data.startswith(("compress_", "crf_")):
                await self.handle_compress_callback(callback)
            # Add other handlers...

        await self.app.start()
        print("Bot is running...")
        await self.app.idle()

    async def handle_compress_callback(self, callback: CallbackQuery):
        user_id = callback.from_user.id
        data = callback.data
        
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        if 'compress_settings' not in self.user_data[user_id]:
            self.user_data[user_id]['compress_settings'] = {
                'resolution': None,
                'crf': 24
            }

        settings = self.user_data[user_id]['compress_settings']

        if data.startswith('compress_'):
            resolution = data.split('_')[1]
            if resolution in ['1080', '720', '480']:
                settings['resolution'] = f"{resolution}p"
                await self.update_compress_menu(callback.message, settings)
        
        elif data.startswith('crf_'):
            crf_value = data.split('_')[1]
            if crf_value == 'custom':
                await callback.message.reply_text(
                    "Please enter a CRF value (16-35):",
                    reply_markup=ForceReply()
                )
            else:
                settings['crf'] = int(crf_value)
                await self.update_compress_menu(callback.message, settings)
