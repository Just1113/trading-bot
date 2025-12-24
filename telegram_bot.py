from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from strategies import STRATEGIES
from ml_model import predict_confidence
from bybit_client import get_candles, get_balance, place_order
import config

LAST_SIGNAL = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Trading bot online.")

async def generate_signals(context):
    balance_info = get_balance()
    # Extract USDT balance (example)
    balance = float(balance_info.get("result", {}).get("USDT", {}).get("totalBalance", 100))

    for pair in config.PAIRS:
        candles = get_candles(pair, config.CANDLE_INTERVAL, config.CANDLE_LIMIT)
        for name, func in STRATEGIES.items():
            signal = func(candles)
            if signal == "HOLD":
                continue
            confidence = predict_confidence(name, signal)
            sl = round(float(candles[-1]['close']) * 0.985, 2)  # 1.5% below for BUY
            tp = round(float(candles[-1]['close']) * 1.03, 2)   # 3% above for BUY
            qty = round(balance * config.RISK_PERCENT / 100 * config.LEVERAGE, 3)

            LAST_SIGNAL[pair] = {"side": signal, "sl": sl, "tp": tp, "qty": qty}

            buttons = [
                [InlineKeyboardButton("YES", callback_data=f"confirm_yes|{pair}"),
                 InlineKeyboardButton("NO", callback_data=f"confirm_no|{pair}")]
            ]

            await context.bot.send_message(
                chat_id=config.ADMIN_ID,
                text=(
                    f"📊 SIGNAL → {pair}\n"
                    f"Strategy: {name}\n"
                    f"Direction: {signal}\n"
                    f"Confidence: {confidence}%\n"
                    f"SL: {sl} | TP: {tp}\nQty: {qty}\n\n"
                    "Execute trade?"
                ),
                reply_markup=InlineKeyboardMarkup(buttons)
            )

async def confirm_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, pair = query.data.split("|")
    signal = LAST_SIGNAL.get(pair)
    if action == "confirm_yes":
        place_order(pair, signal["side"], signal["qty"], signal["sl"], signal["tp"])
        await query.edit_message_text(f"Trade executed for {pair}.")
    else:
        await query.edit_message_text(f"Trade cancelled for {pair}.")

async def set_leverage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        config.LEVERAGE = int(context.args[0])
        await update.message.reply_text(f"Leverage set to {config.LEVERAGE}x")

async def set_risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        config.RISK_PERCENT = int(context.args[0])
        await update.message.reply_text(f"Risk set to {config.RISK_PERCENT}%")

async def startup_message(app):
    await app.bot.send_message(chat_id=config.ADMIN_ID, text="Bot started on Render scanning multiple pairs!")

def start_bot():
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setleverage", set_leverage))
    app.add_handler(CommandHandler("setrisk", set_risk))
    app.add_handler(CallbackQueryHandler(confirm_trade))
    app.post_init = startup_message

    app.job_queue.run_once(generate_signals, when=10)
    app.run_polling()
