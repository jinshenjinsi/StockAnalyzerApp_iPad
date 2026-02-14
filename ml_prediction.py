#!/usr/bin/env python3
"""
Machine Learning Prediction Module for Stock Analyzer
Phase 3: Advanced ML models for stock price prediction and sentiment analysis
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib

class MLPredictionEngine:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_columns = [
            'open', 'high', 'low', 'close', 'volume',
            'macd', 'rsi', 'bollinger_upper', 'bollinger_lower',
            'sma_20', 'sma_50', 'ema_12', 'ema_26'
        ]
        
    def prepare_features(self, df):
        """Prepare features for ML model"""
        # Ensure all required columns exist
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0
        
        return df[self.feature_columns]
    
    def train_price_prediction_model(self, symbol, historical_data):
        """Train ML model for price prediction"""
        try:
            # Prepare features and target
            features = self.prepare_features(historical_data)
            target = historical_data['close'].shift(-1)  # Next day's close price
            
            # Remove last row (no target available)
            features = features[:-1]
            target = target[:-1]
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, target, test_size=0.2, random_state=42
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            model.fit(X_train_scaled, y_train)
            
            # Store model and scaler
            self.models[f"{symbol}_price"] = model
            self.scalers[f"{symbol}_price"] = scaler
            
            # Calculate accuracy
            accuracy = model.score(X_test_scaled, y_test)
            print(f"Model trained for {symbol} with R² score: {accuracy:.4f}")
            
            return accuracy
            
        except Exception as e:
            print(f"Error training model for {symbol}: {str(e)}")
            return 0.0
    
    def predict_next_price(self, symbol, current_features):
        """Predict next day's closing price"""
        try:
            model_key = f"{symbol}_price"
            if model_key not in self.models:
                return None
                
            # Scale features
            scaler = self.scalers[model_key]
            features_scaled = scaler.transform([current_features])
            
            # Make prediction
            prediction = self.models[model_key].predict(features_scaled)[0]
            return float(prediction)
            
        except Exception as e:
            print(f"Error predicting price for {symbol}: {str(e)}")
            return None
    
    def save_models(self, directory="models"):
        """Save trained models to disk"""
        os.makedirs(directory, exist_ok=True)
        for name, model in self.models.items():
            joblib.dump(model, os.path.join(directory, f"{name}.pkl"))
        for name, scaler in self.scalers.items():
            joblib.dump(scaler, os.path.join(directory, f"{name}_scaler.pkl"))
    
    def load_models(self, directory="models"):
        """Load trained models from disk"""
        if not os.path.exists(directory):
            return
            
        for filename in os.listdir(directory):
            if filename.endswith('.pkl'):
                name = filename[:-4]
                filepath = os.path.join(directory, filename)
                if '_scaler' in name:
                    self.scalers[name.replace('_scaler', '')] = joblib.load(filepath)
                else:
                    self.models[name] = joblib.load(filepath)

# Example usage
if __name__ == "__main__":
    engine = MLPredictionEngine()
    print("ML Prediction Engine initialized")