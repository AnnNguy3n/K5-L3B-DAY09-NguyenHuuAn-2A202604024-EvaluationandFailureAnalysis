"""M6: independent draw counts, input validation, item aggregation and gate."""

from itertools import combinations
from pathlib import Path

import numpy as np
import pytest

from lab9 import gate, stats
from lab9.eval import aggregate, load_spec

pytestmark = pytest.mark.student


@pytest.mark.parametrize("n", [1, 2, 5, 7])
def test_estimators_match_enumerated_draws(n):
    for c in range(n + 1):
        for k in range(1, n + 1):
            draws = list(combinations(range(n), k))
            successes = [sum(i < c for i in draw) for draw in draws]
            at = stats.pass_at_k(n, c, k)
            hat = stats.pass_hat_k(n, c, k)
            assert at == pytest.approx(sum(s > 0 for s in successes) / len(draws))
            assert hat == pytest.approx(sum(s == k for s in successes) / len(draws))
            assert 0 <= hat <= c / n + 1e-12
            assert c / n <= at + 1e-12 <= 1 + 1e-12


@pytest.mark.parametrize("estimate", [stats.pass_at_k, stats.pass_hat_k])
def test_both_estimators_reject_invalid_inputs(estimate):
    for args in [
        (0, 0, 1), (-1, 0, 1), (5, -1, 1), (5, 6, 1),
        (5, 2, 0), (5, 2, -1), (5, 2, 6),
        (5.0, 2, 1), (5, 2.0, 1), (5, 2, 1.5),
        (True, 1, 1), (5, False, 1), (5, 2, True),
        ("5", 2, 1), (5, None, 1), (5, 2, float("nan")),
    ]:
        with pytest.raises(ValueError):
            estimate(*args)
    assert estimate(np.int64(5), np.int64(4), np.int64(1)) == pytest.approx(0.8)


def _report(counts):
    rows = [
        {"item_id": f"E-{i}", "seed": seed, "pass_rate": seed <= count, "cost": 0.0}
        for i, count in enumerate(counts) for seed in range(1, 6)
    ]
    return {
        "manifest": {"eval_set_sha": "m6-test", "items": len(counts), "seeds": [1, 2, 3, 4, 5]},
        "rows": rows,
        "metrics": aggregate(rows, ["pass_rate"], k_values=[1, 3, 5]),
        "evaluator_failures": [],
    }


def test_aggregation_averages_item_estimates_instead_of_pooling_trials():
    metrics = _report([5, 4])["metrics"]
    assert metrics["pass_at_1"] == metrics["pass_hat_1"] == 0.9
    assert metrics["pass_at_3"] == metrics["pass_at_5"] == 1.0
    assert metrics["pass_hat_3"] == 0.7
    assert metrics["pass_hat_5"] == metrics["pass_5"] == 0.5


def test_pass_hat_gate_blocks_flakiness_above_pass_rate_floor():
    real_spec = load_spec(Path("config/metric_spec_v2.yaml"))
    rule = next(m for m in real_spec["metrics"] if m["id"] == "pass_hat_5")
    assert rule["blocking"] and rule["threshold"]["min"] >= 0.8
    spec = {"metrics": [
        {"id": "pass_rate", "threshold": {"min": 0.85}, "blocking": True}, rule,
    ]}
    base = _report([5] * 5)
    assert gate.check(base, base, spec)[0] == []
    assert gate.check(_report([5, 5, 5, 5, 4]), base, spec)[0] == []
    flaky = _report([5, 5, 5, 4, 4])
    assert flaky["metrics"]["pass_rate"] > 0.85
    assert gate.check(flaky, base, spec)[0] == ["pass_hat_5"]
