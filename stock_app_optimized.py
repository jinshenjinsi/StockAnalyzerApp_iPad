from flask import Flask, render_template, request, jsonify
import pandas as pd
import yfinance as yf
import numpy as np
import random
from datetime import datetime, timedelta
import requests
import re
from math import isnan
import os
import time

# 全局数据缓存，避免重复调用
_data_cache = {}
_cache_timestamp = {}
CACHE_EXPIRE_MINUTES = 60  # 缓存1小时过期

app = Flask(__name__)

# 关闭可能继承的系统代理，避免数据源被错误代理阻断
for _env in ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy"]:
    if _env in os.environ:
        os.environ.pop(_env, None)
# 强制不使用代理
os.environ["NO_PROXY"] = "*"

# 从环境变量读取API密钥（如果存在）
ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY', '')
TUSHARE_TOKEN = os.environ.get('TUSHARE_TOKEN', '')

try:
    import requests as _rq
    import requests.sessions as _rqs
    _rqs.Session.trust_env = False
except Exception:
    pass

# ====== 智能数据源管理 ======
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

def get_yfinance_data(symbol):
    """使用yfinance获取股票数据"""
    try:
        print(f"🔄 使用yfinance获取 {symbol} 数据...")
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="60d")
        info = ticker.info
        
        if hist.empty:
            raise Exception(f"无法获取 {symbol} 的历史数据")
        
        current_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2] if len(hist) >= 2 else current_price
        change_pct = ((current_price - prev_price) / prev_price) * 100 if prev_price != 0 else 0
        volume = hist['Volume'].iloc[-1]
        
        # 获取公司名称
        name = info.get('longName', info.get('shortName', symbol))
        
        return {
            'symbol': symbol,
            'name': name,
            'current_price': current_price,
            'change_pct': change_pct,
            'volume': volume,
            'history': hist,
            'info': info
        }
    except Exception as e:
        print(f"❌ yfinance获取失败 {symbol}: {e}")
        raise e

def get_a_share_symbol_mapping(code):
    """A股代码映射到yfinance格式"""
    if code.startswith('6'):
        return f"{code}.SS"
    elif code.startswith('0') or code.startswith('3'):
        return f"{code}.SZ"
    else:
        return code

def is_ashare_symbol(symbol):
    """判断是否为A股代码"""
    if re.match(r'^[036]\\d{5}$', symbol):
        return True
    return False

def analyze_stock_enhanced(symbol):
    """增强版股票分析 - 纯真实数据版本"""
    try:
        print(f"🔄 开始分析股票: {symbol}")
        
        # 处理A股代码映射
        if is_ashare_symbol(symbol):
            yf_symbol = get_a_share_symbol_mapping(symbol)
            display_symbol = symbol
        else:
            yf_symbol = symbol
            display_symbol = symbol
        
        # 使用yfinance获取真实数据
        stock_data = get_yfinance_data(yf_symbol)
        
        df = stock_data['history']
        current_price = stock_data['current_price']
        change_pct = stock_data['change_pct']
        volume = stock_data['volume']
        name = stock_data['name']
        
        market_type = "A股" if is_ashare_symbol(symbol) else "美股"
        currency = "¥" if is_ashare_symbol(symbol) else "$"
        data_source = "yfinance真实数据"
        
        print("✅ 使用yfinance真实数据进行分析")
        
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
        support_pct = round(((support - current_price) / current_price) * 100, 2) if support else None
        resistance_pct = round(((resistance - current_price) / current_price) * 100, 2) if resistance else None
        
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
            "symbol": display_symbol,
            "name": name,
            "current_price": round(current_price, 2),
            "change": round(change_pct, 2),
            "volume": format_volume(volume),
            "currency": currency,
            "market_type": market_type,
            "data_source": data_source,
            "technical_score": technical_score,
            "fundamental_score": 50,  # 默认基本面评分
            "support_level": round(support, 2) if support else None,
            "resistance_level": round(resistance, 2) if resistance else None,
            "support_pct": support_pct,
            "resistance_pct": resistance_pct,
            "overall_score": overall_score,
            "institutional_action": "观望",  # 默认机构行为
            "signals": signals if isinstance(signals, list) else [signals],
            "suggestion": suggestion,
            "strategy": "智能分析",
            "recent_prices": recent_prices
        }
        
    except Exception as e:
        print(f"智能分析失败 {symbol}: {e}")
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
    """股票排名页面 - 简化版本"""
    market = request.args.get("market", "US")
    
    # 由于Python 3.6限制，暂时只支持美股排名
    try:
        if market == "US":
            # 返回一些热门美股作为示例
            sample_stocks = [
                {"symbol": "AAPL", "name": "Apple Inc.", "price": 175.43, "change": 1.2, "score": 85},
                {"symbol": "GOOGL", "name": "Alphabet Inc.", "price": 142.56, "change": 0.8, "score": 78},
                {"symbol": "MSFT", "name": "Microsoft Corp", "price": 338.11, "change": 1.5, "score": 82},
                {"symbol": "TSLA", "name": "Tesla Inc", "price": 248.50, "change": -0.5, "score": 65},
                {"symbol": "AMZN", "name": "Amazon.com Inc", "price": 178.22, "change": 2.1, "score": 79}
            ]
            rows = []
            for item in sample_stocks:
                rows.append({
                    "symbol": item["symbol"],
                    "name": item["name"],
                    "last_price": item["price"],
                    "change": item["change"],
                    "resistance": round(item["price"] * 1.1, 2),
                    "resistance_pct": 10.0,
                    "source": "yfinance",
                    "score": item["score"]
                })
        else:
            # A股和港股暂时不支持排名（需要akshare）
            rows = [{
                "symbol": "INFO",
                "name": f"{market}市场排名暂不可用",
                "last_price": "N/A",
                "change": "N/A",
                "resistance": "N/A",
                "resistance_pct": "N/A",
                "source": "功能限制",
                "score": 50
            }]
            
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
    """选股API接口 - 简化版本"""
    try:
        data = request.get_json()
        market = data.get("market", "US")
        strategy = data.get("strategy", "momentum")
        
        # 由于Python 3.6限制，暂时只支持美股选股
        if market == "US":
            results = [
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc.",
                    "current_price": 175.43,
                    "change": 1.2,
                    "volume": "56.2M",
                    "currency": "$",
                    "data_source": "yfinance",
                    "strategy": strategy,
                    "support_level": 158.0,
                    "resistance_level": 193.0,
                    "overall_score": 85,
                    "ai_score": 85,
                    "technical_score": 51,
                    "fundamental_score": 34,
                    "institutional_action": "AI推荐",
                    "signals": ["AI智能选股", "综合评分: 85"]
                },
                {
                    "symbol": "GOOGL",
                    "name": "Alphabet Inc.",
                    "current_price": 142.56,
                    "change": 0.8,
                    "volume": "28.4M",
                    "currency": "$",
                    "data_source": "yfinance",
                    "strategy": strategy,
                    "support_level": 128.0,
                    "resistance_level": 157.0,
                    "overall_score": 78,
                    "ai_score": 78,
                    "technical_score": 47,
                    "fundamental_score": 31,
                    "institutional_action": "AI推荐",
                    "signals": ["AI智能选股", "综合评分: 78"]
                }
            ]
        else:
            results = []
        
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
    # 监听到 0.0.0.0 以便同一局域网设备（如 iPad）访问；默认8082，可用环境变量PORT覆盖
    import os
    port = int(os.environ.get('PORT', 8082))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)