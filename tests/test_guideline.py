from datetime import timedelta
from pathlib import Path

import pytest

from backend import translator as T
from backend.models import Facts, now_ist
from backend.rules_engine import evaluate_eligibility
from backend.summary import render_result

JS = (Path(__file__).resolve().parent.parent / "frontend" / "app.js").read_text(encoding="utf-8")


def d_for(lang="en", **kw):
    now = now_ist()
    base = dict(accident_at=(now - timedelta(hours=3)).isoformat(), motor_vehicle="yes", life_threatening="no",
                hospitalised_at=(now - timedelta(hours=2)).isoformat(), hospital_type="designated",
                police_informed="yes", police_informed_at=(now - timedelta(hours=1)).isoformat(),
                hit_and_run="no", insured="yes", state="Tamil Nadu")
    base.update(kw)
    f = Facts.from_dict(base)
    return render_result(evaluate_eligibility(f, now), f, lang, now)


@pytest.mark.parametrize("lang", ["en", "hi", "ta"])
def test_help_section_names_helpline_in_every_language(lang):
    d = d_for(lang)
    assert len(d["help"]) == 3
    assert any("14555" in h for h in d["help"])
    assert "14555" in d["summary_text"]


@pytest.mark.parametrize("kw", [dict(hit_and_run="yes"), dict(insured="no"), dict(insured="unsure"), dict(hit_and_run="unsure")])
def test_collector_conditions_never_change_status(kw):
    base = d_for()["status"]["code"]
    assert d_for(**kw)["status"]["code"] == base


@pytest.mark.parametrize("lang", ["en", "hi", "ta"])
def test_no_collector_application_anywhere(lang):
    d = d_for(lang, hit_and_run="yes")
    steps_and_checklist = " ".join(d["next_steps"]) + " ".join(i for g in d["checklist"] for i in g["items"])
    assert "written application" not in steps_and_checklist.lower()
    assert all(g["group"] != "collector" for g in d["checklist"])


def test_police_checklist_includes_112_acknowledgement():
    d = d_for()
    police = next(g for g in d["checklist"] if g["group"] == "police")
    assert any("112" in i for i in police["items"])


def test_life_threatening_step_names_hospital_administrator_and_tms():
    now = now_ist()
    f = Facts.from_dict(dict(accident_at=(now - timedelta(hours=3)).isoformat(), motor_vehicle="yes",
                             life_threatening="unsure"))
    d = render_result(evaluate_eligibility(f, now), f, "en", now)
    text = " ".join(d["next_steps"])
    assert "administrator" in text and "TMS" in text


def test_prepared_card_mentions_grievance_helpline_everywhere():
    for lang in ("en", "hi", "ta"):
        assert T.STRINGS[lang]["ui"]["help_other"].count("14555") == 1
    assert JS.count("14555") >= 3
