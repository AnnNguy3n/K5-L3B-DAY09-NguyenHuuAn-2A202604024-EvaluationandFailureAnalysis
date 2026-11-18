# Judge audit — M2

Calibration dùng hai CSV public replay, mỗi tập 100 case; **FAIL là positive class**. Ngưỡng chấp nhận đồng thời: κ ≥ 0.6, precision ≥ 0.8, recall ≥ 0.7; κ không xác định được tính FAIL.

## Kết quả

| Tiêu chí | TP | FP | FN | TN | κ | Precision | Recall | Quyết định |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| tone_ok | 24 | 4 | 6 | 66 | 0.757 | 0.857 | 0.800 | Đạt trong phạm vi replay |
| helpful | 9 | 0 | 21 | 70 | 0.375 | 1.000 | 0.300 | Loại khỏi gate |

Helpful bỏ sót 21/30 lỗi (70%); precision cao không bù được recall và κ dưới sàn. Tone bỏ sót 6/30 lỗi, báo nhầm 4/70 case đạt.

Rogan–Gladen: `clip((p_obs + specificity - 1) / (sensitivity + specificity - 1), 0, 1)`.

| Tiêu chí | Tỷ lệ lỗi quan sát | Sensitivity | Specificity | Tỷ lệ hiệu chỉnh |
|---|---:|---:|---:|---:|
| tone_ok | 0.280 | 0.800 | 66/70 | 0.300 |
| helpful | 0.090 | 0.300 | 1.000 | 0.300 |

Tỷ lệ hiệu chỉnh khớp 30/100 nhãn human trên cùng tập; kết quả này không làm helpful đạt calibration hoặc chứng minh khả năng tổng quát hóa.

## Audit 6 bất đồng

Em đối chiếu reply và ghi chú CSV; giữ nguyên nhãn public, không tạo nhãn người mới. Thông tin ledger/ticket lấy từ ghi chú dataset.

| Case | Judge | Human | Kết luận và bằng chứng | Điều chỉnh rubric đề xuất |
|---|---|---|---|---|
| H-008 | PASS | FAIL | Human đúng theo note: cách xưng hô và “nha” quá suồng sã | Thêm ví dụ FAIL cho giọng thân mật không phù hợp khiếu nại |
| H-029 | PASS | FAIL | Human đúng: “không cần nhắn thêm” mang tính gạt bỏ | Chấm toàn reply; lời mở đầu lịch sự không bù phần ra lệnh |
| H-042 | FAIL | PASS | Human đúng theo note: câu ngắn nhưng đủ kết quả và thời gian tiền về | Không bắt buộc lời xin lỗi khi ngữ cảnh không yêu cầu |
| H-051 | FAIL | PASS | Human đúng theo note: thuật ngữ “refund” được CS LogiX cho phép | Bổ sung danh sách thuật ngữ nghiệp vụ được phép |
| H-081 | FAIL | PASS | Note xác định judge đúng, human đọc nhầm ticket; reply riêng lẻ chưa đủ xác minh | Rà soát nhãn với người có ngữ cảnh, ghi lý do và tạo phiên bản nhãn mới |
| HL-015 | PASS | FAIL | Human đúng theo note: reply 55.000đ nhưng ledger 40.000đ | Dùng code so tiền với ledger; lịch sự không bù được sai tiền |

## Minh chứng và giới hạn

[Log kiểm chứng cuối](../src/reports/submission_validation.txt): tone exit 0, helpful exit 1; test thống kê/calibration nằm trong 121 test đạt. [Log M2 cũ](evidence/m2_verification.txt) lưu lần kiểm tra ban đầu. Các đề xuất rubric chưa được đánh giá lại bằng judge mới.

Lệnh tái lập từ `src/`, môi trường `lab9`:

```bash
conda run -n lab9 python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 10
conda run -n lab9 python -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 5
```

Judge replay công khai chưa có held-out độc lập hoặc nhãn người mới. Tone chưa được tích hợp làm metric blocking; helpful không đủ điều kiện dùng cho gate. Tiền và phê duyệt được chấm bằng code.
