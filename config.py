#!/usr/bin/env python3
"""
Unified Configuration Management for Stock Analyzer
Manages all configuration settings across all phases.
"""

import os
from typing import Dict, Any

class Config:
    def __init__(self):
        # API Keys
        self.api_keys = {
            'alpha_vantage': os.getenv('ALPHA_VANTAGE_API_KEY', ''),
            'finnhub': os.getenv('FINNHUB_API_KEY', ''),
            'newsapi': os.getenv('NEWSAPI_KEY', ''),
            'twitter_bearer': os.getenv('TWITTER_BEARER_TOKEN', ''),
            'openai': os.getenv('OPENAI_API_KEY', '')
        }
        
        # Data Sources
        self.data_sources = {
            'primary': 'alpha_vantage',
            'fallback': 'finnhub',
            'news': 'newsapi',
            'social': 'twitter'
        }
        
        # Cache Settings
        self.cache = {
            'enabled': True,
            'stock_data_ttl': 3600,  # 1 hour
            'technical_indicators_ttl': 7200,  # 2 hours
            'ml_predictions_ttl': 86400,  # 24 hours
            'sentiment_ttl': 3600,  # 1 hour
            'backtest_results_ttl': 604800  # 7 days
        }
        
        # ML Model Settings
        self.ml = {
            'enabled': True,
            'prediction_days': 7,
            'features': ['open', 'high', 'low', 'close', 'volume', 'rsi', 'macd', 'bollinger'],
            'model_type': 'lstm',
            'sequence_length': 60,
            'epochs': 50,
            'batch_size': 32
        }
        
        # Alert Settings
        self.alerts = {
            'enabled': True,
            'max_alerts_per_user': 50,
            'notification_methods': ['email', 'web'],  # WhatsApp will be added when available
            'check_interval_seconds': 300  # 5 minutes
        }
        
        # Performance Settings
        self.performance = {
            'max_concurrent_requests': 10,
            'request_timeout_seconds': 30,
            'rate_limit_per_minute': 60
        }
        
        # Phase Settings
        self.phases = {
            'phase1_enabled': True,
            'phase2_enabled': True,
            'phase3_enabled': True
        }
    
    def get_api_key(self, service: str) -> str:
        """Get API key for a specific service"""
        return self.api_keys.get(service, '')
    
    def is_phase_enabled(self, phase: str) -> bool:
        """Check if a phase is enabled"""
        return self.phases.get(f'{phase}_enabled', False)
    
    def get_cache_ttl(self, data_type: str) -> int:
        """Get cache TTL for a specific data type"""
        return self.cache.get(f'{data_type}_ttl', 3600)
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return status"""
        status = {
            'valid': True,
            'missing_keys': [],
            'warnings': []
        }
        
        # Check required API keys
        required_keys = ['alpha_vantage', 'finnhub']
        for key in required_keys:
            if not self.api_keys.get(key):
                status['missing_keys'].append(key)
                status['valid'] = False
        
        # Check optional keys
        optional_keys = ['newsapi', 'twitter_bearer', 'openai']
        for key in optional_keys:
            if not self.api_keys.get(key):
                status['warnings'].append(f"Optional API key missing: {key}")
        
        return status

# Global config instance
config = Config()

if __name__ == "__main__":
    # Test configuration
    validation = config.validate_config()
    print(f"Configuration valid: {validation['valid']}")
    if validation['missing_keys']:
        print(f"Missing required keys: {validation['missing_keys']}")
    if validation['warnings']:
        print(f"Warnings: {validation['warnings']}")