# CLAUDE.md - Video Download Project

## Project Overview

A multi-platform video downloader supporting 1800+ sites via **yt-dlp** as the core engine,
with specialized platform modules for enhanced site-specific features (Bilibili, YouTube).

**Supported platforms:** YouTube, Bilibili, TikTok, Twitter/X, Twitch, and any site supported by yt-dlp.

## Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | >=3.10 |
| Core engine | [yt-dlp](https://github.com/yt-dlp/yt-dlp) | >=2024.0.0 |
| Bilibili API | [bilibili-api-python](https://github.com/Nemo2011/bilibili-api) | >=17.0.0 |
| Build | hatchling | latest |
| Lint | ruff | >=0.5.0 |
| Test | pytest | >=8.0.0 |

## Project Structure

```
video_download/
├── CLAUDE.md                     # This file
├── README.md                     # Project description
├── pyproject.toml                # Project config & dependencies
├── .gitignore
├── src/
│   └── video_download/
│       ├── __init__.py           # Package init, exports VideoDownloader
│       ├── core.py               # VideoDownloader class (yt-dlp wrapper)
│       └── platforms/
│           ├── __init__.py
│           └── bilibili.py       # Bilibili-specific: danmaku, API info
├── examples/
│   └── basic_download.py         # Usage examples
└── tests/
    ├── __init__.py
    └── test_core.py              # Unit tests for core module
```

## Architecture

```
[CLI / API / GUI]     ← future
       │
[VideoDownloader]     ← core.py — thin orchestrator over yt-dlp
       │
[yt-dlp YoutubeDL]    ← extraction + download engine (1800+ sites)
       │
[FFmpeg]              ← post-processing (merge, convert, burn subtitles)
       │
[platforms/ modules]  ← site-specific extras (danmaku, API enrichment)
```

### Design Principles

1. **yt-dlp is the engine** — We don't reimplement download logic. yt-dlp handles format parsing,
   HTTP/fragment download, DASH/HLS, and post-processing. Our `VideoDownloader` is a thin,
   opinionated wrapper.

2. **Platform modules add, don't fork** — Site-specific features (e.g., Bilibili danmaku) live in
   `platforms/` and use dedicated APIs (bilibili-api-python). They produce data that complements
   yt-dlp's output — never replaces it.

3. **Cookie-based auth** — Authentication uses Netscape-format cookie files passed to yt-dlp.
   Users export cookies from their browser (via browser extensions like "Get cookies.txt").
   For Bilibili, optional `Credential` objects from bilibili-api-python can enable API access.

## Setup

```bash
# Install in dev mode with all dependencies
pip install -e ".[dev]"

# Or install production dependencies only
pip install -e .

# Install FFmpeg (required for video+audio merging)
# Windows: winget install ffmpeg   or   choco install ffmpeg
# macOS:   brew install ffmpeg
# Linux:   apt install ffmpeg
```

## Common Commands

```bash
# Run tests
pytest tests/ -v

# Run linting
ruff check src/

# Run examples
python examples/basic_download.py

# Verify package import
python -c "import video_download; print(video_download.__version__)"
```

## Key API

### Core Downloader

```python
from video_download import VideoDownloader

dl = VideoDownloader(
    output_dir="./downloads",
    cookiefile="./cookies.txt",    # optional
    proxy="socks5://127.0.0.1:1080", # optional
)

# Get video info without downloading
info = dl.extract_info("https://www.youtube.com/watch?v=...")
print(info["title"], info["duration"])

# List available formats
formats = dl.list_formats("https://www.youtube.com/watch?v=...")
for f in formats:
    print(f"{f['format_id']}: {f.get('height')}p {f['ext']}")

# Download with progress
def on_progress(d):
    if d["status"] == "downloading":
        print(f"\r{d['_percent_str']} at {d['_speed_str']}")

dl.download(
    url="https://www.youtube.com/watch?v=...",
    format="best[height<=1080]",
    progress_callback=on_progress,
)

# Audio only
dl.download(url, audio_only=True)
```

### Bilibili Extras

```python
from video_download.platforms.bilibili import (
    extract_bvid, get_video_info, get_danmaku, danmaku_to_ass,
)

bvid = extract_bvid("https://www.bilibili.com/video/BV1xx411c7mD")
info = get_video_info(bvid)
danmakus = get_danmaku(bvid)
ass_content = danmaku_to_ass(danmakus)
```

### Format Selection Quick Reference

| Format String | Result |
|---------------|--------|
| `best` | Best single file (video+audio merged) |
| `bestvideo+bestaudio/best` | Best video+best audio, merge with FFmpeg |
| `best[height<=1080]` | Best quality up to 1080p |
| `bv*[height<=720]+ba/best` | 720p video + best audio |
| `bestaudio/best` | Audio only (best quality) |
| `worst` | Smallest file |

## Adding New Platform Support

1. Create `src/video_download/platforms/<platform>.py`
2. Implement platform-specific extractors/helpers (API calls, metadata parsing)
3. Core downloading is already handled by yt-dlp — only add what yt-dlp can't do
4. Export key functions in the module's `__all__`
5. Add examples in `examples/`

## Dependencies to Know

- **FFmpeg** is a system dependency, not a pip package. yt-dlp uses it to merge
  separate video+audio streams and for format conversion. The downloader works without
  it for simple formats but many options require it.
- **bilibili-api-python** uses `curl_cffi` for TLS fingerprinting to avoid
  Cloudflare blocks on Bilibili. This is installed as a transitive dependency.
