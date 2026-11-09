"""Render a two-host lesson script to one MP3.

Script format, one turn per line:
    A: So here's the thing about pricing...
    B: Right, and that's where most people...

Engine:
- ElevenLabs Text-to-Dialogue when ELEVENLABS_API_KEY is set. One call per
  batch, not isolated lines glued with silence (isolated lines sound robotic).
  Defaults: voices Liam + Jessica (energetic; calm voices read as flat),
  stability 0.3, model eleven_v3. Override with CLAUDEMY_VOICE_A,
  CLAUDEMY_VOICE_B, CLAUDEMY_STABILITY.
- macOS `say` otherwise on macOS (free, offline, plainer). Voices CLAUDEMY_SAY_A /
  CLAUDEMY_SAY_B, default Samantha and Daniel.
- Windows SAPI (`System.Speech`) otherwise on Windows (free, offline, plainer).
  Voices CLAUDEMY_SAY_A / CLAUDEMY_SAY_B, default Microsoft Zira Desktop and
  Microsoft David Desktop.
  Audio tags like [laughs] are dropped on offline engines, since they would read them aloud.
All paths finish with the same warm EQ and loudness pass in ffmpeg.

Usage: python3 render_audio.py <script.txt> <out.mp3>
"""
import json, os, re, shutil, subprocess, sys, tempfile, urllib.error, urllib.request
from pathlib import Path

POLISH_AF = (
    "highpass=f=90,equalizer=f=200:t=q:w=1:g=-2,equalizer=f=3000:t=q:w=1:g=2.5,"
    "deesser,lowpass=f=13500,acompressor=ratio=2.5,aecho=0.8:0.5:40:0.08,loudnorm=I=-16"
)
BATCH_CHARS = 3000


def load_dotenv(script_path):
    """Load ELEVENLABS_API_KEY and CLAUDEMY_* from .env if not already in os.environ."""
    candidates = [os.environ.get("CLAUDEMY_ENV_FILE"), Path.cwd() / ".env"]
    for parent in Path(script_path).resolve().parents[:4]:
        candidates.append(parent / ".env")
    for c in candidates:
        if not c or not Path(c).is_file():
            continue
        for line in Path(c).read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            line = line.removeprefix("export ").strip()
            k, sep, v = line.partition("=")
            if sep and (k.strip() == "ELEVENLABS_API_KEY" or k.strip().startswith("CLAUDEMY_")):
                val = v.strip().strip("'\"")
                if val:
                    os.environ.setdefault(k.strip(), val)


def parse_turns(text):
    turns = []
    for line in text.splitlines():
        speaker, sep, said = line.partition(":")
        if sep and speaker.strip() in ("A", "B") and said.strip():
            turns.append((speaker.strip(), said.strip()))
    if not turns:
        raise ValueError("no 'A:' or 'B:' lines found in the script")
    return turns


def batches(turns):
    batch, size = [], 0
    for t in turns:
        if batch and size + len(t[1]) > BATCH_CHARS:
            yield batch
            batch, size = [], 0
        batch.append(t)
        size += len(t[1])
    yield batch


def elevenlabs_parts(turns, tmp, key):
    voices = {"A": os.environ.get("CLAUDEMY_VOICE_A", "TX3LPaxmHKxFdv7VOQHJ"),
              "B": os.environ.get("CLAUDEMY_VOICE_B", "cgSgspJ2msm6clMCkdW9")}
    stability = float(os.environ.get("CLAUDEMY_STABILITY", "0.3"))
    parts = []
    for i, batch in enumerate(batches(turns)):
        body = {"inputs": [{"text": said, "voice_id": voices[who]} for who, said in batch],
                "model_id": "eleven_v3", "settings": {"stability": stability}, "seed": 42}
        req = urllib.request.Request(
            "https://api.elevenlabs.io/v1/text-to-dialogue", data=json.dumps(body).encode(),
            headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"})
        part = tmp / f"part{i}.mp3"
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                part.write_bytes(r.read())
        except urllib.error.HTTPError as e:
            # "HTTP Error 401" alone hides the cause (bad key, quota, unknown voice id);
            # the API says which in the response body. The key is never printed.
            detail = e.read().decode("utf-8", "replace").strip()[:300]
            sys.exit(f"ElevenLabs refused batch {i + 1}: HTTP {e.code} {e.reason}. {detail}")
        parts.append(part)
    return parts


def say_parts(turns, tmp):
    voices = {"A": os.environ.get("CLAUDEMY_SAY_A", "Samantha"),
              "B": os.environ.get("CLAUDEMY_SAY_B", "Daniel")}
    parts = []
    for i, (who, said) in enumerate(turns):
        part = tmp / f"turn{i:03d}.aiff"
        subprocess.run(["say", "-v", voices[who], "-o", str(part), re.sub(r"\[[^\]]+\]", "", said)], check=True)
        parts.append(part)
    return parts


def sapi_parts(turns, tmp):
    voices = {"A": os.environ.get("CLAUDEMY_SAY_A", "Microsoft Zira Desktop"),
              "B": os.environ.get("CLAUDEMY_SAY_B", "Microsoft David Desktop")}
    items, parts = [], []
    for i, (who, said) in enumerate(turns):
        clean = re.sub(r"\[[^\]]+\]", "", said).strip()
        if not clean:
            continue
        part = tmp / f"turn{i:03d}.wav"
        items.append({"who": who, "voice": voices[who], "out": str(part), "text": clean})
        parts.append(part)
    turns_file = tmp / "turns.json"
    turns_file.write_text(json.dumps(items), encoding="utf-8")
    ps_cmd = (
        "Add-Type -AssemblyName System.Speech; "
        "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$installed = @($synth.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name }); "
        "$items = Get-Content -LiteralPath $env:CLAUDEMY_TURNS_JSON -Raw -Encoding UTF8 | ConvertFrom-Json; "
        "foreach ($it in @($items)) { "
        "  if ($installed -contains $it.voice) { $synth.SelectVoice($it.voice) } "
        "  elseif ($it.who -eq 'A') { $synth.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::Female) } "
        "  else { $synth.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::Male) } "
        "  $synth.SetOutputToWaveFile($it.out); "
        "  $synth.Speak($it.text); "
        "} "
        "$synth.SetOutputToNull(); $synth.Dispose()"
    )
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                   env={**os.environ, "CLAUDEMY_TURNS_JSON": str(turns_file)}, check=True)
    return parts


def stitch(parts, tmp, out_path):
    listing = tmp / "list.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-af", POLISH_AF, "-ar", "44100", "-b:a", "128k", str(out_path)], check=True)


def main(script_path, out_path):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    if not shutil.which("ffmpeg"):
        sys.exit("missing dependency: ffmpeg (install via winget install Gyan.FFmpeg or brew install ffmpeg)")
    load_dotenv(script_path)
    turns = parse_turns(Path(script_path).read_text(encoding="utf-8"))
    key = os.environ.get("ELEVENLABS_API_KEY")
    has_say = bool(shutil.which("say"))
    has_sapi = sys.platform == "win32" and bool(shutil.which("powershell"))
    if not key and not has_say and not has_sapi:
        sys.exit("no audio engine: set ELEVENLABS_API_KEY (or in .env), or run on macOS/Windows for the built-in voices")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        if key:
            parts, engine = elevenlabs_parts(turns, tmp, key), "ElevenLabs"
        elif has_say:
            parts, engine = say_parts(turns, tmp), "macOS say"
        else:
            parts, engine = sapi_parts(turns, tmp), "Windows SAPI"
        stitch(parts, tmp, out_path)
    length = stamp_card(Path(script_path).with_name("card.md"), out_path)
    print(f"wrote {out_path} ({length}) from {len(turns)} turns via {engine}")


def stamp_card(card, mp3):
    """Write the real running time onto the card's Listen line. A hand-typed
    "(2 min)" sat on a 2:32 lesson in the first full test run."""
    secs = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 str(mp3)], capture_output=True, text=True, check=True).stdout.strip())
    length = f"{int(secs // 60)}:{int(secs % 60):02d}"
    if card.exists():
        text = card.read_text(encoding="utf-8")
        card.write_text(re.sub(r"^(\*\*Listen:\*\*.*?)[ \t]*\([^)]*\)[ \t]*$", rf"\1 ({length})", text, count=1, flags=re.M),
                        encoding="utf-8")
    return length


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
