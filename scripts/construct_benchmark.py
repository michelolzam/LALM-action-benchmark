"""Re-run the benchmark construction from scratch (reference implementation).

    python scripts/construct_benchmark.py \
        --ego4d-root /data/ego4d --egoexo4d-root /data/egoexo4d --out construction/

Stages (see docs/construction.md):
  1. cut Ego4D Moments (val) and Ego-Exo4D (test) activity intervals into <= 10 s segments
  2. extract their audio and keep audible, single-label, > 5 s, non-silent segments
  3. embed the segments with CLAP
  4. select central / peripheral exemplars and sample distractors

Outputs in --out: `benchmark.tsv` (same format as data/benchmark.tsv),
`pool.tsv` (candidate pool with typicality scores) and `embeddings.npz`.

IMPORTANT: this does not reproduce the released benchmark bit for bit, because
the original CLAP preprocessing used unseeded random crops and the distractors
were sampled without a seed. To evaluate on the benchmark of the paper, use
`scripts/build_benchmark.py` with the released manifest. This script is meant
for auditing the procedure and for building new variants of the benchmark.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sounding_actions.benchmark import LIST_COLUMNS, LIST_SEPARATOR, make_clip_id  # noqa: E402
from sounding_actions.construction import selection  # noqa: E402
from sounding_actions.construction.embeddings import clap_embeddings  # noqa: E402
from sounding_actions.construction.pool import build_pool, extract_segments  # noqa: E402
from sounding_actions.construction.segments import egoexo4d_segments, ego4d_segments  # noqa: E402
from sounding_actions.construction.taxonomy import Taxonomy  # noqa: E402
from sounding_actions.extraction import audio_info  # noqa: E402

MANIFEST_COLUMNS = [
    'item_id', 'clip_id', 'dataset', 'source_uid', 'take_name', 'source_video',
    'start_sec', 'end_sec', 'sample_rate', 'num_channels', 'num_samples',
    'dataset_label', 'label', 'coarse_labels', 'exemplar_type', 'typicality',
    'distractors_distant', 'distractors_near',
    'distractors_distant_no_roots', 'distractors_near_no_roots',
]


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--ego4d-root', required=True,
                        help='Ego4D download directory (with v2/annotations and v2/full_scale)')
    parser.add_argument('--egoexo4d-root', required=True,
                        help='Ego-Exo4D download directory (with takes.json, annotations/ and takes/)')
    parser.add_argument('--out', required=True, help='Output directory')
    parser.add_argument('--seed', type=int, default=0, help='Seed for CLAP crops and distractors')
    parser.add_argument('--workers', type=int, default=8, help='Parallel ffmpeg processes')
    parser.add_argument('--batch-size', type=int, default=8, help='CLAP batch size')
    return parser.parse_args()


def to_manifest(items, taxonomy):
    items = items.copy()
    items['item_id'] = [f'{"C" if t == "central" else "P"}{i:04d}' for t, i in
                        zip(items['exemplar_type'], items.groupby('exemplar_type').cumcount() + 1)]
    items['clip_id'] = [make_clip_id(*row) for row in zip(
        items['dataset'], items['source_uid'], items['take_name'],
        items['start_sec'], items['end_sec'])]
    info = pd.DataFrame([audio_info(p) for p in items['audio_path']], index=items.index)
    items = items.join(info)
    items['coarse_labels'] = [taxonomy.parents(label) for label in items['label']]
    items['typicality'] = items['typicality'].round(6)
    for col in LIST_COLUMNS:
        items[col] = items[col].map(LIST_SEPARATOR.join)
    return items[MANIFEST_COLUMNS]


def main():
    args = parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    taxonomy = Taxonomy()

    print('Stage 1/4: segments')
    segments = pd.concat([ego4d_segments(args.ego4d_root, split='val'),
                          egoexo4d_segments(args.egoexo4d_root, split='test')],
                         ignore_index=True)
    print(f'  {segments["segment_id"].nunique()} segments')

    print('Stage 2/4: candidate pool')
    segments = extract_segments(segments, out_dir / 'segments', args.ego4d_root,
                                args.egoexo4d_root, workers=args.workers)
    pool = build_pool(segments, taxonomy)
    print(f'  {len(pool)} (segment, label) pairs, {pool["segment_id"].nunique()} segments, '
          f'{pool["label"].nunique()} labels')

    print('Stage 3/4: CLAP embeddings')
    unique = pool.drop_duplicates('segment_id').reset_index(drop=True)
    embeddings = clap_embeddings(unique['audio_path'].tolist(), batch_size=args.batch_size,
                                 seed=args.seed)
    pool['embedding_idx'] = pool['segment_id'].map(
        {segment_id: i for i, segment_id in enumerate(unique['segment_id'])})
    np.savez(out_dir / 'embeddings.npz', embeddings=embeddings,
             segment_ids=unique['segment_id'].to_numpy())

    print('Stage 4/4: exemplars and distractors')
    protos = selection.prototypes(pool, embeddings)
    pool['typicality'] = selection.typicality(pool, embeddings, protos)
    pool.to_csv(out_dir / 'pool.tsv', sep='\t', index=False)
    central, peripheral = selection.select_exemplars(pool)
    items = pd.concat([central, peripheral], ignore_index=True)
    items = selection.add_distractors(items, selection.prototype_similarities(protos),
                                      taxonomy, seed=args.seed)

    manifest = to_manifest(items, taxonomy)
    manifest.to_csv(out_dir / 'benchmark.tsv', sep='\t', index=False)
    print(f'  {len(central)} central + {len(peripheral)} peripheral items, '
          f'{manifest["label"].nunique()} ground-truth labels -> {out_dir / "benchmark.tsv"}')


if __name__ == '__main__':
    main()
