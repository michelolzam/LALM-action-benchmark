#!/usr/bin/env bash
# SALMONN-7B (v0 checkpoint)
# Usage: bash envs/salmonn/setup.sh [conda-env-name]
# Downloads the SALMONN code + checkpoint and its three components into
# $EXTERNALS_DIR/salmonn (default: ./externals), laid out as:
#   salmonn/  code and salmonn_7b_v0.pth (huggingface.co/tsinghua-ee/SALMONN-7B)
#   whisper/  openai/whisper-large-v2
#   vicuna/   lmsys/vicuna-7b-v1.5
#   beats/    BEATs_iter3_plus_AS2M_finetuned_on_AS2M_cpt2.pt
#   ckpt/     salmonn_7b_v0.pth (link)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="${1:-sa-salmonn}"
EXTERNALS_DIR="${EXTERNALS_DIR:-$HERE/../../externals}"
SALMONN_DIR="$EXTERNALS_DIR/salmonn"

eval "$(conda shell.bash hook)"
conda create -y -n "$ENV_NAME" python=3.9
conda activate "$ENV_NAME"
pip install -r "$HERE/requirements.txt"

huggingface-cli download tsinghua-ee/SALMONN-7B --local-dir "$SALMONN_DIR/salmonn"
huggingface-cli download openai/whisper-large-v2 --local-dir "$SALMONN_DIR/whisper"
huggingface-cli download lmsys/vicuna-7b-v1.5 --local-dir "$SALMONN_DIR/vicuna"

# BEATs checkpoint. This is the mirror used for the paper; the original is linked
# from https://github.com/microsoft/unilm/tree/master/beats.
mkdir -p "$SALMONN_DIR/beats" "$SALMONN_DIR/ckpt"
BEATS="$SALMONN_DIR/beats/BEATs_iter3_plus_AS2M_finetuned_on_AS2M_cpt2.pt"
[ -f "$BEATS" ] || wget -O "$BEATS" \
  "https://huggingface.co/THUdyh/Ola_speech_encoders/resolve/refs%2Fpr%2F1/BEATs_iter3_plus_AS2M_finetuned_on_AS2M_cpt2.pt?download=true"
ln -sf ../salmonn/salmonn_7b_v0.pth "$SALMONN_DIR/ckpt/salmonn_7b_v0.pth"

echo "Environment '$ENV_NAME' is ready. Checkpoints: $SALMONN_DIR"
