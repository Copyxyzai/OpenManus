"""
Search Result Cache with TTL and LRU Eviction

Provides caching for search results to reduce API calls and improve performance.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from app.logger import logger


class SearchCache:
    """LRU cache with TTL for search results"""

    def __init__(self, ttl: int = 3600, max_size: int = 100):
        """
        Initialize cache

        Args:
            ttl: Time to live in seconds (default: 1 hour)
            max_size: Maximum number of cached items (default: 100)
        """
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self._ttl = ttl
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def get_cache_key(self, query: str, **params) -> str:
        """
        Generate cache key from query and parameters

        Args:
            query: Search query
            **params: Additional parameters

        Returns:
            Cache key string
        """
        param_str = ":".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{query}:{param_str}" if param_str else query

    def get(self, key: str) -> Optional[Any]:
        """
        Get cached result if not expired

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key in self._cache:
            result, timestamp = self._cache[key]

            # Check if expired
            if datetime.now() - timestamp < timedelta(seconds=self._ttl):
                self._hits += 1
                logger.info(f"✅ Cache hit: {key[:50]}...")
                return result
            else:
                # Expired, remove
                del self._cache[key]
                self._misses += 1
        else:
            self._misses += 1

        return None

    def set(self, key: str, value: Any):
        """
        Store result in cache with LRU eviction

        Args:
            key: Cache key
            value: Value to store
        """
        # LRU eviction if at capacity
        if len(self._cache) >= self._max_size:
            # Find and remove oldest entry
            oldest_key = min(
                self._cache.items(), key=lambda x: x[1][1]  # Sort by timestamp
            )[0]
            del self._cache[oldest_key]
            logger.debug(f"🗑️ Evicted oldest cache entry: {oldest_key[:50]}...")

        # Store with current timestamp
        self._cache[key] = (value, datetime.now())
        logger.debug(f"💾 Cached: {key[:50]}...")

    def clear(self):
        """Clear all cached entries"""
        self._cache.clear()
        logger.info("🗑️ Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats
        """
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "ttl": self._ttl,
        }
