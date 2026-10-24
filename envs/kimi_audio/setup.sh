#!/usr/bin/env bash
# Kimi-Audio-7B-Instruct
# Usage: bash envs/kimi_audio/setup.sh [conda-env-name]
# Clones the Kimi-Audio inference code to $EXTERNALS_DIR/Kimi-Audio (default: ./externals).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="${1:-sa-kimi_audio}"
EXTERNALS_DIR="${EXTERNALS_DIR:-$HERE/../../externals}"
REPO_DIR="$EXTERNALS_DIR/Kimi-Audio"
COMMIT=349251e1d8f4f98d58fda59246381faecd7392e0

if [ ! -d "$REPO_DIR" ]; then
  git clone https://github.com/MoonshotAI/Kimi-Audio "$REPO_DIR"
  git -C "$REPO_DIR" checkout "$COMMIT"
  git -C "$REPO_DIR" submodule update --init --recursive  # GLM-4-Voice tokenizer
fi

eval "$(conda shell.bash hook)"
conda create -y -n "$ENV_NAME" python=3.10
conda activate "$ENV_NAME"

# Kimi-Audio's requirements, except the packages whose versions we pin
# (CUDA 11.8 build of torch, see requirements.txt).
grep -vE '^(torch|torchaudio|flash_attn|deepspeed)([=<> ]|$)' "$REPO_DIR/requirements.txt" \
  > "$REPO_DIR/requirements.without-pinned.txt"
pip install -r "$REPO_DIR/requirements.without-pinned.txt" -r "$HERE/requirements.txt"

# flash-attn needs torch at build time, hence the separate step
pip install flash-attn==2.8.2 --no-build-isolation

echo "Environment '$ENV_NAME' is ready. Add $REPO_DIR to PYTHONPATH to import kimia_infer."
