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
