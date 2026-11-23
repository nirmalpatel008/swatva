"""Files the way colleges really keep them: title rows, Gujarati headers,
numbers stored as decimals, UTF-16 exports and old .xls files."""

import datetime

import openpyxl
import pytest

from swatva.detectors import verhoeff_check_digit
from swatva.scanner import scan
from swatva.sources import find_header

NAMES = ["Patel Rahul", "Shah Diya", "Desai Krish", "Mehta Isha", "Joshi Dhruv"]


def _aadhaar(i: int) -> str:
    body = str(30000000000 + i * 7919)
    return body + verhoeff_check_digit(body)


def _found(result, table_name):
    t = next(t for t in result.tables if t.table.name == table_name)
    return {c.column: c.finding.detector.id for c in t.columns if c.finding}


def test_header_found_below_title_rows():
    rows = [
        ["ABC Institute of Technology, Surat", "", "", ""],
        ["Student List 2025-26", "", "", ""],
        ["", "", "", ""],
        ["Sr No", "Name", "Mobile", "Aadhar No"],
        ["1", "Patel Rahul", "9876543210", "234567890124"],
    ]
    assert find_header(rows) == 3


def test_excel_with_title_rows_and_numeric_cells(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["ABC Institute of Technology, Surat"])
    ws.append(["Student List 2025-26 (Sem 3)"])
    ws.append([])
    ws.append(["Sr No", "Enrollment No", "Name of Student", "DOB", "Mobile No", "Aadhar No", "Caste", "Bank A/c No"])
    for i in range(20):
        ws.append([i + 1, 230090107000 + i, NAMES[i % 5], datetime.datetime(2005, 6, 14),
                   float(9876543210 + i), int(_aadhaar(i)), "OBC", 12345678901 + i])
    wb.save(tmp_path / "list.xlsx")

    r = scan([str(tmp_path / "list.xlsx")])
    found = _found(r, "Sheet1")
    assert found["Enrollment No"] == "student_id"
    assert found["Name of Student"] == "person_name"
    assert found["DOB"] == "dob"
    assert found["Mobile No"] == "phone"
    assert found["Aadhar No"] == "aadhaar"
    assert found["Bank A/c No"] == "bank_account"
    assert "Sr No" not in found
    assert r.tables[0].table.total_rows == 20


def test_gujarati_headers(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Data"
    ws.append(["નામ", "મોબાઇલ", "આધાર નંબર"])
    for i in range(20):
        ws.append(["રાહુલ પટેલ", 9876543210 + i, _aadhaar(i)])
    wb.save(tmp_path / "gu.xlsx")
    found = _found(scan([str(tmp_path / "gu.xlsx")]), "Data")
    assert found == {"નામ": "person_name", "મોબાઇલ": "phone", "આધાર નંબર": "aadhaar"}


def test_utf16_unicode_text_export(tmp_path):
    lines = "Name\tMobile\tEmail\n" + "".join(
        f"{NAMES[i % 5]}\t98765432{i:02d}\tperson{i}@gmail.com\n" for i in range(20))
    (tmp_path / "export.csv").write_text(lines, encoding="utf-16")
    found = _found(scan([str(tmp_path / "export.csv")]), "export")
    assert found == {"Name": "person_name", "Mobile": "phone", "Email": "email"}


def test_old_xls_gives_a_clear_message(tmp_path):
    (tmp_path / "old.xls").write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\0" * 64)
    r = scan([str(tmp_path)])
    assert len(r.errors) == 1
    assert "Save As" in r.errors[0][1]


def test_single_word_student_column(tmp_path):
    (tmp_path / "s.csv").write_text("Student;Phone\n" + "".join(
        f"{NAMES[i % 5]};98765432{i:02d}\n" for i in range(20)), encoding="utf-8")
    found = _found(scan([str(tmp_path / "s.csv")]), "s")
    assert found["Student"] == "person_name"
