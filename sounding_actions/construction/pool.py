"""Stage 2: extract the segment audio and keep the segments usable as exemplars.

Starting from the segments of stage 1, a segment enters the candidate pool if

  1. its annotation maps to an audible label of the taxonomy. The segment is
     then counted for its fine label *and* all audible coarser labels, i.e.
     the pool has one row per (segment, label) pair;
  2. it carries a single annotation label (segments whose audio file received
     several different annotation labels are dropped);
  3. its audio lasts more than 5 s;
  4. its audio is not digital silence.

The order matters: the single-label check (2) is applied after (1), so only
annotations that map into the audible taxonomy are taken into account.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import soundfile as sf
from tqdm import tqdm

from ..extraction import extract_clip, source_video_path

MIN_DURATION_SEC = 5


def extract_segments(segments, audio_dir, ego4d_root, egoexo4d_root, workers=8):
    """Extract each segment to `<audio_dir>/<segment_id>.flac`.

    Adds the columns `audio_path`, `duration` (seconds) and `silent`. Segments
    whose video has no audio stream get `duration = NaN`.
    """
    audio_dir = Path(audio_dir)
    unique = segments.drop_duplicates('segment_id').set_index('segment_id')

    def process(segment_id):
        seg = unique.loc[segment_id]
        video = source_video_path(seg['dataset'], seg['source_video'], ego4d_root, egoexo4d_root)
        audio_path = audio_dir / f'{segment_id}.flac'
        try:
            extract_clip(video, audio_path, seg['start_sec'], seg['end_sec'])
            audio, sample_rate = sf.read(str(audio_path))
        except RuntimeError:  # no audio stream in the video / unreadable file
            return segment_id, str(audio_path), np.nan, True
        return segment_id, str(audio_path), len(audio) / sample_rate, not np.any(audio)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(tqdm(pool.map(process, unique.index), total=len(unique),
                            desc='Extracting segments'))
    info = pd.DataFrame(results, columns=['segment_id', 'audio_path', 'duration', 'silent'])
    return segments.merge(info, on='segment_id', how='left')


def build_pool(segments, taxonomy):
    """Apply the filters above to extracted segments; one row per (segment, label)."""
    df = segments.copy()

    # 1. Map annotation labels to audible taxonomy labels (fine + coarser labels)
    df['label'] = [taxonomy.benchmark_labels(ds, lbl)
                   for ds, lbl in zip(df['dataset'], df['dataset_label'])]
    df = df.explode('label').dropna(subset=['label'])
    df = df.drop_duplicates(['segment_id', 'dataset_label', 'label'])

    # 2. Single annotation label per audio segment
    n_labels = df.groupby('segment_id')['dataset_label'].nunique()
    df = df.loc[df['segment_id'].map(n_labels) == 1]

    # 3. + 4. Long enough and not silent
    df = df.loc[(df['duration'] > MIN_DURATION_SEC) & ~df['silent'].astype(bool)]

    return df.drop_duplicates(['segment_id', 'label']).reset_index(drop=True)
