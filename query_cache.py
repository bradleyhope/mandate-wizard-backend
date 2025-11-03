"""
Query Cache Module
Provides in-memory caching for Pinecone queries to improve performance
"""

import time
import hashlib
import json
from functools import wraps

class QueryCache:
    """Simple in-memory cache with TTL (Time To Live)"""
    
    def __init__(self, default_ttl=300):
        """
        Initialize cache
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 300 = 5 minutes)
        """
        self.cache = {}
        self.default_ttl = default_ttl
    
    def _generate_key(self, func_name, *args, **kwargs):
        """Generate cache key from function name and arguments"""
        # Create a deterministic string from args and kwargs
        key_data = {
            'func': func_name,
            'args': args,
            'kwargs': kwargs
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, key):
        """Get value from cache if not expired"""
        if key in self.cache:
            value, expiry = self.cache[key]
            if time.time() < expiry:
                return value
            else:
                # Expired, remove from cache
                del self.cache[key]
        return None
    
    def set(self, key, value, ttl=None):
        """Set value in cache with TTL"""
        if ttl is None:
            ttl = self.default_ttl
        expiry = time.time() + ttl
        self.cache[key] = (value, expiry)
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
    
    def cleanup(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self.cache.items()
            if current_time >= expiry
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def cached(self, ttl=None):
        """
        Decorator to cache function results
        
        Usage:
            @cache.cached(ttl=600)
            def expensive_function(arg1, arg2):
                return result
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_key(func.__name__, *args, **kwargs)
                
                # Try to get from cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Not in cache, call function
                result = func(*args, **kwargs)
                
                # Store in cache
                self.set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator

# Global cache instance
query_cache = QueryCache(default_ttl=300)  # 5 minutes default

