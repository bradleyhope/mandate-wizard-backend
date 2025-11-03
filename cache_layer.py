"""
Redis Caching Layer
Caches frequent queries to reduce GPT-5 API calls
"""

import redis
import json
import hashlib
from functools import wraps

class CacheLayer:
    def __init__(self, host='localhost', port=6379, db=0):
        try:
            self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.redis_client.ping()
            self.enabled = True
        except:
            print("Warning: Redis not available, caching disabled")
            self.enabled = False
        
        # Cache TTLs (seconds)
        self.QUERY_CACHE_TTL = 3600  # 1 hour
        self.AUTH_CACHE_TTL = 600    # 10 minutes
    
    def get_query_key(self, question, session_id='default'):
        """Generate cache key for query"""
        key_str = f"query:{session_id}:{question}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get_cached_query(self, question, session_id='default'):
        """Get cached query result"""
        if not self.enabled:
            return None
        
        try:
            key = self.get_query_key(question, session_id)
            cached = self.redis_client.get(key)
            if cached:
                return json.loads(cached)
        except:
            pass
        return None
    
    def cache_query(self, question, result, session_id='default'):
        """Cache query result"""
        if not self.enabled:
            return
        
        try:
            key = self.get_query_key(question, session_id)
            self.redis_client.setex(
                key,
                self.QUERY_CACHE_TTL,
                json.dumps(result)
            )
        except:
            pass
    
    def get_cached_auth(self, email):
        """Get cached auth result"""
        if not self.enabled:
            return None
        
        try:
            key = f"auth:{email}"
            cached = self.redis_client.get(key)
            if cached:
                return json.loads(cached)
        except:
            pass
        return None
    
    def cache_auth(self, email, auth_result):
        """Cache auth result"""
        if not self.enabled:
            return
        
        try:
            key = f"auth:{email}"
            self.redis_client.setex(
                key,
                self.AUTH_CACHE_TTL,
                json.dumps(auth_result)
            )
        except:
            pass
    
    def invalidate_auth(self, email):
        """Invalidate cached auth"""
        if not self.enabled:
            return
        
        try:
            key = f"auth:{email}"
            self.redis_client.delete(key)
        except:
            pass
    
    def get_stats(self):
        """Get cache statistics"""
        if not self.enabled:
            return {'enabled': False}
        
        try:
            info = self.redis_client.info('stats')
            return {
                'enabled': True,
                'total_commands': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': info.get('keyspace_hits', 0) / max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1), 1)
            }
        except:
            return {'enabled': False}

# Global cache instance
cache_layer = CacheLayer()
