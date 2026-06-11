"""Basic usage examples for video_download."""

import sys
import time
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from video_download import VideoDownloader
from video_download.platforms.bilibili import extract_bvid, get_video_info, get_danmaku


def example_download():
    """Example: Download a video with progress reporting."""
    def progress_hook(d: dict) -> None:
        if d["status"] == "downloading":
            pct = d.get("_percent_str", "?%")
            speed = d.get("_speed_str", "?")
            eta = d.get("_eta_str", "?")
            print(f"\rDownloading... {pct} at {speed} (ETA: {eta})", end="")
        elif d["status"] == "finished":
            print(f"\rDownload complete! Saved to: {d['filename']}")

    dl = VideoDownloader(output_dir="./downloads")

    # Extract info first (no download)
    print("Fetching video info...")
    info = dl.extract_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    print(f"Title: {info.get('title')}")
    print(f"Duration: {info.get('duration')}s")

    # Download
    print("\nDownloading...")
    dl.download(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        format="best[height<=1080]",
        progress_callback=progress_hook,
    )


def example_bilibili():
    """Example: Bilibili-specific features."""
    url = "https://www.bilibili.com/video/BV1xx411c7mD"

    bvid = extract_bvid(url)
    if bvid:
        print(f"BV ID: {bvid}")

        info = get_video_info(bvid)
        print(f"Title: {info.get('title')}")

        danmakus = get_danmaku(bvid)
        print(f"Danmaku count: {len(danmakus)}")
        if danmakus:
            print(f"First danmaku: {danmakus[0]['text']}")


if __name__ == "__main__":
    print("=== video_download examples ===\n")
    print("Example 1: YouTube download")
    print("-" * 40)
    # example_download()  # Uncomment to actually download
    print("(commented out — uncomment to run)")

    print("\nExample 2: Bilibili info")
    print("-" * 40)
    example_bilibili()
