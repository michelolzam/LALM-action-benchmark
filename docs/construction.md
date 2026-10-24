# How the benchmark was built

**Paper:** https://arxiv.org/abs/XXXX.XXXXX (placeholder) ·
**Dataset:** https://huggingface.co/datasets/ORG/alm-sounding-actions (placeholder)

This document describes the construction pipeline implemented in
`sounding_actions/construction/` and run by `scripts/construct_benchmark.py`.
It is a cleaned-up re-implementation of the research code that produced the
released benchmark (`data/benchmark.tsv`). Every stage was checked against the
artifacts of that original run (see [Verification](#verification)).

> Re-running the pipeline does **not** give back the released benchmark exactly:
> CLAP embeddings of clips longer than 7 s depend on random crops, and
> distractors are sampled at random; neither was seeded in the original run.
> Use the released manifest to evaluate on the benchmark of the paper.

## Overview

| Stage | Module | Output |
|---|---|---|
| 0. Audible taxonomy | `data/taxonomy/` (from two listening rounds) | 99 audible SALT labels |
| 1. Segments | `segments.py` | ≤ 10 s windows of the annotated activities |
| 2. Candidate pool | `pool.py` | (segment, label) pairs usable as exemplars |
| 3. Embeddings | `embeddings.py` | one CLAP embedding per segment |
| 4. Selection | `selection.py` | central / peripheral exemplars, distant / near distractors |

| Parameter | Value |
|---|---|
| Segment length | at most 10 s; segments must last more than 5 s |
| Embedding model | Microsoft CLAP 2023 (`msclap`), 44.1 kHz, 7 s input |
| Outlier threshold | typicality below mean − 2 std of the label |
| Exemplars per label and type | at most 20, one per recording |
| Minimum support | more than 5 exemplars of a type, otherwise the label is not a ground truth of that type |
| Distractors | 3, drawn from the 12 closest (near) or farthest (distant) valid labels |

## Stage 0: audible taxonomy

Activity labels come from the SALT action taxonomy, which maps the labels of
Ego4D, Ego-Exo4D and HD-EPIC to standard labels organised in a hierarchy.
Every SALT action label was rated in two listening rounds (whether the activity
is audible in principle, then how well it can be recognised in 1–2 minutes of
sampled audio); the 99 labels rated 3–4 in round 1 and 2–4 in round 2 form the
audible taxonomy (`data/taxonomy/audibility_ratings.tsv`,
`data/taxonomy/taxonomy_nodes.tsv`). HD-EPIC contributes labels to the taxonomy
but no clips to the benchmark.

## Stage 1: segments

Only held-out data is used: the `val` split of the Ego4D Moments Queries
annotations and the `test` split of Ego-Exo4D. Every Ego4D moment (a labelled
interval of a video, `moments_val.json`) and every Ego-Exo4D take (a single task
between `task_start_sec` and `task_end_sec`, `takes.json`) is cut into
consecutive 10 s windows; the last window keeps the remainder. Zero-length
annotations are skipped.

## Stage 2: candidate pool

Each segment is extracted from the video with ffmpeg (Ego4D: `full_scale`
video; Ego-Exo4D: `ego_preview.mp4`, the preview video of the take, which has an
audio track for most takes). Videos without an audio track are skipped. A
segment enters the pool if

1. its annotation maps to an audible label (`data/taxonomy/label_mapping.tsv`).
   The segment then counts for its fine label **and for all audible coarser
   labels**: a `stirring/mixing_food` segment is also a `general_cooking_actions`,
   `cooking/preparing_food` and `kitchen_management_activities` segment. The pool
   therefore has one row per (segment, label) pair;
2. its audio file received a single annotation label (checked after step 1);
3. its audio lasts more than 5 s;
4. its audio is not digital silence.

## Stage 3: CLAP embeddings

Each segment is embedded with CLAP 2023. The preprocessing reproduces the one
of the original run: resampling to 44.1 kHz, flattening the channels into one
signal (for stereo clips the two channels are concatenated), repeating signals
shorter than 7 s and cropping a random 7 s window from longer ones. Here the
crop is drawn from a seeded generator (`--seed`).

## Stage 4: exemplars and distractors

**Prototypes.** The prototype of a label is the mean embedding of its pool rows.
Because segments also count for coarser labels (stage 2), the prototype of a
coarse label summarises the segments of its descendants too.

**Typicality.** The typicality of a segment for a label is the cosine
similarity between its embedding and the prototype. Ranking by cosine
similarity is the same as ranking by ℓ2 distance between ℓ2-normalised
embeddings.

**Exemplars.** For each label: drop segments with typicality below mean − 2 std;
recompute the mean; *central* candidates are the segments above it (most
typical first), *peripheral* candidates the segments below it (least typical
first), ties broken by longer duration. Keep at most one segment per recording
and 20 per type. A label is a ground truth of a type only if it keeps more
than 5 exemplars of that type. The same segment can be an exemplar of a label
and of one of its ancestors.

**Distractors.** For each item, the labels that have a prototype are ranked by
the cosine similarity of their prototype to the ground-truth prototype (most
similar first for *near* distractors, least similar first for *distant* ones).
Walking down the ranking, a label is skipped when it is a parent or a child of
the ground truth or of a label accepted before; the first 12 accepted labels
form the candidate set, from which 3 distractors are drawn at random. A second
set of distractors excludes root labels altogether; the hierarchical protocols
use it, so that the fine-grained options never include the coarse categories
of the first question.

### Behaviours of the original run kept in the reference implementation

These details are reproduced on purpose, so that the pipeline describes how the
released benchmark was built. Change them if you build a new variant.

- **Recording identity.** "One exemplar per recording" uses the take name for
  Ego-Exo4D but the *annotator id* for Ego4D (the prefix of the original audio
  file names). An Ego4D video can thus contribute several exemplars to a label
  when it was annotated by several annotators, and one annotator contributes
  at most one exemplar per label and type.
- **Only immediate relatives are excluded.** A distractor cannot be the parent
  or a child of the ground truth, but more distant ancestors and descendants
  are allowed (e.g. `kitchen_management_activities` for `boiling/simmering`).
  In the released benchmark this concerns 531 of the 1,938 `distractors_near`
  sets, 411 `distractors_near_no_roots` sets, and about 70 of each distant set.
- **Labels with two parents.** 8 of the 85 labels have two parents in SALT. For
  them, neither parent is excluded from the distractors (only unique parents
  are).
- **Channel flattening and random crops** in the CLAP preprocessing (stage 3).
- **Single-label check after the taxonomy mapping** (stage 2): annotations that
  map outside the audible taxonomy do not make a segment multi-label.

## Verification

`kg-code/release/verify_reference_pipeline.py` in the research repository runs
each stage of this implementation on the data of the original run and compares
the outputs.

| Stage | Check | Result |
|---|---|---|
| 1. Segments | segments and labels vs. the segments cut originally (downloaded videos) | identical, except 49 segments of one Ego4D video (`2a2ff7db-…`) that were not cut in the original run |
| 2. Pool | (segment, label) pairs, using the durations measured originally | identical: 51,819 pairs, 20,640 segments, 85 labels |
| 3. Embeddings | reference embeddings vs. original ones, mono clips under 7 s (no random crop) | median cosine 0.9998 (min 0.980, 120 clips) |
| 4. Exemplars | selection from the **original** embeddings vs. released items | identical: same 903 central and 1,035 peripheral items, in the same order |
| 4. Distractors | released distractors vs. candidate sets computed here | all 1,938 × 4 distractor sets lie in the computed candidate sets |
| Rebuild | `build_benchmark.py` clips vs. the audio used in the paper | same number of samples for all 1,623 clips; max absolute difference 2.4e-7 |
