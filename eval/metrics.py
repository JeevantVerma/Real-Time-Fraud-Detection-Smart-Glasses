"""Shared detection metrics for every module (voice, face, document).

Convention everywhere: higher score = more likely genuine (bona fide).
Terminology follows ISO/IEC 30107-3:
  APCER = share of attacks accepted as genuine (score >  threshold)
  BPCER = share of genuine samples rejected  (score <= threshold)
(">" rather than ">=" matches the threshold semantics of det_curve, so a
threshold taken from eer() reproduces the EER operating point exactly.)

The EER computation mirrors the AASIST/ASVspoof reference implementation
(compute_det_curve / compute_eer) so our numbers match published ones exactly.
"""

import numpy as np


def det_curve(bona: np.ndarray, attack: np.ndarray):
    """Return (bpcer, apcer, thresholds) swept over every observed score."""
    n_bona, n_attack = bona.size, attack.size
    scores = np.concatenate((bona, attack))
    labels = np.concatenate((np.ones(n_bona), np.zeros(n_attack)))

    order = np.argsort(scores, kind="mergesort")
    labels = labels[order]

    tar_cumsum = np.cumsum(labels)
    nontarget_trial_sums = n_attack - (np.arange(1, n_bona + n_attack + 1) - tar_cumsum)

    bpcer = np.concatenate((np.atleast_1d(0), tar_cumsum / n_bona))
    apcer = np.concatenate((np.atleast_1d(1), nontarget_trial_sums / n_attack))
    thresholds = np.concatenate((np.atleast_1d(scores[order[0]] - 0.001), scores[order]))

    # Keep only real operating points: a threshold can't split tied scores, so
    # within a run of equal scores only the last position is reachable. No-op
    # for continuous model scores; matters for the heuristic's few discrete values.
    sorted_scores = scores[order]
    keep = np.concatenate(([True], np.append(sorted_scores[1:] != sorted_scores[:-1], True)))
    return bpcer[keep], apcer[keep], thresholds[keep]


def eer(bona: np.ndarray, attack: np.ndarray):
    """Equal Error Rate and the threshold where it occurs."""
    bpcer, apcer, thresholds = det_curve(bona, attack)
    idx = np.nanargmin(np.abs(bpcer - apcer))
    return float(np.mean((bpcer[idx], apcer[idx]))), float(thresholds[idx])


def rates_at(bona: np.ndarray, attack: np.ndarray, threshold: float):
    """(APCER, BPCER) at a fixed threshold."""
    apcer = float(np.mean(attack > threshold)) if attack.size else float("nan")
    bpcer = float(np.mean(bona <= threshold)) if bona.size else float("nan")
    return apcer, bpcer


def auc(bona: np.ndarray, attack: np.ndarray) -> float:
    """Probability a random genuine sample outscores a random attack (ties count half)."""
    scores = np.concatenate((bona, attack))
    ranks = _average_ranks(scores)
    return float((ranks[: bona.size].sum() - bona.size * (bona.size + 1) / 2) / (bona.size * attack.size))


def _average_ranks(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(x.size)
    sorted_x = x[order]
    i = 0
    while i < x.size:
        j = i
        while j + 1 < x.size and sorted_x[j + 1] == sorted_x[i]:
            j += 1
        ranks[order[i : j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def bootstrap_ci(metric, scores: np.ndarray, is_bona: np.ndarray, groups=None,
                 n_boot: int = 1000, alpha: float = 0.05, seed: int = 0):
    """Percentile bootstrap CI for metric(bona_scores, attack_scores) -> float.

    If `groups` (e.g. speaker IDs) is given, whole groups are resampled together
    (cluster bootstrap), which is the honest choice when one speaker contributes
    many clips. Otherwise samples are resampled within each class.
    """
    rng = np.random.default_rng(seed)
    stats = []
    if groups is not None:
        uniq, inverse = np.unique(groups, return_inverse=True)
        members = [np.flatnonzero(inverse == g) for g in range(uniq.size)]
        for _ in range(n_boot):
            pick = rng.integers(0, uniq.size, uniq.size)
            idx = np.concatenate([members[g] for g in pick])
            b, a = scores[idx][is_bona[idx]], scores[idx][~is_bona[idx]]
            if b.size and a.size:
                stats.append(metric(b, a))
    else:
        bona, attack = scores[is_bona], scores[~is_bona]
        for _ in range(n_boot):
            stats.append(metric(rng.choice(bona, bona.size), rng.choice(attack, attack.size)))
    lo, hi = np.percentile(stats, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)
