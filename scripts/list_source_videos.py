"""List the Ego4D videos and Ego-Exo4D takes to download, and print the download commands.

The official downloaders come with `pip install ego4d` (`ego4d` and `egoexo` CLIs).

To rebuild the released benchmark (198 Ego4D videos, 220 Ego-Exo4D takes):

    python scripts/list_source_videos.py --out-dir downloads/

To re-run the construction pipeline (all Ego4D videos of the Moments `val`
split, read from the Moments annotations, and the Ego-Exo4D `test` split):

    python scripts/list_source_videos.py --out-dir downloads/ --construction --ego4d-root /data/ego4d
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sounding_actions.benchmark import BENCHMARK_TSV, load_benchmark  # noqa: E402

HELP = ('\nThe profile names are those of your AWS credentials; see '
        'docs/downloading_sources.md for access, credentials and download sizes.')


def write_uids(path, uids):
    path.write_text('\n'.join(sorted(uids)) + '\n')
    print(f'{len(uids)} uids -> {path}')


def benchmark_sources(manifest, out_dir):
    benchmark = load_benchmark(manifest)
    ego4d_file = out_dir / 'ego4d_video_uids.txt'
    egoexo4d_file = out_dir / 'egoexo4d_take_uids.txt'
    write_uids(ego4d_file, set(benchmark.loc[benchmark['dataset'] == 'Ego4D', 'source_uid']))
    write_uids(egoexo4d_file, set(benchmark.loc[benchmark['dataset'] == 'Ego-Exo4D', 'source_uid']))

    print('\nDownload commands (Ego4D / Ego-Exo4D licenses required):\n')
    print(f'  ego4d --output_directory <EGO4D_ROOT> --datasets full_scale '
          f'--video_uid_file {ego4d_file} --aws_profile_name ego4d')
    print(f'  egoexo -o <EGOEXO4D_ROOT> --parts takes --views ego '
          f'--uids $(cat {egoexo4d_file}) --s3_profile egoexo')
    print(HELP)


def construction_sources(ego4d_root, out_dir):
    annotations = Path(ego4d_root) / 'v2' / 'annotations' / 'moments_val.json'
    if not annotations.is_file():
        print(f'{annotations} not found. Download the annotations first:\n\n'
              f'  ego4d --output_directory {ego4d_root} --datasets annotations '
              f'--aws_profile_name ego4d')
        sys.exit(1)
    with open(annotations) as f:
        videos = json.load(f)['videos']
    ego4d_file = out_dir / 'ego4d_moments_val_video_uids.txt'
    write_uids(ego4d_file, {video['video_uid'] for video in videos})

    print('\nDownload commands (Ego4D / Ego-Exo4D licenses required):\n')
    print(f'  ego4d --output_directory {ego4d_root} --datasets full_scale '
          f'--video_uid_file {ego4d_file} --aws_profile_name ego4d')
    print('  egoexo -o <EGOEXO4D_ROOT> --parts metadata annotations takes '
          '--views ego --splits test --s3_profile egoexo')
    print(HELP)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--out-dir', default='.', help='Where to write the UID lists')
    parser.add_argument('--manifest', default=BENCHMARK_TSV, help='Benchmark manifest (TSV)')
    parser.add_argument('--construction', action='store_true',
                        help='List the sources of the construction pipeline instead')
    parser.add_argument('--ego4d-root', help='Ego4D download directory (with --construction)')
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.construction:
        if not args.ego4d_root:
            parser.error('--construction needs --ego4d-root')
        construction_sources(args.ego4d_root, out_dir)
    else:
        benchmark_sources(args.manifest, out_dir)


if __name__ == '__main__':
    main()
