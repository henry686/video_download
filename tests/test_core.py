"""Tests for video_download.core."""

from unittest.mock import patch

from video_download import VideoDownloader


class TestVideoDownloader:
    """Tests for the VideoDownloader class."""

    def test_init_default_output_dir(self):
        dl = VideoDownloader()
        assert str(dl.output_dir) in str(dl.output_dir)

    def test_init_custom_output_dir(self):
        dl = VideoDownloader(output_dir="./my_videos")
        assert dl.output_dir.name == "my_videos"

    def test_init_with_cookiefile(self):
        dl = VideoDownloader(cookiefile="./cookies.txt")
        assert dl.cookiefile == "./cookies.txt"

    def test_init_with_proxy(self):
        dl = VideoDownloader(proxy="socks5://127.0.0.1:1080")
        assert dl.proxy == "socks5://127.0.0.1:1080"

    def test_build_options_includes_cookiefile(self):
        dl = VideoDownloader(cookiefile="./cookies.txt")
        opts = dl._build_options(format="best")
        assert opts["cookiefile"] == "./cookies.txt"

    def test_build_options_includes_proxy(self):
        dl = VideoDownloader(proxy="http://proxy:8080")
        opts = dl._build_options(format="best")
        assert opts["proxy"] == "http://proxy:8080"

    def test_build_options_format(self):
        dl = VideoDownloader()
        opts = dl._build_options(format="bestaudio")
        assert opts["format"] == "bestaudio"

    def test_build_options_output_template(self):
        from pathlib import Path

        dl = VideoDownloader(output_dir="/tmp/dl")
        opts = dl._build_options(format="best")
        expected = str(Path("/tmp/dl") / "%(title)s.%(ext)s")
        assert opts["outtmpl"] == expected

    def test_build_options_custom_template(self):
        dl = VideoDownloader()
        opts = dl._build_options(
            format="best",
            output_template="%(uploader)s/%(title)s.%(ext)s",
        )
        assert opts["outtmpl"] == "%(uploader)s/%(title)s.%(ext)s"

    def test_build_options_progress_hook(self):
        dl = VideoDownloader()
        def hook(d: dict) -> None:
            pass
        opts = dl._build_options(format="best", progress_callback=hook)
        assert hook in opts["progress_hooks"]

    def test_build_options_quiet(self):
        dl = VideoDownloader(quiet=True)
        opts = dl._build_options(format="best")
        assert opts["quiet"] is True
        assert opts["no_warnings"] is True

    def test_extract_info_mock(self):
        dl = VideoDownloader()
        with patch("yt_dlp.YoutubeDL") as mock_ydl:
            instance = mock_ydl.return_value
            instance.__enter__.return_value = instance
            instance.extract_info.return_value = {
                "title": "Test Video",
                "duration": 120,
            }
            info = dl.extract_info("https://example.com/video")
            assert info["title"] == "Test Video"
            assert info["duration"] == 120

    def test_list_formats_mock(self):
        dl = VideoDownloader()
        with patch.object(dl, "extract_info") as mock_extract:
            mock_extract.return_value = {
                "formats": [
                    {"format_id": "22", "ext": "mp4", "height": 720},
                    {"format_id": "37", "ext": "mp4", "height": 1080},
                ]
            }
            formats = dl.list_formats("https://example.com/video")
            assert len(formats) == 2
            assert formats[0]["format_id"] == "22"

    def test_download_audio_only_sets_postprocessor(self):
        dl = VideoDownloader()
        with patch.object(dl, "_run") as mock_run:
            mock_run.return_value = {"title": "Test"}
            dl.download("https://example.com/video", audio_only=True)
            call_opts = mock_run.call_args[0][1]
            assert call_opts["format"] == "bestaudio/best"
            assert any(
                pp.get("key") == "FFmpegExtractAudio"
                for pp in call_opts.get("postprocessors", [])
            )
