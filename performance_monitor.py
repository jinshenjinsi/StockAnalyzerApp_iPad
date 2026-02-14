#!/usr/bin/env python3
"""
Performance Monitoring Module for Stock Analyzer
Monitors system performance, API response times, and resource usage.
"""

import os
import json
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from functools import wraps

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'api_calls': {},
            'system_resources': {},
            'ml_predictions': {},
            'cache_hits': 0,
            'cache_misses': 0
        }
        self.start_time = time.time()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/home/admin/.openclaw/workspace/StockAnalyzerApp_iPad/app.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('PerformanceMonitor')
        
    def track_api_call(self, endpoint: str, duration: float, status_code: int = 200):
        """Track API call performance"""
        if endpoint not in self.metrics['api_calls']:
            self.metrics['api_calls'][endpoint] = {
                'count': 0,
                'total_duration': 0,
                'avg_duration': 0,
                'errors': 0
            }
            
        self.metrics['api_calls'][endpoint]['count'] += 1
        self.metrics['api_calls'][endpoint]['total_duration'] += duration
        self.metrics['api_calls'][endpoint]['avg_duration'] = (
            self.metrics['api_calls'][endpoint]['total_duration'] / 
            self.metrics['api_calls'][endpoint]['count']
        )
        
        if status_code >= 400:
            self.metrics['api_calls'][endpoint]['errors'] += 1
            
        self.logger.info(f"API Call: {endpoint} - {duration:.3f}s - Status: {status_code}")
        
    def track_ml_prediction(self, symbol: str, duration: float, model_type: str):
        """Track ML prediction performance"""
        key = f"{symbol}_{model_type}"
        if key not in self.metrics['ml_predictions']:
            self.metrics['ml_predictions'][key] = {
                'count': 0,
                'total_duration': 0,
                'avg_duration': 0
            }
            
        self.metrics['ml_predictions'][key]['count'] += 1
        self.metrics['ml_predictions'][key]['total_duration'] += duration
        self.metrics['ml_predictions'][key]['avg_duration'] = (
            self.metrics['ml_predictions'][key]['total_duration'] / 
            self.metrics['ml_predictions'][key]['count']
        )
        
        self.logger.info(f"ML Prediction: {key} - {duration:.3f}s")
        
    def update_system_resources(self):
        """Update system resource metrics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        self.metrics['system_resources'] = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_mb': memory.available / (1024 * 1024),
            'disk_usage_percent': (disk.used / disk.total) * 100,
            'disk_free_gb': disk.free / (1024 * 1024 * 1024),
            'uptime_seconds': time.time() - self.start_time
        }
        
        self.logger.debug(f"System Resources - CPU: {cpu_percent}%, Memory: {memory.percent}%")
        
    def record_cache_hit(self):
        """Record cache hit"""
        self.metrics['cache_hits'] += 1
        
    def record_cache_miss(self):
        """Record cache miss"""
        self.metrics['cache_misses'] += 1
        
    def get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.metrics['cache_hits'] + self.metrics['cache_misses']
        return self.metrics['cache_hits'] / total if total > 0 else 0
        
    def get_performance_report(self) -> Dict:
        """Generate comprehensive performance report"""
        self.update_system_resources()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'uptime': str(timedelta(seconds=int(time.time() - self.start_time))),
            'system_resources': self.metrics['system_resources'],
            'api_performance': self.metrics['api_calls'],
            'ml_performance': self.metrics['ml_predictions'],
            'cache_statistics': {
                'hits': self.metrics['cache_hits'],
                'misses': self.metrics['cache_misses'],
                'hit_rate': self.get_cache_hit_rate()
            },
            'total_requests': sum(v['count'] for v in self.metrics['api_calls'].values())
        }
        
        return report
        
    def log_performance_summary(self):
        """Log performance summary"""
        report = self.get_performance_report()
        self.logger.info(f"Performance Summary - Uptime: {report['uptime']}, "
                        f"Total Requests: {report['total_requests']}, "
                        f"Cache Hit Rate: {report['cache_statistics']['hit_rate']:.2%}")
                        
    def api_performance_decorator(self, endpoint_name: str):
        """Decorator to automatically track API performance"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    self.track_api_call(endpoint_name, duration, 200)
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    self.track_api_call(endpoint_name, duration, 500)
                    self.logger.error(f"API Error in {endpoint_name}: {str(e)}")
                    raise
            return wrapper
        return decorator

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Example usage
if __name__ == "__main__":
    # Simulate some API calls
    @performance_monitor.api_performance_decorator("test_endpoint")
    def test_api():
        time.sleep(0.1)
        return {"status": "success"}
        
    test_api()
    performance_monitor.log_performance_summary()