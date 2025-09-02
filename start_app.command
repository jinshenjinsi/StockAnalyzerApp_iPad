#!/bin/bash

# 股票分析系统启动脚本
# 双击此文件即可启动应用程序

echo "🚀 启动股票分析系统..."

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    echo ""
    read -p "按任意键退出..."
    exit 1
fi

echo "✅ Python3 已安装: $(python3 --version)"

# 检查依赖包
echo "✅ 检查依赖包..."
python3 -c "
try:
    import flask, pandas, akshare, numpy, requests
    print('✅ 所有依赖包已安装')
except ImportError as e:
    print(f'❌ 缺少依赖包: {e}')
    print('请运行: pip3 install Flask pandas akshare numpy requests')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo ""
    read -p "按任意键退出..."
    exit 1
fi

echo "✅ 启动Flask应用..."
echo "🌐 应用将在 http://127.0.0.1:8082 启动"
echo "📱 在浏览器中打开上述地址即可使用"
echo ""
echo "按 Ctrl+C 停止应用"
echo ""

python3 stock_app_final.py
