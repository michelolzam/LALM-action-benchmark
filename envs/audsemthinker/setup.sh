#!/usr/bin/env bash
# AudSemThinker
# Usage: bash envs/audsemthinker/setup.sh [conda-env-name]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="${1:-sa-audsemthinker}"

eval "$(conda shell.bash hook)"
conda create -y -n "$ENV_NAME" python=3.10
conda activate "$ENV_NAME"
pip install -r "$HERE/requirements.txt"

# flash-attn needs torch at build time, hence the separate step
pip install flash-attn==2.8.2 --no-build-isolation

echo "Environment '$ENV_NAME' is ready."
