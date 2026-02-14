#!/usr/bin/env python3
"""
Advanced Cache Manager for Stock Analyzer
Implements multi-level caching with Redis and file-based fallback.
"""

import os
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
import redis

class CacheManager:
    def __init__(self):
        self.redis_client = None
        self.cache_dir = "/tmp/stock_analyzer_cache"
        self.init_cache()
        
    def init_cache(self):
        """Initialize cache systems"""
        # Try to connect to Redis first
        try:
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', '6379'))
            self.redis_client = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                db=0,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Test connection
            self.redis_client.ping()
            print("Redis cache initialized successfully")
        except Exception as e:
            print(f"Redis not available, using file cache: {e}")
            self.redis_client = None
            
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _get_cache_key(self, prefix: str, *args) -> str:
        """Generate cache key from arguments"""
        key_string = f"{prefix}:" + ":".join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode()).hexdigest()
        
    def _get_redis_key(self, cache_key: str) -> str:
        """Get full Redis key with namespace"""
        return f"stock_analyzer:{cache_key}"
        
    def get(self, prefix: str, *args) -> Optional[Any]:
        """Get cached data"""
        cache_key = self._get_cache_key(prefix, *args)
        
        # Try Redis first
        if self.redis_client:
            try:
                redis_key = self._get_redis_key(cache_key)
                cached_data = self.redis_client.get(redis_key)
                if cached_data:
                    return json.loads(cached_data.decode())
            except Exception as e:
                print(f"Redis get error: {e}")
                
        # Fall back to file cache
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    # Check if expired
                    if 'expires_at' in cache_data:
                        expires_at = datetime.fromisoformat(cache_data['expires_at'])
                        if datetime.now() > expires_at:
                            os.remove(cache_file)
                            return None
                    return cache_data['data']
            except Exception as e:
                print(f"File cache get error: {e}")
                
        return None
        
    def set(self, prefix: str, data: Any, ttl_minutes: int = 60, *args) -> bool:
        """Set cached data with TTL"""
        cache_key = self._get_cache_key(prefix, *args)
        expires_at = datetime.now() + timedelta(minutes=ttl_minutes)
        
        # Store in Redis if available
        if self.redis_client:
            try:
                redis_key = self._get_redis_key(cache_key)
                cache_data = {
                    'data': data,
                    'expires_at': expires_at.isoformat(),
                    'cached_at': datetime.now().isoformat()
                }
                self.redis_client.setex(
                    redis_key, 
                    ttl_minutes * 60, 
                    json.dumps(cache_data)
                )
                return True
            except Exception as e:
                print(f"Redis set error: {e}")
                
        # Fall back to file cache
        try:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            cache_data = {
                'data': data,
                'expires_at': expires_at.isoformat(),
                'cached_at': datetime.now().isoformat()
            }
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
            return True
        except Exception as e:
            print(f"File cache set error: {e}")
            return False
            
    def invalidate(self, prefix: str, *args) -> bool:
        """Invalidate cached data"""
        cache_key = self._get_cache_key(prefix, *args)
        
        # Invalidate Redis
        if self.redis_client:
            try:
                redis_key = self._get_redis_key(cache_key)
                self.redis_client.delete(redis_key)
            except Exception as e:
                print(f"Redis invalidate error: {e}")
                
        # Invalidate file cache
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
                return True
            except Exception as e:
                print(f"File cache invalidate error: {e}")
                return False
                
        return True
        
    def clear_all(self):
        """Clear all cache"""
        if self.redis_client:
            try:
                # Clear Redis keys with pattern
                cursor = 0
                while True:
                    cursor, keys = self.redis_client.scan(cursor=cursor, match="stock_analyzer:*", count=1000)
                    if keys:
                        self.redis_client.delete(*keys)
                    if cursor == 0:
                        break
            except Exception as e:
                print(f"Redis clear error: {e}")
                
        # Clear file cache
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    os.remove(os.path.join(self.cache_dir, filename))
        except Exception as e:
            print(f"File cache clear error: {e}")

# Global cache manager instance
cache_manager = CacheManager()

if __name__ == "__main__":
    # Test cache functionality
    test_data = {"test": "value", "timestamp": time.time()}
    
    # Set cache
    cache_manager.set("test", test_data, ttl_minutes=5, "key1", "key2")
    
    # Get cache
    retrieved = cache_manager.get("test", "key1", "key2")
    print(f"Retrieved: {retrieved}")
    
    # Invalidate
    cache_manager.invalidate("test", "key1", "key2")
    retrieved_after_invalidate = cache_manager.get("test", "key1", "key2")
    print(f"After invalidate: {retrieved_after_invalidate}")