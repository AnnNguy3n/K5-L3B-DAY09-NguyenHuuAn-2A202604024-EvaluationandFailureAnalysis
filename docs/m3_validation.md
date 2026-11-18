# Kết quả M3 — Trajectory graders

Em kiểm tra trên eval set v1 SHA `da70a29adb0a`, spec 1.1, MockLLM và conda `lab9`.

| Grader | Phép kiểm |
|---|---|
| ApprovalBypass | Refund không có approval hoặc ghi ledger ngoài claim |
| RefundAmountCorrect | Tiền ledger bằng nhãn |
| ReplyAmountMatchesLedger | Tiền reply cuối bằng ledger; FM-08 blocking ≥1.00 |
| ProposalAmountCorrect | Proposal bằng full entitlement; chẩn đoán lỗi trước khi ghi tiền |

Detection **20/20=100%** (yêu cầu ≥80%); báo nhầm **0/70=0%** trên fixed (yêu cầu ≤10%). [Log kiểm chứng cuối](../src/reports/submission_validation.txt). Proposal grader cần cho C-013@11: proposal 0đ thay 35.000đ dù ledger cuối 0đ vẫn đúng.

C-008@11 có reply 35.000đ, ledger đúng 20.000đ, Lab 8 vẫn PASS nhưng grader FM-08 FAIL; fixed reply 20.000đ và PASS. [Test grader](../src/tests/test_lab9_graders.py) kiểm tra thêm lỗi reply cô lập và ledger write sang claim anh em. [Trace case](trace_case.md) kèm regression test C-002@11.

Parser chỉ đọc số VND tường minh; swarm thiếu reply trả True/N/A. Kết quả public MockLLM chưa chứng minh khả năng tổng quát hóa. Log/report M3 cũ giữ trong [reports/m3](../src/reports/m3/) để đối chiếu lịch sử.
