"""Tests for core.cache module."""

import pytest
import time
import json
from pathlib import Path
from permitcheck.core.cache import LicenseCache, CacheEntry


def test_cache_entry_expiration():
    """Test cache entry expiration logic."""
    entry = CacheEntry(licenses=['MIT'], timestamp=time.time())
    assert not entry.is_expired(ttl_seconds=3600)
    
    old_entry = CacheEntry(licenses=['MIT'], timestamp=time.time() - 90000)
    assert old_entry.is_expired(ttl_seconds=86400)


def test_cache_set_and_get(tmp_path):
    """Test basic cache set and get operations."""
    cache = LicenseCache(cache_dir=tmp_path, ttl_seconds=3600)
    
    cache.set('test-pkg', {'MIT', 'BSD'})
    licenses = cache.get('test-pkg')
    
    assert licenses == {'MIT', 'BSD'}


def test_cache_get_nonexistent(tmp_path):
    """Test getting non-existent cache entry returns None."""
    cache = LicenseCache(cache_dir=tmp_path)
    
    assert cache.get('nonexistent-pkg') is None


def test_cache_expiration(tmp_path):
    """Test that expired entries return None."""
    cache = LicenseCache(cache_dir=tmp_path, ttl_seconds=1)
    
    cache.set('test-pkg', {'MIT'})
    time.sleep(2)
    
    assert cache.get('test-pkg') is None


def test_cache_persistence(tmp_path):
    """Test that cache persists across instances."""
    cache1 = LicenseCache(cache_dir=tmp_path)
    cache1.set('test-pkg', {'MIT'})
    
    # Create new cache instance
    cache2 = LicenseCache(cache_dir=tmp_path)
    licenses = cache2.get('test-pkg')
    
    assert licenses == {'MIT'}


def test_cache_clear(tmp_path):
    """Test cache clearing."""
    cache = LicenseCache(cache_dir=tmp_path)
    
    cache.set('pkg1', {'MIT'})
    cache.set('pkg2', {'BSD'})
    assert cache.size == 2
    
    cache.clear()
    assert cache.size == 0
    assert cache.get('pkg1') is None


def test_cache_clear_expired(tmp_path):
    """Test clearing only expired entries."""
    cache = LicenseCache(cache_dir=tmp_path, ttl_seconds=1)
    
    # Add entries with different timestamps
    cache.set('fresh-pkg', {'MIT'})
    
    # Manually add expired entry
    cache._cache['expired-pkg'] = CacheEntry(
        licenses=['BSD'],
        timestamp=time.time() - 90000
    )
    
    removed = cache.clear_expired()
    
    assert removed == 1
    assert cache.get('fresh-pkg') == {'MIT'}
    assert cache.get('expired-pkg') is None


def test_cache_with_version(tmp_path):
    """Test cache with package versions."""
    cache = LicenseCache(cache_dir=tmp_path)
    
    cache.set('pkg', {'MIT'}, version='1.0.0')
    cache.set('pkg', {'BSD'}, version='2.0.0')
    
    assert cache.get('pkg', version='1.0.0') == {'MIT'}
    assert cache.get('pkg', version='2.0.0') == {'BSD'}


def test_cache_stats(tmp_path):
    """Test cache statistics."""
    cache = LicenseCache(cache_dir=tmp_path, ttl_seconds=1)
    
    cache.set('pkg1', {'MIT'})
    
    # Add expired entry
    cache._cache['expired'] = CacheEntry(
        licenses=['BSD'],
        timestamp=time.time() - 90000
    )
    
    stats = cache.stats()
    assert stats['total'] == 2
    assert stats['expired'] == 1
    assert stats['valid'] == 1
