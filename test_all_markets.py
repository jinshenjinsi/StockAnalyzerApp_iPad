#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试所有市场的选股功能
验证修复后的系统是否正常工作
"""

import requests
import json
import time

def test_market(market_code, market_name):
    """测试单个市场"""
    print(f"\n🔍 测试 {market_name}")
    print("-" * 50)
    
    try:
        # 测试价值投资策略
        response = requests.post(
            "http://127.0.0.1:8080/api/screen_stocks",
            json={"market": market_code, "strategy": "价值投资"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                stocks = data["data"]
                print(f"✅ 成功筛选出 {len(stocks)} 只股票")
                
                # 显示前3只股票的关键信息
                for i, stock in enumerate(stocks[:3]):
                    print(f"  {i+1}. {stock['symbol']} - {stock['name']}")
                    print(f"     价格: {stock['currency']}{stock['current_price']}")
                    print(f"     支撑位: {stock['currency']}{stock['support_level']}")
                    print(f"     压力位: {stock['currency']}{stock['resistance_level']}")
                    print(f"     评分: {stock['overall_score']}")
                    print(f"     数据源: {stock['data_source']}")
                    print()
                
                # 检查是否有NaN值
                has_nan = False
                for stock in stocks:
                    for key, value in stock.items():
                        if isinstance(value, float) and str(value) == 'nan':
                            has_nan = True
                            print(f"⚠️  发现NaN值: {key} = {value}")
                
                if not has_nan:
                    print("✅ 所有数据都正常，没有NaN值")
                else:
                    print("❌ 发现NaN值，需要进一步修复")
                
                return True
            else:
                print(f"❌ 选股失败: {data.get('error', '未知错误')}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ 请求超时")
        return False
    except requests.exceptions.ConnectionError:
        print("🔌 连接错误，请确保系统正在运行")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 全面测试智能选股系统")
    print("=" * 60)
    
    # 测试三个市场
    markets = [
        ("CN", "🇨🇳 A股市场 (主板+科创板+创业板+中小板)"),
        ("HK", "🇭🇰 港股市场"),
        ("US", "🇺🇸 美股市场")
    ]
    
    results = []
    for market_code, market_name in markets:
        success = test_market(market_code, market_name)
        results.append((market_name, success))
        time.sleep(1)  # 避免请求过快
    
    # 总结测试结果
    print("\n📊 测试结果总结")
    print("=" * 60)
    
    all_success = True
    for market_name, success in results:
        status = "✅ 正常" if success else "❌ 异常"
        print(f"{market_name}: {status}")
        if not success:
            all_success = False
    
    print("\n" + "=" * 60)
    if all_success:
        print("🎊 所有市场测试通过！系统运行正常")
        print("💡 现在可以正常使用智能选股功能了")
    else:
        print("⚠️  部分市场存在问题，需要进一步检查")
    
    print("\n🌐 访问地址:")
    print("   🔍 智能选股: http://127.0.0.1:8080/screener")
    print("   📊 股票排名: http://127.0.0.1:8080/ranking")
    print("   🏠 首页分析: http://127.0.0.1:8080")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        print("💡 请确保智能选股系统正在运行")



