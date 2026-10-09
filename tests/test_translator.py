import inspect
import re

import pytest

from backend import rules_engine as RE
from backend import translator as T
from backend.models import Status

SRC = inspect.getsource(RE)
REASON_CODES = set(re.findall(r'add\("([a-z_0-9]+)",\s*"R\d+"', SRC)) | {c for c, _ in RE._STEP_MAP}
STEP_CODES = set(re.findall(r'add\("([a-z_0-9]+)"\)', SRC)) | {s for _, s in RE._STEP_MAP}
QUESTION_KEYS = set(getattr(RE, "_QUESTION_ORDER", []))
LANG_CODES = ["en", "hi", "ta"]


def _missing(codes, section):
    return sorted(set(codes) - set(T.STRINGS["en"][section]))


def test_engine_codes_were_found():
    assert len(REASON_CODES) >= 20 and len(STEP_CODES) >= 8


def test_every_reason_code_translated():
    assert not _missing(REASON_CODES, "reason"), f"Add translations for reasons: {_missing(REASON_CODES, 'reason')}"


def test_every_step_code_translated():
    assert not _missing(STEP_CODES, "step"), f"Add translations for steps: {_missing(STEP_CODES, 'step')}"


def test_every_question_translated():
    assert not _missing(QUESTION_KEYS, "question"), f"Add translations for questions: {_missing(QUESTION_KEYS, 'question')}"


def test_every_status_and_route_translated():
    assert not _missing({s.value for s in Status}, "status")
    assert not _missing({"hospital_and_police", "district_collector"}, "route")


def test_languages_have_same_keys():
    for sec in T.STRINGS["en"]:
        for lang in ("hi", "ta"):
            assert set(T.STRINGS[lang][sec]) == set(T.STRINGS["en"][sec]), (lang, sec)


def test_no_empty_strings_and_placeholders_match():
    for sec, items in T.STRINGS["en"].items():
        for k, en in items.items():
            for lang in ("hi", "ta"):
                s = T.STRINGS[lang][sec][k]
                assert s.strip(), (lang, sec, k)
                assert T.placeholders(s) == T.placeholders(en), (lang, sec, k)


@pytest.mark.parametrize("sec", ["reason", "step", "question", "status", "route", "item", "group"])
def test_hindi_and_tamil_use_their_scripts(sec):
    for k in T.STRINGS["en"][sec]:
        assert re.search(r"[\u0900-\u097F]", T.STRINGS["hi"][sec][k]), ("hi", sec, k)
        assert re.search(r"[\u0B80-\u0BFF]", T.STRINGS["ta"][sec][k]), ("ta", sec, k)


def test_unknown_lang_falls_back_to_english():
    assert T.t("xx", "ui", "emergency") == T.STRINGS["en"]["ui"]["emergency"]


def test_missing_placeholder_does_not_crash():
    assert "—" in T.t("en", "reason", "police_pending")


@pytest.mark.parametrize("lang", LANG_CODES)
def test_112_in_emergency_banner(lang):
    assert "112" in T.STRINGS[lang]["ui"]["emergency"]
