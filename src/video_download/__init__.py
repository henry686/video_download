"""video_download - Multi-platform video downloader.

Supports YouTube, Bilibili, and 1800+ sites via yt-dlp engine.
"""

__version__ = "0.1.0"

# Apply platform patches early (must run before any yt-dlp instantiation)
import video_download.platforms.bilibili  # noqa: F401 — anti-bot WBI patch
from video_download.core import VideoDownloader

__all__ = ["VideoDownloader", "launch_gui"]


def launch_gui() -> None:
    """Launch the Tkinter GUI for the video downloader."""
    from video_download.gui import main as _gui_main

    _gui_main()
