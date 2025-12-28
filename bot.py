import asyncio
import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Main entry point"""
    logger.info("🚀 Starting Bybit Trading Bot on Render...")
    
    # Check environment variables
    required_vars = ['TELEGRAM_BOT_TOKEN', 'ADMIN_CHAT_ID', 'BYBIT_API_KEY', 'BYBIT_API_SECRET']
    missing = [v for v in required_vars if not os.getenv(v)]
    
    if missing:
        logger.error(f"❌ Missing environment variables: {missing}")
        logger.info("Set these in Render dashboard > Environment")
        sys.exit(1)
    
    logger.info("✅ All environment variables verified")
    
    # Import and start bot
    from telegram_bot import TelegramBot
    bot = TelegramBot()
    logger.info("✅ Telegram bot initialized")
    
    # Start the bot
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
