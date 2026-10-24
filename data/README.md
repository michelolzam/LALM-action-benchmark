# Benchmark metadata

**Paper:** https://arxiv.org/abs/XXXX.XXXXX (placeholder) ·
**Dataset:** https://huggingface.co/datasets/ORG/alm-sounding-actions (placeholder)

All files are tab-separated. List-valued columns hold labels separated by `|`
and are empty when the list is empty. `sounding_actions.load_benchmark()` and
`load_labels()` return them as Python lists.

| File | Rows | Content |
|---|---|---|
| `benchmark.tsv` | 1,938 | one row per benchmark item |
| `labels.tsv` | 85 | the label space: every label that is a ground truth or a distractor |
| `taxonomy/taxonomy_nodes.tsv` | 99 | the audible taxonomy |
| `taxonomy/label_mapping.tsv` | 265 | Ego4D / Ego-Exo4D annotation labels mapped to SALT labels |
| `taxonomy/audibility_ratings.tsv` | 712 | two-round audibility rating of every SALT action label |

## `benchmark.tsv`

| Column | Description |
|---|---|
| `item_id` | `C0001`–`C0903` (central exemplars), `P0001`–`P1035` (peripheral exemplars) |
| `clip_id` | id of the audio clip, `<dataset>_<video uid or take name>_<start>_<end>`. Several items can share a clip (1,623 clips for 1,938 items), most often a clip that is an exemplar of both a label and one of its ancestors |
| `dataset` | `Ego4D` or `Ego-Exo4D` |
| `source_uid` | Ego4D `video_uid` or Ego-Exo4D `take_uid` |
| `take_name` | Ego-Exo4D take name (empty for Ego4D) |
| `source_video` | path of the source video inside the dataset download: `v2/full_scale/<video_uid>.mp4` (Ego4D) or `takes/<take_name>/ego_preview.mp4` (Ego-Exo4D) |
| `start_sec`, `end_sec` | clip boundaries in the source video, in seconds (full precision) |
| `sample_rate`, `num_channels`, `num_samples` | properties of the extracted FLAC clip, used to verify a rebuild |
| `dataset_label` | original annotation: Ego4D Moments label or Ego-Exo4D task name |
| `label` | ground-truth activity (SALT label) |
| `coarse_labels` | parent label(s) of `label` in the SALT taxonomy: the coarse answer of the hierarchical protocols. Empty for root labels. 8 labels have two parents; both are valid coarse answers |
| `exemplar_type` | `central` (typical of its label) or `peripheral` (atypical) |
| `typicality` | cosine similarity between the CLAP embedding of the clip and the label prototype (mean CLAP embedding of the label) |
| `distractors_distant` | 3 distractors drawn among the labels least similar to `label` (C-Dist, P-Dist) |
| `distractors_near` | 3 distractors drawn among the labels most similar to `label` (C-Near, P-Near) |
| `distractors_distant_no_roots`, `distractors_near_no_roots` | same, but root labels are never distractors. Used by the hierarchical protocols |

Distractors are never the parent or a child of the ground truth, but can be a
more distant ancestor or descendant; see [docs/construction.md](../docs/construction.md).

The four conditions of the paper:

| Condition | `exemplar_type` | distractor column | name in the raw experiment outputs |
|---|---|---|---|
| C-Dist | `central` | `distractors_distant` | `easy` |
| C-Near | `central` | `distractors_near` | `medium` |
| P-Dist | `peripheral` | `distractors_distant` | `challenging` |
| P-Near | `peripheral` | `distractors_near` | `hard` |

Which columns each protocol uses:

| Protocol | Items | Candidate labels |
|---|---|---|
| P1 direct inference, P2 event-grounded inference | all items | ground truth + `distractors_*` |
| P3 open-ended inference | central and peripheral items (reported as C-Dist and P-Near) whose `label` is not a root | none |
| H1 joint / H2 sequential hierarchical inference | items whose `label` is not a root | fine: ground truth + `distractors_*_no_roots`; coarse: the parents of these four labels (`labels.tsv`) |

## `labels.tsv`

| Column | Description |
|---|---|
| `label` | SALT label |
| `is_root` | top-level label of the taxonomy |
| `coarse_labels` | parent label(s) in the SALT taxonomy |
| `is_ground_truth` | has benchmark items (66 labels); the other 19 labels only appear as distractors |
| `n_central`, `n_peripheral`, `n_items` | number of benchmark items |
| `n_pool_clips` | number of candidate clips the label prototype was computed from |
| `low_support` | fewer than 20 items (19 labels) |
| `very_low_support` | fewer than 10 items (4 labels) |
| `skewed` | central/peripheral ratio of at least 5:1, or one of them empty (8 labels) |
| `audibility_round1`, `audibility_round2` | audibility ratings (see below) |

Results on `low_support` or `skewed` labels are less certain than on the others.

## `taxonomy/`

**`audibility_ratings.tsv`.** Each SALT action label was rated in two rounds
(`round1`, `round2`; `0` means not rated in round 2). Round 1 asks whether the
activity can in principle be recognised from sound: 1 visual only, 2 too
specific or too brief, 3 ambiguous but plausibly audible, 4 clearly audible.
Round 2 rates 1–2 minutes of audio from 6–14 files: 1 sound absent or
uninformative, 2 audible but insufficient on its own, 3 recognisable, 4
dominant and unambiguous. A label is kept if round 1 is 3–4 and round 2 is 2–4:
this gives the 99 audible labels.

**`taxonomy_nodes.tsv`.** The 99 audible labels, with their `parents` and
`children` in the full SALT action taxonomy (which may lie outside the audible
set) and their `audible_ancestors` (coarser labels that are audible
themselves).

**`label_mapping.tsv`.** For each Ego4D Moments label and Ego-Exo4D task name:
its fine SALT label (`salt_label`) and the audible labels a clip with that
annotation counts towards (`benchmark_labels`: the fine label if it is audible
and all its audible ancestors). Annotation labels whose `benchmark_labels` is
empty are not used.
