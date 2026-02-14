#!/usr/bin/env python3
"""
Phase 3: Advanced Stock Analysis System with ML Prediction and Sentiment Analysis
"""

import os
import sys
import json
from datetime import datetime

# Import Phase 2 modules
from technical_indicators import TechnicalIndicators
from alert_system import AlertSystem  
from favorites_manager import FavoritesManager

# Import Phase 3 modules
from ml_prediction import MLPredictionEngine
from sentiment_analysis import SentimentAnalysis
from backtesting import BacktestingEngine

class StockAnalyzerPhase3:
    def __init__(self):
        self.config = self.load_config()
        self.tech_indicators = TechnicalIndicators()
        self.alert_system = AlertSystem()
        self.favorites_manager = FavoritesManager()
        self.ml_engine = MLPredictionEngine()
        self.sentiment_analyzer = SentimentAnalysis()
        self.backtester = BacktestingEngine()
        
    def load_config(self):
        """Load configuration from environment variables"""
        return {
            'api_keys': {
                'alpha_vantage': os.getenv('ALPHA_VANTAGE_API_KEY', ''),
                'newsapi': os.getenv('NEWSAPI_KEY', ''),
                'finnhub': os.getenv('FINNHUB_API_KEY', '')
            },
            'ml_model_path': os.getenv('ML_MODEL_PATH', './models/'),
            'cache_dir': os.getenv('CACHE_DIR', './cache/'),
            'data_sources': ['yahoo_finance', 'alpha_vantage']
        }
    
    def analyze_stock_comprehensive(self, symbol: str) -> Dict:
        """Comprehensive stock analysis combining all Phase 2 and Phase 3 features"""
        print(f"Analyzing {symbol} comprehensively...")
        
        # Phase 2: Technical Analysis
        tech_data = self.tech_indicators.get_all_indicators(symbol)
        
        # Phase 3: ML Prediction
        ml_prediction = self.ml_engine.predict_price(symbol, days_ahead=7)
        
        # Phase 3: Sentiment Analysis  
        sentiment_data = self.sentiment_analyzer.get_sentiment_signals(symbol)
        
        # Combine all analysis
        comprehensive_analysis = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'technical_analysis': tech_data,
            'ml_prediction': ml_prediction,
            'sentiment_analysis': sentiment_data,
            'combined_signal': self.generate_combined_signal(tech_data, ml_prediction, sentiment_data)
        }
        
        return comprehensive_analysis
    
    def generate_combined_signal(self, tech_data: Dict, ml_data: Dict, sentiment_data: Dict) -> Dict:
        """Generate combined trading signal from all analysis methods"""
        # Weight different signals based on confidence
        tech_weight = 0.4
        ml_weight = 0.4  
        sentiment_weight = 0.2
        
        # Extract signals (simplified - real implementation would be more sophisticated)
        tech_signal = self.extract_tech_signal(tech_data)
        ml_signal = self.extract_ml_signal(ml_data)
        sentiment_signal = sentiment_data.get('signal', 'NEUTRAL')
        
        # Calculate weighted decision
        buy_score = 0
        sell_score = 0
        
        if tech_signal == 'BUY':
            buy_score += tech_weight
        elif tech_signal == 'SELL':
            sell_score += tech_weight
            
        if ml_signal == 'BUY':
            buy_score += ml_weight
        elif ml_signal == 'SELL':
            sell_score += ml_weight
            
        if sentiment_signal == 'BUY':
            buy_score += sentiment_weight
        elif sentiment_signal == 'SELL':
            sell_score += sentiment_weight
            
        # Determine final signal
        if buy_score > sell_score and buy_score > 0.5:
            final_signal = 'BUY'
            strength = 'STRONG' if buy_score > 0.7 else 'MODERATE'
        elif sell_score > buy_score and sell_score > 0.5:
            final_signal = 'SELL'
            strength = 'STRONG' if sell_score > 0.7 else 'MODERATE'
        else:
            final_signal = 'NEUTRAL'
            strength = 'WEAK'
            
        return {
            'signal': final_signal,
            'strength': strength,
            'buy_score': buy_score,
            'sell_score': sell_score,
            'confidence': max(buy_score, sell_score, 0.3)  # Minimum confidence
        }
    
    def extract_tech_signal(self, tech_data: Dict) -> str:
        """Extract trading signal from technical indicators"""
        # Simplified logic - real implementation would use more sophisticated rules
        rsi = tech_data.get('rsi', 50)
        macd_signal = tech_data.get('macd_signal', 'NEUTRAL')
        
        if rsi < 30 and macd_signal == 'BUY':
            return 'BUY'
        elif rsi > 70 and macd_signal == 'SELL':
            return 'SELL'
        else:
            return 'NEUTRAL'
            
    def extract_ml_signal(self, ml_data: Dict) -> str:
        """Extract trading signal from ML prediction"""
        prediction = ml_data.get('prediction', {})
        current_price = prediction.get('current_price', 0)
        predicted_price = prediction.get('predicted_price', 0)
        
        if current_price > 0:
            change_percent = (predicted_price - current_price) / current_price * 100
            if change_percent > 2:
                return 'BUY'
            elif change_percent < -2:
                return 'SELL'
                
        return 'NEUTRAL'
    
    def run_backtest_on_strategy(self, strategy_name: str, symbols: List[str]) -> Dict:
        """Run backtesting on multiple symbols for a given strategy"""
        results = {}
        for symbol in symbols:
            result = self.backtester.run_backtest(
                strategy_name, symbol, 
                "2023-01-01", "2023-12-31"
            )
            results[symbol] = result
        return results
    
    def start_monitoring_favorites(self):
        """Start monitoring favorite stocks with all analysis features"""
        favorites = self.favorites_manager.get_favorites()
        for symbol in favorites:
            analysis = self.analyze_stock_comprehensive(symbol)
            # Check alerts based on comprehensive analysis
            self.alert_system.check_comprehensive_alerts(symbol, analysis)

def main():
    analyzer = StockAnalyzerPhase3()
    
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
        result = analyzer.analyze_stock_comprehensive(symbol)
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python stock_app_phase3.py <SYMBOL>")
        print("Example: python stock_app_phase3.py AAPL")

if __name__ == "__main__":
    main()