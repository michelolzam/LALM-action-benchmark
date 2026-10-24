#!/usr/bin/env bash
# LTU (Listen, Think, and Understand), original checkpoint of the paper
# Usage: bash envs/ltu/setup.sh [conda-env-name]
# Clones YuanGongND/ltu to $EXTERNALS_DIR/ltu (default: ./externals) and downloads
# the Vicuna / LTU weights into $EXTERNALS_DIR/ltu/pretrained_mdls (about 15 GB).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="${1:-sa-ltu}"
EXTERNALS_DIR="${EXTERNALS_DIR:-$HERE/../../externals}"
REPO_DIR="$EXTERNALS_DIR/ltu"
COMMIT=2002aad8305ee5579a2237a85a6e792c1174cda7

if [ ! -d "$REPO_DIR" ]; then
  git clone https://github.com/YuanGongND/ltu "$REPO_DIR"
  git -C "$REPO_DIR" checkout "$COMMIT"
fi

eval "$(conda shell.bash hook)"
conda create -y -n "$ENV_NAME" python=3.10
conda activate "$ENV_NAME"

# LTU's requirements without its numpy / numba pins (see requirements.txt), then
# the customised transformers and peft shipped with LTU (the originals do not work).
grep -vE '^(numpy|numba)([=<> ]|$)' "$REPO_DIR/src/ltu/requirements.txt" \
  > "$REPO_DIR/src/ltu/requirements.without-pinned.txt"
pip install -r "$REPO_DIR/src/ltu/requirements.without-pinned.txt" -r "$HERE/requirements.txt"
pip install -e "$REPO_DIR/src/ltu/hf-dev/transformers-main"
pip install -e "$REPO_DIR/src/ltu/peft-main"

# Weights (URLs from src/ltu/inference.sh of the LTU repository)
MODELS_DIR="$REPO_DIR/pretrained_mdls"
download_folder() {  # <name> <dropbox folder url>
  if [ ! -d "$MODELS_DIR/$1" ]; then
    mkdir -p "$MODELS_DIR/$1"
    wget -O "$MODELS_DIR/$1.zip" "$2"
    unzip -q "$MODELS_DIR/$1.zip" -d "$MODELS_DIR/$1" && rm "$MODELS_DIR/$1.zip"
  fi
}
download_folder vicuna "https://www.dropbox.com/scl/fo/mjn5wdnc1j67kkhbu0j9d/h?rlkey=anna5roa7netrmkjjm8p2hvyy&dl=1"
download_folder vicuna_ltu "https://www.dropbox.com/scl/fo/wzw72e9e88x6nfd94zwi7/h?rlkey=9izvxo6eegww5qfkukz2bhdch&dl=1"
# vicuna_ltu reuses the LLaMA shards of vicuna
for shard in pytorch_model-00001-of-00002.bin pytorch_model-00002-of-00002.bin; do
  ln -sf "../vicuna/$shard" "$MODELS_DIR/vicuna_ltu/$shard"
done
[ -f "$MODELS_DIR/ltu_ori_paper.bin" ] || wget -O "$MODELS_DIR/ltu_ori_paper.bin" \
  "https://www.dropbox.com/scl/fi/ir69ci3bhf4cthxnnnl76/ltu_ori_paper.bin?rlkey=zgqin9hh1nn2ua39jictcdhil&dl=1"

echo "Environment '$ENV_NAME' is ready. Weights: $MODELS_DIR"
