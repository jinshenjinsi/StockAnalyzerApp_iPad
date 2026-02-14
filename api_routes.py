#!/usr/bin/env python3
"""
API Routes for Stock Analyzer Application
Handles all REST API endpoints for the stock analysis system.
"""

from flask import Flask, jsonify, request, render_template
import json
import logging
from datetime import datetime

# Import modules
try:
    from technical_indicators import TechnicalIndicators
    from alert_system import AlertSystem
    from favorites_manager import FavoritesManager
    from ml_prediction import MLPredictionModel
    from sentiment_analysis import SentimentAnalysis
    from backtesting import BacktestingEngine
except ImportError as e:
    logging.error(f"Failed to import modules: {e}")
    # Create dummy classes for graceful degradation
    class DummyClass:
        def __init__(self): pass
        def __getattr__(self, name): return lambda *args, **kwargs: {}
    
    TechnicalIndicators = DummyClass
    AlertSystem = DummyClass
    FavoritesManager = DummyClass
    MLPredictionModel = DummyClass
    SentimentAnalysis = DummyClass
    BacktestingEngine = DummyClass

# Initialize components
tech_indicators = TechnicalIndicators()
alert_system = AlertSystem()
favorites_manager = FavoritesManager()
ml_model = MLPredictionModel()
sentiment_analyzer = SentimentAnalysis()
backtester = BacktestingEngine()

def register_api_routes(app):
    """Register all API routes with the Flask app"""
    
    @app.route('/api/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '3.0.0'
        })
    
    @app.route('/api/stock/<symbol>/indicators')
    def get_technical_indicators(symbol):
        """Get technical indicators for a stock symbol"""
        try:
            period = request.args.get('period', '1y')
            indicators = tech_indicators.calculate_all_indicators(symbol, period)
            return jsonify(indicators)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/alerts', methods=['GET', 'POST'])
    def handle_alerts():
        """Handle alert operations"""
        if request.method == 'GET':
            # Get all alerts
            alerts = alert_system.get_all_alerts()
            return jsonify(alerts)
        elif request.method == 'POST':
            # Create new alert
            data = request.json
            result = alert_system.create_alert(
                symbol=data.get('symbol'),
                condition=data.get('condition'),
                threshold=data.get('threshold'),
                alert_type=data.get('type', 'price')
            )
            return jsonify(result)
    
    @app.route('/api/alerts/<alert_id>', methods=['DELETE'])
    def delete_alert(alert_id):
        """Delete an alert"""
        result = alert_system.delete_alert(alert_id)
        return jsonify(result)
    
    @app.route('/api/favorites', methods=['GET', 'POST'])
    def handle_favorites():
        """Handle favorite operations"""
        if request.method == 'GET':
            favorites = favorites_manager.get_favorites()
            return jsonify(favorites)
        elif request.method == 'POST':
            data = request.json
            result = favorites_manager.add_favorite(data.get('symbol'), data.get('name'))
            return jsonify(result)
    
    @app.route('/api/favorites/<symbol>', methods=['DELETE'])
    def remove_favorite(symbol):
        """Remove a favorite"""
        result = favorites_manager.remove_favorite(symbol)
        return jsonify(result)
    
    @app.route('/api/ml/<symbol>/predict')
    def get_ml_prediction(symbol):
        """Get ML prediction for a stock symbol"""
        try:
            days = int(request.args.get('days', 7))
            prediction = ml_model.predict_price(symbol, days)
            return jsonify(prediction)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/sentiment/<symbol>')
    def get_sentiment_analysis(symbol):
        """Get sentiment analysis for a stock symbol"""
        try:
            days = int(request.args.get('days', 7))
            sentiment = sentiment_analyzer.get_sentiment_signals(symbol)
            return jsonify(sentiment)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/backtest', methods=['POST'])
    def run_backtest():
        """Run backtest for a strategy"""
        try:
            data = request.json
            result = backtester.run_backtest(
                strategy_name=data['strategy'],
                symbol=data['symbol'],
                start_date=data['startDate'],
                end_date=data['endDate'],
                initial_capital=data.get('capital', 10000)
            )
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/search')
    def search_stocks():
        """Search for stocks (placeholder)"""
        query = request.args.get('q', '')
        # This would integrate with a real stock search API
        return jsonify({'results': [], 'query': query})
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
