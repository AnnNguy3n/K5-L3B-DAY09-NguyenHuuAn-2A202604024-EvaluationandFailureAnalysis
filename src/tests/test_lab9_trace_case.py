"""M1: observe the ticket-over-DB regression and its fixed control offline."""

import pytest

pytestmark = pytest.mark.student


@pytest.fixture(scope="module")
def c002_trials():
    from lab9.trace_case import investigate

    return {shape: investigate(shape, "C-002", 11)
            for shape in ("seeded_regression", "fixed")}


def test_c002_fixed_respects_database_and_expected_outcome(c002_trials):
    case = c002_trials["fixed"]
    trial, label = case["trial"], case["label"]

    assert trial["lab8_pass"], trial["lab8_reason"]
    assert trial["result"]["status"] == label["status"] == "denied"
    assert trial["snapshot"]["refund_vnd"] == label["refund_vnd"] == 0
    assert not any(event["kind"] == "model_override" for event in trial["events"])


def test_c002_regression_overrides_database_before_wrong_refund(c002_trials):
    case = c002_trials["seeded_regression"]
    trial, label = case["trial"], case["label"]
    events = trial["events"]
    investigator = next(event for event in events if event["kind"] == "investigator")
    override_index = next(i for i, event in enumerate(events) if event["kind"] == "model_override")
    quote_index = next(i for i, event in enumerate(events) if event["kind"] == "quote")

    assert investigator["payload"]["lookup_order"]["order"]["delay_days"] == 2
    assert events[override_index]["payload"]["delay_days"] == 5
    assert override_index < quote_index
    assert not trial["lab8_pass"]
    assert trial["result"]["status"] == "resolved" != label["status"]
    assert trial["snapshot"]["refund_vnd"] == 20000 > label["refund_vnd"]
