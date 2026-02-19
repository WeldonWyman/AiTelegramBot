#!/usr/bin/env python3
"""
Simple test script to verify bot components without requiring a real bot token.
"""
import asyncio
import sys
from datetime import datetime

def test_config_loader():
    """Test configuration loading."""
    print("Testing config loader...", end=" ")
    try:
        from config_loader import load_config
        config = load_config('config.toml')
        assert config.bot.token
        assert config.limits.max_file_size_mb > 0
        assert config.cache.retention_hours > 0
        assert config.queue.max_size > 0
        assert config.queue.parallel_workers > 0
        print("✅")
        return True
    except Exception as e:
        print(f"❌ {e}")
        return False


def test_cache_manager():
    """Test cache manager."""
    print("Testing cache manager...", end=" ")
    try:
        from cache_manager import CacheManager
        import os
        import shutil
        
        # Create test cache
        cache = CacheManager('./test_cache', 24)
        
        # Test adding to cache
        test_file = './test_cache/test.mp4'
        os.makedirs('./test_cache', exist_ok=True)
        with open(test_file, 'w') as f:
            f.write('test')
        
        cache.add_to_cache('http://test.com/video', test_file, {'title': 'Test'})
        
        # Test retrieval
        result = cache.get_cached_file('http://test.com/video')
        assert result is not None
        
        # Cleanup
        shutil.rmtree('./test_cache')
        print("✅")
        return True
    except Exception as e:
        print(f"❌ {e}")
        import traceback
        traceback.print_exc()
        return False


def test_downloader():
    """Test media downloader."""
    print("Testing downloader...", end=" ")
    try:
        from downloader import MediaDownloader
        
        downloader = MediaDownloader('./test_cache', 50, 3600)
        
        # Test limit checking
        info = {'duration': 300, 'filesize': 10 * 1024 * 1024}
        is_valid, error = downloader.check_limits(info)
        assert is_valid
        
        # Test oversized file
        info_large = {'duration': 300, 'filesize': 100 * 1024 * 1024}
        is_valid, error = downloader.check_limits(info_large)
        assert not is_valid
        
        print("✅")
        return True
    except Exception as e:
        print(f"❌ {e}")
        return False


async def test_queue_manager():
    """Test queue manager."""
    print("Testing queue manager...", end=" ")
    try:
        from queue_manager import DownloadQueue, DownloadTask
        
        queue = DownloadQueue(5, 1)
        
        # Test adding tasks
        for i in range(5):
            task = DownloadTask(
                url=f'http://test.com/video{i}',
                user_id=123,
                chat_id=456,
                message_id=i,
                timestamp=datetime.now()
            )
            added = await queue.add_task(task)
            assert added
        
        # Test queue full
        task = DownloadTask(
            url='http://test.com/video_extra',
            user_id=123,
            chat_id=456,
            message_id=999,
            timestamp=datetime.now()
        )
        added = await queue.add_task(task)
        assert not added
        assert queue.is_full()
        
        print("✅")
        return True
    except Exception as e:
        print(f"❌ {e}")
        import traceback
        traceback.print_exc()
        return False


def test_whitelist_logic():
    """Test whitelist logic."""
    print("Testing whitelist logic...", end=" ")
    try:
        # Empty whitelist - allow all
        user_ids = []
        group_ids = []
        
        def is_allowed(uid, cid):
            if not user_ids and not group_ids:
                return True
            if user_ids and uid in user_ids:
                return True
            if group_ids and cid in group_ids:
                return True
            return False
        
        assert is_allowed(123, 456)
        
        # User whitelist
        user_ids = [123]
        assert is_allowed(123, 456)
        assert not is_allowed(999, 456)
        
        # Group whitelist
        user_ids = []
        group_ids = [456]
        assert is_allowed(999, 456)
        assert not is_allowed(999, 789)
        
        print("✅")
        return True
    except Exception as e:
        print(f"❌ {e}")
        return False


async def run_async_tests():
    """Run async tests."""
    return await test_queue_manager()


def main():
    """Run all tests."""
    print("=" * 60)
    print("Running Bot Component Tests")
    print("=" * 60)
    print()
    
    results = []
    
    # Sync tests
    results.append(test_config_loader())
    results.append(test_cache_manager())
    results.append(test_downloader())
    results.append(test_whitelist_logic())
    
    # Async tests
    results.append(asyncio.run(run_async_tests()))
    
    print()
    print("=" * 60)
    
    if all(results):
        print("✅ All tests passed!")
        print("=" * 60)
        return 0
    else:
        print("❌ Some tests failed!")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
