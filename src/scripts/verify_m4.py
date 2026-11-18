"""Reproduce M4 with the active Python interpreter and save auditable evidence.

Run from any directory with: conda run -n lab9 python /path/to/src/scripts/verify_m4.py
Reports are produced by lab9.eval. This script records CLI output, exit codes,
report coverage, bootstrap intervals, and hashes; it never edits report metrics.
"""

from __future__ import annotations

import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import re
import shlex
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

SRC = Path(__file__).resolve().parents[1]
ROOT = SRC.parent
EVIDENCE = SRC / "reports/m4"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    summary = {
        "status": "RUNNING",
        "checked_at": datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).isoformat(),
        "python": sys.executable,
        "python_version": sys.version.split()[0],
        "packages": {name: version(name) for name in ("numpy", "scipy", "pydantic-evals", "pytest")},
        "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "steps": [],
        "reports": {},
    }

    def run(name: str, args: list[str], expected: int = 0, pattern: str | None = None):
        command = [sys.executable, "-m", *args]
        result = subprocess.run(command, cwd=SRC, capture_output=True, text=True, timeout=180)
        matched = pattern is None or re.search(pattern, result.stdout, re.MULTILINE) is not None
        step = {"name": name, "command": shlex.join(command), "cwd": str(SRC),
                "exit_code": result.returncode, "expected_exit_code": expected,
                "passed": result.returncode == expected and matched}
        if pattern:
            step["required_stdout_pattern"] = pattern
        log = EVIDENCE / f"{name}.txt"
        log.write_text(
            f"$ {step['command']}\ncwd: {SRC}\n\n{result.stdout}"
            f"\nSTDERR:\n{result.stderr}\nexit_code={result.returncode}; expected={expected}\n",
            encoding="utf-8",
        )
        step["log"] = log.relative_to(ROOT).as_posix()
        summary["steps"].append(step)
        print(f"{'PASS' if step['passed'] else 'FAIL'} {name}: exit {result.returncode} (expected {expected})", flush=True)
        if not step["passed"]:
            raise RuntimeError(f"{name} failed; see {log}")

    try:
        # Same Core checks and commands as .github/workflows/eval-gate.yml.
        run("smoke", ["lab9.smoke"], pattern=r"^M0 PASS$")
        run("pytest_core", ["pytest", "-q", "-m", "student", "-o", "addopts=",
                            "-k", "lab9 and not advanced", "--junitxml=reports/m4/pytest_core.xml"])
        run("evalset_check", ["lab9.evalset", "--check"], pattern=r"0 problem\(s\)")
        for shape, filename in (("swarm", "baseline_v1"), ("swarm", "eval_pr"),
                                ("fixed", "eval_fixed"), ("seeded_regression", "eval_seeded_regression")):
            run(filename, ["lab9.eval", "--shape", shape, "--spec", "config/metric_spec.yaml",
                           "--out", f"reports/{filename}.json"])
        baseline_args = ["--baseline", "reports/baseline_v1.json", "--spec", "config/metric_spec.yaml"]
        run("gate_baseline_self", ["lab9.gate", "--pr", "reports/baseline_v1.json", *baseline_args],
            pattern=r"^exit 0 — merge$")
        run("gate_pr", ["lab9.gate", "--pr", "reports/eval_pr.json", *baseline_args],
            pattern=r"^exit 0 — merge$")
        run("ci_check", ["lab9.ci_check", "--pr", "reports/eval_pr.json", *baseline_args])
        run("gate_fixed", ["lab9.gate", "--pr", "reports/eval_fixed.json", *baseline_args],
            pattern=r"^exit 0 — merge$")
        run("gate_seeded_regression", ["lab9.gate", "--pr", "reports/eval_seeded_regression.json", *baseline_args],
            expected=1, pattern=r"^exit 1 — blocked: ([^,]+, )*pass_rate(, |$)")

        # Inspect the real artifacts independently of the gate's aggregate verdict.
        sys.path.insert(0, str(SRC))
        from lab9 import stats
        from lab9.eval import load_spec, per_item
        from lab9.evalset import load_jsonl, sha12
        from lab9.graders import GRADERS
        import yaml

        spec = load_spec(SRC / "config/metric_spec.yaml")
        items = load_jsonl(SRC / spec["eval_set"])
        expected_pairs = {(item["item_id"], seed) for item in items for seed in spec["seeds"]}
        expected_sha = sha12(SRC / spec["eval_set"])
        reports = {name: json.loads((SRC / f"reports/{name}.json").read_text(encoding="utf-8"))
                   for name in ("baseline_v1", "eval_pr", "eval_fixed", "eval_seeded_regression")}
        base = reports["baseline_v1"]
        assert base["shape"] == "swarm", "baseline must evaluate swarm"
        for name, report in reports.items():
            manifest, rows = report["manifest"], report["rows"]
            assert manifest["items"] == len(items) and manifest["seeds"] == spec["seeds"]
            assert manifest["metric_spec_version"] == spec["metric_spec_version"]
            assert manifest["eval_set_sha"] == expected_sha
            assert len(rows) == len(expected_pairs)
            assert {(r["item_id"], r["seed"]) for r in rows} == expected_pairs
            assert report["evaluator_failures"] == []
            assert all(isinstance(v, (int, float)) and math.isfinite(v) for v in report["metrics"].values())
            assert all(isinstance(row.get(mid), bool) for row in rows
                       for mid in GRADERS if mid in {m["id"] for m in spec["metrics"]})
            pr_items, base_items = per_item(report, "pass_rate"), per_item(base, "pass_rate")
            keys = sorted(base_items)
            delta, lo, hi = stats.paired_bootstrap([pr_items[k] for k in keys], [base_items[k] for k in keys],
                                                 n_resamples=spec["bootstrap"]["n_resamples"],
                                                 rng=spec["bootstrap"]["rng"], confidence=spec["bootstrap"]["confidence"])
            summary["reports"][name] = {"path": f"src/reports/{name}.json", "run_id": report["run_id"],
                                         "shape": report["shape"], "rows": len(rows), "unique_pairs": len(expected_pairs),
                                         "eval_set_sha": expected_sha, "evaluator_failures": 0,
                                         "metrics": report["metrics"],
                                         "pass_rate_comparison": {"delta": delta, "lo": lo, "hi": hi}}
        actual = summary["reports"]["eval_seeded_regression"]["pass_rate_comparison"]
        assert all(abs(actual[key] - ref) <= 0.01 for key, ref in (("delta", -0.271), ("lo", -0.500), ("hi", -0.057)))
        harness = yaml.safe_load((SRC / "harness_map.yaml").read_text(encoding="utf-8"))
        assert harness["harness_map_version"] == "1.2"
        evaluation = harness["sections"]["eval"]
        assert evaluation["eval_set"] == spec["eval_set"] and evaluation["labels"] == spec["labels"]
        assert evaluation["baseline"] == "reports/baseline_v1.json" and evaluation["gate"] == "python -m lab9.gate"
        summary["harness_map"] = {"version": harness["harness_map_version"], "eval": evaluation}
        files = [SRC / path for path in ("lab9/stats.py", "lab9/gate.py", "lab9/eval.py", "lab9/ci_check.py",
                                        "lab9/graders.py", "config/metric_spec.yaml", "harness_map.yaml",
                                        "data/eval/eval_set_v1.jsonl", "data/eval/labels_v1.json",
                                        "tests/test_lab9_stats.py", "tests/test_lab9_gate.py", "scripts/verify_m4.py")]
        files += [SRC / f"reports/{name}.json" for name in reports]
        files += [ROOT / ".github/workflows/eval-gate.yml"]
        summary["sha256"] = {path.relative_to(ROOT).as_posix(): sha256(path) for path in files}
        summary["status"] = "PASS"
    except Exception as error:
        summary["status"] = "FAIL"
        summary["error"] = f"{type(error).__name__}: {error}"
        print(summary["error"], file=sys.stderr)
    finally:
        target = EVIDENCE / "verification.json"
        target.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{summary['status']} M4: {target}", flush=True)
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
