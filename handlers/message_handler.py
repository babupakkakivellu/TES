from pyrogram.types import Message
from utils.keyboard import Keyboard
from processors.file_manager import FileManager
import logging

logger = logging.getLogger(__name__)

class MessageHandler:
    def __init__(self, bot):
        self.bot = bot
        self.keyboard = Keyboard()
        self.file_manager = FileManager()

    async def handle_video_message(self, message: Message):
        """Handle incoming video messages"""
        try:
            # Show processing message
            progress_msg = await message.reply_text(
                "**⏳ Processing Video**\n\n"
                "Please wait while I analyze your file..."
            )

            # Validate file
            if not await self.validate_video(message):
                await progress_msg.edit_text(
                    "❌ Invalid file!\n\n"
                    "Please send a valid video file."
                )
                return

            # Store file info
            user_id = message.from_user.id
            self.bot.user_data[user_id] = {
                'file_id': message.video.file_id if message.video else message.document.file_id,
                'file_name': message.video.file_name if message.video else message.document.file_name,
                'file_size': message.video.file_size if message.video else message.document.file_size,
                'message_id': message.id,
                'progress_msg_id': progress_msg.id
            }

            # Show main menu
            keyboard = self.keyboard.get_main_keyboard()
            await progress_msg.edit_text(
                "**🎥 Video Processor**\n\n"
                f"File: `{self.bot.user_data[user_id]['file_name']}`\n"
                f"Size: {await self.file_manager.format_size(self.bot.user_data[user_id]['file_size'])}\n\n"
                "Select an operation:",
                reply_markup=keyboard
            )

        except Exception as e:
            logger.error(f"Error handling video message: {e}")
            await message.reply_text(
                "❌ Error processing video!\n"
                "Please try again or contact support."
            )

    async def validate_video(self, message: Message) -> bool:
        """Validate video file"""
        try:
            # Check file type
            file_name = message.video.file_name if message.video else message.document.file_name
            if not any(file_name.lower().endswith(ext) for ext in self.bot.config.SUPPORTED_FORMATS['video']):
                return False

            # Check file size
            file_size = message.video.file_size if message.video else message.document.file_size
            if file_size > self.bot.config.MAX_FILE_SIZE:
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating video: {e}")
            return False
