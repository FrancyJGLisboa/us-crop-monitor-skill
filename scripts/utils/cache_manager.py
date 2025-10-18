#!/usr/bin/env python3
"""
Cache Manager for NASS API Data

Provides intelligent caching with TTL-based expiration for optimal performance.
Historical data (>2 weeks old) cached permanently. Recent data cached with 7-day TTL.

Author: Agent Creator
Version: 1.0.0
"""

import json
import hashlib
import os
import time
from pathlib import Path
from typing import Any, Optional, Dict
from datetime import datetime, timedelta


class CacheManager:
    """
    Manages file-based cache for NASS API responses.

    Features:
    - TTL-based expiration
    - Automatic cleanup
    - Pattern-based invalidation
    - Separate historical and recent data storage
    """

    def __init__(self, cache_dir: str = "data/cache"):
        """
        Initialize cache manager.

        Args:
            cache_dir: Base directory for cache storage
        """
        self.cache_dir = Path(cache_dir)
        self.historical_dir = self.cache_dir / "historical"
        self.recent_dir = self.cache_dir / "recent"

        # Create directories
        self.historical_dir.mkdir(parents=True, exist_ok=True)
        self.recent_dir.mkdir(parents=True, exist_ok=True)

    def _generate_key(self, params: Dict[str, Any]) -> str:
        """
        Generate unique cache key from parameters.

        Args:
            params: Request parameters dictionary

        Returns:
            Hash string
        """
        # Sort params for consistent hashing
        sorted_params = json.dumps(params, sort_keys=True)
        hash_obj = hashlib.sha256(sorted_params.encode())
        return hash_obj.hexdigest()[:16]

    def _get_cache_path(self, key: str, is_historical: bool = False) -> Path:
        """
        Get file path for cache key.

        Args:
            key: Cache key
            is_historical: Whether data is historical (>2 weeks old)

        Returns:
            Path to cache file
        """
        directory = self.historical_dir if is_historical else self.recent_dir
        return directory / f"{key}.json"

    def _is_historical(self, params: Dict[str, Any]) -> bool:
        """
        Determine if data should be cached as historical.

        Historical data:
        - Year < current year
        - Week < current week - 2

        Args:
            params: Request parameters

        Returns:
            True if historical
        """
        current_year = datetime.now().year
        current_week = datetime.now().isocalendar()[1]

        param_year = params.get('year')
        param_week = params.get('reference_period_desc', '')

        # Extract week number from "WEEK #XX" format
        if param_week and 'WEEK' in param_week:
            try:
                week_num = int(param_week.split('#')[1])
            except (IndexError, ValueError):
                return False
        else:
            return False

        # Historical if previous year or >2 weeks ago
        if param_year and param_year < current_year:
            return True

        if param_year == current_year and week_num < current_week - 2:
            return True

        return False

    def get(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from cache.

        Args:
            params: Request parameters

        Returns:
            Cached data or None if not found/expired
        """
        key = self._generate_key(params)
        is_hist = self._is_historical(params)
        cache_path = self._get_cache_path(key, is_hist)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r') as f:
                cached = json.load(f)

            # Check expiration (historical never expires)
            if not is_hist:
                expired_at = cached.get('expired_at')
                if expired_at and time.time() > expired_at:
                    # Expired, remove
                    cache_path.unlink()
                    return None

            return cached.get('data')

        except (json.JSONDecodeError, IOError) as e:
            # Corrupted cache, remove
            if cache_path.exists():
                cache_path.unlink()
            return None

    def get_with_metadata(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from cache with metadata.

        Args:
            params: Request parameters

        Returns:
            Dict with 'data' and 'metadata' keys, or None if not found/expired
        """
        key = self._generate_key(params)
        is_hist = self._is_historical(params)
        cache_path = self._get_cache_path(key, is_hist)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r') as f:
                cached = json.load(f)

            # Check expiration (historical never expires)
            if not is_hist:
                expired_at = cached.get('expired_at')
                if expired_at and time.time() > expired_at:
                    # Expired, remove
                    cache_path.unlink()
                    return None

            # Extract metadata
            metadata = {
                'from_cache': True,
                'cached_at': cached.get('cached_at'),
                'is_historical': is_hist,
                'version': cached.get('version', '1.0.0')
            }

            return {
                'data': cached.get('data'),
                'metadata': metadata
            }

        except (json.JSONDecodeError, IOError) as e:
            # Corrupted cache, remove
            if cache_path.exists():
                cache_path.unlink()
            return None

    def set(self, params: Dict[str, Any], data: Any, ttl: Optional[int] = None) -> bool:
        """
        Store data in cache.

        Args:
            params: Request parameters
            data: Data to cache
            ttl: Time-to-live in seconds (None for infinite)

        Returns:
            True if successful
        """
        key = self._generate_key(params)
        is_hist = self._is_historical(params)
        cache_path = self._get_cache_path(key, is_hist)

        # Historical data has infinite TTL
        if is_hist:
            ttl = None
        # Default TTL for recent data: 7 days
        elif ttl is None:
            ttl = 7 * 24 * 3600

        # Store metadata with ISO format timestamps
        cached_at_dt = datetime.now()
        cache_obj = {
            'data': data,
            'cached_at': cached_at_dt.isoformat(),
            'cached_at_unix': time.time(),
            'expired_at': time.time() + ttl if ttl else None,
            'params': params,
            'version': '2.0.0'
        }

        try:
            with open(cache_path, 'w') as f:
                json.dump(cache_obj, f, indent=2)
            return True
        except IOError as e:
            # Can't write cache, log warning but continue
            print(f"Warning: Cache write failed: {e}")
            return False

    def invalidate(self, pattern: str = '*') -> int:
        """
        Invalidate cache entries matching pattern.

        Args:
            pattern: Glob pattern to match keys

        Returns:
            Number of entries removed
        """
        count = 0

        for directory in [self.historical_dir, self.recent_dir]:
            for cache_file in directory.glob(f"{pattern}.json"):
                try:
                    cache_file.unlink()
                    count += 1
                except IOError:
                    pass

        return count

    def cleanup(self) -> int:
        """
        Remove expired cache entries.

        Returns:
            Number of entries removed
        """
        count = 0
        current_time = time.time()

        # Only check recent directory (historical never expires)
        for cache_file in self.recent_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    cached = json.load(f)

                expired_at = cached.get('expired_at')
                if expired_at and current_time > expired_at:
                    cache_file.unlink()
                    count += 1

            except (json.JSONDecodeError, IOError):
                # Corrupted, remove
                cache_file.unlink()
                count += 1

        return count

    def stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        hist_count = len(list(self.historical_dir.glob("*.json")))
        recent_count = len(list(self.recent_dir.glob("*.json")))

        # Calculate total size
        hist_size = sum(f.stat().st_size for f in self.historical_dir.glob("*.json"))
        recent_size = sum(f.stat().st_size for f in self.recent_dir.glob("*.json"))

        return {
            'historical_entries': hist_count,
            'recent_entries': recent_count,
            'total_entries': hist_count + recent_count,
            'historical_size_kb': hist_size // 1024,
            'recent_size_kb': recent_size // 1024,
            'total_size_kb': (hist_size + recent_size) // 1024
        }


if __name__ == "__main__":
    # Test cache manager
    cache = CacheManager()

    # Test params
    test_params = {
        'commodity_desc': 'CORN',
        'year': 2023,
        'reference_period_desc': 'WEEK #30'
    }

    test_data = {'test': 'data', 'value': 42}

    # Set and get
    cache.set(test_params, test_data)
    retrieved = cache.get(test_params)

    print(f"Set: {test_data}")
    print(f"Get: {retrieved}")
    print(f"Match: {test_data == retrieved}")

    # Stats
    stats = cache.stats()
    print(f"\nCache Stats: {stats}")

    # Cleanup
    removed = cache.cleanup()
    print(f"Cleanup removed: {removed} entries")
