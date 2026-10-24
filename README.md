# Probing Large Audio-Language Models for Compositional Understanding of Sounding Actions

[![Paper](https://img.shields.io/badge/arXiv-2609.35345-b31b1b.svg)](https://arxiv.org/abs/2609.35345)
[![Website](https://img.shields.io/badge/companion-website-blue)](https://alm-sounding-actions.onrender.com/)

This repository rebuilds the benchmark of the paper from the original
[Ego4D](https://ego4d-data.org/) and [Ego-Exo4D](https://ego-exo4d-data.org/)
videos, and provides the environments of the audio-language models we evaluated.

The benchmark asks a model to recognise an everyday human activity (e.g.
*floor sweeping*, *playing guitar*, *frying food*) from a 5–10 s egocentric audio
clip, by choosing among four candidate activities. Two factors control the
difficulty of each question: how **typical** the clip is of its activity
(central vs. peripheral exemplar) and how **acoustically similar** the three
wrong answers are to the correct one (distant vs. near distractors).

Ego4D and Ego-Exo4D do not allow redistribution of their media, so we release
only metadata: which clip, cut from which video, at which timestamps, with
which label and distractors. The scripts below cut the clips from your own,
licensed copy of the datasets. **The rebuilt audio matches the audio used in
the paper:** every clip has the same length, and waveforms differ by at most
2.4e-7 (ffmpeg rounding).

## The benchmark at a glance

| | |
|---|---|
| Items | 1,938 (903 central, 1,035 peripheral) |
| Audio clips | 1,623 unique clips, 5–10 s, 48 kHz FLAC |
| Sources | 198 Ego4D videos (Moments, `val` split) and 220 Ego-Exo4D takes (`test` split) |
| Labels | 85 labels in the candidate space; 66 of them are ground truths (6–40 items each, median 35) |
| Taxonomy | 99 audible activity labels, organised hierarchically (SALT action taxonomy) |

Crossing exemplar typicality with distractor similarity gives the four
evaluation conditions:

| Condition | Clips | Distractors | Items |
|---|---|---|---|
| C-Dist | central | distant | 903 |
| C-Near | central | near | 903 |
| P-Dist | peripheral | distant | 1,035 |
| P-Near | peripheral | near | 1,035 |

## Rebuilding the benchmark

**1. Install** (conda, with ffmpeg 6.1):

```bash
git clone https://github.com/ORG/alm-sounding-actions && cd alm-sounding-actions
conda env create -f environment.yml
conda activate sounding-actions
```

**2. Get access** to Ego4D and Ego-Exo4D by signing their license agreements.
Each dataset gives you its own AWS credentials for the official downloaders
(installed above by `pip install ego4d`).

**3. Download only the videos you need** (198 Ego4D videos and 220 Ego-Exo4D
takes, about 215 GiB), with the credentials stored as the AWS profiles `ego4d`
and `egoexo`:

```bash
python scripts/list_source_videos.py --out-dir downloads/
ego4d --output_directory /data/ego4d --datasets full_scale \
      --video_uid_file downloads/ego4d_video_uids.txt --aws_profile_name ego4d
egoexo -o /data/egoexo4d --parts takes --views ego \
       --uids $(cat downloads/egoexo4d_take_uids.txt) --s3_profile egoexo
```

[docs/downloading_sources.md](docs/downloading_sources.md) walks through the
license requests, the credentials, the download sizes and how to reuse a copy
you already have (`<ego4d_root>/v2/full_scale/` and `<egoexo4d_root>/takes/`).

**4. Cut the clips** (about 2 minutes with 16 workers):

```bash
python scripts/build_benchmark.py \
    --ego4d-root /data/ego4d --egoexo4d-root /data/egoexo4d --out benchmark/
```

This writes `benchmark/audio/<clip_id>.flac` and `benchmark/benchmark.tsv` (the
manifest plus an `audio_path` column). Every clip is checked against the
sampling rate, channel count and number of samples recorded when the benchmark
was built; the script exits with an error if one does not match.

## Using the benchmark

```python
import random
from sounding_actions import load_benchmark, condition_items

benchmark = load_benchmark('benchmark/benchmark.tsv')

# Flat closed-set protocols (P1 direct inference, P2 event-grounded inference)
items = condition_items(benchmark, 'P-Near')
for item in items.itertuples():
    options = random.sample(item.options, k=4)  # 3 distractors + ground truth, shuffled
    audio = f'benchmark/{item.audio_path}'
    ...  # ask the model to pick one of `options`; the answer is `item.label`

# Hierarchical protocols (H1, H2) and open-ended inference (P3): root labels
# are not used as ground truths or distractors.
items = condition_items(benchmark, 'C-Dist', hierarchical=True)
# `item.coarse_labels` lists the coarse category (parent label) of the ground
# truth; the coarse candidates are the parents of the four options, see
# data/labels.tsv.
```

The columns of every file in `data/` are described in [data/README.md](data/README.md).
Labels with few items or an unbalanced central/peripheral split are flagged in
`data/labels.tsv` (`low_support`, `very_low_support`, `skewed`).

## Model environments

[envs/](envs/) contains one setup script per model family evaluated in the paper
(24 open-model configurations in 17 environments, plus the four Gemini models).
Each pins the package versions of the environment used for the paper; see
[envs/README.md](envs/README.md).

```bash
bash envs/qwen2_5_omni/setup.sh      # creates the conda env `sa-qwen2_5_omni`
```

## Reproducing the construction

The released manifest is the benchmark. For transparency, and to build new
variants, [scripts/construct_benchmark.py](scripts/construct_benchmark.py)
re-runs the whole curation from the raw annotations: cutting 10 s segments,
filtering by audibility and duration, CLAP embeddings, exemplar selection and
distractor sampling. Each stage was checked against the artifacts of the
original run. The method, its parameters and the verification are documented
in [docs/construction.md](docs/construction.md).

```bash
pip install -e ".[construction]"   # adds torch, torchaudio and msclap
python scripts/construct_benchmark.py \
    --ego4d-root /data/ego4d --egoexo4d-root /data/egoexo4d --out construction/
```

This needs the Ego4D Moments annotations and all Ego4D videos of the Moments
`val` split, and the `test` split of Ego-Exo4D with its metadata (about 480 GiB,
see [docs/downloading_sources.md](docs/downloading_sources.md#4-download-the-sources-of-the-construction-pipeline)).
The command below prints the corresponding download commands:

```bash
python scripts/list_source_videos.py --out-dir downloads/ --construction --ego4d-root /data/ego4d
```

## Repository layout

```text
data/                 benchmark metadata (no media): manifest, labels, taxonomy
sounding_actions/     Python package: manifest loading, clip extraction
  construction/       reference implementation of the benchmark construction
scripts/              list_source_videos.py, build_benchmark.py, construct_benchmark.py
envs/                 environment setup per evaluated model
docs/                 downloading the source datasets, construction method and verification
```

## Citation

```bibtex
@article{olvera2026sounding,
  title   = {Probing Large Audio-Language Models for Compositional Understanding of Sounding Actions},
  author  = {Olvera, Michel and Stamatiadis, Paraskevas and Wang, Changhong and Richard, Ga{\"e}l},
  journal = {arXiv preprint arXiv:2609.35345},
  year    = {2026}
}
```

If you use the benchmark, please also cite the source datasets:

```bibtex
@inproceedings{grauman2022ego4d,
  title     = {Ego4D: Around the World in 3,000 Hours of Egocentric Video},
  author    = {Grauman, Kristen and others},
  booktitle = {Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)},
  pages     = {18995--19012},
  year      = {2022}
}

@inproceedings{grauman2024egoexo4d,
  title     = {Ego-Exo4D: Understanding Skilled Human Activity from First- and Third-Person Perspectives},
  author    = {Grauman, Kristen and others},
  booktitle = {Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)},
  pages     = {19383--19400},
  year      = {2024}
}
```

## License

The metadata in `data/` is derived from Ego4D and Ego-Exo4D annotations. It
contains no media and is released for non-commercial research only, under terms
equivalent to those of the source datasets. Using the audio requires your own
Ego4D and Ego-Exo4D license (see <https://ego4d-data.org/docs/start-here/>).
The license of the code is TODO.

## Acknowledgments

This work was supported by the Hi!Paris Center and by the European Union (ERC,
HI-Audio, 101052978).
