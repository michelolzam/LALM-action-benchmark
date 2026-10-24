#!/usr/bin/env bash
# Audio Flamingo 3 (thinking and no-thinking modes; checkpoint nvidia/audio-flamingo-3)
# Usage: bash envs/audio_flamingo_3/setup.sh [conda-env-name]
# Clones the audio_flamingo_3 branch of NVIDIA/audio-flamingo to
# $EXTERNALS_DIR/audio-flamingo-3 (default: ./externals). This follows the
# repository's environment_setup.sh with the package versions of the paper.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="${1:-sa-audio_flamingo_3}"
EXTERNALS_DIR="${EXTERNALS_DIR:-$HERE/../../externals}"
REPO_DIR="$EXTERNALS_DIR/audio-flamingo-3"
COMMIT=3ac1b62c3852675235295d8a0e7d7fd5c16cae52  # branch audio_flamingo_3

if [ ! -d "$REPO_DIR" ]; then
  git clone --branch audio_flamingo_3 https://github.com/NVIDIA/audio-flamingo "$REPO_DIR"
  git -C "$REPO_DIR" checkout "$COMMIT"
fi

eval "$(conda shell.bash hook)"
conda create -y -n "$ENV_NAME" python=3.10.14
conda activate "$ENV_NAME"

pip install --upgrade pip setuptools
pip install -e "$REPO_DIR[train,eval]"   # the `llava` package of Audio Flamingo 3
pip install -r "$HERE/requirements.txt"
pip install flash-attn==2.7.3 --no-build-isolation

# As in the repository's setup script: patched deepspeed files and a newer triton
SITE_PACKAGES="$(python -c 'import site; print(site.getsitepackages()[0])')"
cp -r "$REPO_DIR"/llava/train/deepspeed_replace/* "$SITE_PACKAGES/deepspeed/"
pip install triton==3.1.0

echo "Environment '$ENV_NAME' is ready."
