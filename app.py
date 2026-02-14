#!/usr/bin/env python3
"""
Main Application Entry Point for Stock Analyzer
Integrates all phases (1, 2, 3) into a unified system.
"""

import os
import sys
import json
from flask import Flask, render_template, request, jsonify
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modules from all phases
try:
    # Phase 1: Core functionality
    from stock_app_optimized import get_stock_data, get_real_time_price
    
    # Phase 2: Technical indicators and alerts
    from technical_indicators import calculate_all_indicators
    from alert_system import AlertSystem
    from favorites_manager import FavoritesManager
    
    # Phase 3: Advanced features
    from ml_prediction import MLPredictionEngine
    from sentiment_analysis import SentimentAnalysis
    from backtesting import BacktestingEngine
    
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

# Initialize the Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'stock-analyzer-secret-key')

# Initialize components
alert_system = AlertSystem()
favorites_manager = FavoritesManager()
ml_engine = MLPredictionEngine()
sentiment_analyzer = SentimentAnalysis()
backtester = BacktestingEngine()

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index_phase2.html')

@app.route('/ml')
def ml_predictions():
    """ML predictions page"""
    return render_template('ml_predictions.html')

@app.route('/sentiment')
def sentiment():
    """Sentiment analysis page"""
    return render_template('sentiment.html')

@app.route('/backtest')
def backtesting():
    """Backtesting page"""
    return render_template('backtesting.html')

@app.route('/favorites')
def favorites():
    """Favorites management page"""
    return render_template('favorites.html')

@app.route('/alerts')
def alerts():
    """Alerts management page"""
    return render_template('alerts.html')

# API Endpoints
@app.route('/api/stock/<symbol>')
def api_stock_data(symbol):
    """Get comprehensive stock data including technical indicators"""
    try:
        # Get basic stock data
        stock_data = get_stock_data(symbol)
        if not stock_data:
            return jsonify({'error': 'Stock data not found'}), 404
            
        # Calculate technical indicators
        indicators = calculate_all_indicators(stock_data)
        
        # Get ML prediction
        ml_prediction = ml_engine.get_prediction(symbol)
        
        # Get sentiment analysis
        sentiment_data = sentiment_analyzer.get_sentiment_signals(symbol)
        
        return jsonify({
            'symbol': symbol,
            'stock_data': stock_data,
            'technical_indicators': indicators,
            'ml_prediction': ml_prediction,
            'sentiment_analysis': sentiment_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sentiment/<symbol>')
def api_sentiment(symbol):
    """Get sentiment analysis for a symbol"""
    try:
        sentiment_data = sentiment_analyzer.get_sentiment_signals(symbol)
        return jsonify(sentiment_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ml/<symbol>')
def api_ml_prediction(symbol):
    """Get ML prediction for a symbol"""
    try:
        prediction = ml_engine.get_prediction(symbol)
        return jsonify(prediction)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backtest', methods=['POST'])
def api_backtest():
    """Run backtest with provided parameters"""
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        strategy = data.get('strategy')
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        capital = data.get('capital', 10000)
        
        if not all([symbol, strategy, start_date, end_date]):
            return jsonify({'error': 'Missing required parameters'}), 400
            
        result = backtester.run_backtest(strategy, symbol, start_date, end_date, capital)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/favorites', methods=['GET', 'POST', 'DELETE'])
def api_favorites():
    """Manage favorites"""
    try:
        if request.method == 'GET':
            favorites = favorites_manager.get_all_favorites()
            return jsonify(favorites)
            
        elif request.method == 'POST':
            data = request.get_json()
            symbol = data.get('symbol')
            name = data.get('name', '')
            if symbol:
                favorites_manager.add_favorite(symbol, name)
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Symbol required'}), 400
                
        elif request.method == 'DELETE':
            data = request.get_json()
            symbol = data.get('symbol')
            if symbol:
                favorites_manager.remove_favorite(symbol)
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Symbol required'}), 400
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts', methods=['GET', 'POST', 'DELETE'])
def api_alerts():
    """Manage alerts"""
    try:
        if request.method == 'GET':
            alerts = alert_system.get_all_alerts()
            return jsonify(alerts)
            
        elif request.method == 'POST':
            data = request.get_json()
            symbol = data.get('symbol')
            condition = data.get('condition')
            threshold = data.get('threshold')
            alert_type = data.get('alertType', 'price')
            
            if symbol and condition and threshold:
                alert_system.create_alert(symbol, condition, float(threshold), alert_type)
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Missing required parameters'}), 400
                
        elif request.method == 'DELETE':
            data = request.get_json()
            alert_id = data.get('alertId')
            if alert_id:
                alert_system.delete_alert(alert_id)
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Alert ID required'}), 400
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Run the application
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)