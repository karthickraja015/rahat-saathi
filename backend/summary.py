"""Turns an EligibilityResult into localized, display-ready output and a shareable text summary."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from backend import translator as T
from backend.checklist import build_checklist
from backend.models import Facts, now_ist
from backend.rules_engine import evaluate_eligibility


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
        L += ["", f'{ui["deadlines"]}:'] + [f"- {x['label']}: {x['at_text']}" for x in d["deadlines"]]
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
    reasons = [
        {"code": r.code, "rule_id": r.rule_id, "severity": r.severity,
         "text": T.t(lang, "reason", r.code, **_params(r.params))}
        for r in result.reasons
    ]
    deadlines = []
    if result.windows is not None:
        for name, dt in sorted(result.windows.deadlines.items(), key=lambda kv: kv[1]):
            label = T.STRINGS[lang]["deadline"].get(name) or name.replace("_", " ")
            deadlines.append({"key": name, "label": label, "at_iso": dt.isoformat(),
                              "at_text": T.fmt_dt(dt), "seconds_left": int((dt - now).total_seconds())})
    checklist = [
        {"group": g["group"], "title": T.t(lang, "group", g["group"]),
         "items": [T.t(lang, "item", i) for i in g["items"]]}
        for g in build_checklist(facts, result)
    ]
    nq = result.next_question
    d = {
        "lang": lang,
        "ui": dict(ui),
        "status": {"code": result.status.value, "label": T.t(lang, "status", result.status.value)},
        "reasons": reasons,
        "deadlines": deadlines,
        "next_steps": [T.t(lang, "step", s) for s in result.next_steps],
        "escalation": {"route": result.escalation.route, "text": T.t(lang, "route", result.escalation.route)},
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
