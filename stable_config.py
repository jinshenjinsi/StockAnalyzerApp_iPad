# 稳定配置文件
import os

# 禁用Flask的自动重载
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = '0'

# 设置环境变量
os.environ['PYTHONUNBUFFERED'] = '1'
