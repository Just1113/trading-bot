import os

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])

LEVERAGE = 5
RISK_PERCENT = 2

# Pairs to scan
PAIRS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]

# Candle interval and number of candles
CANDLE_INTERVAL = "1m"
CANDLE_LIMIT = 50
