"""Result caching system with TTL and statistics tracking.

This module provides hash-based memoization of execution results with
configurable time-to-live (TTL) and comprehensive statistics tracking.

Features:
- MD5-based result hashing for code lookup
- Configurable TTL and cache size limits
- Hit/miss tracking and statistics
- Memory-efficient caching
- Cache invalidation and expiration
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from agent_discovery.result_processor import EnhancedResult


@dataclass
class CacheEntry:
    """Single cached result entry."""

    code_hash: str
    """MD5 hash of the code that produced this result."""

    result: EnhancedResult
    """Cached execution result."""

    timestamp: datetime
    """When this result was cached."""

    ttl_seconds: int
    """Time-to-live in seconds."""

    hit_count: int = 0
    """Number of times this entry has been retrieved."""

    last_accessed: datetime = field(default_factory=datetime.now)
    """Timestamp of last access."""

    def is_expired(self) -> bool:
        """Check if cache entry has expired.

        Returns:
            True if entry has exceeded TTL
        """
        expiration_time = self.timestamp + timedelta(seconds=self.ttl_seconds)
        return datetime.now() > expiration_time

    def record_hit(self) -> None:
        """Record a cache hit."""
        self.hit_count += 1
        self.last_accessed = datetime.now()


@dataclass
class CacheStatistics:
    """Cache performance statistics."""

    total_hits: int = 0
    """Total number of cache hits."""

    total_misses: int = 0
    """Total number of cache misses."""

    total_entries: int = 0
    """Current number of entries in cache."""

    max_entries: int = 500
    """Maximum allowed entries in cache."""

    total_evicted: int = 0
    """Number of entries evicted due to size limits."""

    total_expired: int = 0
    """Number of entries expired due to TTL."""

    avg_hit_rate: float = 0.0
    """Average hit rate (0-1)."""

    avg_entry_size_bytes: int = 0
    """Average size of cached entries."""

    memory_used_mb: float = 0.0
    """Estimated memory usage in MB."""

    def get_hit_rate(self) -> float:
        """Calculate current hit rate.

        Returns:
            Hit rate as percentage (0-1)
        """
        total_requests = self.total_hits + self.total_misses
        return self.total_hits / total_requests if total_requests > 0 else 0.0

    def update_memory_stats(self, cache: dict[str, CacheEntry]) -> None:
        """Update memory statistics from cache.

        Args:
            cache: The cache dictionary
        """
        if not cache:
            self.memory_used_mb = 0.0
            self.avg_entry_size_bytes = 0
            self.total_entries = 0
            return

        self.total_entries = len(cache)
        total_size = 0

        for entry in cache.values():
            # Estimate entry size
            entry_size = (
                len(entry.code_hash)
                + len(str(entry.result))
                + 56  # Approximate overhead for dataclass fields
            )
            total_size += entry_size

        self.avg_entry_size_bytes = total_size // len(cache) if cache else 0
        self.memory_used_mb = total_size / (1024 * 1024)


class ResultCache:
    """Hash-based result caching with TTL and statistics.

    The ResultCache stores execution results keyed by code hash, allowing
    fast lookup of previously executed code patterns. Results expire based
    on configurable TTL, and cache size is managed with LRU eviction.
    """

    def __init__(
        self,
        max_entries: int = 500,
        default_ttl_seconds: int = 1800,
        eviction_policy: str = "lru",
    ):
        """Initialize result cache.

        Args:
            max_entries: Maximum number of cached entries (default 500)
            default_ttl_seconds: Default TTL in seconds (default 30 minutes)
            eviction_policy: Eviction policy ("lru" or "lfu")
        """
        self.max_entries = max_entries
        self.default_ttl_seconds = default_ttl_seconds
        self.eviction_policy = eviction_policy
        self._cache: dict[str, CacheEntry] = {}
        self.stats = CacheStatistics(max_entries=max_entries)

    def get(self, code: str) -> EnhancedResult | None:
        """Retrieve cached result for code.

        Args:
            code: Code to look up

        Returns:
            EnhancedResult if found and valid, None otherwise
        """
        code_hash = self._hash_code(code)
        entry = self._cache.get(code_hash)

        if entry is None:
            self.stats.total_misses += 1
            return None

        # Check if expired
        if entry.is_expired():
            del self._cache[code_hash]
            self.stats.total_expired += 1
            self.stats.total_misses += 1
            return None

        # Record hit
        entry.record_hit()
        self.stats.total_hits += 1
        return entry.result

    def put(
        self,
        code: str,
        result: EnhancedResult,
        ttl_seconds: int | None = None,
    ) -> None:
        """Store result in cache.

        Args:
            code: Code that was executed
            result: Result to cache
            ttl_seconds: Optional custom TTL (uses default if not provided)
        """
        if not result.is_cacheable:
            return

        code_hash = self._hash_code(code)
        ttl = ttl_seconds or self.default_ttl_seconds

        # Check if we need to evict
        if len(self._cache) >= self.max_entries:
            self._evict_one_entry()

        entry = CacheEntry(
            code_hash=code_hash,
            result=result,
            timestamp=datetime.now(),
            ttl_seconds=ttl,
        )

        self._cache[code_hash] = entry

    def clear(self) -> None:
        """Clear entire cache and reset statistics."""
        self._cache.clear()
        self.stats = CacheStatistics(max_entries=self.max_entries)

    def cleanup_expired(self) -> int:
        """Remove all expired entries.

        Returns:
            Number of entries removed
        """
        expired_hashes = [
            code_hash for code_hash, entry in self._cache.items() if entry.is_expired()
        ]

        for code_hash in expired_hashes:
            del self._cache[code_hash]
            self.stats.total_expired += 1

        return len(expired_hashes)

    def get_statistics(self) -> CacheStatistics:
        """Get current cache statistics.

        Returns:
            CacheStatistics with current data
        """
        # Clean up expired entries
        self.cleanup_expired()

        # Update statistics
        self.stats.avg_hit_rate = self.stats.get_hit_rate()
        self.stats.update_memory_stats(self._cache)

        return self.stats

    def export_cache(self, include_expired: bool = False) -> dict[str, Any]:
        """Export cache contents as dictionary.

        Args:
            include_expired: Whether to include expired entries

        Returns:
            Dictionary with cache contents
        """
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "stats": {
                "total_entries": len(self._cache),
                "total_hits": self.stats.total_hits,
                "total_misses": self.stats.total_misses,
                "hit_rate": self.stats.get_hit_rate(),
            },
            "entries": {},
        }

        for code_hash, entry in self._cache.items():
            if not include_expired and entry.is_expired():
                continue

            export_data["entries"][code_hash] = {
                "timestamp": entry.timestamp.isoformat(),
                "ttl_seconds": entry.ttl_seconds,
                "hit_count": entry.hit_count,
                "is_expired": entry.is_expired(),
                "result_summary": {
                    "category": entry.result.category.value,
                    "is_successful": entry.result.is_successful,
                    "is_cacheable": entry.result.is_cacheable,
                },
            }

        return export_data

    def import_cache(self, cache_data: dict[str, Any]) -> bool:
        """Import cache from exported format.

        Note: This is a partial import - only metadata is restored.
        Full result objects cannot be deserialized without the original
        orchestrated results.

        Args:
            cache_data: Exported cache data

        Returns:
            True if import was successful
        """
        try:
            entries = cache_data.get("entries", {})
            for _, entry_data in entries.items():
                # Verify structure
                if not all(k in entry_data for k in ["timestamp", "ttl_seconds"]):
                    return False
            return True
        except (KeyError, TypeError, ValueError):
            return False

    def get_hot_entries(self, top_n: int = 10) -> list[tuple[str, int]]:
        """Get most frequently accessed entries.

        Args:
            top_n: Number of top entries to return

        Returns:
            List of (code_hash, hit_count) tuples
        """
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].hit_count,
            reverse=True,
        )
        return [(code_hash, entry.hit_count) for code_hash, entry in sorted_entries[:top_n]]

    def _hash_code(self, code: str) -> str:
        """Generate MD5 hash of code.

        Args:
            code: Code to hash

        Returns:
            MD5 hash string
        """
        return hashlib.md5(code.encode()).hexdigest()

    def _evict_one_entry(self) -> None:
        """Evict one entry based on eviction policy."""
        if not self._cache:
            return

        if self.eviction_policy == "lru":
            # Find least recently used
            lru_entry = min(
                self._cache.items(),
                key=lambda x: x[1].last_accessed,
            )
            del self._cache[lru_entry[0]]
        elif self.eviction_policy == "lfu":
            # Find least frequently used
            lfu_entry = min(
                self._cache.items(),
                key=lambda x: x[1].hit_count,
            )
            del self._cache[lfu_entry[0]]
        else:
            # Default: remove first (FIFO)
            first_key = next(iter(self._cache))
            del self._cache[first_key]

        self.stats.total_evicted += 1
