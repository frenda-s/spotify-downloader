#!/usr/bin/env bash
# Interactive launcher for the Spotify and YouTube downloader.
# Prompts for a link, destination directory, audio format and extra options,
# then runs the Python entry point with the matching flags.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GREEN=$'\033[38;2;30;215;96m'
DIM=$'\033[2m'
CYAN=$'\033[36m'
YELLOW=$'\033[33m'
RED=$'\033[31m'
BOLD=$'\033[1m'
RESET=$'\033[0m'

clear 2>/dev/null || true

printf '%s%s' "$GREEN" "$BOLD"
cat <<'BANNER'
  ███████╗██████╗  ██████╗ ████████╗██╗███████╗██╗   ██╗
  ██╔════╝██╔══██╗██╔═══██╗╚══██╔══╝██║██╔════╝╚██╗ ██╔╝
  ███████╗██████╔╝██║   ██║   ██║   ██║█████╗   ╚████╔╝
  ╚════██║██╔═══╝ ██║   ██║   ██║   ██║██╔══╝    ╚██╔╝
  ███████║██║     ╚██████╔╝   ██║   ██║██║        ██║
  ╚══════╝╚═╝      ╚═════╝    ╚═╝   ╚═╝╚═╝        ╚═╝
BANNER
printf '%s          SPOTIFY AND YOUTUBE DOWNLOADER%s\n' "$BOLD" "$RESET"
printf '%s  Audio to MP3, M4A, FLAC, OPUS, OGG and WAV with artwork and tags%s\n' "$DIM" "$RESET"
printf '%s──────────────────────────────────────────────────────────────%s\n\n' "$DIM" "$RESET"

if [ ! -d "$DIR/.venv" ]; then
    printf '%s[*] Creating the Python virtual environment...%s\n' "$YELLOW" "$RESET"
    python3 -m venv "$DIR/.venv"
    "$DIR/.venv/bin/pip" install --upgrade pip
    "$DIR/.venv/bin/pip" install -r "$DIR/requirements.txt"
fi

TARGET="${1:-}"
if [ -z "$TARGET" ]; then
    printf '%s[?] Paste a Spotify or YouTube link (track, album, playlist, video):%s\n' "$CYAN" "$RESET"
    read -rp "    > " TARGET
    if [ -z "$TARGET" ]; then
        printf '%s[!] A link is required.%s\n' "$RED" "$RESET"
        exit 1
    fi
fi

DEFAULT_OUTPUT="$HOME/Downloads"
printf '\n%s[?] Destination directory [default: %s]:%s\n' "$CYAN" "$DEFAULT_OUTPUT" "$RESET"
read -rp "    > " USER_OUTPUT
if [ -z "$USER_OUTPUT" ]; then
    OUTPUT_DIR="$DEFAULT_OUTPUT"
else
    USER_OUTPUT="${USER_OUTPUT//\\//}"
    OUTPUT_DIR="${USER_OUTPUT/#\~/$HOME}"
fi
mkdir -p "$OUTPUT_DIR"

printf '\n%s[?] Audio format:%s\n' "$CYAN" "$RESET"
printf '    %s1)%s MP3  (320 kbps, widest compatibility)\n' "$BOLD" "$RESET"
printf '    %s2)%s M4A  (AAC, small files, good quality)\n' "$BOLD" "$RESET"
printf '    %s3)%s FLAC (lossless, large files)\n' "$BOLD" "$RESET"
printf '    %s4)%s OPUS\n' "$BOLD" "$RESET"
read -rp "    Choose [1-4, default 1]: " FORMAT_CHOICE

case "$FORMAT_CHOICE" in
    2) FORMAT="m4a"; BITRATE="auto" ;;
    3) FORMAT="flac"; BITRATE="auto" ;;
    4) FORMAT="opus"; BITRATE="auto" ;;
    *) FORMAT="mp3"; BITRATE="320k" ;;
esac

EXTRAS=()
printf '\n%s[?] Extra options:%s\n' "$CYAN" "$RESET"
read -rp "    Embed synced lyrics and write .lrc files? [y/N] " WANT_LYRICS
case "${WANT_LYRICS,,}" in y|yes) EXTRAS+=("--lyrics") ;; esac
read -rp "    Save cover images as separate .jpg files? [y/N] " WANT_COVER
case "${WANT_COVER,,}" in y|yes) EXTRAS+=("--save-cover") ;; esac

printf '\n%s[*] Starting download...%s\n' "$GREEN" "$RESET"
printf '    %sSource :%s %s\n' "$DIM" "$RESET" "$TARGET"
printf '    %sOutput :%s %s\n' "$DIM" "$RESET" "$OUTPUT_DIR"
printf '    %sFormat :%s %s (%s)\n\n' "$DIM" "$RESET" "$FORMAT" "$BITRATE"

"$DIR/.venv/bin/python" "$DIR/spotify_downloader.py" \
    "$TARGET" \
    --output "$OUTPUT_DIR" \
    --format "$FORMAT" \
    --bitrate "$BITRATE" \
    "${EXTRAS[@]+"${EXTRAS[@]}"}"

printf '\n%s%s[+] Finished.%s\n' "$GREEN" "$BOLD" "$RESET"
printf '    Files with embedded artwork and metadata are in: %s%s%s\n\n' "$BOLD" "$OUTPUT_DIR" "$RESET"
