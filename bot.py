from pyrogram import Client, filters, idle
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
            elif data == "cancel":
                await callback.message.delete()
            # Add other handlers...

        await self.app.start()
        print("Bot is running...")
        await idle()  # Use the imported idle function
