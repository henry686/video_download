"""Bilibili-specific features using bilibili-api-python.

Provides:
- Danmaku (bullet comment) extraction and ASS subtitle generation
- Bilibili video metadata enrichment
- Quality presets optimized for Bilibili (Dolby Vision, HDR, 8K, etc.)
- Anti-bot WBI patch for yt-dlp (dm_img_* parameters on playback API)
"""

from __future__ import annotations

import base64
import random
import string
from typing import Any

# ---------------------------------------------------------------------------
# Anti-bot patch: yt-dlp's BiliBili extractor misses dm_img_* parameters on
# the playback API (wbi/playurl), causing HTTP 412 errors since ~2025-06.
# This monkey-patch adds the missing fingerpint params before yt-dlp signs
# the WBI request.  Remove this block once yt-dlp upstream includes the fix.
# ---------------------------------------------------------------------------
try:
    from yt_dlp.extractor.bilibili import BiliBiliIE

    _orig_download_playinfo = BiliBiliIE._download_playinfo

    def _patched_download_playinfo(self, bvid, cid, headers=None, query=None):
        dm = {
            "dm_img_list": "[]",
            "dm_img_str": base64.b64encode(
                "".join(random.choices(string.printable, k=random.randint(16, 64))).encode()
            )[:-2].decode(),
            "dm_cover_img_str": base64.b64encode(
                "".join(random.choices(string.printable, k=random.randint(32, 128))).encode()
            )[:-2].decode(),
            "dm_img_inter": '{"ds":[],"wh":[6093,6631,31],"of":[430,760,380]}',
        }
        query = {**(query or {}), **dm}
        return _orig_download_playinfo(self, bvid, cid, headers=headers, query=query)

    BiliBiliIE._download_playinfo = _patched_download_playinfo
except ImportError:
    pass

# ---------------------------------------------------------------------------

from bilibili_api import sync
from bilibili_api.video import Video

# Bilibili quality presets for yt-dlp format selection
BILIBILI_QUALITY_PRESETS: dict[str, str] = {
    "8k": "bv*[height<=4320]+ba/best",
    "4k": "bv*[height<=2160]+ba/best",
    "1440p": "bv*[height<=1440]+ba/best",
    "1080p60": "bv*[height<=1080][fps>30]+ba/best",
    "1080p": "bv*[height<=1080]+ba/best",
    "720p": "bv*[height<=720]+ba/best",
    "480p": "bv*[height<=480]+ba/best",
    "audio": "bestaudio/best",
}


def extract_bvid(url: str) -> str | None:
    """Extract Bilibili video BV ID from a URL.

    Args:
        url: Bilibili video URL (e.g. https://www.bilibili.com/video/BV1xx411c7mD).

    Returns:
        BV ID string or None if not a Bilibili URL.
    """
    import re
    match = re.search(r"(BV[a-zA-Z0-9]{10})", url)
    return match.group(1) if match else None


def get_video_info(bvid: str, credential: Any | None = None) -> dict:
    """Get detailed Bilibili video information via the API.

    Args:
        bvid: Bilibili video BV ID.
        credential: Optional bilibili_api.Credential for authenticated requests.

    Returns:
        Dictionary with video title, description, tags, stats, etc.
    """
    video = Video(bvid=bvid, credential=credential)
    info = sync(video.get_info())
    return info


def get_danmaku(
    bvid: str,
    page_index: int = 0,
    credential: Any | None = None,
) -> list[dict]:
    """Fetch danmaku (bullet comments) for a Bilibili video.

    Args:
        bvid: Bilibili video BV ID.
        page_index: Video part/page index (0-based).
        credential: Optional bilibili_api.Credential.

    Returns:
        List of danmaku dicts with keys: text, time (seconds), mode, color, etc.
    """
    video = Video(bvid=bvid, credential=credential)
    danmakus = sync(video.get_danmakus(page_index=page_index))

    result = []
    for dm in danmakus:
        result.append({
            "text": dm.text,
            "time": dm.dm_time,
            "mode": dm.mode.value if hasattr(dm.mode, "value") else dm.mode,
            "color": dm.color,
            "font_size": dm.font_size,
            "send_time": dm.send_time,
        })
    return result


def danmaku_to_ass(
    danmakus: list[dict],
    video_width: int = 1920,
    video_height: int = 1080,
) -> str:
    """Convert danmaku list to ASS subtitle format.

    Args:
        danmakus: List of danmaku dicts from get_danmaku().
        video_width: Video width in pixels.
        video_height: Video height in pixels.

    Returns:
        ASS subtitle content as a string.
    """
    # Danmaku mode mapping
    # 1-3: scrolling, 4: bottom, 5: top, 6: reversed, 7: special
    lines = [
        "[Script Info]",
        "Title: Bilibili Danmaku",
        "ScriptType: v4.00+",
        f"PlayResX: {video_width}",
        f"PlayResY: {video_height}",
        "WrapStyle: 2",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: DM,Microsoft YaHei,36,&H00FFFFFF,&H000000FF,&H00000000,"
        "&H00000000,0,0,0,0,100,100,0,0,1,1,0,2,10,10,10,134",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
        "Effect, Text",
    ]

    for dm in danmakus:
        start_sec = float(dm["time"])
        start = _seconds_to_ass_time(start_sec)
        end = _seconds_to_ass_time(start_sec + 8)  # 8 second display

        # Determine alignment based on mode
        mode = dm.get("mode", 1)
        if mode == 5:  # top
            alignment = 8
        elif mode == 4:  # bottom
            alignment = 2
        else:  # scrolling (1,2,3,6) and default
            alignment = 2

        color = dm.get("color", 0xFFFFFF)
        text = dm["text"].replace("\n", "\\N")

        lines.append(
            f"Dialogue: 0,{start},{end},DM,,0,0,0,,"
            f"{{\\an{alignment}\\c&H{color:06X}&}}{text}"
        )

    return "\n".join(lines)


def _seconds_to_ass_time(seconds: float) -> str:
    """Convert seconds to ASS timestamp format (H:MM:SS.CC)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centisecs = int((seconds % 1) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"
