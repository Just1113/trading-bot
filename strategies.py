import pandas as pd

def rsi_strategy(candles):
    closes = [float(c['close']) for c in candles]
    df = pd.Series(closes)
    delta = df.diff()
    up = delta.clip(lower=0)
    down = -1*delta.clip(upper=0)
    roll_up = up.rolling(14).mean()
    roll_down = down.rolling(14).mean()
    rs = roll_up / roll_down
    rsi = 100 - (100 / (1 + rs))
    if rsi.iloc[-1] < 30: return "BUY"
    if rsi.iloc[-1] > 70: return "SELL"
    return "HOLD"

def ema_crossover(candles):
    closes = [float(c['close']) for c in candles]
    df = pd.Series(closes)
    ema_fast = df.ewm(span=10).mean()
    ema_slow = df.ewm(span=30).mean()
    if ema_fast.iloc[-1] > ema_slow.iloc[-1] and ema_fast.iloc[-2] <= ema_slow.iloc[-2]:
        return "BUY"
    if ema_fast.iloc[-1] < ema_slow.iloc[-1] and ema_fast.iloc[-2] >= ema_slow.iloc[-2]:
        return "SELL"
    return "HOLD"

def breakout(candles):
    highs = [float(c['high']) for c in candles[-20:]]
    lows = [float(c['low']) for c in candles[-20:]]
    close = float(candles[-1]['close'])
    if close > max(highs[:-1]): return "BUY"
    if close < min(lows[:-1]): return "SELL"
    return "HOLD"

def trend_follow(candles):
    closes = [float(c['close']) for c in candles[-20:]]
    slope = closes[-1] - closes[0]
    if slope > 0: return "BUY"
    if slope < 0: return "SELL"
    return "HOLD"

def mean_reversion(candles):
    closes = [float(c['close']) for c in candles[-20:]]
    sma = sum(closes)/len(closes)
    last = closes[-1]
    if last < 0.98*sma: return "BUY"
    if last > 1.02*sma: return "SELL"
    return "HOLD"

STRATEGIES = {
    "RSI": rsi_strategy,
    "EMA": ema_crossover,
    "BREAKOUT": breakout,
    "TREND": trend_follow,
    "MEAN_REV": mean_reversion,
}
