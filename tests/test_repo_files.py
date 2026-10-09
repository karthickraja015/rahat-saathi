from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_deploy_and_docs_files_exist():
    for f in ("Dockerfile", "render.yaml", ".env.example", "README.md", ".github/workflows/tests.yml", ".gitignore"):
        assert (ROOT / f).exists(), f


def test_env_example_has_no_real_key():
    for line in (ROOT / ".env.example").read_text().splitlines():
        if line.startswith("LLM_API_KEY="):
            assert line.strip() == "LLM_API_KEY="


def test_gitignore_protects_secrets():
    g = (ROOT / ".gitignore").read_text().splitlines()
    assert ".env" in g and ".venv/" in g


def test_readme_has_safety_and_honest_sections():
    r = (ROOT / "README.md").read_text()
    for s in ("112", "Not affiliated", "Verification status", "Impact and evidence", "Apache-2.0"):
        assert s in r
