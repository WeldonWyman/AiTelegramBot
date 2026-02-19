"""Media downloader using yt-dlp."""
import os
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Tuple
import yt_dlp


class MediaDownloader:
    """Downloads media using yt-dlp."""
    
    def __init__(self, cache_dir: str, max_file_size_mb: int, max_duration_seconds: int):
        """Initialize downloader.
        
        Args:
            cache_dir: Directory to save downloads
            max_file_size_mb: Maximum file size in MB
            max_duration_seconds: Maximum video duration in seconds
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.max_duration_seconds = max_duration_seconds
    
    def get_video_info(self, url: str) -> Optional[Dict]:
        """Get video information without downloading.
        
        Args:
            url: Video URL
            
        Returns:
            Video info dictionary or None if error
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            return None
    
    def check_limits(self, info: Dict) -> Tuple[bool, Optional[str]]:
        """Check if video meets size and duration limits.
        
        Args:
            info: Video information dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check duration
        duration = info.get('duration', 0)
        if duration and duration > self.max_duration_seconds:
            return False, f"Video duration ({duration}s) exceeds maximum ({self.max_duration_seconds}s)"
        
        # Check file size
        filesize = info.get('filesize') or info.get('filesize_approx', 0)
        if filesize and filesize > self.max_file_size_bytes:
            size_mb = filesize / (1024 * 1024)
            max_mb = self.max_file_size_bytes / (1024 * 1024)
            return False, f"File size ({size_mb:.1f}MB) exceeds maximum ({max_mb:.1f}MB)"
        
        return True, None
    
    async def download(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[Dict]]:
        """Download media from URL.
        
        Args:
            url: Media URL
            
        Returns:
            Tuple of (file_path, error_message, file_info)
        """
        try:
            # Get video info first
            info = self.get_video_info(url)
            if not info:
                return None, "Failed to fetch video information", None
            
            # Check limits
            is_valid, error_msg = self.check_limits(info)
            if not is_valid:
                return None, error_msg, None
            
            # Set up download options
            output_template = str(self.cache_dir / '%(id)s.%(ext)s')
            ydl_opts = {
                'format': 'best[filesize<50M]/best',  # Prefer files under 50MB
                'outtmpl': output_template,
                'quiet': True,
                'no_warnings': True,
                # Convert to mp4 if needed for better Telegram compatibility
                'merge_output_format': 'mp4',
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
            }
            
            # Download the video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(url, download=True)
                
                # Get the downloaded filename
                filename = ydl.prepare_filename(result)
                
                # Check if file was actually downloaded
                if not os.path.exists(filename):
                    # Try with .mp4 extension
                    base = os.path.splitext(filename)[0]
                    filename = f"{base}.mp4"
                
                if not os.path.exists(filename):
                    return None, "Download completed but file not found", None
                
                # Check final file size
                file_size = os.path.getsize(filename)
                if file_size > self.max_file_size_bytes:
                    os.remove(filename)
                    size_mb = file_size / (1024 * 1024)
                    max_mb = self.max_file_size_bytes / (1024 * 1024)
                    return None, f"Downloaded file size ({size_mb:.1f}MB) exceeds maximum ({max_mb:.1f}MB)", None
                
                file_info = {
                    'title': result.get('title', 'Unknown'),
                    'duration': result.get('duration', 0),
                    'filesize': file_size,
                    'ext': result.get('ext', 'unknown'),
                }
                
                return filename, None, file_info
                
        except Exception as e:
            return None, f"Download failed: {str(e)}", None
