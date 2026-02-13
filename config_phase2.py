"""
Phase 2 配置文件 - 支持高级技术指标、预警系统和收藏夹管理
"""
import os
from datetime import timedelta

# API 密钥配置
ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY', '')
TUSHARE_TOKEN = os.environ.get('TUSHARE_TOKEN', '')

# 缓存配置
CACHE_EXPIRE_MINUTES = 60
ALERT_CACHE_EXPIRE_MINUTES = 30

# 预警系统配置
ALERT_CHECK_INTERVAL = 300  # 5分钟检查一次
MAX_ALERTS_PER_USER = 50
ALERT_HISTORY_DAYS = 7

# 收藏夹配置
MAX_FAVORITES_PER_USER = 100
FAVORITES_CACHE_EXPIRE_MINUTES = 1440  # 24小时

# 技术指标配置
TECHNICAL_INDICATORS = {
    'rsi': {'period': 14, 'overbought': 70, 'oversold': 30},
    'macd': {'fast': 12, 'slow': 26, 'signal': 9},
    'bollinger_bands': {'period': 20, 'std_dev': 2},
    'ema': {'short': 12, 'long': 26},
    'sma': {'short': 20, 'long': 50},
    'adx': {'period': 14, 'threshold': 25},
    'stochastic': {'k_period': 14, 'd_period': 3, 'overbought': 80, 'oversold': 20}
}

# 数据源配置
DATA_SOURCES = {
    'yfinance': {
        'enabled': True,
        'max_retries': 3,
        'timeout': 10
    },
    'alpha_vantage': {
        'enabled': bool(ALPHA_VANTAGE_API_KEY),
        'max_retries': 3,
        'timeout': 10
    }
}

# 前端配置
FRONTEND_CONFIG = {
    'chart_timeframes': ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y'],
    'default_timeframe': '3mo',
    'max_chart_points': 1000,
    'refresh_interval': 60000  # 60秒自动刷新
}

# 安全配置
SECURITY_CONFIG = {
    'max_symbols_per_request': 10,
    'rate_limit_per_minute': 60,
    'allowed_symbol_patterns': [r'^[A-Z0-9\.]+$', r'^[036]\d{5}$']
}