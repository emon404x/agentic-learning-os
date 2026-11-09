# Installation Guide (`Agentic Learning OS` v3.0.0)

**Project Name**: Agentic Learning OS (`agentic-learning-os`)  
**Developer & Maintainer**: **Md. Aktaruzzaman Emon** ([@emon404x](https://github.com/emon404x))  
**Repository**: [https://github.com/emon404x/agentic-learning-os](https://github.com/emon404x/agentic-learning-os)

---

## 1. Prerequisites
- **Python**: Python `3.10+` (tested on Python `3.10` through `3.14` across Windows, macOS, and Linux).
- **Optional System Tools**:
  - `ffmpeg` & `ffprobe` (optional — used only when stitching multi-turn audio files).
  - `gcc` / `clang` / `node` / `javac` (optional — used for compiled C/C++/Java/JS lab execution; Python and SQL labs run out-of-the-box via Python's standard library).

---

## 2. Clone & Install

```powershell
# Clone your repository
git clone https://github.com/emon404x/agentic-learning-os.git
cd agentic-learning-os

# Install in editable mode
pip install -e .
```

---

## 3. Environment Configuration (Optional)

No API key is required for core agentic orchestration, course generation, adaptive tutoring, coding labs, document/repository ingestion, assessment, or local OS/text-only audio fallback.

To enable optional cloud TTS via ElevenLabs:
```powershell
Copy-Item .env.example .env
# Edit .env and set ELEVENLABS_API_KEY=your_key_here
```

---

## 4. Verify Installation

Run the automated 74-test verification suite:
```powershell
python -m unittest discover -s tests -v
```
