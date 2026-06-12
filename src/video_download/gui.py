"""Tkinter GUI for the video downloader.

Provides a simple graphical interface to download videos
without using the command line.
"""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from video_download import VideoDownloader
from video_download.core import _find_ffmpeg

# Common format presets shown in the dropdown
FORMAT_PRESETS: dict[str, str] = {
    "最佳质量 (推荐)": "bestvideo+bestaudio/best",
    "1080p": "bv*[height<=1080]+ba/best",
    "720p": "bv*[height<=720]+ba/best",
    "480p": "bv*[height<=480]+ba/best",
    "仅音频 (MP3)": "bestaudio/best",
    "最差质量 (最小文件)": "worst",
}


class DownloaderGUI(tk.Tk):
    """Main GUI window for the video downloader."""

    def __init__(self) -> None:
        super().__init__()

        self.title("Video Downloader")
        self.geometry("640x520")
        self.minsize(500, 420)
        self.resizable(True, True)

        self._downloader: VideoDownloader | None = None
        self._downloading = False

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Create and lay out all UI widgets."""
        # --- Top padding ---
        ttk.Label(self, text=" ").pack()

        # --- URL row ---
        url_frame = ttk.Frame(self)
        url_frame.pack(fill=tk.X, padx=12, pady=(4, 2))
        ttk.Label(url_frame, text="视频地址:").pack(side=tk.LEFT)
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))

        # --- Output directory row ---
        dir_frame = ttk.Frame(self)
        dir_frame.pack(fill=tk.X, padx=12, pady=4)
        ttk.Label(dir_frame, text="保存目录:").pack(side=tk.LEFT)
        self.dir_var = tk.StringVar(value=str(Path.cwd() / "downloads"))
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var)
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))
        ttk.Button(dir_frame, text="浏览...", command=self._browse_dir, width=8).pack(
            side=tk.LEFT, padx=(4, 0)
        )

        # --- Format row ---
        fmt_frame = ttk.Frame(self)
        fmt_frame.pack(fill=tk.X, padx=12, pady=4)
        ttk.Label(fmt_frame, text="下载格式:").pack(side=tk.LEFT)
        self.fmt_var = tk.StringVar(value=list(FORMAT_PRESETS.keys())[0])
        self.fmt_combo = ttk.Combobox(
            fmt_frame,
            textvariable=self.fmt_var,
            values=list(FORMAT_PRESETS.keys()),
            state="readonly",
            width=28,
        )
        self.fmt_combo.pack(side=tk.LEFT, padx=(6, 0))

        # --- Audio-only checkbox ---
        self.audio_only_var = tk.BooleanVar(value=False)

        def _on_fmt_changed(*_args: object) -> None:
            """Sync the audio_only checkbox when the user picks '仅音频' from the dropdown."""
            if "音频" in self.fmt_var.get():
                self.audio_only_var.set(True)
            else:
                self.audio_only_var.set(False)

        self.fmt_var.trace_add("write", _on_fmt_changed)
        self.audio_cb = ttk.Checkbutton(
            fmt_frame,
            text="仅音频",
            variable=self.audio_only_var,
            command=self._on_audio_check,
        )
        self.audio_cb.pack(side=tk.LEFT, padx=(12, 0))

        # --- Cookie file row (optional) ---
        cookie_frame = ttk.Frame(self)
        cookie_frame.pack(fill=tk.X, padx=12, pady=2)
        ttk.Label(cookie_frame, text="Cookie文件 (可选):").pack(side=tk.LEFT)
        self.cookie_var = tk.StringVar()
        self.cookie_entry = ttk.Entry(cookie_frame, textvariable=self.cookie_var)
        self.cookie_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))
        ttk.Button(
            cookie_frame, text="浏览...", command=self._browse_cookie, width=8
        ).pack(side=tk.LEFT, padx=(4, 0))

        # --- Separator ---
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=12, pady=10)

        # --- Download button ---
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=12, pady=(0, 4))
        self.dl_btn = ttk.Button(
            btn_frame, text="开始下载", command=self._start_download
        )
        self.dl_btn.pack(side=tk.LEFT)
        self.cancel_btn = ttk.Button(
            btn_frame, text="取消", command=self._cancel_download, state=tk.DISABLED
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=(6, 0))

        # --- Progress bar ---
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self,
            variable=self.progress_var,
            mode="determinate",
            length=580,
        )
        self.progress_bar.pack(fill=tk.X, padx=12, pady=(0, 4))

        # --- Status label ---
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(
            self, textvariable=self.status_var, anchor=tk.W, foreground="gray"
        )
        status_label.pack(fill=tk.X, padx=12, pady=(0, 6))

        # --- Log area ---
        log_frame = ttk.Frame(self)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))
        ttk.Label(log_frame, text="下载日志:").pack(anchor=tk.W)
        self.log_text = tk.Text(
            log_frame,
            height=8,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 9),
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(2, 0))

        # Scrollbar for log
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _browse_dir(self) -> None:
        path = filedialog.askdirectory(title="选择下载保存目录")
        if path:
            self.dir_var.set(path)

    def _browse_cookie(self) -> None:
        path = filedialog.askopenfilename(
            title="选择 Cookie 文件", filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            self.cookie_var.set(path)

    def _on_audio_check(self) -> None:
        """When audio-only is toggled via checkbox, sync the format dropdown."""
        if self.audio_only_var.get():
            self.fmt_var.set("仅音频 (MP3)")
        else:
            self.fmt_var.set("最佳质量 (推荐)")

    def _log(self, message: str) -> None:
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Download logic (runs in background thread)
    # ------------------------------------------------------------------

    def _start_download(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("提示", "请输入视频地址")
            return

        output_dir = self.dir_var.get().strip()
        if not output_dir:
            messagebox.showwarning("提示", "请选择保存目录")
            return

        # Check FFmpeg availability (required for merging video+audio)
        ffmpeg_path = _find_ffmpeg()
        if not ffmpeg_path:
            self._log("⚠ 未检测到 FFmpeg，高清视频下载将失败")
            self._log("  请运行: winget install Gyan.FFmpeg")
            messagebox.showwarning(
                "缺少 FFmpeg",
                "未检测到 FFmpeg！\n\n"
                "下载高清视频需要 FFmpeg 来合并视频和音频。\n\n"
                "请打开命令行运行以下命令安装（只需一次）：\n"
                "  winget install Gyan.FFmpeg\n\n"
                "安装完成后重新启动本程序即可。",
            )
        else:
            self._log(f"FFmpeg: {ffmpeg_path}")

        self._downloading = True
        self._set_ui_state(downloading=True)
        self._log(f"开始下载: {url}")
        self._log(f"保存目录: {output_dir}")

        cookie = self.cookie_var.get().strip() or None
        self._downloader = VideoDownloader(output_dir=output_dir, cookiefile=cookie)

        thread = threading.Thread(
            target=self._do_download,
            args=(url,),
            daemon=True,
        )
        thread.start()

    def _do_download(self, url: str) -> None:
        try:
            # Step 1: extract info
            self._update_status("正在获取视频信息...")
            self._log("获取视频信息...")
            info = self._downloader.extract_info(url)
            title = info.get("title", "未知标题")
            duration = info.get("duration", 0)
            self._log(f"  标题: {title}")
            self._log(f"  时长: {duration}s")

            # Step 2: download
            preset_label = self.fmt_var.get()
            fmt = FORMAT_PRESETS.get(preset_label, "best")
            audio_only = self.audio_only_var.get()

            self._update_status("正在下载...")
            self._log(f"  格式: {preset_label} ({fmt})")

            result = self._downloader.download(
                url,
                format=fmt,
                audio_only=audio_only,
                progress_callback=self._on_progress,
            )

            filename = result.get("title", "完成")
            self._log(f"✓ 下载完成: {filename}")
            self._update_status("下载完成 ✓")
            self.progress_var.set(100)
            self.after(0, lambda: messagebox.showinfo("完成", f"下载完成:\n{filename}"))

        except Exception as exc:
            self._log(f"✗ 错误: {exc}")
            self._update_status("下载失败 ✗")
            self.after(0, lambda _err=str(exc): messagebox.showerror("错误", _err))
        finally:
            self._downloading = False
            self.after(0, lambda: self._set_ui_state(downloading=False))

    def _on_progress(self, d: dict) -> None:
        status = d.get("status", "")
        if status == "downloading":
            pct_str = d.get("_percent_str", "0%")
            speed_str = d.get("_speed_str", "?")
            eta_str = d.get("_eta_str", "?")

            # Parse percentage (strip ANSI & '%')
            try:
                pct = float(pct_str.replace("%", "").strip())
            except ValueError:
                pct = 0
            self.progress_var.set(pct)
            self._update_status(f"下载中... {pct_str} 速度: {speed_str} 剩余: {eta_str}")

        elif status == "finished":
            self._log("  处理中 (合并/转换)...")
            self._update_status("正在处理文件...")

    def _cancel_download(self) -> None:
        # yt-dlp doesn't expose a clean cancel, but we can signal
        self._log("正在取消...")
        self._downloading = False
        self._update_status("已取消")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_ui_state(self, *, downloading: bool) -> None:
        state = tk.DISABLED if downloading else tk.NORMAL
        self.url_entry.config(state=state)
        self.dir_entry.config(state=state)
        self.fmt_combo.config(state="readonly" if not downloading else tk.DISABLED)
        self.audio_cb.config(state=state)
        self.cookie_entry.config(state=state)
        self.dl_btn.config(state=tk.DISABLED if downloading else tk.NORMAL)
        self.cancel_btn.config(state=tk.NORMAL if downloading else tk.DISABLED)
        if not downloading:
            self.progress_var.set(0)

    def _update_status(self, text: str) -> None:
        self.after(0, lambda: self.status_var.set(text))


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------


def main() -> None:
    """Launch the GUI."""
    app = DownloaderGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
