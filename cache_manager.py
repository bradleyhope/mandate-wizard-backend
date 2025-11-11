"""
Redis Caching Module for Mandate Wizard V5
Phase 3.2: Caching Layer

This module provides intelligent caching for:
- Query responses (full GPT-5 answers)
- Vector search results (Pinecone queries)
- Embeddings (question embeddings)
"""

import redis
import json
import hashlib
import os
from typing import Any, Optional, Dict
from datetime import timedelta


class CacheManager:
    """Manages Redis caching for Mandate Wizard."""
    
    def __init__(self, host: str = None, port: int = None, db: int = None, password: str = None):
        """
        Initialize Redis cache manager.
        
        Args:
            host: Redis server host (defaults to REDIS_HOST env var)
            port: Redis server port (defaults to REDIS_PORT env var)
            db: Redis database number (defaults to REDIS_DB env var)
            password: Redis password (defaults to REDIS_PASSWORD env var)
        """
        # Read from environment variables if not provided
        host = host or os.getenv('REDIS_HOST', 'localhost')
        port = port or int(os.getenv('REDIS_PORT', '6379'))
        db = db or int(os.getenv('REDIS_DB', '0'))
        password = password or os.getenv('REDIS_PASSWORD')
        
        try:
            self.redis = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis.ping()
            self.enabled = True
            print("✅ Redis cache connected")
        except Exception as e:
            print(f"⚠️ Redis connection failed: {e}")
            print("  Continuing without caching...")
            self.enabled = False
            self.redis = None
    
    def _make_key(self, prefix: str, data: str) -> str:
        """
        Create a cache key from prefix and data.
        
        Args:
            prefix: Key prefix (e.g., 'response', 'vector', 'embedding')
            data: Data to hash (e.g., question text)
        
        Returns:
            Cache key string
        """
        # Create hash of data for consistent key length
        data_hash = hashlib.md5(data.encode()).hexdigest()
        return f"mandate_wizard:{prefix}:{data_hash}"
    
    def get(self, prefix: str, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            prefix: Key prefix
            key: Key data
        
        Returns:
            Cached value or None if not found
        """
        if not self.enabled:
            return None
        
        try:
            cache_key = self._make_key(prefix, key)
            value = self.redis.get(cache_key)
            
            if value:
                # Try to parse as JSON
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            
            return None
        except Exception as e:
            print(f"⚠️ Cache get error: {e}")
            return None
    
    def set(
        self,
        prefix: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            prefix: Key prefix
            key: Key data
            value: Value to cache
            ttl: Time to live in seconds (None = no expiration)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            cache_key = self._make_key(prefix, key)
            
            # Serialize value as JSON if it's a dict/list
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            if ttl:
                self.redis.setex(cache_key, ttl, value)
            else:
                self.redis.set(cache_key, value)
            
            return True
        except Exception as e:
            print(f"⚠️ Cache set error: {e}")
            return False
    
    def delete(self, prefix: str, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            prefix: Key prefix
            key: Key data
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            cache_key = self._make_key(prefix, key)
            self.redis.delete(cache_key)
            return True
        except Exception as e:
            print(f"⚠️ Cache delete error: {e}")
            return False
    
    def clear_all(self) -> bool:
        """
        Clear all Mandate Wizard cache entries.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Find all keys with mandate_wizard prefix
            keys = self.redis.keys("mandate_wizard:*")
            if keys:
                self.redis.delete(*keys)
                print(f"✅ Cleared {len(keys)} cache entries")
            return True
        except Exception as e:
            print(f"⚠️ Cache clear error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        if not self.enabled:
            return {'enabled': False}
        
        try:
            info = self.redis.info('stats')
            keys = self.redis.keys("mandate_wizard:*")
            
            return {
                'enabled': True,
                'total_keys': len(keys),
                'total_commands': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                )
            }
        except Exception as e:
            print(f"⚠️ Cache stats error: {e}")
            return {'enabled': True, 'error': str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage."""
        total = hits + misses
        if total == 0:
            return 0.0
        return (hits / total) * 100


# Singleton instance
_cache_instance = None

def get_cache() -> CacheManager:
    """Get or create singleton cache manager instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheManager()
    return _cache_instance


# Cache TTL constants (in seconds)
RESPONSE_TTL = 3600 * 24  # 24 hours for full responses
VECTOR_TTL = 3600 * 12    # 12 hours for vector search results
EMBEDDING_TTL = 3600 * 24 * 7  # 7 days for embeddings (rarely change)


# Example usage
if __name__ == "__main__":
    # Test the cache
    cache = CacheManager()
    
    # Test response caching
    question = "Who handles Korean content?"
    response = {
        'answer': 'Don Kang is VP of Content for Korea...',
        'followups': ['What are recent mandates?', 'Who reports to Don Kang?']
    }
    
    print("\n1. Testing response cache...")
    cache.set('response', question, response, ttl=RESPONSE_TTL)
    cached = cache.get('response', question)
    print(f"   Cached: {cached is not None}")
    print(f"   Match: {cached == response}")
    
    # Test vector search caching
    print("\n2. Testing vector search cache...")
    vector_results = {
        'ids': ['doc1', 'doc2'],
        'documents': ['text1', 'text2']
    }
    cache.set('vector', question, vector_results, ttl=VECTOR_TTL)
    cached_vector = cache.get('vector', question)
    print(f"   Cached: {cached_vector is not None}")
    
    # Test embedding caching
    print("\n3. Testing embedding cache...")
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
    cache.set('embedding', question, embedding, ttl=EMBEDDING_TTL)
    cached_embedding = cache.get('embedding', question)
    print(f"   Cached: {cached_embedding is not None}")
    
    # Get stats
    print("\n4. Cache statistics:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Clear all
    print("\n5. Clearing cache...")
    cache.clear_all()

