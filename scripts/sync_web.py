"""Copy the scanner's Python files into docs/try/ so the in-browser version on
swatva.org runs exactly the same code as the command line tool, and rebuild the
sample report shown on the website.

    python scripts/sync_web.py

tests/test_web_copy.py fails if this has not been run after a change.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULES = ["__init__.py", "detectors.py", "sources.py", "scanner.py", "report.py"]


def sync() -> None:
    dest = ROOT / "docs" / "try" / "swatva"
    dest.mkdir(parents=True, exist_ok=True)
    for name in MODULES:
        shutil.copyfile(ROOT / "swatva" / name, dest / name)
    shutil.copyfile(ROOT / "examples" / "student_list_sem3.xlsx", ROOT / "docs" / "try" / "student_list_sem3.xlsx")
    print(f"Copied {len(MODULES)} modules and the sample workbook to {dest.parent}")

    sys.path.insert(0, str(ROOT))
    from swatva.report import to_html, to_markdown
    from swatva.scanner import scan

    result = scan([str(ROOT / "sample_data")])
    (ROOT / "docs" / "sample-report.html").write_text(to_html(result, home_url="./"), encoding="utf-8")
    (ROOT / "docs" / "sample-report.md").write_text(to_markdown(result), encoding="utf-8")
    print("Rebuilt docs/sample-report.html and docs/sample-report.md")


if __name__ == "__main__":
    sync()
