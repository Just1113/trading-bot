import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID', '')
    
    # Bybit Configuration
    BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', '')
    BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET', '')
    BYBIT_TESTNET = os.getenv('BYBIT_TESTNET', 'true').lower() == 'true'
    
    # Trading Configuration
    TRADE_PAIRS = os.getenv('TRADE_PAIRS', 'BTCUSDT,ETHUSDT,BNBUSDT').split(',')
    DEFAULT_LEVERAGE = float(os.getenv('DEFAULT_LEVERAGE', '10'))
    RISK_PERCENTAGE = float(os.getenv('RISK_PERCENTAGE', '2'))  # 2% per trade
    STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', '1.5'))
    TAKE_PROFIT_PERCENT = float(os.getenv('TAKE_PROFIT_PERCENT', '3.0'))
    
    # Bot Configuration
    SCAN_INTERVAL = int(os.getenv('SCAN_INTERVAL', '60'))  # seconds
    MIN_CONFIDENCE = float(os.getenv('MIN_CONFIDENCE', '0.7'))  # 70% confidence
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

config = Config()
