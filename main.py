import asyncio
import logging
from pathlib import Path
from bot import VideoBot
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    try:
        # Create necessary directories
        Path(Config.TEMP_DIR).mkdir(parents=True, exist_ok=True)
        Path(Config.THUMB_DIR).mkdir(parents=True, exist_ok=True)
        
        # Initialize and start bot
        bot = VideoBot()
        await bot.start()
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
