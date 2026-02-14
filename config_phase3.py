#!/usr/bin/env python3
"""
Configuration for Phase 3: Machine Learning Prediction Models
"""

import os
from typing import Dict, List

# API Keys (loaded from environment variables)
API_KEYS = {
    'alpha_vantage': os.getenv('ALPHA_VANTAGE_API_KEY', ''),
    'newsapi': os.getenv('NEWSAPI_KEY', ''),
    'twitter_bearer': os.getenv('TWITTER_BEARER_TOKEN', ''),
    'finnhub': os.getenv('FINNHUB_API_KEY', ''),
    'polygon': os.getenv('POLYGON_API_KEY', '')
}

# Machine Learning Configuration
ML_CONFIG = {
    'models': {
        'lstm': {
            'sequence_length': 60,
            'units': 50,
            'dropout': 0.2,
            'epochs': 100,
            'batch_size': 32
        },
        'random_forest': {
            'n_estimators': 100,
            'max_depth': 10,
            'min_samples_split': 2,
            'min_samples_leaf': 1
        },
        'xgboost': {
            'n_estimators': 1000,
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8
        }
    },
    'features': [
        'open', 'high', 'low', 'close', 'volume',
        'sma_20', 'sma_50', 'ema_20',
        'rsi', 'macd', 'macd_signal', 'macd_hist',
        'bb_upper', 'bb_middle', 'bb_lower',
        'sentiment_score', 'sentiment_confidence'
    ],
    'target': 'close_future_5d'  # Predict 5-day future close price
}

# Backtesting Configuration
BACKTESTING_CONFIG = {
    'initial_capital': 10000,
    'commission_rate': 0.001,  # 0.1% commission
    'slippage_rate': 0.0005,  # 0.05% slippage
    'risk_per_trade': 0.02,   # 2% risk per trade
    'max_position_size': 0.2   # Maximum 20% of portfolio in one position
}

# Sentiment Analysis Configuration
SENTIMENT_CONFIG = {
    'news_sources': ['reuters', 'bloomberg', 'cnbc', 'financial_times'],
    'social_sources': ['twitter', 'reddit'],
    'sentiment_threshold': {
        'strong_buy': 2.0,
        'buy': 0.5,
        'sell': -0.5,
        'strong_sell': -2.0
    },
    'confidence_threshold': 0.3
}

# Data Sources Configuration
DATA_SOURCES = {
    'primary': 'alpha_vantage',  # Primary data source
    'fallback': ['polygon', 'finnhub'],  # Fallback sources
    'cache_duration': 3600,  # Cache data for 1 hour
    'max_retries': 3
}

# Model Training Configuration
TRAINING_CONFIG = {
    'validation_split': 0.2,
    'test_split': 0.1,
    'early_stopping_patience': 10,
    'model_save_path': './models/',
    'feature_scaling': True,
    'handle_missing_data': 'interpolate'
}