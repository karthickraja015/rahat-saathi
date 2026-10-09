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
