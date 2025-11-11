"""
Background Worker for Mandate Wizard
Processes events from Redis Streams asynchronously
"""

import sys
import os
import time
import signal
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from streams import get_streams_client
from worker.handlers.query_signal_handler import handle_query_signal
from worker.handlers.update_request_handler import handle_update_request
from worker.error_handler import process_with_retry, get_retry_stats


class BackgroundWorker:
    """Main background worker process"""
    
    def __init__(self):
        """Initialize worker"""
        self.running = True
        self.streams_client = get_streams_client()
        
        # Consumer group and name from environment or defaults
        self.consumer_group = os.getenv('WORKER_CONSUMER_GROUP', 'mandate-wizard-workers')
        self.consumer_name = os.getenv('WORKER_CONSUMER_NAME', f'worker-{os.getpid()}')
        
        # Statistics
        self.stats = {
            'started_at': datetime.now().isoformat(),
            'query_signals_processed': 0,
            'update_requests_processed': 0,
            'errors': 0
        }
        
        print(f"🚀 Background Worker Starting...")
        print(f"   Consumer Group: {self.consumer_group}")
        print(f"   Consumer Name: {self.consumer_name}")
        print(f"   Process ID: {os.getpid()}")
        print(f"   Started: {self.stats['started_at']}")
        
    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)
        
    def handle_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        print(f"\n⚠️  Received shutdown signal ({signum})")
        print("📊 Final Statistics:")
        print(f"   Query Signals Processed: {self.stats['query_signals_processed']}")
        print(f"   Update Requests Processed: {self.stats['update_requests_processed']}")
        print(f"   Errors: {self.stats['errors']}")
        print("👋 Shutting down gracefully...")
        self.running = False
        
    def process_query_signals(self):
        """Process QuerySignal events"""
        try:
            events = self.streams_client.consume_query_signals(
                consumer_group=self.consumer_group,
                consumer_name=self.consumer_name,
                block_ms=1000,  # Block for 1 second
                count=10  # Process up to 10 events at once
            )
            
            for event in events:
                # Use retry logic
                def acknowledge():
                    self.streams_client.acknowledge_event(
                        stream=event['stream'],
                        consumer_group=self.consumer_group,
                        event_id=event['id']
                    )
                
                success = process_with_retry(
                    event=event,
                    handler=handle_query_signal,
                    acknowledge_fn=acknowledge,
                    max_retries=3
                )
                
                if success:
                    self.stats['query_signals_processed'] += 1
                    
                    # Log every 10 events
                    if self.stats['query_signals_processed'] % 10 == 0:
                        print(f"✅ Processed {self.stats['query_signals_processed']} QuerySignal events")
                else:
                    self.stats['errors'] += 1
                    
        except Exception as e:
            print(f"❌ Error consuming QuerySignals: {e}")
            self.stats['errors'] += 1
            
    def process_update_requests(self):
        """Process UpdateRequest events"""
        try:
            events = self.streams_client.consume_update_requests(
                consumer_group=self.consumer_group,
                consumer_name=self.consumer_name,
                block_ms=1000,  # Block for 1 second
                count=5  # Process up to 5 events at once (these are heavier)
            )
            
            for event in events:
                # Use retry logic
                def acknowledge():
                    self.streams_client.acknowledge_event(
                        stream=event['stream'],
                        consumer_group=self.consumer_group,
                        event_id=event['id']
                    )
                
                success = process_with_retry(
                    event=event,
                    handler=handle_update_request,
                    acknowledge_fn=acknowledge,
                    max_retries=3
                )
                
                if success:
                    self.stats['update_requests_processed'] += 1
                    print(f"✅ Processed UpdateRequest {event['id']}")
                else:
                    self.stats['errors'] += 1
                    
        except Exception as e:
            print(f"❌ Error consuming UpdateRequests: {e}")
            self.stats['errors'] += 1
            
    def run(self):
        """Main event loop"""
        self.setup_signal_handlers()
        
        print("✅ Worker ready - waiting for events...")
        print("   (Press Ctrl+C to stop)")
        print()
        
        iteration = 0
        
        while self.running:
            iteration += 1
            
            # Process both event types
            self.process_query_signals()
            self.process_update_requests()
            
            # Print status every 60 iterations (~1 minute)
            if iteration % 60 == 0:
                retry_stats = get_retry_stats()
                print(f"💓 Heartbeat - Worker alive (iteration {iteration})")
                print(f"   Query Signals: {self.stats['query_signals_processed']}")
                print(f"   Update Requests: {self.stats['update_requests_processed']}")
                print(f"   Errors: {self.stats['errors']}")
                print(f"   Retrying: {retry_stats['events_with_retries']} events")
            
            # Small sleep to avoid busy-waiting
            time.sleep(0.1)
        
        print("✅ Worker stopped cleanly")


def main():
    """Entry point"""
    try:
        worker = BackgroundWorker()
        worker.run()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
