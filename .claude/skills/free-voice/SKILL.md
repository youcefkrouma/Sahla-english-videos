---
name: free-voice
description: Free offline voice-over and subtitles for Sahla English videos. Kokoro voices for English, Piper for Arabic (automatic tashkeel), faster-whisper for SRT subtitles. No API key, no account, no cost. Use whenever the user wants narration, Fahimo's voice, a voice-over, TTS, pronunciation audio, a transcript, captions or an SRT file.
---

# Free voice and subtitles

Everything runs locally on CPU and is free. Models are open source
(Kokoro-82M Apache-2.0, Piper voices, Whisper MIT).

## First use in a session

If `~/.sahla-venv/bin/python` or `~/.cache/sahla/models` is missing, run once from the repo root:

```bash
bash tools/setup_free.sh      # ~30 s, downloads ~400 MB of models
```

`PY=~/.sahla-venv/bin/python` below.

## Voice-over

One line:

```bash
$PY .claude/skills/free-voice/scripts/tts.py --lang en --text "Good morning!" -o out/hello.wav
$PY .claude/skills/free-voice/scripts/tts.py --lang ar --text "صباح الخير يا أصدقاء" -o out/ar.wav
```

A whole lesson in one go: write a script file, get `lesson.wav` + `lesson.srt` + `lesson.json`
(exact start/end of every line, ready for captions and for timing pictures).

```text
ar: مرحبا يا أصدقاء! اليوم نتعلم كيف نقول صباح الخير.
en: Good morning!
pause: 1.2
en[af_heart,0.75]: Good morning!
ar: ردد معي.
pause: 2
en[am_puck]: Good morning, Fahimo!
```

```bash
$PY .claude/skills/free-voice/scripts/tts.py --script lesson.txt -o out/lesson.wav
```

- `en[voice,speed]:` overrides voice/speed for that line. Default English speed is 0.9 (clear for learners).
- `pause: N` leaves N seconds of silence, for "repeat after me" moments.
- `--list-voices` shows voices. Good picks: `af_heart` (warm female), `af_bella`, `am_puck` (playful male),
  `am_michael`, `bf_emma` / `bm_george` (British).
- Arabic is one male voice (`ar_JO-kareem`, Modern Standard Arabic). It does not speak Darija;
  write Arabic lines in simple MSA. Piper adds tashkeel automatically; add your own harakat to fix a
  mispronounced word.
- Generation is fast (about 4 s for a 17 s lesson).

## Subtitles from any video or audio

```bash
$PY .claude/skills/free-voice/scripts/subtitles.py week2/15-weather.mp4               # auto language
$PY .claude/skills/free-voice/scripts/subtitles.py clip.mp4 --language ar --prompt "فهيمو, Fahimo"
$PY .claude/skills/free-voice/scripts/subtitles.py clip.mp4 --model large-v3-turbo --words
```

- `small` (default) transcribed a 94 s mixed Arabic/English video in ~24 s with good accuracy.
- `large-v3-turbo` is better for Arabic but slower and downloads ~1.6 GB the first time.
- Always proofread Arabic lines before burning them in. Fix the SRT text, keep the times.

## Then

Burn captions, mix the voice with music/SFX and export with the `ffmpeg-skill`
(`caption.py --srt`, `audio.py --replace/--music --duck`, `render.py --template tiktok`).
For Arabic captions use the repo fonts (`Tajawal`, `Lalezar`, `Baloo Bhaijaan 2`), installed by the setup script.
