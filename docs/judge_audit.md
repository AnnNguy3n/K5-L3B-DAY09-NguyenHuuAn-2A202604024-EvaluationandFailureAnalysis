# Judge audit — M2

## Phạm vi và cách đo

Calibration chạy offline bằng conda `lab9` (Python 3.13.18), dùng nguyên hai CSV công khai trong `src/data/eval/`. Nhãn `human` là nhãn tham chiếu để tính số liệu; `judge` là kết quả replay, không gọi LLM mới và không cần API key. Không thay đổi CSV, nhãn gốc hoặc FLOORS để làm kết quả đạt.

**FAIL là positive class:** TP = human FAIL / judge FAIL; FP = human PASS / judge FAIL; FN = human FAIL / judge PASS; TN = human PASS / judge PASS. Precision đo độ đúng của cảnh báo lỗi, recall đo tỷ lệ lỗi được phát hiện. Judge chỉ được dùng khi đồng thời κ ≥ 0.6, precision ≥ 0.8 và recall ≥ 0.7; κ không xác định được xem là không đạt.

## Kết quả calibration

| Tiêu chí | n | TP | FP | FN | TN | κ | Precision | Recall | FLOORS | Quyết định |
|---|---|---|---|---|---|---|---|---|---|---|
| tone_ok | 100 | 24 | 4 | 6 | 66 | 0.757 | 0.857 | 0.800 | PASS | Dùng cho tiêu chí tone trong phạm vi replay đã kiểm tra |
| helpful | 100 | 9 | 0 | 21 | 70 | 0.375 | 1.000 | 0.300 | FAIL | Loại khỏi gate |

Tone phát hiện 24/30 lỗi, bỏ sót 6 lỗi và báo nhầm 4/70 case đạt; có tổng cộng 10 bất đồng. Cả ba chỉ số vượt hoặc đạt sàn, nhưng kết quả này chưa chứng minh judge đáng tin trên dữ liệu mới.

Helpful phát hiện chỉ 9/30 lỗi, bỏ sót 21/30 lỗi (70%) và có tổng cộng 21 bất đồng. Precision = 1.0 chỉ nói rằng 9 cảnh báo đều đúng; nó không bù được recall = 0.3 và κ = 0.375. Judge này không được dùng để quyết định merge/release.

## Hiệu chỉnh tỷ lệ lỗi bằng Rogan–Gladen

Sensitivity = TP/(TP+FN), specificity = TN/(TN+FP), tỷ lệ quan sát = (TP+FP)/n. Tỷ lệ hiệu chỉnh là `(observed + specificity - 1) / (sensitivity + specificity - 1)`, giới hạn về [0, 1].

| Tiêu chí | Tỷ lệ lỗi quan sát | Sensitivity | Specificity | Tỷ lệ lỗi hiệu chỉnh | Tỷ lệ lỗi theo human |
|---|---|---|---|---|---|
| tone_ok | 0.280 | 0.800 | 66/70 ≈ 0.942857 | 0.300 | 30/100 = 0.300 |
| helpful | 0.090 | 0.300 | 70/70 = 1.000000 | 0.300 | 30/100 = 0.300 |

Đây là hiệu chỉnh tỷ lệ tổng thể, không sửa nhãn từng case hoặc làm helpful đạt calibration. Sensitivity và specificity được ước lượng trên chính tập replay nên việc khớp tỷ lệ human ở đây không phải bằng chứng tổng quát hóa. Khi mẫu số bằng 0, hàm thống kê báo `ValueError`; CLI vẫn trả kết luận calibration, hiển thị tỷ lệ hiệu chỉnh `nan` thay vì crash. Judge hằng PASS hoặc κ không xác định phải FAIL FLOORS.

## Audit 10 bất đồng và hành động sửa rubric

Audit dưới đây có hỗ trợ Codex, dựa trên toàn bộ `reply`, `human`, `judge`, `note` và `human_failure` trong CSV. Đây không phải nhãn người mới. Chi tiết tuổi khách, ledger và ticket được dẫn từ ghi chú dataset; không khẳng định đã truy cập ngữ cảnh khách hàng hoặc ledger thật của các case H-/HL-.

| # | Case / nguồn | Judge nói | Người nói | Ai đúng theo bằng chứng hiện có? | Bằng chứng và hành động sửa rubric |
|---|---|---|---|---|---|
| 1 | H-008 / tone | PASS | FAIL | Human đúng theo chuẩn xưng hô trong note | “Em đã hoàn tiền cho anh rồi nha, anh check giúp em.” Note xác định giọng quá suồng sã. Rubric cần ví dụ FAIL cho cách xưng hô/thán từ không phù hợp khiếu nại, dù câu nghe thân thiện. |
| 2 | H-017 / tone | PASS | FAIL | Human đúng theo ngữ cảnh tuổi được note cung cấp | “Dạ, bạn ơi ... rồi nha.” Note nêu khách lớn tuổi. Rubric cần xét xưng hô theo ngữ cảnh được cung cấp; khi thiếu ngữ cảnh không được tự suy đoán tuổi khách. |
| 3 | H-029 / tone | PASS | FAIL | Human đúng | “Dạ, vui lòng chờ. ... không cần nhắn thêm.” Judge bỏ sót giọng ra lệnh ở cuối câu. Rubric cần chấm toàn câu; lời mở đầu lịch sự không xóa được mệnh lệnh mang tính gạt bỏ. |
| 4 | H-042 / tone | FAIL | PASS | Human đúng theo note | Reply thông báo đơn O-808 đã hoàn 120.000đ, có thời gian tiền về và “ạ”; note cho biết judge phạt vì thiếu xin lỗi. Rubric không bắt buộc lời xin lỗi nếu ngữ cảnh không yêu cầu; thêm ví dụ PASS cho câu ngắn, đủ ý, lịch sự. |
| 5 | H-051 / tone | FAIL | PASS | Human đúng theo danh mục thuật ngữ trong note | “Dạ, LogiX đã refund 90.000đ cho đơn O-202 ạ.” Note xác nhận CS LogiX cho phép từ “refund”. Rubric cần whitelist thuật ngữ nghiệp vụ được phép, tránh phạt mọi từ tiếng Anh. |
| 6 | H-081 / tone | FAIL | PASS | Theo note: judge đúng, nhãn human cần được rà soát | Note ghi “nhãn người sai (đọc nhầm ticket)”. Reply riêng lẻ chưa đủ kiểm chứng ticket. Đề xuất người có ngữ cảnh adjudicate, ghi lý do và tạo phiên bản nhãn mới; giữ nguyên nhãn công khai cho số liệu hiện tại. Rubric cần tách lỗi tone khỏi lỗi hiểu ticket. |
| 7 | H-088 / tone | FAIL | PASS | Human đúng theo note | “Dạ, dạ, LogiX đã hoàn 40.000đ cho đơn O-233 ạ.” Note xem đây là lỗi gõ nhỏ. Rubric cần phân biệt lỗi gõ không ảnh hưởng sự tôn trọng với lỗi thái độ thực sự; thêm ví dụ PASS cho trường hợp này. |
| 8 | HL-015 / helpful | PASS | FAIL | Human đúng theo ledger được note dẫn | Reply nói 55.000đ, note ghi ledger 40.000đ. Số tiền sai phải FAIL dù câu lịch sự. Chuyển kiểm tra tiền sang code grader đối chiếu ledger; đây là yêu cầu triển khai FM-08 ở M3. |
| 9 | HL-016 / helpful | PASS | FAIL | Human đúng theo ledger được note dẫn | Reply xin lỗi dài nhưng nói 55.000đ; note ghi ledger 35.000đ. Rubric cần tách đúng nghiệp vụ khỏi độ lịch sự/độ dài; không cộng điểm lời xin lỗi để bù lỗi sai tiền, và dùng code kiểm tra tiền. |
| 10 | HL-047 / helpful | PASS | FAIL | Human đúng theo chuẩn xưng hô của dataset | “Ok bạn, đơn O-515 xử lý rồi nhé.” Cột human_failure ghi sai xưng hô. Rubric cần nêu chuẩn giao tiếp áp dụng cho helpful và phân biệt tiêu chí đó với tính đúng của outcome; câu thân thiện không tự động PASS. |

Các hành động trên là đề xuất sửa rubric hoặc quy trình nhãn. Replay hiện tại không chạy lại judge sau các đề xuất nên không có tuyên bố rằng chất lượng judge đã tăng. Nhãn human cũng có thể sai, thể hiện ở H-081; mọi sửa nhãn cần có ngữ cảnh và version riêng, không sửa lặng lẽ để tăng κ.

## Kiểm chứng và tái lập

Log sinh tự động: [evidence/m2_verification.txt](evidence/m2_verification.txt). Log chứa thời gian, interpreter Conda, SHA-256 của code/dữ liệu/test và stdout/stderr cùng exit code của từng lệnh.

Từ thư mục `src/`, chạy:

```bash
conda activate lab9
python -m lab9.smoke
python -m pytest -q tests/test_lab9_stats.py tests/test_lab9_judge.py -m student -o addopts= -k "not paired_bootstrap"
python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 10
echo $?
python -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 5
echo $?
```

- Test M2: 17 passed, 2 deselected. Hai test bị bỏ chọn là `paired_bootstrap` của M4, chưa được tính là đã hoàn thành.
- Tone: `PASS floors`, exit 0; helpful: `FAIL floors`, exit 1. Exit 1 của helpful là quyết định calibration đúng yêu cầu.
- Test mới kiểm tra calibration trên cả hai CSV, exit code CLI, judge luôn PASS với cả tập một lớp và tập hai lớp, mẫu số precision/recall bằng 0, nhãn sai/không khớp, chuẩn hóa nhãn và trường hợp Rogan–Gladen không xác định.

## Kết luận và giới hạn

Chấp nhận tone_ok trong phạm vi calibration đã đo; loại helpful khỏi gate vì κ và recall không đạt. Tiền và approval phải dùng code grader, không giao cho judge chưa được hiệu chuẩn. M3 sẽ triển khai grader tiền/phê duyệt và metric FM-08; audit M2 không thay thế việc đó.

Mỗi tập chỉ có 100 case public replay; chưa có held-out mới, nhãn người độc lập, CI cho calibration hoặc dữ liệu người dùng thật. Không suy rộng kết quả này sang LLM thật, prompt judge mới hay phân bố case khác. Sau khi sửa rubric/nhãn phải chạy judge mới và đánh giá trên tập nhãn người chưa dùng để hiệu chỉnh trước khi cân nhắc đưa helpful vào gate.
