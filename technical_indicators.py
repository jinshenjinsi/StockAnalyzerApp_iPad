"""
高级技术指标模块
包含 MACD、RSI、布林带等完整实现，以及更多高级指标
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

class TechnicalIndicators:
    """技术指标计算类"""
    
    def __init__(self):
        self.indicators = {}
    
    def calculate_rsi(self, df, period=14):
        """计算RSI相对强弱指标 - 完整实现"""
        try:
            if len(df) < period + 1:
                return None
                
            # 计算价格变化
            delta = df['Close'].diff()
            
            # 分离上涨和下跌
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            # 计算平均上涨和平均下跌（使用指数移动平均）
            avg_gain = gain.ewm(com=period-1, min_periods=period).mean()
            avg_loss = loss.ewm(com=period-1, min_periods=period).mean()
            
            # 计算RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return {
                'rsi': float(rsi.iloc[-1]),
                'rsi_history': rsi.tolist(),
                'overbought': 70,
                'oversold': 30,
                'signal': 'neutral'
            }
            
        except Exception as e:
            print(f"RSI计算错误: {e}")
            return None
    
    def calculate_macd(self, df, fast=12, slow=26, signal=9):
        """计算MACD指标 - 完整实现"""
        try:
            if len(df) < slow + signal:
                return None
                
            # 计算快速EMA和慢速EMA
            ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
            ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
            
            # 计算MACD线
            macd_line = ema_fast - ema_slow
            
            # 计算信号线
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()
            
            # 计算柱状图
            histogram = macd_line - signal_line
            
            # 判断信号
            current_macd = macd_line.iloc[-1]
            current_signal = signal_line.iloc[-1]
            prev_macd = macd_line.iloc[-2] if len(macd_line) >= 2 else current_macd
            prev_signal = signal_line.iloc[-2] if len(signal_line) >= 2 else current_signal
            
            if prev_macd <= prev_signal and current_macd > current_signal:
                signal_type = 'bullish_crossover'  # 金叉
            elif prev_macd >= prev_signal and current_macd < current_signal:
                signal_type = 'bearish_crossover'  # 死叉
            elif current_macd > 0 and current_signal > 0:
                signal_type = 'bullish_trend'  # 多头趋势
            elif current_macd < 0 and current_signal < 0:
                signal_type = 'bearish_trend'  # 空头趋势
            else:
                signal_type = 'neutral'
            
            return {
                'macd': float(current_macd),
                'signal': float(current_signal),
                'histogram': float(histogram.iloc[-1]),
                'macd_history': macd_line.tolist(),
                'signal_history': signal_line.tolist(),
                'histogram_history': histogram.tolist(),
                'signal_type': signal_type
            }
            
        except Exception as e:
            print(f"MACD计算错误: {e}")
            return None
    
    def calculate_bollinger_bands(self, df, period=20, std_dev=2):
        """计算布林带 - 完整实现"""
        try:
            if len(df) < period:
                return None
                
            # 计算中轨（SMA）
            middle_band = df['Close'].rolling(window=period).mean()
            
            # 计算标准差
            std = df['Close'].rolling(window=period).std()
            
            # 计算上轨和下轨
            upper_band = middle_band + (std * std_dev)
            lower_band = middle_band - (std * std_dev)
            
            # 计算布林带宽度和%b
            bb_width = (upper_band - lower_band) / middle_band
            bb_percent = (df['Close'] - lower_band) / (upper_band - lower_band)
            
            current_price = df['Close'].iloc[-1]
            current_upper = upper_band.iloc[-1]
            current_lower = lower_band.iloc[-1]
            current_middle = middle_band.iloc[-1]
            current_bb_width = bb_width.iloc[-1]
            current_bb_percent = bb_percent.iloc[-1]
            
            # 判断信号
            if current_price <= current_lower:
                signal = 'oversold'  # 超卖
            elif current_price >= current_upper:
                signal = 'overbought'  # 超买
            elif current_bb_width < bb_width.mean() * 0.8:
                signal = 'squeeze'  # 布林带收窄
            else:
                signal = 'normal'
            
            return {
                'upper_band': float(current_upper),
                'middle_band': float(current_middle),
                'lower_band': float(current_lower),
                'bb_width': float(current_bb_width),
                'bb_percent': float(current_bb_percent),
                'upper_history': upper_band.tolist(),
                'middle_history': middle_band.tolist(),
                'lower_history': lower_band.tolist(),
                'signal': signal
            }
            
        except Exception as e:
            print(f"布林带计算错误: {e}")
            return None
    
    def calculate_stochastic_oscillator(self, df, k_period=14, d_period=3):
        """计算随机震荡指标"""
        try:
            if len(df) < k_period:
                return None
                
            # 计算%K
            low_min = df['Low'].rolling(window=k_period).min()
            high_max = df['High'].rolling(window=k_period).max()
            k = 100 * ((df['Close'] - low_min) / (high_max - low_min))
            
            # 计算%D
            d = k.rolling(window=d_period).mean()
            
            current_k = k.iloc[-1]
            current_d = d.iloc[-1]
            
            # 判断信号
            if current_k < 20 and current_d < 20:
                signal = 'oversold'
            elif current_k > 80 and current_d > 80:
                signal = 'overbought'
            elif current_k > current_d and current_k < 50:
                signal = 'bullish'
            elif current_k < current_d and current_k > 50:
                signal = 'bearish'
            else:
                signal = 'neutral'
            
            return {
                'k': float(current_k),
                'd': float(current_d),
                'k_history': k.tolist(),
                'd_history': d.tolist(),
                'signal': signal
            }
            
        except Exception as e:
            print(f"随机震荡指标计算错误: {e}")
            return None
    
    def calculate_atr(self, df, period=14):
        """计算平均真实波幅(ATR)"""
        try:
            if len(df) < period + 1:
                return None
                
            # 计算真实波幅
            high_low = df['High'] - df['Low']
            high_close = abs(df['High'] - df['Close'].shift(1))
            low_close = abs(df['Low'] - df['Close'].shift(1))
            
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            
            # 计算ATR
            atr = tr.ewm(span=period, adjust=False).mean()
            
            return {
                'atr': float(atr.iloc[-1]),
                'atr_history': atr.tolist(),
                'volatility_level': 'high' if atr.iloc[-1] > df['Close'].iloc[-1] * 0.02 else 'low'
            }
            
        except Exception as e:
            print(f"ATR计算错误: {e}")
            return None
    
    def calculate_all_indicators(self, df):
        """计算所有技术指标"""
        indicators = {}
        
        # RSI
        rsi_data = self.calculate_rsi(df)
        if rsi_data:
            indicators['rsi'] = rsi_data
        
        # MACD
        macd_data = self.calculate_macd(df)
        if macd_data:
            indicators['macd'] = macd_data
        
        # 布林带
        bb_data = self.calculate_bollinger_bands(df)
        if bb_data:
            indicators['bollinger_bands'] = bb_data
        
        # 随机震荡指标
        stoch_data = self.calculate_stochastic_oscillator(df)
        if stoch_data:
            indicators['stochastic'] = stoch_data
        
        # ATR
        atr_data = self.calculate_atr(df)
        if atr_data:
            indicators['atr'] = atr_data
        
        return indicators

# 全局技术指标实例
tech_indicators = TechnicalIndicators()