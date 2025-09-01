#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络环境检测脚本
检测akshare、yfinance等数据源的连接状态
"""

import requests
import time

def test_network_connection():
    """测试网络连接状态"""
    print("🔍 检测网络连接状态...")
    
    # 测试基本网络连接
    test_urls = [
        "https://www.baidu.com",
        "https://www.google.com",
        "https://www.alphavantage.co",
        "https://query1.finance.yahoo.com"
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=5)
            print(f"✅ {url}: 连接正常 (状态码: {response.status_code})")
        except Exception as e:
            print(f"❌ {url}: 连接失败 - {str(e)}")
    
    print("\n" + "="*50)
    
    # 测试代理设置
    print("🔍 检测代理设置...")
    try:
        proxies = requests.get("https://httpbin.org/ip", timeout=5).json()
        print(f"✅ 当前IP: {proxies.get('origin', '未知')}")
    except Exception as e:
        print(f"❌ IP检测失败: {str(e)}")
    
    # 测试akshare数据源
    print("\n🔍 测试akshare数据源...")
    try:
        import akshare as ak
        print("✅ akshare模块导入成功")
        
        # 测试A股数据获取
        start_time = time.time()
        df = ak.stock_zh_a_spot_em()
        end_time = time.time()
        
        if not df.empty:
            print(f"✅ A股数据获取成功: {len(df)}行数据")
            print(f"⏱️  耗时: {end_time - start_time:.2f}秒")
        else:
            print("⚠️  A股数据为空")
            
    except Exception as e:
        print(f"❌ akshare测试失败: {str(e)}")
    
    # 测试yfinance
    print("\n🔍 测试yfinance数据源...")
    try:
        import yfinance as yf
        print("✅ yfinance模块导入成功")
        
        # 测试美股数据获取
        start_time = time.time()
        ticker = yf.Ticker("AAPL")
        info = ticker.info
        end_time = time.time()
        
        if info:
            print(f"✅ 美股数据获取成功: {info.get('shortName', 'Apple')}")
            print(f"⏱️  耗时: {end_time - start_time:.2f}秒")
        else:
            print("⚠️  美股数据为空")
            
    except Exception as e:
        print(f"❌ yfinance测试失败: {str(e)}")

if __name__ == "__main__":
    test_network_connection()

