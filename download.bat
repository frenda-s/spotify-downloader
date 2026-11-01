@echo off
:: Interactive Windows launcher for Spotify and YouTube Downloader.
:: Supports Command Prompt and double-click execution.
setlocal enabledelayedexpansion
chcp 65001 >nul

set "DIR=%~dp0"
set "PYTHON_EXE=%DIR%.venv\Scripts\python.exe"
set "PIP_EXE=%DIR%.venv\Scripts\pip.exe"

title Spotify and YouTube Downloader

echo ================================================================
echo           SPOTIFY AND YOUTUBE DOWNLOADER (Windows)
echo   Audio to MP3, M4A, FLAC, OPUS with metadata and cover artwork
echo ================================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] Python is not installed or not in PATH.
    echo     Please install Python 3.9+ from https://www.python.org/
    echo     and make sure to check "Add Python to PATH" during setup.
    pause
    exit /b 1
)

if not exist "%PYTHON_EXE%" (
    echo [*] Initializing virtual environment in .venv...
    python -m venv "%DIR%.venv"
    if %errorlevel% neq 0 (
        echo [!] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [*] Installing dependencies from requirements.txt...
    "%PIP_EXE%" install --upgrade pip >nul 2>nul
    "%PIP_EXE%" install -r "%DIR%requirements.txt"
    if %errorlevel% neq 0 (
        echo [!] Failed to install dependencies.
        pause
        exit /b 1
    )
)

set "TARGET=%~1"
if "%TARGET%"=="" (
    set /p "TARGET=[?] Paste Spotify or YouTube link (track, album, playlist, video): "
    if "!TARGET!"=="" (
        echo [!] Target link cannot be empty.
        pause
        exit /b 1
    )
)

set "DEFAULT_OUTPUT=%USERPROFILE%\Downloads"
echo.
echo [?] Destination folder [Default: %DEFAULT_OUTPUT%]
set /p "USER_OUTPUT=    > "
if "!USER_OUTPUT!"=="" (
    set "OUTPUT_DIR=%DEFAULT_OUTPUT%"
) else (
    set "OUTPUT_DIR=!USER_OUTPUT!"
)

if not exist "!OUTPUT_DIR!" mkdir "!OUTPUT_DIR!" 2>nul

echo.
echo [?] Audio format:
echo     1) MP3  (320 kbps, recommended, maximum compatibility)
echo     2) M4A  (AAC, small file size, high quality)
echo     3) FLAC (Lossless, large file size)
echo     4) OPUS
set /p "FORMAT_CHOICE=    Choose [1-4, default 1]: "

set "FORMAT=mp3"
set "BITRATE=320k"
if "!FORMAT_CHOICE!"=="2" ( set "FORMAT=m4a" & set "BITRATE=auto" )
if "!FORMAT_CHOICE!"=="3" ( set "FORMAT=flac" & set "BITRATE=auto" )
if "!FORMAT_CHOICE!"=="4" ( set "FORMAT=opus" & set "BITRATE=auto" )

set "EXTRAS="
echo.
set /p "WANT_LYRICS=    Fetch synced lyrics (.lrc files)? [y/N]: "
if /i "!WANT_LYRICS!"=="y" set "EXTRAS=!EXTRAS! --lyrics"
if /i "!WANT_LYRICS!"=="yes" set "EXTRAS=!EXTRAS! --lyrics"

set /p "WANT_COVER=    Save standalone .jpg cover images? [y/N]: "
if /i "!WANT_COVER!"=="y" set "EXTRAS=!EXTRAS! --save-cover"
if /i "!WANT_COVER!"=="yes" set "EXTRAS=!EXTRAS! --save-cover"

echo.
echo [*] Starting download process...
echo     Source : !TARGET!
echo     Output : !OUTPUT_DIR!
echo     Format : !FORMAT! (!BITRATE!)
echo.

"%PYTHON_EXE%" "%DIR%spotify_downloader.py" "!TARGET!" --output "!OUTPUT_DIR!" --format "!FORMAT!" --bitrate "!BITRATE!" !EXTRAS!

if %errorlevel% equ 0 (
    echo.
    echo [+] Completed successfully.
    echo     Files saved to: !OUTPUT_DIR!
) else (
    echo.
    echo [!] Download encountered an error. Code: %errorlevel%
)

echo.
pause
