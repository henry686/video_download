"""video_download - Multi-platform video downloader.

Supports YouTube, Bilibili, and 1800+ sites via yt-dlp engine.
"""

__version__ = "0.1.0"

from video_download.core import VideoDownloader

__all__ = ["VideoDownloader", "launch_gui"]


def launch_gui() -> None:
    """Launch the Tkinter GUI for the video downloader."""
    from video_download.gui import main as _gui_main

    _gui_main()
