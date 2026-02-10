#!/bin/bash

# 股票分析系统启动脚本
# 支持环境变量配置API密钥

# 设置工作目录
cd "$(dirname "$0")"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
fi

# 检查依赖包是否安装
echo "🔍 检查依赖包..."
pip3 list | grep -q flask || pip3 install Flask
pip3 list | grep -q pandas || pip3 install pandas  
pip3 list | grep -q akshare || pip3 install akshare
pip3 list | grep -q yfinance || pip3 install yfinance
pip3 list | grep -q numpy || pip3 install numpy
pip3 list | grep -q requests || pip3 install requests
pip3 list | grep -q tushare || pip3 install tushare

# 获取本地IP地址（用于局域网访问）
LOCAL_IP=$(ip route get 8.8.8.8 | awk '{print $7}' | head -n1)
if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP="127.0.0.1"
fi

echo "🚀 启动股票分析系统..."
echo "🏠 本地访问: http://127.0.0.1:8082"
echo "📱 局域网访问: http://$LOCAL_IP:8082"
echo "💡 确保iPad和电脑在同一WiFi网络下"

# 启动应用（固定端口8082，便于iPad访问）
python3 stock_app_optimized.py