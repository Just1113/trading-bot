import requests, time, hmac, hashlib, os

BASE_URL = "https://api.bybitglobal.com"
API_KEY = os.environ["BYBIT_API_KEY"]
API_SECRET = os.environ["BYBIT_API_SECRET"]

def sign(params):
    q = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()

def get_balance():
    ts = int(time.time() * 1000)
    params = {"api_key": API_KEY, "timestamp": ts, "accountType": "UNIFIED"}
    params["sign"] = sign(params)
    r = requests.get(f"{BASE_URL}/v5/account/wallet-balance", params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def get_candles(symbol, interval="1m", limit=50):
    url = f"{BASE_URL}/v2/public/kline/list"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json().get("result", [])

def place_order(symbol, side, qty, sl, tp):
    # Example: replace with actual Bybit order endpoint
    print(f"EXECUTE ORDER → {symbol} | {side} | qty={qty} | SL={sl} | TP={tp}")
    
