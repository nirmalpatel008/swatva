# Personal data map

admissions_2026.csv, college_erp.db, hostel_allotment.csv and timetable_sem5.csv. Scanned on 23 November 2026 at 14:13 with Swatva 0.1.2, reading up to 1,000 rows from each table.

Personal data was found in **6 of 8 tables** and **36 of 68 columns**, covering 1,581 rows.

4 tables hold sensitive data, such as Aadhaar numbers, bank details, caste or category, family income or disability status.

82 records belong to people under 18. Under the DPDP Act, their data needs verifiable consent from a parent or guardian.

## What was found

| Personal data | Columns | Found in | What to do |
|---|--:|---|---|
| Person's name | 6 | admissions_2026.csv, staff, students, hostel_allotment.csv | Names make every other field in the row personal data. |
| Student / staff ID | 5 | marks, scholarships, staff, students, hostel_allotment.csv | Internal ID. Personal data because it points to one person. |
| Mobile number | 4 | admissions_2026.csv, staff, students | Contact data. Use it only for the purpose it was collected for. |
| Email address | 3 | admissions_2026.csv, staff, students | Contact data. Use it only for the purpose it was collected for. |
| Aadhaar number | 2 | admissions_2026.csv, students | Keep only if a rule requires it. Store the masked form (last 4 digits) wherever possible. |
| Bank account number | 2 | scholarships, staff | Financial data. Restrict access and delete once payments are settled. |
| Caste / category | 2 | admissions_2026.csv, students | Highly sensitive. Keep it only where reservation or scholarship rules need it, with tight access. |
| Date of birth | 2 | admissions_2026.csv, students | Shows age. Records of anyone under 18 need verifiable parental consent under DPDP. |
| IFSC code | 2 | scholarships, staff | Not personal on its own, but marks this table as holding bank details. |
| APAAR / ABC ID | 1 | students | Lifelong academic ID linked to Aadhaar. Limit who can see it. |
| Address | 1 | students | Home address. Limit who can see it. |
| Disability status | 1 | students | Health-related and highly sensitive. Restrict to the people who need it. |
| Family income | 1 | scholarships | Financial data about the family. Restrict to the scholarship cell. |
| Gender | 1 | students | Personal data. Collect it only where it is needed. |
| PAN | 1 | staff | Usually needed only for salary and TDS. Restrict to accounts staff. |
| PIN code | 1 | students | Part of an address. Fine on its own, sensitive next to a name. |
| Typed into notes (Email address, Mobile number) | 1 | hostel_allotment.csv | People typed identifiers into a notes field. These are easy to miss when deleting data. |

## Table by table

### admissions_2026.csv

106 rows, 10 columns. Holds sensitive data.

| Column | Holds | Found in sample | Example (masked) |
|---|---|---|---|
| `Candidate Name` | Person's name | 106 of 106 | `S. R.` |
| `Date of Birth` | Date of birth | 106 of 106, 41 under 18 | `XX-XX-2006` |
| `Category` | Caste / category | 106 of 106 | `[hidden]` |
| `Mobile` | Mobile number | 106 of 106 | `XXXXXX8102` |
| `Email` | Email address | 106 of 106 | `s***@outlook.com` |
| `Aadhaar Number` | Aadhaar number | 106 of 106 | `XXXXXXXX3898` |

No personal data in `Form No`, `ACPC Merit Rank`, `Branch Allotted`, `Fee Paid`.

### college_erp.db / courses

6 rows, 5 columns.

No personal data found.

### college_erp.db / marks

750 rows, 7 columns.

| Column | Holds | Found in sample | Example (masked) |
|---|---|---|---|
| `enrollment_no` | Student / staff ID | 750 of 750 | `XXXXXXX0000` |

No personal data in `semester`, `subject_code`, `subject_name`, `internal`, `external`, `grade`.

### college_erp.db / scholarships

160 rows, 8 columns. Holds sensitive data.

| Column | Holds | Found in sample | Example (masked) |
|---|---|---|---|
| `enrollment_no` | Student / staff ID | 160 of 160 | `XXXXXXX0211` |
| `annual_family_income` | Family income | 160 of 160 | `[hidden]` |
| `bank_account_no` | Bank account number | 160 of 160 | `XXXXXXXXXXX1904` |
| `ifsc_code` | IFSC code | 160 of 160 | `[hidden]` |

No personal data in `scheme_name`, `academic_year`, `amount_sanctioned`, `status`.

### college_erp.db / staff

45 rows, 10 columns. Holds sensitive data.

| Column | Holds | Found in sample | Example (masked) |
|---|---|---|---|
| `emp_code` | Student / staff ID | 45 of 45 | `XXX1001` |
| `staff_name` | Person's name | 45 of 45 | `P. K. B.` |
| `pan_no` | PAN | 45 of 45 | `XXXXXX049G` |
| `mobile` | Mobile number | 45 of 45 | `XXXXXX0203` |
| `email` | Email address | 45 of 45 | `k***@outlook.com` |
| `salary_account_no` | Bank account number | 45 of 45 | `XXXXXXX5872` |
| `ifsc` | IFSC code | 45 of 45 | `[hidden]` |

No personal data in `designation`, `department`, `date_of_joining`.

### college_erp.db / students

400 rows, 17 columns. Holds sensitive data.

| Column | Holds | Found in sample | Example (masked) |
|---|---|---|---|
| `enrollment_no` | Student / staff ID | 400 of 400 | `XXXXXXX0000` |
| `student_name` | Person's name | 400 of 400 | `H. P.` |
| `student_name_gujarati` | Person's name | 43 of 43 | `દ. દ.` |
| `dob` | Date of birth | 400 of 400, 41 under 18 | `XX-XX-2005` |
| `gender` | Gender | 400 of 400 | `[hidden]` |
| `mobile_no` | Mobile number | 400 of 400 | `XXXXXX2553` |
| `email_id` | Email address | 400 of 400 | `h***@rediffmail.com` |
| `aadhaar_no` | Aadhaar number | 400 of 400 | `XXXX XXXX 7485` |
| `apaar_id` | APAAR / ABC ID | 400 of 400 | `XXXXXXXX9119` |
| `category` | Caste / category | 400 of 400 | `[hidden]` |
| `pwd_status` | Disability status | 400 of 400 | `[hidden]` |
| `address` | Address | 400 of 400 | `[hidden]` |
| `pincode` | PIN code | 400 of 400 | `[hidden]` |
| `father_name` | Person's name | 400 of 400 | `D. P.` |
| `parent_mobile` | Mobile number | 400 of 400 | `XXXXXX8180` |

No personal data in `branch`, `admission_year`.

### hostel_allotment.csv

120 rows, 6 columns.

| Column | Holds | Found in sample | Example (masked) |
|---|---|---|---|
| `Roll No` | Student / staff ID | 120 of 120 | `XXXXXXX0368` |
| `Name` | Person's name | 120 of 120 | `P. B.` |
| `Remarks` | Typed into notes (Email address, Mobile number) | 44 of 92 | `[hidden]` |

No personal data in `Hostel Name`, `Room`, `Check In`.

### timetable_sem5.csv

20 rows, 5 columns.

No personal data found.

---

This report shows where personal data appears to be stored, based on a sample of rows. It is a starting point for DPDP Act preparation, not legal advice, and it can miss data or flag columns that are not personal. Values are masked: the report never shows full identifiers.
