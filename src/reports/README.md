# Minh chứng Lab 9 — M1–M7

**Nguyễn Hữu An — 2A202604024.** Em tổng hợp kết quả trong [eval card](../../docs/eval_card.md); [log cuối](submission_validation.txt) ghi **121 test pass**, A/A Δ=0, mutation **3/3, 0 báo nhầm**, **4/4 trap gate exit 1** và baseline tự so exit 0.

| Bộ dữ liệu | Report sinh bằng script |
|---|---|
| v1: 14 item × 5 seed, SHA `da70a29adb0a`, spec 1.1 | [baseline](baseline_v1.json), [fixed](eval_fixed.json), [seeded_regression](eval_seeded_regression.json) |
| v2: 28 item × 5 seed, SHA `395c9495a572`, spec 2.1 | [baseline](baseline_v2.json), [fixed](eval_fixed_v2.json), [honest_refactor](eval_honest_refactor_v2.json), [seeded_regression](eval_seeded_regression_v2.json), [slice_regression](eval_slice_regression_v2.json), [flaky_regression](eval_flaky_regression_v2.json) |
| M7 | [trap grader lỗi](traps/evaluator_errors_as_nan.json), [bỏ dòng](traps/dropped_failing_rows.json), [chọn seed](traps/cherry_picked_seeds.json), [nới spec](traps/loosened_spec.json), [spec bị nới](traps/loosened_spec.spec.yaml) |

Tái lập từ root repo: `conda run --no-capture-output -n lab9 python src/scripts/verify_submission.py`. Script sinh report/log và kiểm tra coverage; không chỉnh tay số liệu. Các thư mục m3/m4 và log m5/m6 lưu lịch sử; kết quả hiện tại dùng log cuối.
