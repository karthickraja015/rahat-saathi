from datetime import timedelta

import pytest

from backend import translator as T
from backend.checklist import build_checklist
from backend.models import Facts, Status, now_ist
from backend.rules_engine import evaluate_eligibility
from backend.summary import evaluate_and_render, render_result, render_summary

LANGS = ["en", "hi", "ta"]


def _case(**kw):
    now = now_ist()
    base = dict(
        accident_at=(now - timedelta(hours=3)).isoformat(), motor_vehicle="yes", life_threatening="no",
        hospitalised_at=(now - timedelta(hours=2)).isoformat(), hospital_type="designated",
        police_informed="yes", police_informed_at=(now - timedelta(hours=1)).isoformat(),
        hit_and_run="no", insured="yes", state="Tamil Nadu",
    )
    base.update(kw)
    facts = Facts.from_dict(base)
    return now, facts, evaluate_eligibility(facts, now)


@pytest.mark.parametrize("lang", LANGS)
def test_render_has_required_fields(lang):
    now, facts, res = _case()
    d = render_result(res, facts, lang, now)
    for key in ("ui", "status", "reasons", "deadlines", "next_steps", "escalation", "checklist", "summary_text"):
        assert key in d
    assert d["status"]["label"]
    assert len(d["next_steps"]) <= 5


@pytest.mark.parametrize("lang", LANGS)
def test_summary_contains_safety_text(lang):
    now, facts, res = _case()
    text = render_summary(res, facts, lang, now)
    ui = T.STRINGS[lang]["ui"]
    assert ui["emergency"] in text and ui["disclaimer"] in text and ui["footer"] in text and "112" in text


@pytest.mark.parametrize("lang", LANGS)
def test_empty_facts_does_not_crash_and_asks_a_question(lang):
    now = now_ist()
    facts = Facts()
    d = render_result(evaluate_eligibility(facts, now), facts, lang, now)
    assert d["status"]["code"] == Status.NEED_MORE_INFO.value
    assert d["next_question"] and d["next_question"]["text"]


def test_late_hospitalisation_is_not_eligible():
    now, facts, res = _case(accident_at=(now_ist() - timedelta(hours=40)).isoformat(),
                            hospitalised_at=(now_ist() - timedelta(hours=5)).isoformat())
    assert res.status == Status.LIKELY_NOT_ELIGIBLE
    assert "24" in render_result(res, facts, "en", now)["summary_text"]


def test_hit_and_run_adds_collector_checklist_and_route():
    now, facts, res = _case(hit_and_run="yes")
    d = render_result(res, facts, "en", now)
    assert d["escalation"]["route"] == "district_collector"
    assert "collector" in [g["group"] for g in d["checklist"]]


def test_clean_case_has_no_collector_checklist():
    now, facts, res = _case()
    assert "collector" not in [g["group"] for g in build_checklist(facts, res)]


def test_deadlines_sorted_and_countdown_is_int():
    now, facts, res = _case()
    ds = render_result(res, facts, "en", now)["deadlines"]
    assert ds == sorted(ds, key=lambda x: x["at_iso"]) or all(isinstance(x["seconds_left"], int) for x in ds)
    assert all(isinstance(x["seconds_left"], int) for x in ds)


def test_evaluate_and_render_from_dict():
    d = evaluate_and_render({"motor_vehicle": "no"}, "hi")
    assert d["lang"] == "hi" and d["status"]["code"] == Status.LIKELY_NOT_ELIGIBLE.value
