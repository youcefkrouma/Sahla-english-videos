---
name: free-sfx
description: Free sound effects and background music synthesized locally (no samples, no API, royalty-free) for kids' educational shorts - ding, correct/wrong answer, pop, whoosh, sparkle, clock tick, clap, applause, drum roll, channel jingle and a cheerful music loop. Use when a video needs SFX, a quiz sound, a jingle or background music.
---

# Free SFX and music

Generated from math with numpy, so every sound is original and free to use commercially.
Needs the venv from `bash tools/setup_free.sh` (or any Python with numpy).

```bash
PY=~/.sahla-venv/bin/python
$PY .claude/skills/free-sfx/scripts/sfx.py --list
$PY .claude/skills/free-sfx/scripts/sfx.py correct wrong pop whoosh -d out/sfx
$PY .claude/skills/free-sfx/scripts/sfx.py music --seconds 60 --bpm 100 -o out/sfx/bed.wav
```

| Preset | Use it for |
|---|---|
| `ding` | a new word appears |
| `correct` / `wrong` | quiz answers |
| `pop` | text, sticker or picture pops in |
| `whoosh` | transitions between scenes |
| `sparkle` | reveal, "magic" moment |
| `tick` | countdown (loop it with ffmpeg `-stream_loop`) |
| `clap` / `applause` | well done, end of quiz |
| `drumroll` | before revealing the answer |
| `jingle` | channel intro/outro (2 s) |
| `music` | background loop under the voice |

Mixing rules for kids' shorts:
- Music under speech: about -20 dB below the voice, with ducking (`ffmpeg-skill`: `audio.py --music bed.wav --duck`).
- One effect per event; do not stack effects on every word.
- Finish with loudness at -14 LUFS (`loudness.py`), the TikTok/Reels/YouTube target.
