"""Voice the demo with ElevenLabs and lay the narration onto the video.

  XI_API_KEY=... python demo/voiceover.py <out-dir> [voice_id]
  XI_API_KEY=... python demo/voiceover.py <out-dir> [voice_id] --clips-only   # just the clips + their lengths

Reads <out-dir>/timeline.json and lens-demo.mp4 (from record_demo.js + build_outputs.py) and writes
  voice/scene-XX.mp3         one clip per scene
  lens-demo-voiceover.mp3    the narration track on its own, timed to the video
  lens-demo-voiced.mp4       the video with the narration

The key is read from the environment and never written anywhere.
"""
import json, os, re, subprocess, sys
from pathlib import Path

import requests

CLIPS_ONLY = "--clips-only" in sys.argv
args = [a for a in sys.argv[1:] if a != "--clips-only"]
OUT = Path(args[0] if args else "out")
VOICE = args[1] if len(args) > 1 else "NvA7c85NkZVpFBAHHQQ3"
KEY = os.environ.get("XI_API_KEY") or sys.exit("Set XI_API_KEY")
MODEL = os.environ.get("XI_MODEL", "eleven_multilingual_v2")
# Natural, expressive delivery: lower stability lets intonation vary like a person reading, a little
# style exaggeration adds warmth, speaker boost keeps the voice close to the original.
SETTINGS = {"stability": 0.38, "similarity_boost": 0.8, "style": 0.32, "use_speaker_boost": True, "speed": 1.0}
LEAD_IN, GAP, MAX_TEMPO = 0.3, 0.25, 1.10

tl = json.loads((OUT / "timeline.json").read_text())
facts, scenes = tl["facts"], tl["scenes"]
lead = max(0.0, scenes[0]["start"] - 0.6)
video_len = scenes[-1]["end"] + 0.8 - lead
fill = lambda t: re.sub(r"\{(\w+)\}", lambda m: str(facts.get(m.group(1), m.group(0))), t)
texts = [fill(s["narration"]) for s in scenes]


def duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                                capture_output=True, text=True, check=True).stdout)


voice_dir = OUT / "voice"; voice_dir.mkdir(exist_ok=True)
clips = []
for i, (sc, text) in enumerate(zip(scenes, texts)):
    path = voice_dir / f"scene-{i + 1:02d}.mp3"
    if not path.exists():
        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}?output_format=mp3_44100_192",
            headers={"xi-api-key": KEY, "accept": "audio/mpeg"},
            json={"text": text, "model_id": MODEL, "voice_settings": SETTINGS,
                  "previous_text": " ".join(texts[max(0, i - 2):i]) or None,
                  "next_text": texts[i + 1] if i + 1 < len(texts) else None},
            timeout=120)
        if r.status_code >= 400:
            sys.exit(f"ElevenLabs HTTP {r.status_code}: {r.text[:300]}")
        path.write_bytes(r.content)
    start = sc["start"] - lead + LEAD_IN
    slot = (scenes[i + 1]["start"] - lead if i + 1 < len(scenes) else video_len) - start - GAP
    d = duration(path); tempo = 1.0
    if d > slot:
        tempo = min(MAX_TEMPO, d / slot)
    clips.append((path, start, d, slot, tempo))
    flag = "" if d / tempo <= slot + 0.05 else "  <-- still runs over; shorten this line or slow the scene"
    print(f"scene {i + 1:02d}  at {start:6.1f}s  voice {d:5.1f}s  room {slot:5.1f}s  tempo {tempo:.2f}{flag}")

(voice_dir / "durations.json").write_text(json.dumps([round(c[2], 2) for c in clips]))
if CLIPS_ONLY:
    sys.exit(f"wrote {len(clips)} clips and voice/durations.json")

# Mix: each clip delayed to its scene, tempo-adjusted only if needed, then loudness-normalised.
inputs, filters = [], []
for n, (path, start, d, slot, tempo) in enumerate(clips):
    inputs += ["-i", str(path)]
    chain = f"[{n}:a]" + (f"atempo={tempo:.3f}," if tempo > 1.0 else "") + f"adelay={int(start * 1000)}:all=1[a{n}]"
    filters.append(chain)
mix = "".join(f"[a{n}]" for n in range(len(clips)))
filters.append(f"{mix}amix=inputs={len(clips)}:normalize=0,apad,atrim=0:{video_len:.2f},loudnorm=I=-16:TP=-1.5:LRA=11[voice]")
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[voice]",
                "-c:a", "libmp3lame", "-b:a", "192k", str(OUT / "lens-demo-voiceover.mp3")], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / "lens-demo.mp4"), "-i", str(OUT / "lens-demo-voiceover.mp3"),
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                str(OUT / "lens-demo-voiced.mp4")], check=True)
print("wrote lens-demo-voiceover.mp3 and lens-demo-voiced.mp4")
