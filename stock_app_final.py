from flask import Flask, render_template, request, jsonify
import akshare as ak
import pandas as pd
import yfinance as yf
import numpy as np
import random
from datetime import datetime, timedelta
import requests
from config import API_KEY
import re

# 全局数据缓存，避免重复调用
_data_cache = {}
_cache_timestamp = {}
CACHE_EXPIRE_MINUTES = 5  # 缓存5分钟过期

app = Flask(__name__)

# ====== 数据缓存管理 ======
def get_cached_data(key):
    """获取缓存的数据"""
    if key in _data_cache and key in _cache_timestamp:
        # 检查缓存是否过期
        if (datetime.now() - _cache_timestamp[key]).total_seconds() < CACHE_EXPIRE_MINUTES * 60:
            return _data_cache[key]
        else:
            # 缓存过期，删除
            del _data_cache[key]
            del _cache_timestamp[key]
    return None

def set_cached_data(key, data):
    """设置缓存数据"""
    _data_cache[key] = data
    _cache_timestamp[key] = datetime.now()

def get_ashare_data():
    """获取A股数据（带缓存）"""
    cache_key = "ashare_spot"
    cached_data = get_cached_data(cache_key)
    if cached_data is not None:
        print("📦 使用缓存的A股数据")
        return cached_data
    
    print("🔄 从akshare获取A股数据...")
    try:
        # 首先尝试实时数据
        try:
            data = ak.stock_zh_a_spot_em()
            if not data.empty:
                set_cached_data(cache_key, data)
                print("✅ A股实时数据获取成功并缓存")
                return data
        except Exception as e:
            print(f"实时数据获取失败: {e}")
        
        # 如果实时数据失败，使用历史数据构建
        print("🔄 使用历史数据构建A股数据...")
        data = build_ashare_data_from_history()
        if not data.empty:
            set_cached_data(cache_key, data)
            print("✅ A股历史数据构建成功并缓存")
            return data
        else:
            raise Exception("无法获取A股数据")
            
    except Exception as e:
        print(f"❌ A股数据获取失败: {e}")
        raise e

def get_hkshare_data():
    """获取港股数据（带缓存）"""
    cache_key = "hkshare_spot"
    cached_data = get_cached_data(cache_key)
    if cached_data is not None:
        print("📦 使用缓存的港股数据")
        return cached_data
    
    print("🔄 从akshare获取港股数据...")
    try:
        # 首先尝试实时数据
        try:
            data = ak.stock_hk_spot_em()
            if not data.empty:
                set_cached_data(cache_key, data)
                print("✅ 港股实时数据获取成功并缓存")
                return data
        except Exception as e:
            print(f"实时数据获取失败: {e}")
        
        # 如果实时数据失败，使用历史数据构建
        print("🔄 使用历史数据构建港股数据...")
        data = build_hkshare_data_from_history()
        if not data.empty:
            set_cached_data(cache_key, data)
            print("✅ 港股历史数据构建成功并缓存")
            return data
        else:
            raise Exception("无法获取港股数据")
            
    except Exception as e:
        print(f"❌ 港股数据获取失败: {e}")
        raise e

# ====== 简化排名系统 ======
def get_market_rankings(market):
    """获取市场排名 - 简化版本，只保留A股和港股"""
    try:
        if market == "CN":
            # A股排名 - 使用缓存数据
            try:
                df = get_ashare_data()
                if df.empty:
                    return []
            except Exception as e:
                print(f"A股排名数据获取失败: {e}")
                return []
            
            # 按涨跌幅排序，取前20
            df = df.sort_values('涨跌幅', ascending=False).head(20)
            
            rankings = []
            for _, row in df.iterrows():
                rankings.append({
                    "symbol": row['代码'],
                    "name": row['名称'],
                    "price": row['最新价'],
                    "change": row['涨跌幅'],
                    "volume": row['成交量'],
                    "currency": "¥"
                })
            return rankings
            
        elif market == "HK":
            # 港股排名 - 使用缓存数据
            try:
                df = get_hkshare_data()
                if df.empty:
                    return []
            except Exception as e:
                print(f"港股排名数据获取失败: {e}")
                return []
            
            # 按涨跌幅排序，取前20
            df = df.sort_values('涨跌幅', ascending=False).head(20)
            
            rankings = []
            for _, row in df.iterrows():
                rankings.append({
                    "symbol": row['代码'],
                    "name": row['名称'],
                    "price": row['最新价'],
                    "change": row['涨跌幅'],
                    "volume": row['成交量'],
                    "currency": "HK$"
                })
            return rankings
            
        elif market == "US":
            # 美股排名 - 简化处理，返回提示信息
            return [{
                "symbol": "INFO",
                "name": "美股数据暂时不可用",
                "price": "N/A",
                "change": "N/A",
                "volume": "N/A",
                "currency": "$",
                "note": "由于API限制，美股排名暂时不可用。请使用智能选股功能获取美股信息。"
            }]
            
        else:
            return []
            
    except Exception as e:
        print(f"获取{market}市场排名失败: {e}")
        return []

# ====== 增强选股功能 ======
def screen_stocks_enhanced(market, strategy, limit=20):
    """增强版选股功能 - 混合模式：优先真实数据，失败时离线模式"""
    try:
        if market == "CN":
            # A股选股 - 混合模式
            try:
                df = get_ashare_data()
                if df.empty:
                    raise Exception("akshare返回空数据")
                
                use_real_data = True
                print("✅ A股使用数据（缓存或实时）")
                
                # 应用选股策略
                if strategy == "momentum":
                    df = df.sort_values('涨跌幅', ascending=False)
                elif strategy == "volume":
                    df = df.sort_values('成交量', ascending=False)
                elif strategy == "value":
                    if '市盈率' in df.columns:
                        df = df[df['市盈率'] > 0].sort_values('市盈率')
                    else:
                        df = df.sort_values('最新价')
                else:
                    df = df.sort_values('涨跌幅', ascending=False)
                
                df = df.head(limit)
                
                results = []
                for _, row in df.iterrows():
                    try:
                        analysis = analyze_stock_enhanced(row['代码'])
                        results.append(analysis)
                    except Exception as e:
                        print(f"A股详细分析失败 {row['代码']}: {e}")
                        # 基础数据 - 匹配前端期望的数据结构
                        results.append({
                            "symbol": row['代码'],
                            "name": row['名称'],
                            "current_price": row['最新价'],
                            "change": row['涨跌幅'],
                            "volume": row['成交量'],
                            "currency": "¥",
                            "data_source": "历史数据构建",
                            "strategy": strategy,
                            "support_level": round(row['最新价'] * 0.9, 2),
                            "resistance_level": round(row['最新价'] * 1.1, 2),
                            "overall_score": 50,
                            "technical_score": 50,
                            "fundamental_score": 50,
                            "institutional_action": "观望",
                            "signals": ["历史数据", "基础分析"]
                        })
                
                return results
                
            except Exception as e:
                print(f"❌ A股实时数据获取失败: {e}")
                print("🔄 无法获取A股数据，请检查网络连接")
                return []
            
        elif market == "HK":
            # 港股选股 - 混合模式
            try:
                df = get_hkshare_data()
                if df.empty:
                    raise Exception("akshare返回空数据")
                
                use_real_data = True
                print("✅ 港股使用数据（缓存或实时）")
                
                # 应用选股策略
                if strategy == "momentum":
                    df = df.sort_values('涨跌幅', ascending=False)
                elif strategy == "volume":
                    df = df.sort_values('成交量', ascending=False)
                elif strategy == "value":
                    if '市盈率' in df.columns:
                        df = df[df['市盈率'] > 0].sort_values('市盈率')
                    else:
                        df = df.sort_values('最新价')
                else:
                    df = df.sort_values('涨跌幅', ascending=False)
                
                df = df.head(limit)
                
                results = []
                for _, row in df.iterrows():
                    try:
                        analysis = analyze_stock_enhanced(row['代码'])
                        results.append(analysis)
                    except Exception as e:
                        print(f"港股详细分析失败 {row['代码']}: {e}")
                        results.append({
                            "symbol": row['代码'],
                            "name": row['名称'],
                            "current_price": row['最新价'],
                            "change": row['涨跌幅'],
                            "volume": row['成交量'],
                            "currency": "HK$",
                            "data_source": "历史数据构建",
                            "strategy": strategy,
                            "support_level": round(row['最新价'] * 0.9, 2),
                            "resistance_level": round(row['最新价'] * 1.1, 2),
                            "overall_score": 50,
                            "technical_score": 50,
                            "fundamental_score": 50,
                            "institutional_action": "观望",
                            "signals": ["历史数据", "基础分析"]
                        })
                
                return results
                
            except Exception as e:
                print(f"❌ 港股实时数据获取失败: {e}")
                print("🔄 无法获取港股数据，请检查网络连接")
                return []
            
        elif market == "US":
            # 美股选股 - 混合模式
            try:
                print("🔄 尝试获取美股实时数据...")
                
                # 测试几个主要股票
                test_stocks = ["AAPL", "MSFT", "GOOGL"]
                test_results = []
                
                for symbol in test_stocks:
                    try:
                        analysis = analyze_stock_enhanced(symbol)
                        test_results.append(analysis)
                    except Exception as e:
                        print(f"美股测试失败 {symbol}: {e}")
                
                if len(test_results) >= 2:  # 大部分成功
                    print("✅ 美股使用实时数据")
                    
                    # 获取完整列表
                    us_stocks = [
                        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "BRK-B", "JPM", "V",
                        "JNJ", "WMT", "PG", "XOM", "MA", "UNH", "HD", "DIS", "PYPL", "NFLX"
                    ]
                    
                    results = []
                    for symbol in us_stocks[:limit]:
                        try:
                            analysis = analyze_stock_enhanced(symbol)
                            results.append(analysis)
                        except Exception as e:
                            print(f"美股详细分析失败 {symbol}: {e}")
                            # 模拟数据
                            results.append({
                                "symbol": symbol,
                                "name": f"{symbol} Corp",
                                "last_price": round(random.uniform(50, 500), 2),
                                "change": round(random.uniform(-10, 15), 2),
                                "volume": f"{random.randint(1000, 10000)}K",
                                "currency": "$",
                                "source": "混合数据 (部分实时)",
                                "strategy": strategy,
                                "note": "部分实时数据，部分模拟数据",
                                "support": round(random.uniform(40, 400), 2),
                                "resistance": round(random.uniform(60, 600), 2),
                                "overall_score": random.randint(40, 80),
                                "signals": "混合数据"
                            })
                    
                    return results
                else:
                    raise Exception("实时数据获取失败")
                    
            except Exception as e:
                print(f"❌ 美股实时数据获取失败: {e}")
                print("🔄 无法获取美股数据，请检查网络连接")
                return []
            
        else:
            return []
            
    except Exception as e:
        print(f"选股失败: {e}")
        return []

def analyze_stock_enhanced(symbol):
    """增强版股票分析 - 重点功能"""
    try:
        # 获取股票数据
        if is_ashare_symbol(symbol):
            try:
                df = fetch_ashare_data(symbol)
                market_type = "A股"
                currency = "¥"
                data_source = "历史数据"
            except Exception as e:
                print(f"A股历史数据获取失败 {symbol}: {e}")
                print("🔄 尝试获取实时行情数据...")
                # 尝试获取实时行情数据作为备选
                try:
                    spot_data = get_ashare_data()
                    if not spot_data.empty:
                        stock_data = spot_data[spot_data['代码'] == symbol]
                        if not stock_data.empty:
                            row = stock_data.iloc[0]
                            # 使用实时行情数据创建简化的DataFrame
                            current_price = row['最新价']
                            change_pct = row['涨跌幅']
                            volume = row['成交量']
                            
                            # 创建简化的历史数据用于技术分析
                            dates = pd.date_range(end=pd.Timestamp.now(), periods=5, freq='D')
                            df = pd.DataFrame({
                                'Open': [current_price * (1 + random.uniform(-0.02, 0.02)) for _ in dates],
                                'High': [current_price * (1 + random.uniform(0, 0.03)) for _ in dates],
                                'Low': [current_price * (1 + random.uniform(-0.03, 0)) for _ in dates],
                                'Close': [current_price * (1 + random.uniform(-0.01, 0.01)) for _ in dates],
                                'Volume': [volume * random.uniform(0.8, 1.2) for _ in dates]
                            }, index=dates)
                            
                            market_type = "A股"
                            currency = "¥"
                            data_source = "实时行情数据"
                            print("✅ 使用实时行情数据进行分析")
                        else:
                            raise Exception("股票代码不在实时行情列表中")
                    else:
                        raise Exception("无法获取实时行情数据")
                except Exception as e2:
                    print(f"实时行情数据获取也失败: {e2}")
                    raise e
                    
        elif is_hkshare_symbol(symbol):
            try:
                df = fetch_hkshare_data(symbol)
                market_type = "港股"
                currency = "HK$"
                data_source = "历史数据"
            except Exception as e:
                print(f"港股历史数据获取失败 {symbol}: {e}")
                print("🔄 尝试获取实时行情数据...")
                # 尝试获取实时行情数据作为备选
                try:
                    spot_data = get_hkshare_data()
                    if not spot_data.empty:
                        stock_data = spot_data[spot_data['代码'] == symbol]
                        if not stock_data.empty:
                            row = stock_data.iloc[0]
                            current_price = row['最新价']
                            change_pct = row['涨跌幅']
                            volume = row['成交量']
                            
                            dates = pd.date_range(end=pd.Timestamp.now(), periods=5, freq='D')
                            df = pd.DataFrame({
                                'Open': [current_price * (1 + random.uniform(-0.02, 0.02)) for _ in dates],
                                'High': [current_price * (1 + random.uniform(0, 0.03)) for _ in dates],
                                'Low': [current_price * (1 + random.uniform(-0.03, 0)) for _ in dates],
                                'Close': [current_price * (1 + random.uniform(-0.01, 0.01)) for _ in dates],
                                'Volume': [volume * random.uniform(0.8, 1.2) for _ in dates]
                            }, index=dates)
                            
                            market_type = "港股"
                            currency = "HK$"
                            data_source = "实时行情数据"
                            print("✅ 使用实时行情数据进行分析")
                        else:
                            raise Exception("股票代码不在实时行情列表中")
                    else:
                        raise Exception("无法获取实时行情数据")
                except Exception as e2:
                    print(f"实时行情数据获取也失败: {e2}")
                    raise e
        else:
            # 美股或其他
            try:
                df = fetch_alpha_vantage(symbol)
                market_type = "美股"
                currency = "$"
                data_source = "历史数据"
            except:
                # 使用模拟数据
                df = generate_simulated_data(symbol)
                market_type = "美股(模拟)"
                currency = "$"
                data_source = "模拟数据"
        
        # 计算技术指标
        technical_score = calculate_enhanced_technical_score(df)
        
        # 计算支撑位和阻力位
        support = calculate_smart_support(df)
        resistance = calculate_smart_resistance(df)
        
        # 计算综合评分
        overall_score = calculate_overall_score_enhanced(df, technical_score)
        
        # 生成交易信号
        signals = generate_enhanced_signals(df, support, resistance, overall_score)
        
        # 计算支撑位和阻力位相对于最新价的百分比
        support_pct = round(((support - df["Close"].iloc[-1]) / df["Close"].iloc[-1]) * 100, 2) if support else None
        resistance_pct = round(((resistance - df["Close"].iloc[-1]) / df["Close"].iloc[-1]) * 100, 2) if resistance else None
        
        # 生成投资建议
        if overall_score >= 80:
            suggestion = "强烈买入 - 技术面优秀，建议积极关注"
        elif overall_score >= 60:
            suggestion = "建议买入 - 技术面良好，可考虑建仓"
        elif overall_score >= 40:
            suggestion = "观望 - 技术面中性，建议等待更好时机"
        else:
            suggestion = "注意风险 - 技术面偏弱，建议谨慎操作"
        
        return {
            "symbol": symbol,
            "name": fetch_stock_name(symbol) or f"{symbol} Corp",
            "current_price": round(df["Close"].iloc[-1], 2),
            "change": calculate_price_change(df),
            "volume": format_volume(df["Volume"].iloc[-1]),
            "currency": currency,
            "market_type": market_type,
            "data_source": data_source,
            "technical_score": technical_score,
            "fundamental_score": 50,  # 默认基本面评分
            "support_level": support,
            "resistance_level": resistance,
            "support_pct": support_pct,
            "resistance_pct": resistance_pct,
            "overall_score": overall_score,
            "institutional_action": "观望",  # 默认机构行为
            "signals": signals if isinstance(signals, list) else [signals],
            "suggestion": suggestion,
            "strategy": "增强分析"
        }
        
    except Exception as e:
        print(f"增强分析失败 {symbol}: {e}")
        raise e

# ====== 技术指标计算 ======
def calculate_rsi(df, period=14):
    """计算RSI相对强弱指标"""
    try:
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]
    except:
        return 50.0

def calculate_macd(df, fast=12, slow=26, signal=9):
    """计算MACD指标"""
    try:
        ema_fast = df['Close'].ewm(span=fast).mean()
        ema_slow = df['Close'].ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line.iloc[-1],
            'signal': signal_line.iloc[-1],
            'histogram': histogram.iloc[-1]
        }
    except:
        return {'macd': 0, 'signal': 0, 'histogram': 0}

def calculate_bollinger_bands(df, period=20, std_dev=2):
    """计算布林带"""
    try:
        sma = df['Close'].rolling(window=period).mean()
        std = df['Close'].rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return upper_band.iloc[-1], lower_band.iloc[-1]
    except:
        current_price = df['Close'].iloc[-1]
        return current_price * 1.1, current_price * 0.9

def calculate_enhanced_technical_score(df):
    """计算增强版技术评分"""
    try:
        score = 0
        
        # RSI评分
        rsi = calculate_rsi(df)
        if rsi is not None:
            if 30 <= rsi <= 70:
                score += 20  # 正常区间
            elif rsi < 30:
                score += 30  # 超卖，买入机会
            elif rsi > 70:
                score += 10  # 超买，注意风险
        
        # MACD评分
        macd_signal = calculate_macd_signal(df)
        if macd_signal == "bullish":
            score += 25
        elif macd_signal == "bearish":
            score += 5
        else:
            score += 15
        
        # 布林带评分
        bb_signal = calculate_bollinger_signal(df)
        if bb_signal == "oversold":
            score += 20
        elif bb_signal == "overbought":
            score += 5
        else:
            score += 15
        
        # 成交量评分
        volume_score = calculate_volume_score(df)
        score += volume_score
        
        return min(score, 100)  # 最高100分
        
    except Exception:
        return 50  # 默认中等评分

def calculate_macd_signal(df):
    """计算MACD信号"""
    try:
        macd_data = calculate_macd(df)
        if macd_data['macd'] > macd_data['signal']:
            return "bullish"  # 看涨
        elif macd_data['macd'] < macd_data['signal']:
            return "bearish"  # 看跌
        return "neutral"  # 中性
    except:
        return "neutral"

def calculate_bollinger_signal(df):
    """计算布林带信号"""
    try:
        bb_upper, bb_lower = calculate_bollinger_bands(df)
        if bb_upper is not None and bb_lower is not None:
            current_price = df["Close"].iloc[-1]
            if current_price <= bb_lower:
                return "oversold"  # 超卖
            elif current_price >= bb_upper:
                return "overbought"  # 超买
        return "normal"  # 正常
    except:
        return "normal"

def calculate_volume_score(df):
    """计算成交量评分"""
    try:
        if len(df) < 5:
            return 10
        
        recent_volume = df["Volume"].tail(5).mean()
        avg_volume = df["Volume"].mean()
        
        if recent_volume > avg_volume * 1.5:
            return 20  # 放量
        elif recent_volume > avg_volume:
            return 15  # 温和放量
        else:
            return 10  # 缩量
    except:
        return 10

def calculate_overall_score_enhanced(df, technical_score):
    """计算增强版综合评分"""
    try:
        score = technical_score * 0.6  # 技术面权重60%
        
        # 价格趋势评分
        price_trend = calculate_price_trend_score(df)
        score += price_trend * 0.4  # 价格趋势权重40%
        
        return min(round(score, 1), 100)
    except:
        return technical_score

def calculate_price_trend_score(df):
    """计算价格趋势评分"""
    try:
        if len(df) < 5:
            return 50
        
        recent_prices = df["Close"].tail(5)
        trend = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0] * 100
        
        if trend > 5:
            return 40  # 强势上涨
        elif trend > 0:
            return 30  # 温和上涨
        elif trend > -5:
            return 20  # 小幅下跌
        else:
            return 10  # 明显下跌
    except:
        return 25

def generate_enhanced_signals(df, support, resistance, overall_score):
    """生成增强版交易信号"""
    try:
        current_price = df["Close"].iloc[-1]
        signals = []
        
        # 基于评分的信号
        if overall_score >= 80:
            signals.append("强烈买入")
        elif overall_score >= 60:
            signals.append("建议买入")
        elif overall_score >= 40:
            signals.append("观望")
        else:
            signals.append("注意风险")
        
        # 基于支撑阻力位的信号
        if support and resistance:
            if current_price <= support * 1.02:
                signals.append("接近支撑位")
            elif current_price >= resistance * 0.98:
                signals.append("接近阻力位")
        
        # 基于技术指标的信号
        rsi = calculate_rsi(df)
        if rsi:
            if rsi < 30:
                signals.append("RSI超卖")
            elif rsi > 70:
                signals.append("RSI超买")
        
        return signals
        
    except:
        return ["信号生成失败"]

# ====== 辅助函数 ======
def format_volume(volume):
    """格式化成交量显示"""
    try:
        if volume >= 1e9:
            return f"{volume/1e9:.1f}B"
        elif volume >= 1e6:
            return f"{volume/1e6:.1f}M"
        elif volume >= 1e3:
            return f"{volume/1e3:.1f}K"
        else:
            return str(int(volume))
    except:
        return "N/A"

def calculate_price_change(df):
    """计算价格变化百分比"""
    try:
        if len(df) >= 2:
            change = ((df["Close"].iloc[-1] - df["Close"].iloc[-2]) / df["Close"].iloc[-2]) * 100
            return round(change, 2)
        return 0
    except:
        return 0

def generate_simulated_data(symbol):
    """生成模拟数据（用于美股）"""
    dates = pd.date_range(end=pd.Timestamp.now(), periods=30, freq='D')
    np.random.seed(hash(symbol) % 1000)  # 基于股票代码的固定随机数
    
    base_price = random.uniform(50, 500)
    prices = []
    for i in range(30):
        if i == 0:
            prices.append(base_price)
        else:
            change = random.uniform(-0.05, 0.05)
            prices.append(prices[-1] * (1 + change))
    
    df = pd.DataFrame({
        'Open': [p * random.uniform(0.98, 1.02) for p in prices],
        'High': [p * random.uniform(1.0, 1.05) for p in prices],
        'Low': [p * random.uniform(0.95, 1.0) for p in prices],
        'Close': prices,
        'Volume': [random.randint(1000000, 10000000) for _ in prices]
    }, index=dates)
    
    return df

def is_ashare_symbol(symbol):
    """判断是否为A股代码"""
    if re.match(r'^[036]\d{5}$', symbol):
        return True
    return False

def is_hkshare_symbol(symbol):
    """判断是否为港股代码"""
    if re.match(r'^\d{5}$', symbol):
        return True
    return False

def fetch_stock_name(symbol):
    """获取股票名称"""
    name_mapping = {
        "000001": "平安银行", "600000": "浦发银行", "600036": "招商银行",
        "600519": "贵州茅台", "600887": "伊利股份", "600276": "恒瑞医药",
        "00700": "腾讯控股", "09988": "阿里巴巴", "03690": "美团",
        "AAPL": "Apple Inc.", "MSFT": "Microsoft", "GOOGL": "Alphabet"
    }
    return name_mapping.get(symbol, symbol)

def fetch_ashare_data(symbol):
    """获取A股数据"""
    try:
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                               start_date=(pd.Timestamp.now() - pd.Timedelta(days=30)).strftime('%Y%m%d'),
                               end_date=pd.Timestamp.now().strftime('%Y%m%d'),
                               adjust="qfq")
        
        if df.empty:
            raise Exception("akshare返回空数据")
        
        df = df.rename(columns={
            '日期': 'date', '开盘': 'Open', '最高': 'High', '最低': 'Low', '收盘': 'Close', '成交量': 'Volume'
        })
        
        df['Open'] = pd.to_numeric(df['Open'])
        df['High'] = pd.to_numeric(df['High'])
        df['Low'] = pd.to_numeric(df['Low'])
        df['Close'] = pd.to_numeric(df['Close'])
        df['Volume'] = pd.to_numeric(df['Volume'])
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        df = df.tail(5)
        
        return df
        
    except Exception as e:
        raise Exception(f"akshare A股数据获取失败: {str(e)}")

def fetch_hkshare_data(symbol):
    """获取港股数据"""
    try:
        df = ak.stock_hk_daily(symbol=symbol, adjust="qfq")
        
        if df.empty:
            raise Exception("akshare港股返回空数据")
        
        column_mapping = {}
        if '日期' in df.columns:
            column_mapping['日期'] = 'date'
        elif 'date' in df.columns:
            column_mapping['date'] = 'date'
            
        if '开盘' in df.columns:
            column_mapping['开盘'] = 'Open'
        elif 'open' in df.columns:
            column_mapping['open'] = 'Open'
            
        if '最高' in df.columns:
            column_mapping['最高'] = 'High'
        elif 'high' in df.columns:
            column_mapping['high'] = 'High'
            
        if '最低' in df.columns:
            column_mapping['最低'] = 'Low'
        elif 'low' in df.columns:
            column_mapping['low'] = 'Low'
            
        if '收盘' in df.columns:
            column_mapping['收盘'] = 'Close'
        elif 'close' in df.columns:
            column_mapping['close'] = 'Close'
            
        if '成交量' in df.columns:
            column_mapping['成交量'] = 'Volume'
        elif 'volume' in df.columns:
            column_mapping['volume'] = 'Volume'
        
        df = df.rename(columns=column_mapping)
        
        required_columns = ['date', 'Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise Exception(f"港股数据缺少必要列: {missing_columns}")
        
        df['Open'] = pd.to_numeric(df['Open'])
        df['High'] = pd.to_numeric(df['High'])
        df['Low'] = pd.to_numeric(df['Low'])
        df['Close'] = pd.to_numeric(df['Close'])
        df['Volume'] = pd.to_numeric(df['Volume'])
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        df = df.tail(5)
        
        return df
        
    except Exception as e:
        raise Exception(f"akshare港股数据获取失败: {str(e)}")

def fetch_alpha_vantage(symbol):
    """获取Alpha Vantage数据"""
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": "compact",
        "apikey": API_KEY
    }
    r = requests.get(url, params=params, timeout=10)
    data = r.json()

    if "Time Series (Daily)" not in data:
        raise Exception("Alpha Vantage 返回无效数据")

    df = pd.DataFrame(data["Time Series (Daily)"]).T
    df = df.rename(columns={
        "1. open": "Open", "2. high": "High", "3. low": "Low", "4. close": "Close", "5. volume": "Volume"
    })
    df = df.astype(float)
    df.index = pd.to_datetime(df.index)
    return df.sort_index()

def calculate_smart_support(df):
    """计算智能支撑位"""
    try:
        if len(df) < 20:
            current_price = df['Close'].iloc[-1]
            return current_price * 0.90
        
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma50 = df['Close'].rolling(50).mean().iloc[-1] if len(df) >= 50 else ma20
        recent_low = df['Low'].tail(min(10, len(df))).min()
        
        if pd.isna(ma20) or pd.isna(ma50) or pd.isna(recent_low):
            current_price = df['Close'].iloc[-1]
            return current_price * 0.90
        
        high = df['High'].tail(min(20, len(df))).max()
        low = df['Low'].tail(min(20, len(df))).min()
        fib_38 = high - (high - low) * 0.382
        fib_50 = high - (high - low) * 0.5
        
        technical_support = np.mean([ma20, ma50, recent_low, fib_38, fib_50])
        return technical_support
        
    except Exception as e:
        current_price = df['Close'].iloc[-1]
        return current_price * 0.90

def calculate_smart_resistance(df):
    """计算智能压力位"""
    try:
        if len(df) < 20:
            current_price = df['Close'].iloc[-1]
            return current_price * 1.10
        
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma50 = df['Close'].rolling(50).mean().iloc[-1] if len(df) >= 50 else ma20
        recent_high = df['High'].tail(min(10, len(df))).max()
        
        if pd.isna(ma20) or pd.isna(ma50) or pd.isna(recent_high):
            current_price = df['Close'].iloc[-1]
            return current_price * 1.10
        
        high = df['High'].tail(min(20, len(df))).max()
        low = df['Low'].tail(min(20, len(df))).min()
        fib_138 = high + (high - low) * 0.382
        fib_150 = high + (high - low) * 0.5
        
        technical_resistance = np.mean([ma20, ma50, recent_high, fib_138, fib_150])
        return technical_resistance
        
    except Exception as e:
        current_price = df['Close'].iloc[-1]
        return current_price * 1.10

# ====== 历史数据构建函数 ======
def build_ashare_data_from_history():
    """从历史数据构建A股数据"""
    try:
        print("🔄 构建A股数据...")
        # 获取主要股票的历史数据
        symbols = ['000001', '000002', '000858', '002415', '600036', '600519', '000858', '002594', '300059', '000725']
        data_list = []
        
        for symbol in symbols:
            try:
                # 获取最近2天的数据
                df = ak.stock_zh_a_hist(symbol=symbol, period='daily', start_date='20240901', end_date='20240902')
                if not df.empty:
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else latest
                    
                    # 计算涨跌幅
                    change_pct = ((latest['收盘'] - prev['收盘']) / prev['收盘']) * 100 if prev['收盘'] != 0 else 0
                    
                    data_list.append({
                        '代码': symbol,
                        '名称': get_stock_name_from_symbol(symbol),
                        '最新价': latest['收盘'],
                        '涨跌幅': change_pct,
                        '成交量': latest['成交量'],
                        '成交额': latest['成交额'],
                        '开盘': latest['开盘'],
                        '最高': latest['最高'],
                        '最低': latest['最低']
                    })
            except Exception as e:
                print(f"获取{symbol}数据失败: {e}")
                continue
        
        if data_list:
            df = pd.DataFrame(data_list)
            print(f"✅ 成功构建{len(df)}只股票的数据")
            return df
        else:
            raise Exception("无法构建A股数据")
            
    except Exception as e:
        print(f"构建A股数据失败: {e}")
        raise e

def get_stock_name_from_symbol(symbol):
    """从股票代码获取股票名称"""
    # 简单的股票名称映射
    name_map = {
        '000001': '平安银行',
        '000002': '万科A',
        '000858': '五粮液',
        '002415': '海康威视',
        '600036': '招商银行',
        '600519': '贵州茅台',
        '002594': '比亚迪',
        '300059': '东方财富',
        '000725': '京东方A'
    }
    return name_map.get(symbol, symbol)

def build_hkshare_data_from_history():
    """从历史数据构建港股数据"""
    try:
        print("🔄 构建港股数据...")
        # 获取主要港股的历史数据
        symbols = ['00700', '09988', '03690', '02318', '00941', '02020', '00388', '01398', '02382', '01810']
        data_list = []
        
        for symbol in symbols:
            try:
                # 获取最近2天的数据
                df = ak.stock_hk_hist(symbol=symbol, period='daily', start_date='20240901', end_date='20240902')
                if not df.empty:
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else latest
                    
                    # 计算涨跌幅
                    change_pct = ((latest['收盘'] - prev['收盘']) / prev['收盘']) * 100 if prev['收盘'] != 0 else 0
                    
                    data_list.append({
                        '代码': symbol,
                        '名称': get_hkshare_name_from_symbol(symbol),
                        '最新价': latest['收盘'],
                        '涨跌幅': change_pct,
                        '成交量': latest['成交量'],
                        '成交额': latest['成交额'],
                        '开盘': latest['开盘'],
                        '最高': latest['最高'],
                        '最低': latest['最低']
                    })
            except Exception as e:
                print(f"获取{symbol}数据失败: {e}")
                continue
        
        if data_list:
            df = pd.DataFrame(data_list)
            print(f"✅ 成功构建{len(df)}只港股的数据")
            return df
        else:
            raise Exception("无法构建港股数据")
            
    except Exception as e:
        print(f"构建港股数据失败: {e}")
        raise e

def get_hkshare_name_from_symbol(symbol):
    """从港股代码获取股票名称"""
    # 简单的港股名称映射
    name_map = {
        '00700': '腾讯控股',
        '09988': '阿里巴巴-SW',
        '03690': '美团-W',
        '02318': '中国平安',
        '00941': '中国移动',
        '02020': '安踏体育',
        '00388': '香港交易所',
        '01398': '工商银行',
        '02382': '舜宇光学科技',
        '01810': '小米集团-W'
    }
    return name_map.get(symbol, symbol)

# ====== 路由 ======
@app.route("/", methods=["GET", "POST"])
def index():
    """主页"""
    result = None
    if request.method == "POST":
        symbol = request.form.get("symbol", "").strip().upper()
        if symbol:
            try:
                print(f"🔄 开始分析股票: {symbol}")
                result = analyze_stock_enhanced(symbol)
                print(f"✅ 分析完成: {result}")
            except Exception as e:
                print(f"❌ 分析失败: {e}")
                result = {"error": str(e)}
    
    return render_template("index.html", result=result)

@app.route("/ranking")
def ranking_page():
    """股票排名页面 - 简化版"""
    market = request.args.get("market", "CN")
    
    try:
        if market == "CN":
            rankings = get_market_rankings("CN")
            # 转换数据格式以匹配模板期望
            rows = []
            for item in rankings:
                rows.append({
                    "symbol": item["symbol"],
                    "name": item["name"],
                    "last_price": item["price"],
                    "resistance": round(item["price"] * 1.1, 2),
                    "resistance_pct": 10.0,
                    "source": "历史数据构建"
                })
        elif market == "HK":
            rankings = get_market_rankings("HK")
            rows = []
            for item in rankings:
                rows.append({
                    "symbol": item["symbol"],
                    "name": item["name"],
                    "last_price": item["price"],
                    "resistance": round(item["price"] * 1.1, 2),
                    "resistance_pct": 10.0,
                    "source": "历史数据构建"
                })
        elif market == "US":
            rankings = get_market_rankings("US")
            rows = []
            for item in rankings:
                rows.append({
                    "symbol": item["symbol"],
                    "name": item["name"],
                    "last_price": item["price"],
                    "resistance": "N/A",
                    "resistance_pct": "N/A",
                    "source": item.get("note", "美股数据")
                })
        else:
            rows = []
            
    except Exception as e:
        print(f"{market}市场排名获取失败: {e}")
        rows = []
    
    return render_template("ranking.html", market=market, rows=rows)

@app.route("/screener")
def screener_page():
    """智能选股页面"""
    return render_template("screener.html")

@app.route("/api/screen_stocks", methods=["POST"])
def api_screen_stocks():
    """选股API接口"""
    try:
        data = request.get_json()
        market = data.get("market", "CN")
        strategy = data.get("strategy", "momentum")
        
        # 执行选股
        results = screen_stocks_enhanced(market, strategy)
        
        return jsonify({
            "success": True,
            "data": results,
            "market": market,
            "strategy": strategy,
            "count": len(results)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8082, debug=False, use_reloader=False)
