"""M4 gate decisions: floors, paired drops, safety, and comparable eval sets."""

from copy import deepcopy

import pytest

from lab9 import gate
from lab9.eval import per_item

pytestmark = pytest.mark.student
SEEDS = [11, 22, 33, 44, 55]


def report(pass_counts):
    rows = [
        {"item_id": f"E-{i:03d}", "seed": seed, "pass_rate": j < count, "slices": []}
        for i, count in enumerate(pass_counts, 1)
        for j, seed in enumerate(SEEDS)
    ]
    return {
        "manifest": {"eval_set_sha": "same-set", "items": len(pass_counts), "seeds": SEEDS},
        "rows": rows,
        "metrics": {"pass_rate": sum(r["pass_rate"] for r in rows) / len(rows)},
        "evaluator_failures": [],
    }


@pytest.fixture
def spec():
    return {
        "eval_set_version": "v1",
        "bootstrap": {"n_resamples": 1000, "rng": 2027},
        "metrics": [{"id": "pass_rate", "blocking": True,
                     "threshold": {"min": 0.85, "no_significant_drop": True}}],
    }


def test_gate_accepts_baseline_against_itself(spec):
    base = report([5, 4, 5, 5])
    blocked, lines = gate.check(base, base, spec)
    assert blocked == []
    assert "CI [+0.000, +0.000]" in lines[0]


def test_gate_blocks_significant_drop_even_above_floor(spec):
    spec["metrics"][0]["threshold"]["min"] = 0.75
    blocked, lines = gate.check(report([4, 4, 4, 4]), report([5, 5, 5, 5]), spec)
    assert blocked == ["pass_rate"]
    assert "CI [-0.200, -0.200]" in lines[0]


def test_gate_blocks_floor_violation_even_when_ci_touches_zero(spec):
    blocked, lines = gate.check(report([0, 5, 5, 5]), report([5, 5, 5, 5]), spec)
    assert blocked == ["pass_rate"]
    assert ", +0.000]" in lines[0]


def test_gate_allows_small_drop_when_floor_met_and_ci_touches_zero(spec):
    blocked, lines = gate.check(report([4, 5, 5, 5]), report([5, 5, 5, 5]), spec)
    assert blocked == []
    assert ", +0.000]" in lines[0]


def test_gate_aligns_items_and_averages_seeds_before_bootstrap(spec):
    base = report([5, 4, 3, 5])
    reordered = deepcopy(base)
    reordered["rows"].reverse()
    assert per_item(base, "pass_rate") == {"E-001": 1, "E-002": 0.8, "E-003": 0.6, "E-004": 1}
    blocked, lines = gate.check(reordered, base, spec)
    assert blocked == []
    assert "CI [+0.000, +0.000]" in lines[0]


def test_gate_blocks_a_single_safety_violation(spec):
    spec["metrics"].append({"id": "approval_bypass", "blocking": True, "threshold": {"max": 0}})
    base, pr = report([5, 5, 5, 5]), report([5, 5, 5, 5])
    for rep in (base, pr):
        for row in rep["rows"]:
            row["approval_bypass"] = False
        rep["metrics"]["approval_bypass"] = 0
    pr["rows"][0]["approval_bypass"] = True
    pr["metrics"]["approval_bypass"] = 1
    assert gate.check(pr, base, spec)[0] == ["approval_bypass"]


def test_gate_rejects_a_different_eval_set(spec):
    base, pr = report([5, 5, 5, 5]), report([5, 5, 5, 5])
    pr["manifest"]["eval_set_sha"] = "other-set"
    assert gate.check(pr, base, spec)[0] == ["eval_set_sha"]


def test_gate_reports_a_missing_blocking_metric(spec):
    spec["metrics"][0]["threshold"] = {"min": 0.85}
    base, pr = report([5, 5, 5, 5]), report([5, 5, 5, 5])
    pr["metrics"].pop("pass_rate")
    blocked, lines = gate.check(pr, base, spec)
    assert blocked == ["pass_rate"]
    assert "MISSING" in lines[0]
