"""
Error Handling and Retry Logic for Background Worker
"""

import time
from typing import Dict, Callable, Any
from datetime import datetime


class RetryTracker:
    """Track retry counts for events"""
    
    def __init__(self):
        self.retry_counts = {}  # event_id -> retry_count
        self.last_retry_time = {}  # event_id -> timestamp
        
    def get_retry_count(self, event_id: str) -> int:
        """Get current retry count for an event"""
        return self.retry_counts.get(event_id, 0)
    
    def increment_retry(self, event_id: str):
        """Increment retry count for an event"""
        self.retry_counts[event_id] = self.get_retry_count(event_id) + 1
        self.last_retry_time[event_id] = time.time()
    
    def clear_retry(self, event_id: str):
        """Clear retry count after successful processing"""
        if event_id in self.retry_counts:
            del self.retry_counts[event_id]
        if event_id in self.last_retry_time:
            del self.last_retry_time[event_id]
    
    def should_retry(self, event_id: str, max_retries: int = 3) -> bool:
        """Check if event should be retried"""
        return self.get_retry_count(event_id) < max_retries
    
    def get_backoff_delay(self, event_id: str) -> float:
        """Calculate exponential backoff delay in seconds"""
        retry_count = self.get_retry_count(event_id)
        # Exponential backoff: 1s, 2s, 4s, 8s, ...
        return min(2 ** retry_count, 60)  # Cap at 60 seconds


# Global retry tracker instance
_retry_tracker = RetryTracker()


def process_with_retry(
    event: Dict[str, Any],
    handler: Callable,
    acknowledge_fn: Callable,
    max_retries: int = 3
) -> bool:
    """
    Process an event with retry logic
    
    Args:
        event: Event dictionary with 'id', 'stream', 'data'
        handler: Function to process the event data
        acknowledge_fn: Function to acknowledge the event
        max_retries: Maximum number of retries before giving up
        
    Returns:
        True if processed successfully, False if failed permanently
    """
    event_id = event['id']
    retry_count = _retry_tracker.get_retry_count(event_id)
    
    try:
        # Check if we should apply backoff delay
        if retry_count > 0:
            delay = _retry_tracker.get_backoff_delay(event_id)
            last_retry = _retry_tracker.last_retry_time.get(event_id, 0)
            time_since_last = time.time() - last_retry
            
            if time_since_last < delay:
                # Too soon to retry, skip for now
                return False
        
        # Try to process the event
        handler(event['data'])
        
        # Success! Acknowledge and clear retry count
        acknowledge_fn()
        _retry_tracker.clear_retry(event_id)
        
        return True
        
    except Exception as e:
        # Processing failed
        _retry_tracker.increment_retry(event_id)
        retry_count = _retry_tracker.get_retry_count(event_id)
        
        if retry_count >= max_retries:
            # Max retries exceeded - move to dead letter queue
            print(f"❌ Event {event_id} failed after {max_retries} retries: {e}")
            print(f"   Moving to dead letter queue")
            
            # Log to dead letter queue (for now, just acknowledge to remove from stream)
            # TODO: Implement proper dead letter queue storage
            acknowledge_fn()
            _retry_tracker.clear_retry(event_id)
            
            return False
        else:
            # Will retry later
            backoff = _retry_tracker.get_backoff_delay(event_id)
            print(f"⚠️  Event {event_id} failed (retry {retry_count}/{max_retries}): {e}")
            print(f"   Will retry in {backoff}s")
            
            # Don't acknowledge - will retry
            return False


def log_error(event: Dict[str, Any], error: Exception, retry_count: int):
    """
    Log error details for debugging
    
    Args:
        event: Event that failed
        error: Exception that occurred
        retry_count: Current retry count
    """
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] ERROR processing event {event['id']}")
    print(f"  Stream: {event['stream']}")
    print(f"  Retry: {retry_count}")
    print(f"  Error: {type(error).__name__}: {error}")
    print(f"  Data: {event['data']}")


def get_retry_stats() -> Dict[str, Any]:
    """Get statistics about retries"""
    return {
        'events_with_retries': len(_retry_tracker.retry_counts),
        'retry_counts': dict(_retry_tracker.retry_counts),
        'total_retries': sum(_retry_tracker.retry_counts.values())
    }
