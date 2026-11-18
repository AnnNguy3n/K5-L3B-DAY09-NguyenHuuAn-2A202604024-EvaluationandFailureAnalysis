# Kết quả M4 — Paired bootstrap và gate

Kiểm chứng **18/11/2026 12:44 +07:00**, conda `lab9`: Python 3.13.18, SciPy 1.18.1, NumPy 2.5.5, pydantic-evals 2.68.0. [Summary tự sinh](../src/reports/m4/verification.json) lưu cấu hình, exit code và SHA-256 của mã/dữ liệu/report.

## Kết quả Core

| Phép kiểm | Kết quả | Minh chứng |
|---|---|---|
| Smoke / eval set | M0 PASS; 0 problem(s), SHA `da70a29adb0a` | [smoke](../src/reports/m4/smoke.txt), [eval set](../src/reports/m4/evalset_check.txt) |
| Test Core | **65 passed**, 317 deselected | [pytest](../src/reports/m4/pytest_core.txt) |
| Baseline tự so / swarm chạy lại | exit 0 / exit 0 | [self](../src/reports/m4/gate_baseline_self.txt), [PR swarm](../src/reports/m4/gate_pr.txt) |
| Baseline và metric FM-08 | ci_check exit 0; harness map 1.2 có section eval | [ci_check](../src/reports/m4/ci_check.txt), [harness map](../src/harness_map.yaml) |
| fixed / seeded_regression | exit 0 / exit 1, có `pass_rate` trong danh sách chặn | [fixed](../src/reports/m4/gate_fixed.txt), [regression](../src/reports/m4/gate_seeded_regression.txt) |

Mỗi report có 14 item × 5 seed = **70 cặp item/seed**, không trùng/thiếu, `evaluator_failures=[]`, metric hữu hạn. Spec 1.1; seed `11,22,33,44,55`. Bootstrap resample theo 14 cặp trung bình item: paired, percentile, 1.000 lần, RNG 2027, CI 95%, Δ = PR − baseline.

| Report / run ID | pass_rate | Δ | CI 95% |
|---|---:|---:|---|
| [baseline](../src/reports/baseline_v1.json) / `E-swarm-20261118-da70` | 0.9857 | 0.000 | [0.000, 0.000] |
| [fixed](../src/reports/eval_fixed.json) / `E-fixed-20261118-da70` | 1.0000 | +0.014 | [0.000, +0.043] |
| [regression](../src/reports/eval_seeded_regression.json) / `E-seeded_regression-20261118-da70` | 0.7143 | −0.271 | [−0.500, −0.057] |

Δ và CI của regression lệch dưới 0.01 so với checkpoint. Output gate:

```text
  pass_rate              0.7143   {"min": 0.85, "no_significant_drop": true} Δ -0.271 CI [-0.500, -0.057] BLOCK
exit 1 — blocked: refund_amount_correct, pass_rate, reply_amount_matches_ledger
```

GitHub job **eval-gate SUCCESS** tại commit `b57fed5`, [run 44246652149](https://github.com/AnnNguy3n/K5-L3B-DAY09-NguyenHuuAn-2A202604024-EvaluationandFailureAnalysis/actions/runs/44246652149), theo [bằng chứng API đã lưu](../src/reports/m4/github_ci_baseline.json). Run dùng `workflow_dispatch`; chưa xác nhận CI của commit nộp cuối hoặc PR đã merge. Job v2 bỏ qua các bước Advanced vì chưa có baseline v2.

Tái lập toàn bộ từ root repo: `conda run --no-capture-output -n lab9 python src/scripts/verify_m4.py`. Script sinh report và log bằng CLI chính thức; không sửa tay JSON. [Eval card](eval_card.md) ghi toàn bộ metric và giới hạn MockLLM/14 item/judge replay; M5–M7 chưa thuộc kết quả này.
