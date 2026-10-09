"""RAHAT Saathi API. Works fully without an LLM."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from backend import llm, logger
from backend import translator as T
from backend.models import now_ist
from backend.summary import evaluate_and_render

app = FastAPI(title="RAHAT Saathi", version="0.1.0",
              description="Unofficial helper for PM-RAHAT. Information only.")


@app.middleware("http")
async def security_headers(request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    if request.url.path.startswith("/api"):
        resp.headers["Cache-Control"] = "no-store"
    return resp


class FactsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    accident_at: Optional[str] = Field(None, max_length=60)
    motor_vehicle: Optional[str] = Field(None, max_length=20)
    life_threatening: Optional[str] = Field(None, max_length=20)
    hospitalised_at: Optional[str] = Field(None, max_length=60)
    hospital_type: Optional[str] = Field(None, max_length=20)
    police_informed: Optional[str] = Field(None, max_length=20)
    police_informed_at: Optional[str] = Field(None, max_length=60)
    hit_and_run: Optional[str] = Field(None, max_length=20)
    insured: Optional[str] = Field(None, max_length=20)
    state: Optional[str] = Field(None, max_length=60)


class EvaluateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    facts: FactsIn = Field(default_factory=FactsIn)
    lang: str = Field("en", max_length=5)


class ExtractIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(..., min_length=3, max_length=1000)
    lang: str = Field("en", max_length=5)


class EventIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event: str = Field(..., max_length=40)
    lang: Optional[str] = Field(None, max_length=5)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/config")
def config():
    return {"llm_available": llm.configured(), "languages": T.LANGS}


@app.get("/api/strings/{lang}")
def strings(lang: str):
    lang = T.norm_lang(lang)
    s = T.STRINGS[lang]
    return {"lang": lang, "ui": s["ui"], "question": s["question"], "status": s["status"]}


@app.post("/api/evaluate")
def evaluate(body: EvaluateIn):
    lang = T.norm_lang(body.lang)
    facts = {k: v for k, v in body.facts.model_dump().items() if v not in (None, "")}
    out = evaluate_and_render(facts, lang)
    logger.log_event("evaluated", lang, out["status"]["code"])
    if out["escalation"]["route"] == "district_collector":
        logger.log_event("escalation_shown", lang)
    return out


@app.post("/api/extract")
def extract(body: ExtractIn):
    """Returns extracted facts for the user to CONFIRM. Never returns an eligibility decision."""
    lang = T.norm_lang(body.lang)
    if not llm.configured():
        logger.log_event("extract_unavailable", lang)
        return {"available": False, "facts": None, "reason": "no_llm"}
    if not llm.take_slot():
        logger.log_event("extract_unavailable", lang)
        return {"available": False, "facts": None, "reason": "daily_limit"}
    facts = llm.extract_facts(body.text, now_ist())
    if facts is None:
        logger.log_event("extract_unavailable", lang)
        return {"available": True, "facts": None, "reason": "failed"}
    logger.log_event("extract_used", lang)
    return {"available": True, "facts": facts, "reason": None}


@app.post("/api/event")
def event(body: EventIn):
    if body.event not in logger.CLIENT_EVENTS:
        raise HTTPException(status_code=400, detail="unknown event")
    logger.log_event(body.event, body.lang)
    return {"ok": True}


@app.get("/api/stats")
def stats():
    return logger.stats()


FRONT = Path(__file__).resolve().parent.parent / "frontend"
if FRONT.is_dir():
    app.mount("/static", StaticFiles(directory=str(FRONT)), name="static")


@app.get("/", include_in_schema=False)
def index():
    idx = FRONT / "index.html"
    if idx.exists():
        return FileResponse(idx)
    return JSONResponse({"app": "RAHAT Saathi", "status": "API running; frontend not installed yet"})
