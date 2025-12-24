import asyncio
import logging
import sys
import os
from telegram_bot import TelegramBot
# 🔥 REMOVE this import: from keepalive import KeepAliveServer
import signal

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

async def run_bot():
    """Run the trading bot"""
    try:
        logger.info("🚀 Starting Bybit Trading Bot on Render...")
        
        # Check required environment variables
        required_env_vars = [
            'TELEGRAM_BOT_TOKEN',
            'ADMIN_CHAT_ID', 
            'BYBIT_API_KEY',
            'BYBIT_API_SECRET'
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {missing_vars}")
            logger.error("Please set these in Render dashboard > Environment")
            sys.exit(1)
        
        logger.info("✅ All environment variables verified")
        
        # 🔥 COMMENT OUT OR REMOVE the keepalive server - NOT NEEDED ON RENDER
        # keepalive = KeepAliveServer()
        # keepalive.start()
        # logger.info("✅ Keepalive server started on port 8080")
        
        logger.info("⚠️ Keepalive server disabled - using Render's built-in health checks")
        
        # Start Telegram bot
        telegram_bot = TelegramBot()
        logger.info("✅ Telegram bot initialized")
        
        await telegram_bot.run()
        
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}", exc_info=True)
        sys.exit(1)

def handle_signal(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"⚠️ Received signal {signum}, shutting down...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Run the bot
    asyncio.run(run_bot())
