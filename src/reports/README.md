# Minh chứng Lab 9

Các report được sinh bằng `lab9.eval`, eval set v1 SHA `da70a29adb0a`, metric spec 1.1; mỗi report có 14 item × 5 seed. Số liệu tổng hợp tại [eval card](../../docs/eval_card.md).

| File | Run ID | Kết quả |
|---|---|---|
| [baseline_v1.json](baseline_v1.json) | E-swarm-20261118-da70 | Baseline swarm |
| [eval_fixed.json](eval_fixed.json) | E-fixed-20261118-da70 | Gate exit 0 |
| [eval_seeded_regression.json](eval_seeded_regression.json) | E-seeded_regression-20261118-da70 | Gate exit 1, chặn pass_rate |

M5: [baseline v2](baseline_v2.json), [fixed v2](eval_fixed_v2.json), [honest_refactor v2](eval_honest_refactor_v2.json), [slice_regression v2](eval_slice_regression_v2.json); mỗi report 28 item × 5 seed, SHA `395c9495a572`. Em ghi kết quả trong [eval card](../../docs/eval_card.md) và giữ [một log kiểm tra M5](m5_validation.txt). M6/M7 chưa hoàn thành.

[M3](../../docs/m3_validation.md) lưu detection và test grader; [M4](../../docs/m4_validation.md) lưu bootstrap, gate và CI. Các thư mục `m3/`, `m4/` giữ log/JSON/XML gốc; chúng là bằng chứng lịch sử tại thời điểm chạy.

Tái lập từ root repo: `conda run --no-capture-output -n lab9 python src/scripts/verify_m4.py`. Report và log được sinh bằng script; không chỉnh tay số liệu. Report JSON nộp bài được commit bằng `git add -f src/reports/*.json`.
