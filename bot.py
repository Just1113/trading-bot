import threading
from keepalive import run
from telegram_bot import start_bot

# Start Flask server for Render port binding
threading.Thread(target=run, daemon=True).start()

# Start Telegram bot (async polling)
start_bot()
