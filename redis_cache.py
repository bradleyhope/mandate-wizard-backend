"""
Redis Distributed Cache
Shared cache across multiple server instances
"""

import json
import hashlib
from typing import Any, Optional
import os


try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class RedisCache:
    """
    Distributed cache using Redis

    Benefits:
    - Shared across multiple server instances
    - Persistent across restarts
    - Sub-millisecond lookups
    - Automatic expiration (TTL)
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: int = 1800,  # 30 minutes
        key_prefix: str = 'mandatewizard:'
    ):
        """
        Initialize Redis cache

        Args:
            redis_url: Redis connection URL (redis://host:port/db)
            default_ttl: Default time-to-live in seconds
            key_prefix: Prefix for all keys
        """
        self.redis_url = redis_url or os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix

        # Initialize Redis client
        self.client = None
        self.available = False

        if REDIS_AVAILABLE:
            try:
                self.client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                # Test connection
                self.client.ping()
                self.available = True
                print(f"✓ Connected to Redis at {self.redis_url}")
            except Exception as e:
                print(f"⚠️ Redis connection failed: {e}")
                print("  Falling back to in-memory cache")
                self.available = False
        else:
            print("⚠️ redis-py not installed, using in-memory cache")
            print("  Install with: pip install redis")

        # Fallback in-memory cache
        self.memory_cache = {}

    def _make_key(self, key: str) -> str:
        """Create full Redis key with prefix"""
        return f"{self.key_prefix}{key}"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        full_key = self._make_key(key)

        if self.available and self.client:
            try:
                value = self.client.get(full_key)
                if value:
                    return json.loads(value)
                return None
            except Exception as e:
                print(f"⚠️ Redis GET failed: {e}")
                # Fall through to memory cache

        # Fallback to memory cache
        if key in self.memory_cache:
            value, expiry = self.memory_cache[key]
            import time
            if time.time() < expiry:
                return value
            else:
                del self.memory_cache[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time-to-live in seconds (None = default)
        """
        full_key = self._make_key(key)
        ttl = ttl or self.default_ttl

        if self.available and self.client:
            try:
                serialized = json.dumps(value)
                self.client.setex(full_key, ttl, serialized)
                return
            except Exception as e:
                print(f"⚠️ Redis SET failed: {e}")
                # Fall through to memory cache

        # Fallback to memory cache
        import time
        self.memory_cache[key] = (value, time.time() + ttl)

    def delete(self, key: str):
        """Delete key from cache"""
        full_key = self._make_key(key)

        if self.available and self.client:
            try:
                self.client.delete(full_key)
                return
            except Exception as e:
                print(f"⚠️ Redis DELETE failed: {e}")

        # Fallback to memory cache
        if key in self.memory_cache:
            del self.memory_cache[key]

    def clear(self):
        """Clear all keys with prefix"""
        if self.available and self.client:
            try:
                # Find all keys with prefix
                pattern = f"{self.key_prefix}*"
                keys = self.client.keys(pattern)
                if keys:
                    self.client.delete(*keys)
                print(f"✓ Cleared {len(keys)} keys from Redis")
                return
            except Exception as e:
                print(f"⚠️ Redis CLEAR failed: {e}")

        # Fallback to memory cache
        self.memory_cache.clear()

    def get_stats(self) -> dict:
        """Get cache statistics"""
        stats = {
            'available': self.available,
            'redis_url': self.redis_url if self.available else None,
            'memory_cache_size': len(self.memory_cache)
        }

        if self.available and self.client:
            try:
                info = self.client.info('stats')
                stats['redis_stats'] = {
                    'total_connections': info.get('total_connections_received', 0),
                    'total_commands': info.get('total_commands_processed', 0),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0)
                }

                # Calculate hit rate
                hits = stats['redis_stats']['keyspace_hits']
                misses = stats['redis_stats']['keyspace_misses']
                total = hits + misses
                if total > 0:
                    stats['redis_stats']['hit_rate'] = round(hits / total, 3)

                # Count keys with prefix
                pattern = f"{self.key_prefix}*"
                stats['key_count'] = len(self.client.keys(pattern))

            except Exception as e:
                print(f"⚠️ Failed to get Redis stats: {e}")

        return stats

    def health_check(self) -> bool:
        """Check if Redis is healthy"""
        if not self.available or not self.client:
            return False

        try:
            self.client.ping()
            return True
        except Exception:
            return False


# Global instance
_redis_cache = None


def get_redis_cache() -> RedisCache:
    """Get or create global Redis cache instance"""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCache()
    return _redis_cache


# Example usage
if __name__ == '__main__':
    cache = RedisCache()

    print("\nTesting Redis cache...")

    # Test set/get
    cache.set('test_key', {'message': 'Hello Redis!'}, ttl=60)
    value = cache.get('test_key')
    print(f"Got value: {value}")

    # Test stats
    stats = cache.get_stats()
    print(f"\nCache stats: {json.dumps(stats, indent=2)}")

    # Test health
    healthy = cache.health_check()
    print(f"\nRedis healthy: {healthy}")
