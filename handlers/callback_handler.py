from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup
from utils.keyboard import Keyboard
from processors.video_processor import VideoProcessor
from processors.file_manager import FileManager
import logging

logger = logging.getLogger(__name__)

class CallbackHandler:
    def __init__(self, bot):
        self.bot = bot
        self.video_processor = VideoProcessor()
        self.file_manager = FileManager()
        self.keyboard = Keyboard()

    async def handle_callback(self, callback: CallbackQuery):
        """Main callback handler"""
        try:
            data = callback.data
            user_id = callback.from_user.id

            # Check session validity
            if user_id not in self.bot.user_data and data != "cancel":
                await callback.answer(
                    "⚠️ Session expired. Please send the video again.",
                    show_alert=True
                )
                return

            # Handle different callbacks
            if data == "cancel":
                await self.handle_cancel(callback, user_id)
            elif data == "compress":
                await self.handle_compress_menu(callback)
            elif data.startswith("compress_"):
                await self.handle_compression_callback(callback)
            elif data == "merge":
                await self.handle_merge_menu(callback)
            elif data.startswith("merge_"):
                await self.handle_merge_callback(callback)
            elif data == "audio":
                await self.handle_audio_menu(callback)
            elif data.startswith("audio_"):
                await self.handle_audio_callback(callback)
            elif data == "mediainfo":
                await self.handle_mediainfo(callback)
            else:
                await callback.answer("🚧 Feature under development")

        except Exception as e:
            logger.error(f"Error handling callback: {e}")
            await self.handle_error(callback)

    async def handle_compress_menu(self, callback: CallbackQuery):
        """Show compression options menu"""
        try:
            user_id = callback.from_user.id
            if 'compress_settings' not in self.bot.user_data[user_id]:
                self.bot.user_data[user_id]['compress_settings'] = {
                    'resolution': None,
                    'quality': None,
                    'crf': None,
                    'preset': None
                }

            keyboard = self.keyboard.get_compression_keyboard(
                self.bot.user_data[user_id]['compress_settings']
            )

            await callback.message.edit_text(
                "**🎯 Compression Settings**\n\n"
                "Select your preferred settings:",
                reply_markup=keyboard
            )

        except Exception as e:
            logger.error(f"Error showing compression menu: {e}")
            await self.handle_error(callback)

    async def handle_compression_callback(self, callback: CallbackQuery):
        """Handle compression-related callbacks"""
        try:
            data = callback.data
            user_id = callback.from_user.id
            settings = self.bot.user_data[user_id]['compress_settings']

            if data.startswith("res_"):
                resolution = data.split("_")[1]
                settings['resolution'] = resolution
            elif data.startswith("quality_"):
                quality = data.split("_")[1]
                settings['quality'] = quality
                # Set corresponding CRF and preset
                preset = self.bot.config.COMPRESSION_PRESETS[quality]
                settings['crf'] = preset['crf']
                settings['preset'] = preset['preset']
            elif data == "compress_start":
                if not settings.get('resolution') or not settings.get('quality'):
                    await callback.answer(
                        "⚠️ Please select both resolution and quality!",
                        show_alert=True
                    )
                    return
                await self.start_compression(callback)
                return

            # Update menu
            keyboard = self.keyboard.get_compression_keyboard(settings)
            await callback.message.edit_text(
                "**🎯 Compression Settings**\n\n"
                f"Resolution: {settings.get('resolution', 'Not Set')}\n"
                f"Quality: {settings.get('quality', 'Not Set')}\n"
                f"CRF: {settings.get('crf', 'Auto')}\n"
                f"Preset: {settings.get('preset', 'Auto')}\n\n"
                "Select your settings:",
                reply_markup=keyboard
            )

        except Exception as e:
            logger.error(f"Error handling compression callback: {e}")
            await self.handle_error(callback)

    async def start_compression(self, callback: CallbackQuery):
        """Start video compression process"""
        try:
            user_id = callback.from_user.id
            settings = self.bot.user_data[user_id]['compress_settings']
            
            await callback.message.edit_text(
                "**🔄 Starting Compression**\n\n"
                "⏳ Please wait while I process your video..."
            )

            # Process video
            success = await self.video_processor.compress_video(
                self.bot.user_data[user_id]['file_path'],
                settings,
                callback.message
            )

            if success:
                await callback.message.edit_text(
                    "✅ Video compressed successfully!"
                )
            else:
                await callback.message.edit_text(
                    "❌ Compression failed. Please try again."
                )

        except Exception as e:
            logger.error(f"Error starting compression: {e}")
            await self.handle_error(callback)

    async def handle_error(self, callback: CallbackQuery):
        """Handle errors in callback processing"""
        try:
            await callback.answer(
                "❌ An error occurred. Please try again.",
                show_alert=True
            )
        except:
            pass

    async def handle_cancel(self, callback: CallbackQuery, user_id: int):
        """Handle cancel button"""
        try:
            # Cleanup user data
            await self.file_manager.cleanup_user_files(user_id)
            if user_id in self.bot.user_data:
                del self.bot.user_data[user_id]
            
            # Delete message
            await callback.message.delete()
            
        except Exception as e:
            logger.error(f"Error handling cancel: {e}")
