#!/usr/bin/env python3
"""Smoke checks for spotify_downloader.

Run with:  .venv/bin/python tests/test_smoke.py

Verifies URL routing, cover extraction from a real MP3 container, and the
exact command lines handed to spotdl and yt-dlp. No network access required.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import spotify_downloader as sd  # noqa: E402


class RoutingTests(unittest.TestCase):
    def test_youtube_urls(self):
        for url in (
            "https://www.youtube.com/watch?v=abc",
            "https://youtu.be/abc",
            "https://music.youtube.com/watch?v=abc",
            "https://www.youtube.com/shorts/abc",
        ):
            self.assertTrue(sd.is_youtube_query(url), url)

    def test_spotify_urls(self):
        for url in (
            "https://open.spotify.com/album/xyz",
            "spotify:track:xyz",
        ):
            self.assertTrue(sd.is_spotify_query(url), url)

    def test_unrelated_url(self):
        self.assertFalse(sd.is_youtube_query("https://example.com"))
        self.assertFalse(sd.is_spotify_query("https://example.com"))


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.calls = []

        def fake_run(command, **kwargs):
            self.calls.append(command)
            return subprocess.CompletedProcess(command, 0)

        patcher = mock.patch("spotify_downloader.subprocess.run", side_effect=fake_run)
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_spotify_command_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            sd.download_spotify(
                "https://open.spotify.com/album/xyz",
                Path(tmp),
                "flac",
                "auto",
                6,
                True,
                "skip",
            )
        command = self.calls[0]
        self.assertIn("--format", command)
        self.assertEqual(command[command.index("--format") + 1], "flac")
        self.assertEqual(command[command.index("--threads") + 1], "6")
        self.assertIn("--lyrics", command)
        self.assertIn("--generate-lrc", command)

    def test_youtube_command_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            sd.download_youtube(
                "https://www.youtube.com/watch?v=abc", Path(tmp), "mp3", True
            )
        command = self.calls[0]
        self.assertIn("--extract-audio", command)
        self.assertIn("--embed-thumbnail", command)
        self.assertIn("--write-thumbnail", command)
        self.assertEqual(command[-1], "https://www.youtube.com/watch?v=abc")

    def test_missing_binary_raises(self):
        with mock.patch("spotify_downloader.shutil.which", return_value=None):
            with self.assertRaises(sd.ToolError):
                sd.resolve_binary("definitely-not-installed-binary")


class CoverTests(unittest.TestCase):
    def test_extract_from_generated_mp3(self):
        """Build an MP3 with an embedded picture using ffmpeg, then extract it."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            cover = tmp_path / "cover.png"
            audio = tmp_path / "fixture.mp3"
            built = subprocess.run(
                [
                    "ffmpeg", "-loglevel", "error",
                    "-f", "lavfi", "-i", "color=c=#1ed760:s=300x300:d=1",
                    "-frames:v", "1", "-y", str(cover),
                ]
            )
            if built.returncode != 0:
                self.skipTest("ffmpeg unavailable")
            subprocess.run(
                [
                    "ffmpeg", "-loglevel", "error",
                    "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
                    "-i", str(cover),
                    "-map", "0:a", "-map", "1:v",
                    "-c:a", "libmp3lame", "-b:a", "128k", "-c:v", "copy",
                    "-id3v2_version", "3",
                    "-metadata:s:v", "title=Album cover",
                    "-metadata", "artist=Test",
                    "-y", str(audio),
                ],
                check=True,
            )
            out = tmp_path / "extracted.jpg"
            self.assertTrue(sd.extract_cover(audio, out))
            self.assertGreater(out.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
