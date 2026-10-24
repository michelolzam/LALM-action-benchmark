#!/usr/bin/env bash
# GAMA (stage-5 checkpoint)
# Usage: bash envs/gama/setup.sh [conda-env-name]
# Clones Sreyan88/GAMA to $EXTERNALS_DIR/GAMA (default: ./externals) and downloads
# the checkpoints published by the GAMA authors on Google Drive into $EXTERNALS_DIR/GAMA/assets.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="${1:-sa-gama}"
EXTERNALS_DIR="${EXTERNALS_DIR:-$HERE/../../externals}"
REPO_DIR="$EXTERNALS_DIR/GAMA"
COMMIT=041c3a623c6c635e65463cef16ce0cfde72e5c57

if [ ! -d "$REPO_DIR" ]; then
  git clone https://github.com/Sreyan88/GAMA "$REPO_DIR"
  git -C "$REPO_DIR" checkout "$COMMIT"
fi

eval "$(conda shell.bash hook)"
conda create -y -n "$ENV_NAME" python=3.10
conda activate "$ENV_NAME"

# GAMA's requirements without its numpy / numba pins (see requirements.txt), then
# the customised transformers and peft shipped with GAMA.
grep -vE '^(numpy|numba)([=<> ]|$)' "$REPO_DIR/requirements.txt" \
  > "$REPO_DIR/requirements.without-pinned.txt"
pip install -r "$REPO_DIR/requirements.without-pinned.txt" -r "$HERE/requirements.txt"
pip install -e "$REPO_DIR/hf-dev-train/transformers-main" -e "$REPO_DIR/peft-main"

# Checkpoints: stage-5 GAMA weights (checkpoint-2500/) and the Llama-2 Q-Former base model
cd "$REPO_DIR/assets"
if [ ! -d checkpoint-2500 ]; then
  gdown 1Rfwf9CGubPZ1lHX9yIhIjZjwB3IGX1cy -O stage5_epoch2.zip
  unzip -q stage5_epoch2.zip && rm stage5_epoch2.zip
fi
if [ ! -d Llama-2-7b-chat-hf-qformer ]; then
  gdown 1bWIyJOOzlrQbuIZPYTwH8au8ywrATe7K -O Llama-2-7b-chat-hf-qformer.zip
  unzip -q Llama-2-7b-chat-hf-qformer.zip && rm Llama-2-7b-chat-hf-qformer.zip
fi

echo "Environment '$ENV_NAME' is ready. Checkpoints: $REPO_DIR/assets"
