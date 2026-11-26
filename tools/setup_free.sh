#!/usr/bin/env bash
# Free, offline toolchain for Sahla English videos.
# Installs Python packages in a venv and downloads open models once.
# Safe to re-run: skips what is already there.
set -euo pipefail

VENV="${SAHLA_VENV:-$HOME/.sahla-venv}"
MODELS="${SAHLA_MODELS:-$HOME/.cache/sahla/models}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
HF="https://huggingface.co"

say() { printf '\n== %s\n' "$*"; }

# 1. Python packages (all free / open source)
if [ ! -x "$VENV/bin/python" ]; then
  say "Creating venv at $VENV"
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q --upgrade pip
fi
if ! "$VENV/bin/python" -c "import piper, kokoro_onnx, faster_whisper, soundfile, PIL" 2>/dev/null; then
  say "Installing piper-tts, kokoro-onnx, faster-whisper, pillow"
  "$VENV/bin/pip" install -q piper-tts kokoro-onnx faster-whisper soundfile numpy pillow
fi

fetch() { # url dest
  [ -s "$2" ] && return 0
  mkdir -p "$(dirname "$2")"
  curl -fsSL --retry 3 -o "$2.part" "$1" && mv "$2.part" "$2"
}

# 2. Kokoro-82M (English voices, Apache-2.0)
K="$MODELS/kokoro"
say "Kokoro English model"
fetch "$HF/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main/onnx/model.onnx" "$K/model.onnx"
if [ ! -s "$K/voices.npz" ]; then
  for v in af_heart af_bella af_nicole af_sarah af_sky am_michael am_puck am_adam am_echo bf_emma bf_lily bm_george bm_lewis; do
    fetch "$HF/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main/voices/$v.bin" "$K/voices/$v.bin"
  done
  "$VENV/bin/python" - "$K" <<'PY'
import sys, pathlib, numpy as np
d = pathlib.Path(sys.argv[1])
voices = {p.stem: np.fromfile(p, dtype=np.float32).reshape(-1, 1, 256) for p in sorted((d / "voices").glob("*.bin"))}
np.savez(d / "voices.npz", **voices)
print("voices:", ", ".join(voices))
PY
fi

# 3. Piper Arabic voice (ar_JO kareem, built-in automatic tashkeel)
P="$MODELS/piper"
say "Piper Arabic voice"
for f in ar_JO-kareem-medium.onnx ar_JO-kareem-medium.onnx.json; do
  fetch "$HF/rhasspy/piper-voices/resolve/main/ar/ar_JO/kareem/medium/$f" "$P/$f"
done

# 4. Fonts with Arabic + Latin (SIL OFL, kept in the repo)
say "Fonts"
mkdir -p "$HOME/.local/share/fonts"
cp -n "$REPO"/assets/fonts/*.ttf "$HOME/.local/share/fonts/" 2>/dev/null || true
fc-cache -f >/dev/null 2>&1 || true

say "Done. Models in $MODELS, venv in $VENV"
