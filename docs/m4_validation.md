# M4 — Paired bootstrap và bằng chứng gate

Kiểm chứng lúc **18/11/2026 12:44:24 +0700**, bằng conda `lab9`: Python 3.13.18, SciPy 1.18.1, NumPy 2.5.5, pydantic-evals 2.68.0, pytest 8.4.2.
Interpreter thực tế: `/opt/miniconda3/envs/lab9/bin/python`.

## Phạm vi và nguồn thay đổi

Trước lượt hoàn thiện này, commit `b57fed5` đã có cài đặt `paired_bootstrap`, harness map version 1.2 và bốn report M4. Lượt này giữ cách tính đã có, bổ sung tài liệu cho hàm, chuẩn hóa import và newline, thêm test độc lập cho các điều kiện quyết định gate, viết script tái lập và lưu bằng chứng chạy lại.

| Công việc hoàn thiện/kiểm chứng | Minh chứng |
|---|---|
| Xác nhận bootstrap ghép cặp theo item, PR trừ baseline, percentile, seed tái lập | [stats.py](../src/lab9/stats.py), [test stats](../src/tests/test_lab9_stats.py) |
| Bổ sung 11 test bootstrap: giữ cặp, tái lập với cấu hình riêng, dữ liệu và cấu hình không hợp lệ | [test stats](../src/tests/test_lab9_stats.py), [log pytest](../src/reports/m4/pytest_core.txt) |
| Bổ sung 8 test gate: baseline tự so, sàn và CI độc lập, CI chạm 0, thứ tự row, safety và SHA eval set | [test gate](../src/tests/test_lab9_gate.py) |
| Kiểm tra section eval trong harness map 1.2 và đường dẫn baseline | [harness map](../src/harness_map.yaml), [verification JSON](../src/reports/m4/verification.json) |
| Sinh lại baseline từ swarm, PR swarm, fixed và seeded_regression bằng CLI chính thức | Bốn report trong bảng dưới và log từng lệnh |
| Chạy các kiểm tra Core tương ứng workflow hiện có, thêm self-comparison và kiểm tra cấu trúc report | [script tái lập](../src/scripts/verify_m4.py), [verification JSON](../src/reports/m4/verification.json) |
| Lưu stdout, stderr, exit code, JUnit XML, phiên bản môi trường và SHA-256 code/dữ liệu/report | [thư mục bằng chứng](../src/reports/m4/), [JUnit XML](../src/reports/m4/pytest_core.xml) |

Không thay đổi code Lab 8, public claims/labels, failure-mode tags, ngưỡng metric, variants, traps hoặc workflow để làm gate đạt. Bốn report được sinh lại bằng `lab9.eval` và không có diff so với report đã commit; không chỉnh tay số liệu JSON.

## Kết quả test và kiểm tra dữ liệu

- Smoke: `M0 PASS`, exit 0.
- Eval set: SHA `da70a29adb0a`, `0 problem(s)`, exit 0.
- Bộ test Core theo selector của workflow: **65 passed, 317 deselected**, không có failure/error.
- 12/12 lệnh kiểm chứng có exit code và verdict đúng mong đợi. Exit 1 của seeded_regression được tính là PASS vì đây là hồi quy cần chặn; script còn yêu cầu danh sách metric bị chặn chứa `pass_rate` để tránh nhầm với exception Python.

| Bước / log | Exit thực tế | Exit yêu cầu | Kết quả |
|---|---:|---:|---|
| [smoke](../src/reports/m4/smoke.txt) | 0 | 0 | PASS |
| [pytest_core](../src/reports/m4/pytest_core.txt) | 0 | 0 | PASS |
| [evalset_check](../src/reports/m4/evalset_check.txt) | 0 | 0 | PASS |
| [baseline_v1](../src/reports/m4/baseline_v1.txt) | 0 | 0 | PASS |
| [eval_pr](../src/reports/m4/eval_pr.txt) | 0 | 0 | PASS |
| [eval_fixed](../src/reports/m4/eval_fixed.txt) | 0 | 0 | PASS |
| [eval_seeded_regression](../src/reports/m4/eval_seeded_regression.txt) | 0 | 0 | PASS |
| [gate_baseline_self](../src/reports/m4/gate_baseline_self.txt) | 0 | 0 | PASS |
| [gate_pr](../src/reports/m4/gate_pr.txt) | 0 | 0 | PASS |
| [ci_check](../src/reports/m4/ci_check.txt) | 0 | 0 | PASS |
| [gate_fixed](../src/reports/m4/gate_fixed.txt) | 0 | 0 | PASS |
| [gate_seeded_regression](../src/reports/m4/gate_seeded_regression.txt) | 1 | 1 | PASS |

## Report và paired CI

Tất cả report dùng metric spec **1.1**, eval set **v1** SHA `da70a29adb0a`, 14 item × 5 seed = **70 row**. Seeds: 11, 22, 33, 44, 55. Script kiểm tra đủ tập `(item_id, seed)`, không có row trùng/thiếu, mọi giá trị grader là boolean, metric hữu hạn và `evaluator_failures=[]`.

Bootstrap lấy trung bình theo seed trước, rồi resample 14 cặp item. Cấu hình: `paired=True`, `method=percentile`, `1000` resamples, RNG `2027`, confidence `0.95`. Δ = PR − baseline. Baseline phải là shape `swarm`; baseline và PR dùng cùng eval set, seeds và spec.

| Report | Run ID | pass_rate | Δ | CI 95% |
|---|---|---:|---:|---|
| [baseline_v1](../src/reports/baseline_v1.json) | `E-swarm-20261118-da70` | 0.9857 | +0.000 | [+0.000, +0.000] |
| [eval_pr](../src/reports/eval_pr.json) | `E-swarm-20261118-da70` | 0.9857 | +0.000 | [+0.000, +0.000] |
| [eval_fixed](../src/reports/eval_fixed.json) | `E-fixed-20261118-da70` | 1.0000 | +0.014 | [+0.000, +0.043] |
| [eval_seeded_regression](../src/reports/eval_seeded_regression.json) | `E-seeded_regression-20261118-da70` | 0.7143 | -0.271 | [-0.500, -0.057] |

Gate trả exit 0 cho baseline so với chính nó, swarm của PR và fixed. Với seeded_regression, `pass_rate` thấp hơn sàn 0.85 và CI của Δ nằm hoàn toàn dưới 0, nên bị chặn. Δ và CI lệch không quá 0.01 so với checkpoint (−0.271, −0.500, −0.057).

Output để dán vào mô tả PR, trích từ log CLI:

```text
  pass_rate              0.7143   {"min": 0.85, "no_significant_drop": true} Δ -0.271 CI [-0.500, -0.057] BLOCK
exit 1 — blocked: refund_amount_correct, pass_rate, reply_amount_matches_ledger
```

`refund_amount_correct` cũng bị chặn do dưới sàn 0.95 mặc dù CI chạm 0. Metric FM-08 `reply_amount_matches_ledger` bị chặn do dưới sàn 1.0. Các cảnh báo metric không blocking không tự làm gate exit 1. [Log đầy đủ](../src/reports/m4/gate_seeded_regression.txt).

`lab9.ci_check` trả `exit 0 — baseline and spec look sound`: baseline là swarm, metrics khớp swarm chạy lại và spec có metric capability blocking riêng đã đăng ký grader. [Log](../src/reports/m4/ci_check.txt).

## Tái lập bằng conda lab9

Từ root repo:

```bash
conda run --no-capture-output -n lab9 python src/scripts/verify_m4.py
```

Script dùng `sys.executable` cho mọi subprocess Python nên tất cả lệnh con cùng interpreter conda `lab9`. Report gốc được sinh bằng `lab9.eval`; log và summary được script sinh tự động. `verification.json` lưu base commit và SHA-256 để nhận diện đúng phiên bản code đang kiểm chứng, kể cả khi các bổ sung chưa được commit.

Bằng chứng trong `src/reports/` bị gitignore. Khi đưa thay đổi lên repo, force-add bằng chứng:

```bash
git add src/lab9/stats.py src/harness_map.yaml src/tests/test_lab9_stats.py src/tests/test_lab9_gate.py src/scripts/verify_m4.py docs/m4_validation.md
git add -f src/reports/m4/*.txt src/reports/m4/*.json src/reports/m4/*.xml
```

## Trạng thái CI và giới hạn

Các bước Core của workflow đã chạy thành công **trên máy local bằng conda lab9**. GitHub Actions cũng xác nhận job **eval-gate SUCCESS** trên commit `b57fed5` qua [workflow run 44246652149](https://github.com/AnnNguy3n/K5-L3B-DAY09-NguyenHuuAn-2A202604024-EvaluationandFailureAnalysis/actions/runs/44246652149) (`workflow_dispatch`, nhánh `starter/d09`). [Minh chứng CI từ GitHub API](../src/reports/m4/github_ci_baseline.json) lưu SHA, kết luận từng job và từng step. Run này kiểm tra cài đặt bootstrap và baseline đã commit; bộ 65 test local còn kiểm tra các test bổ sung trong commit tiến độ. Khi đánh giá commit mới, đối chiếu `head_sha` của run với SHA commit đã push. Bộ test Core mới được workflow chọn tự động bởi `lab9 and not advanced`.

Job v2 không thực thi test Advanced vì chưa có baseline v2; kết quả này chỉ xác nhận M4/Core. Việc mở PR và merge vào `main` thuộc bước nộp bài, chưa thực hiện trong lượt kiểm chứng này.

Kiểm chứng này thuộc M4. TODO slice/integrity/pass@k/pass^k thuộc M5–M7; eval card và PRD tổng hợp Core vẫn là tài liệu ở bước tiếp theo. Dữ liệu là MockLLM, 14 item public và judge replay, chưa chứng minh chất lượng trên LLM hoặc người dùng thật. Metric reply trên swarm có thể trả N/A vì trace gốc không có event reply, như giới hạn đã ghi ở [M3](m3_validation.md).
