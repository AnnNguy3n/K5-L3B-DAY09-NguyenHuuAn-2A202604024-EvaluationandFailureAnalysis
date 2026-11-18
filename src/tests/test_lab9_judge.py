"""M2 calibration decisions, CLI exit codes, and degenerate-classifier regressions."""

import csv
import math
from pathlib import Path

import pytest

from lab9 import judge, stats

pytestmark = pytest.mark.student


@pytest.mark.parametrize(
    "filename,cm,kappa,precision,recall,observed,passed",
    [
        ("judge_tone_public.csv", {"tp": 24, "fp": 4, "fn": 6, "tn": 66},
         0.757, 0.857, 0.8, 0.28, True),
        ("judge_helpful_public.csv", {"tp": 9, "fp": 0, "fn": 21, "tn": 70},
         0.375, 1.0, 0.3, 0.09, False),
    ],
)
def test_public_calibration(filename, cm, kappa, precision, recall, observed, passed):
    result = judge.calibrate(Path("data/eval") / filename)
    assert result["n"] == 100
    assert result["confusion"] == cm
    assert result["kappa"] == kappa
    assert result["precision"] == precision
    assert result["recall"] == recall
    assert result["observed_fail_rate"] == observed
    assert result["corrected_fail_rate"] == 0.3
    assert len(result["disagreements"]) == cm["fp"] + cm["fn"]
    assert result["passed"] is passed


@pytest.mark.parametrize(
    "filename,status,verdict",
    [("judge_tone_public.csv", 0, "PASS floors"),
     ("judge_helpful_public.csv", 1, "FAIL floors")],
)
def test_judge_cli_exit_code(filename, status, verdict, capsys):
    assert judge.main(["--csv", str(Path("data/eval") / filename), "--audit", "5"]) == status
    assert verdict in capsys.readouterr().out


@pytest.mark.parametrize(
    "human,labels,undefined_kappa",
    [(["PASS", "PASS"], ["PASS", "PASS"], True),
     (["PASS", "FAIL"], ["PASS", "PASS"], False)],
)
def test_constant_judge_fails_calibration_without_crashing(
    human, labels, undefined_kappa, tmp_path, capsys
):
    path = tmp_path / "constant_judge.csv"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["item_id", "reply", "human", "judge"])
        writer.writeheader()
        for index, (h, j) in enumerate(zip(human, labels)):
            writer.writerow({"item_id": f"constant-{index}", "reply": "test", "human": h, "judge": j})

    result = judge.calibrate(path)
    assert result["passed"] is False
    assert math.isnan(result["corrected_fail_rate"])
    if undefined_kappa:
        assert math.isnan(result["kappa"])
    else:
        assert result["kappa"] == 0.0
    assert judge.main(["--csv", str(path)]) == 1
    assert "FAIL floors" in capsys.readouterr().out


@pytest.mark.parametrize("human,labels", [([], []), (["PASS"], ["PASS"])])
def test_precision_recall_without_positive_cases_is_zero(human, labels):
    assert stats.precision_recall(human, labels) == (0.0, 0.0)


@pytest.mark.parametrize(
    "human,labels",
    [(["PASS"], []), (["UNKNOWN"], ["PASS"]), (["PASS"], ["UNKNOWN"])],
)
def test_confusion_rejects_unusable_labels(human, labels):
    with pytest.raises(ValueError):
        stats.confusion(human, labels)


def test_confusion_normalizes_case_and_whitespace():
    assert stats.confusion(
        [" fail ", "pass", " Fail", " Pass"],
        [" fail ", "FAIL", " PASS ", " pass "],
    ) == {"tp": 1, "fp": 1, "fn": 1, "tn": 1}


def test_rogan_gladen_clips_upper_bound_and_rejects_undefined_correction():
    assert stats.rogan_gladen(1.0, 0.8, 0.9) == 1.0
    with pytest.raises(ValueError):
        stats.rogan_gladen(0.0, 0.0, 1.0)
