"""Turns an EligibilityResult into localized, display-ready output and a shareable text summary."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from backend import translator as T
from backend.checklist import build_checklist
from backend.models import Facts, now_ist
from backend.rules_engine import evaluate_eligibility

# Reasons that only make sense when a motor vehicle was involved.
_COLLECTOR_REASONS = {"hit_and_run_collector", "hit_and_run_unknown", "uninsured_collector",
                      "insured_unsure", "insurance_unknown", "insured_unknown"}
_ANCHOR_KEY = {"police_deadline": "police", "stabilisation_end": "stabilisation"}


def _params(params: Optional[dict]) -> dict:
    out: dict = {}
    for k, v in (params or {}).items():
        if k == "delay_minutes":
            out["delay_h"] = f"{v / 60:.1f}"
        elif k in ("deadline", "cover_end", "stabilisation_end"):
            try:
                s = T.fmt_dt(datetime.fromisoformat(v))
            except Exception:
                s = str(v)
            out["stab_end" if k == "stabilisation_end" else k] = s
        else:
            out[k] = v
    return out


def _text(d: dict, ui: dict, now) -> str:
    L = [ui["summary_title"], ui["emergency"], "", f'{ui["status"]}: {d["status"]["label"]}', "", f'{ui["why"]}:']
    L += [f"- {x['text']}" for x in d["reasons"]]
    if d["deadlines"]:
        L += ["", f'{ui["deadlines"]}:']
        for x in d["deadlines"]:
            L.append(f"- {x['label']}: {x['at_text']}")
            if x.get("basis"):
                L.append(f"    {x['basis']}")
            if x.get("safe_text"):
                L.append(f"    {x['safe_text']}")
    L += ["", f'{ui["next_steps"]}:'] + [f"{i}. {s}" for i, s in enumerate(d["next_steps"], 1)]
    L += ["", f'{ui["escalation"]}: {d["escalation"]["text"]}', "", f'{ui["documents"]}:', f'({ui["checklist_note"]})']
    for g in d["checklist"]:
        L.append(g["title"] + ":")
        L += [f"  - {i}" for i in g["items"]]
    L += ["", ui["disclaimer"], ui["source_note"], ui["footer"], f'{ui["generated"]}: {T.fmt_dt(now)}']
    return "\n".join(L)


def render_result(result, facts, lang: str = "en", now=None) -> dict:
    lang = T.norm_lang(lang)
    now = now or now_ist()
    ui = T.STRINGS[lang]["ui"]
    no_vehicle = facts.motor_vehicle == "no"

    reasons = [
        {"code": r.code, "rule_id": r.rule_id, "severity": r.severity,
         "text": T.t(lang, "reason", r.code, **_params(r.params))}
        for r in result.reasons
        if not (no_vehicle and r.code in _COLLECTOR_REASONS)
    ]
    steps = [s for s in result.next_steps if not (no_vehicle and s == "approach_district_collector")]
    route = "hospital_and_police" if no_vehicle else result.escalation.route

    deadlines = []
    if result.windows is not None:
        anchors = getattr(result.windows, "anchors", {}) or {}
        h = facts.hospitalised_at
        for name, dt in sorted(result.windows.deadlines.items(), key=lambda kv: kv[1]):
            if name == "hospitalisation_deadline" and h is not None and h <= dt:
                continue  # already admitted in time; deadline is just noise
            label = T.STRINGS[lang]["deadline"].get(name) or name.replace("_", " ")
            item = {"key": name, "label": label, "at_iso": dt.isoformat(),
                    "at_text": T.fmt_dt(dt), "seconds_left": int((dt - now).total_seconds())}
            anchor = anchors.get(_ANCHOR_KEY.get(name, ""))
            if anchor == "hospitalisation":
                item["basis"] = ui["from_hosp"]
            elif anchor == "accident":
                item["basis"] = ui["from_acc"]
            if name == "police_deadline" and anchor == "hospitalisation" and facts.accident_at and h is not None:
                safe = facts.accident_at + (dt - h)
                if safe < dt:
                    item["safe_text"] = T.t(lang, "ui", "safe_by", when=T.fmt_dt(safe))
            deadlines.append(item)

    groups = build_checklist(facts, result)
    if no_vehicle:
        groups = [g for g in groups if g["group"] != "collector"]
    checklist = [
        {"group": g["group"], "title": T.t(lang, "group", g["group"]),
         "items": [T.t(lang, "item", i) for i in g["items"]]}
        for g in groups
    ]
    nq = result.next_question
    d = {
        "lang": lang,
        "ui": dict(ui),
        "status": {"code": result.status.value, "label": T.t(lang, "status", result.status.value)},
        "reasons": reasons,
        "deadlines": deadlines,
        "next_steps": [T.t(lang, "step", s) for s in steps],
        "escalation": {"route": route, "text": T.t(lang, "route", route)},
        "checklist": checklist,
        "next_question": {"key": nq, "text": T.t(lang, "question", nq)} if nq else None,
    }
    d["summary_text"] = _text(d, ui, now)
    return d


def render_summary(result, facts, lang: str = "en", now=None) -> str:
    return render_result(result, facts, lang, now)["summary_text"]


def evaluate_and_render(facts_dict: Optional[dict], lang: str = "en", now=None) -> dict:
    now = now or now_ist()
    facts = Facts.from_dict(facts_dict)
    return render_result(evaluate_eligibility(facts, now), facts, lang, now)
