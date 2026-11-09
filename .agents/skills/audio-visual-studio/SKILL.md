---
name: audio-visual-studio
description: >-
  Audio & Podcast Studio (single-narrator, two-host dialogue, expert interview, chapter audio,
  synchronized transcripts, ElevenLabs + macOS/Windows TTS + text-only fallback) and Visual Learning
  Studio (Mermaid flowcharts, sequence diagrams, ER diagrams, state diagrams, and algorithm step
  traces). Use when rendering audio lessons or visual diagrams for a course.
---

# Audio-Visual Studio — Multimodal Learning Engine

Implements Feature Set J (Audio and Podcast Studio) and Feature Set K (Visual Learning Studio).

## Audio & Podcast Studio
Run [render_studio.py](./scripts/render_studio.py) or `learning_engine.audio.studio.render_lesson_audio_package`:
- Supports 4 formats: `single_narrator`, `two_host_dialogue`, `expert_interview`, `chapter_narration`.
- Always generates `script.txt`, `transcript.json` (synchronized turn timestamps), and `chapters.json`.
- Provider chain:
  1. **ElevenLabs** (`ELEVENLABS_API_KEY` set in env or `.env`). Disclose external transmission to `api.elevenlabs.io`.
  2. **Local OS Voices** (`say` on macOS, `System.Speech` on Windows) — 100% local and free.
  3. **Text-Only Fallback** — When no TTS engine is requested/available, returns `status: "text_only_fallback"` without fabricating fake audio files or false success messages.

## Visual Learning Studio
Use `learning_engine.visualization.studio` to produce validated Mermaid diagrams only when visuals genuinely clarify understanding:
- `flowchart TD` / `flowchart LR` for concept maps and architectures
- `sequenceDiagram` for network/API protocols (e.g., TCP 3-way handshake, OAuth flow)
- `erDiagram` for relational database schemas
- `stateDiagram-v2` for process/protocol state machines
- Step-by-step algorithm state trace tables (`generate_algorithm_step_trace`)
