import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
import logging

logger = logging.getLogger(__name__)

class TradingStrategies:
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """Calculate RSI indicator"""
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        
        if down == 0:
            return 100.0
        
        rs = up / down
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return rsi
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return [np.nan] * len(prices)
        
        ema_values = []
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        ema_values.extend([np.nan] * (period - 1))
        ema_values.append(ema)
        
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
            ema_values.append(ema)
        
        return ema_values
    
    @staticmethod
    def rsi_strategy(prices: List[float]) -> Tuple[str, float]:
        """RSI Overbought/Oversold Strategy"""
        if len(prices) < 15:
            return "HOLD", 0.0
        
        rsi = TradingStrategies.calculate_rsi(prices)
        
        if rsi < 30:
            confidence = (30 - rsi) / 30  # Normalize to 0-1
            return "BUY", confidence
        elif rsi > 70:
            confidence = (rsi - 70) / 30
            return "SELL", confidence
        else:
            return "HOLD", 0.0
    
    @staticmethod
    def ema_crossover_strategy(prices: List[float]) -> Tuple[str, float]:
        """EMA Crossover Strategy (9 & 21 period)"""
        if len(prices) < 22:
            return "HOLD", 0.0
        
        ema_9 = TradingStrategies.calculate_ema(prices, 9)
        ema_21 = TradingStrategies.calculate_ema(prices, 21)
        
        if len(ema_9) < 2 or len(ema_21) < 2:
            return "HOLD", 0.0
        
        # Get last two values for comparison
        ema_9_current = ema_9[-1]
        ema_9_prev = ema_9[-2]
        ema_21_current = ema_21[-1]
        ema_21_prev = ema_21[-2]
        
        if pd.isna(ema_9_current) or pd.isna(ema_21_current):
            return "HOLD", 0.0
        
        # Check for crossover
        if ema_9_prev <= ema_21_prev and ema_9_current > ema_21_current:
            # Golden cross - BUY signal
            crossover_strength = (ema_9_current - ema_21_current) / ema_21_current
            confidence = min(0.3 + abs(crossover_strength) * 10, 0.9)
            return "BUY", confidence
        elif ema_9_prev >= ema_21_prev and ema_9_current < ema_21_current:
            # Death cross - SELL signal
            crossover_strength = (ema_21_current - ema_9_current) / ema_9_current
            confidence = min(0.3 + abs(crossover_strength) * 10, 0.9)
            return "SELL", confidence
        
        return "HOLD", 0.0
    
    @staticmethod
    def breakout_strategy(prices: List[float]) -> Tuple[str, float]:
        """Breakout Strategy using recent highs/lows"""
        if len(prices) < 20:
            return "HOLD", 0.0
        
        recent_prices = prices[-20:]
        current_price = prices[-1]
        
        resistance = max(recent_prices[:15])
        support = min(recent_prices[:15])
        
        # Check for breakout
        if current_price > resistance * 1.02:  # 2% above resistance
            breakout_strength = (current_price - resistance) / resistance
            confidence = min(0.4 + breakout_strength * 20, 0.85)
            return "BUY", confidence
        elif current_price < support * 0.98:  # 2% below support
            breakdown_strength = (support - current_price) / support
            confidence = min(0.4 + breakdown_strength * 20, 0.85)
            return "SELL", confidence
        
        return "HOLD", 0.0
    
    @staticmethod
    def trend_following_strategy(prices: List[float]) -> Tuple[str, float]:
        """Trend Following using multiple EMAs"""
        if len(prices) < 50:
            return "HOLD", 0.0
        
        ema_20 = TradingStrategies.calculate_ema(prices, 20)
        ema_50 = TradingStrategies.calculate_ema(prices, 50)
        
        if len(ema_20) < 2 or len(ema_50) < 2:
            return "HOLD", 0.0
        
        ema_20_current = ema_20[-1]
        ema_50_current = ema_50[-1]
        
        if pd.isna(ema_20_current) or pd.isna(ema_50_current):
            return "HOLD", 0.0
        
        price_trend = np.polyfit(range(len(prices[-10:])), prices[-10:], 1)[0]
        
        if ema_20_current > ema_50_current and price_trend > 0:
            trend_strength = (ema_20_current - ema_50_current) / ema_50_current
            confidence = min(0.5 + abs(trend_strength) * 15, 0.88)
            return "BUY", confidence
        elif ema_20_current < ema_50_current and price_trend < 0:
            trend_strength = (ema_50_current - ema_20_current) / ema_20_current
            confidence = min(0.5 + abs(trend_strength) * 15, 0.88)
            return "SELL", confidence
        
        return "HOLD", 0.0
    
    @staticmethod
    def mean_reversion_strategy(prices: List[float]) -> Tuple[str, float]:
        """Mean Reversion using Bollinger Bands"""
        if len(prices) < 20:
            return "HOLD", 0.0
        
        recent_prices = prices[-20:]
        current_price = prices[-1]
        
        sma = np.mean(recent_prices)
        std = np.std(recent_prices)
        
        upper_band = sma + (2 * std)
        lower_band = sma - (2 * std)
        
        if current_price < lower_band:
            deviation = (lower_band - current_price) / lower_band
            confidence = min(0.6 + deviation * 25, 0.95)
            return "BUY", confidence
        elif current_price > upper_band:
            deviation = (current_price - upper_band) / upper_band
            confidence = min(0.6 + deviation * 25, 0.95)
            return "SELL", confidence
        
        return "HOLD", 0.0
    
    @staticmethod
    def analyze_all_strategies(prices: List[float]) -> Dict:
        """Run all strategies and aggregate results"""
        strategies = {
            'RSI': TradingStrategies.rsi_strategy,
            'EMA_CROSSOVER': TradingStrategies.ema_crossover_strategy,
            'BREAKOUT': TradingStrategies.breakout_strategy,
            'TREND': TradingStrategies.trend_following_strategy,
            'MEAN_REVERSION': TradingStrategies.mean_reversion_strategy
        }
        
        results = {}
        buy_signals = 0
        sell_signals = 0
        total_confidence = 0
        
        for name, strategy_func in strategies.items():
            signal, confidence = strategy_func(prices)
            results[name] = {'signal': signal, 'confidence': confidence}
            
            if signal == 'BUY':
                buy_signals += 1
                total_confidence += confidence
            elif signal == 'SELL':
                sell_signals += 1
                total_confidence += confidence
        
        # Determine final signal based on majority
        final_signal = "HOLD"
        avg_confidence = 0.0
        
        if buy_signals > sell_signals and buy_signals >= 3:
            final_signal = "BUY"
            avg_confidence = total_confidence / buy_signals if buy_signals > 0 else 0
        elif sell_signals > buy_signals and sell_signals >= 3:
            final_signal = "SELL"
            avg_confidence = total_confidence / sell_signals if sell_signals > 0 else 0
        
        return {
            'final_signal': final_signal,
            'confidence': avg_confidence,
            'individual_results': results
        }
