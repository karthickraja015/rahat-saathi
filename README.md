# RAHAT Saathi

An unofficial helper for people dealing with a road accident in India. It explains the PM-RAHAT cashless treatment scheme in **English, Hindi and Tamil**, works out the scheme's time limits from the facts you give, says who to approach, and lists the documents to keep.

**Information only. Not legal or medical advice. Not affiliated with the Government of India or PM-RAHAT. In an emergency, call 112.**

Built for the Code for a Billion - Bharat Agentic-AI Hackathon 2026 (Transportation Safety).

Live demo: ADD_LIVE_URL_HERE

## The problem

- Road crashes kill about 1.8 lakh people a year in India (2024 figure as reported by a secondary source; replace with the official MoRTH number before submitting).
- PM-RAHAT launched on 13 February 2026. It offers cashless treatment up to Rs 1.5 lakh for up to 7 days, but eligibility depends on time limits and police confirmation that families under stress rarely know.
- Hit-and-run, uninsured vehicles and non-designated hospitals follow different routes (the District Collector).

Sources used (public, secondary; verify against the official scheme guideline):

- https://en.vikaspedia.in/viewcontent/schemesall/central-government-schemes/pm-rahat
- https://westkhasihills.gov.in/scheme/prime-minister-road-accident-victims-hospitalisation-assured-treatment-pm-rahat/
- https://rsdebate.nic.in/bitstream/123456789/757469/1/PQ_267_19032025_U2166_p300_p301.pdf
- https://visionias.in/current-affairs/monthly-magazine/2025-02-22/economy/cashless-treatment-scheme-for-road-accident-victims

## What it does

1. You answer a short guided form (or, if an LLM key is set, describe the accident in your own words and confirm the extracted answers).
2. A deterministic rules engine computes the deadlines and one of four statuses: Likely eligible, At risk, Likely not eligible, Need more information. It never says "definitely eligible".
3. You get live countdowns, up to five next steps, the escalation route, a document checklist, and a shareable text summary.
4. A "Be prepared" page gives a one-screen card for sharing before anything happens.

## How it works

- `rules.yaml`: every rule has an id, text, source URL, last-verified date and a `needs_verification` flag.
- `backend/rules_engine.py`: pure Python eligibility logic. **The LLM never decides eligibility.**
- `backend/llm.py`: optional. Extracts facts from free text only, configured by environment variables, with a daily cap. Output is whitelisted and shown to the user to confirm.
- `backend/translator.py`: all English, Hindi and Tamil text is fixed strings, never LLM-generated.
- `backend/logger.py`: anonymous event counters only. No names, phone numbers, free text, IP addresses or case facts are stored.
- `frontend/`: dependency-free mobile-first page. Works without any LLM.

## Safety and limits

- "Emergency? Call 112 now." is on every screen. No first-aid or medical advice.
- Rules are summarised from public information and **may be incomplete or outdated**. Always confirm with the hospital, police or District Collector.
- Hindi and Tamil text needs review by native speakers (status below).
- It does not connect to any government system. It cannot check real eligibility or find hospitals.

## Verification status (be honest)

| Item | Status |
|---|---|
| Rules vs official PM-RAHAT guideline | TODO. All rules still `needs_verification: true` |
| Hindi text reviewed by a native speaker | TODO |
| Tamil text reviewed by a native speaker | TODO |
| Problem-size figures vs official MoRTH data | TODO |

## Impact and evidence

No real-world usage data yet. Fill this in with real numbers only:

- Automated tests: run `pytest` (180+ tests, including boundary cases such as 23h59m vs 24h01m).
- Awareness quiz (before and after using the app): TODO, with number of respondents and results.
- Anonymous usage counts from `/api/stats`: TODO.

## Run locally

    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    pytest -q
    uvicorn backend.app:app --no-access-log

Open http://127.0.0.1:8000. The app works with no environment variables.

## Optional LLM

Copy `.env.example`, set `LLM_PROVIDER` (`anthropic` or `openai`), `LLM_API_KEY` and `LLM_MODEL` as environment variables on your host. Never commit keys.

## Deploy (free tier)

A `Dockerfile` and `render.yaml` are included. On Render: New, then Blueprint (or Web Service), connect this repo, deploy. Add the optional `LLM_*` variables in the dashboard. Free instances may sleep when idle, so open the link before a demo. Check the host's current free-tier terms.

## Licence

Apache-2.0. See `LICENSE`.
