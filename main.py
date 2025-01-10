import asyncio
import os
from bot import VideoBot
from config import config

async def main():
    # Create temp directory
    os.makedirs(config['temp_dir'], exist_ok=True)
    
    # Initialize and start bot
    bot = VideoBot(
        api_id=config['api_id'],
        api_hash=config['api_hash'],
        bot_token=config['bot_token'],
        temp_dir=config['temp_dir']
    )
    
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())
