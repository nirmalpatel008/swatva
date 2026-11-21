import importlib.util
import json
from datetime import date
from pathlib import Path

from swatva.report import to_dict, write_reports
from swatva.scanner import scan

ROOT = Path(__file__).resolve().parents[1]


def _build_sample(tmp_path: Path) -> Path:
    spec = importlib.util.spec_from_file_location("mk", ROOT / "scripts" / "make_sample_data.py")
    mk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mk)
    out = tmp_path / "data"
    mk.build(out)
    return out


def _types(result, table_name):
    t = next(t for t in result.tables if t.table.name == table_name)
    return {c.column: c.finding.detector.id for c in t.columns if c.finding}, t


def test_end_to_end_on_sample_college(tmp_path):
    data = _build_sample(tmp_path)
    r = scan([str(data)], today=date(2026, 11, 20))

    students, _ = _types(r, "students")
    assert students["aadhaar_no"] == "aadhaar"
    assert students["apaar_id"] == "apaar"
    assert students["mobile_no"] == "phone"
    assert students["category"] == "caste"
    assert students["pwd_status"] == "disability"
    assert students["student_name_gujarati"] == "person_name"
    assert "branch" not in students and "admission_year" not in students

    staff, _ = _types(r, "staff")
    assert staff["pan_no"] == "pan"
    assert staff["salary_account_no"] == "bank_account"

    _, courses = _types(r, "courses")
    assert not courses.personal_columns

    _, timetable = _types(r, "timetable_sem5")
    assert not timetable.personal_columns

    hostel = next(t for t in r.tables if t.table.name == "hostel_allotment")
    remarks = next(c for c in hostel.columns if c.column == "Remarks")
    assert "phone" in remarks.free_text_types
    assert next(c for c in hostel.columns if c.column == "Hostel Name").finding is None


def test_reports_are_written_and_masked(tmp_path):
    data = _build_sample(tmp_path)
    r = scan([str(data)], today=date(2026, 11, 20))
    files = write_reports(r, str(tmp_path / "out"), ["md", "html", "json"])
    assert len(files) == 3
    d = json.loads((tmp_path / "out" / "swatva-report.json").read_text())
    assert d["summary"]["tables_with_personal_data"] == 6

    # No full 10-digit mobile number may appear anywhere in the reports.
    import re
    for f in files:
        text = f.read_text(encoding="utf-8")
        assert not re.search(r"(?<![\dX])[6-9]\d{9}(?!\d)", text), f.name
    assert to_dict(r)["disclaimer"]
