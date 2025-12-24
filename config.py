import os

# Telegram
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])

# Bybit
LEVERAGE = 5
RISK_PERCENT = 2

# Trading pairs
PAIRS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]

# Candles
CANDLE_INTERVAL = "1m"
CANDLE_LIMIT = 50
