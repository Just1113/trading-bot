def predict_confidence(strategy_name, signal):
    # Confidence depends on strength of signal
    if signal == "HOLD":
        return 50
    if strategy_name == "RSI":
        return 90 if signal == "BUY" else 85
    if strategy_name == "EMA":
        return 85
    if strategy_name == "BREAKOUT":
        return 88
    if strategy_name == "TREND":
        return 80
    if strategy_name == "MEAN_REV":
        return 82
    return 70
