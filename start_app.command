#!/bin/bash

# 股票分析系统启动脚本 (v1.2.0 兼容版)
# 适配Python 3.6.8环境

echo "🚀 启动股票分析系统 v1.2.0 (兼容版)..."
echo "📍 检测到Python版本: $(python3 --version)"

# 关闭可能存在的旧进程
pkill -f "stock_app_compatible.py" 2>/dev/null

# 设置环境变量（如果未设置）
export NO_PROXY="*"
export ALPHA_VANTAGE_API_KEY="${ALPHA_VANTAGE_API_KEY:-Z4GC8T7NGOHOFHE9}"

# 启动应用
echo "🌐 应用将在 http://0.0.0.0:8082 启动"
echo "📱 在同一局域网的设备上访问: http://$(hostname -I | awk '{print $1}'):8082"
echo "⏳ 启动中，请稍候..."

# 使用nohup后台运行，输出日志到文件
nohup python3 stock_app_compatible.py > app.log 2>&1 &

# 等待几秒让服务启动
sleep 3

# 检查是否启动成功
if ps aux | grep -v grep | grep "stock_app_compatible.py" > /dev/null; then
    echo "✅ 股票分析系统启动成功！"
    echo "🔗 访问地址: http://$(hostname -I | awk '{print $1}'):8082"
else
    echo "❌ 启动失败，请查看 app.log 文件"
    cat app.log
fi