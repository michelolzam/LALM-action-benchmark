"""The audible part of the SALT action taxonomy, as used to build the benchmark.

Files in `data/taxonomy/`:

    audibility_ratings.tsv  two-round audibility rating of every SALT action label
    taxonomy_nodes.tsv      the 99 labels that passed both rounds, with their
                            parents / children in the full SALT taxonomy and
                            their audible ancestors
    label_mapping.tsv       Ego4D / Ego-Exo4D annotation label -> SALT label, and
                            the audible labels a clip with that annotation counts
                            towards (the fine label and its audible ancestors)
"""
from pathlib import Path

import pandas as pd

TAXONOMY_DIR = Path(__file__).resolve().parents[2] / 'data' / 'taxonomy'


def _split(value):
    return value.split('|') if value else []


class Taxonomy:
    def __init__(self, taxonomy_dir=TAXONOMY_DIR):
        taxonomy_dir = Path(taxonomy_dir)
        nodes = pd.read_csv(taxonomy_dir / 'taxonomy_nodes.tsv', sep='\t', keep_default_na=False)
        mapping = pd.read_csv(taxonomy_dir / 'label_mapping.tsv', sep='\t', keep_default_na=False)

        self.labels = nodes['label'].tolist()
        self.roots = set(nodes.loc[nodes['is_root'], 'label'])
        self._parents = dict(zip(nodes['label'], nodes['parents'].map(_split)))
        self._children = dict(zip(nodes['label'], nodes['children'].map(_split)))
        self._benchmark_labels = {
            (row.dataset, row.dataset_label): _split(row.benchmark_labels)
            for row in mapping.itertuples()
        }

    def parents(self, label):
        """Parent label(s) in the full SALT taxonomy (empty for roots)."""
        return self._parents[label]

    def children(self, label):
        """Child labels in the full SALT taxonomy."""
        return self._children[label]

    def benchmark_labels(self, dataset, dataset_label):
        """Audible SALT labels a clip annotated with `dataset_label` counts towards.

        A clip counts towards its own (fine) SALT label and towards every audible
        coarser label, e.g. a clip of `stirring/mixing_food` is also a clip of
        `general_cooking_actions`, `cooking/preparing_food`, ...
        Returns an empty list for annotation labels outside the taxonomy.
        """
        return self._benchmark_labels.get((dataset, dataset_label), [])
