"""Stage 1: cut the annotated activity intervals into segments of at most 10 s.

Sources (held-out splits only, so that no training data is used):

    Ego4D      Moments Queries annotations of the `val` split
               (<ego4d_root>/v2/annotations/moments_val.json). Every annotated
               moment is an interval of a video with one activity label.
    Ego-Exo4D  takes of the `test` split (<egoexo4d_root>/annotations/splits.json).
               Every take is one activity (`task_name`) performed between
               `task_start_sec` and `task_end_sec` (<egoexo4d_root>/takes.json).

Each interval is cut into consecutive 10 s windows; the last window keeps the
remainder (which is later dropped if it is not longer than 5 s).

Columns of the returned segment tables:

    segment_id     unique key of the audio segment. Two annotations that produce
                   the same key share the same audio file.
    dedup_group    recording identifier used to keep at most one exemplar per
                   recording and label. NOTE: for Ego4D the original run used
                   the annotator id (the prefix of the audio file name), not
                   the video id; this is reproduced here.
"""
import json
import math
from pathlib import Path

import pandas as pd

WINDOW_SEC = 10


def split_into_windows(start_sec, end_sec, window_sec=WINDOW_SEC):
    """[(start, end), ...] windows covering the interval, as in the original code."""
    if end_sec <= start_sec:  # zero-length annotation: nothing to cut
        return []
    if end_sec - start_sec <= window_sec:
        return [(start_sec, end_sec)]
    n_windows = math.ceil((end_sec - start_sec) / window_sec)
    windows = []
    for i in range(n_windows):
        seg_start = start_sec + i * window_sec
        windows.append((seg_start, min(seg_start + window_sec, end_sec)))
    return windows


def ego4d_segments(ego4d_root, split='val'):
    annotations = Path(ego4d_root) / 'v2' / 'annotations' / f'moments_{split}.json'
    with open(annotations) as f:
        videos = json.load(f)['videos']

    rows = []
    for video in videos:
        video_uid = video['video_uid']
        for clip in video['clips']:
            for annotation in clip['annotations']:
                annotator_uid = annotation['annotator_uid']
                for moment in annotation['labels']:
                    windows = split_into_windows(moment['video_start_time'],
                                                 moment['video_end_time'])
                    for start, end in windows:
                        rows.append({
                            'segment_id': f'{video_uid}/{annotator_uid}_{start:.3f}_{end:.3f}',
                            'dataset': 'Ego4D',
                            'source_uid': video_uid,
                            'take_name': '',
                            'source_video': f'v2/full_scale/{video_uid}.mp4',
                            'dedup_group': str(annotator_uid),
                            'dataset_label': moment['label'],
                            'start_sec': start,
                            'end_sec': end,
                        })
    return pd.DataFrame(rows)


def egoexo4d_segments(egoexo4d_root, split='test'):
    egoexo4d_root = Path(egoexo4d_root)
    with open(egoexo4d_root / 'annotations' / 'splits.json') as f:
        split_takes = set(json.load(f)['split_to_take_uids'][split])
    with open(egoexo4d_root / 'takes.json') as f:
        takes = json.load(f)

    rows = []
    for take in takes:
        if take['take_uid'] not in split_takes:
            continue
        if take['task_start_sec'] is None or take['task_end_sec'] is None:
            continue
        take_name = take['take_name']
        for start, end in split_into_windows(take['task_start_sec'], take['task_end_sec']):
            rows.append({
                'segment_id': f'{take_name}/{take_name}_{start:.3f}_{end:.3f}',
                'dataset': 'Ego-Exo4D',
                'source_uid': take['take_uid'],
                'take_name': take_name,
                'source_video': f'{take["root_dir"]}/ego_preview.mp4',
                'dedup_group': take_name,
                'dataset_label': take['task_name'],
                'start_sec': start,
                'end_sec': end,
            })
    return pd.DataFrame(rows)
