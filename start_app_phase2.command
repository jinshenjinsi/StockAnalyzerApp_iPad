#!/bin/bash
# Phase 2 启动脚本 - 无敌股票分析系统

# 设置工作目录
cd "$(dirname "$0")"

# 检查Python版本
python_version=$(python3 --version 2>&1)
echo "当前Python版本: $python_version"

# 安装依赖
echo "正在安装依赖..."
pip3 install -r requirements.txt

# 设置环境变量（如果需要）
# export ALPHA_VANTAGE_API_KEY="your_key_here"
# export TUSHARE_TOKEN="your_token_here"

# 启动应用
echo "启动无敌股票分析系统 Phase 2..."
python3 stock_app_phase2.py

echo "应用已启动，访问 http://localhost:8082"