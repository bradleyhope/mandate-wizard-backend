"""
Cache Manager for Mandate Wizard

Provides Redis-based caching for expensive queries and analytics.
Improves performance by reducing database load for frequently accessed data.
"""

import json
import hashlib
from typing import Any, Optional, Callable
from functools import wraps
import os
from redis import Redis


class CacheManager:
    """
    Manages caching for analytics and priority queries.
    
    Uses Redis for distributed caching with configurable TTLs.
    """
    
    def __init__(self, redis_client: Optional[Redis] = None):
        """
        Initialize cache manager.
        
        Args:
            redis_client: Optional Redis client (creates new one if not provided)
        """
        if redis_client:
            self.redis = redis_client
        else:
            self.redis = Redis(
                host=os.getenv('REDIS_HOST'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                password=os.getenv('REDIS_PASSWORD'),
                db=int(os.getenv('REDIS_DB', 0)),
                decode_responses=True
            )
        
        # Cache key prefixes
        self.PREFIX_ANALYTICS = 'analytics:'
        self.PREFIX_PRIORITY = 'priority:'
        self.PREFIX_ENTITY = 'entity:'
        
        # Default TTLs (in seconds)
        self.TTL_ANALYTICS = 300      # 5 minutes
        self.TTL_PRIORITY = 600       # 10 minutes
        self.TTL_ENTITY = 180         # 3 minutes
        self.TTL_STATS = 60           # 1 minute (frequently changing)
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from prefix and arguments.
        
        Args:
            prefix: Cache key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Cache key string
        """
        # Combine all arguments into a string
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_string = ":".join(key_parts)
        
        # Hash if too long
        if len(key_string) > 100:
            key_string = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"{prefix}{key_string}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int):
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds
        """
        try:
            self.redis.setex(
                key,
                ttl,
                json.dumps(value, default=str)  # default=str handles datetime
            )
        except Exception as e:
            print(f"Cache set error: {e}")
    
    def delete(self, key: str):
        """
        Delete value from cache.
        
        Args:
            key: Cache key
        """
        try:
            self.redis.delete(key)
        except Exception as e:
            print(f"Cache delete error: {e}")
    
    def invalidate_pattern(self, pattern: str):
        """
        Invalidate all keys matching a pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "analytics:*")
        """
        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
        except Exception as e:
            print(f"Cache invalidate error: {e}")
    
    def cached(self, prefix: str, ttl: int):
        """
        Decorator for caching function results.
        
        Args:
            prefix: Cache key prefix
            ttl: Time to live in seconds
            
        Returns:
            Decorated function
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_key(prefix, *args, **kwargs)
                
                # Try to get from cache
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Cache result
                self.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator
    
    # Convenience methods for common cache operations
    
    def get_analytics_stats(self) -> Optional[dict]:
        """Get cached analytics stats"""
        return self.get(f"{self.PREFIX_ANALYTICS}stats")
    
    def set_analytics_stats(self, stats: dict):
        """Cache analytics stats"""
        self.set(f"{self.PREFIX_ANALYTICS}stats", stats, self.TTL_STATS)
    
    def get_top_entities(self, limit: int, entity_type: str = '') -> Optional[list]:
        """Get cached top entities"""
        key = self._generate_key(self.PREFIX_ANALYTICS, 'top', limit=limit, type=entity_type)
        return self.get(key)
    
    def set_top_entities(self, entities: list, limit: int, entity_type: str = ''):
        """Cache top entities"""
        key = self._generate_key(self.PREFIX_ANALYTICS, 'top', limit=limit, type=entity_type)
        self.set(key, entities, self.TTL_ANALYTICS)
    
    def get_priority_batch(self, limit: int, min_priority: str = '', entity_type: str = '') -> Optional[list]:
        """Get cached priority batch"""
        key = self._generate_key(
            self.PREFIX_PRIORITY, 
            'batch', 
            limit=limit, 
            priority=min_priority,
            type=entity_type
        )
        return self.get(key)
    
    def set_priority_batch(self, batch: list, limit: int, min_priority: str = '', entity_type: str = ''):
        """Cache priority batch"""
        key = self._generate_key(
            self.PREFIX_PRIORITY, 
            'batch', 
            limit=limit, 
            priority=min_priority,
            type=entity_type
        )
        self.set(key, batch, self.TTL_PRIORITY)
    
    def get_entity_details(self, entity_id: str) -> Optional[dict]:
        """Get cached entity details"""
        return self.get(f"{self.PREFIX_ENTITY}{entity_id}")
    
    def set_entity_details(self, entity_id: str, details: dict):
        """Cache entity details"""
        self.set(f"{self.PREFIX_ENTITY}{entity_id}", details, self.TTL_ENTITY)
    
    def invalidate_entity(self, entity_id: str):
        """Invalidate all cache entries for an entity"""
        self.delete(f"{self.PREFIX_ENTITY}{entity_id}")
        # Also invalidate lists that might contain this entity
        self.invalidate_pattern(f"{self.PREFIX_ANALYTICS}*")
        self.invalidate_pattern(f"{self.PREFIX_PRIORITY}*")
    
    def invalidate_all_analytics(self):
        """Invalidate all analytics caches"""
        self.invalidate_pattern(f"{self.PREFIX_ANALYTICS}*")
    
    def invalidate_all_priority(self):
        """Invalidate all priority caches"""
        self.invalidate_pattern(f"{self.PREFIX_PRIORITY}*")
    
    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache statistics
        """
        try:
            info = self.redis.info('stats')
            
            return {
                'total_keys': self.redis.dbsize(),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                ),
                'analytics_keys': len(self.redis.keys(f"{self.PREFIX_ANALYTICS}*")),
                'priority_keys': len(self.redis.keys(f"{self.PREFIX_PRIORITY}*")),
                'entity_keys': len(self.redis.keys(f"{self.PREFIX_ENTITY}*"))
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)


# Singleton instance
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """Get singleton cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
