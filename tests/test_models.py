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
