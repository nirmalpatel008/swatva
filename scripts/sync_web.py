"""Copy the scanner's Python files into docs/try/ so the in-browser version on
swatva.org runs exactly the same code as the command line tool.

    python scripts/sync_web.py

tests/test_web_copy.py fails if this has not been run after a change.
"""

from __future__ import annotations

import shutil
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


if __name__ == "__main__":
    sync()
