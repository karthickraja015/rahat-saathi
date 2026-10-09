import pytest

from backend.models import Facts, SEVERITY_RANK
from backend.rules_engine import evaluate_eligibility, load_rules
from tests.scenarios import BASE, SCENARIOS


@pytest.mark.parametrize("sc", SCENARIOS, ids=[s["id"] for s in SCENARIOS])
def test_scenario(sc):
    facts = Facts.from_dict({**BASE, **sc["facts"]})
    res = evaluate_eligibility(facts, now=sc["now"])
    codes = {r.code for r in res.reasons}
    assert res.status == sc["status"]
    assert res.escalation.route == sc["route"]
    assert set(sc["codes"]) <= codes
    assert not (set(sc["absent"]) & codes)
    rules = load_rules()
    assert all(r.rule_id in rules and r.severity in SEVERITY_RANK for r in res.reasons)
    assert 1 <= len(res.next_steps) <= 5
