"""Build a fake college's data so Swatva can be tried without touching real records.

Every value here is made up. Aadhaar-style numbers pass the checksum so the
scanner can be tested, but they were generated at random and belong to no one.

    python scripts/make_sample_data.py            # writes sample_data/ and examples/
    python scripts/make_sample_data.py out_dir
"""

from __future__ import annotations

import csv
import random
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from swatva.detectors import verhoeff_check_digit  # noqa: E402

rng = random.Random(2027)

FIRST = ["Aarav", "Diya", "Krish", "Isha", "Vivaan", "Ananya", "Dhruv", "Riya", "Harsh", "Kavya",
         "Yash", "Nidhi", "Parth", "Khushi", "Rohan", "Mira", "Jay", "Pooja", "Meet", "Hetvi",
         "Aryan", "Sneha", "Dev", "Tanvi", "Kunal", "Bhumi", "Neel", "Riddhi", "Om", "Jinal"]
LAST = ["Patel", "Shah", "Desai", "Mehta", "Joshi", "Parmar", "Chauhan", "Solanki", "Rana", "Modi",
        "Trivedi", "Bhatt", "Vasava", "Gamit", "Chaudhari", "Naik", "Prajapati", "Panchal"]
FIRST_GU = {"Aarav": "આરવ", "Diya": "દિયા", "Krish": "ક્રિશ", "Isha": "ઈશા", "Vivaan": "વિવાન",
            "Ananya": "અનન્યા", "Dhruv": "ધ્રુવ", "Riya": "રિયા", "Harsh": "હર્ષ", "Kavya": "કાવ્યા"}
LAST_GU = {"Patel": "પટેલ", "Shah": "શાહ", "Desai": "દેસાઈ", "Mehta": "મહેતા", "Joshi": "જોષી"}
AREAS = ["Adajan", "Vesu", "Katargam", "Varachha", "Athwa", "Pal", "Udhna", "Citylight", "Bardoli", "Navsari"]
PINS = {"Adajan": "395009", "Vesu": "395007", "Katargam": "395004", "Varachha": "395006",
        "Athwa": "395001", "Pal": "395009", "Udhna": "394210", "Citylight": "395007",
        "Bardoli": "394601", "Navsari": "396445"}
BRANCHES = ["CE", "IT", "ME", "EE", "CIVIL", "AIDS"]
CATEGORIES = ["GEN"] * 5 + ["OBC"] * 3 + ["SEBC"] * 2 + ["SC", "ST", "EWS"]
BANKS = ["SBIN", "BARB", "HDFC", "ICIC", "PUNB", "UBIN", "KKBK"]
SCHEMES = ["MYSY", "Post Matric SC", "Post Matric ST", "Digital Gujarat OBC", "EWS Fee Waiver"]
DOMAINS = ["gmail.com", "yahoo.co.in", "outlook.com", "rediffmail.com"]
TODAY = date(2026, 11, 20)


def aadhaar() -> str:
    body = str(rng.randint(2, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(10))
    return body + verhoeff_check_digit(body)


def spaced(a: str) -> str:
    return f"{a[:4]} {a[4:8]} {a[8:]}"


def apaar() -> str:
    while True:
        v = "".join(str(rng.randint(0, 9)) for _ in range(12))
        if v[0] in "01" or verhoeff_check_digit(v[:11]) != v[11]:
            return v


def mobile() -> str:
    return str(rng.choice([6, 7, 8, 9])) + "".join(str(rng.randint(0, 9)) for _ in range(9))


def pan(person: bool = True) -> str:
    L = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return ("".join(rng.choice(L) for _ in range(3)) + ("P" if person else "C") + rng.choice(L)
            + "".join(str(rng.randint(0, 9)) for _ in range(4)) + rng.choice(L))


def ifsc() -> str:
    return rng.choice(BANKS) + "0" + "".join(str(rng.randint(0, 9)) for _ in range(6))


def account() -> str:
    return "".join(str(rng.randint(0, 9)) for _ in range(rng.choice([11, 12, 14, 15])))


def dob(min_age: int, max_age: int) -> date:
    start = TODAY - timedelta(days=365 * max_age)
    end = TODAY - timedelta(days=365 * min_age)
    return start + timedelta(days=rng.randint(0, (end - start).days))


def email_for(first: str, last: str) -> str:
    return f"{first.lower()}.{last.lower()}{rng.randint(1, 999)}@{rng.choice(DOMAINS)}"


def build(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    db_path = out / "college_erp.db"
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    c = con.cursor()

    c.executescript("""
    CREATE TABLE students (
        enrollment_no TEXT PRIMARY KEY, student_name TEXT, student_name_gujarati TEXT,
        branch TEXT, admission_year INTEGER, dob TEXT, gender TEXT, mobile_no TEXT,
        email_id TEXT, aadhaar_no TEXT, apaar_id TEXT, category TEXT, pwd_status TEXT,
        address TEXT, pincode TEXT, father_name TEXT, parent_mobile TEXT);
    CREATE TABLE scholarships (
        enrollment_no TEXT, scheme_name TEXT, academic_year TEXT, annual_family_income INTEGER,
        bank_account_no TEXT, ifsc_code TEXT, amount_sanctioned INTEGER, status TEXT);
    CREATE TABLE staff (
        emp_code TEXT PRIMARY KEY, staff_name TEXT, designation TEXT, department TEXT,
        pan_no TEXT, mobile TEXT, email TEXT, salary_account_no TEXT, ifsc TEXT, date_of_joining TEXT);
    CREATE TABLE marks (
        enrollment_no TEXT, semester INTEGER, subject_code TEXT, subject_name TEXT,
        internal INTEGER, external INTEGER, grade TEXT);
    CREATE TABLE courses (
        subject_code TEXT PRIMARY KEY, subject_name TEXT, branch TEXT, semester INTEGER, credits INTEGER);
    """)

    subjects = [
        ("3150703", "Analysis and Design of Algorithms"), ("3150711", "Software Engineering"),
        ("3160712", "Microprocessor and Interfacing"), ("3170716", "Artificial Intelligence"),
        ("3170717", "Cloud Computing"), ("3160707", "Advanced Java Programming"),
    ]
    for code, name in subjects:
        c.execute("INSERT INTO courses VALUES (?,?,?,?,?)", (code, name, rng.choice(BRANCHES), rng.randint(3, 8), 4))

    students = []
    for i in range(400):
        first, last = rng.choice(FIRST), rng.choice(LAST)
        year = rng.choice([2023, 2024, 2025, 2026])
        branch = rng.choice(BRANCHES)
        enr = f"{str(year)[2:]}0{rng.choice(['09', '11', '42'])}{BRANCHES.index(branch) + 1:02d}{i:04d}"
        # first-years admitted in 2026 include some 17 year olds
        born = dob(17, 20) if year == 2026 else dob(18 + (2026 - year), 21 + (2026 - year))
        area = rng.choice(AREAS)
        gu = (FIRST_GU.get(first, "") + " " + LAST_GU.get(last, "")).strip()
        row = (
            enr, f"{first} {last}", gu if " " in gu else "", branch, year,
            born.strftime("%d-%m-%Y"), rng.choice(["M", "F"]), mobile(),
            email_for(first, last), spaced(aadhaar()) if rng.random() < 0.6 else aadhaar(), apaar(),
            rng.choice(CATEGORIES), rng.choice(["No"] * 18 + ["Yes - Locomotor", "Yes - Low vision"]),
            f"{rng.randint(1, 240)}, {rng.choice(['Shanti', 'Gokul', 'Om', 'Sai'])} Society, {area}, Surat",
            PINS[area], f"{rng.choice(['Rajesh', 'Mahesh', 'Suresh', 'Dinesh', 'Kiran', 'Bharat'])} {last}",
            mobile(),
        )
        students.append(row)
    c.executemany(f"INSERT INTO students VALUES ({','.join('?' * 17)})", students)

    for s in rng.sample(students, 160):
        c.execute("INSERT INTO scholarships VALUES (?,?,?,?,?,?,?,?)", (
            s[0], rng.choice(SCHEMES), "2025-26", rng.choice([120000, 180000, 240000, 350000, 450000, 580000]),
            account(), ifsc(), rng.choice([25000, 50000, 75000, 100000]), rng.choice(["Approved", "Pending", "Disbursed"]),
        ))

    for i in range(45):
        first, last = rng.choice(FIRST), rng.choice(LAST)
        c.execute("INSERT INTO staff VALUES (?,?,?,?,?,?,?,?,?,?)", (
            f"EMP{1001 + i}", f"{'Dr. ' if rng.random() < 0.3 else 'Prof. '}{first} {last}",
            rng.choice(["Assistant Professor", "Associate Professor", "Lab Assistant", "Clerk"]),
            rng.choice(BRANCHES + ["Admin", "Accounts"]), pan(), mobile(), email_for(first, last),
            account(), ifsc(), (date(2010, 6, 1) + timedelta(days=rng.randint(0, 5000))).isoformat(),
        ))

    for s in students[:250]:
        for code, name in rng.sample(subjects, 3):
            internal, external = rng.randint(14, 30), rng.randint(28, 70)
            total = internal + external
            grade = "AA" if total >= 85 else "AB" if total >= 75 else "BB" if total >= 65 else "BC" if total >= 55 else "CC"
            c.execute("INSERT INTO marks VALUES (?,?,?,?,?,?,?)", (s[0], rng.randint(3, 8), code, name, internal, external, grade))
    con.commit()
    con.close()

    # A spreadsheet export from the admissions office
    with open(out / "admissions_2026.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Form No", "Candidate Name", "Date of Birth", "Category", "Mobile", "Email",
                    "Aadhaar Number", "ACPC Merit Rank", "Branch Allotted", "Fee Paid"])
        for i, s in enumerate([s for s in students if s[4] == 2026]):
            w.writerow([f"ACPC26{i + 3001}", s[1], s[5], s[11], s[7], s[8], s[9].replace(" ", ""),
                        rng.randint(1500, 42000), s[3], rng.choice(["Yes", "No"])])

    # The hostel office keeps a sheet where people type notes
    remarks = [
        "Room changed on request", "Parent visited, call father on {p} if late", "Fee pending",
        "Medical leave, contact {p}", "Shifted from block B", "", "", "Guardian email {e}",
        "Local guardian: uncle, mob {p}", "OK",
    ]
    with open(out / "hostel_allotment.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Roll No", "Name", "Hostel Name", "Room", "Check In", "Remarks"])
        for s in rng.sample(students, 120):
            r = rng.choice(remarks).format(p=mobile(), e=email_for("guardian", s[1].split()[1]))
            w.writerow([s[0], s[1], rng.choice(["Boys Hostel A", "Girls Hostel", "Boys Hostel B"]),
                        f"{rng.choice('ABC')}-{rng.randint(101, 320)}", "2026-07-15", r])

    # Something with no personal data at all, to show the scanner stays quiet
    with open(out / "timetable_sem5.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Day", "Slot", "Subject Code", "Subject Name", "Room"])
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri"]:
            for slot in ["09:00", "10:00", "11:15", "12:15"]:
                code, name = rng.choice(subjects)
                w.writerow([day, slot, code, name, f"Lab-{rng.randint(1, 6)}"])

    print(f"Sample college data written to {out}/")


def build_excel_example(path: Path) -> None:
    """A student list the way college offices really keep it: a title above the
    headers, numbers typed as numbers, real Excel dates, and a second sheet with
    Gujarati column names. Needs openpyxl."""
    import datetime as dt

    import openpyxl
    from openpyxl.styles import Font

    path.parent.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sem 3 CE"
    ws.append(["Shree Example Institute of Technology, Surat"])
    ws.append(["Student List 2026-27, Semester 3, Computer Engineering"])
    ws.append([])
    ws.append(["Sr No", "Enrollment No", "Name of Student", "DOB", "Gender", "Mobile No",
               "Aadhar No", "Caste", "Bank A/c No", "IFSC", "Remarks"])
    ws["A1"].font = Font(bold=True, size=14)
    for c in ws[4]:
        c.font = Font(bold=True)
    for i in range(60):
        first, last = rng.choice(FIRST), rng.choice(LAST)
        born = dob(18, 21)
        note = rng.choice(["", "", "", f"Father mob {mobile()}", "Scholarship form pending", ""])
        ws.append([
            i + 1, int(f"25009010{7000 + i}"), f"{last} {first}",
            dt.datetime(born.year, born.month, born.day), rng.choice(["M", "F"]),
            int(mobile()), int(aadhaar()), rng.choice(CATEGORIES), int(account()), ifsc(), note,
        ])
    for col, width in zip("ABCDEFGHIJK", [7, 16, 22, 12, 8, 14, 16, 8, 18, 14, 28]):
        ws.column_dimensions[col].width = width
    for row in ws.iter_rows(min_row=5, min_col=4, max_col=4):
        for cell in row:
            cell.number_format = "DD-MM-YYYY"

    gu = wb.create_sheet("હોસ્ટેલ")
    gu.append(["ક્રમ", "નામ", "મોબાઇલ", "આધાર નંબર", "રૂમ"])
    for i in range(30):
        first = rng.choice(list(FIRST_GU))
        last = rng.choice(list(LAST_GU))
        gu.append([i + 1, f"{FIRST_GU[first]} {LAST_GU[last]}", int(mobile()), spaced(aadhaar()), f"B-{rng.randint(101, 220)}"])
    wb.save(path)
    print(f"Excel example written to {path}")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    build(Path(sys.argv[1]) if len(sys.argv) > 1 else root / "sample_data")
    try:
        build_excel_example(root / "examples" / "student_list_sem3.xlsx")
    except ImportError:
        print("Skipped the Excel example: pip install openpyxl to build it")
