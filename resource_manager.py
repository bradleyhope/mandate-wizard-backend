"""
Resource Manager
Handles cleanup and resource management to prevent memory leaks and connection exhaustion
"""

import gc
import psutil
import os
from datetime import datetime

class ResourceManager:
    """Manages system resources and prevents leaks"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.query_count = 0
        self.last_cleanup = datetime.now()
    
    def check_memory_usage(self):
        """Check current memory usage"""
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        return memory_mb
    
    def cleanup_if_needed(self):
        """Perform cleanup if memory usage is high"""
        self.query_count += 1
        
        # Cleanup every 10 queries or if memory > 1GB
        memory_mb = self.check_memory_usage()
        should_cleanup = (
            self.query_count % 10 == 0 or
            memory_mb > 1024
        )
        
        if should_cleanup:
            print(f"[RESOURCE] Performing cleanup (queries: {self.query_count}, memory: {memory_mb:.1f}MB)")
            
            # Force garbage collection
            gc.collect()
            
            # Log memory after cleanup
            new_memory = self.check_memory_usage()
            freed = memory_mb - new_memory
            print(f"[RESOURCE] Cleanup complete (freed: {freed:.1f}MB, current: {new_memory:.1f}MB)")
            
            self.last_cleanup = datetime.now()
            
            return True
        
        return False
    
    def get_stats(self):
        """Get current resource stats"""
        return {
            'query_count': self.query_count,
            'memory_mb': self.check_memory_usage(),
            'cpu_percent': self.process.cpu_percent(),
            'last_cleanup': self.last_cleanup.isoformat()
        }

# Global instance
resource_manager = ResourceManager()

def get_resource_manager():
    """Get the global resource manager instance"""
    return resource_manager

