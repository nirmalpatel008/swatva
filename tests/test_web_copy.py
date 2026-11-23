from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_browser_copy_matches_package():
    """docs/try/swatva must be identical to swatva/. Run scripts/sync_web.py after changes."""
    for name in ["__init__.py", "detectors.py", "sources.py", "scanner.py", "report.py"]:
        a = (ROOT / "swatva" / name).read_bytes()
        b = (ROOT / "docs" / "try" / "swatva" / name).read_bytes()
        assert a == b, f"docs/try/swatva/{name} is out of date: run python scripts/sync_web.py"
