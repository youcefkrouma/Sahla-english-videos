#!/usr/bin/env python3
"""Free sound effects and simple background music, synthesized locally.

Everything is generated from math (no samples, no API), so it is free to use
anywhere, commercially too.

  sfx.py ding -o ding.wav
  sfx.py correct wrong pop whoosh -d sfx/        (several at once)
  sfx.py music --seconds 60 --bpm 100 -o bed.wav (cheerful loop for under the voice)
  sfx.py --list
"""
import argparse
import sys
import wave
from pathlib import Path

import numpy as np

SR = 44100
rng = np.random.default_rng(7)


def t_axis(sec):
    return np.arange(int(sec * SR)) / SR


def env(n, attack=0.005, decay=None, sec=None):
    """Fast attack, exponential decay envelope."""
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    d = np.exp(-t / decay) if decay else np.ones(n)
    return a * d


def sine(freq, sec, phase=0.0):
    t = t_axis(sec)
    if np.ndim(freq):
        return np.sin(2 * np.pi * np.cumsum(freq) / SR + phase)
    return np.sin(2 * np.pi * freq * t + phase)


def bell(freq, sec=1.2, decay=0.35):
    t = t_axis(sec)
    x = (np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t / (decay / 2))
         + 0.25 * np.sin(2 * np.pi * freq * 5.4 * t) * np.exp(-t / (decay / 4)))
    return x * env(len(t), 0.002, decay)


def pluck(freq, sec=0.8, bright=0.5):
    """Karplus-Strong plucked string (ukulele / guitar-like)."""
    n, period = int(sec * SR), max(2, int(SR / freq))
    buf = rng.uniform(-1, 1, period)
    out = np.empty(n)
    for i in range(n):
        out[i] = buf[i % period]
        nxt = buf[(i + 1) % period]
        buf[i % period] = 0.996 * (bright * out[i] + (1 - bright) * 0.5 * (out[i] + nxt))
    return out * env(n, 0.001, sec / 2.5)


def lowpass(x, cutoff):
    """One-pole low-pass; cutoff may be an array (sweep)."""
    cutoff = np.broadcast_to(np.asarray(cutoff, dtype=float), x.shape)
    a = 1 - np.exp(-2 * np.pi * cutoff / SR)
    y, acc = np.empty_like(x), 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def place(dst, src, at):
    i = int(at * SR)
    end = min(len(dst), i + len(src))
    dst[i:end] += src[: end - i]
    return dst


def note(name):
    names = {"C": -9, "D": -7, "E": -5, "F": -4, "G": -2, "A": 0, "B": 2}
    semis = names[name[0]] + (1 if "#" in name else 0) + 12 * (int(name[-1]) - 4)
    return 440.0 * 2 ** (semis / 12)


# ---------------------------------------------------------------- presets
def ding():
    return bell(note("E6"), 1.4, 0.45) + 0.6 * bell(note("B6"), 1.4, 0.35)


def correct():
    out = np.zeros(int(1.3 * SR))
    for k, n in enumerate(["C6", "E6", "G6", "C7"]):
        place(out, bell(note(n), 0.9, 0.3) * (0.8 + 0.1 * k), k * 0.09)
    return out


def wrong():
    t = t_axis(0.55)
    f = np.linspace(180, 120, len(t))
    sq = np.sign(sine(f, 0.55)) * 0.5 + 0.5 * sine(f / 2, 0.55)
    return lowpass(sq, 1800) * env(len(t), 0.01, 0.35)


def pop():
    t = t_axis(0.12)
    f = 700 * np.exp(-t / 0.025) + 160
    return sine(f, 0.12) * env(len(t), 0.001, 0.04)


def whoosh():
    sec = 0.7
    t = t_axis(sec)
    shape = np.sin(np.pi * t / sec) ** 2
    noise = rng.normal(0, 1, len(t))
    return lowpass(noise, 300 + 5000 * shape) * shape


def sparkle():
    out = np.zeros(int(1.2 * SR))
    for k in range(9):
        f = note("C7") * 2 ** (rng.integers(-5, 8) / 12)
        place(out, bell(f, 0.5, 0.12) * (1 - k / 12), k * 0.07 + rng.uniform(0, 0.03))
    return out


def tick():
    n = int(0.05 * SR)
    return lowpass(rng.normal(0, 1, n), 6000) * env(n, 0.0005, 0.006) + 0.5 * sine(2000, 0.05) * env(n, 0.0005, 0.01)


def clap(at_once=1):
    n = int(0.25 * SR)
    burst = np.zeros(n)
    for k in range(3):
        place(burst, rng.normal(0, 1, int(0.02 * SR)) * env(int(0.02 * SR), 0.0005, 0.006), k * 0.011)
    tail = rng.normal(0, 1, n) * env(n, 0.001, 0.05) * 0.4
    return lowpass(burst + tail, 3500)


def applause():
    out = np.zeros(int(2.6 * SR))
    for _ in range(140):
        place(out, clap() * rng.uniform(0.3, 1.0), rng.uniform(0, 2.2))
    fade = np.ones(len(out))
    fade[-int(0.6 * SR):] = np.linspace(1, 0, int(0.6 * SR))
    return out * fade


def drumroll():
    out = np.zeros(int(2.2 * SR))
    t, gap = 0.0, 0.09
    while t < 1.6:
        n = int(0.06 * SR)
        hit = lowpass(rng.normal(0, 1, n), 4000) * env(n, 0.001, 0.02) * (0.4 + 0.6 * t / 1.6)
        place(out, hit, t)
        t += gap
        gap = max(0.035, gap * 0.97)
    n = int(0.6 * SR)
    crash = lowpass(rng.normal(0, 1, n), 7000) * env(n, 0.001, 0.2) + 0.8 * sine(90, 0.6) * env(n, 0.001, 0.12)
    return place(out, crash, 1.62)


def jingle():
    out = np.zeros(int(2.0 * SR))
    melody = [("C5", 0.0), ("E5", 0.15), ("G5", 0.3), ("C6", 0.45), ("G5", 0.75), ("C6", 0.9)]
    for n, at in melody:
        place(out, pluck(note(n), 0.9, 0.6), at)
    for n in ["C4", "E4", "G4"]:
        place(out, pluck(note(n), 1.1, 0.4) * 0.6, 0.9)
    return out


def music(seconds=30.0, bpm=100):
    """Cheerful I-V-vi-IV loop: plucked arpeggios + soft bass. Ends on a clean bar."""
    beat = 60.0 / bpm
    bar = 4 * beat
    chords = [("C4", "E4", "G4", "C3"), ("G3", "B3", "D4", "G2"), ("A3", "C4", "E4", "A2"), ("F3", "A3", "C4", "F2")]
    bars = max(1, int(round(seconds / bar)))
    out = np.zeros(int((bars * bar + 1.5) * SR))
    for b in range(bars):
        c = chords[b % 4]
        t0 = b * bar
        for step, idx in enumerate([0, 1, 2, 1, 0, 1, 2, 1]):
            place(out, pluck(note(c[idx]) * 2, 0.6, 0.55) * 0.35, t0 + step * beat / 2)
        for k in range(2):
            place(out, pluck(note(c[3]), 1.4, 0.3) * 0.5, t0 + k * 2 * beat)
        if b % 2 == 1:
            place(out, bell(note(c[2]) * 2, 0.8, 0.25) * 0.12, t0 + 3 * beat)
    return out


PRESETS = {
    "ding": (ding, "bell ding, highlight a new word"),
    "correct": (correct, "rising chime, right answer"),
    "wrong": (wrong, "soft buzzer, wrong answer"),
    "pop": (pop, "bubble pop, text or sticker appears"),
    "whoosh": (whoosh, "swoosh, transition"),
    "sparkle": (sparkle, "magic sparkle, reveal"),
    "tick": (tick, "clock tick, quiz countdown (loop it)"),
    "clap": (clap, "one clap"),
    "applause": (applause, "kids clapping, end of quiz"),
    "drumroll": (drumroll, "drum roll + crash, before the answer"),
    "jingle": (jingle, "short channel jingle (intro/outro)"),
    "music": (music, "background loop, use --seconds and --bpm"),
}


def write_wav(path, x):
    peak = float(np.max(np.abs(x))) or 1.0
    pcm = (x / peak * 0.79 * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*", help="preset names (see --list)")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--seconds", type=float, default=30.0, help="music length")
    ap.add_argument("--bpm", type=int, default=100, help="music tempo")
    ap.add_argument("-o", "--output", help="output file (one preset)")
    ap.add_argument("-d", "--dir", default=".", help="output folder (several presets)")
    a = ap.parse_args()

    if a.list or not a.names:
        for k, (_, doc) in PRESETS.items():
            print(f"  {k:9} {doc}")
        return
    bad = [n for n in a.names if n not in PRESETS]
    if bad:
        sys.exit(f"unknown preset(s): {', '.join(bad)} (see --list)")
    Path(a.dir).mkdir(parents=True, exist_ok=True)
    for n in a.names:
        fn = PRESETS[n][0]
        x = fn(a.seconds, a.bpm) if n == "music" else fn()
        out = Path(a.output) if (a.output and len(a.names) == 1) else Path(a.dir) / f"{n}.wav"
        write_wav(out, x)
        print(f"Done: {out} ({len(x) / SR:.2f} s)")


if __name__ == "__main__":
    main()
