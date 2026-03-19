# ScreenCapture360

A lightweight PyQt6 desktop application for recording your screen or any application window.

## Features

- 🖥 **Monitor recording** — capture any connected display
- 🪟 **Window recording** — capture a specific application window (follows the window if moved)
- ⏸ **Pause / Resume** — pause mid-recording without ending the session
- ⏹ **Stop** — finalise and save the recording
- 🎙 **Audio recording** — capture microphone input during screen recording
- 🔊 **Audio/Video Muxing** — automatically combines audio and video into a single MP4
- 🔴 **Floating controls** — draggable, always-on-top pill with a pulsing REC indicator and audio toggle
- 💾 **Auto-save** — output saved to `~/Videos/ScreenCapture360_YYYYMMDD_HHMMSS.mp4`

## Requirements

- Python 3.11+
- Windows 10 / 11

## Setup

```bash
# 1. Install dependencies and create venv
poetry install

# 2. Run the application
poetry run python main.py

# 3. Build standalone executable (Windows)
# This generates ScreenCapture360.exe in the dist/ folder
poetry run python scripts/build_windows.py
```

## Installation (Windows)

You can run the standalone executable directly without installing Python:
1. Navigate to the `dist/` folder.
2. Run `ScreenCapture360.exe`.

### Professional Installer (Optional)

If you want to create a professional `.exe` installer (with wizard and uninstaller):
1. Install [Inno Setup](https://jrsoftware.org/isdl.php).
2. Open `scripts/installer.iss` in Inno Setup.
3. Click **Compile**.
4. The installer will be generated in `scripts/Output/`.

> [!WARNING]
> **Windows SmartScreen Warning**: Since this application is not digitally signed, Windows may show a protection warning ("Windows protected your PC"). 
> - Click **"More info"**
> - Click **"Run anyway"**

## Project Structure

```
ScreenCapture360/
├── main.py                  # Entry point
├── requirements.txt
├── ui/
│   ├── main_window.py       # Primary window
│   ├── screen_selector.py   # Monitor / window picker dialog
│   └── floating_controls.py # Always-on-top recording controls
├── core/
│   └── recorder.py          # Background capture & encoding thread
├── scripts/
│   └── build_windows.py     # Windows build automation script
└── dist/                    # Output directory for standalone executable
```

## Output

Videos are saved as `.mp4` (H.264) in `~/Videos/`.

## License

Copyright (c) 2026 KhowarLabs. All rights reserved. 

The source code in this repository is proprietary. Unauthorized copying, modification, or redistribution of the code is strictly prohibited. See the [LICENSE](LICENSE) file for more details.
