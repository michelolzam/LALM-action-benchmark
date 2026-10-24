#!/usr/bin/env bash
# Audio Flamingo Next (base, Think and Captioner checkpoints)
# Usage: bash envs/audio_flamingo_next/setup.sh [conda-env-name]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="${1:-sa-audio_flamingo_next}"

eval "$(conda shell.bash hook)"
conda create -y -n "$ENV_NAME" python=3.10
conda activate "$ENV_NAME"
pip install -r "$HERE/requirements.txt"

echo "Environment '$ENV_NAME' is ready."
