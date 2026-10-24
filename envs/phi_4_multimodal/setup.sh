#!/usr/bin/env bash
# Phi-4-multimodal-instruct
# Usage: bash envs/phi_4_multimodal/setup.sh [conda-env-name]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="${1:-sa-phi_4_multimodal}"

eval "$(conda shell.bash hook)"
conda create -y -n "$ENV_NAME" python=3.10
conda activate "$ENV_NAME"
pip install -r "$HERE/requirements.txt"

# flash-attn needs torch at build time, hence the separate step
pip install flash-attn==2.7.4.post1 --no-build-isolation

echo "Environment '$ENV_NAME' is ready."
