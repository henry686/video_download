"""video_download - Multi-platform video downloader.

Supports YouTube, Bilibili, and 1800+ sites via yt-dlp engine.
"""

__version__ = "0.1.0"

from video_download.core import VideoDownloader

__all__ = ["VideoDownloader"]
