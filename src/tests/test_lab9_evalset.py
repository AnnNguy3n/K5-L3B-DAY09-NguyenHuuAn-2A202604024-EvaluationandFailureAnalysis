"""M0 command-line checks run before completing the M1 taxonomy."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.fixture
def evalset_cli(tmp_path):
    source = tmp_path / "data/public_claims.jsonl"
    source.parent.mkdir()
    claim = {"claim_id": "C-001", "matrix_id": "T01", "expected": {"refund_vnd": 35000}}
    source.write_text(json.dumps(claim) + "\n", encoding="utf-8")

    def run_evalset(*args):
        return subprocess.run(
            [sys.executable, "-m", "lab9.evalset", *args],
            cwd=tmp_path,
            env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
            capture_output=True,
            text=True,
        )

    return run_evalset


def test_build_writes_items_and_labels_without_checking_tags(tmp_path, evalset_cli):
    result = evalset_cli("--build")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "problem(s)" not in result.stdout
    item = json.loads((tmp_path / "data/eval/eval_set_v1.jsonl").read_text(encoding="utf-8"))
    labels = json.loads((tmp_path / "data/eval/labels_v1.json").read_text(encoding="utf-8"))
    assert item["claim_id"] == "C-001"
    assert "expected" not in item
    assert labels == {"C-001": {"refund_vnd": 35000}}


def test_explicit_check_runs_after_build(tmp_path, evalset_cli):
    result = evalset_cli("--build", "--check")
    item = json.loads((tmp_path / "data/eval/eval_set_v1.jsonl").read_text(encoding="utf-8"))
    expected_problems = int(not item["failure_modes"])
    assert result.returncode == expected_problems, result.stdout + result.stderr
    assert f"{expected_problems} problem(s)" in result.stdout


def test_check_rejects_missing_tags(tmp_path, evalset_cli):
    evalset_cli("--build")
    items_path = tmp_path / "data/eval/eval_set_v1.jsonl"
    item = json.loads(items_path.read_text(encoding="utf-8"))
    item["failure_modes"] = []
    items_path.write_text(json.dumps(item) + "\n", encoding="utf-8")

    result = evalset_cli("--check")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "failure_modes empty" in result.stdout


@pytest.mark.student
def test_public_build_preserves_coverage_provenance_and_separate_labels(tmp_path, monkeypatch):
    from lab9 import evalset

    source = Path(__file__).resolve().parents[1] / "data/public_claims.jsonl"
    claims = evalset.load_jsonl(source)
    items_path, labels_path = tmp_path / "items.jsonl", tmp_path / "labels.json"
    monkeypatch.setattr(evalset, "ITEMS", items_path)
    monkeypatch.setattr(evalset, "LABELS", labels_path)

    assert evalset.build(source) == (len(claims), len(claims))
    first_build = (items_path.read_bytes(), labels_path.read_bytes())
    evalset.build(source)
    assert (items_path.read_bytes(), labels_path.read_bytes()) == first_build
    assert evalset.check(items_path, labels_path) == []

    items = evalset.load_jsonl(items_path)
    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    assert {item["claim_id"] for item in items} == {claim["claim_id"] for claim in claims}
    assert labels == {claim["claim_id"]: claim["expected"] for claim in claims}
    for item, claim in zip(items, claims):
        assert item["failure_modes"]
        assert "expected" not in item and "label" not in item
        assert item["provenance"]["matrix_id"] == claim["matrix_id"]
        assert item["provenance"]["checked_by"]
