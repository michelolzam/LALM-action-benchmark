#!/usr/bin/env bash
# Audio-Reasoner (thinking and no-thinking prompting), run through ms-swift
# Usage: bash envs/audio_reasoner/setup.sh [conda-env-name]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="${1:-sa-audio_reasoner}"

eval "$(conda shell.bash hook)"
conda create -y -n "$ENV_NAME" python=3.10
conda activate "$ENV_NAME"
pip install -r "$HERE/requirements.txt"
# ms-swift 3.0.0 declares transformers<4.48, but Audio-Reasoner was run with 4.48.0
# (installed on top, as in the paper environment; pip reports the conflict).
pip install transformers==4.48.0

echo "Environment '$ENV_NAME' is ready."
