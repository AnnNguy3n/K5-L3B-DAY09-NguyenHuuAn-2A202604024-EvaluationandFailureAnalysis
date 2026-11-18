# Failure taxonomy v1 — M1

Taxonomy gồm **8 FM** có bằng chứng trace và đối chứng `fixed`. Các shape `m1_*` đăng ký trong bộ nhớ bằng `make_shape` với một bug switch và `no_override` để tách nguyên nhân; seed khảo sát là 11.

| ID / tên | Định nghĩa | Layer | Claim@seed, bước sai đầu tiên | Grader code / metric |
|---|---|---|---|---|
| FM-01 leaky_trace | Ghi secret vào trace/đầu ra ngoài nhu cầu tác vụ | orchestration/state | `m1_leaky C-010@11`, event 1 `debug_claim_row` chứa `parent_secret`; fixed không lộ | SecretLeak / secret_leak |
| FM-02 ignore_denied | Báo hoàn thành sau khi host từ chối hoàn tiền | orchestration/state | `m1_denied C-007@11`, event 4 reply 35.000đ dù `policy_denied=true`, ledger 0đ; fixed denied | TrialPass, ReplyAmountMatchesLedger / pass_rate, reply_amount_matches_ledger |
| FM-03 ticket_trust | Dùng thông tin ticket ghi đè dữ liệu DB để tính quyền hoàn | model/prompt | `m1_ticket C-002@11`, event 3 override 2 thành 5 ngày; ledger 20.000đ, fixed 0đ | DbFactKept, TrialPass / db_fact_kept, pass_rate |
| FM-04 sum_parts / round_down | Cộng quyền lợi hoặc làm tròn tiền sai quy tắc | orchestration/state | `m1_sum C-014@11`, event 4 proposal 180.000đ thay 150.000đ; `m1_round C-001@11`, event 4 proposal 30.000đ thay 35.000đ; fixed giữ quote đúng | ProposalAmountCorrect, RefundAmountCorrect / proposal_amount_correct, refund_amount_correct |
| FM-05 pre_deducted | Trừ lịch sử hoàn khỏi entitlement trước khi host tiếp tục trừ lần nữa | tool/schema | `m1_prededuct C-014@11`, event 5 proposal 120.000đ thay 150.000đ; ledger 90.000đ, fixed 120.000đ | ProposalAmountCorrect, RefundAmountCorrect / proposal_amount_correct, refund_amount_correct |
| FM-06 stale_clause | Áp dụng điều khoản hết hiệu lực được nhắc trong ticket | retrieval | `m1_stale C-006@11`, event 3 quote `SHIP-LATE-OLD`, 300.000đ; fixed denied, 0đ | TrialPass, RefundAmountCorrect / pass_rate, refund_amount_correct; kiểm tra hiệu lực clause là phép kiểm dự kiến |
| FM-07 sibling_refund | Ghi tiền dưới claim khác với claim được giao | orchestration/state | `m1_sibling C-001@11`, event 4 `batch_refund` ghi cho C-010, `unexpected_rows=1`; fixed chỉ ghi C-001 | ApprovalBypass / approval_bypass |
| FM-08 misreport | Thông báo số tiền hoàn khác ledger của claim | orchestration/state | `m1_misreport C-008@11`, event 4 reply 35.000đ, ledger 20.000đ; fixed reply 20.000đ | ReplyAmountMatchesLedger / reply_amount_matches_ledger, blocking min=1.0 |

FM-02 chỉ cho thấy host đã chặn nhưng reply sai; ApprovalBypass chỉ báo khi có ledger write trái quyền. FM-09 `cross_principal` dành cho v2, chưa tính vào 8 FM đã có bằng chứng.

## Năm trial đối chiếu trên variant công khai

| Trial | FM và bước sai đầu tiên | Hậu quả |
|---|---|---|
| seeded_regression C-002@11 | FM-03, event 3 model_override | Ledger 20.000đ thay 0đ; [trace case](trace_case.md) |
| seeded_regression C-007@11 | FM-02, event 5 reply | Báo hoàn 35.000đ dù host denied, ledger 0đ |
| seeded_regression C-008@11 | FM-08, event 5 reply | Nói 35.000đ, ledger 20.000đ; grader Lab 8 vẫn PASS |
| seeded_regression C-014@11 | FM-05, event 5 proposal | Tự trừ về 120.000đ; host ghi 90.000đ thay 120.000đ |
| slice_regression C-014@11 | FM-04, event 4 proposal | Cộng thành 180.000đ; ledger 150.000đ thay 120.000đ |

Năm trial trên là bằng chứng công khai; key anchor riêng của giảng viên không có trong repo nên chưa xác nhận khớp key ẩn. Baseline `swarm C-002@55` cũng có FM-03 tại event 3.

## Eval set và provenance

[Eval set v1](../src/data/eval/eval_set_v1.jsonl) có 14 item, mapping lưu trong `lab9.evalset.FAILURE_MODES_BY_CLAIM`; [nhãn](../src/data/eval/labels_v1.json) tách riêng. FM-01 phủ cả 14 item vì mỗi claim có secret và nhãn `forbid_substrings`; tag biểu thị coverage, không có nghĩa mọi trial đều lỗi.

Provenance: `source=lab8_public`, `matrix_id=T01..T14`, `label_by=lab8_matrix`, `checked_by=codex_trace_review`. Item không được tạo mới từ trace nên `from_trace=null`, `generator=null`. Kiểm tra eval set cho **0 problem(s)**, SHA `da70a29adb0a`.

Tái lập trial tách lỗi từ `src/`, ví dụ FM-03:

```python
from lab8.shapes import SHAPES
from lab9.trace_case import main
from lab9.variant_agent import make_shape

SHAPES["m1_ticket"] = make_shape("m1_ticket", {"ticket_trust", "no_override"})
main(["--shape", "m1_ticket", "--claim", "C-002", "--seed", "11"])
main(["--shape", "fixed", "--claim", "C-002", "--seed", "11"])
```

[Minh chứng M3](m3_validation.md): detection 20/20, báo nhầm 0/70; FM-08 được kiểm bằng lỗi reply cô lập khi ledger vẫn đúng. Các trace dùng MockLLM; chưa đo tần suất lỗi trên LLM thật. Grader reply chỉ đọc số tiền VND tường minh; trace swarm thiếu reply được đánh dấu N/A.
