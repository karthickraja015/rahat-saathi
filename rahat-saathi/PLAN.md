# RAHAT Saathi: Project Plan & File Structure

## Problem Statement
Road accident victims, bystanders, and families in India need to navigate the PM-RAHAT cashless treatment scheme. Many don't know:
- Are they eligible?
- Which hospitals are covered?
- What deadlines apply?
- What documents to collect?
- What to do if the hospital says no?

**Solution**: A mobile-first AI agent + web app that guides users through the scheme in their language (English, Hindi, Tamil) without storing personal data.

---

## High-Level Architecture

### Backend: Python FastAPI
- **Rules Engine** (plain Python): Deterministic, config-driven from `rules.yaml`
- **LLM Agent**: Uses Claude/GPT to extract facts from free text; LLM does NOT decide eligibility
- **Tools**: `extract_facts`, `compute_time_windows`, `evaluate_eligibility`, `route_escalation`, `build_checklist`, `render_summary`
- **Logging**: Anonymous event counts only (no names, phone numbers, free text)

### Frontend: Mobile-first HTML/JS
- Large buttons, voice input, language switcher
- Real-time countdown timers to deadlines
- Shareable summary cards

### Tests: pytest
- 60+ scenario tests covering boundary cases
- Extraction accuracy eval on 30 samples per language

---

## File Structure (Phase 1–4)

```
rahat-saathi/
├── rules.yaml                    # [PHASE 1] Non-negotiable rules + metadata
├── backend/
│   ├── rules_engine.py          # [PHASE 2] Deterministic rule evaluator
│   ├── agent.py                 # [PHASE 3] LLM-backed fact extraction + orchestration
│   ├── app.py                   # [PHASE 3] FastAPI routes
│   ├── logger.py                # [PHASE 3] Anonymous event logging
│   ├── translator.py            # [PHASE 3] i18n for fixed strings
│   ├── models.py                # [PHASE 2] Pydantic schemas
│   └── requirements.txt
├── frontend/
│   ├── index.html               # [PHASE 4] Mobile-first entry
│   ├── collect_facts.html       # [PHASE 4] Fact collection form + voice
│   ├── result.html              # [PHASE 4] Eligibility result + summary
│   ├── be_prepared.html         # [PHASE 4] Emergency card (shareable)
│   ├── style.css                # [PHASE 4] Mobile-first design
│   └── app.js                   # [PHASE 4] Client-side logic
├── tests/
│   ├── test_rules_engine.py     # [PHASE 2] 60+ scenario tests
│   ├── test_agent.py            # [PHASE 3] Fact extraction accuracy
│   ├── scenarios.json           # [PHASE 2] Test case definitions
│   └── conftest.py              # [PHASE 2] pytest fixtures
├── scripts/
│   ├── eval_extraction.py       # [PHASE 3] Eval extraction on 30 samples per language
│   └── verify_rules.py          # [PHASE 1] Check rules against official source (manual step)
├── README.md                     # [PHASE 4] Complete documentation
├── .github/workflows/
│   └── tests.yml                # [PHASE 4] GitHub Actions CI
├── docker-compose.yml           # [PHASE 4] Local dev setup
└── Makefile                      # [PHASE 4] Task shortcuts
```

---

## Phases

### Phase 1: Rules Engine Foundation ✓ [NOW]
- [x] `rules.yaml`: All 7 rules with metadata, marked `needs_verification: true`
- [ ] `backend/models.py`: Pydantic schemas for Facts, Rule, EligibilityResult
- [ ] `backend/rules_engine.py`: Core logic to evaluate facts against rules

### Phase 2: Testing & Scenarios [NEXT]
- [ ] `tests/scenarios.json`: 60+ test cases (normal, boundary, edge cases)
- [ ] `tests/test_rules_engine.py`: pytest suite; all must pass
- [ ] `tests/conftest.py`: Fixtures and helpers

### Phase 3: LLM Agent & API [THEN]
- [ ] `backend/agent.py`: Claude-based fact extractor + orchestrator
- [ ] `backend/app.py`: FastAPI routes (POST `/extract`, `/evaluate`, `/summary`)
- [ ] `backend/translator.py`: i18n strings in EN, HI, TA
- [ ] `backend/logger.py`: Anonymous event logging
- [ ] `scripts/eval_extraction.py`: Accuracy report on 30 samples per language

### Phase 4: Frontend & Deployment [FINALLY]
- [ ] HTML/CSS/JS: Mobile-first UI, voice input
- [ ] Docker + GitHub Actions + Deployment to Render/Railway
- [ ] `README.md`: Full problem statement, how to run, limits, safety

---

## Rules Summary (from rules.yaml)

| Rule ID | Summary | Window |
|---------|---------|--------|
| `cashless_cover_limit` | Rs 1.5 lakh or 7 days, whichever earlier | N/A |
| `first_hospitalisation_window` | Must be ≤24h after accident | 0–24h post-accident |
| `stabilisation_duration` | 24h (non-life) or 48h (life-threatening) | From first hosp. |
| `police_confirmation_window` | Police auth within 24h / 48h | From accident |
| `designated_hospitals` | Only designated hospitals for full cover; non-designated for stabilisation only | N/A |
| `escalation_to_collector` | Escalate if: uninsured, hit-and-run, non-designated stabilisation, no police response | N/A |
| `call_112` | 112 → nearest designated hospital + ambulance | N/A |

---

## Facts to Collect (from user)

1. **Accident date/time** (mandatory)
2. **Motor vehicle involved** (yes/no)
3. **Life-threatening injury** (yes/no/unsure)
4. **First hospitalisation date/time** (mandatory)
5. **Hospital type** (designated / not sure)
6. **Police informed** (yes/no, when)
7. **Hit-and-run** (yes/no)
8. **Vehicle insured** (yes/no/unknown)
9. **State** (to find District Collector)

---

## Eligibility Logic Pseudocode

```
if motor_vehicle == no:
  status = "not_eligible" (not a road accident)
  
elif first_hosp_time - accident_time > 24h:
  status = "not_eligible" (outside cashless window)
  
elif life_threatening == yes:
  stabilisation_window = 48h
  police_window = 48h
elif life_threatening == no or unsure:
  stabilisation_window = 24h
  police_window = 24h

if police_informed == no or police_time - accident_time > police_window:
  status = "escalation_to_collector"
  reason = "police authentication required"
  
elif vehicle_insured == no or hit_and_run == yes:
  status = "escalation_to_collector"
  reason = "claim escalation required"
  
elif hospital_type == "not_sure":
  status = "at_risk"
  reason = "confirm hospital is designated; non-designated can only provide stabilisation"
  
elif hospital_type != "designated":
  status = "escalation_to_collector"
  reason = "non-designated hospital; stabilisation only"
  
else:
  status = "likely_eligible"
  remaining_days = 7 - (now - accident_time).days
  remaining_amount = 150000 - claims_amount
  
deadline_1 = accident_time + police_window
deadline_2 = accident_time + stabilisation_window
deadline_3 = first_hosp_time + 7d (if in-hospital)
deadline_4 = accident_time + 24h (if unsure)
```

---

## Output Per Session (User-Facing)

1. **Status & Reason** (with 4-level confidence)
2. **Deadlines with Live Countdowns**
3. **"Do This Next" Steps** (max 5)
4. **Escalation Route** (if applicable)
5. **Document Checklist** (hospital, police, insurance)
6. **Shareable Summary** (in chosen language)

---

## Safety Guardrails

✓ Top of every screen: "Emergency? Call 112 now."
✓ Footer: "Unofficial helper app. Not affiliated with GOI or PM-RAHAT."
✓ No first-aid or medical advice.
✓ Never "definitely eligible" — use: Likely / At risk / Likely not / Need info.
✓ Every result: "Information only, not legal/medical advice. Confirm with hospital/police/Collector."
✓ Source notes on rules.
✓ No login; no personal data stored; anonymous event logs only.

---

## Quality Checklist

- [ ] 60+ pytest scenarios (boundary cases: 23h59m vs 24h01m, hit-and-run, uninsured, unsure)
- [ ] All tests pass in CI (GitHub Actions)
- [ ] Extraction eval on 30 samples per language
- [ ] Mobile-first UI, large buttons, voice input
- [ ] README with sources, rules engine explanation, limits, safety, how to run
- [ ] Apache-2.0 licence
- [ ] Deploy to free tier (Render/Railway) with live URL

---

## Next Step

Start Phase 1 (✓ rules.yaml) and Phase 2:
1. Build `backend/models.py` (Pydantic schemas)
2. Build `backend/rules_engine.py` (core evaluator)
3. Build `tests/scenarios.json` (60+ test cases)
4. Build `tests/test_rules_engine.py` (pytest suite)
5. Run tests and iterate until all pass

