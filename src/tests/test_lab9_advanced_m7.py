"""M7: reject altered evidence while accepting valid reports and tighter rules."""

from copy import deepcopy

import pytest

from lab9 import gate

pytestmark = pytest.mark.student


@pytest.fixture
def evidence():
    spec = {
        "eval_set_version": "v2", "seeds": [11, 22],
        "metrics": [
            {"id": "pass_rate", "blocking": True,
             "threshold": {"min": 0.8, "no_significant_drop": True}},
            {"id": "approval_bypass", "blocking": True, "threshold": {"max": 0}},
            {"id": "cost_per_success", "threshold": {"max_increase": 0.1}},
        ],
        "slices": [{"name": "money_movement", "metric": "pass_rate", "min": 0.9,
                    "blocking": True, "no_significant_drop": True}],
    }
    report = {
        "manifest": {"eval_set_sha": "m7", "items": 2, "seeds": [11, 22]},
        "metrics": {"pass_rate": 1.0, "approval_bypass": 0, "cost_per_success": 1.0},
        "evaluator_failures": [],
        "rows": [{"item_id": item, "seed": seed, "pass_rate": True,
                  "approval_bypass": False, "slices": ["money_movement"]}
                 for item in ("E-1", "E-2") for seed in (11, 22)],
    }
    return report, spec


def test_valid_report_and_reordered_rows_merge(evidence):
    base, spec = evidence
    pr = deepcopy(base)
    pr["rows"].reverse()
    assert gate.integrity_check(pr, base, spec, spec) == []
    assert gate.check(pr, base, spec, spec)[0] == []


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), "1.0"])
def test_invalid_aggregate_blocks_even_when_monitoring(evidence, value):
    base, spec = evidence
    pr = deepcopy(base)
    pr["metrics"]["cost_per_success"] = value
    assert gate.check(pr, base, spec)[0] == ["integrity"]


@pytest.mark.parametrize("alteration", [
    "drop", "duplicate", "cherry_pick", "replace_seed", "relabel_slice",
    "grader_none", "grader_missing", "grader_nan", "evaluator_failure",
    "manifest_count", "duplicate_seed", "malformed_row",
])
def test_altered_evidence_blocks_with_integrity_reason(evidence, alteration):
    base, spec = evidence
    pr = deepcopy(base)
    if alteration == "drop":
        pr["rows"].pop()
    elif alteration == "duplicate":
        pr["rows"][-1] = deepcopy(pr["rows"][0])  # Total row count stays unchanged.
    elif alteration == "cherry_pick":
        pr["manifest"]["seeds"] = [11]
        pr["rows"] = [r for r in pr["rows"] if r["seed"] == 11]
    elif alteration == "replace_seed":
        pr["manifest"]["seeds"] = [11, 33]
        for row in pr["rows"]:
            if row["seed"] == 22:
                row["seed"] = 33
    elif alteration == "relabel_slice":
        for row in pr["rows"]:
            row["slices"] = []
    elif alteration == "grader_none":
        pr["rows"][0]["pass_rate"] = None
    elif alteration == "grader_missing":
        del pr["rows"][0]["pass_rate"]
    elif alteration == "grader_nan":
        pr["rows"][0]["pass_rate"] = float("nan")
    elif alteration == "evaluator_failure":
        pr["evaluator_failures"] = ["grader crashed"]  # Aggregates remain green.
    elif alteration == "manifest_count":
        pr["manifest"]["items"] = 3
    elif alteration == "duplicate_seed":
        pr["manifest"]["seeds"] = [11, 11]
    elif alteration == "malformed_row":
        del pr["rows"][0]["seed"]
    blocked, lines = gate.check(pr, base, spec)
    assert blocked == ["integrity"]
    assert all("INTEGRITY" in line for line in lines)


@pytest.mark.parametrize("section,index,field,value", [
    ("metrics", 0, "min", 0.5),
    ("metrics", 1, "max", 1),
    ("metrics", 2, "max_increase", 0.2),
    ("metrics", 0, "no_significant_drop", False),
    ("metrics", 0, "blocking", False),
    ("slices", 0, "min", 0.5),
    ("slices", 0, "no_significant_drop", False),
    ("slices", 0, "blocking", False),
])
def test_ratchet_blocks_looser_rule_despite_spec_version_bump(evidence, section, index, field, value):
    base, spec = evidence
    loose = deepcopy(spec)
    loose["metric_spec_version"] = "99.0"
    rule = loose[section][index]
    if section == "metrics" and field != "blocking":
        rule = rule["threshold"]
    rule[field] = value
    blocked, lines = gate.check(base, base, loose, spec)
    assert blocked == ["integrity"]
    assert any("ratchet" in line for line in lines)


@pytest.mark.parametrize("section", ["metrics", "slices"])
def test_ratchet_blocks_removed_rule(evidence, section):
    base, spec = evidence
    loose = deepcopy(spec)
    loose[section].pop(0)
    assert gate.integrity_check(base, base, loose, spec)


@pytest.mark.parametrize("field", ["min", "no_significant_drop"])
def test_ratchet_blocks_deleted_threshold(evidence, field):
    base, spec = evidence
    loose = deepcopy(spec)
    del loose["metrics"][0]["threshold"][field]
    assert gate.integrity_check(base, base, loose, spec)


def test_tighter_rules_and_false_grader_values_are_valid(evidence):
    base, spec = evidence
    tighter = deepcopy(spec)
    tighter["metrics"][0]["threshold"]["min"] = 0.9
    tighter["metrics"][2]["threshold"]["max_increase"] = 0.05
    tighter["slices"][0]["min"] = 0.95
    assert gate.integrity_check(base, base, tighter, spec) == []
    failed = deepcopy(base)
    failed["rows"][0]["pass_rate"] = False
    failed["metrics"]["pass_rate"] = 0.75
    assert gate.integrity_check(failed, base, spec) == []
    assert "pass_rate" in gate.check(failed, base, spec)[0]
