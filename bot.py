import asyncio
import logging
from telegram_bot import TelegramBot
from keepalive import KeepAliveServer
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self):
        self.telegram_bot = TelegramBot()
        self.keepalive_server = KeepAliveServer()
        self.is_running = False
    
    async def start(self):
        """Start the trading bot"""
        try:
            logger.info("Starting Bybit Trading Bot...")
            self.is_running = True
            
            # Start keepalive server for Render
            self.keepalive_server.start()
            
            # Start Telegram bot
            await self.telegram_bot.run()
            
        except Exception as e:
            logger.error(f"Bot startup failed: {e}")
            raise
    
    def stop(self):
        """Stop the trading bot gracefully"""
        logger.info("Stopping bot...")
        self.is_running = False
        self.keepalive_server.stop()
        sys.exit(0)

def handle_signal(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    bot.stop()

async def main():
    """Main entry point"""
    bot = TradingBot()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, lambda s, f: asyncio.create_task(bot.stop()))
    signal.signal(signal.SIGTERM, lambda s, f: asyncio.create_task(bot.stop()))
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        bot.stop()
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
