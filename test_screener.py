#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试选股功能脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stock_app_final import screen_stocks_enhanced

def test_screener():
    """测试选股功能"""
    print("🔍 测试智能选股功能...")
    
    # 测试A股选股
    print("\n📈 测试A股选股 (动量策略):")
    try:
        results = screen_stocks_enhanced("CN", "momentum", 5)
        print(f"✅ 返回结果数量: {len(results)}")
        if results:
            for i, result in enumerate(results[:3]):
                print(f"  {i+1}. {result.get('symbol', 'N/A')} - {result.get('name', 'N/A')}")
                print(f"     价格: {result.get('last_price', 'N/A')} 涨跌幅: {result.get('change', 'N/A')}%")
        else:
            print("❌ 没有返回结果")
    except Exception as e:
        print(f"❌ A股选股失败: {e}")
    
    # 测试港股选股
    print("\n📈 测试港股选股 (动量策略):")
    try:
        results = screen_stocks_enhanced("HK", "momentum", 5)
        print(f"✅ 返回结果数量: {len(results)}")
        if results:
            for i, result in enumerate(results[:3]):
                print(f"  {i+1}. {result.get('symbol', 'N/A')} - {result.get('name', 'N/A')}")
                print(f"     价格: {result.get('last_price', 'N/A')} 涨跌幅: {result.get('change', 'N/A')}%")
        else:
            print("❌ 没有返回结果")
    except Exception as e:
        print(f"❌ 港股选股失败: {e}")
    
    # 测试美股选股
    print("\n📈 测试美股选股 (动量策略):")
    try:
        results = screen_stocks_enhanced("US", "momentum", 5)
        print(f"✅ 返回结果数量: {len(results)}")
        if results:
            for i, result in enumerate(results[:3]):
                print(f"  {i+1}. {result.get('symbol', 'N/A')} - {result.get('name', 'N/A')}")
                print(f"     价格: {result.get('last_price', 'N/A')} 涨跌幅: {result.get('change', 'N/A')}%")
        else:
            print("❌ 没有返回结果")
    except Exception as e:
        print(f"❌ 美股选股失败: {e}")

if __name__ == "__main__":
    test_screener()

