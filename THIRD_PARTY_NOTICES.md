# Third-Party Notices

This repository incorporates or interacts with the following third-party open-source components and standards:

## 1. Claudemy (`assafkip/claudemy`)
- **Copyright**: Copyright (c) 2026 Assaf Kipnis
- **License**: MIT License (see [LICENSE](LICENSE))
- **Scope in Repository**: `skills/claudemy/`, `.agents/skills/claudemy/`, `hooks/export_elevenlabs_key.py`, and baseline unit tests in `tests/test_scripts.py`.

## 2. Beautiful Soup 4 (`beautifulsoup4`)
- **Author**: Leonard Richardson
- **License**: MIT License
- **Usage**: HTML parsing in `learning_engine/src/learning_engine/documents/ingestor.py` and `skills/claudemy/scripts/scrape.py`.

## 3. External Optional CLI / Runtime Tools (Not Bundled)
- **FFmpeg** (`ffmpeg` / `ffprobe`): Optional system tool used when stitching multi-turn audio files.
- **Google Antigravity Python SDK** (`google-antigravity`): Optional PyPI package detected dynamically via `learning_engine.mcp.adapters.AntigravitySDKRuntimeAdapter`.
- **ElevenLabs API**: Optional user-configured cloud TTS API (`ELEVENLABS_API_KEY`).
