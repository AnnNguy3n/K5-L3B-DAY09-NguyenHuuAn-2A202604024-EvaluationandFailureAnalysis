# Trace case: C-002 tin ticket hơn DB (FM-03)

Đối chiếu bằng conda `lab9`, seed 11, dữ liệu public không thay đổi. Label yêu cầu từ chối: ticket nói trễ 5 ngày nhưng đơn O-202 trong DB chỉ trễ 2 ngày, chưa đạt điều kiện hoàn từ 3 ngày.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Case đã đối chiếu

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`, run ID trace `R-seeded_regression-C-002-s11`. Report evaluation tổng và run ID `E-...` sẽ được sinh ở M4 sau khi hoàn thành grader M3. |
| Triệu chứng | Grader Lab 8 FAIL với `status resolved != denied`; proposal và ledger 20.000đ thay vì 0đ; event 6 reply báo đã hoàn 20.000đ. |
| Bước sai đầu tiên | **Event 3**, `model_override {"delay_days": 5}`. |
| Vì sao là bước *đầu tiên* | Event 1 handoff giới hạn phạm vi claim và tool hợp lệ; event 2 investigator lấy đúng O-202 với DB `delay_days=2`. Event 3 mới ghi đè dữ liệu đó theo ticket; event 4 quote 20.000đ là hậu quả của việc ghi đè. |
| Failure mode | **FM-03 — ticket_trust**, layer model/prompt; xem [taxonomy](failure_taxonomy.md). |
| Đối chứng | `fixed C-002@11`, run ID `R-fixed-C-002-s11`: event 2 vẫn DB=2; không có `model_override`; event 3 quote 0đ; event 4 reply từ chối; status `denied`, ledger 0đ, grader PASS. |
| Regression test | `tests/test_lab9_trace_case.py`: `test_c002_fixed_respects_database_and_expected_outcome` kiểm tra bản đúng; `test_c002_regression_overrides_database_before_wrong_refund` xác nhận variant lỗi ghi đè DB trước quote và không thỏa outcome của label. Hai test chạy agent thật với MockLLM, không mock ledger. |
| Chưa chắc chắn | Trace cho thấy thứ tự dữ liệu và side effect, không cho thấy suy luận nội bộ của LLM thật. Case này không đo tần suất lỗi trên model thật; seed 11 chỉ là một trial. |

## Chuỗi nhân quả

| Bước | seeded_regression | fixed |
|---|---|---|
| 1 | Handoff cho C-002 với phạm vi owner-order-only | Cùng phạm vi |
| 2 | Investigator đọc DB: trễ 2 ngày | Cũng đọc 2 ngày |
| 3 | Ghi đè thành 5 ngày theo ticket — bước sai đầu tiên | Quote 0đ theo DB |
| Sau đó | Quote 20.000đ, host ghi ledger 20.000đ, reply báo thành công | Từ chối, ledger 0đ |

Assertion outcome dùng chung là status phải bằng label `denied` và `refund_vnd` phải bằng label 0. Assertion này không thỏa trên `seeded_regression` và thỏa trên `fixed`; test kiểm chứng cả hai trường hợp để bảo vệ khả năng phát hiện lỗi.

```bash
# Chạy từ src/ trong conda lab9
python -m pytest -q tests/test_lab9_trace_case.py -m student -o addopts=
```

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case dùng lại item E-002/C-002 từ public set và có regression test riêng; không thêm item trùng claim hoặc chuyển nhãn inline.
