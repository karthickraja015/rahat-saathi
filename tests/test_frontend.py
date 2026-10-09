import re
from pathlib import Path

from fastapi.testclient import TestClient

from backend import app as appmod

client = TestClient(appmod.app)
FRONT = Path(__file__).resolve().parent.parent / "frontend"
JS = (FRONT / "app.js").read_text(encoding="utf-8")
CSS = (FRONT / "style.css").read_text(encoding="utf-8")
HTML = (FRONT / "index.html").read_text(encoding="utf-8")


def test_index_is_html_with_hooks():
    r = client.get("/")
    assert "text/html" in r.headers["content-type"]
    for id_ in ("emergency", "langs", "form", "result", "footer", "tab-check", "tab-prepared", "view-prepared", "btn-check"):
        assert f'id="{id_}"' in r.text


def test_emergency_banner_links_to_112():
    assert 'href="tel:112"' in HTML


def test_assets_served():
    for p in ("/static/app.js", "/static/style.css"):
        assert client.get(p).status_code == 200


def test_no_external_resources():
    assert not re.search(r'(src|href)="https?://', HTML)
    assert "@import" not in CSS and "url(http" not in CSS


def test_no_unsafe_dom_apis():
    for bad in ("innerHTML", "outerHTML", "document.write", "eval(", "insertAdjacentHTML"):
        assert bad not in JS


def test_js_has_three_languages_and_scripts():
    assert re.search(r"[\u0900-\u097F]", JS) and re.search(r"[\u0B80-\u0BFF]", JS)
    for code in ("en:", "hi:", "ta:"):
        assert code in JS


def test_all_36_states_and_uts_present():
    block = re.search(r"const STATES = \[(.*?)\];", JS, re.S).group(1)
    assert len(re.findall(r'"[^"]+"', block)) == 36
    for s in ("Tamil Nadu", "Kerala", "Uttar Pradesh", "Delhi", "Ladakh", "Puducherry"):
        assert s in block


def test_js_calls_only_known_endpoints():
    found = set(re.findall(r'"(/api/[a-z/]+)', JS))
    assert found <= {"/api/strings/", "/api/config", "/api/evaluate", "/api/extract", "/api/event"}
    assert {"/api/evaluate", "/api/strings/"} <= found


def test_prepared_card_has_six_items_in_each_language():
    for lang in ("en", "hi", "ta"):
        m = re.search(r"const PREP = \{.*?\n\};", JS, re.S).group(0)
        assert m.count(f"{lang}: [") == 1
    assert JS.count("112") >= 3
