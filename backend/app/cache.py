# backend/app/cache.py
"""
Simple in-memory caching for performance optimization
Reduces database load and improves response times
"""

import time
from typing import Optional, Dict, Any, Callable
from threading import Lock

class SimpleCache:
    """Thread-safe cache with TTL"""
    
    def __init__(self, ttl_seconds: int = 10):
        self.ttl = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        with self.lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            if time.time() - entry['timestamp'] > self.ttl:
                # Expired
                del self.cache[key]
                return None
            
            return entry['value']
    
    def set(self, key: str, value: Any):
        """Set cached value with current timestamp"""
        with self.lock:
            self.cache[key] = {
                'value': value,
                'timestamp': time.time()
            }
    
    def invalidate(self, key: str):
        """Remove specific key from cache"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
    
    def clear(self):
        """Clear entire cache"""
        with self.lock:
            self.cache.clear()
    
    async def get_or_fetch(self, key: str, fetch_func: Callable) -> Any:
        """Get from cache or fetch and cache if not present"""
        cached = self.get(key)
        if cached is not None:
            return cached
        
        # Fetch fresh data
        value = await fetch_func()
        self.set(key, value)
        return value


# Global cache instances
patient_cache = SimpleCache(ttl_seconds=30)  # Patient data changes infrequently
alert_cache = SimpleCache(ttl_seconds=5)     # Alerts need fresher data
stats_cache = SimpleCache(ttl_seconds=10)    # Stats can be slightly stale
stream_cache = SimpleCache(ttl_seconds=2)    # Streams need near real-time

