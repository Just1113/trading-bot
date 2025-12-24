import threading
from keepalive import run
from telegram_bot import start_bot

# Run Flask server for Render port binding
threading.Thread(target=run, daemon=True).start()

# Run Telegram bot
start_bot()
