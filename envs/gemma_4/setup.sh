#!/usr/bin/env bash
# Gemma-4-E4B-it (vLLM, with the E4B-it-assistant checkpoint for speculative decoding)
# Usage: bash envs/gemma_4/setup.sh [conda-env-name]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="${1:-sa-gemma_4}"

eval "$(conda shell.bash hook)"
conda create -y -n "$ENV_NAME" python=3.10
conda activate "$ENV_NAME"
pip install -r "$HERE/requirements.txt"

echo "Environment '$ENV_NAME' is ready."
