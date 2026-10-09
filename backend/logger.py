"""Anonymous event counters. Never stores names, phones, free text, IPs or facts."""
from __future__ import annotations

import json
import os
import re
import threading
from collections import Counter
from datetime import datetime, timezone

ALLOWED_EVENTS = {
    "session_started", "language_changed", "evaluated", "extract_used", "extract_unavailable",
    "summary_copied", "summary_shared", "prepared_viewed", "escalation_shown",
}
CLIENT_EVENTS = {"session_started", "language_changed", "summary_copied", "summary_shared", "prepared_viewed"}
_LANGS = {"en", "hi", "ta"}
_SAFE = re.compile(r"^[a-z_]{1,40}$")
_lock = threading.Lock()
_counts: Counter = Counter()
_since = datetime.now(timezone.utc).isoformat(timespec="seconds")


def log_event(event: str, lang=None, outcome=None) -> bool:
    if event not in ALLOWED_EVENTS:
        return False
    lang = lang if lang in _LANGS else None
    outcome = outcome if isinstance(outcome, str) and _SAFE.match(outcome) else None
    with _lock:
        _counts[event] += 1
        if lang:
            _counts[f"{event}:{lang}"] += 1
        if outcome:
            _counts[f"{event}:{outcome}"] += 1
        path = os.getenv("EVENTS_FILE")
        if path:
            row = {"hour": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:00Z"),
                   "event": event, "lang": lang, "outcome": outcome}
            try:
                with open(path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(row) + "\n")
            except OSError:
                pass
    return True


def stats() -> dict:
    with _lock:
        return {"since": _since, "counts": dict(sorted(_counts.items()))}


def reset() -> None:
    with _lock:
        _counts.clear()
