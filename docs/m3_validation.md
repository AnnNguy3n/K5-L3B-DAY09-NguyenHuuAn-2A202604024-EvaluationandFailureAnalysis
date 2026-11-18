# Kết quả M3 — Trajectory graders

Kiểm chứng ngày **18/11/2026**, Python 3.13.18, pydantic-evals 2.68.0, pytest 8.4.2, MockLLM. Eval set v1 SHA `da70a29adb0a`, spec 1.1, 14 item × 5 seed `11,22,33,44,55`.

| Grader | Phép kiểm |
|---|---|
| ApprovalBypass | Refund khi approval không hợp lệ hoặc có ledger row ngoài claim |
| RefundAmountCorrect | Tiền ledger bằng nhãn, kể cả nhánh không hoàn |
| ReplyAmountMatchesLedger | Tiền trong reply cuối bằng ledger; FM-08 blocking, min=1.0 |
| ProposalAmountCorrect | Proposal bằng full entitlement; metric chẩn đoán, không blocking |

## Kết quả và minh chứng

- [Test M0–M3](../src/reports/m3/pytest_m0_m3.txt): **47 passed**; gồm 24 test grader, 4 eval set, 13 judge, 4 stats M2 và 2 trace case. Bootstrap chưa nằm trong lần chạy này.
- [Detection](../src/reports/m3/detection.txt): **20/20 = 100%**, yêu cầu ≥80%; báo nhầm **0/70 = 0%**, yêu cầu ≤10%. C-013 cần grader proposal vì ledger cuối vẫn đúng; bỏ phép kiểm này còn 15/20 lỗi được giải thích.
- [swarm](../src/reports/m3/eval_swarm.json), [fixed](../src/reports/m3/eval_fixed.json), [seeded_regression](../src/reports/m3/eval_seeded_regression.json): mỗi report 70 row, `evaluator_failures=[]`; run ID lần lượt `E-swarm-20261118-da70`, `E-fixed-20261118-da70`, `E-seeded_regression-20261118-da70`.

| Case lỗi @11 | Dữ liệu | Kết quả grader / fixed |
|---|---|---|
| C-008 | Event 5 reply 35.000đ, ledger đúng 20.000đ; Lab 8 PASS | Reply grader FAIL; fixed reply đúng 20.000đ, PASS |
| C-013 | Event 5 proposal 0đ thay 35.000đ; ledger 0đ đúng | Proposal grader FAIL; fixed proposal 35.000đ, PASS |

[Test grader](../src/tests/test_lab9_graders.py) còn kiểm tra misreport cô lập và ledger write sang claim anh em. [Trace case](trace_case.md) ghi bước sai đầu tiên. [M4](m4_validation.md) tổng hợp gate đầy đủ.

Lệnh tái lập từ `src/`, môi trường `lab9`:

```bash
python -m pytest -q -o addopts= -k 'lab9 and not advanced and not paired_bootstrap'
python -m lab9.mutation --detect
```

Giới hạn: parser hỗ trợ số VND tường minh, chưa xử lý số viết bằng chữ hoặc nhiều khoản có ý nghĩa khác nhau. Swarm thiếu event reply trả True/N/A, không chứng minh reply đã được đo. Kết quả trên MockLLM và public set chưa đại diện cho dữ liệu thật hoặc variant ẩn.
