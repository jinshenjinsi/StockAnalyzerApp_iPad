#!/bin/bash

# 股票分析系统 - 稳定启动脚本
# 禁用自动重载，避免文件被意外修改

echo "🚀 启动股票分析系统 (稳定模式)..."

# 检查并激活虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先创建"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖
echo "📦 检查依赖..."
pip install -q flask akshare pandas yfinance numpy requests

# 检查主程序文件
if [ ! -f "stock_app_final.py" ]; then
    echo "❌ 主程序文件不存在"
    exit 1
fi

# 检查端口占用
echo "🔍 检查端口8082..."
if lsof -i :8082 > /dev/null 2>&1; then
    echo "⚠️  端口8082被占用，正在清理..."
    lsof -ti :8082 | xargs kill -9
    sleep 2
fi

# 创建稳定的配置文件
cat > stable_config.py << 'EOF'
# 稳定配置文件
import os

# 禁用Flask的自动重载
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = '0'

# 设置环境变量
os.environ['PYTHONUNBUFFERED'] = '1'
EOF

# 启动系统（禁用自动重载）
echo "✅ 启动系统 (稳定模式，禁用自动重载)..."
echo "🌐 访问地址: http://127.0.0.1:8082"
echo "📱 排名页面: http://127.0.0.1:8082/ranking"
echo "🔍 选股系统: http://127.0.0.1:8082/screener"
echo ""
echo "💡 提示："
echo "   - 系统已禁用自动重载，文件不会被意外修改"
echo "   - 如需修改代码，请手动重启系统"
echo "   - 按 Ctrl+C 停止系统"
echo ""

# 使用nohup在后台运行，避免终端关闭影响
nohup python3 -c "
import stable_config
from stock_app_final import app
app.run(host='127.0.0.1', port=8082, debug=False, use_reloader=False)
" > app.log 2>&1 &

# 等待启动
sleep 3

# 检查启动状态
if curl -s http://127.0.0.1:8082 > /dev/null 2>&1; then
    echo "✅ 系统启动成功！"
    echo "📊 日志文件: app.log"
    echo "🔄 进程ID: $(lsof -ti :8082)"
else
    echo "❌ 系统启动失败，请检查日志文件 app.log"
    exit 1
fi

echo ""
echo "🎯 系统功能："
echo "   1. 个股分析 (主页)"
echo "   2. 市场排名 (A股/港股)"
echo "   3. 智能选股 (多策略)"
echo ""
echo "🔧 如需重启，请运行: ./start_stable.command"

