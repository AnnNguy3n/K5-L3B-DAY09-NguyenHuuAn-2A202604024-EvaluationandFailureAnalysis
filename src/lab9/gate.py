"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, load_spec, per_item
from lab9.graders import GRADERS


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    problems = []
    coverage, tags = {}, {}
    graded = {m["id"] for m in spec["metrics"] if m["id"] in GRADERS}

    for name, report in (("PR", pr), ("baseline", base)):
        manifest = report.get("manifest")
        rows, metrics = report.get("rows"), report.get("metrics")
        if not isinstance(manifest, dict) or not isinstance(rows, list) or not isinstance(metrics, dict):
            problems.append(f"{name}: malformed manifest/rows/metrics")
            continue
        if not manifest.get("eval_set_sha"):
            problems.append(f"{name}: missing eval_set_sha")
        items, seeds = manifest.get("items"), manifest.get("seeds")
        if (type(items) is not int or items < 1 or not isinstance(seeds, list)
                or not seeds or any(type(s) is not int for s in seeds)):
            problems.append(f"{name}: invalid item count or seeds")
            continue
        if len(set(seeds)) != len(seeds):
            problems.append(f"{name}: duplicate manifest seeds")
        if len(rows) != items * len(seeds):
            problems.append(f"{name}: row count differs from items x seeds")
        if "seeds" in spec and set(seeds) != set(spec["seeds"]):
            problems.append(f"{name}: seeds differ from spec")
        if report.get("evaluator_failures", []) != []:
            problems.append(f"{name}: evaluator_failures present")
        for mid, value in metrics.items():
            # None remains a missing aggregate verdict in check(); it is never
            # allowed for a per-trial grader result below.
            if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value)):
                problems.append(f"{name}: non-finite or non-numeric metric {mid}")

        pairs, item_tags = Counter(), {}
        for row in rows:
            if (not isinstance(row, dict) or not isinstance(row.get("item_id"), str)
                    or type(row.get("seed")) is not int):
                problems.append(f"{name}: malformed item/seed row")
                continue
            item, seed = row["item_id"], row["seed"]
            pairs[item, seed] += 1
            slices = row.get("slices", [])
            if not isinstance(slices, list) or any(not isinstance(s, str) for s in slices):
                problems.append(f"{name}: invalid slices for {item}")
            else:
                row_tags = frozenset(slices)
                if item in item_tags and item_tags[item] != row_tags:
                    problems.append(f"{name}: inconsistent slice tags for {item}")
                item_tags[item] = row_tags
            for mid in graded:
                value = row.get(mid)
                if (value is None or not isinstance(value, (bool, int, float))
                        or not math.isfinite(value) or value not in (0, 1)):
                    problems.append(f"{name}: missing/invalid grader {mid} at {item}@{seed}")

        item_ids = {item for item, _ in pairs}
        expected = {(item, seed) for item in item_ids for seed in seeds}
        if (len(item_ids) != items or set(pairs) != expected
                or any(count != 1 for count in pairs.values())):
            problems.append(f"{name}: incomplete or duplicate item/seed coverage")
        coverage[name], tags[name] = pairs, item_tags

    if coverage.get("PR") != coverage.get("baseline"):
        problems.append("PR item/seed coverage differs from baseline")
    if tags.get("PR") != tags.get("baseline"):
        problems.append("PR item slice tags differ from baseline")

    if base_spec is not None and spec.get("eval_set_version") == base_spec.get("eval_set_version"):
        problems.extend(_ratchet_problems(spec, base_spec))
    return list(dict.fromkeys(problems))


def _ratchet_problems(spec: dict, base_spec: dict) -> list[str]:
    """Compare rules by identity, allowing additions and tighter thresholds."""
    problems = []
    for section in ("metrics", "slices"):
        def key(rule):
            return rule["id"] if section == "metrics" else (rule["name"], rule["metric"])

        current = {key(rule): rule for rule in spec.get(section, [])}
        if len(current) != len(spec.get(section, [])):
            problems.append(f"ratchet: duplicate {section} rules")
        for old in base_spec.get(section, []):
            identity = key(old)
            new = current.get(identity)
            label = f"ratchet {section}:{identity}"
            if new is None:
                problems.append(f"{label}: removed rule")
                continue
            if old.get("blocking") and not new.get("blocking"):
                problems.append(f"{label}: disabled blocking")
            before = old.get("threshold", {}) if section == "metrics" else old
            after = new.get("threshold", {}) if section == "metrics" else new
            for field in ("min", "max", "max_increase"):
                if field not in before:
                    continue
                value = after.get(field)
                if not isinstance(value, (int, float)) or not math.isfinite(value):
                    problems.append(f"{label}: removed/invalid {field}")
                elif (field == "min" and value < before[field]) or (field != "min" and value > before[field]):
                    problems.append(f"{label}: loosened {field}")
            if before.get("no_significant_drop") and not after.get("no_significant_drop"):
                problems.append(f"{label}: disabled no_significant_drop")
    return problems


def slice_check(
    pr: dict, base: dict, spec: dict
) -> tuple[list[str], list[str]]:
    """Apply each slice's floor and paired CI to aligned per-item seed means."""
    blocked, lines = [], []
    bootstrap = spec.get("bootstrap", {})

    for rule in spec.get("slices", []):
        name, metric = rule["name"], rule["metric"]
        mid = f"slice:{name}/{metric}"

        a = per_item(pr, metric, slice_name=name)
        b = per_item(base, metric, slice_name=name)
        failed, notes = False, []

        if not a or a.keys() != b.keys():
            failed = True
            notes.append("missing or unmatched slice items")
        else:
            keys = sorted(a)
            value = sum(a.values()) / len(a)
            notes.append(f"value={value:.4f}")

            if "min" in rule and value < rule["min"]:
                failed = True
                notes.append(f"below min={rule['min']}")

            if rule.get("no_significant_drop"):
                try:
                    delta, lo, hi = stats.paired_bootstrap(
                        [a[k] for k in keys],
                        [b[k] for k in keys],
                        n_resamples=bootstrap.get("n_resamples", 1000),
                        rng=bootstrap.get("rng", 2027),
                        confidence=bootstrap.get("confidence", 0.95),
                    )
                    notes.append(
                        f"delta={delta:+.3f} "
                        f"CI [{lo:+.3f}, {hi:+.3f}]"
                    )
                    failed = failed or hi < 0
                except ValueError as exc:
                    failed = True
                    notes.append(f"CI unavailable: {exc}")

        blocking = rule.get("blocking", False)
        if failed and blocking:
            blocked.append(mid)

        verdict = (
            "BLOCK" if failed and blocking
            else "warn" if failed
            else "ok"
        )
        lines.append(f"  {mid}: {'; '.join(notes)} {verdict}")

    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
