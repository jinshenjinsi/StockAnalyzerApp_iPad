#!/usr/bin/env python3
"""
Error Handling and Logging Module for Stock Analyzer
Provides comprehensive error handling, logging, and monitoring capabilities.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import traceback

class ErrorHandler:
    def __init__(self, log_level: str = "INFO"):
        self.setup_logging(log_level)
        self.error_counts = {}
        
    def setup_logging(self, log_level: str):
        """Setup logging configuration"""
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        log_file = os.path.join(log_dir, f"stock_analyzer_{datetime.now().strftime('%Y%m%d')}.log")
        
        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        
    def log_error(self, error: Exception, context: Dict[str, Any] = None, 
                  error_type: str = "GENERAL"):
        """Log an error with context"""
        error_id = f"{error_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        error_info = {
            "error_id": error_id,
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": str(error),
            "error_class": error.__class__.__name__,
            "traceback": traceback.format_exc(),
            "context": context or {}
        }
        
        self.logger.error(json.dumps(error_info, indent=2))
        
        # Update error count
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
        
        return error_id
    
    def log_warning(self, message: str, context: Dict[str, Any] = None):
        """Log a warning"""
        warning_info = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "context": context or {}
        }
        self.logger.warning(json.dumps(warning_info, indent=2))
        
    def log_info(self, message: str, context: Dict[str, Any] = None):
        """Log an info message"""
        info_info = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "context": context or {}
        }
        self.logger.info(json.dumps(info_info, indent=2))
        
    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics"""
        return self.error_counts.copy()
    
    def reset_error_counts(self):
        """Reset error counts"""
        self.error_counts.clear()

# Global error handler instance
error_handler = ErrorHandler(os.getenv('LOG_LEVEL', 'INFO'))

def handle_api_error(func):
    """Decorator for API error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_context = {
                "function": func.__name__,
                "args": str(args)[:200],  # Truncate long args
                "kwargs": str(kwargs)[:200]
            }
            error_id = error_handler.log_error(e, error_context, "API_ERROR")
            return {
                "error": str(e),
                "error_id": error_id,
                "status": "error"
            }
    return wrapper

def handle_data_error(func):
    """Decorator for data processing error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_context = {
                "function": func.__name__,
                "data_source": getattr(args[0], 'source', 'unknown') if args else 'unknown'
            }
            error_id = error_handler.log_error(e, error_context, "DATA_ERROR")
            return None
    return wrapper

# Example usage
if __name__ == "__main__":
    # Test error handling
    try:
        raise ValueError("Test error")
    except Exception as e:
        error_id = error_handler.log_error(e, {"test": True}, "TEST_ERROR")
        print(f"Logged error with ID: {error_id}")
        
    # Test logging
    error_handler.log_info("Application started", {"version": "1.0.0"})
    error_handler.log_warning("High memory usage detected", {"memory_mb": 1024})