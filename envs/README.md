# Environments of the evaluated models

**Paper:** https://arxiv.org/abs/2609.35345

The models depend on different, often incompatible versions of `torch` and
`transformers`, so each model family gets its own conda environment. Every
folder contains:

- `setup.sh`: creates the conda environment (named `sa-<folder>` by default,
  or the name given as first argument), installs the packages and, when needed,
  clones the model's code at the commit we used and downloads checkpoints that
  are not on the Hugging Face Hub;
- `requirements.txt`: the pinned versions of the packages that matter
  (`torch`, `transformers`, ...), taken from the environment used for the paper;
- `pip-freeze.txt`: the full snapshot of that environment, for reference.

```bash
bash envs/qwen2_5_omni/setup.sh                 # conda env "sa-qwen2_5_omni"
EXTERNALS_DIR=/data/models bash envs/ltu/setup.sh  # where code/checkpoints go (default: ./externals)
```

Requirements: Linux x86-64, conda, an NVIDIA GPU with a recent driver, and git.
Models hosted on the Hugging Face Hub are downloaded on first use; run
`huggingface-cli login` first and accept the licenses of the gated models
(Gemma, and Llama 3.1 for DeSTA2.5-Audio).

## Models

| Model (as in the paper) | Environment | Checkpoint(s) | Revision used |
|---|---|---|---|
| LTU | `ltu` | original LTU checkpoint `ltu_ori_paper.bin` + `vicuna_ltu` (downloaded by `setup.sh`) | — |
| GAMA | `gama` | GAMA stage-5 `checkpoint-2500` + `Llama-2-7b-chat-hf-qformer` (downloaded by `setup.sh`) | — |
| SALMONN | `salmonn` | [tsinghua-ee/SALMONN-7B](https://huggingface.co/tsinghua-ee/SALMONN-7B) (`salmonn_7b_v0.pth`), whisper-large-v2, vicuna-7b-v1.5, BEATs (downloaded by `setup.sh`) | — |
| Qwen3-Omni-30B-A3B-Captioner | `qwen3_omni` | [Qwen/Qwen3-Omni-30B-A3B-Captioner](https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Captioner) | `a2bd106c` |
| Audio Flamingo Next-Captioner | `audio_flamingo_next` | [nvidia/audio-flamingo-next-captioner-hf](https://huggingface.co/nvidia/audio-flamingo-next-captioner-hf) | `62aa63a6` |
| Gemma-3n-E4B-it | `gemma_3n` | [google/gemma-3n-e4b-it](https://huggingface.co/google/gemma-3n-e4b-it) | — |
| Kimi-Audio-7B-Instruct | `kimi_audio` | [moonshotai/Kimi-Audio-7B-Instruct](https://huggingface.co/moonshotai/Kimi-Audio-7B-Instruct) | `9a82a84c` |
| Qwen2-Audio-7B-Instruct | `qwen2_audio` | [Qwen/Qwen2-Audio-7B-Instruct](https://huggingface.co/Qwen/Qwen2-Audio-7B-Instruct) | — |
| Qwen2.5-Omni-3B / 7B | `qwen2_5_omni` | [Qwen/Qwen2.5-Omni-3B](https://huggingface.co/Qwen/Qwen2.5-Omni-3B), [Qwen/Qwen2.5-Omni-7B](https://huggingface.co/Qwen/Qwen2.5-Omni-7B) | — |
| Qwen3-Omni-30B-A3B-Instruct | `qwen3_omni` | [Qwen/Qwen3-Omni-30B-A3B-Instruct](https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct) | `26291f79` |
| DeSTA2.5-Audio | `desta2_5_audio` | [DeSTA-ntu/DeSTA2.5-Audio-Llama-3.1-8B](https://huggingface.co/DeSTA-ntu/DeSTA2.5-Audio-Llama-3.1-8B) | — |
| Phi-4-Multimodal-Instruct | `phi_4_multimodal` | [microsoft/Phi-4-multimodal-instruct](https://huggingface.co/microsoft/Phi-4-multimodal-instruct) | `93f923e1` |
| Audio Flamingo 3 (Thinking / No Thinking) | `audio_flamingo_3` | [nvidia/audio-flamingo-3](https://huggingface.co/nvidia/audio-flamingo-3) (thinking: its `stage35` adapter) | `51841c40` |
| Audio Flamingo Next (Thinking / No Thinking) | `audio_flamingo_next` | [nvidia/audio-flamingo-next-think-hf](https://huggingface.co/nvidia/audio-flamingo-next-think-hf) / [nvidia/audio-flamingo-next-hf](https://huggingface.co/nvidia/audio-flamingo-next-hf) | `e3b98384` / `5634886e` |
| Audio-Reasoner (Thinking / No Thinking) | `audio_reasoner` | [zhifeixie/Audio-Reasoner](https://huggingface.co/zhifeixie/Audio-Reasoner) | `f38198da` |
| MiMo-Audio (Thinking / No Thinking) | `mimo_audio` | [XiaomiMiMo/MiMo-Audio-7B-Instruct](https://huggingface.co/XiaomiMiMo/MiMo-Audio-7B-Instruct) + [MiMo-Audio-Tokenizer](https://huggingface.co/XiaomiMiMo/MiMo-Audio-Tokenizer) (downloaded by `setup.sh`) | `6fd52f6a` / `c00d7b05` |
| AudSemThinker | `audsemthinker` | [gijs/audsemthinker](https://huggingface.co/gijs/audsemthinker) (with the Qwen2.5-Omni-7B processor) | — |
| Qwen3-Omni-30B-A3B-Thinking | `qwen3_omni_vllm` | [Qwen/Qwen3-Omni-30B-A3B-Thinking](https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Thinking), served with vLLM | — |
| Gemma-4-E4B-it | `gemma_4` | [google/gemma-4-E4B-it](https://huggingface.co/google/gemma-4-E4B-it) with [google/gemma-4-E4B-it-assistant](https://huggingface.co/google/gemma-4-E4B-it-assistant) for speculative decoding, served with vLLM | — |
| Gemini 2.0-Flash-Lite, 2.5-Flash-Lite, 2.0-Flash, 2.5-Flash | `gemini` | Gemini API (`gemini-2.0-flash-lite`, `gemini-2.5-flash-lite`, `gemini-2.0-flash`, `gemini-2.5-flash`); set `GEMINI_API_KEY` | — |

"Revision used" is the Hugging Face commit we evaluated, where we have a record
of it; pass it as `revision=` to `from_pretrained` to use exactly the same
weights. "Thinking / No Thinking" variants share a checkpoint and differ in
prompting or decoding mode, except Audio Flamingo Next, which has a separate
thinking checkpoint.

## Main package versions

| Environment | Python | torch | transformers | Other |
|---|---|---|---|---|
| `audio_flamingo_3` | 3.10.14 | 2.3.0 | 4.46.0 | flash-attn 2.7.3, deepspeed 0.15.4, [code](https://github.com/NVIDIA/audio-flamingo/tree/audio_flamingo_3) @ `3ac1b62` |
| `audio_flamingo_next` | 3.10 | 2.12.0 | 5.8.1 | |
| `audio_reasoner` | 3.10 | 2.8.0 | 4.48.0 | ms-swift 3.0.0 |
| `audsemthinker` | 3.10 | 2.7.1 | 4.54.1 | flash-attn 2.8.2, qwen-omni-utils 0.0.8 |
| `desta2_5_audio` | 3.10 | 2.8.0 | 4.49.0 | peft 0.17.1, [code](https://github.com/kehanlu/DeSTA2.5-Audio) @ `5503dfc` |
| `gama` | 3.10 | 1.13.1 | GAMA's fork (4.28.0.dev0) | [code](https://github.com/Sreyan88/GAMA) @ `041c3a6` |
| `gemini` | 3.10 | — | — | google-genai 1.52.0 |
| `gemma_3n` | 3.10 | 2.9.1 | 4.57.3 | timm 1.0.22 |
| `gemma_4` | 3.10 | 2.11.0 | 5.8.1 | vllm 0.21.0 |
| `kimi_audio` | 3.10 | 2.7.1 (CUDA 11.8) | 4.54.1 | flash-attn 2.8.2, [code](https://github.com/MoonshotAI/Kimi-Audio) @ `349251e` |
| `ltu` | 3.10 | 1.13.1 | LTU's fork (4.28.0.dev0) | [code](https://github.com/YuanGongND/ltu) @ `2002aad` |
| `mimo_audio` | 3.12 | 2.6.0 | 4.49.0 | flash-attn 2.7.4.post1, [code](https://github.com/XiaomiMiMo/MiMo-Audio) @ `62d956b` + `mimo_audio.patch` |
| `phi_4_multimodal` | 3.10 | 2.6.0 | 4.48.2 | flash-attn 2.7.4.post1, peft 0.13.2 |
| `qwen2_5_omni` | 3.10 | 2.8.0 | git `cb39f7d` (4.52.0.dev0) | flash-attn 2.8.3, qwen-omni-utils 0.0.8 |
| `qwen2_audio` | 3.10 | 2.7.1 | git `b727c2b` (4.55.0.dev0) | |
| `qwen3_omni` | 3.10 | 2.5.1 (CUDA 12.1) | git `7bbfc19` (5.0.0.dev0) | flash-attn 2.8.3, qwen-omni-utils 0.0.8 |
| `qwen3_omni_vllm` | 3.10 | 2.11.0 | git `b797f0d` (5.8.0.dev0) | vllm 0.21.0, qwen-omni-utils 0.0.9 |
| `salmonn` | 3.9 | 2.0.1 | 4.28.0 | peft 0.3.0 |

Notes:

- **GPU memory.** The Qwen3-Omni-30B-A3B models (about 70 GB of weights in
  bf16) need an 80 GB GPU or several GPUs; the vLLM setup uses all visible GPUs
  with tensor parallelism.
- **flash-attn** is installed in a separate step with `--no-build-isolation`;
  when no pre-built wheel matches your CUDA / torch combination, pip compiles it,
  which requires the CUDA toolkit and takes a while.
- **Version conflicts reported by pip are expected** for `audio_reasoner`
  (ms-swift 3.0.0 declares `transformers<4.48`) and `audio_flamingo_3` (the
  repository pins older deepspeed / triton versions that its own setup script
  then upgrades). The scripts reproduce the environments used for the paper.
- **MiMo-Audio** is run with the small changes in `mimo_audio/mimo_audio.patch`
  (passing `max_new_tokens` through `audio_understanding_sft`, and a temperature
  switch whose default values are those of the original code).
