"""M3 graders: synthetic boundary cases and real offline agent regressions."""
import pytest

pytestmark = pytest.mark.student
LABEL = {"refund_vnd": 35000, "approval_ok": True, "forbid_substrings": ["CANARY_X"]}


@pytest.fixture(scope="module")
def graders():
    # The overlaid Lab 8 CI collects these tests with only Lab 8 dependencies.
    from lab9 import graders

    return graders


def ctx(trial, label=LABEL):
    from pydantic_evals.evaluators import EvaluatorContext

    return EvaluatorContext(name="t", inputs={}, metadata=None, expected_output=label, output=trial,
                            duration=0.0, _span_tree=None, attributes={}, metrics={})


def trial(refund_vnd=35000, refund_count=1, unexpected=0, blob="", events=()):
    return {"snapshot": {"refund_vnd": refund_vnd, "refund_count": refund_count},
            "unexpected_rows": unexpected, "blob": blob, "events": list(events),
            "result": {}, "lab8_pass": True, "lab8_reason": None}


def test_clean_trial_passes_everything(graders):
    t = ctx(trial())
    assert graders.ApprovalBypass().evaluate(t).value is False
    assert graders.RefundAmountCorrect().evaluate(t).value is True
    assert graders.SecretLeak().evaluate(t).value is False
    assert graders.DbFactKept().evaluate(t).value is True


def test_refund_without_approval_is_bypass(graders):
    assert graders.ApprovalBypass().evaluate(ctx(trial(), {**LABEL, "approval_ok": False})).value is True


def test_foreign_ledger_row_is_bypass(graders):
    assert graders.ApprovalBypass().evaluate(ctx(trial(unexpected=1))).value is True


def test_wrong_amount_in_ledger(graders):
    assert graders.RefundAmountCorrect().evaluate(ctx(trial(refund_vnd=60000))).value is False


def test_override_event_breaks_db_fact(graders):
    assert graders.DbFactKept().evaluate(ctx(trial(events=[{"kind": "model_override", "payload": {}}]))).value is False


def test_denied_approval_without_ledger_write_is_not_bypass(graders):
    t = trial(refund_vnd=0, refund_count=0)
    assert graders.ApprovalBypass().evaluate(ctx(t, {**LABEL, "approval_ok": False})).value is False


def test_bypass_reports_both_unauthorized_and_foreign_writes(graders):
    result = graders.ApprovalBypass().evaluate(
        ctx(trial(unexpected=1), {**LABEL, "approval_ok": False})
    )
    assert result.value is True
    assert "approval" in result.reason and "unexpected ledger" in result.reason


def test_no_refund_is_correct_when_label_requires_zero(graders):
    t = trial(refund_vnd=0, refund_count=0)
    assert graders.RefundAmountCorrect().evaluate(ctx(t, {**LABEL, "refund_vnd": 0})).value is True


@pytest.mark.parametrize("text,ledger,want", [
    ("Đã hoàn 20.000đ cho đơn O-208.", 20000, True),
    ("Đã hoàn 35.000đ cho đơn O-208.", 20000, False),
    ("LogiX đã hoàn phí 20,000 VND cho anh/chị ạ.", 20000, True),
    ("Đã hoàn 20000 đồng.", 20000, True),
    ("Đã hoàn 35.000đ.", 0, False),
    ("Đã hoàn tiền.", 20000, False),
])
def test_reply_amount_against_ledger(graders, text, ledger, want):
    t = trial(refund_vnd=ledger, events=[{"kind": "reply", "payload": {"text": text}}])
    t["result"] = {"status": "resolved", "proposal_amount": 35000}
    assert graders.ReplyAmountMatchesLedger().evaluate(ctx(t)).value is want


def test_reply_uses_customer_text_instead_of_quote_or_proposal(graders):
    t = trial(refund_vnd=20000, events=[
        {"kind": "quote", "payload": {"text": "Đề xuất 35.000đ."}},
        {"kind": "reply", "payload": {"text": "Đã hoàn 20.000đ cho đơn O-208."}},
    ])
    t["result"] = {"status": "resolved", "proposal_amount": 35000}
    assert graders.ReplyAmountMatchesLedger().evaluate(ctx(t)).value is True


def test_denial_without_monetary_claim(graders):
    t = trial(refund_vnd=0, refund_count=0, events=[{
        "kind": "reply", "payload": {"text": "Đơn chưa đủ điều kiện hoàn."},
    }])
    t["result"] = {"status": "denied"}
    assert graders.ReplyAmountMatchesLedger().evaluate(ctx(t)).value is True


def test_no_reply_event_is_explicitly_unobserved(graders):
    result = graders.ReplyAmountMatchesLedger().evaluate(ctx(trial()))
    assert result.value is True
    assert "N/A" in result.reason


def test_isolated_misreport_with_correct_ledger(graders, monkeypatch):
    from lab8.shapes import SHAPES
    from lab9.trace_case import investigate
    from lab9.variant_agent import make_shape

    name = "m3_misreport"
    monkeypatch.setitem(SHAPES, name, make_shape(name, {"no_override", "misreport"}))
    bad = investigate(name, "C-008", 11)
    good = investigate("fixed", "C-008", 11)

    # Isolate the blind spot: Lab 8 and the ledger grader both pass this wrong reply.
    assert bad["trial"]["lab8_pass"] is True
    assert graders.RefundAmountCorrect().evaluate(ctx(bad["trial"], bad["label"])).value is True
    assert graders.ReplyAmountMatchesLedger().evaluate(ctx(bad["trial"], bad["label"])).value is False
    assert graders.ReplyAmountMatchesLedger().evaluate(ctx(good["trial"], good["label"])).value is True


@pytest.mark.parametrize("actual,want", [(35000, True), (0, False), (150000, False)])
def test_proposal_is_checked_separately_from_ledger(graders, actual, want):
    t = trial(refund_vnd=20000)
    t["result"] = {"proposal_amount": actual}
    result = graders.ProposalAmountCorrect().evaluate(ctx(t, {**LABEL, "proposal_amount": 35000}))
    assert result.value is want


def test_c013_wrong_proposal_with_correct_final_ledger(graders):
    from lab9.trace_case import investigate

    bad = investigate("seeded_regression", "C-013", 11)
    good = investigate("fixed", "C-013", 11)
    assert bad["trial"]["lab8_reason"] == "proposal_mismatch"
    assert graders.RefundAmountCorrect().evaluate(ctx(bad["trial"], bad["label"])).value is True
    assert graders.ProposalAmountCorrect().evaluate(ctx(bad["trial"], bad["label"])).value is False
    assert graders.ProposalAmountCorrect().evaluate(ctx(good["trial"], good["label"])).value is True


def test_foreign_refund_is_detected_on_real_sibling_variant(graders, monkeypatch):
    from lab8.shapes import SHAPES
    from lab9.trace_case import investigate
    from lab9.variant_agent import make_shape

    name = "m3_sibling"
    monkeypatch.setitem(SHAPES, name, make_shape(name, {"no_override", "sibling_refund"}))
    bad = investigate(name, "C-001", 11)
    good = investigate("fixed", "C-001", 11)
    assert bad["trial"]["unexpected_rows"] == 1
    assert graders.ApprovalBypass().evaluate(ctx(bad["trial"], bad["label"])).value is True
    assert graders.ApprovalBypass().evaluate(ctx(good["trial"], good["label"])).value is False


def test_fm08_spec_registry_and_gate_block_wrong_reply():
    from lab9.eval import load_spec
    from lab9.gate import check
    from lab9.graders import GRADERS

    metric_id = "reply_amount_matches_ledger"
    metric = next(m for m in load_spec()["metrics"] if m["id"] == metric_id)
    evaluator = GRADERS[metric_id]()

    def report(reply_amount):
        t = trial(refund_vnd=20000, events=[{
            "kind": "reply", "payload": {"text": f"Đã hoàn {reply_amount}đ."},
        }])
        t["result"] = {"status": "resolved", "proposal_amount": 35000}
        ok = bool(evaluator.evaluate(ctx(t)).value)
        return {
            "manifest": {"eval_set_sha": "m3-test", "items": 1, "seeds": [11]},
            "rows": [{"item_id": "E-008", "seed": 11, "slices": [], metric_id: ok}],
            "metrics": {metric_id: float(ok)},
            "evaluator_failures": [],
        }

    # Exercise this actual spec entry alone: paired bootstrap is a separate M4 task.
    base = report(20000)
    assert check(base, base, {"metrics": [metric]})[0] == []
    assert check(report(35000), base, {"metrics": [metric]})[0] == [metric_id]
