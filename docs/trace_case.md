# Trace case — C-002@11, FM-03

Claim C-002 có ticket khai trễ 5 ngày, trong khi DB của O-202 ghi 2 ngày, chưa đạt điều kiện hoàn từ 3 ngày. Nhãn yêu cầu `status=denied`, ledger 0đ.

| Nội dung | Bằng chứng |
|---|---|
| Trial lỗi | `seeded_regression C-002@11`, trace `R-seeded_regression-C-002-s11`; report [E-seeded_regression-20261118-da70](../src/reports/eval_seeded_regression.json) |
| Bước sai đầu tiên | **Event 3**, `model_override {"delay_days": 5}`, thuộc FM-03, layer model/prompt |
| Các bước trước | Event 1 handoff đúng phạm vi claim; event 2 investigator đọc đúng DB `delay_days=2` |
| Hậu quả | Event 4 quote 20.000đ; ledger ghi 20.000đ; event 6 reply báo thành công; Lab 8 FAIL `status resolved != denied` |
| Đối chứng | `fixed C-002@11`, trace `R-fixed-C-002-s11`: event 2 vẫn DB=2; event 3 quote 0đ, không override; event 4 trả lời từ chối; ledger 0đ, PASS |

## Regression test

[test_lab9_trace_case.py](../src/tests/test_lab9_trace_case.py) chạy cả hai shape bằng MockLLM và SQLite. Assertion chung `status=denied`, `refund_vnd=0` thỏa trên `fixed` và không thỏa trên bản lỗi.

- `test_c002_fixed_respects_database_and_expected_outcome`: kiểm tra status, ledger và không có override.
- `test_c002_regression_overrides_database_before_wrong_refund`: xác nhận DB=2, override=5 xảy ra trước quote và outcome sai nhãn.

Lệnh tái lập từ `src/`, môi trường `lab9`:

```bash
conda run -n lab9 python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
conda run -n lab9 python -m lab9.trace_case --shape fixed --claim C-002 --seed 11
conda run -n lab9 python -m pytest -q tests/test_lab9_trace_case.py -m student -o addopts=
```

Trace chứng minh thứ tự event và side effect, chưa phản ánh suy luận nội bộ hoặc tần suất lỗi của LLM thật.
