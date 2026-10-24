#!/usr/bin/env bash
# Qwen3-Omni-30B-A3B-Thinking (vLLM)
# Usage: bash envs/qwen3_omni_vllm/setup.sh [conda-env-name]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="${1:-sa-qwen3_omni_vllm}"

eval "$(conda shell.bash hook)"
conda create -y -n "$ENV_NAME" python=3.10
conda activate "$ENV_NAME"
pip install -r "$HERE/requirements.txt"

echo "Environment '$ENV_NAME' is ready."
