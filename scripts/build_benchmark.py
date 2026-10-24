"""Rebuild the benchmark audio from local copies of Ego4D and Ego-Exo4D.

For every clip in the manifest, the audio between `start_sec` and `end_sec` of
the source video is written to `<out>/audio/<clip_id>.flac`. The script then
checks each clip against the sampling rate, channel count and sample count
recorded when the benchmark was created, and writes a copy of the manifest with
an extra `audio_path` column to `<out>/benchmark.tsv`.

    python scripts/build_benchmark.py \
        --ego4d-root /data/ego4d --egoexo4d-root /data/egoexo4d --out benchmark/

The script is idempotent: clips that already exist are not extracted again.
"""
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sounding_actions.benchmark import BENCHMARK_TSV, LIST_COLUMNS, LIST_SEPARATOR, load_benchmark  # noqa: E402
from sounding_actions.extraction import audio_info, extract_clip, source_video_path  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--ego4d-root', required=True,
                        help='Output directory of the `ego4d` downloader (contains v2/full_scale/)')
    parser.add_argument('--egoexo4d-root', required=True,
                        help='Output directory of the `egoexo` downloader (contains takes/)')
    parser.add_argument('--out', required=True, help='Output directory for the benchmark')
    parser.add_argument('--manifest', default=BENCHMARK_TSV, help='Benchmark manifest (TSV)')
    parser.add_argument('--workers', type=int, default=8, help='Parallel ffmpeg processes')
    return parser.parse_args()


def main():
    args = parse_args()
    out_dir = Path(args.out)
    benchmark = load_benchmark(args.manifest)

    # Several items can share the same audio clip (e.g. a clip that is an
    # exemplar of both a label and its parent label): extract each clip once.
    clips = benchmark.drop_duplicates('clip_id').set_index('clip_id')
    clips['video_path'] = [source_video_path(row.dataset, row.source_video,
                                             args.ego4d_root, args.egoexo4d_root)
                           for row in clips.itertuples()]
    clips['audio_path'] = [out_dir / 'audio' / f'{clip_id}.flac' for clip_id in clips.index]

    missing_videos = sorted({str(p) for p in clips['video_path'] if not p.is_file()})
    if missing_videos:
        print(f'{len(missing_videos)} source videos are missing, e.g.:')
        print('\n'.join(f'  {p}' for p in missing_videos[:5]))
        print('Run `python scripts/list_source_videos.py` to see the download commands.')
        sys.exit(1)

    def process(clip_id):
        clip = clips.loc[clip_id]
        try:
            extract_clip(clip['video_path'], clip['audio_path'], clip['start_sec'], clip['end_sec'])
        except RuntimeError as err:
            return clip_id, str(err)
        found = audio_info(clip['audio_path'])
        expected = {k: int(clip[k]) for k in found}
        return clip_id, None if found == expected else f'expected {expected}, got {found}'

    print(f'Extracting {len(clips)} clips for {len(benchmark)} benchmark items ...')
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(tqdm(pool.map(process, clips.index), total=len(clips)))
    problems = {clip_id: msg for clip_id, msg in results if msg}

    benchmark['audio_path'] = [str(clips.loc[c, 'audio_path'].relative_to(out_dir))
                               for c in benchmark['clip_id']]
    for col in LIST_COLUMNS:
        benchmark[col] = benchmark[col].map(LIST_SEPARATOR.join)
    benchmark.to_csv(out_dir / 'benchmark.tsv', sep='\t', index=False)

    if problems:
        print(f'\n{len(problems)} clips failed verification:')
        for clip_id, msg in list(problems.items())[:20]:
            print(f'  {clip_id}: {msg}')
        sys.exit(1)
    print(f'\nDone: {len(clips)} clips verified. Manifest with audio paths: {out_dir / "benchmark.tsv"}')


if __name__ == '__main__':
    main()
