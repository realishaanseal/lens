"""Turn a recording + timeline.json into the deliverables:

  lens-demo.mp4               clean 1080p video for the voice-over
  lens-demo-captioned.mp4     the same with the narration burned in, to rehearse against
  lens-demo.srt               narration as subtitles, timed to the video
  lens-demo-script.md         voice-over script: timestamps, what's on screen, what to say

Usage: python build_outputs.py <out-dir-with-timeline.json>
"""
import json, re, subprocess, sys
from pathlib import Path

out = Path(sys.argv[1] if len(sys.argv) > 1 else "out")
tl = json.loads((out / "timeline.json").read_text())
facts, scenes = tl["facts"], tl["scenes"]
LEAD = max(0.0, scenes[0]["start"] - 0.6)          # trim the blank page before the first scene
END = scenes[-1]["end"] + 0.8 - LEAD


def fill(text):
    return re.sub(r"\{(\w+)\}", lambda m: str(facts.get(m.group(1), m.group(0))), text)


def ts(t, srt=False):
    t = max(0.0, t); h, rem = divmod(t, 3600); m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", ",") if srt else f"{int(m)}:{s:04.1f}"


# Captions: split each scene's narration into chunks of about 9 words, spread across the time a
# narrator needs to read them (2.5 words/s) from the scene's start.
cues = []
for sc in scenes:
    sc["start_v"], sc["end_v"] = sc["start"] - LEAD, sc["end"] - LEAD
    words = fill(sc["narration"]).split(); chunks, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 9 and (w.endswith((",", ".", ":", "?")) or len(cur) >= 12):
            chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    t = sc["start_v"] + 0.2
    for c in chunks:
        dur = len(c) / 2.5
        cues.append((t, min(t + dur, sc["end_v"] - 0.05), " ".join(c))); t += dur

srt = "\n".join(f"{i}\n{ts(a, True)} --> {ts(b, True)}\n{text}\n" for i, (a, b, text) in enumerate(cues, 1))
(out / "lens-demo.srt").write_text(srt)

lines = ["# Lens demo: voice-over script", "",
         f"Video: `lens-demo.mp4` ({ts(END)} long, 1920×1080). Each line starts at the time shown; "
         "read at a relaxed pace (about 150 words a minute) and every line fits its scene with room to breathe. "
         "`lens-demo.srt` has the same text as subtitles, and `lens-demo-captioned.mp4` shows it on screen for rehearsal.", "",
         "| # | Time | On screen | Narration |", "|---|---|---|---|"]
for i, sc in enumerate(scenes, 1):
    lines.append(f"| {i} | {ts(sc['start_v'])}–{ts(sc['end_v'])} | {sc['onScreen']} | {fill(sc['narration'])} |")
lines += ["", "## Narration only", ""]
for sc in scenes:
    lines.append(f"**[{ts(sc['start_v'])}] {sc['title']}**  \n{fill(sc['narration'])}\n")
(out / "lens-demo-script.md").write_text("\n".join(lines))

src = tl["video"]
base = ["ffmpeg", "-v", "error", "-y", "-ss", f"{LEAD:.2f}", "-i", src, "-t", f"{END:.2f}"]
scale = "scale=1920:1080:flags=lanczos,fps=30"
enc = ["-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an"]
subprocess.run(base + ["-vf", scale] + enc + [str(out / "lens-demo.mp4")], check=True)
style = "FontName=DejaVu Sans,FontSize=13,PrimaryColour=&H00FFFFFF,BackColour=&H99000000,BorderStyle=4,Outline=0,Shadow=0,MarginV=26"
sub = str(out / "lens-demo.srt").replace(":", r"\:")
subprocess.run(base + ["-vf", f"{scale},subtitles='{sub}':force_style='{style}'"] + enc + [str(out / "lens-demo-captioned.mp4")], check=True)
print(f"trimmed {LEAD:.1f}s; {ts(END)} long; {len(cues)} captions")
