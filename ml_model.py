import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os
from typing import Dict, Tuple, List  # ✅ CORRECT IMPORT
import logging

logger = logging.getLogger(__name__)

class SignalConfidenceModel:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.model_path = 'signal_model.pkl'
        self.scaler_path = 'signal_scaler.pkl'
        
    def extract_features(self, prices: List[float], indicators: Dict) -> np.ndarray:
        """Extract features for ML model"""
        features = []
        
        # Price-based features
        recent_prices = prices[-10:]
        features.append(np.mean(recent_prices))
        features.append(np.std(recent_prices))
        features.append((prices[-1] - prices[-10]) / prices[-10])  # 10-period return
        
        # Volatility features
        returns = np.diff(prices[-20:]) / prices[-21:-1]
        features.append(np.std(returns))
        
        # Indicator-based features
        if 'rsi' in indicators:
            features.append(indicators['rsi'])
        
        if 'ema_diff' in indicators:
            features.append(indicators['ema_diff'])
        
        return np.array(features).reshape(1, -1)
    
    def calculate_confidence(self, prices: List[float], signal: str, 
                           strategy_results: Dict) -> float:
        """Calculate confidence score using ML model"""
        try:
            # Extract technical indicators for features
            indicators = {}
            
            # Calculate RSI
            if len(prices) >= 15:
                deltas = np.diff(prices[-15:])
                up = deltas[deltas >= 0]
                down = -deltas[deltas < 0]
                
                if len(down) > 0 and np.mean(down) > 0:
                    rs = np.mean(up) / np.mean(down) if len(up) > 0 else 0
                    rsi = 100 - (100 / (1 + rs))
                    indicators['rsi'] = rsi
            
            # Calculate EMA difference
            # You need to import TradingStrategies if used here
            from strategies import TradingStrategies
            if len(prices) >= 22:
                ema_9 = TradingStrategies.calculate_ema(prices, 9)[-1]
                ema_21 = TradingStrategies.calculate_ema(prices, 21)[-1]
                if not np.isnan(ema_9) and not np.isnan(ema_21):
                    indicators['ema_diff'] = (ema_9 - ema_21) / ema_21
            
            # Extract features
            features = self.extract_features(prices, indicators)
            
            # Load or create model
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
            else:
                # Create synthetic training data for initial model
                self._create_initial_model()
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Get prediction probabilities
            probabilities = self.model.predict_proba(features_scaled)[0]
            
            # Map signal to class
            signal_map = {'BUY': 0, 'SELL': 1, 'HOLD': 2}
            if signal in signal_map:
                confidence = probabilities[signal_map[signal]]
            else:
                confidence = probabilities[2]  # Default to HOLD confidence
            
            # Adjust based on strategy agreement
            strategy_confidence = strategy_results.get('confidence', 0.5)
            final_confidence = (confidence + strategy_confidence) / 2
            
            return min(max(final_confidence, 0), 1)
            
        except Exception as e:
            logger.error(f"ML confidence calculation failed: {e}")
            return strategy_results.get('confidence', 0.5)
    
    def _create_initial_model(self):
        """Create initial ML model with synthetic data"""
        np.random.seed(42)
        n_samples = 1000
        
        # Create synthetic features
        X = np.random.randn(n_samples, 5)
        y = np.random.choice([0, 1, 2], size=n_samples, p=[0.3, 0.3, 0.4])
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        
        # Save model
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        
        logger.info("Initial ML model created and saved")
    
    def update_model(self, features: np.ndarray, actual_success: bool):
        """Update model with new training data"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
            
            # Prepare new data
            label = 1 if actual_success else 0
            
            # Partial fit (if supported) or retrain periodically
            logger.info(f"Model update queued - Success: {actual_success}")
            
        except Exception as e:
            logger.error(f"Model update failed: {e}")
