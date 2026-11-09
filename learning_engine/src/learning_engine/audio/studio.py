"""Audio and Podcast Studio Subsystem (Feature Set J).

Supports:
- Single-speaker narration (single_narrator)
- Two-speaker educational discussions (two_host_dialogue)
- Interview-style explanations (expert_interview)
- Chapter-based audio with timestamps & chapter metadata JSON (chapter_narration)
- Synchronized lesson transcripts
- Modular TTS provider adapters:
  1. ElevenLabs (`ELEVENLABS_API_KEY`)
  2. macOS `say`
  3. Windows SAPI (`System.Speech`)
  4. Text-Only Transcript Fallback (never fabricates fake MP3 files or false audio success messages!)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import Any

from ..core.safety import redact_secrets

PRIVACY_DISCLOSURE = (
    "Audio Privacy Notice: When `ELEVENLABS_API_KEY` is configured and external TTS is enabled, lesson dialogue text "
    "is transmitted to ElevenLabs (`api.elevenlabs.io`) for audio synthesis. Local OS voices (`say` / Windows SAPI) "
    "and Text-Only fallback process 100% locally on your machine."
)


class AudioFormat(str, Enum):
    SINGLE_NARRATOR = "single_narrator"
    TWO_HOST_DIALOGUE = "two_host_dialogue"
    EXPERT_INTERVIEW = "expert_interview"
    CHAPTER_NARRATION = "chapter_narration"


def format_script_and_chapters(
    title: str,
    turns: list[tuple[str, str]],
    audio_format: str = AudioFormat.TWO_HOST_DIALOGUE.value,
) -> dict[str, Any]:
    """Generate a formatted script, synchronized transcript with estimated timestamps, and chapter markers."""
    script_lines: list[str] = []
    transcript_entries: list[dict[str, Any]] = []
    chapters: list[dict[str, Any]] = []
    elapsed_sec = 0.0

    for idx, (speaker, text) in enumerate(turns, start=1):
        speaker_label = "A" if audio_format == AudioFormat.SINGLE_NARRATOR.value else speaker
        script_lines.append(f"{speaker_label}: {text}")
        words = len(text.split())
        duration_est = round(max(1.5, words / 2.5), 1)
        start_sec = round(elapsed_sec, 1)
        end_sec = round(elapsed_sec + duration_est, 1)
        transcript_entries.append(
            {
                "turn": idx,
                "speaker": speaker_label,
                "start_sec": start_sec,
                "end_sec": end_sec,
                "text": text,
            }
        )
        if idx == 1 or idx % 4 == 0:
            chapters.append(
                {
                    "chapter": len(chapters) + 1,
                    "title": f"Part {len(chapters) + 1}: {text[:48].rstrip('.,?!')}...",
                    "start_sec": start_sec,
                }
            )
        elapsed_sec = end_sec

    return {
        "title": title,
        "format": audio_format,
        "script_text": "\n".join(script_lines) + "\n",
        "estimated_duration_sec": round(elapsed_sec, 1),
        "chapters": chapters,
        "transcript": transcript_entries,
    }


def render_lesson_audio_package(
    out_dir: str | Path,
    title: str,
    turns: list[tuple[str, str]],
    audio_format: str = AudioFormat.TWO_HOST_DIALOGUE.value,
    provider_preference: str = "auto",  # "auto" | "elevenlabs" | "local_os" | "text_only"
) -> dict[str, Any]:
    """Render synchronized transcript, chapter metadata, and optional MP3 audio with honest fallback."""
    target = Path(out_dir).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)

    pkg = format_script_and_chapters(title, turns, audio_format=audio_format)
    script_path = target / "script.txt"
    transcript_path = target / "transcript.json"
    chapters_path = target / "chapters.json"
    mp3_path = target / "lesson.mp3"

    script_path.write_text(pkg["script_text"], encoding="utf-8")
    transcript_path.write_text(json.dumps(pkg["transcript"], indent=2, ensure_ascii=False), encoding="utf-8")
    chapters_path.write_text(json.dumps(pkg["chapters"], indent=2, ensure_ascii=False), encoding="utf-8")

    # Determine provider availability honestly (Test 11: Audio Failure / No API key)
    has_key = bool(os.environ.get("ELEVENLABS_API_KEY", "").strip())
    has_ffmpeg = bool(shutil.which("ffmpeg"))
    has_local_tts = bool(shutil.which("say")) or (sys.platform == "win32" and bool(shutil.which("powershell")))

    if provider_preference == "text_only":
        return {
            "status": "text_only_fallback",
            "audio_generated": False,
            "provider_used": "text_only",
            "message": "Text-only mode selected. Synchronized transcript and chapter metadata written; no MP3 generated.",
            "script_path": str(script_path),
            "transcript_path": str(transcript_path),
            "chapters_path": str(chapters_path),
            "mp3_path": None,
            "privacy_notice": PRIVACY_DISCLOSURE,
        }

    if provider_preference == "elevenlabs" and not has_key:
        return {
            "status": "text_only_fallback",
            "audio_generated": False,
            "provider_used": "text_only",
            "message": "ELEVENLABS_API_KEY is not set. Falling back cleanly to text transcript and chapters without creating fake audio.",
            "script_path": str(script_path),
            "transcript_path": str(transcript_path),
            "chapters_path": str(chapters_path),
            "mp3_path": None,
            "privacy_notice": PRIVACY_DISCLOSURE,
        }

    if not has_ffmpeg or (not has_key and not has_local_tts):
        return {
            "status": "text_only_fallback",
            "audio_generated": False,
            "provider_used": "text_only",
            "message": "Audio engine or ffmpeg unavailable; text learning, transcript, and chapters remain 100% functional.",
            "script_path": str(script_path),
            "transcript_path": str(transcript_path),
            "chapters_path": str(chapters_path),
            "mp3_path": None,
            "privacy_notice": PRIVACY_DISCLOSURE,
        }

    # Invoke the verified render_audio.py script
    renderer = Path(__file__).resolve().parents[4] / ".agents" / "skills" / "claudemy" / "scripts" / "render_audio.py"
    if not renderer.exists():
        renderer = Path(__file__).resolve().parents[4] / "skills" / "claudemy" / "scripts" / "render_audio.py"

    env = dict(os.environ)
    if provider_preference == "local_os":
        env.pop("ELEVENLABS_API_KEY", None)

    proc = subprocess.run(
        [sys.executable, str(renderer), str(script_path), str(mp3_path)],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0 or not mp3_path.exists():
        safe_err = redact_secrets((proc.stderr or proc.stdout).strip())
        return {
            "status": "text_only_fallback",
            "audio_generated": False,
            "provider_used": "text_only",
            "message": f"Audio rendering failed ({safe_err}); text learning and synchronized transcript remain available.",
            "script_path": str(script_path),
            "transcript_path": str(transcript_path),
            "chapters_path": str(chapters_path),
            "mp3_path": None,
            "privacy_notice": PRIVACY_DISCLOSURE,
        }

    return {
        "status": "audio_rendered",
        "audio_generated": True,
        "provider_used": "elevenlabs" if (has_key and provider_preference != "local_os") else "local_os",
        "message": redact_secrets(proc.stdout.strip()),
        "script_path": str(script_path),
        "transcript_path": str(transcript_path),
        "chapters_path": str(chapters_path),
        "mp3_path": str(mp3_path),
        "privacy_notice": PRIVACY_DISCLOSURE,
    }
