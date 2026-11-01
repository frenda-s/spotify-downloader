#!/usr/bin/env python3
"""Spotify and YouTube audio downloader with embedded metadata and cover art.

Resolves a Spotify album, playlist or track link, or a YouTube video,
playlist or Shorts link, into local audio files with cover art and ID3
tags already embedded.

Intended for personal offline listening of audio you have the rights to.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4

VERSION = "1.0.0"
SUPPORTED_FORMATS = ("mp3", "m4a", "flac", "opus", "ogg", "wav")
YOUTUBE_PATTERNS = (
    r"youtube\.com/watch",
    r"youtu\.be/",
    r"youtube\.com/playlist",
    r"youtube\.com/shorts/",
    r"music\.youtube\.com/",
)
SPOTIFY_PATTERNS = (
    r"open\.spotify\.com/",
    r"spotify:",
)


class ToolError(RuntimeError):
    """Raised when an external binary is missing or exits with an error."""


def resolve_binary(name: str) -> str:
    """Prefer the binary installed in the local .venv, otherwise use PATH.

    Handles POSIX layout (.venv/bin/<name>) and Windows (.venv/Scripts/<name>.exe).
    """
    root = Path(__file__).resolve().parent
    candidates = (
        root / ".venv" / "Scripts" / f"{name}.exe",
        root / ".venv" / "Scripts" / name,
        root / ".venv" / "bin" / name,
    )
    for path in candidates:
        if path.is_file():
            return str(path)
    found = shutil.which(name)
    if not found:
        raise ToolError(
            f"required binary '{name}' not found. Install it with "
            f"'{sys.executable} -m pip install {name}' or add it to PATH"
        )
    return found


def is_youtube_query(query: str) -> bool:
    """Return True when the query points at YouTube."""
    return any(re.search(pattern, query, re.IGNORECASE) for pattern in YOUTUBE_PATTERNS)


def is_spotify_query(query: str) -> bool:
    """Return True when the query points at Spotify."""
    return any(re.search(pattern, query, re.IGNORECASE) for pattern in SPOTIFY_PATTERNS)


def extract_cover(audio_path: Path, image_path: Path) -> bool:
    """Write the first embedded picture of an audio file to image_path."""
    try:
        suffix = audio_path.suffix.lower()
        if suffix == ".mp3":
            audio = MP3(str(audio_path))
            for frame in (audio.tags or {}).values():
                if getattr(frame, "FrameID", None) == "APIC":
                    image_path.write_bytes(frame.data)
                    return True
        elif suffix == ".flac":
            audio = FLAC(str(audio_path))
            if audio.pictures:
                image_path.write_bytes(audio.pictures[0].data)
                return True
        elif suffix in (".m4a", ".mp4"):
            audio = MP4(str(audio_path))
            covers = (audio.tags or {}).get("covr", [])
            if covers:
                image_path.write_bytes(bytes(covers[0]))
                return True
    except Exception as exc:  # one damaged file must not abort the batch
        print(f"[warn] could not read cover from {audio_path.name}: {exc}")
    return False


def export_covers(directory: Path, audio_format: str, save_cover: bool) -> int:
    """Save a .jpg per track and a folder cover. Returns how many were written."""
    written = 0
    for audio_path in sorted(directory.glob(f"*.{audio_format}")):
        image_path = audio_path.with_suffix(".jpg")
        if not image_path.exists() and extract_cover(audio_path, image_path):
            written += 1

    folder_cover = directory / "cover.jpg"
    if save_cover and not folder_cover.exists():
        first = next(iter(sorted(directory.glob("*.jpg"))), None)
        if first:
            folder_cover.write_bytes(first.read_bytes())
    return written


def run_external(command: list[str], label: str) -> None:
    """Run an external command and raise a clean error on failure."""
    print(f"[*] running {label}")
    try:
        result = subprocess.run(command)
    except OSError as exc:
        raise ToolError(f"could not start {label}: {exc}") from exc
    if result.returncode != 0:
        raise ToolError(f"{label} exited with code {result.returncode}")


def download_youtube(
    query: str,
    output_dir: Path,
    audio_format: str,
    save_cover: bool,
) -> None:
    """Fetch audio from YouTube with thumbnail and metadata embedded."""
    command = [
        resolve_binary("yt-dlp"),
        "--extract-audio",
        "--audio-format",
        audio_format,
        "--audio-quality",
        "0",
        "--embed-thumbnail",
        "--embed-metadata",
        "--output",
        str(output_dir / "%(title)s.%(ext)s"),
    ]
    if "playlist" in query.lower():
        command.append("--yes-playlist")
    else:
        command.append("--no-playlist")
    if save_cover:
        command.extend(["--write-thumbnail", "--convert-thumbnails", "jpg"])
    command.append(query)
    run_external(command, "yt-dlp")


def download_spotify(
    query: str,
    output_dir: Path,
    audio_format: str,
    bitrate: str,
    threads: int,
    fetch_lyrics: bool,
    overwrite: str,
) -> None:
    """Fetch tracks through spotdl and export the embedded artwork."""
    command = [
        resolve_binary("spotdl"),
        "download",
        query,
        "--format",
        audio_format,
        "--bitrate",
        bitrate,
        "--threads",
        str(threads),
        "--overwrite",
        overwrite,
        "--output",
        str(output_dir / "{artists} - {title}.{output-ext}"),
    ]
    if fetch_lyrics:
        command.extend(["--lyrics", "synced", "--generate-lrc"])
    run_external(command, "spotdl")


def prepare_output_dir(raw: str | None) -> Path:
    """Resolve and create the destination directory."""
    directory = Path(raw).expanduser() if raw else Path.home() / "Downloads"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def download_media(
    query: str,
    output_dir: str | None = None,
    audio_format: str = "mp3",
    bitrate: str = "320k",
    threads: int = 4,
    save_cover: bool = False,
    fetch_lyrics: bool = False,
    overwrite: str = "skip",
) -> int:
    """Route the query to the matching backend and report what was written."""
    directory = prepare_output_dir(output_dir)
    use_youtube = is_youtube_query(query)

    print(f"[*] source : {'YouTube' if use_youtube else 'Spotify'}")
    print(f"[*] target : {query}")
    print(f"[*] output : {directory}")
    print(f"[*] format : {audio_format} ({bitrate})")
    print(f"[*] threads: {threads}")

    if use_youtube:
        download_youtube(query, directory, audio_format, save_cover)
    else:
        if not is_spotify_query(query):
            print("[warn] input is not a Spotify link, spotdl will treat it as a search phrase")
        download_spotify(
            query,
            directory,
            audio_format,
            bitrate,
            max(1, threads),
            fetch_lyrics,
            overwrite,
        )

    written = export_covers(directory, audio_format, save_cover)
    if written:
        print(f"[+] wrote {written} cover image(s) to {directory}")

    tracks = len(list(directory.glob(f"*.{audio_format}")))
    print(f"[+] done: {tracks} {audio_format} file(s) in {directory}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spotify_downloader",
        description=(
            "Download Spotify or YouTube audio into MP3, M4A, FLAC, OPUS, OGG "
            "or WAV with embedded cover art and metadata."
        ),
    )
    parser.add_argument("query", help="Spotify or YouTube URL, or a search phrase")
    parser.add_argument("-o", "--output", help="output directory (default: ~/Downloads)")
    parser.add_argument(
        "-f",
        "--format",
        default="mp3",
        choices=SUPPORTED_FORMATS,
        help="audio container (default: mp3)",
    )
    parser.add_argument("-b", "--bitrate", default="320k", help="bitrate (default: 320k)")
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=4,
        help="parallel downloads (default: 4)",
    )
    parser.add_argument(
        "--save-cover",
        action="store_true",
        help="also write a .jpg cover per track and a folder cover",
    )
    parser.add_argument(
        "--lyrics",
        action="store_true",
        help="embed synced lyrics and write matching .lrc files",
    )
    parser.add_argument(
        "--overwrite",
        default="skip",
        choices=("skip", "metadata", "force"),
        help="behaviour for files that already exist (default: skip)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return download_media(
            query=args.query,
            output_dir=args.output,
            audio_format=args.format,
            bitrate=args.bitrate,
            threads=args.threads,
            save_cover=args.save_cover,
            fetch_lyrics=args.lyrics,
            overwrite=args.overwrite,
        )
    except ToolError as exc:
        print(f"[!] {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n[!] interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
