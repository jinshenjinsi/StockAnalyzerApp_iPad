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
from math import isnan
import os

# 全局数据缓存，避免重复调用
_data_cache = {}
_cache_timestamp = {}
CACHE_EXPIRE_MINUTES = 5  # 缓存5分钟过期

app = Flask(__name__)

# 关闭可能继承的系统代理，避免数据源被错误代理阻断
for _env in ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy"]:
    if _env in os.environ:
        os.environ.pop(_env, None)
# 强制不使用代理
os.environ["NO_PROXY"] = "*"
try:
    import requests as _rq
    import requests.sessions as _rqs
    _rqs.Session.trust_env = False
except Exception:
    pass

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
            # 最后兜底：使用yfinance构建简易现货列表
            print("🔄 使用yfinance兜底构建A股数据...")
            data = build_cn_spot_from_yf()
            if not data.empty:
                set_cached_data(cache_key, data)
                print("✅ A股yfinance兜底成功并缓存")
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
            # 最后兜底：使用yfinance构建简易现货列表
            print("🔄 使用yfinance兜底构建港股数据...")
            data = build_hk_spot_from_yf()
            if not data.empty:
                set_cached_data(cache_key, data)
                print("✅ 港股yfinance兜底成功并缓存")
                return data
            else:
                raise Exception("无法获取港股数据")
            
    except Exception as e:
        print(f"❌ 港股数据获取失败: {e}")
        raise e

# ====== 简化排名系统 ======
def get_market_rankings(market):
    """获取市场排名 - 简化版本，优先使用yfinance"""
    try:
        if market == "CN":
            # A股排名 - 优先使用yfinance兜底
            try:
                df = build_cn_spot_from_yf()
                if df.empty:
                    return []
            except Exception as e:
                print(f"A股排名数据获取失败: {e}")
                return []
            
            # 为每只股票计算综合得分并排序
            stock_scores = []
            for _, row in df.iterrows():
                try:
                    # 获取历史数据进行评分
                    hist_data = fetch_ashare_data(row['代码'])
                    if not hist_data.empty:
                        overall_score = calculate_overall_score_enhanced(hist_data, calculate_enhanced_technical_score(hist_data))
                    else:
                        # 如果无法获取历史数据，使用基础评分
                        overall_score = 50
                except Exception as e:
                    print(f"评分计算失败 {row['代码']}: {e}")
                    overall_score = 50
                
                stock_scores.append({
                    'row': row,
                    'score': overall_score
                })
            
            # 按综合得分排序，取前20
            stock_scores.sort(key=lambda x: x['score'], reverse=True)
            top_stocks = stock_scores[:20]
            
            rankings = []
            for stock_data in top_stocks:
                row = stock_data['row']
                score = stock_data['score']
                rankings.append({
                    "symbol": row['代码'],
                    "name": row['名称'],
                    "price": row['最新价'],
                    "change": row['涨跌幅'],
                    "volume": row['成交量'],
                    "currency": "¥",
                    "score": score
                })
            return rankings
            
        elif market == "HK":
            # 港股排名 - 优先使用yfinance兜底
            try:
                df = build_hk_spot_from_yf()
                if df.empty:
                    return []
            except Exception as e:
                print(f"港股排名数据获取失败: {e}")
                return []
            
            # 为每只港股计算综合得分并排序
            stock_scores = []
            for _, row in df.iterrows():
                try:
                    # 获取历史数据进行评分
                    hist_data = fetch_hkshare_data(row['代码'])
                    if not hist_data.empty:
                        overall_score = calculate_overall_score_enhanced(hist_data, calculate_enhanced_technical_score(hist_data))
                    else:
                        # 如果无法获取历史数据，使用基础评分
                        overall_score = 50
                except Exception as e:
                    print(f"港股评分计算失败 {row['代码']}: {e}")
                    overall_score = 50
                
                stock_scores.append({
                    'row': row,
                    'score': overall_score
                })
            
            # 按综合得分排序，取前20
            stock_scores.sort(key=lambda x: x['score'], reverse=True)
            top_stocks = stock_scores[:20]
            
            rankings = []
            for stock_data in top_stocks:
                row = stock_data['row']
                score = stock_data['score']
                rankings.append({
                    "symbol": row['代码'],
                    "name": row['名称'],
                    "price": row['最新价'],
                    "change": row['涨跌幅'],
                    "volume": row['成交量'],
                    "currency": "HK$",
                    "score": score
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

# ====== AI选股算法 ======
def calculate_ai_score(df, strategy):
    """计算AI综合评分 - 投资价值导向版本"""
    try:
        # 计算基础评分
        technical_score = calculate_technical_score(df)
        momentum_score = calculate_momentum_score(df)
        risk_score = calculate_risk_score(df)
        strategy_score = calculate_strategy_adjustment(df, strategy)
        
        # 根据策略调整权重分配，专注于投资价值
        if strategy == "momentum":
            # 成长动量策略：寻找高成长潜力的股票
            # 权重：技术面25%，动量45%，风险15%，策略15%
            score = (technical_score * 0.25 + 
                    momentum_score * 0.45 + 
                    risk_score * 0.15 + 
                    strategy_score * 0.15)
                    
        elif strategy == "value":
            # 价值投资策略：寻找被低估的优质股票
            # 权重：技术面20%，动量15%，风险35%，策略30%
            score = (technical_score * 0.20 + 
                    momentum_score * 0.15 + 
                    risk_score * 0.35 + 
                    strategy_score * 0.30)
                    
        elif strategy == "volume":
            # 资金关注策略：寻找资金大量流入的股票
            # 权重：技术面35%，动量25%，风险10%，策略30%
            score = (technical_score * 0.35 + 
                    momentum_score * 0.25 + 
                    risk_score * 0.10 + 
                    strategy_score * 0.30)
                    
        else:  # 默认策略 - 均衡投资
            # 均衡投资策略：平衡各因素，寻找稳健投资机会
            # 权重：技术面30%，动量25%，风险25%，策略20%
            score = (technical_score * 0.30 + 
                    momentum_score * 0.25 + 
                    risk_score * 0.25 + 
                    strategy_score * 0.20)
        
        return min(max(score, 0), 100)  # 限制在0-100范围内
        
    except Exception as e:
        print(f"AI评分计算失败: {e}")
        return 50

def calculate_technical_score(df):
    """计算技术面评分"""
    try:
        score = 0
        
        # RSI评分
        rsi = calculate_rsi(df)
        if rsi is not None:
            if 30 <= rsi <= 70:
                score += 25  # 正常区间
            elif rsi < 30:
                score += 35  # 超卖，买入机会
            elif rsi > 70:
                score += 15  # 超买，注意风险
        
        # MACD评分
        macd_data = calculate_macd(df)
        if macd_data['macd'] > macd_data['signal']:
            score += 25  # 看涨信号
        elif macd_data['macd'] < macd_data['signal']:
            score += 15  # 看跌信号
        else:
            score += 20  # 中性
        
        # 布林带评分
        bb_upper, bb_lower = calculate_bollinger_bands(df)
        if bb_upper is not None and bb_lower is not None:
            current_price = df["Close"].iloc[-1]
            if current_price <= bb_lower * 1.02:
                score += 25  # 接近下轨，超卖
            elif current_price >= bb_upper * 0.98:
                score += 15  # 接近上轨，超买
            else:
                score += 20  # 正常区间
        
        # 成交量评分
        volume_score = calculate_volume_score(df)
        score += volume_score
        
        return min(score, 100)
        
    except Exception as e:
        print(f"技术面评分计算失败: {e}")
        return 50

def calculate_momentum_score(df):
    """计算动量评分"""
    try:
        if len(df) < 20:
            return 50
        
        # 短期动量 (5日)
        short_momentum = (df['Close'].iloc[-1] - df['Close'].iloc[-6]) / df['Close'].iloc[-6] * 100
        
        # 中期动量 (20日)
        medium_momentum = (df['Close'].iloc[-1] - df['Close'].iloc[-21]) / df['Close'].iloc[-21] * 100
        
        # 动量一致性
        if short_momentum > 0 and medium_momentum > 0:
            score = 80  # 双上涨
        elif short_momentum > 0 and medium_momentum < 0:
            score = 60  # 短期反弹
        elif short_momentum < 0 and medium_momentum > 0:
            score = 40  # 短期回调
        else:
            score = 20  # 双下跌
        
        return score
        
    except Exception as e:
        print(f"动量评分计算失败: {e}")
        return 50

def calculate_risk_score(df):
    """计算风险评分"""
    try:
        if len(df) < 20:
            return 50
        
        # 波动率计算
        returns = df['Close'].pct_change().dropna()
        volatility = returns.std() * 100
        
        # 最大回撤
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max * 100
        max_drawdown = abs(drawdown.min())
        
        # 风险评分 (波动率越低，回撤越小，评分越高)
        volatility_score = max(0, 100 - volatility * 2)
        drawdown_score = max(0, 100 - max_drawdown)
        
        risk_score = (volatility_score + drawdown_score) / 2
        return risk_score
        
    except Exception as e:
        print(f"风险评分计算失败: {e}")
        return 50

def calculate_strategy_adjustment(df, strategy):
    """根据策略调整评分 - 投资价值导向版本"""
    try:
        if strategy == "momentum":
            # 成长动量策略：寻找高成长潜力的股票
            score = 0
            if len(df) >= 10:
                # 1. 短期成长性 (5日涨幅)
                if len(df) >= 6:
                    short_change = (df['Close'].iloc[-1] - df['Close'].iloc[-6]) / df['Close'].iloc[-6] * 100
                else:
                    short_change = 0
                
                # 2. 中期成长性 (20日涨幅)
                if len(df) >= 21:
                    medium_change = (df['Close'].iloc[-1] - df['Close'].iloc[-21]) / df['Close'].iloc[-21] * 100
                else:
                    medium_change = 0
                
                # 3. 成长性评分
                if short_change > 10 and medium_change > 15:
                    score += 40  # 双高成长
                elif short_change > 5 and medium_change > 10:
                    score += 30  # 高成长
                elif short_change > 0 and medium_change > 5:
                    score += 20  # 温和成长
                elif short_change > 0 or medium_change > 0:
                    score += 10  # 微成长
                else:
                    score += 0   # 无成长
                
                # 4. 成交量确认
                recent_volume = df['Volume'].tail(5).mean()
                avg_volume = df['Volume'].mean()
                if recent_volume > avg_volume * 2:
                    score += 20  # 放量确认
                elif recent_volume > avg_volume * 1.5:
                    score += 15  # 温和放量
                elif recent_volume > avg_volume:
                    score += 10  # 略放量
                    
            return min(score, 60)  # 最高60分
        
        elif strategy == "value":
            # 价值投资策略：寻找被低估的优质股票
            score = 0
            if len(df) >= 20:
                current_price = df['Close'].iloc[-1]
                
                # 1. 价格相对均线位置（估值水平）
                ma20 = df['Close'].rolling(20).mean().iloc[-1]
                ma50 = df['Close'].rolling(50).mean().iloc[-1] if len(df) >= 50 else ma20
                
                # 2. 价值评分（价格越低，价值越高）
                if current_price < ma20 * 0.8:
                    score += 35  # 严重低估
                elif current_price < ma20 * 0.9:
                    score += 25  # 明显低估
                elif current_price < ma20 * 0.95:
                    score += 15  # 轻微低估
                elif current_price < ma20:
                    score += 10  # 略低估
                else:
                    score += 0   # 高估
                
                # 3. 长期支撑确认
                if current_price < ma50 * 0.85:
                    score += 25  # 长期严重低估
                elif current_price < ma50 * 0.95:
                    score += 15  # 长期低估
                elif current_price < ma50:
                    score += 10  # 长期略低估
                
                # 4. 风险控制（波动率）
                if len(df) >= 20:
                    returns = df['Close'].pct_change().dropna()
                    volatility = returns.std() * 100
                    if volatility < 15:
                        score += 20  # 低风险
                    elif volatility < 25:
                        score += 15  # 中等风险
                    elif volatility < 35:
                        score += 10  # 较高风险
                    else:
                        score += 0   # 高风险
                    
            return min(score, 60)  # 最高60分
        
        elif strategy == "volume":
            # 资金关注策略：寻找资金大量流入的股票
            score = 0
            if len(df) >= 10:
                # 1. 成交量分析
                recent_volume = df['Volume'].tail(5).mean()
                avg_volume = df['Volume'].mean()
                volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
                
                # 2. 资金流入评分
                if volume_ratio > 4:
                    score += 40  # 巨量资金流入
                elif volume_ratio > 3:
                    score += 35  # 大量资金流入
                elif volume_ratio > 2:
                    score += 25  # 明显资金流入
                elif volume_ratio > 1.5:
                    score += 15  # 温和资金流入
                elif volume_ratio > 1:
                    score += 10  # 略资金流入
                else:
                    score += 0   # 资金流出
                
                # 3. 价格突破确认
                if len(df) >= 10:
                    recent_high = df['High'].tail(5).max()
                    prev_high = df['High'].iloc[-10:-5].max()
                    if recent_high > prev_high * 1.05:
                        score += 20  # 强势突破
                    elif recent_high > prev_high * 1.02:
                        score += 15  # 明显突破
                    elif recent_high > prev_high:
                        score += 10  # 轻微突破
                
                # 4. 技术面确认
                if len(df) >= 5:
                    # 连续上涨确认
                    recent_closes = df['Close'].tail(5)
                    if all(recent_closes.iloc[i] >= recent_closes.iloc[i-1] for i in range(1, len(recent_closes))):
                        score += 20  # 连续上涨
                    elif recent_closes.iloc[-1] > recent_closes.iloc[0]:
                        score += 10  # 整体上涨
                        
            return min(score, 60)  # 最高60分
        
        else:  # 默认策略 - 均衡投资
            # 均衡投资策略：平衡各因素，寻找稳健投资机会
            score = 0
            if len(df) >= 20:
                current_price = df['Close'].iloc[-1]
                ma20 = df['Close'].rolling(20).mean().iloc[-1]
                
                # 1. 价格合理性
                if 0.95 <= current_price / ma20 <= 1.05:
                    score += 20  # 价格合理
                elif 0.9 <= current_price / ma20 <= 1.1:
                    score += 15  # 价格较合理
                else:
                    score += 10  # 价格偏离
                
                # 2. 稳定性
                if len(df) >= 20:
                    returns = df['Close'].pct_change().dropna()
                    volatility = returns.std() * 100
                    if volatility < 20:
                        score += 20  # 高稳定性
                    elif volatility < 30:
                        score += 15  # 中等稳定性
                    else:
                        score += 10  # 低稳定性
                
                # 3. 趋势性
                if len(df) >= 10:
                    recent_trend = (df['Close'].iloc[-1] - df['Close'].iloc[-10]) / df['Close'].iloc[-10] * 100
                    if 5 <= recent_trend <= 15:
                        score += 20  # 稳健上涨
                    elif 0 <= recent_trend <= 20:
                        score += 15  # 温和上涨
                    else:
                        score += 10  # 趋势不明
                        
            return min(score, 60)  # 最高60分
        
    except Exception as e:
        print(f"策略调整计算失败: {e}")
        return 30

# ====== 增强选股功能 ======
def screen_stocks_enhanced(market, strategy, limit=20):
    """增强版选股功能 - 混合模式：优先真实数据，失败时离线模式"""
    try:
        if market == "CN":
            # A股选股 - 优先使用yfinance
            try:
                df = build_cn_spot_from_yf()
                if df.empty:
                    raise Exception("yfinance返回空数据")
                
                use_real_data = True
                print("✅ A股使用数据（缓存或实时）")
                
                # 应用AI选股策略
                print("🤖 使用AI算法进行智能选股...")
                
                # 为每只股票计算AI评分
                stock_scores = []
                for _, row in df.iterrows():
                    try:
                        # 获取历史数据进行AI分析
                        hist_data = fetch_ashare_data(row['代码'])
                        if not hist_data.empty:
                            ai_score = calculate_ai_score(hist_data, strategy)
                            stock_scores.append({
                                'row': row,
                                'ai_score': ai_score
                            })
                        else:
                            # 如果无法获取历史数据，使用基础评分
                            stock_scores.append({
                                'row': row,
                                'ai_score': 50
                            })
                    except Exception as e:
                        print(f"AI评分计算失败 {row['代码']}: {e}")
                        stock_scores.append({
                            'row': row,
                            'ai_score': 50
                        })
                
                # 按AI评分排序
                stock_scores.sort(key=lambda x: x['ai_score'], reverse=True)
                top_stocks = stock_scores[:limit]
                
                print(f"✅ AI选股完成，筛选出 {len(top_stocks)} 只优质股票")
                
                results = []
                for stock_data in top_stocks:
                    row = stock_data['row']
                    ai_score = stock_data['ai_score']
                    
                    try:
                        analysis = analyze_stock_enhanced(row['代码'])
                        # 更新AI评分
                        analysis['ai_score'] = ai_score
                        analysis['overall_score'] = max(analysis['overall_score'], ai_score)
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
                            "data_source": "AI智能选股",
                            "strategy": strategy,
                            "support_level": round(row['最新价'] * 0.9, 2),
                            "resistance_level": round(row['最新价'] * 1.1, 2),
                            "overall_score": ai_score,
                            "ai_score": ai_score,
                            "technical_score": ai_score * 0.6,
                            "fundamental_score": ai_score * 0.4,
                            "institutional_action": "AI推荐",
                            "signals": ["AI智能选股", f"综合评分: {ai_score}"]
                        })
                
                return results
                
            except Exception as e:
                print(f"❌ A股实时数据获取失败: {e}")
                print("🔄 无法获取A股数据，请检查网络连接")
                return []
            
        elif market == "HK":
            # 港股选股 - 优先使用yfinance
            try:
                df = build_hk_spot_from_yf()
                if df.empty:
                    raise Exception("yfinance返回空数据")
                
                use_real_data = True
                print("✅ 港股使用数据（缓存或实时）")
                
                # 应用AI选股策略
                print("🤖 使用AI算法进行智能选股...")
                
                # 为每只股票计算AI评分
                stock_scores = []
                for _, row in df.iterrows():
                    try:
                        # 获取历史数据进行AI分析
                        hist_data = fetch_hkshare_data(row['代码'])
                        if not hist_data.empty:
                            ai_score = calculate_ai_score(hist_data, strategy)
                            stock_scores.append({
                                'row': row,
                                'ai_score': ai_score
                            })
                        else:
                            # 如果无法获取历史数据，使用基础评分
                            stock_scores.append({
                                'row': row,
                                'ai_score': 50
                            })
                    except Exception as e:
                        print(f"AI评分计算失败 {row['代码']}: {e}")
                        stock_scores.append({
                            'row': row,
                            'ai_score': 50
                        })
                
                # 按AI评分排序
                stock_scores.sort(key=lambda x: x['ai_score'], reverse=True)
                top_stocks = stock_scores[:limit]
                
                print(f"✅ AI选股完成，筛选出 {len(top_stocks)} 只优质股票")
                
                results = []
                for stock_data in top_stocks:
                    row = stock_data['row']
                    ai_score = stock_data['ai_score']
                    
                    try:
                        analysis = analyze_stock_enhanced(row['代码'])
                        # 更新AI评分
                        analysis['ai_score'] = ai_score
                        analysis['overall_score'] = max(analysis['overall_score'], ai_score)
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
                            "data_source": "AI智能选股",
                            "strategy": strategy,
                            "support_level": round(row['最新价'] * 0.9, 2),
                            "resistance_level": round(row['最新价'] * 1.1, 2),
                            "overall_score": ai_score,
                            "ai_score": ai_score,
                            "technical_score": ai_score * 0.6,
                            "fundamental_score": ai_score * 0.4,
                            "institutional_action": "AI推荐",
                            "signals": ["AI智能选股", f"综合评分: {ai_score}"]
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
                            # 跳过失败的股票，继续分析其他股票
                            continue
                    
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
                            # 基于真实价格创建合理的历史数据
                            price_variation = current_price * 0.01  # 1%的价格波动
                            df = pd.DataFrame({
                                'Open': [current_price - price_variation * 0.5] * 5,
                                'High': [current_price + price_variation] * 5,
                                'Low': [current_price - price_variation] * 5,
                                'Close': [current_price] * 5,
                                'Volume': [volume] * 5
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
                    # 最终备选：尝试通过yfinance获取（映射至 .SZ/.SS）
                    try:
                        yahoo_symbol = to_yahoo_symbol(symbol)
                        if yahoo_symbol:
                            df = fetch_yfinance(yahoo_symbol)
                            market_type = "A股"
                            currency = "¥"
                            data_source = "yfinance映射数据"
                            print("✅ 使用yfinance映射获取A股数据成功")
                        else:
                            raise e
                    except Exception as e3:
                        print(f"yfinance映射获取失败: {e3}")
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
                            # 基于真实价格创建合理的历史数据
                            price_variation = current_price * 0.01  # 1%的价格波动
                            df = pd.DataFrame({
                                'Open': [current_price - price_variation * 0.5] * 5,
                                'High': [current_price + price_variation] * 5,
                                'Low': [current_price - price_variation] * 5,
                                'Close': [current_price] * 5,
                                'Volume': [volume] * 5
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
                    # 最终备选：尝试通过yfinance获取（映射至 .HK）
                    try:
                        yahoo_symbol = to_yahoo_symbol(symbol)
                        if yahoo_symbol:
                            df = fetch_yfinance(yahoo_symbol)
                            market_type = "港股"
                            currency = "HK$"
                            data_source = "yfinance映射数据"
                            print("✅ 使用yfinance映射获取港股数据成功")
                        else:
                            raise e
                    except Exception as e3:
                        print(f"yfinance映射获取失败: {e3}")
                        raise e
        else:
            # 美股或其他
            try:
                # 优先使用yfinance获取美股数据
                df = fetch_yfinance(symbol)
                market_type = "美股"
                currency = "$"
                data_source = "yfinance实时数据"
                print("✅ 使用yfinance获取美股数据成功")
            except Exception as e1:
                print(f"yfinance获取失败: {e1}")
                try:
                    # 备用方案：使用Alpha Vantage
                    df = fetch_alpha_vantage(symbol)
                    market_type = "美股"
                    currency = "$"
                    data_source = "Alpha Vantage历史数据"
                    print("✅ 使用Alpha Vantage获取美股数据成功")
                except Exception as e2:
                    print(f"Alpha Vantage获取失败: {e2}")
                    # 如果两个数据源都失败，抛出异常
                    raise Exception(f"无法获取 {symbol} 的美股数据，请检查股票代码是否正确")
        
        # 计算技术指标
        technical_score = calculate_enhanced_technical_score(df)
        
        # 计算支撑位和阻力位
        support = calculate_smart_support(df)
        resistance = calculate_smart_resistance(df)
        
        # 计算综合评分
        overall_score = calculate_overall_score_enhanced(df, technical_score)
        
        # 生成交易信号
        signals = generate_enhanced_signals(df, support, resistance, overall_score)

        # 扩展：技术信号胜率统计与形态标签
        try:
            history_df = get_history_for_signals(symbol)
            signal_stats, pattern_tags = compute_signal_stats(history_df)
        except Exception as _e:
            signal_stats, pattern_tags = {}, []

        # 扩展：基本面雷达（轻量版：以价格与成交量衍生的稳健度代理指标）
        try:
            radar = compute_radar_metrics(history_df if 'history_df' in locals() else df)
            radar_comment = generate_radar_comment(radar)
        except Exception:
            radar, radar_comment = {}, "数据不足，暂不生成雷达解读"
        
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
        
        # 近60日收盘价（用于前端迷你走势图）
        recent_prices = []
        try:
            tail_df = df.tail(60)
            for idx, row in tail_df.iterrows():
                recent_prices.append(float(row['Close']))
        except Exception:
            recent_prices = []

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
            "strategy": "增强分析",
            "signal_stats": signal_stats,
            "pattern_tags": pattern_tags,
            "radar": radar,
            "radar_comment": radar_comment,
            "recent_prices": recent_prices
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

# ====== 技术信号胜率统计与形态标签 ======
def get_history_for_signals(symbol: str, days: int = 200) -> pd.DataFrame:
    """获取用于统计的历史K线。A股/港股走akshare，美股走yfinance。"""
    try:
        if is_ashare_symbol(symbol):
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily",
                                    start_date=(pd.Timestamp.now() - pd.Timedelta(days=days)).strftime('%Y%m%d'),
                                    end_date=pd.Timestamp.now().strftime('%Y%m%d'), adjust="qfq")
            df = df.rename(columns={'日期':'date','开盘':'Open','最高':'High','最低':'Low','收盘':'Close','成交量':'Volume'})
        elif is_hkshare_symbol(symbol):
            df = ak.stock_hk_hist(symbol=symbol, period='daily',
                                  start_date=(pd.Timestamp.now() - pd.Timedelta(days=days)).strftime('%Y%m%d'),
                                  end_date=pd.Timestamp.now().strftime('%Y%m%d'))
            df = df.rename(columns={'日期':'date','开盘':'Open','最高':'High','最低':'Low','收盘':'Close','成交量':'Volume'})
        else:
            t = yf.Ticker(symbol)
            df = t.history(period=f"{days}d").rename(columns={'Open':'Open','High':'High','Low':'Low','Close':'Close','Volume':'Volume'})
            df['date'] = df.index
        df['date'] = pd.to_datetime(df['date'])
        df = df[['date','Open','High','Low','Close','Volume']].dropna()
        df = df.set_index('date').sort_index()
        return df
    except Exception as e:
        return pd.DataFrame()

def compute_signal_stats(df: pd.DataFrame) -> tuple:
    """计算MACD金叉/死叉，WR(14)超买超卖，放量等信号在2/5/10日后的胜率与平均涨幅；并给出形态标签。"""
    if df is None or df.empty or len(df) < 60:
        return {}, []
    closes = df['Close']
    # MACD
    ema_fast = closes.ewm(span=12).mean()
    ema_slow = closes.ewm(span=26).mean()
    macd = ema_fast - ema_slow
    signal = macd.ewm(span=9).mean()
    macd_cross_up = (macd.shift(1) < signal.shift(1)) & (macd >= signal)
    macd_cross_down = (macd.shift(1) > signal.shift(1)) & (macd <= signal)
    # WR(14)
    period = 14
    highest = df['High'].rolling(period).max()
    lowest = df['Low'].rolling(period).min()
    wr = (highest - closes) / (highest - lowest + 1e-9) * 100
    wr_oversold = wr > 80
    wr_overbought = wr < 20
    # 放量
    vol_ma = df['Volume'].rolling(20).mean()
    vol_spike = df['Volume'] > vol_ma * 1.5

    horizons = [2,5,10]
    signals = {
        'MACD金叉': macd_cross_up,
        'MACD死叉': macd_cross_down,
        'WR超卖': wr_oversold,
        'WR超买': wr_overbought,
        '放量': vol_spike,
    }
    stats = {}
    for name, mask in signals.items():
        idx = mask[mask].index
        if len(idx) == 0:
            continue
        res = {}
        for h in horizons:
            future = []
            for t in idx:
                if t in closes.index and t in closes.index and t in df.index:
                    if t in closes.index and (t in closes.index):
                        pass
                if t not in closes.index:
                    continue
                try:
                    t_next = closes.index.get_loc(t) + h
                    if t_next < len(closes):
                        ret = (closes.iloc[t_next] - closes.loc[t]) / closes.loc[t] * 100
                        future.append(ret)
                except Exception:
                    continue
            if future:
                winrate = sum(1 for r in future if r > 0) / len(future) * 100
                avg = float(np.mean(future))
                res[str(h)] = { 'winrate': round(winrate,2), 'avg': round(avg,2) }
        if res:
            stats[name] = res

    # 形态标签：简单基于近期形态
    tags = []
    try:
        last_close = closes.iloc[-1]
        ma20 = closes.rolling(20).mean().iloc[-1]
        if last_close > ma20:
            tags.append('站上20日线')
        rng = df['High'].tail(10).max() - df['Low'].tail(10).min()
        if rng > 0 and (df['High'].iloc[-1]-df['Low'].iloc[-1]) < rng*0.25:
            tags.append('小阴星/小阳星')
        if df['Close'].iloc[-1] > df['Close'].rolling(60).max().iloc[-2]*0.98:
            tags.append('接近前高')
    except Exception:
        pass

    return stats, tags

def compute_radar_metrics(df: pd.DataFrame) -> dict:
    """生成雷达图五维：盈利能力、成长能力、营运能力、偿债能力、现金流（用价格与波动的代理指标，避免外部财报依赖）。"""
    if df is None or df.empty or len(df) < 60:
        return {}
    closes = df['Close']
    returns = closes.pct_change().dropna()
    # 盈利能力(近60日收益率)
    profitability = max(0, min(100, (closes.iloc[-1]/closes.iloc[-60]-1)*100 + 50))
    # 成长能力(近20日趋势)
    growth = max(0, min(100, (closes.iloc[-1]/closes.iloc[-20]-1)*200 + 50))
    # 营运能力(波动率越低越高)
    vol = returns.std()*100
    operation = max(0, min(100, 100 - vol*2))
    # 偿债能力(最大回撤越小越高)
    cum = (1+returns).cumprod()
    draw = ((cum.cummax()-cum)/cum.cummax()*100).max()
    debt = max(0, min(100, 100 - draw))
    # 现金流(量价配合：量比)
    vol_ratio = df['Volume'].tail(5).mean() / (df['Volume'].rolling(60).mean().iloc[-1] + 1e-9)
    cashflow = max(0, min(100, (vol_ratio-1)*50 + 50))
    return {
        '盈利能力': round(profitability,1),
        '成长能力': round(growth,1),
        '营运能力': round(operation,1),
        '偿债能力': round(debt,1),
        '现金流': round(cashflow,1)
    }

def generate_radar_comment(radar: dict) -> str:
    if not radar:
        return ""
    top = sorted(radar.items(), key=lambda x: x[1], reverse=True)[:2]
    weak = sorted(radar.items(), key=lambda x: x[1])[:1]
    return f"优势：{top[0][0]}、{top[1][0]}；短板：{weak[0][0]}。综合看，可结合支撑/压力位分批操作。"
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

# ====== 美股数据获取 ======
def fetch_yfinance(symbol):
    """使用yfinance获取美股数据"""
    try:
        print(f"🔄 从yfinance获取 {symbol} 数据...")
        ticker = yf.Ticker(symbol)
        
        # 获取最近100天的历史数据
        df = ticker.history(period="100d")
        
        if df.empty:
            raise Exception("yfinance返回空数据")
        
        # 确保列名一致
        df = df.rename(columns={
            'Open': 'Open',
            'High': 'High', 
            'Low': 'Low',
            'Close': 'Close',
            'Volume': 'Volume'
        })
        
        print(f"✅ yfinance数据获取成功: {len(df)} 条记录")
        return df
        
    except Exception as e:
        print(f"❌ yfinance数据获取失败: {e}")
        raise e

def to_yahoo_symbol(symbol: str) -> str:
    """将 A股/港股代码映射为 yfinance 可识别代码。A股: 000001->000001.SZ/ 600xxx->.SS；港股：00700->0700.HK。其他：原样返回。"""
    try:
        # 港股：5位数字，前导0去掉后补齐4位并加 .HK
        if is_hkshare_symbol(symbol):
            num = symbol.lstrip('0')
            num = num.zfill(4)
            return f"{num}.HK"
        # A股：6位数字，0/3 开头为深圳 .SZ，6 开头为上海 .SS
        if is_ashare_symbol(symbol):
            if symbol.startswith('6'):
                return f"{symbol}.SS"
            else:
                return f"{symbol}.SZ"
        # 其他直接返回
        return symbol
    except Exception:
        return symbol

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

# ====== yfinance 兜底：构建CN/HK现货数据（简化版） ======
def build_cn_spot_from_yf():
    """使用 yfinance 兜底构建 A股简化现货列表。仅选取一组代表性股票并计算涨跌幅。"""
    symbols = [
        '600519', '600036', '601318', '600690', '600703',
        '000001', '000002', '000858', '002594', '300750'
    ]
    rows = []
    for s in symbols:
        try:
            ys = to_yahoo_symbol(s)
            df = fetch_yfinance(ys)
            if df is None or df.empty or len(df) < 2:
                continue
            latest = float(df['Close'].iloc[-1])
            prev = float(df['Close'].iloc[-2])
            change_pct = (latest - prev) / prev * 100 if prev != 0 else 0
            volume = float(df['Volume'].iloc[-1]) if 'Volume' in df.columns else 0
            rows.append({
                '代码': s,
                '名称': fetch_stock_name(s),
                '最新价': latest,
                '涨跌幅': change_pct,
                '成交量': volume,
            })
        except Exception:
            continue
    return pd.DataFrame(rows)

def build_hk_spot_from_yf():
    """使用 yfinance 兜底构建 港股简化现货列表。"""
    symbols = ['00700', '09988', '03690', '00388', '02318', '00941', '01299']
    rows = []
    for s in symbols:
        try:
            ys = to_yahoo_symbol(s)
            df = fetch_yfinance(ys)
            if df is None or df.empty or len(df) < 2:
                continue
            latest = float(df['Close'].iloc[-1])
            prev = float(df['Close'].iloc[-2])
            change_pct = (latest - prev) / prev * 100 if prev != 0 else 0
            volume = float(df['Volume'].iloc[-1]) if 'Volume' in df.columns else 0
            rows.append({
                '代码': s,
                '名称': fetch_stock_name(s),
                '最新价': latest,
                '涨跌幅': change_pct,
                '成交量': volume,
            })
        except Exception:
            continue
    return pd.DataFrame(rows)

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
                
                # 确保数据类型正确，转换为Python原生类型
                if result and isinstance(result, dict):
                    for key, value in result.items():
                        if hasattr(value, 'item'):  # numpy类型
                            result[key] = value.item()
                        elif isinstance(value, (list, tuple)):
                            result[key] = [str(v) if hasattr(v, 'item') else v for v in value]
                
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
    # 监听到 0.0.0.0 以便同一局域网设备（如 iPad）访问；默认8083，可用环境变量PORT覆盖
    import os
    port = int(os.environ.get('PORT', 8083))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
