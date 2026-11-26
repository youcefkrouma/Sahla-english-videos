---
name: free-cover
description: Free 1080x1920 covers and thumbnails in the Sahla English style - sun-ray background, glow, stars, "Sahla English" and episode pills, an Arabic title and a yellow English phrase, with Fahimo cut out automatically. Arabic is shaped correctly and everything stays inside the TikTok/Instagram profile-grid crop. Use for any cover, thumbnail or title card.
---

# Free covers

Pillow only, no API. Needs the venv from `bash tools/setup_free.sh` (installs the fonts too).

```bash
PY=~/.sahla-venv/bin/python
$PY .claude/skills/free-cover/scripts/cover.py \
    --ar "كيف الطقس اليوم؟" --en "What's the weather like?" --num 15 \
    --theme sky --deco sun,stars -o covers/15.png
```

Options:
- `--theme` night, day, sunny, sky, grass, candy, purple (match the topic: night words → night).
- `--deco` any of stars, sun, moon, hearts, dots, or none.
- `--image` another Fahimo pose. PNG with transparency is best. A plain white background is
  removed automatically. Default: `refs/fahimo-ref.png`.
- `--bg-image` a picture instead of the rays (a kitchen for "things in my home", etc.).
- `--guides` draws red lines at the profile-grid crop (y 240 and 1680) to check placement.

Rules that keep covers readable on a phone:
- Arabic title up to about 18 characters; English phrase up to about 22. Longer text shrinks.
- The title asks or promises one thing ("تقولها في الليل؟"), and the English line is the answer.
- Look at the PNG before using it (open it with the Read tool).

Add the cover as the first frames of a video with `ffmpeg-skill` (`insert.py cover.png --duration 0.5`, then `join.py`).

## New Fahimo poses for free

Generating a new pose of Fahimo needs an image model, and none runs well on this CPU-only machine.
Free ways: Google AI Studio or the Gemini app on the web (free daily quota) with
`refs/fahimo-ref.png` attached as reference, then save the result in `refs/` and pass it with `--image`.
