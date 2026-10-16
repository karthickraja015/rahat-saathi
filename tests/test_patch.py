from datetime import timedelta
from pathlib import Path

import pytest

from backend.models import Facts, now_ist
from backend.rules_engine import evaluate_eligibility
from backend.summary import render_result

JS = (Path(__file__).resolve().parent.parent / "frontend" / "app.js").read_text(encoding="utf-8")
COLLECTOR = {"hit_and_run_collector", "hit_and_run_unknown", "uninsured_collector",
             "insured_unsure", "insurance_unknown", "insured_unknown"}


def case(**kw):
    now = now_ist()
    base = dict(accident_at=(now - timedelta(hours=3)).isoformat(), motor_vehicle="yes", life_threatening="no",
                hospitalised_at=(now - timedelta(hours=2)).isoformat(), hospital_type="designated",
                police_informed="yes", police_informed_at=(now - timedelta(hours=1)).isoformat(),
                hit_and_run="no", insured="yes", state="Tamil Nadu")
    base.update(kw)
    facts = Facts.from_dict(base)
    return now, facts, evaluate_eligibility(facts, now)


@pytest.mark.parametrize("lang", ["en", "hi", "ta"])
def test_no_vehicle_hides_collector_content(lang):
    now, facts, res = case(motor_vehicle="no", hit_and_run="yes", insured="no")
    d = render_result(res, facts, lang, now)
    assert d["status"]["code"] == "likely_not_eligible"
    assert not ({r["code"] for r in d["reasons"]} & COLLECTOR)
    assert d["escalation"]["route"] == "hospital_and_police"


def test_vehicle_yes_hit_and_run_keeps_route_code_without_collector_application():
    now, facts, res = case(hit_and_run="yes")
    d = render_result(res, facts, "en", now)
    assert d["escalation"]["route"] == "district_collector"
    assert {r["code"] for r in d["reasons"]} & COLLECTOR
    assert "collector" not in [g["group"] for g in d["checklist"]]
    assert "need to apply" in d["escalation"]["text"]


def test_admitted_in_time_hides_first_admission_deadline():
    now, facts, res = case()
    assert "hospitalisation_deadline" not in [x["key"] for x in render_result(res, facts, "en", now)["deadlines"]]


def test_late_admission_keeps_first_admission_deadline():
    now = now_ist()
    now, facts, res = case(accident_at=(now - timedelta(hours=40)).isoformat(),
                           hospitalised_at=(now - timedelta(hours=5)).isoformat())
    assert "hospitalisation_deadline" in [x["key"] for x in render_result(res, facts, "en", now)["deadlines"]]


def test_police_deadline_has_basis_and_no_invented_safe_date():
    now, facts, res = case()
    d = render_result(res, facts, "en", now)
    keys = [x["key"] for x in d["deadlines"]]
    assert "police_deadline" in keys and "stabilisation_end" not in keys
    item = next(x for x in d["deadlines"] if x["key"] == "police_deadline")
    assert item.get("basis") and "safe_text" not in item
    assert "Counted from" in d["summary_text"]


def test_police_wording_follows_guideline():
    from backend import translator as T
    assert "eDAR" in T.STRINGS["en"]["question"]["police_informed"]
    assert "confirmed" in T.STRINGS["en"]["reason"]["police_in_time"]


def test_frontend_hides_dependent_fields_and_shows_basis():
    assert JS.count('values.motor_vehicle !== "no"') == 2
    assert "x.basis" in JS
