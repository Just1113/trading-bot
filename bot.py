import threading
from keepalive import run
from telegram_bot import start_bot

threading.Thread(target=run, daemon=True).start()
start_bot()
