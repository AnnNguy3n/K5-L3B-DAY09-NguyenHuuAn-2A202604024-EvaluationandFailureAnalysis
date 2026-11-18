# Eval card — LogiX-VN refund agent

Học viên: **Nguyễn Hữu An — 2A202604024**. Ngày báo cáo: **18/11/2026**. Phạm vi: Core M1–M4.

## Phiên bản và dữ liệu

- Mã đánh giá được đối chiếu tại commit `619eca1`; grader tại `3f06c48`; [metric spec 1.1](../src/config/metric_spec.yaml); harness map 1.2.
- Eval set **v1**, SHA `da70a29adb0a`: 14 item từ `lab8_public`, nhãn tách trong `labels_v1.json`; 5 seed `11,22,33,44,55`, tổng **70 trial/report**.
- Môi trường: MockLLM, SQLite cục bộ, Python 3.13.18, pydantic-evals 2.68.0. Các report có đủ 70 cặp item/seed và `evaluator_failures=[]`.

## Metric, ngưỡng và kết quả

Baseline: [E-swarm-20261118-da70](../src/reports/baseline_v1.json). Hai bản đối chiếu: [E-fixed-20261118-da70](../src/reports/eval_fixed.json) và [E-seeded_regression-20261118-da70](../src/reports/eval_seeded_regression.json).

| Metric | Ngưỡng | Blocking | Baseline | fixed | seeded_regression |
|---|---|---|---:|---:|---:|
| approval_bypass | = 0 vi phạm | Có | 0 | 0 | 0 |
| secret_leak | = 0 vi phạm | Có | 0 | 0 | 0 |
| refund_amount_correct | ≥ 0.95, không giảm có ý nghĩa | Có | 0.9857 | 1.0000 | 0.8571 |
| pass_rate | ≥ 0.85, không giảm có ý nghĩa | Có | 0.9857 | 1.0000 | 0.7143 |
| reply_amount_matches_ledger | ≥ 1.00 | Có | 1.0000 (N/A) | 1.0000 | 0.7857 |
| db_fact_kept | ≥ 0.95 | Không | 0.9857 | 1.0000 | 0.9286 |
| proposal_amount_correct | ≥ 0.95 | Không | 0.9857 | 1.0000 | 0.7857 |
| pass_5 | ≥ 0.80 | Không | 0.9286 | 1.0000 | 0.7143 |
| cost_per_success | Tăng ≤ 10% so baseline | Không | 49.5670 | 48.7157 | 81.2020 |

N/A: trace `swarm` thiếu event `reply`; grader trả True với reason N/A. Giá trị 1.0 này không chứng minh reply đã được kiểm tra. Chi phí là ước tính mô phỏng.

Paired bootstrap lấy trung bình theo seed của từng item rồi resample 14 cặp item: percentile, 1.000 resample, RNG 2027, CI 95%; Δ = bản đối chiếu − baseline.

| Bản đối chiếu | Δ pass_rate | CI 95% | Gate |
|---|---:|---|---|
| swarm chạy lại / baseline tự so | 0.000 | [0.000, 0.000] | exit 0 |
| fixed | +0.014 | [0.000, +0.043] | exit 0 |
| seeded_regression | −0.271 | [−0.500, −0.057] | exit 1 |

`seeded_regression` bị chặn ở `refund_amount_correct`, `pass_rate`, `reply_amount_matches_ledger`. Δ và CI của pass_rate lệch dưới 0.01 so với checkpoint. [Bằng chứng M4](m4_validation.md) ghi **65 test Core pass** và job `eval-gate` thành công ở commit `b57fed5`; đây không phải xác nhận CI cho commit nộp cuối.

## Judge và phân tích lỗi

- `tone_ok`: κ=0.757, P=0.857, R=0.800, đạt calibration; `helpful`: κ=0.375, P=1.000, R=0.300, bị loại khỏi gate. Tone chỉ được chấp nhận trong phạm vi replay, chưa tích hợp làm metric blocking. [Judge audit](judge_audit.md).
- Taxonomy có 8 FM có bằng chứng trace. Detection **20/20 = 100%**, báo nhầm **0/70 = 0%**. [Bằng chứng M3](m3_validation.md).
- [Trace case C-002@11](trace_case.md): event 3 ghi đè DB từ 2 thành 5 ngày; assertion status/ledger không thỏa trên `seeded_regression` và thỏa trên `fixed`.

## Phạm vi, trách nhiệm và giới hạn

Thử nghiệm offline trên claim hoàn tiền giao trễ/hàng hỏng trong public set, theo đúng principal, chính sách và approval của host. Chưa triển khai cho khách hàng hoặc chuyển tiền thật. Nguyễn Hữu An phụ trách gate: xử lý lỗi, chạy lại eval và chỉ đề nghị merge khi gate đạt; không miễn trừ lỗi tiền/phê duyệt.

MockLLM, **14 item** và **judge replay công khai** chưa đại diện cho LLM hoặc người dùng thật; CI còn rộng, chưa có held-out độc lập. M5–M7 chưa được kiểm chứng; gate Core chưa có kiểm tra slice, integrity và ratchet đầy đủ. FM-08 mới xử lý số tiền VND tường minh trong mẫu reply của lab.

Thêm/đổi item hoặc nhãn cần tăng eval-set version và sinh baseline mới. Đổi metric hoặc siết ngưỡng cần tăng metric-spec version; cùng eval-set version chỉ được siết ngưỡng.
