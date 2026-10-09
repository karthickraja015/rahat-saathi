import json
from datetime import timedelta

import backend.rules_engine as engine
from backend.models import Facts, Status
from backend.rules_engine import (
    compute_time_windows, evaluate_eligibility, next_question, route_escalation,
)
from tests.scenarios import ACC, BASE, H, NOW


def mk(**over):
    return Facts.from_dict({**BASE, **over})


# ---- windows
def test_windows_none_without_accident_time():
    assert compute_time_windows(Facts()) is None


def test_windows_standard():
    w = compute_time_windows(mk())
    assert w.cover_end == ACC + timedelta(days=7)
    assert w.hospitalisation_deadline == H(24)
    assert w.stabilisation_end == H(25) and w.police_deadline == H(25)
    assert w.lt_mode == "non_life_threatening"


def test_windows_life_threatening_48h():
    w = compute_time_windows(mk(life_threatening="yes"))
    assert w.stabilisation_end == H(49) and w.police_deadline == H(49)


def test_windows_unsure_uses_24h_and_flags_assumption():
    w = compute_time_windows(mk(life_threatening="unsure"))
    assert w.police_deadline == H(25)
    assert w.lt_mode == "non_life_threatening_assumed"


def test_windows_anchor_falls_back_to_accident():
    w = compute_time_windows(mk(hospitalised_at=None))
    assert w.stabilisation_end == H(24)
    assert w.anchors == {"stabilisation": "accident", "police": "accident"}


def test_windows_seconds_left_positive_and_negative():
    w = compute_time_windows(mk())
    assert w.to_dict(NOW)["deadlines"]["hospitalisation_deadline"]["seconds_left"] == 21 * 3600
    assert w.to_dict(H(30))["deadlines"]["hospitalisation_deadline"]["seconds_left"] == -6 * 3600


# ---- escalation
def test_escalation_none():
    e = route_escalation(mk(), NOW)
    assert e.route == "hospital_and_police" and e.triggers == []


def test_escalation_uninsured():
    assert route_escalation(mk(insured="no"), NOW).triggers == ["uninsured_vehicle"]


def test_escalation_hit_and_run():
    assert route_escalation(mk(hit_and_run="yes"), NOW).triggers == ["hit_and_run"]


def test_escalation_non_designated():
    assert route_escalation(mk(hospital_type="non_designated"), NOW).triggers == ["non_designated_stabilisation"]


def test_escalation_police_timeout_not_informed():
    e = route_escalation(mk(police_informed="no", police_informed_at=None), H(30))
    assert e.triggers == ["police_timeout"]


def test_escalation_police_late():
    e = route_escalation(mk(police_informed_at=H(26)), H(30))
    assert e.triggers == ["police_timeout"]


def test_escalation_all_triggers_in_order():
    e = route_escalation(mk(insured="no", hit_and_run="yes", hospital_type="non_designated",
                            police_informed="no", police_informed_at=None), H(30))
    assert e.triggers == ["uninsured_vehicle", "hit_and_run", "non_designated_stabilisation", "police_timeout"]
    assert e.route == "district_collector"


def test_escalation_without_accident_time_is_default():
    assert route_escalation(Facts(), NOW).route == "hospital_and_police"


# ---- one question at a time
def test_next_question_sequence():
    steps = [("accident_at", ACC, "motor_vehicle"), ("motor_vehicle", "yes", "life_threatening"),
             ("life_threatening", "no", "hospitalised_at"), ("hospitalised_at", H(1), "hospital_type"),
             ("hospital_type", "designated", "police_informed"),
             ("police_informed", "yes", "police_informed_at"),
             ("police_informed_at", H(2), "hit_and_run"), ("hit_and_run", "no", "insured"),
             ("insured", "yes", "state"), ("state", "Tamil Nadu", None)]
    d = {}
    assert next_question(Facts.from_dict(d)) == "accident_at"
    for k, v, expected in steps:
        d[k] = v
        assert next_question(Facts.from_dict(d)) == expected


def test_next_question_skips_police_time_when_not_informed():
    f = mk(police_informed="no", police_informed_at=None, hit_and_run=None)
    assert next_question(f) == "hit_and_run"


def test_unsure_counts_as_answered():
    f = mk(life_threatening="unsure", hit_and_run="unsure", insured="unsure", hospital_type="not_sure")
    assert next_question(f) is None


# ---- next steps
def test_next_steps_baseline():
    assert evaluate_eligibility(mk(), NOW).next_steps == ["ask_hospital_cashless", "keep_documents"]


def test_next_steps_capped_at_five_and_end_with_keep_documents():
    f = Facts.from_dict({"accident_at": ACC, "motor_vehicle": "unsure", "life_threatening": "unsure",
                         "hospitalised_at": H(1), "hospital_type": "non_designated",
                         "police_informed": "no", "insured": "no"})
    res = evaluate_eligibility(f, H(30))
    assert len(res.next_steps) <= 5 and res.next_steps[-1] == "keep_documents"


def test_next_steps_collector_when_uninsured():
    assert "approach_district_collector" in evaluate_eligibility(mk(insured="no"), NOW).next_steps


def test_next_steps_police_when_not_informed():
    res = evaluate_eligibility(mk(police_informed="no", police_informed_at=None), NOW)
    assert "get_police_confirmation" in res.next_steps


def test_next_steps_not_eligible_has_no_cashless_step():
    res = evaluate_eligibility(mk(hospitalised_at=H(30)), H(31))
    assert "ask_hospital_cashless" not in res.next_steps
    assert "ask_hospital_about_other_options" in res.next_steps


# ---- result / safety properties
def test_status_vocabulary_is_fixed():
    assert {s.value for s in Status} == {"likely_eligible", "at_risk", "likely_not_eligible",
                                         "need_more_information"}


def test_empty_facts_need_more_info_and_default_now_works():
    res = evaluate_eligibility(Facts())
    assert res.status == Status.NEED_MORE_INFO and res.next_question == "accident_at"


def test_result_is_json_serialisable_and_has_cover_limit():
    d = evaluate_eligibility(mk(), NOW).to_dict(NOW)
    json.dumps(d)
    assert d["cover_limit_inr"] == 150000
    assert d["status"] == "likely_eligible"


def test_result_never_says_definitely():
    text = json.dumps(evaluate_eligibility(mk(), NOW).to_dict(NOW)).lower()
    assert "definite" not in text


def test_engine_is_deterministic():
    a = evaluate_eligibility(mk(), NOW).to_dict(NOW)
    b = evaluate_eligibility(mk(), NOW).to_dict(NOW)
    assert a == b


def test_engine_module_has_no_ai_dependency():
    src = open(engine.__file__, encoding="utf-8").read().lower()
    assert "llm" not in src and "openai" not in src and "anthropic" not in src
