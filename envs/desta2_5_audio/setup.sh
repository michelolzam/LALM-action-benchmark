#!/usr/bin/env bash
# DeSTA2.5-Audio (DeSTA2.5-Audio-Llama-3.1-8B)
# Usage: bash envs/desta2_5_audio/setup.sh [conda-env-name]
# Clones the DeSTA2.5-Audio code to $EXTERNALS_DIR/DeSTA2.5-Audio (default: ./externals).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="${1:-sa-desta2_5_audio}"
EXTERNALS_DIR="${EXTERNALS_DIR:-$HERE/../../externals}"
REPO_DIR="$EXTERNALS_DIR/DeSTA2.5-Audio"
COMMIT=5503dfcb8c07ddc608ef705542f0f9b94cc99de8

if [ ! -d "$REPO_DIR" ]; then
  git clone https://github.com/kehanlu/DeSTA2.5-Audio "$REPO_DIR"
  git -C "$REPO_DIR" checkout "$COMMIT"
fi

eval "$(conda shell.bash hook)"
conda create -y -n "$ENV_NAME" python=3.10
conda activate "$ENV_NAME"
pip install -r "$HERE/requirements.txt"
pip install -e "$REPO_DIR"

echo "Environment '$ENV_NAME' is ready."
