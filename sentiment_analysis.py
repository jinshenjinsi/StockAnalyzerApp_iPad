#!/usr/bin/env python3
"""
Sentiment Analysis Module for Stock Analyzer
Analyzes market sentiment from news, social media, and financial reports
to provide additional signals for stock prediction.
"""

import os
import json
import requests
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Tuple

class SentimentAnalysis:
    def __init__(self):
        self.api_keys = {
            'newsapi': os.getenv('NEWSAPI_KEY', ''),
            'twitter': os.getenv('TWITTER_BEARER_TOKEN', ''),
            'finnhub': os.getenv('FINNHUB_API_KEY', '')
        }
        self.sentiment_cache = {}
        
    def analyze_news_sentiment(self, symbol: str, days: int = 7) -> Dict:
        """Analyze sentiment from financial news"""
        try:
            # Get recent news for the stock symbol
            url = f"https://newsapi.org/v2/everything"
            params = {
                'q': symbol,
                'sortBy': 'publishedAt',
                'language': 'en',
                'pageSize': 100,
                'apiKey': self.api_keys['newsapi']
            }
            
            if days > 0:
                from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                params['from'] = from_date
                
            response = requests.get(url, params=params)
            news_data = response.json()
            
            # Simple sentiment scoring (in real implementation, use NLP models)
            positive_keywords = ['growth', 'profit', 'success', 'upgrade', 'bullish', 'strong']
            negative_keywords = ['loss', 'decline', 'downgrade', 'bearish', 'weak', 'crisis']
            
            total_score = 0
            article_count = 0
            
            for article in news_data.get('articles', []):
                title = article.get('title', '').lower()
                description = article.get('description', '').lower()
                content = title + ' ' + description
                
                pos_score = sum(1 for word in positive_keywords if word in content)
                neg_score = sum(1 for word in negative_keywords if word in content)
                article_score = pos_score - neg_score
                
                total_score += article_score
                article_count += 1
                
            avg_sentiment = total_score / article_count if article_count > 0 else 0
            
            return {
                'symbol': symbol,
                'sentiment_score': avg_sentiment,
                'article_count': article_count,
                'analysis_date': datetime.now().isoformat(),
                'confidence': min(article_count / 10, 1.0)  # Confidence based on article count
            }
            
        except Exception as e:
            print(f"Error analyzing news sentiment for {symbol}: {e}")
            return {
                'symbol': symbol,
                'sentiment_score': 0,
                'article_count': 0,
                'analysis_date': datetime.now().isoformat(),
                'confidence': 0
            }
    
    def analyze_social_sentiment(self, symbol: str) -> Dict:
        """Analyze sentiment from social media (Twitter/X)"""
        # Implementation for social media sentiment analysis
        # This would use Twitter API v2 with bearer token
        return {
            'symbol': symbol,
            'social_sentiment': 0,
            'tweet_count': 0,
            'analysis_date': datetime.now().isoformat(),
            'confidence': 0
        }
    
    def get_combined_sentiment(self, symbol: str) -> Dict:
        """Combine news and social sentiment into overall score"""
        news_sentiment = self.analyze_news_sentiment(symbol)
        social_sentiment = self.analyze_social_sentiment(symbol)
        
        # Weighted average (news gets higher weight initially)
        news_weight = 0.7
        social_weight = 0.3
        
        combined_score = (
            news_sentiment['sentiment_score'] * news_weight * news_sentiment['confidence'] +
            social_sentiment['social_sentiment'] * social_weight * social_sentiment['confidence']
        )
        
        confidence = (news_sentiment['confidence'] + social_sentiment['confidence']) / 2
        
        return {
            'symbol': symbol,
            'combined_sentiment': combined_score,
            'confidence': confidence,
            'news_data': news_sentiment,
            'social_data': social_sentiment,
            'analysis_date': datetime.now().isoformat()
        }
    
    def get_sentiment_signals(self, symbol: str) -> Dict:
        """Generate trading signals based on sentiment analysis"""
        sentiment_data = self.get_combined_sentiment(symbol)
        score = sentiment_data['combined_sentiment']
        confidence = sentiment_data['confidence']
        
        if confidence < 0.3:
            signal = 'NEUTRAL'
            strength = 'WEAK'
        elif score > 2:
            signal = 'BUY'
            strength = 'STRONG' if confidence > 0.7 else 'MODERATE'
        elif score > 0.5:
            signal = 'BUY'
            strength = 'WEAK'
        elif score < -2:
            signal = 'SELL'
            strength = 'STRONG' if confidence > 0.7 else 'MODERATE'
        elif score < -0.5:
            signal = 'SELL'
            strength = 'WEAK'
        else:
            signal = 'NEUTRAL'
            strength = 'MODERATE'
            
        return {
            'symbol': symbol,
            'signal': signal,
            'strength': strength,
            'sentiment_score': score,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        }

# Example usage
if __name__ == "__main__":
    sentiment_analyzer = SentimentAnalysis()
    result = sentiment_analyzer.get_sentiment_signals("AAPL")
    print(json.dumps(result, indent=2))