#!/usr/bin/env bash
# Gemma-3n-E4B-it
# Usage: bash envs/gemma_3n/setup.sh [conda-env-name]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="${1:-sa-gemma_3n}"

eval "$(conda shell.bash hook)"
conda create -y -n "$ENV_NAME" python=3.10
conda activate "$ENV_NAME"
pip install -r "$HERE/requirements.txt"

echo "Environment '$ENV_NAME' is ready."
