from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, JobQueue
)
from strategies import STRATEGIES
from ml_model import predict_confidence
from bybit_client import get_candles, get_balance, place_order
import config

LAST_SIGNAL = {}

# --- Admin commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Trading bot online.")

async def set_leverage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        try:
            config.LEVERAGE = int(context.args[0])
            await update.message.reply_text(f"Leverage set to {config.LEVERAGE}x")
        except ValueError:
            await update.message.reply_text("Invalid number")
    else:
        await update.message.reply_text("Usage: /setleverage <number>")

async def set_risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        try:
            config.RISK_PERCENT = float(context.args[0])
            await update.message.reply_text(f"Risk set to {config.RISK_PERCENT}%")
        except ValueError:
            await update.message.reply_text("Invalid number")
    else:
        await update.message.reply_text("Usage: /setrisk <number>")

# --- Signal generation ---
async def generate_signals(context: ContextTypes.DEFAULT_TYPE):
    balance_info = get_balance()
    balance = float(balance_info.get("result", {}).get("USDT", {}).get("totalBalance", 100))
    for pair in config.PAIRS:
        candles = get_candles(pair, config.CANDLE_INTERVAL, config.CANDLE_LIMIT)
        for name, func in STRATEGIES.items():
            signal = func(candles)
            if signal == "HOLD": continue
            confidence = predict_confidence(name, signal)
            last_price = float(candles[-1]['close'])
            if signal == "BUY":
                sl = round(last_price * 0.985, 2)
                tp = round(last_price * 1.03, 2)
            else:
                sl = round(last_price * 1.015, 2)
                tp = round(last_price * 0.97, 2)
            qty = round(balance * config.RISK_PERCENT / 100 * config.LEVERAGE, 3)
            LAST_SIGNAL[pair] = {"side": signal, "sl": sl, "tp": tp, "qty": qty}
            buttons = [[InlineKeyboardButton("YES", callback_data=f"confirm_yes|{pair}"),
                        InlineKeyboardButton("NO", callback_data=f"confirm_no|{pair}")]]
            await context.bot.send_message(
                chat_id=config.ADMIN_ID,
                text=(
                    f"📊 SIGNAL → {pair}\n"
                    f"Strategy: {name}\nDirection: {signal}\nConfidence: {confidence}%\n"
                    f"SL: {sl} | TP: {tp}\nQty: {qty}\n\nExecute trade?"
                ),
                reply_markup=InlineKeyboardMarkup(buttons)
            )

# --- YES/NO callback ---
async def confirm_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, pair = query.data.split("|")
    signal = LAST_SIGNAL.get(pair)
    if not signal:
        await query.edit_message_text("Signal expired or not found")
        return
    if action == "confirm_yes":
        place_order(pair, signal["side"], signal["qty"], signal["sl"], signal["tp"])
        await query.edit_message_text(f"✅ Trade executed for {pair}.")
    else:
        await query.edit_message_text(f"❌ Trade cancelled for {pair}.")

# --- Startup message ---
async def startup_message(application):
    await application.bot.send_message(chat_id=config.ADMIN_ID,
                                       text="🚀 Bot started successfully on Render!")

# --- Start bot ---
def start_bot():
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setleverage", set_leverage))
    app.add_handler(CommandHandler("setrisk", set_risk))
    app.add_handler(CallbackQueryHandler(confirm_trade))
    app.post_init = startup_message
    job_queue: JobQueue = app.job_queue
    job_queue.run_repeating(generate_signals, interval=60, first=10)
    app.run_polling()
                
