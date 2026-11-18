"""Reproduce M1-M7 and save one compact log using the active Python interpreter."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

SRC = Path(__file__).resolve().parents[1]
ROOT = SRC.parent
LOG = SRC / "reports/submission_validation.txt"


def main() -> int:
    lines = ["Minh chứng M1–M7 — Nguyễn Hữu An — 2A202604024",
             f"Python: {sys.version.split()[0]}; môi trường: {Path(sys.prefix).name}"]

    def run(args, expected=0, required=None, keep=None):
        result = subprocess.run([sys.executable, "-m", *args], cwd=SRC,
                                capture_output=True, text=True, timeout=180)
        output = result.stdout + result.stderr
        lines.append("\n$ python -m " + " ".join(args))
        lines.extend(line.rstrip() for line in output.splitlines()
                     if line.strip() and (keep is None or any(s in line for s in keep)))
        lines.append(f"exit {result.returncode} (yêu cầu {expected})")
        if result.returncode != expected or (required and required not in output):
            raise RuntimeError(f"Không đạt: {' '.join(args)}\n{output}")

    try:
        run(["lab9.smoke"], keep=["M0 PASS"])
        run(["pytest", "-q", "-m", "student", "-o", "addopts=", "-k", "lab9"], keep=["passed"])
        run(["lab9.evalset", "--check"])
        run(["lab9.evalset", "--v2"])
        run(["lab9.judge", "--csv", "data/eval/judge_tone_public.csv"], required="PASS floors")
        run(["lab9.judge", "--csv", "data/eval/judge_helpful_public.csv"], expected=1, required="FAIL floors")
        run(["lab9.mutation", "--detect"])

        for version, cases in (
            ("v1", [("swarm", "baseline_v1"), ("swarm", "eval_pr"),
                    ("fixed", "eval_fixed"), ("seeded_regression", "eval_seeded_regression")]),
            ("v2", [("swarm", "baseline_v2"), *[(shape, f"eval_{shape}_v2") for shape in
                    ("fixed", "honest_refactor", "seeded_regression", "slice_regression", "flaky_regression")]]),
        ):
            spec = f"config/metric_spec{'_v2' if version == 'v2' else ''}.yaml"
            for shape, filename in cases:
                run(["lab9.eval", "--shape", shape, "--spec", spec, "--out", f"reports/{filename}.json"],
                    keep=["E-", "wrote", "failure"])
            for shape, filename in cases:
                expected = int(shape.endswith("regression"))
                run(["lab9.gate", "--pr", f"reports/{filename}.json", "--baseline",
                     f"reports/baseline_{version}.json", "--spec", spec, "--base-spec", spec],
                    expected=expected, required=f"exit {expected} —",
                    keep=["pass_rate ", "slice:money_movement", "exit "])

        run(["lab9.ci_check", "--pr", "reports/eval_pr.json", "--baseline", "reports/baseline_v1.json",
             "--spec", "config/metric_spec.yaml"])
        run(["lab9.mutation", "--spec", "config/metric_spec_v2.yaml", "--aa", "66,77,88,99,110"])
        run(["lab9.mutation", "--spec", "config/metric_spec_v2.yaml", "--baseline", "reports/baseline_v2.json"],
            required="mutation score 3/3 · false alarms 0")
        run(["lab9.traps", "--pr", "reports/eval_slice_regression_v2.json", "--baseline",
             "reports/baseline_v2.json", "--spec", "config/metric_spec_v2.yaml"],
            required="exit 0 — the gate blocked every public trap")
        for trap in ("evaluator_errors_as_nan", "dropped_failing_rows", "cherry_picked_seeds", "loosened_spec"):
            spec = ("reports/traps/loosened_spec.spec.yaml" if trap == "loosened_spec"
                    else "config/metric_spec_v2.yaml")
            run(["lab9.gate", "--pr", f"reports/traps/{trap}.json", "--baseline", "reports/baseline_v2.json",
                 "--spec", spec, "--base-spec", "config/metric_spec_v2.yaml"],
                expected=1, required="INTEGRITY", keep=["INTEGRITY", "exit "])

        # Coverage is also checked against the input files, independently of the manifest.
        sys.path.insert(0, str(SRC))
        from lab9.eval import load_spec, per_item
        from lab9.evalset import load_jsonl, sha12
        from lab9.stats import paired_bootstrap
        import yaml

        for version in ("v1", "v2"):
            spec = load_spec(SRC / f"config/metric_spec{'_v2' if version == 'v2' else ''}.yaml")
            items_path = SRC / spec["eval_set"]
            items = load_jsonl(items_path)
            labels = json.loads((SRC / spec["labels"]).read_text())
            expected = {(item["item_id"], seed) for item in items for seed in spec["seeds"]}
            assert all("expected" not in it and "label" not in it and it["claim_id"] in labels for it in items)
            names = (["baseline_v1", "eval_pr", "eval_fixed", "eval_seeded_regression"] if version == "v1"
                     else ["baseline_v2", *[f"eval_{s}_v2" for s in
                           ("fixed", "honest_refactor", "seeded_regression", "slice_regression", "flaky_regression")]])
            for name in names:
                report = json.loads((SRC / f"reports/{name}.json").read_text())
                assert len(report["rows"]) == len(expected)
                assert {(r["item_id"], r["seed"]) for r in report["rows"]} == expected
                assert report["manifest"]["eval_set_sha"] == sha12(items_path)
                assert report["manifest"]["metric_spec_version"] == spec["metric_spec_version"]
                assert report["evaluator_failures"] == []
            lines.append(f"\n{version}: {len(items)} item, {len(expected)} cặp item/seed/report; "
                         f"SHA {sha12(items_path)}; nhãn tách riêng; không có evaluator failure.")

        base = json.loads((SRC / "reports/baseline_v1.json").read_text())
        pr = json.loads((SRC / "reports/eval_seeded_regression.json").read_text())
        a, b = per_item(pr, "pass_rate"), per_item(base, "pass_rate")
        delta, lo, hi = paired_bootstrap([a[k] for k in sorted(a)], [b[k] for k in sorted(a)])
        assert all(abs(x - ref) <= .01 for x, ref in zip((delta, lo, hi), (-.271, -.500, -.057)))
        harness = yaml.safe_load((SRC / "harness_map.yaml").read_text())
        assert harness["harness_map_version"] == "1.2" and "eval" in harness["sections"]
        lines.append(f"M4: Δ {delta:+.3f}; CI [{lo:+.3f}, {hi:+.3f}]; sai lệch tham chiếu ≤0.01; harness map 1.2 có eval.")
        lines.append("\nKết quả: ĐẠT kiểm tra công khai M1–M7. Bộ chấm ẩn không có trong repo.")
        status = 0
    except Exception as error:
        lines.append(f"\nKHÔNG ĐẠT: {error}")
        status = 1
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(LOG.read_text(), end="")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
