import hmac
import hashlib
import time
import requests
import json
from typing import Dict, Any, Optional
from urllib.parse import urlencode
import logging

from config import config

logger = logging.getLogger(__name__)

class BybitClient:
    def __init__(self):
        self.base_url = "https://api-testnet.bybit.com" if config.BYBIT_TESTNET else "https://api.bybit.com"
        self.api_key = config.BYBIT_API_KEY
        self.api_secret = config.BYBIT_API_SECRET
        self.session = requests.Session()
    
    def _generate_signature(self, params: Dict) -> str:
        """Generate HMAC SHA256 signature for Bybit API"""
        param_str = urlencode(sorted(params.items()))
        signature = hmac.new(
            bytes(self.api_secret, 'utf-8'),
            bytes(param_str, 'utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, private: bool = False) -> Dict:
        """Make authenticated request to Bybit API"""
        url = f"{self.base_url}{endpoint}"
        
        if private:
            if params is None:
                params = {}
            params['api_key'] = self.api_key
            params['timestamp'] = str(int(time.time() * 1000))
            params['recv_window'] = '5000'
            params['sign'] = self._generate_signature(params)
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            else:
                response = self.session.post(url, data=params)
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API request failed: {e}")
            raise
    
    def get_account_balance(self) -> float:
        """Get available USDT balance"""
        try:
            response = self._request('GET', '/v5/account/wallet-balance', {
                'accountType': 'UNIFIED',
                'coin': 'USDT'
            }, private=True)
            
            if response['retCode'] == 0:
                total_equity = float(response['result']['list'][0]['totalEquity'])
                return total_equity
            else:
                logger.error(f"Balance fetch failed: {response}")
                return 0.0
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return 0.0
    
    def get_market_data(self, symbol: str, interval: str = '15', limit: int = 100) -> Optional[Dict]:
        """Get candlestick data for a symbol"""
        try:
            response = self._request('GET', '/v5/market/kline', {
                'category': 'linear',
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            })
            
            if response['retCode'] == 0:
                return response['result']
            return None
        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            return None
    
    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for a trading pair"""
        try:
            response = self._request('POST', '/v5/position/set-leverage', {
                'category': 'linear',
                'symbol': symbol,
                'buyLeverage': str(leverage),
                'sellLeverage': str(leverage)
            }, private=True)
            
            return response['retCode'] == 0
        except Exception as e:
            logger.error(f"Failed to set leverage: {e}")
            return False
    
    def place_order(self, symbol: str, side: str, qty: float, 
                   stop_loss: float, take_profit: float) -> Optional[Dict]:
        """Place a market order with stop loss and take profit"""
        try:
            # Main order
            order_params = {
                'category': 'linear',
                'symbol': symbol,
                'side': side,
                'orderType': 'Market',
                'qty': str(qty),
                'timeInForce': 'GTC',
                'positionIdx': 0
            }
            
            order_response = self._request('POST', '/v5/order/create', order_params, private=True)
            
            if order_response['retCode'] != 0:
                logger.error(f"Order failed: {order_response}")
                return None
            
            # Set stop loss and take profit
            sl_tp_params = {
                'category': 'linear',
                'symbol': symbol,
                'side': 'Sell' if side == 'Buy' else 'Buy',
                'orderType': 'Market',
                'qty': str(qty),
                'triggerPrice': str(stop_loss),
                'triggerBy': 'MarkPrice',
                'reduceOnly': True,
                'closeOnTrigger': True
            }
            
            self._request('POST', '/v5/order/create', sl_tp_params, private=True)
            
            return order_response['result']
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return None
    
    def get_open_positions(self) -> Dict:
        """Get all open positions"""
        try:
            response = self._request('GET', '/v5/position/list', {
                'category': 'linear',
                'settleCoin': 'USDT'
            }, private=True)
            
            return response.get('result', {}).get('list', [])
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
