import os
import time
import asyncio
import logging
from pyrogram import Client, filters, idle
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from processors.video_processor import VideoProcessor
from processors.file_manager import FileManager
from utils.keyboard import Keyboard
from utils.helpers import TimeFormatter, SizeFormatter, MediaInfo
from config import Config

logger = logging.getLogger(__name__)

class VideoBot:
    def __init__(self):
        self.config = Config()
        self.app = Client(
            name="video_processor_bot",
            api_id=self.config.API_ID,
            api_hash=self.config.API_HASH,
            bot_token=self.config.BOT_TOKEN,
            in_memory=True
        )
        self.video_processor = VideoProcessor()
        self.file_manager = FileManager()
        self.keyboard = Keyboard()
        self.user_data = {}

    async def start(self):
        """Start the bot and register handlers"""
        try:
            # Register handlers
            self.register_handlers()
            
            # Start the bot
            logger.info("Starting bot...")
            await self.app.start()
            logger.info("Bot started successfully!")
            
            # Keep the bot running
            await idle()

        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise

        finally:
            if self.app.is_connected:
                await self.app.stop()

    def register_handlers(self):
        """Register message and callback handlers"""
        @self.app.on_message(filters.command("start"))
        async def start_command(_, message: Message):
            await message.reply_text(
                "**👋 Welcome to Video Processor Bot!**\n\n"
                "I can help you with:\n"
                "• Compress videos\n"
                "• Extract/Remove audio tracks\n"
                "• Merge multiple videos\n"
                "• Convert video formats\n"
                "• Extract subtitles\n"
                "• View detailed MediaInfo\n\n"
                "Send me any video to get started!"
            )

        @self.app.on_message(filters.video | filters.document)
        async def handle_video(_, message: Message):
            await self.handle_video_message(message)

        @self.app.on_callback_query()
        async def handle_callback(_, callback: CallbackQuery):
            await self.handle_callback_query(callback)

    async def handle_video_message(self, message: Message):
        """Handle incoming video messages"""
        try:
            # Show processing message
            progress_msg = await message.reply_text(
                "**⏳ Processing Video**\n\n"
                "Please wait while I analyze your file..."
            )

            # Validate file
            file_name = message.video.file_name if message.video else message.document.file_name
            if not any(file_name.lower().endswith(ext) for ext in self.config.SUPPORTED_FORMATS['video']):
                await progress_msg.edit_text(
                    "❌ Invalid file format!\n"
                    "Please send a valid video file."
                )
                return

            # Check file size
            file_size = message.video.file_size if message.video else message.document.file_size
            if file_size > self.config.MAX_FILE_SIZE:
                await progress_msg.edit_text(
                    "❌ File too large!\n"
                    f"Maximum file size: {SizeFormatter.format_size(self.config.MAX_FILE_SIZE)}"
                )
                return

            # Download the file
            file_id = message.video.file_id if message.video else message.document.file_id
            file_path = os.path.join(
                self.config.TEMP_DIR,
                f"video_{message.from_user.id}_{int(time.time())}{os.path.splitext(file_name)[1]}"
            )

            try:
                await message.download(file_path)
            except Exception as e:
                logger.error(f"Error downloading file: {e}")
                await progress_msg.edit_text(
                    "❌ Error downloading file!\n"
                    "Please try again."
                )
                return

            # Store file info
            user_id = message.from_user.id
            self.user_data[user_id] = {
                'file_id': file_id,
                'file_name': file_name,
                'file_size': file_size,
                'file_path': file_path,
                'message_id': message.id,
                'progress_msg_id': progress_msg.id
            }

            # Show main menu
            await progress_msg.edit_text(
                "**🎥 Video Processor**\n\n"
                f"File: `{file_name}`\n"
                f"Size: {SizeFormatter.format_size(file_size)}\n\n"
                "Select an operation:",
                reply_markup=self.keyboard.get_main_keyboard()
            )

        except Exception as e:
            logger.error(f"Error handling video message: {e}")
            await message.reply_text(
                "❌ Error processing video!\n"
                "Please try again or contact support."
            )

    async def handle_callback_query(self, callback: CallbackQuery):
        """Handle callback queries"""
        try:
            data = callback.data
            user_id = callback.from_user.id

            # Check session validity
            if user_id not in self.user_data and data != "cancel":
                await callback.answer(
                    "⚠️ Session expired. Please send the video again.",
                    show_alert=True
                )
                return

            # Handle different callbacks
            if data == "cancel":
                await self.handle_cancel(callback, user_id)
            elif data == "compress_menu":
                await self.show_compression_menu(callback)
            elif data.startswith("compress_"):
                await self.handle_compression_callback(callback)
            elif data == "audio_menu":
                await self.show_audio_menu(callback)
            elif data.startswith("audio_"):
                await self.handle_audio_callback(callback)
            elif data == "merge_menu":
                await self.show_merge_menu(callback)
            elif data.startswith("merge_"):
                await self.handle_merge_callback(callback)
            elif data == "mediainfo":
                await self.show_mediainfo(callback)
            elif data == "main_menu":
                await self.show_main_menu(callback)
            else:
                await callback.answer("🚧 Feature under development")

        except Exception as e:
            logger.error(f"Error handling callback: {e}")
            await callback.answer(
                "❌ An error occurred. Please try again.",
                show_alert=True
            )

    async def show_main_menu(self, callback: CallbackQuery):
        """Show main menu"""
        try:
            user_id = callback.from_user.id
            file_info = self.user_data[user_id]
            
            await callback.message.edit_text(
                "**🎥 Video Processor**\n\n"
                f"File: `{file_info['file_name']}`\n"
                f"Size: {SizeFormatter.format_size(file_info['file_size'])}\n\n"
                "Select an operation:",
                reply_markup=self.keyboard.get_main_keyboard()
            )
        except Exception as e:
            logger.error(f"Error showing main menu: {e}")
            await callback.answer(
                "❌ Error showing menu.",
                show_alert=True
            )

    async def handle_cancel(self, callback: CallbackQuery, user_id: int):
        """Handle cancel button"""
        try:
            # Cleanup user data and files
            if user_id in self.user_data:
                file_path = self.user_data[user_id].get('file_path')
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                del self.user_data[user_id]
            
            # Delete message
            await callback.message.delete()
            
        except Exception as e:
            logger.error(f"Error handling cancel: {e}")

    async def show_mediainfo(self, callback: CallbackQuery):
        """Show media information"""
        try:
            user_id = callback.from_user.id
            file_path = self.user_data[user_id].get('file_path')
            
            if not file_path or not os.path.exists(file_path):
                await callback.answer(
                    "⚠️ File not found. Please send the video again.",
                    show_alert=True
                )
                return

            # Get media info
            info = await self.video_processor.ffmpeg.probe_video(file_path)
            media_info = MediaInfo(info)
            
            # Show info with back button
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back", callback_data="main_menu")
            ]])
            
            await callback.message.edit_text(
                media_info.format_info(),
                reply_markup=keyboard
            )

        except Exception as e:
            logger.error(f"Error showing mediainfo: {e}")
            await callback.answer(
                "❌ Error getting media information.",
                show_alert=True
            )

    # ... [Previous compression, audio, and merge methods remain the same]

    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Cleanup all user files
            for user_id in self.user_data:
                file_path = self.user_data[user_id].get('file_path')
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
            
            # Clear user data
            self.user_data.clear()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
