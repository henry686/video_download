# video_download

基于 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 的多平台视频下载器，支持 **1800+** 站点，并提供桌面 GUI。

## 支持的平台

YouTube、Bilibili、TikTok、Twitter/X、Twitch，以及 yt-dlp 支持的所有站点。

## 安装

### 方式一：独立可执行文件（无需 Python 环境）

从 [Releases](https://github.com/henry686/video_download/releases) 下载 `VideoDownloader.exe`（约 37MB），直接运行即可。

> 下载高清视频需要 FFmpeg。首次使用若提示缺失，运行 `winget install Gyan.FFmpeg` 安装一次即可，程序会自动检测。

### 方式二：pip 安装（需要 Python 3.10+）

#### 1. 安装 Python 依赖

```bash
pip install video-download
# 或开发模式安装：
# git clone https://github.com/henry686/video_download.git
# cd video_download
# pip install -e .
```

#### 2. 安装 FFmpeg（必需）

FFmpeg 用于合并视频和音频流（YouTube 1080p+ 必须）：

| 系统 | 安装命令 |
|------|---------|
| Windows | `winget install Gyan.FFmpeg` 或 `choco install ffmpeg` |
| macOS | `brew install ffmpeg` |
| Linux | `apt install ffmpeg` |

## 使用方法

### 桌面 GUI（推荐）

```bash
# 启动图形界面
python -m video_download.gui
```

或安装后在命令行直接运行：

```bash
video-download-gui
```

![GUI 界面包含：视频地址输入框、保存目录选择、格式下拉菜单（最佳质量/1080p/720p/480p/仅音频）、Cookie 文件、下载进度条、日志输出](gui-preview)

**GUI 操作步骤：**
1. 粘贴视频链接到「视频地址」
2. 点击「浏览...」选择下载保存目录
3. 选择下载格式（默认「最佳质量」）
4. 点击「开始下载」
5. 在日志区查看进度和结果

### Python API

```python
from video_download import VideoDownloader

# 创建下载器
dl = VideoDownloader(
    output_dir="./downloads",        # 保存目录
    cookiefile="./cookies.txt",      # Cookie 文件（可选）
    proxy="socks5://127.0.0.1:1080", # 代理（可选）
)

# 获取视频信息（不下载）
info = dl.extract_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
print(info["title"], info["duration"])

# 列出可用格式
formats = dl.list_formats("https://www.youtube.com/watch?v=...")
for f in formats:
    print(f"{f['format_id']}: {f.get('height')}p {f['ext']}")

# 下载视频（带进度回调）
def on_progress(d):
    if d["status"] == "downloading":
        print(f"\r{d['_percent_str']} at {d['_speed_str']}")

dl.download(
    url="https://www.youtube.com/watch?v=...",
    format="bestvideo+bestaudio/best",  # 最高质量
    progress_callback=on_progress,
)

# 仅下载音频
dl.download(url, audio_only=True)
```

### 格式选择参考

| 格式字符串 | 结果 |
|-----------|------|
| `bestvideo+bestaudio/best` | 最高质量（需 FFmpeg 合并） |
| `best[height<=1080]` | 最高不超过 1080p |
| `bv*[height<=720]+ba/best` | 720p 视频 + 最佳音频 |
| `bestaudio/best` | 仅音频 |
| `worst` | 最小文件 |

### Bilibili 专属功能

```python
from video_download.platforms.bilibili import (
    extract_bvid, get_video_info, get_danmaku, danmaku_to_ass,
)

# 从 URL 提取 BV 号
bvid = extract_bvid("https://www.bilibili.com/video/BV1xx411c7mD")

# 获取视频详情
info = get_video_info(bvid)

# 获取弹幕并转为 ASS 字幕
danmakus = get_danmaku(bvid)
ass_content = danmaku_to_ass(danmakus)
# 可将 ass_content 写入 .ass 文件用作播放器字幕
```

## 常用命令

```bash
# 运行测试
pytest tests/ -v

# 代码检查
ruff check src/

# 运行示例
python examples/basic_download.py

# 打包为独立 exe（需要 PyInstaller）
pip install pyinstaller
pyinstaller VideoDownloader.spec
```

## 常见问题

**Q: 下载时报 `UnicodeEncodeError`？**
A: 已内置修复，自动将编码设为 UTF-8。如仍遇到，请确保使用最新版本。

**Q: "FFmpeg is not installed"？**
A: YouTube 1080p+ 需要 FFmpeg 合并视频和音频。请按照上方「安装 FFmpeg」部分操作。

**Q: Bilibili 视频下载失败？**
A: B 站部分视频需要登录。提供 Cookie 文件即可。可从浏览器导出（推荐使用 "Get cookies.txt" 扩展）。

**Q: 如何获取 Cookie 文件？**
A: 安装浏览器扩展 "Get cookies.txt"，访问对应网站并登录，点击扩展图标导出为 `cookies.txt`。

## 项目结构

```
video_download/
├── README.md
├── CLAUDE.md
├── pyproject.toml
├── VideoDownloader.spec    # PyInstaller 打包配置
├── src/video_download/
│   ├── __init__.py        # 包入口
│   ├── core.py            # 下载核心（yt-dlp 封装）
│   ├── gui.py             # Tkinter 桌面 GUI
│   └── platforms/
│       └── bilibili.py    # B 站弹幕、字幕支持
├── examples/
│   └── basic_download.py
└── tests/
    └── test_core.py
```

## 许可

MIT
