#!/usr/bin/env python3
"""Free offline voice-over: Kokoro (English) + Piper (Arabic).

One line:
  tts.py --lang en --text "Good morning!" -o hello.wav
  tts.py --lang ar --text "صباح الخير" -o sabah.wav

A whole script (one WAV + matching SRT + timings JSON):
  tts.py --script lesson.txt -o lesson.wav

Script format, one item per line:
  en: Good morning!
  ar: صباح الخير يا أصدقاء
  pause: 1.5
  en[am_puck,0.8]: Good morning      <- voice and speed for this line only
  # comment lines and blank lines are ignored
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

MODELS = Path(os.environ.get("SAHLA_MODELS", Path.home() / ".cache/sahla/models"))
KOKORO_MODEL = MODELS / "kokoro/model.onnx"
KOKORO_VOICES = MODELS / "kokoro/voices.npz"
PIPER_AR = MODELS / "piper/ar_JO-kareem-medium.onnx"
OUT_RATE = 44100

LINE_RE = re.compile(r"^\s*(en|ar|pause)\s*(?:\[([^\]]*)\])?\s*:\s*(.*)$", re.I)


def need(path):
    if not path.exists():
        sys.exit(f"Missing {path}. Run: bash tools/setup_free.sh")


class Engines:
    def __init__(self):
        self._kokoro = None
        self._piper = None

    def kokoro(self):
        if self._kokoro is None:
            need(KOKORO_MODEL)
            need(KOKORO_VOICES)
            from kokoro_onnx import Kokoro
            self._kokoro = Kokoro(str(KOKORO_MODEL), str(KOKORO_VOICES))
        return self._kokoro

    def piper(self):
        if self._piper is None:
            need(PIPER_AR)
            from piper import PiperVoice
            self._piper = PiperVoice.load(str(PIPER_AR))
        return self._piper

    def say(self, lang, text, voice=None, speed=1.0):
        """Return (float32 mono samples, sample_rate)."""
        if lang == "en":
            voice = voice or "af_heart"
            accent = "en-gb" if voice.startswith("b") else "en-us"
            samples, rate = self.kokoro().create(text, voice=voice, speed=speed, lang=accent)
            return np.asarray(samples, dtype=np.float32), rate
        if lang == "ar":
            from piper import SynthesisConfig
            cfg = SynthesisConfig(length_scale=1.0 / max(speed, 0.1))
            chunks = list(self.piper().synthesize(text, syn_config=cfg))
            audio = np.concatenate([c.audio_float_array for c in chunks]).astype(np.float32)
            return audio, chunks[0].sample_rate
        raise ValueError(f"unknown language {lang!r} (use en or ar)")


def resample(x, src, dst):
    if src == dst or len(x) == 0:
        return x
    with tempfile.TemporaryDirectory() as d:
        a, b = Path(d, "a.f32"), Path(d, "b.f32")
        x.astype(np.float32).tofile(a)
        subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(src), "-ac", "1", "-i", str(a),
                        "-af", f"aresample={dst}:resampler=soxr", "-f", "f32le", "-ac", "1", str(b)], check=True)
        return np.fromfile(b, dtype=np.float32)


def write_wav(path, x, rate=OUT_RATE):
    peak = float(np.max(np.abs(x))) if len(x) else 0.0
    if peak > 0.98:
        x = x * (0.98 / peak)
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def parse_script(text):
    items = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = LINE_RE.match(line)
        if not m:
            sys.exit(f"line {n}: expected 'en: ...', 'ar: ...' or 'pause: N' -> {raw!r}")
        kind, opts, body = m.group(1).lower(), m.group(2), m.group(3).strip()
        if kind == "pause":
            items.append({"kind": "pause", "seconds": float(body or 1)})
            continue
        voice, speed = None, None
        for part in (opts or "").split(","):
            part = part.strip()
            if not part:
                continue
            try:
                speed = float(part)
            except ValueError:
                voice = part
        items.append({"kind": kind, "text": body, "voice": voice, "speed": speed})
    return items


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--text", help="text for a single line")
    ap.add_argument("--lang", choices=["en", "ar"], default="en")
    ap.add_argument("--script", help="script file (en:/ar:/pause: lines)")
    ap.add_argument("--en-voice", default="af_heart", help="default English voice (see --list-voices)")
    ap.add_argument("--en-speed", type=float, default=0.9, help="English speed, 0.9 suits learners")
    ap.add_argument("--ar-speed", type=float, default=1.0)
    ap.add_argument("--gap", type=float, default=0.35, help="silence between script lines, seconds")
    ap.add_argument("--list-voices", action="store_true")
    ap.add_argument("-o", "--output", default="voice.wav")
    a = ap.parse_args()

    if a.list_voices:
        need(KOKORO_VOICES)
        names = sorted(np.load(KOKORO_VOICES).files)
        print("English (Kokoro): " + ", ".join(names))
        print("  af_/am_ = American female/male, bf_/bm_ = British female/male")
        print("Arabic (Piper): ar_JO-kareem (male, automatic tashkeel)")
        return

    if a.script:
        items = parse_script(Path(a.script).read_text(encoding="utf-8"))
    elif a.text:
        items = [{"kind": a.lang, "text": a.text, "voice": None, "speed": None}]
    else:
        ap.error("give --text or --script")

    eng = Engines()
    out, t, cues = [], 0.0, []
    gap = np.zeros(int(a.gap * OUT_RATE), dtype=np.float32)
    for i, it in enumerate(items):
        if it["kind"] == "pause":
            n = int(it["seconds"] * OUT_RATE)
            out.append(np.zeros(n, dtype=np.float32))
            t += n / OUT_RATE
            continue
        if i > 0 and len(gap):
            out.append(gap)
            t += len(gap) / OUT_RATE
        default_speed = a.en_speed if it["kind"] == "en" else a.ar_speed
        voice = it["voice"] or (a.en_voice if it["kind"] == "en" else None)
        x, rate = eng.say(it["kind"], it["text"], voice, it["speed"] or default_speed)
        x = resample(x, rate, OUT_RATE)
        start, t = t, t + len(x) / OUT_RATE
        cues.append({"lang": it["kind"], "text": it["text"], "start": round(start, 3), "end": round(t, 3)})
        out.append(x)
        print(f"{start:6.2f}-{t:6.2f}  {it['kind']}: {it['text']}", file=sys.stderr)

    audio = np.concatenate(out) if out else np.zeros(1, dtype=np.float32)
    dst = Path(a.output)
    if dst.suffix.lower() == ".wav":
        write_wav(dst, audio)
    else:
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d, "v.wav")
            write_wav(tmp, audio)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), str(dst)], check=True)

    srt = dst.with_suffix(".srt")
    srt.write_text("".join(f"{k}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{c['text']}\n\n"
                           for k, c in enumerate(cues, 1)), encoding="utf-8")
    dst.with_suffix(".json").write_text(json.dumps({"duration": round(t, 3), "cues": cues},
                                                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Done: {dst} ({t:.2f} s), {srt.name}, {dst.with_suffix('.json').name}")


if __name__ == "__main__":
    main()
