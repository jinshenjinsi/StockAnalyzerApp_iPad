#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 启动智能选股系统..."
echo "================================"
echo "📁 工作目录: $SCRIPT_DIR"
echo "================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 错误: 虚拟环境不存在，请先创建虚拟环境"
    echo "运行命令: python3 -m venv venv"
    exit 1
fi

# 激活虚拟环境
echo "📦 激活虚拟环境..."
source venv/bin/activate

# 检查依赖
echo "🔍 检查依赖包..."
python3 -c "import flask, pandas, numpy, akshare, yfinance" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📥 安装依赖包..."
    pip install flask pandas numpy akshare yfinance requests
fi

# 检查主程序文件
if [ ! -f "stock_app_final.py" ]; then
    echo "❌ 错误: 主程序文件 stock_app_final.py 不存在"
    echo "📁 当前目录: $(pwd)"
    echo "📁 目录内容:"
    ls -la
    exit 1
fi

# 检查端口占用
echo "🔍 检查端口8080..."
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  端口8080已被占用，正在停止占用进程..."
    lsof -ti:8080 | xargs kill -9
    sleep 2
fi

# 启动应用
echo "🚀 启动智能选股系统..."
echo "================================"
echo "🌐 访问地址: http://127.0.0.1:8080"
echo "🔍 智能选股: http://127.0.0.1:8080/screener"
echo "📊 股票排名: http://127.0.0.1:8080/ranking"
echo "🏠 首页分析: http://127.0.0.1:8080"
echo "================================"
echo "💡 功能说明:"
echo "   - 🔍 智能选股：机构行为监控 + 智能支撑压力位"
echo "   - 📊 股票排名：压力位偏离度分析"
echo "   - 🏠 首页分析：个股技术分析"
echo "================================"

python3 stock_app_final.py



