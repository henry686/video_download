# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for VideoDownloader GUI.

Usage:
    pyinstaller VideoDownloader.spec
"""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

# -- Collect yt-dlp and bilibili-api with all their dynamic imports --
yt_dlp_datas, yt_dlp_binaries, yt_dlp_hiddenimports = collect_all("yt_dlp")
bili_datas, bili_binaries, bili_hiddenimports = collect_all("bilibili_api")

hiddenimports = [
    # yt-dlp runtime
    *yt_dlp_hiddenimports,
    # bilibili-api + its TLS backend
    *bili_hiddenimports,
    "curl_cffi",
    # Standard library modules that PyInstaller may miss
    "urllib.parse", "html.parser", "xml.etree.ElementTree", "json",
    "http.cookiejar", "netrc",
]

# Collect our own source package (SPECPATH = directory of this .spec file)
src_path = Path(SPECPATH) / "src"
package_path = src_path / "video_download"

a = Analysis(
    [str(package_path / "gui.py")],
    pathex=[str(src_path)],
    binaries=yt_dlp_binaries + bili_binaries,
    datas=[
        *yt_dlp_datas,
        *bili_datas,
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Reduce size: exclude dev/test tools
        "pytest", "pip", "setuptools",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="VideoDownloader",
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # --windowed: no console popup
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,           # Set to a .ico path to add a custom icon
)
