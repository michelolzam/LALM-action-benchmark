#!/usr/bin/env bash
# Gemini 2.0 Flash(-Lite) and 2.5 Flash(-Lite), through the Gemini API
# Usage: bash envs/gemini/setup.sh [conda-env-name]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="${1:-sa-gemini}"

eval "$(conda shell.bash hook)"
conda create -y -n "$ENV_NAME" python=3.10
conda activate "$ENV_NAME"
pip install -r "$HERE/requirements.txt"

if [ -z "${GEMINI_API_KEY:-}" ]; then
  echo "Note: export GEMINI_API_KEY=<your key> before running the Gemini models."
fi

echo "Environment '$ENV_NAME' is ready."
