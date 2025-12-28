from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)
import asyncio
import logging
from typing import Dict, Any

from config import config
from strategies import TradingStrategies
from ml_model import SignalConfidenceModel
from bybit_client import BybitClient

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.application = None
        self.bybit_client = BybitClient()
        self.ml_model = SignalConfidenceModel()
        self.pending_signals = {}  # Store pending signals for confirmation
        self.last_signals = {}  # Track last signals to avoid duplicates
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        if str(update.effective_chat.id) != config.ADMIN_CHAT_ID:
            await update.message.reply_text("⛔ Unauthorized access.")
            return
        
        await update.message.reply_text(
            "🤖 Bybit Trading Bot Started!\n\n"
            "Available Commands:\n"
            "/start - Start the bot\n"
            "/setleverage <number> - Set leverage\n"
            "/setrisk <percentage> - Set risk percentage\n"
            "/status - Check bot status\n"
            "/balance - Check account balance\n"
            "/positions - View open positions"
        )
        
        # Start scanning in background
        asyncio.create_task(self.start_scanning())
        
        logger.info("Bot started successfully")
    
    async def set_leverage_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setleverage command"""
        if str(update.effective_chat.id) != config.ADMIN_CHAT_ID:
            await update.message.reply_text("⛔ Unauthorized access.")
            return
        
        try:
            leverage = int(context.args[0])
            if leverage < 1 or leverage > 100:
                await update.message.reply_text("⚠️ Leverage must be between 1 and 100.")
                return
            
            # Set leverage for all pairs
            for symbol in config.TRADE_PAIRS:
                success = self.bybit_client.set_leverage(symbol, leverage)
                if success:
                    logger.info(f"Leverage set to {leverage} for {symbol}")
            
            config.DEFAULT_LEVERAGE = leverage
            await update.message.reply_text(f"✅ Leverage set to {leverage}x for all pairs.")
            
        except (IndexError, ValueError):
            await update.message.reply_text("⚠️ Usage: /setleverage <number>")
    
    async def set_risk_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setrisk command"""
        if str(update.effective_chat.id) != config.ADMIN_CHAT_ID:
            await update.message.reply_text("⛔ Unauthorized access.")
            return
        
        try:
            risk_percent = float(context.args[0])
            if risk_percent < 0.1 or risk_percent > 10:
                await update.message.reply_text("⚠️ Risk percentage must be between 0.1 and 10.")
                return
            
            config.RISK_PERCENTAGE = risk_percent
            await update.message.reply_text(f"✅ Risk percentage set to {risk_percent}%.")
            
        except (IndexError, ValueError):
            await update.message.reply_text("⚠️ Usage: /setrisk <percentage>")
    
    async def check_balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command"""
        if str(update.effective_chat.id) != config.ADMIN_CHAT_ID:
            await update.message.reply_text("⛔ Unauthorized access.")
            return
        
        balance = self.bybit_client.get_account_balance()
        await update.message.reply_text(f"💰 Account Balance: ${balance:,.2f}")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks for trade confirmation"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        chat_id = str(update.effective_chat.id)
        
        if chat_id != config.ADMIN_CHAT_ID:
            await query.edit_message_text("⛔ Unauthorized access.")
            return
        
        if data in self.pending_signals:
            signal_data = self.pending_signals[data]
            
            if data.startswith('confirm_'):
                # Execute trade
                await self.execute_trade(signal_data, query)
            elif data.startswith('cancel_'):
                # Cancel trade
                await query.edit_message_text(
                    f"❌ Trade canceled for {signal_data['symbol']}\n"
                    f"Signal: {signal_data['signal']}\n"
                    f"Price: ${signal_data['current_price']}"
                )
            
            # Remove from pending signals
            del self.pending_signals[data]
    
    async def execute_trade(self, signal_data: Dict, query):
        """Execute confirmed trade"""
        try:
            symbol = signal_data['symbol']
            signal = signal_data['signal']
            current_price = signal_data['current_price']
            
            # Calculate position size
            balance = self.bybit_client.get_account_balance()
            risk_amount = balance * (config.RISK_PERCENTAGE / 100)
            
            # Calculate quantity with leverage
            position_value = risk_amount * config.DEFAULT_LEVERAGE
            quantity = position_value / current_price
            
            # Calculate stop loss and take profit
            if signal == 'BUY':
                stop_loss = current_price * (1 - config.STOP_LOSS_PERCENT / 100)
                take_profit = current_price * (1 + config.TAKE_PROFIT_PERCENT / 100)
                side = 'Buy'
            else:  # SELL
                stop_loss = current_price * (1 + config.STOP_LOSS_PERCENT / 100)
                take_profit = current_price * (1 - config.TAKE_PROFIT_PERCENT / 100)
                side = 'Sell'
            
            # Place order
            order_result = self.bybit_client.place_order(
                symbol=symbol,
                side=side,
                qty=quantity,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            if order_result:
                await query.edit_message_text(
                    f"✅ Trade Executed!\n\n"
                    f"Symbol: {symbol}\n"
                    f"Side: {side}\n"
                    f"Quantity: {quantity:.4f}\n"
                    f"Entry: ${current_price:.2f}\n"
                    f"Stop Loss: ${stop_loss:.2f}\n"
                    f"Take Profit: ${take_profit:.2f}\n"
                    f"Confidence: {signal_data['confidence']:.1%}"
                )
                
                # Log the trade
                logger.info(f"Trade executed: {symbol} {side} {quantity} @ {current_price}")
            else:
                await query.edit_message_text(
                    f"❌ Trade execution failed for {symbol}"
                )
                
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            await query.edit_message_text("❌ Trade execution failed due to an error.")
    
    async def scan_pair(self, symbol: str):
        """Scan a single pair for trading signals"""
        try:
            # Get market data
            market_data = self.bybit_client.get_market_data(symbol, '15', 100)
            if not market_data or 'list' not in market_data:
                return None
            
            # Extract closing prices
            prices = [float(candle[4]) for candle in market_data['list']]  # Close prices
            current_price = prices[-1] if prices else 0
            
            # Analyze with strategies
            strategy_results = TradingStrategies.analyze_all_strategies(prices)
            final_signal = strategy_results['final_signal']
            
            if final_signal == 'HOLD':
                return None
            
            # Calculate ML confidence
            ml_confidence = self.ml_model.calculate_confidence(
                prices, final_signal, strategy_results
            )
            
            # Check minimum confidence
            if ml_confidence < config.MIN_CONFIDENCE:
                return None
            
            # Check for duplicate signal
            signal_key = f"{symbol}_{final_signal}"
            if (signal_key in self.last_signals and 
                (asyncio.get_event_loop().time() - self.last_signals[signal_key]) < 300):  # 5 minutes
                return None
            
            return {
                'symbol': symbol,
                'signal': final_signal,
                'confidence': ml_confidence,
                'current_price': current_price,
                'strategy_results': strategy_results
            }
            
        except Exception as e:
            logger.error(f"Error scanning {symbol}: {e}")
            return None
    
    async def start_scanning(self):
        """Start continuous scanning of all pairs"""
        logger.info("Starting multi-pair scanning...")
        
        while True:
            try:
                for symbol in config.TRADE_PAIRS:
                    signal = await self.scan_pair(symbol)
                    
                    if signal:
                        # Store in last signals
                        signal_key = f"{signal['symbol']}_{signal['signal']}"
                        self.last_signals[signal_key] = asyncio.get_event_loop().time()
                        
                        # Send signal to Telegram
                        await self.send_signal_alert(signal)
                
                # Wait for next scan
                await asyncio.sleep(config.SCAN_INTERVAL)
                
            except Exception as e:
                logger.error(f"Scanning error: {e}")
                await asyncio.sleep(config.SCAN_INTERVAL)
    
    async def send_signal_alert(self, signal: Dict):
        """Send signal alert to Telegram with confirmation buttons"""
        symbol = signal['symbol']
        current_price = signal['current_price']
        confidence = signal['confidence']
        
        # Create unique callback data
        callback_id = f"confirm_{symbol}_{int(asyncio.get_event_loop().time())}"
        cancel_id = f"cancel_{symbol}_{int(asyncio.get_event_loop().time())}"
        
        # Store signal data
        self.pending_signals[callback_id] = signal
        self.pending_signals[cancel_id] = signal
        
        # Create keyboard
        keyboard = [
            [
                InlineKeyboardButton("✅ YES - Execute", callback_data=callback_id),
                InlineKeyboardButton("❌ NO - Cancel", callback_data=cancel_id)
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send message
        message_text = (
            f"🚨 Trading Signal Detected!\n\n"
            f"Symbol: {symbol}\n"
            f"Signal: {signal['signal']}\n"
            f"Current Price: ${current_price:.2f}\n"
            f"Confidence: {confidence:.1%}\n\n"
            f"Execute trade?"
        )
        
        # Get bot instance from application
        if self.application:
            await self.application.bot.send_message(
                chat_id=config.ADMIN_CHAT_ID,
                text=message_text,
                reply_markup=reply_markup
            )
    
    # ... (keep all your existing imports and class definition)

async def run(self):
    """Start the Telegram bot - CORRECTED VERSION"""
    # Create application
    self.application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    self.application.add_handler(CommandHandler("start", self.start_command))
    self.application.add_handler(CommandHandler("setleverage", self.set_leverage_command))
    self.application.add_handler(CommandHandler("setrisk", self.set_risk_command))
    self.application.add_handler(CommandHandler("balance", self.check_balance_command))
    
    # Add callback handler for buttons
    self.application.add_handler(CallbackQueryHandler(self.button_callback))
    
    # Start bot
    logger.info("Telegram bot starting...")
    
    # 🔥 CORRECTION: Use create_task instead of await for polling
    # This prevents blocking the main event loop
    asyncio.create_task(self.application.run_polling())
    
    # 🔥 ADD: Start scanning in background
    asyncio.create_task(self.start_scanning())
    
    # 🔥 ADD: Keep the event loop running
    # This is the key fix - we need to keep the main coroutine alive
    while True:
        await asyncio.sleep(3600)  # Sleep for 1 hour, keep bot alive
