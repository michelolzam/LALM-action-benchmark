"""Load the benchmark manifest and assemble the items of each evaluation condition.

The manifest (`data/benchmark.tsv`) has one row per benchmark item. An item is
an audio clip, its ground-truth label and two sets of three distractor labels:
acoustically *distant* ones and acoustically *near* ones. Crossing the exemplar
type of the clip with the distractor type gives the four conditions of the paper:

    condition  exemplar     distractors   difficulty
    C-Dist     central      distant       easiest
    C-Near     central      near
    P-Dist     peripheral   distant
    P-Near     peripheral   near          hardest
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
BENCHMARK_TSV = DATA_DIR / 'benchmark.tsv'
LABELS_TSV = DATA_DIR / 'labels.tsv'

LIST_SEPARATOR = '|'
LIST_COLUMNS = ['coarse_labels', 'distractors_distant', 'distractors_near',
                'distractors_distant_no_roots', 'distractors_near_no_roots']


@dataclass(frozen=True)
class Condition:
    name: str
    exemplar_type: str  # 'central' or 'peripheral'
    distractor_type: str  # 'distant' or 'near'
    internal_name: str  # benchmark name used in the raw experiment outputs


CONDITIONS = {
    c.name: c for c in [
        Condition('C-Dist', 'central', 'distant', internal_name='easy'),
        Condition('C-Near', 'central', 'near', internal_name='medium'),
        Condition('P-Dist', 'peripheral', 'distant', internal_name='challenging'),
        Condition('P-Near', 'peripheral', 'near', internal_name='hard'),
    ]
}


def _split(value: str) -> list:
    return value.split(LIST_SEPARATOR) if value else []


def make_clip_id(dataset: str, source_uid: str, take_name: str,
                 start_sec: float, end_sec: float) -> str:
    """Id of an audio clip: `<dataset>_<video uid or take name>_<start>_<end>`.

    Items that use the same window of the same source video share one clip."""
    if dataset == 'Ego4D':
        return f'ego4d_{source_uid}_{start_sec:.6f}_{end_sec:.6f}'
    return f'egoexo4d_{take_name}_{start_sec:.6f}_{end_sec:.6f}'


def load_benchmark(path: Union[str, Path] = BENCHMARK_TSV) -> pd.DataFrame:
    """Read a benchmark manifest; list-valued columns are returned as Python lists.

    Works both for the released manifest and for the manifest written by
    `scripts/build_benchmark.py` (which adds an `audio_path` column).
    """
    df = pd.read_csv(path, sep='\t', keep_default_na=False, float_precision='round_trip')
    for col in LIST_COLUMNS:
        df[col] = df[col].map(_split)
    return df


def load_labels(path: Union[str, Path] = LABELS_TSV) -> pd.DataFrame:
    """Read the label table (label space of 85 labels with statistics and flags)."""
    df = pd.read_csv(path, sep='\t', keep_default_na=False)
    df['coarse_labels'] = df['coarse_labels'].map(_split)
    return df


def condition_items(benchmark: pd.DataFrame,
                    condition: str,
                    hierarchical: bool = False,
                    include_root_labels: Optional[bool] = None) -> pd.DataFrame:
    """Items of one condition, with the candidate labels in an `options` column.

    Parameters
    ----------
    benchmark
        Output of `load_benchmark`.
    condition
        One of 'C-Dist', 'C-Near', 'P-Dist', 'P-Near'.
    hierarchical
        Use the settings of the hierarchical protocols (H1, H2) and of the
        open-ended protocol (P3): items whose ground truth is a root label are
        dropped and distractors are drawn without root labels. The flat
        closed-set protocols (P1, P2) use `hierarchical=False`.
    include_root_labels
        Override which distractor set is used. By default, the distractor set
        with root labels is used for flat protocols and the one without root
        labels for hierarchical protocols.

    Returns
    -------
    pd.DataFrame
        One row per item. `options` holds the three distractors followed by
        the ground truth; shuffle them before building a prompt.
    """
    cond = CONDITIONS[condition]
    if include_root_labels is None:
        include_root_labels = not hierarchical

    items = benchmark.loc[benchmark['exemplar_type'] == cond.exemplar_type].copy()
    if hierarchical:
        # Root labels have no coarser category to predict.
        items = items.loc[items['coarse_labels'].map(len) > 0]

    column = f'distractors_{cond.distractor_type}'
    if not include_root_labels:
        column += '_no_roots'
    items['distractors'] = items[column]
    items['options'] = [d + [gt] for d, gt in zip(items['distractors'], items['label'])]
    items['condition'] = cond.name
    return items.reset_index(drop=True)
