# 配置文件
# 金融数据API密钥配置

import os

# Alpha Vantage API 密钥 - 用于美股数据
# 从 https://www.alphavantage.co/support/#api-key 获取
# 优先从环境变量读取，如果不存在则使用默认值
API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY', 'Z4GC8T7NGOHOFHE9')

# Tushare Pro Token - 用于专业金融数据  
# 从 https://tushare.pro/user/token 获取
# 优先从环境变量读取，如果不存在则使用默认值
TUSHARE_TOKEN = os.environ.get('TUSHARE_TOKEN', '6d2d3670dc991b5d6aa899ab533dcc1f8f6c283683aea96d996136c4')

# 数据源说明：
# 1. A股和港股：使用akshare专业数据（无需API密钥）
# 2. 美股：使用Alpha Vantage + yfinance
# 3. 专业数据：可使用Tushare Pro（如需使用）

# 缓存配置
CACHE_EXPIRE_MINUTES = int(os.environ.get('CACHE_EXPIRE_MINUTES', '60'))  # 默认缓存60分钟

# 调试模式
DEBUG_MODE = os.environ.get('DEBUG_MODE', 'false').lower() == 'true'