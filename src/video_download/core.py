"""Core download orchestrator wrapping yt-dlp's YoutubeDL.

Provides a clean Python API for video downloading with support for:
- Multi-format downloads (best, specific quality, audio-only)
- Progress callbacks
- Cookie-based authentication
- Proxy configuration
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

# Ensure UTF-8 encoding on all platforms, especially Windows
# where the default GBK codec can't handle Unicode video titles.
# Must run before any yt-dlp output to avoid UnicodeEncodeError.
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

import yt_dlp  # noqa: E402  # encoding setup must run before yt-dlp import


def _find_ffmpeg() -> str | None:
    """Auto-detect FFmpeg executable location.

    Searches common install paths (especially on Windows where FFmpeg
    is often not on PATH). Returns the path if found, None otherwise.
    """
    import subprocess

    # 1. Already in PATH — cheapest check
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=5,
        )
        return "ffmpeg"  # found in PATH, no explicit path needed
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # 2. Search common install directories
    candidates: list[Path] = []
    if sys.platform == "win32":
        # winget (Gyan.FFmpeg)
        prog = os.environ.get("ProgramFiles", "C:\\Program Files")
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        candidates = [
            Path(prog) / "AIGO" / "ffmpeg.exe",
            Path(prog) / "ffmpeg" / "bin" / "ffmpeg.exe",
            Path(prog).parent / "Program Files (x86)" / "ffmpeg" / "bin" / "ffmpeg.exe",
        ]
        if local_appdata:
            # WinGet package directory
            for d in Path(local_appdata, "Microsoft", "WinGet", "Packages").glob(
                "Gyan.FFmpeg_*"
            ):
                exe = d / "ffmpeg.exe"
                candidates.append(exe)
    else:
        candidates = [
            Path("/usr/bin/ffmpeg"),
            Path("/usr/local/bin/ffmpeg"),
            Path("/opt/homebrew/bin/ffmpeg"),
        ]

    for path in candidates:
        if path.is_file():
            return str(path)

    return None


class VideoDownloader:
    """Main downloader class wrapping yt-dlp's YoutubeDL.

    Usage:
        dl = VideoDownloader(output_dir="./downloads")
        dl.download("https://www.youtube.com/watch?v=...")
    """

    def __init__(
        self,
        output_dir: str | Path = "./downloads",
        cookiefile: str | None = None,
        proxy: str | None = None,
        quiet: bool = False,
        ffmpeg_path: str | None = None,
    ):
        """Initialize the downloader.

        Args:
            output_dir: Directory to save downloaded videos.
            cookiefile: Path to Netscape-format cookie file for authentication.
            proxy: Proxy URL (e.g. "socks5://127.0.0.1:1080" or "http://127.0.0.1:8080").
            quiet: Suppress yt-dlp output.
            ffmpeg_path: Path to ffmpeg executable. Auto-detected if not provided.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cookiefile = cookiefile
        self.proxy = proxy
        self.quiet = quiet
        self._ffmpeg_path: str | None = ffmpeg_path or _find_ffmpeg()

    def _build_options(
        self,
        format: str,
        output_template: str | None = None,
        progress_callback: Callable[[dict], None] | None = None,
        **extra,
    ) -> dict:
        """Build yt-dlp options dictionary."""
        outtmpl = output_template or str(self.output_dir / "%(title)s.%(ext)s")

        opts: dict[str, Any] = {
            "format": format,
            "outtmpl": outtmpl,
            "quiet": self.quiet,
            "no_warnings": self.quiet,
            "extract_flat": False,
            "progress_hooks": [],
        }

        if progress_callback:
            opts["progress_hooks"].append(progress_callback)

        if self.cookiefile:
            opts["cookiefile"] = self.cookiefile

        if self.proxy:
            opts["proxy"] = self.proxy

        if self._ffmpeg_path:
            opts["ffmpeg_location"] = self._ffmpeg_path

        opts.update(extra)
        return opts

    def _run(
        self,
        url: str,
        options: dict,
        download: bool,
    ) -> dict:
        """Execute a yt-dlp operation."""
        with yt_dlp.YoutubeDL(options) as ydl:
            return ydl.extract_info(url, download=download)

    def extract_info(self, url: str) -> dict:
        """Extract video metadata without downloading.

        Args:
            url: Video URL from any supported platform.

        Returns:
            info_dict with title, duration, formats, thumbnail, etc.
        """
        options = self._build_options(format="best", download=False)
        return self._run(url, options, download=False)

    def list_formats(self, url: str) -> list[dict]:
        """List all available formats for a video.

        Args:
            url: Video URL.

        Returns:
            List of format dictionaries with format_id, ext, resolution, filesize, etc.
        """
        info = self.extract_info(url)
        return info.get("formats", [])

    def download(
        self,
        url: str,
        format: str = "best",
        output_template: str | None = None,
        progress_callback: Callable[[dict], None] | None = None,
        audio_only: bool = False,
        **extra,
    ) -> dict:
        """Download a video.

        Args:
            url: Video URL to download.
            format: yt-dlp format string. Common values:
                - "best" — best quality video+audio (default)
                - "bestvideo+bestaudio/best" — best separate streams, merge with FFmpeg
                - "worst" — smallest file
                - "bestaudio/best" — audio only
                - "bv*[height<=1080]+ba/best" — best up to 1080p
            output_template: Custom output path template (yt-dlp syntax).
            progress_callback: Called with progress dict: {status, downloaded_bytes,
                              total_bytes, speed, eta, _percent_str, ...}.
            audio_only: If True, download audio only and convert to best audio format.
            **extra: Additional yt-dlp options.

        Returns:
            info_dict with metadata about the downloaded video.
        """
        if audio_only:
            final_format = "bestaudio/best"
            extra.setdefault("postprocessors", [])
            extra["postprocessors"].append({
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
            })

        options = self._build_options(
            format=format if not audio_only else final_format,
            output_template=output_template,
            progress_callback=progress_callback,
            **extra,
        )
        return self._run(url, options, download=True)


# Convenience functions
_default_downloader: VideoDownloader | None = None


def _get_downloader(output_dir: str = "./downloads") -> VideoDownloader:
    global _default_downloader
    if _default_downloader is None:
        _default_downloader = VideoDownloader(output_dir=output_dir)
    return _default_downloader


def download(url: str, output_dir: str = "./downloads", **kwargs) -> dict:
    """Convenience function for one-off downloads."""
    dl = VideoDownloader(output_dir=output_dir)
    return dl.download(url, **kwargs)


def extract_info(url: str) -> dict:
    """Convenience function to extract video metadata."""
    dl = _get_downloader()
    return dl.extract_info(url)
