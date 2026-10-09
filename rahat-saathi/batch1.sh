#!/usr/bin/env bash
set -euo pipefail
DIR="$HOME/Downloads/India AI/rahat-saathi/rahat-saathi"
mkdir -p "$DIR/backend" "$DIR/tests"
cd "$DIR"
[ -d .git ] || git init -q

cat > requirements.txt <<'EOF'
fastapi>=0.110
uvicorn[standard]>=0.27
pyyaml>=6.0
httpx>=0.27
pytest>=8.0
EOF

cat > pytest.ini <<'EOF'
[pytest]
pythonpath = .
testpaths = tests
EOF

cat > .gitignore <<'EOF'
.venv/
__pycache__/
.pytest_cache/
.env
.DS_Store
EOF

touch backend/__init__.py tests/__init__.py

cat > backend/rules.yaml <<'EOF'
# RAHAT Saathi rules. ALL rules need verification against the official guideline.
# Edit only this file to change rule parameters. Unofficial helper; not legal advice.
version: 1
rules:
  - id: R01
    name: cover_limit
    text: "Cashless cover is up to Rs 1.5 lakh or 7 days from the accident, whichever is earlier."
    source_url: "https://www.nha.gov.in/"   # TODO: replace with exact guideline URL
    last_verified_date: null
    needs_verification: true
    params:
      amount_inr: 150000
      days: 7

  - id: R02
    name: first_hospitalisation_window
    text: "If first hospitalisation is more than 24 hours after the accident, the victim is not eligible."
    source_url: "https://www.nha.gov.in/"
    last_verified_date: null
    needs_verification: true
    params:
      hours: 24

  - id: R03
    name: stabilisation_window
    text: "Stabilisation is covered up to 24 hours (non-life-threatening) or 48 hours (life-threatening), subject to police authentication."
    source_url: "https://www.nha.gov.in/"
    last_verified_date: null
    needs_verification: true
    params:
      anchor: hospitalisation   # or: accident
      hours:
        non_life_threatening: 24
        life_threatening: 48

  - id: R04
    name: police_confirmation_window
    text: "Police confirmation is needed within 24 hours (non-life-threatening) or 48 hours (life-threatening)."
    source_url: "https://www.nha.gov.in/"
    last_verified_date: null
    needs_verification: true
    params:
      anchor: hospitalisation   # or: accident
      hours:
        non_life_threatening: 24
        life_threatening: 48

  - id: R05
    name: designated_hospitals
    text: "Designated hospitals are those empanelled under AB PM-JAY, plus others meeting scheme requirements. Non-designated hospitals provide stabilisation only."
    source_url: "https://www.nha.gov.in/"
    last_verified_date: null
    needs_verification: true
    params: {}

  - id: R06
    name: district_collector_route
    text: "For an uninsured vehicle, hit-and-run, stabilisation at a non-designated hospital, or a police-response timeout, the claim goes to the District Collector of the accident location."
    source_url: "https://www.nha.gov.in/"
    last_verified_date: null
    needs_verification: true
    params:
      triggers: [uninsured_vehicle, hit_and_run, non_designated_stabilisation, police_timeout]

  - id: R07
    name: emergency_112
    text: "Dialling 112 gives the nearest designated hospital and an ambulance."
    source_url: "https://112.gov.in/"
    last_verified_date: null
    needs_verification: true
    params:
      number: "112"

  - id: R08
    name: motor_vehicle_required
    text: "The scheme applies to road accidents involving a motor vehicle. (Added by the app author; verify.)"
    source_url: "https://morth.nic.in/"
    last_verified_date: null
    needs_verification: true
    params: {}
EOF

cat > backend/models.py <<'EOF'
"""Data models for RAHAT Saathi. Holds structured facts only: no names, phones or free text."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

IST = timezone(timedelta(hours=5, minutes=30))

STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
    "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal", "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir", "Ladakh",
    "Lakshadweep", "Puducherry",
]
_STATE_LOOKUP = {s.lower(): s for s in STATES}


class Status(str, Enum):
    LIKELY_ELIGIBLE = "likely_eligible"
    AT_RISK = "at_risk"
    LIKELY_NOT_ELIGIBLE = "likely_not_eligible"
    NEED_MORE_INFO = "need_more_information"


# ok/note do not change status; info -> need more info; risk -> at risk; not -> likely not eligible
SEVERITY_RANK = {"ok": 0, "note": 0, "info": 1, "risk": 2, "not": 3}

_TRI = {
    "yes": "yes", "y": "yes", "true": "yes",
    "no": "no", "n": "no", "false": "no",
    "unsure": "unsure", "unknown": "unsure", "not sure": "unsure", "not_sure": "unsure",
    "dont know": "unsure", "don't know": "unsure",
}
_HOSP = {
    "designated": "designated",
    "non_designated": "non_designated", "non-designated": "non_designated",
    "not_designated": "non_designated", "not designated": "non_designated",
    "not_sure": "not_sure", "not sure": "not_sure", "unsure": "not_sure", "unknown": "not_sure",
}


def now_ist() -> datetime:
    return datetime.now(IST).replace(tzinfo=None)


def parse_dt(v: Any) -> Optional[datetime]:
    if v is None or v == "":
        return None
    if isinstance(v, str):
        v = datetime.fromisoformat(v.strip())
    if not isinstance(v, datetime):
        raise ValueError(f"invalid datetime: {v!r}")
    if v.tzinfo is not None:
        v = v.astimezone(IST).replace(tzinfo=None)
    return v


def norm_tri(v: Any) -> Optional[str]:
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        return "yes" if v else "no"
    s = str(v).strip().lower()
    if s in _TRI:
        return _TRI[s]
    raise ValueError(f"invalid yes/no/unsure value: {v!r}")


def norm_hospital(v: Any) -> Optional[str]:
    if v is None or v == "":
        return None
    s = str(v).strip().lower()
    if s in _HOSP:
        return _HOSP[s]
    raise ValueError(f"invalid hospital type: {v!r}")


def norm_state(v: Any) -> Optional[str]:
    if v is None or v == "":
        return None
    s = str(v).strip().lower()
    if s in _STATE_LOOKUP:
        return _STATE_LOOKUP[s]
    raise ValueError(f"invalid state: {v!r}")


@dataclass
class Facts:
    accident_at: Optional[datetime] = None
    motor_vehicle: Optional[str] = None        # yes/no/unsure
    life_threatening: Optional[str] = None     # yes/no/unsure
    hospitalised_at: Optional[datetime] = None
    hospital_type: Optional[str] = None        # designated/non_designated/not_sure
    police_informed: Optional[str] = None      # yes/no/unsure
    police_informed_at: Optional[datetime] = None
    hit_and_run: Optional[str] = None          # yes/no/unsure
    insured: Optional[str] = None              # yes/no/unsure (unknown)
    state: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Optional[dict]) -> "Facts":
        d = d or {}
        return cls(
            accident_at=parse_dt(d.get("accident_at")),
            motor_vehicle=norm_tri(d.get("motor_vehicle")),
            life_threatening=norm_tri(d.get("life_threatening")),
            hospitalised_at=parse_dt(d.get("hospitalised_at")),
            hospital_type=norm_hospital(d.get("hospital_type")),
            police_informed=norm_tri(d.get("police_informed")),
            police_informed_at=parse_dt(d.get("police_informed_at")),
            hit_and_run=norm_tri(d.get("hit_and_run")),
            insured=norm_tri(d.get("insured")),
            state=norm_state(d.get("state")),
        )

    def to_dict(self) -> dict:
        out = {}
        for k, v in self.__dict__.items():
            out[k] = v.isoformat() if isinstance(v, datetime) else v
        return out


@dataclass
class Reason:
    code: str
    rule_id: str
    severity: str
    params: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"code": self.code, "rule_id": self.rule_id, "severity": self.severity, "params": self.params}


@dataclass
class TimeWindows:
    deadlines: dict          # name -> datetime
    anchors: dict            # "stabilisation"/"police" -> "hospitalisation"|"accident"
    lt_mode: str             # life_threatening | non_life_threatening | non_life_threatening_assumed

    @property
    def cover_end(self) -> datetime:
        return self.deadlines["cover_end"]

    @property
    def hospitalisation_deadline(self) -> datetime:
        return self.deadlines["hospitalisation_deadline"]

    @property
    def stabilisation_end(self) -> datetime:
        return self.deadlines["stabilisation_end"]

    @property
    def police_deadline(self) -> datetime:
        return self.deadlines["police_deadline"]

    def to_dict(self, now: Optional[datetime] = None) -> dict:
        now = now or now_ist()
        return {
            "anchors": self.anchors,
            "life_threatening_mode": self.lt_mode,
            "deadlines": {
                k: {"at": v.isoformat(), "seconds_left": int((v - now).total_seconds())}
                for k, v in self.deadlines.items()
            },
        }


@dataclass
class Escalation:
    route: str               # hospital_and_police | district_collector
    triggers: list
    rule_id: str = "R06"

    def to_dict(self) -> dict:
        return {"route": self.route, "triggers": self.triggers, "rule_id": self.rule_id}


@dataclass
class EligibilityResult:
    status: Status
    reasons: list
    windows: Optional[TimeWindows]
    escalation: Escalation
    next_steps: list
    next_question: Optional[str]
    cover_limit_inr: int

    def to_dict(self, now: Optional[datetime] = None) -> dict:
        return {
            "status": self.status.value,
            "reasons": [r.to_dict() for r in self.reasons],
            "windows": self.windows.to_dict(now) if self.windows else None,
            "escalation": self.escalation.to_dict(),
            "next_steps": self.next_steps,
            "next_question": self.next_question,
            "cover_limit_inr": self.cover_limit_inr,
        }
EOF

cat > backend/rules_engine.py <<'EOF'
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
EOF

cat > tests/scenarios.py <<'EOF'
"""Scenario table. All times are offsets from the accident time ACC."""
from datetime import datetime, timedelta

ACC = datetime(2026, 10, 1, 10, 0)


def H(hours=0, minutes=0):
    return ACC + timedelta(hours=hours, minutes=minutes)


NOW = H(3)
LE, AR, LN, NI = "likely_eligible", "at_risk", "likely_not_eligible", "need_more_information"
COL = "district_collector"

BASE = dict(
    accident_at=ACC, motor_vehicle="yes", life_threatening="no", hospitalised_at=H(1),
    hospital_type="designated", police_informed="yes", police_informed_at=H(2),
    hit_and_run="no", insured="yes", state="Tamil Nadu",
)


def sc(sid, status, route="hospital_and_police", now=NOW, codes=(), absent=(), **facts):
    return {"id": sid, "status": status, "route": route, "now": now,
            "codes": tuple(codes), "absent": tuple(absent), "facts": facts}


SCENARIOS = [
    sc("baseline_all_good", LE, codes=["hospitalised_within_24h", "hospital_designated", "police_in_time"]),
    sc("hosp_23h59", LE, now=H(26), hospitalised_at=H(23, 59), codes=["hospitalised_within_24h"]),
    sc("hosp_exactly_24h00", LE, now=H(26), hospitalised_at=H(24), codes=["hospitalised_within_24h"]),
    sc("hosp_24h01", LN, now=H(26), hospitalised_at=H(24, 1), codes=["hospitalised_after_24h"]),
    sc("hosp_3_days_late", LN, now=H(80), hospitalised_at=H(72), codes=["hospitalised_after_24h"]),
    sc("hosp_24h01_life_threatening", LN, now=H(26), hospitalised_at=H(24, 1), life_threatening="yes"),
    sc("lt_police_47h59", LE, now=H(50), life_threatening="yes", police_informed_at=H(48, 59),
       codes=["police_in_time"], absent=["police_late"]),
    sc("lt_police_48h01", AR, COL, now=H(50), life_threatening="yes", police_informed_at=H(49, 1),
       codes=["police_late"]),
    sc("nlt_police_23h59", LE, now=H(26), police_informed_at=H(24, 59), codes=["police_in_time"]),
    sc("nlt_police_24h01", AR, COL, now=H(26), police_informed_at=H(25, 1), codes=["police_late"]),
    sc("lt_unsure_police_late_uses_24h", AR, COL, now=H(26), life_threatening="unsure",
       police_informed_at=H(25, 1), codes=["life_threatening_unsure", "police_late"]),
    sc("lt_unsure_otherwise_ok", NI, life_threatening="unsure", codes=["life_threatening_unsure"]),
    sc("lt_missing", NI, life_threatening=None, codes=["life_threatening_missing"]),
    sc("lt_yes_ok", LE, life_threatening="yes"),
    sc("no_motor_vehicle", LN, motor_vehicle="no", codes=["no_motor_vehicle"]),
    sc("motor_vehicle_unsure", NI, motor_vehicle="unsure", codes=["motor_vehicle_unsure"]),
    sc("motor_vehicle_missing", NI, motor_vehicle=None, codes=["motor_vehicle_missing"]),
    sc("accident_time_missing", NI, accident_at=None, hospitalised_at=None, police_informed_at=None,
       codes=["accident_time_missing"]),
    sc("hospitalisation_time_missing", NI, hospitalised_at=None, codes=["hospitalisation_time_missing"]),
    sc("hospitalised_before_accident", NI, hospitalised_at=H(-2),
       codes=["hospitalisation_before_accident"], absent=["hospitalised_after_24h"]),
    sc("hit_and_run", LE, COL, hit_and_run="yes", codes=["hit_and_run_collector"]),
    sc("hit_and_run_unsure", LE, hit_and_run="unsure", codes=["hit_and_run_unknown"]),
    sc("uninsured", LE, COL, insured="no", codes=["uninsured_collector"]),
    sc("insured_unsure", LE, insured="unsure", codes=["insured_unknown"]),
    sc("insured_missing", LE, insured=None, absent=["insured_unknown", "uninsured_collector"]),
    sc("non_designated_early", AR, COL, hospital_type="non_designated",
       codes=["non_designated_stabilisation_only"], absent=["stabilisation_window_ended"]),
    sc("non_designated_after_stabilisation", AR, COL, now=H(30), hospital_type="non_designated",
       codes=["stabilisation_window_ended"]),
    sc("hospital_not_sure", NI, hospital_type="not_sure", codes=["hospital_type_unsure"]),
    sc("hospital_missing", NI, hospital_type=None, codes=["hospital_type_missing"]),
    sc("police_no_pending", AR, police_informed="no", police_informed_at=None, codes=["police_pending"]),
    sc("police_no_timeout", AR, COL, now=H(26), police_informed="no", police_informed_at=None,
       codes=["police_timeout"]),
    sc("police_unsure", NI, police_informed="unsure", police_informed_at=None, codes=["police_unsure"]),
    sc("police_missing", NI, police_informed=None, police_informed_at=None, codes=["police_missing"]),
    sc("police_yes_time_missing", NI, police_informed_at=None, codes=["police_time_missing"]),
    sc("cover_ended_8_days", AR, now=H(24 * 8), codes=["cover_window_ended"]),
    sc("cover_boundary_exact_7d", LE, now=H(168), absent=["cover_window_ended"]),
    sc("cover_boundary_7d_plus_1min", AR, now=H(168, 1), codes=["cover_window_ended"]),
    sc("accident_in_future", NI, accident_at=H(4), hospitalised_at=H(5), codes=["accident_in_future"]),
    sc("hospitalisation_in_future", NI, hospitalised_at=H(5), codes=["hospitalisation_in_future"]),
    sc("stacked_collector_triggers", AR, COL, hospital_type="non_designated", hit_and_run="yes",
       insured="no", codes=["non_designated_stabilisation_only", "hit_and_run_collector", "uninsured_collector"]),
    sc("not_eligible_beats_at_risk", LN, now=H(31), hospitalised_at=H(30), police_informed="no",
       police_informed_at=None, codes=["hospitalised_after_24h", "police_pending"]),
    sc("not_eligible_beats_missing_info", LN, now=H(31), hospitalised_at=H(30), life_threatening=None),
    sc("not_eligible_still_routes_collector", LN, COL, now=H(31), hospitalised_at=H(30), insured="no"),
    sc("state_missing_is_fine", LE, state=None),
    sc("lt_police_pending_47h59", AR, now=H(48, 59), life_threatening="yes", police_informed="no",
       police_informed_at=None, codes=["police_pending"], absent=["police_timeout"]),
    sc("lt_police_timeout_48h01", AR, COL, now=H(49, 1), life_threatening="yes", police_informed="no",
       police_informed_at=None, codes=["police_timeout"]),
    sc("nlt_police_pending_23h59", AR, now=H(24, 59), police_informed="no", police_informed_at=None,
       codes=["police_pending"], absent=["police_timeout"]),
    sc("nlt_police_timeout_24h01", AR, COL, now=H(25, 1), police_informed="no", police_informed_at=None,
       codes=["police_timeout"]),
    sc("lt_nondesignated_stab_47h59", AR, COL, now=H(48, 59), life_threatening="yes",
       hospital_type="non_designated", absent=["stabilisation_window_ended"]),
    sc("lt_nondesignated_stab_48h01", AR, COL, now=H(49, 1), life_threatening="yes",
       hospital_type="non_designated", codes=["stabilisation_window_ended"]),
    sc("nlt_nondesignated_stab_23h59", AR, COL, now=H(24, 59), hospital_type="non_designated",
       absent=["stabilisation_window_ended"]),
    sc("nlt_nondesignated_stab_24h01", AR, COL, now=H(25, 1), hospital_type="non_designated",
       codes=["stabilisation_window_ended"]),
    sc("lt_unsure_nondesignated_uses_24h", AR, COL, now=H(25, 1), life_threatening="unsure",
       hospital_type="non_designated", codes=["stabilisation_window_ended", "life_threatening_unsure"]),
]
EOF

cat > tests/test_scenarios.py <<'EOF'
import pytest

from backend.models import Facts, SEVERITY_RANK
from backend.rules_engine import evaluate_eligibility, load_rules
from tests.scenarios import BASE, SCENARIOS


@pytest.mark.parametrize("sc", SCENARIOS, ids=[s["id"] for s in SCENARIOS])
def test_scenario(sc):
    facts = Facts.from_dict({**BASE, **sc["facts"]})
    res = evaluate_eligibility(facts, now=sc["now"])
    codes = {r.code for r in res.reasons}
    assert res.status == sc["status"]
    assert res.escalation.route == sc["route"]
    assert set(sc["codes"]) <= codes
    assert not (set(sc["absent"]) & codes)
    rules = load_rules()
    assert all(r.rule_id in rules and r.severity in SEVERITY_RANK for r in res.reasons)
    assert 1 <= len(res.next_steps) <= 5
EOF

cat > tests/test_models.py <<'EOF'
from datetime import datetime

import pytest

from backend.models import STATES, Facts, norm_hospital, norm_tri, parse_dt


def test_parse_iso_naive():
    assert Facts.from_dict({"accident_at": "2026-10-01T10:00"}).accident_at == datetime(2026, 10, 1, 10, 0)


def test_parse_timezone_converted_to_ist():
    assert parse_dt("2026-10-01T04:30:00+00:00") == datetime(2026, 10, 1, 10, 0)


def test_parse_invalid_datetime_raises():
    with pytest.raises(ValueError):
        parse_dt("not a date")


@pytest.mark.parametrize("raw,expected", [
    ("yes", "yes"), ("Y", "yes"), (True, "yes"), (False, "no"), ("no", "no"),
    ("unknown", "unsure"), ("Not sure", "unsure"), ("", None), (None, None),
])
def test_norm_tri(raw, expected):
    assert norm_tri(raw) == expected


def test_norm_tri_invalid():
    with pytest.raises(ValueError):
        norm_tri("maybe")


@pytest.mark.parametrize("raw,expected", [
    ("designated", "designated"), ("non-designated", "non_designated"),
    ("not_sure", "not_sure"), ("unknown", "not_sure"), (None, None),
])
def test_norm_hospital(raw, expected):
    assert norm_hospital(raw) == expected


def test_norm_hospital_invalid():
    with pytest.raises(ValueError):
        norm_hospital("private clinic")


def test_state_case_insensitive():
    assert Facts.from_dict({"state": "tamil nadu"}).state == "Tamil Nadu"


def test_state_free_text_rejected():
    with pytest.raises(ValueError):
        Facts.from_dict({"state": "Mars"})


def test_unknown_keys_are_dropped_no_free_text_stored():
    f = Facts.from_dict({"name": "Asha", "phone": "999", "notes": "free text", "motor_vehicle": "yes"})
    d = f.to_dict()
    assert "name" not in d and "phone" not in d and "notes" not in d
    assert set(d) == {"accident_at", "motor_vehicle", "life_threatening", "hospitalised_at", "hospital_type",
                      "police_informed", "police_informed_at", "hit_and_run", "insured", "state"}


def test_roundtrip():
    f = Facts.from_dict({"accident_at": "2026-10-01T10:00", "insured": "no", "state": "Kerala"})
    assert Facts.from_dict(f.to_dict()) == f


def test_states_count():
    assert len(STATES) == 36
EOF

cat > tests/test_rules_yaml.py <<'EOF'
import pytest
import yaml

from backend.rules_engine import RULES_PATH, load_rules

IDS = ["R01", "R02", "R03", "R04", "R05", "R06", "R07", "R08"]


def test_all_rules_present():
    assert sorted(load_rules()) == IDS


def test_ids_unique():
    raw = yaml.safe_load(open(RULES_PATH, encoding="utf-8"))["rules"]
    assert len(raw) == len({r["id"] for r in raw})


@pytest.mark.parametrize("rid", IDS)
def test_rule_needs_verification(rid):
    assert load_rules()[rid]["needs_verification"] is True


@pytest.mark.parametrize("rid", IDS)
def test_rule_has_text_and_source(rid):
    r = load_rules()[rid]
    assert r["text"].strip()
    assert r["source_url"].startswith("https://")
    assert "last_verified_date" in r


def test_numeric_params():
    r = load_rules()
    assert r["R01"]["params"] == {"amount_inr": 150000, "days": 7}
    assert r["R02"]["params"]["hours"] == 24
    for rid in ("R03", "R04"):
        assert r[rid]["params"]["hours"] == {"non_life_threatening": 24, "life_threatening": 48}


def test_loader_rejects_rule_missing_keys(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("rules:\n  - id: X1\n    text: hi\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_rules(p)
EOF

cat > tests/test_engine_units.py <<'EOF'
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
EOF

echo "Batch 1 files written to: $DIR"