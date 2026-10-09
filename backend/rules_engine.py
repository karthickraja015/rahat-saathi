"""Deterministic rules engine. Pure Python, driven by rules.yaml, no external services."""
from __future__ import annotations

from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml

from .models import (
    SEVERITY_RANK, EligibilityResult, Escalation, Facts, Reason, Status, TimeWindows, now_ist,
)

RULES_PATH = Path(__file__).with_name("rules.yaml")
REQUIRED_RULE_KEYS = ("id", "text", "source_url", "last_verified_date", "needs_verification")


@lru_cache(maxsize=4)
def _load(path_str: str) -> dict:
    with open(path_str, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    rules = {}
    for r in data["rules"]:
        missing = [k for k in REQUIRED_RULE_KEYS if k not in r]
        if missing:
            raise ValueError(f"rule {r.get('id', '?')} missing keys: {missing}")
        rules[r["id"]] = r
    return rules


def load_rules(path=None) -> dict:
    return _load(str(path or RULES_PATH))


# ---------------------------------------------------------------- time windows
def compute_time_windows(facts: Facts, rules: Optional[dict] = None) -> Optional[TimeWindows]:
    rules = rules or load_rules()
    acc = facts.accident_at
    if acc is None:
        return None
    lt = facts.life_threatening
    key = "life_threatening" if lt == "yes" else "non_life_threatening"
    mode = {"yes": "life_threatening", "no": "non_life_threatening"}.get(lt, "non_life_threatening_assumed")

    def anchor(rule_id: str):
        want = rules[rule_id]["params"].get("anchor", "accident")
        if want == "hospitalisation" and facts.hospitalised_at is not None:
            return facts.hospitalised_at, "hospitalisation"
        return acc, "accident"

    stab_anchor, stab_name = anchor("R03")
    pol_anchor, pol_name = anchor("R04")
    deadlines = {
        "cover_end": acc + timedelta(days=rules["R01"]["params"]["days"]),
        "hospitalisation_deadline": acc + timedelta(hours=rules["R02"]["params"]["hours"]),
        "stabilisation_end": stab_anchor + timedelta(hours=rules["R03"]["params"]["hours"][key]),
        "police_deadline": pol_anchor + timedelta(hours=rules["R04"]["params"]["hours"][key]),
    }
    return TimeWindows(deadlines, {"stabilisation": stab_name, "police": pol_name}, mode)


# ------------------------------------------------------------------ escalation
def _escalation(facts: Facts, windows: Optional[TimeWindows], now: datetime) -> Escalation:
    triggers = []
    if facts.insured == "no":
        triggers.append("uninsured_vehicle")
    if facts.hit_and_run == "yes":
        triggers.append("hit_and_run")
    if facts.hospital_type == "non_designated":
        triggers.append("non_designated_stabilisation")
    if windows is not None:
        timed_out = False
        if facts.police_informed == "no":
            timed_out = now > windows.police_deadline
        elif facts.police_informed == "yes" and facts.police_informed_at is not None:
            timed_out = facts.police_informed_at > windows.police_deadline
        if timed_out:
            triggers.append("police_timeout")
    route = "district_collector" if triggers else "hospital_and_police"
    return Escalation(route=route, triggers=triggers)


def route_escalation(facts: Facts, now: Optional[datetime] = None, rules: Optional[dict] = None) -> Escalation:
    rules = rules or load_rules()
    return _escalation(facts, compute_time_windows(facts, rules), now or now_ist())


# ------------------------------------------------------------- questions/steps
_QUESTION_ORDER = ["accident_at", "motor_vehicle", "life_threatening", "hospitalised_at",
                   "hospital_type", "police_informed", "police_informed_at",
                   "hit_and_run", "insured", "state"]


def next_question(facts: Facts) -> Optional[str]:
    """Return the key of the single next fact to ask for, or None when complete."""
    for key in _QUESTION_ORDER:
        if key == "police_informed_at" and facts.police_informed != "yes":
            continue
        if getattr(facts, key) is None:
            return key
    return None


_STEP_MAP = [
    ("hospitalised_after_24h", "ask_hospital_about_other_options"),
    ("no_motor_vehicle", "ask_hospital_about_other_options"),
    ("motor_vehicle_unsure", "confirm_vehicle_involved"),
    ("motor_vehicle_missing", "confirm_vehicle_involved"),
    ("non_designated_stabilisation_only", "move_to_designated_hospital"),
    ("hospital_type_unsure", "confirm_designated_hospital"),
    ("hospital_type_missing", "confirm_designated_hospital"),
    ("police_pending", "get_police_confirmation"),
    ("police_missing", "get_police_confirmation"),
    ("police_unsure", "get_police_confirmation"),
    ("police_time_missing", "get_police_confirmation"),
    ("police_late", "get_police_confirmation"),
    ("police_timeout", "get_police_confirmation"),
    ("life_threatening_unsure", "ask_hospital_to_record_severity"),
    ("life_threatening_missing", "ask_hospital_to_record_severity"),
    ("cover_window_ended", "ask_hospital_about_cover_end"),
]


def build_next_steps(reasons: list, escalation: Escalation) -> list:
    codes = {r.code for r in reasons}
    steps: list = []

    def add(c: str):
        if c not in steps:
            steps.append(c)

    if not any(r.severity == "not" for r in reasons):
        add("ask_hospital_cashless")
    for code, step in _STEP_MAP:
        if code in codes:
            add(step)
    if escalation.route == "district_collector":
        add("approach_district_collector")
    return steps[:4] + ["keep_documents"]   # at most 5 steps


# ------------------------------------------------------------------ evaluation
def evaluate_eligibility(facts: Facts, now: Optional[datetime] = None,
                         rules: Optional[dict] = None) -> EligibilityResult:
    rules = rules or load_rules()
    now = now or now_ist()
    windows = compute_time_windows(facts, rules)
    reasons: list = []

    def add(code, rule_id, severity, **params):
        reasons.append(Reason(code, rule_id, severity, params))

    # R08 motor vehicle
    if facts.motor_vehicle == "no":
        add("no_motor_vehicle", "R08", "not")
    elif facts.motor_vehicle == "unsure":
        add("motor_vehicle_unsure", "R08", "info")
    elif facts.motor_vehicle is None:
        add("motor_vehicle_missing", "R08", "info")

    # severity of injury (needed to pick windows)
    if facts.life_threatening is None:
        add("life_threatening_missing", "R03", "info")
    elif facts.life_threatening == "unsure":
        add("life_threatening_unsure", "R03", "info")

    # R01 / R02 times
    if windows is None:
        add("accident_time_missing", "R01", "info")
    else:
        acc = facts.accident_at
        if acc > now:
            add("accident_in_future", "R01", "info")
        h = facts.hospitalised_at
        limit = timedelta(hours=rules["R02"]["params"]["hours"])
        if h is None:
            add("hospitalisation_time_missing", "R02", "info")
        elif h < acc:
            add("hospitalisation_before_accident", "R02", "info")
        else:
            delay = h - acc
            minutes = int(delay.total_seconds() // 60)
            if delay > limit:
                add("hospitalised_after_24h", "R02", "not", delay_minutes=minutes)
            else:
                add("hospitalised_within_24h", "R02", "ok", delay_minutes=minutes)
            if h > now:
                add("hospitalisation_in_future", "R02", "info")
        if now > windows.cover_end:
            add("cover_window_ended", "R01", "risk", cover_end=windows.cover_end.isoformat())

    # R05 hospital type (+ R03 stabilisation end)
    ht = facts.hospital_type
    if ht == "designated":
        add("hospital_designated", "R05", "ok")
    elif ht == "non_designated":
        add("non_designated_stabilisation_only", "R05", "risk")
        if windows is not None and now > windows.stabilisation_end:
            add("stabilisation_window_ended", "R03", "risk",
                stabilisation_end=windows.stabilisation_end.isoformat())
    elif ht == "not_sure":
        add("hospital_type_unsure", "R05", "info")
    else:
        add("hospital_type_missing", "R05", "info")

    # R04 police
    pi = facts.police_informed
    if pi is None:
        add("police_missing", "R04", "info")
    elif pi == "unsure":
        add("police_unsure", "R04", "info")
    elif pi == "no":
        if windows is not None and now > windows.police_deadline:
            add("police_timeout", "R04", "risk", deadline=windows.police_deadline.isoformat())
        else:
            params = {"deadline": windows.police_deadline.isoformat()} if windows else {}
            add("police_pending", "R04", "risk", **params)
    else:
        t = facts.police_informed_at
        if t is None or windows is None:
            add("police_time_missing", "R04", "info")
        elif t > windows.police_deadline:
            add("police_late", "R04", "risk", deadline=windows.police_deadline.isoformat())
        else:
            add("police_in_time", "R04", "ok")

    # R06 notes (affect route only, not status)
    if facts.hit_and_run == "yes":
        add("hit_and_run_collector", "R06", "note")
    elif facts.hit_and_run == "unsure":
        add("hit_and_run_unknown", "R06", "note")
    if facts.insured == "no":
        add("uninsured_collector", "R06", "note")
    elif facts.insured == "unsure":
        add("insured_unknown", "R06", "note")

    worst = max((SEVERITY_RANK[r.severity] for r in reasons), default=0)
    status = {0: Status.LIKELY_ELIGIBLE, 1: Status.NEED_MORE_INFO,
              2: Status.AT_RISK, 3: Status.LIKELY_NOT_ELIGIBLE}[worst]
    escalation = _escalation(facts, windows, now)
    return EligibilityResult(
        status=status,
        reasons=reasons,
        windows=windows,
        escalation=escalation,
        next_steps=build_next_steps(reasons, escalation),
        next_question=next_question(facts),
        cover_limit_inr=rules["R01"]["params"]["amount_inr"],
    )
