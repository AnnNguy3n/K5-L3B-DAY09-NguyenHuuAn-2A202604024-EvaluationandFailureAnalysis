# Kết quả M4 — Paired bootstrap và gate

Em kiểm chứng lại bằng conda `lab9`, Python 3.13.18; [log M1–M7](../src/reports/submission_validation.txt) lưu lệnh và exit code. Eval set v1 SHA `da70a29adb0a`, spec 1.1, 14 item × 5 seed = 70 cặp/report, không thiếu/trùng hoặc evaluator failure. [Harness map 1.2](../src/harness_map.yaml) có section eval; ci_check exit 0.

| Report / run ID | pass_rate | Δ | CI 95% | Gate |
|---|---:|---:|---|---|
| [baseline](../src/reports/baseline_v1.json) / `E-swarm-20261118-da70` | 0.9857 | 0.000 | [0.000, 0.000] | exit 0, tự so |
| [fixed](../src/reports/eval_fixed.json) / `E-fixed-20261118-da70` | 1.0000 | +0.014 | [0.000, +0.043] | exit 0 |
| [regression](../src/reports/eval_seeded_regression.json) / `E-seeded_regression-20261118-da70` | 0.7143 | −0.271 | [−0.500, −0.057] | exit 1 |

Bootstrap paired theo trung bình item qua seed, percentile, 1.000 resample, RNG 2027, CI 95%, Δ=PR−baseline. Sai lệch tham chiếu ≤0.01. Output regression:

```text
pass_rate 0.7143; Δ -0.271 CI [-0.500, -0.057] BLOCK
exit 1 — blocked: refund_amount_correct, pass_rate, reply_amount_matches_ledger
```

[Log M4 cũ](../src/reports/m4/verification.json) giữ bằng chứng tại thời điểm làm M4; kết quả hoàn tất M1–M7 dùng log kiểm chứng cuối và CI của PR nộp bài. Giới hạn: MockLLM, 14 item v1 và judge replay; chưa đo người dùng thật.
