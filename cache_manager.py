"""Cache manager for downloaded media files."""
import os
import time
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime, timedelta
import asyncio


class CacheManager:
    """Manages cached media files."""
    
    def __init__(self, cache_dir: str, retention_hours: int):
        """Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cached files
            retention_hours: How long to keep cached files in hours
        """
        self.cache_dir = Path(cache_dir)
        self.retention_hours = retention_hours
        self.metadata_file = self.cache_dir / "metadata.json"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._load_metadata()
    
    def _load_metadata(self):
        """Load cache metadata from disk."""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}
    
    def _save_metadata(self):
        """Save cache metadata to disk."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def _get_cache_key(self, url: str) -> str:
        """Generate cache key from URL.
        
        Args:
            url: Media URL
            
        Returns:
            Cache key (hash of URL)
        """
        return hashlib.sha256(url.encode()).hexdigest()
    
    def get_cached_file(self, url: str) -> Optional[str]:
        """Get cached file path if exists and not expired.
        
        Args:
            url: Media URL
            
        Returns:
            File path if cached and valid, None otherwise
        """
        cache_key = self._get_cache_key(url)
        
        if cache_key not in self.metadata:
            return None
        
        entry = self.metadata[cache_key]
        cached_time = datetime.fromisoformat(entry['timestamp'])
        expiry_time = cached_time + timedelta(hours=self.retention_hours)
        
        if datetime.now() > expiry_time:
            # Cache expired
            self._remove_cache_entry(cache_key)
            return None
        
        file_path = self.cache_dir / entry['filename']
        if not file_path.exists():
            # File was deleted
            self._remove_cache_entry(cache_key)
            return None
        
        return str(file_path)
    
    def add_to_cache(self, url: str, file_path: str, file_info: Dict):
        """Add file to cache.
        
        Args:
            url: Media URL
            file_path: Path to downloaded file
            file_info: Additional file information
        """
        cache_key = self._get_cache_key(url)
        filename = Path(file_path).name
        
        self.metadata[cache_key] = {
            'url': url,
            'filename': filename,
            'timestamp': datetime.now().isoformat(),
            'file_info': file_info
        }
        self._save_metadata()
    
    def _remove_cache_entry(self, cache_key: str):
        """Remove cache entry.
        
        Args:
            cache_key: Cache key to remove
        """
        if cache_key in self.metadata:
            entry = self.metadata[cache_key]
            file_path = self.cache_dir / entry['filename']
            
            if file_path.exists():
                try:
                    file_path.unlink()
                except Exception:
                    pass
            
            del self.metadata[cache_key]
            self._save_metadata()
    
    async def cleanup_expired(self):
        """Clean up expired cache entries."""
        current_time = datetime.now()
        expired_keys = []
        
        for cache_key, entry in self.metadata.items():
            cached_time = datetime.fromisoformat(entry['timestamp'])
            expiry_time = cached_time + timedelta(hours=self.retention_hours)
            
            if current_time > expiry_time:
                expired_keys.append(cache_key)
        
        for cache_key in expired_keys:
            self._remove_cache_entry(cache_key)
    
    def get_cache_info(self, url: str) -> Optional[Dict]:
        """Get cache information for URL.
        
        Args:
            url: Media URL
            
        Returns:
            Cache info dict or None
        """
        cache_key = self._get_cache_key(url)
        return self.metadata.get(cache_key)
