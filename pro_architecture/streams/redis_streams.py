"""
Redis Streams Client for Mandate Wizard
Handles event publishing and consumption for async processing
"""

import json
import time
from typing import Dict, Any, Optional, List
from redis import Redis
import os


class RedisStreamsClient:
    """Client for publishing and consuming events via Redis Streams"""
    
    def __init__(self):
        """Initialize Redis connection using environment variables"""
        self.redis = Redis(
            host=os.getenv('REDIS_HOST'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            password=os.getenv('REDIS_PASSWORD'),
            db=int(os.getenv('REDIS_DB', 0)),
            decode_responses=True
        )
        
        # Stream names
        self.QUERY_SIGNAL_STREAM = 'mandate_wizard:query_signals'
        self.UPDATE_REQUEST_STREAM = 'mandate_wizard:update_requests'
        
    def publish_query_signal(self, entity_id: str, entity_type: str, 
                            query: str, user_id: Optional[str] = None) -> str:
        """
        Publish a QuerySignal event when a user queries an entity
        
        Args:
            entity_id: UUID of the entity that was queried
            entity_type: Type of entity (person, company, etc.)
            query: The user's original query text
            user_id: Optional user identifier
            
        Returns:
            Event ID from Redis Streams
        """
        event_data = {
            'event_type': 'query_signal',
            'entity_id': entity_id,
            'entity_type': entity_type,
            'query': query,
            'user_id': user_id or 'anonymous',
            'timestamp': int(time.time())
        }
        
        # Publish to Redis Streams
        event_id = self.redis.xadd(
            self.QUERY_SIGNAL_STREAM,
            event_data,
            maxlen=10000  # Keep last 10k events
        )
        
        return event_id
    
    def publish_update_request(self, entity_ids: List[str], 
                               operation: str, source: str) -> str:
        """
        Publish an UpdateRequest event when data needs to be synced
        
        Args:
            entity_ids: List of entity UUIDs that need syncing
            operation: Type of operation (create, update, delete)
            source: Source of the update (newsletter, manual, api)
            
        Returns:
            Event ID from Redis Streams
        """
        event_data = {
            'event_type': 'update_request',
            'entity_ids': json.dumps(entity_ids),
            'operation': operation,
            'source': source,
            'timestamp': int(time.time())
        }
        
        # Publish to Redis Streams
        event_id = self.redis.xadd(
            self.UPDATE_REQUEST_STREAM,
            event_data,
            maxlen=5000  # Keep last 5k events
        )
        
        return event_id
    
    def consume_query_signals(self, consumer_group: str, consumer_name: str,
                             block_ms: int = 5000, count: int = 10) -> List[Dict[str, Any]]:
        """
        Consume QuerySignal events from the stream
        
        Args:
            consumer_group: Name of the consumer group
            consumer_name: Name of this consumer instance
            block_ms: How long to block waiting for new events (milliseconds)
            count: Maximum number of events to read at once
            
        Returns:
            List of events with their IDs and data
        """
        # Ensure consumer group exists
        try:
            self.redis.xgroup_create(
                self.QUERY_SIGNAL_STREAM,
                consumer_group,
                id='0',
                mkstream=True
            )
        except Exception:
            # Group already exists
            pass
        
        # Read new events
        events = self.redis.xreadgroup(
            consumer_group,
            consumer_name,
            {self.QUERY_SIGNAL_STREAM: '>'},
            count=count,
            block=block_ms
        )
        
        # Parse events
        parsed_events = []
        if events:
            for stream_name, messages in events:
                for message_id, data in messages:
                    parsed_events.append({
                        'id': message_id,
                        'stream': stream_name,
                        'data': data
                    })
        
        return parsed_events
    
    def consume_update_requests(self, consumer_group: str, consumer_name: str,
                               block_ms: int = 5000, count: int = 10) -> List[Dict[str, Any]]:
        """
        Consume UpdateRequest events from the stream
        
        Args:
            consumer_group: Name of the consumer group
            consumer_name: Name of this consumer instance
            block_ms: How long to block waiting for new events (milliseconds)
            count: Maximum number of events to read at once
            
        Returns:
            List of events with their IDs and data
        """
        # Ensure consumer group exists
        try:
            self.redis.xgroup_create(
                self.UPDATE_REQUEST_STREAM,
                consumer_group,
                id='0',
                mkstream=True
            )
        except Exception:
            # Group already exists
            pass
        
        # Read new events
        events = self.redis.xreadgroup(
            consumer_group,
            consumer_name,
            {self.UPDATE_REQUEST_STREAM: '>'},
            count=count,
            block=block_ms
        )
        
        # Parse events
        parsed_events = []
        if events:
            for stream_name, messages in events:
                for message_id, data in messages:
                    # Parse entity_ids JSON
                    if 'entity_ids' in data:
                        data['entity_ids'] = json.loads(data['entity_ids'])
                    
                    parsed_events.append({
                        'id': message_id,
                        'stream': stream_name,
                        'data': data
                    })
        
        return parsed_events
    
    def acknowledge_event(self, stream: str, consumer_group: str, event_id: str):
        """
        Acknowledge that an event has been processed
        
        Args:
            stream: Name of the stream
            consumer_group: Name of the consumer group
            event_id: ID of the event to acknowledge
        """
        self.redis.xack(stream, consumer_group, event_id)
    
    def get_stream_info(self, stream: str) -> Dict[str, Any]:
        """
        Get information about a stream
        
        Args:
            stream: Name of the stream
            
        Returns:
            Dictionary with stream information
        """
        try:
            info = self.redis.xinfo_stream(stream)
            return {
                'length': info['length'],
                'first_entry': info['first-entry'],
                'last_entry': info['last-entry'],
                'groups': info['groups']
            }
        except Exception as e:
            return {'error': str(e)}
    
    def health_check(self) -> bool:
        """Check if Redis connection is healthy"""
        try:
            self.redis.ping()
            return True
        except Exception:
            return False


# Singleton instance
_streams_client = None

def get_streams_client() -> RedisStreamsClient:
    """Get or create the Redis Streams client singleton"""
    global _streams_client
    if _streams_client is None:
        _streams_client = RedisStreamsClient()
    return _streams_client
