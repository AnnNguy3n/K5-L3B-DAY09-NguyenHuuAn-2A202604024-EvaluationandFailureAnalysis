"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import bootstrap

from collections.abc import Sequence

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """Count tp/fp/fn/tn with FAIL as positive; reject unpaired or invalid labels."""
    if len(human) != len(judge):
        raise ValueError("human and judge must have the same length")

    cm = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}

    for h, j in zip(human, judge):
        h, j = h.strip().upper(), j.strip().upper()

        if h not in {"PASS", "FAIL"} or j not in {"PASS", "FAIL"}:
            raise ValueError("labels must be PASS or FAIL")

        if h == POS:
            cm["tp" if j == POS else "fn"] += 1
        else:
            cm["fp" if j == POS else "tn"] += 1

    return cm


def precision_recall(
    human: Sequence[str], judge: Sequence[str]
) -> tuple[float, float]:
    """Return failure-detection precision and recall, using 0 for an empty denominator."""
    cm = confusion(human, judge)

    p_denom = cm["tp"] + cm["fp"]
    r_denom = cm["tp"] + cm["fn"]

    precision = cm["tp"] / p_denom if p_denom else 0.0
    recall = cm["tp"] / r_denom if r_denom else 0.0

    return precision, recall


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """Agreement beyond chance; empty data or expected agreement 1 is undefined."""
    cm = confusion(human, judge)
    n = sum(cm.values())

    if n == 0:
        raise ValueError("kappa is undefined for empty data")

    observed = (cm["tp"] + cm["tn"]) / n

    human_fail = (cm["tp"] + cm["fn"]) / n
    judge_fail = (cm["tp"] + cm["fp"]) / n

    expected = (
        human_fail * judge_fail
        + (1 - human_fail) * (1 - judge_fail)
    )

    if expected == 1.0:
        raise ValueError(
            "kappa is undefined when expected agreement is 1"
        )

    return (observed - expected) / (1 - expected)


def rogan_gladen(
    observed_rate: float,
    sensitivity: float,
    specificity: float,
) -> float:
    """Correct the observed failure rate, clip to [0, 1], and reject an undefined correction."""
    if not all(
        0 <= x <= 1
        for x in (observed_rate, sensitivity, specificity)
    ):
        raise ValueError("rates must be in [0, 1]")

    denominator = sensitivity + specificity - 1

    if denominator == 0:
        raise ValueError(
            "Rogan-Gladen is undefined when "
            "sensitivity + specificity = 1"
        )

    corrected = (
        observed_rate + specificity - 1
    ) / denominator

    return min(1.0, max(0.0, corrected))


def paired_bootstrap(
    a: Sequence[float],
    b: Sequence[float],
    *,
    n_resamples: int = 1000,
    rng: int = 2027,
    confidence: float = 0.95,
) -> tuple[float, float, float]:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)

    if (
        a.ndim != 1
        or b.ndim != 1
        or a.shape != b.shape
        or a.size == 0
    ):
        raise ValueError(
            "a and b must be non-empty, paired 1-D arrays"
        )

    if not (np.isfinite(a).all() and np.isfinite(b).all()):
        raise ValueError("a and b must contain finite values")

    if n_resamples <= 0 or not 0 < confidence < 1:
        raise ValueError("invalid n_resamples or confidence")

    if np.array_equal(a, b):
        return 0.0, 0.0, 0.0

    if a.size < 2:
        raise ValueError(
            "bootstrap requires at least two item pairs"
        )

    def difference(x, y, axis=-1):
        return np.mean(x, axis=axis) - np.mean(y, axis=axis)

    result = bootstrap(
        (a, b),
        difference,
        paired=True,
        vectorized=True,
        n_resamples=n_resamples,
        confidence_level=confidence,
        method="percentile",
        rng=np.random.default_rng(rng),
    )

    return (
        float(difference(a, b)),
        float(result.confidence_interval.low),
        float(result.confidence_interval.high),
    )


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    # TODO M6
    raise NotImplementedError


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    # TODO M6
    raise NotImplementedError
