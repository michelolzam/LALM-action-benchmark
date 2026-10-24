"""Stage 4: select central / peripheral exemplars and sample distractor labels.

Prototypes. The prototype of a label is the mean CLAP embedding of all its
pool rows (a clip counts for its fine label and its audible coarser labels, so
coarse prototypes also summarise the clips of their descendants).

Typicality. The typicality of a clip for a label is the cosine similarity
between the clip embedding and the label prototype. Ranking by cosine
similarity is the same as ranking by l2 distance between l2-normalised
embeddings.

Exemplars (per label):
  1. drop outliers, i.e. clips with typicality below mean - 2 std;
  2. central candidates are the clips above the (recomputed) mean typicality,
     most typical first; peripheral candidates are the clips below it, least
     typical first (ties broken by longer duration);
  3. keep at most one clip per recording (`dedup_group`) and at most 20 clips;
  4. a label becomes a ground truth of a split only if it keeps more than 5
     clips in that split.

Distractors (per item). The labels with a prototype are ranked by prototype
similarity to the ground truth: most similar first for *near* distractors,
least similar first for *distant* ones. Walking down the ranking, a label is
skipped if it is hierarchically adjacent to the ground truth or to an already
accepted candidate (a parent or a child). The first 12 accepted labels form
the candidate set, from which 3 distractors are drawn at random. In the
"no roots" variant, used by the hierarchical protocols, root labels are never
candidates.
"""
import random

import numpy as np
import pandas as pd

MAX_PER_LABEL = 20
MIN_PER_LABEL = 5
N_DISTRACTORS = 3
CANDIDATE_POOL_SIZE = 12


def prototypes(pool, embeddings):
    """Mean embedding per label. `pool` rows index `embeddings` via `embedding_idx`."""
    return {label: embeddings[group['embedding_idx'].to_numpy()].mean(axis=0)
            for label, group in pool.groupby('label')}


def cosine(a, b):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    return (a * b).sum(-1) / (np.linalg.norm(a, axis=-1) * np.linalg.norm(b, axis=-1))


def typicality(pool, embeddings, protos):
    mu = np.stack([protos[label] for label in pool['label']])
    return cosine(embeddings[pool['embedding_idx'].to_numpy()], mu)


def select_exemplars(pool, max_per_label=MAX_PER_LABEL, min_per_label=MIN_PER_LABEL):
    """Return (central, peripheral) DataFrames. `pool` needs a `typicality` column."""
    central, peripheral = [], []
    for _, group in pool.groupby('label'):
        mean, std = group['typicality'].mean(), group['typicality'].std()
        group = group.loc[group['typicality'] >= mean - 2 * std]
        if group.empty:
            continue
        mean = group['typicality'].mean()

        above = group.loc[group['typicality'] > mean].sort_values(
            ['typicality', 'duration'], ascending=[False, False])
        below = group.loc[group['typicality'] < mean].sort_values(
            ['typicality', 'duration'], ascending=[True, False])
        central.append(above.drop_duplicates('dedup_group').head(max_per_label))
        peripheral.append(below.drop_duplicates('dedup_group').head(max_per_label))

    def enough_support(df):
        counts = df['label'].value_counts()
        return df.loc[df['label'].map(counts) > min_per_label].reset_index(drop=True)

    return (enough_support(pd.concat(central)).assign(exemplar_type='central'),
            enough_support(pd.concat(peripheral)).assign(exemplar_type='peripheral'))


def prototype_similarities(protos):
    """Square DataFrame of cosine similarities between label prototypes."""
    labels = sorted(protos)
    matrix = np.stack([protos[label] for label in labels]).astype(np.float64)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
    return pd.DataFrame(matrix @ matrix.T, index=labels, columns=labels)


def _adjacent(label, taxonomy):
    """Labels that may not appear next to `label`: its children and its parent.

    As in the original run, the parent is only excluded when it is unique;
    labels with two parents in SALT (8 of the 85 labels) exclude neither.
    """
    parents = taxonomy.parents(label)
    return set(taxonomy.children(label)) | (set(parents) if len(parents) == 1 else set())


def distractor_candidates(ground_truth, similarities, taxonomy, near,
                          include_root_labels=True, pool_size=CANDIDATE_POOL_SIZE):
    """The `pool_size` labels from which the distractors of `ground_truth` are drawn."""
    ranking = similarities[ground_truth].drop(ground_truth).sort_values(ascending=not near)
    excluded = _adjacent(ground_truth, taxonomy)
    if not include_root_labels:
        excluded |= taxonomy.roots

    candidates = []
    for label in ranking.index:
        if label in excluded:
            continue
        candidates.append(label)
        excluded |= _adjacent(label, taxonomy)
        if len(candidates) == pool_size:
            break
    return candidates


def sample_distractors(ground_truth, similarities, taxonomy, near, rng,
                       include_root_labels=True, n=N_DISTRACTORS):
    candidates = distractor_candidates(ground_truth, similarities, taxonomy, near,
                                       include_root_labels)
    if len(candidates) < n:
        raise ValueError(f'Only {len(candidates)} valid distractors for "{ground_truth}"')
    rng.shuffle(candidates)
    return rng.sample(candidates, n)


def add_distractors(items, similarities, taxonomy, seed=0):
    """Add the four distractor columns of the manifest to the benchmark items."""
    rng = random.Random(seed)
    items = items.copy()
    for include_roots, suffix in [(True, ''), (False, '_no_roots')]:
        for near, name in [(False, 'distant'), (True, 'near')]:
            items[f'distractors_{name}{suffix}'] = [
                sample_distractors(gt, similarities, taxonomy, near, rng, include_roots)
                for gt in items['label']]
    return items
