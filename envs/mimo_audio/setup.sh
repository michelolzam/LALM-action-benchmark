#!/usr/bin/env bash
# MiMo-Audio-7B-Instruct (thinking and no-thinking modes)
# Usage: bash envs/mimo_audio/setup.sh [conda-env-name]
# Clones XiaomiMiMo/MiMo-Audio to $EXTERNALS_DIR/MiMo-Audio (default: ./externals),
# applies mimo_audio.patch and downloads the model and tokenizer into its models/ folder.
#
# mimo_audio.patch contains the changes made for the paper: `audio_understanding_sft`
# accepts `max_new_tokens` / `add_history`, and a `temperature_mode` switch was added
# (its default values are the upstream ones).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="${1:-sa-mimo_audio}"
EXTERNALS_DIR="${EXTERNALS_DIR:-$HERE/../../externals}"
REPO_DIR="$EXTERNALS_DIR/MiMo-Audio"
COMMIT=62d956b4a1a45419bee5e41f477078c3684dbbcc

if [ ! -d "$REPO_DIR" ]; then
  git clone https://github.com/XiaomiMiMo/MiMo-Audio "$REPO_DIR"
  git -C "$REPO_DIR" checkout "$COMMIT"
  git -C "$REPO_DIR" apply "$HERE/mimo_audio.patch"
fi

eval "$(conda shell.bash hook)"
conda create -y -n "$ENV_NAME" python=3.12
conda activate "$ENV_NAME"
pip install -r "$REPO_DIR/requirements.txt" -r "$HERE/requirements.txt"
pip install "https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.4.post1/flash_attn-2.7.4.post1+cu12torch2.6cxx11abiFALSE-cp312-cp312-linux_x86_64.whl"

# Model revisions used for the paper
huggingface-cli download XiaomiMiMo/MiMo-Audio-7B-Instruct \
  --revision 6fd52f6aa692f46f5091b12d538b18cf3cb0327c --local-dir "$REPO_DIR/models/MiMo-Audio-7B-Instruct"
huggingface-cli download XiaomiMiMo/MiMo-Audio-Tokenizer \
  --revision c00d7b05062f6eda60890a03b9dfcb7da09b1d29 --local-dir "$REPO_DIR/models/MiMo-Audio-Tokenizer"

echo "Environment '$ENV_NAME' is ready."
