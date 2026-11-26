#!/usr/bin/env python3
"""Free offline subtitles with faster-whisper (no API, no account).

  subtitles.py video.mp4                      -> video.srt (language auto-detected)
  subtitles.py video.mp4 --language ar        -> force Arabic
  subtitles.py video.mp4 --model large-v3-turbo   (better Arabic, slower)
  subtitles.py video.mp4 --words              -> also video.words.json (word timings)

Models download once from Hugging Face into ~/.cache/huggingface.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_XET", "1")  # plain HTTPS download works behind the proxy

import numpy as np

MODELS = {
    "small": "small",
    "medium": "medium",
    "large-v3-turbo": "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
}


def load_audio(path, rate=16000):
    """Decode any audio/video with ffmpeg into 16 kHz mono float32."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(rate),
                          "-f", "f32le", "-"], check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--language", help="en, ar, ... (default: auto-detect)")
    ap.add_argument("--model", default="small", help="small | medium | large-v3-turbo | a local path")
    ap.add_argument("--words", action="store_true", help="also write word-level timings JSON")
    ap.add_argument("--prompt", help="hint words (names, terms), e.g. 'Fahimo, Sahla English'")
    ap.add_argument("-o", "--output", help="SRT path (default: next to the input)")
    a = ap.parse_args()

    from faster_whisper import WhisperModel
    model = WhisperModel(MODELS.get(a.model, a.model), device="cpu", compute_type="int8")
    audio = load_audio(a.input)
    segs, info = model.transcribe(audio, language=a.language, word_timestamps=a.words,
                                  vad_filter=True, initial_prompt=a.prompt)
    segs = list(segs)

    out = Path(a.output) if a.output else Path(a.input).with_suffix(".srt")
    out.write_text("".join(f"{i}\n{srt_time(s.start)} --> {srt_time(s.end)}\n{s.text.strip()}\n\n"
                           for i, s in enumerate(segs, 1)), encoding="utf-8")
    if a.words:
        words = [{"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
                 for s in segs for w in (s.words or [])]
        out.with_suffix(".words.json").write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Done: {out} ({len(segs)} lines, language {info.language} p={info.language_probability:.2f})")


if __name__ == "__main__":
    sys.exit(main())
