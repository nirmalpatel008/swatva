# Swatva personal data map

Scanned 2026-11-21 15:34:08 with Swatva 0.1.0. Up to 1000 rows sampled per table.

## Summary

- **6 of 8** tables hold personal data, across 4 file(s).
- **36 of 68** columns contain personal data.
- **1,581** rows sit in tables with personal data.
- **4** table(s) hold sensitive data (Aadhaar, bank details, caste or category, income, or disability).
- **82** record(s) in the sample belong to people under 18. These need verifiable parental consent under DPDP.

## What was found

| Type of personal data | Columns |
|---|---|
| Person's name | 6 |
| Student / staff ID | 5 |
| Mobile number | 4 |
| Email address | 3 |
| Aadhaar number | 2 |
| Bank account number | 2 |
| Caste / category | 2 |
| Date of birth | 2 |
| IFSC code | 2 |
| Address | 1 |
| APAAR / ABC ID | 1 |
| Disability status | 1 |
| Email address (inside free text) | 1 |
| Mobile number (inside free text) | 1 |
| Gender | 1 |
| Family income | 1 |
| PAN | 1 |
| PIN code | 1 |

## Table by table

### admissions_2026.csv (sensitive)

106 rows, 10 columns.

| Column | Holds | Confidence | Matched in sample | Example (masked) |
|---|---|---|---|---|
| `Candidate Name` | Person's name | high | 106/106 (100%) | S. R. |
| `Date of Birth` | Date of birth | high | 106/106 (100%), 41 under 18 | XX-XX-2006 |
| `Category` | Caste / category | high | 106/106 (100%) | [hidden] |
| `Mobile` | Mobile number | high | 106/106 (100%) | XXXXXX8102 |
| `Email` | Email address | high | 106/106 (100%) | s***@outlook.com |
| `Aadhaar Number` | Aadhaar number | high | 106/106 (100%) | XXXXXXXX3898 |

- Names make every other field in the row personal data.
- Shows age. Records of anyone under 18 need verifiable parental consent under DPDP.
- Highly sensitive. Keep it only where reservation or scholarship rules need it, with tight access.
- Contact data. Use it only for the purpose it was collected for.
- Keep only if a rule requires it. Store the masked form (last 4 digits) wherever possible.

No personal data in: `Form No`, `ACPC Merit Rank`, `Branch Allotted`, `Fee Paid`

### college_erp.db : courses

6 rows, 5 columns.

No personal data found.

### college_erp.db : marks

750 rows, 7 columns.

| Column | Holds | Confidence | Matched in sample | Example (masked) |
|---|---|---|---|---|
| `enrollment_no` | Student / staff ID | high | 750/750 (100%) | XXXXXXX0000 |

- Internal ID. Personal data because it points to one person.

No personal data in: `semester`, `subject_code`, `subject_name`, `internal`, `external`, `grade`

### college_erp.db : scholarships (sensitive)

160 rows, 8 columns.

| Column | Holds | Confidence | Matched in sample | Example (masked) |
|---|---|---|---|---|
| `enrollment_no` | Student / staff ID | high | 160/160 (100%) | XXXXXXX0211 |
| `annual_family_income` | Family income | high | 160/160 (100%) | [hidden] |
| `bank_account_no` | Bank account number | high | 160/160 (100%) | XXXXXXXXXXX1904 |
| `ifsc_code` | IFSC code | high | 160/160 (100%) | [hidden] |

- Internal ID. Personal data because it points to one person.
- Financial data about the family. Restrict to the scholarship cell.
- Financial data. Restrict access and delete once payments are settled.
- Not personal on its own, but marks this table as holding bank details.

No personal data in: `scheme_name`, `academic_year`, `amount_sanctioned`, `status`

### college_erp.db : staff (sensitive)

45 rows, 10 columns.

| Column | Holds | Confidence | Matched in sample | Example (masked) |
|---|---|---|---|---|
| `emp_code` | Student / staff ID | high | 45/45 (100%) | XXX1001 |
| `staff_name` | Person's name | high | 45/45 (100%) | P. K. B. |
| `pan_no` | PAN | high | 45/45 (100%) | XXXXXX049G |
| `mobile` | Mobile number | high | 45/45 (100%) | XXXXXX0203 |
| `email` | Email address | high | 45/45 (100%) | k***@outlook.com |
| `salary_account_no` | Bank account number | high | 45/45 (100%) | XXXXXXX5872 |
| `ifsc` | IFSC code | high | 45/45 (100%) | [hidden] |

- Internal ID. Personal data because it points to one person.
- Names make every other field in the row personal data.
- Usually needed only for salary and TDS. Restrict to accounts staff.
- Contact data. Use it only for the purpose it was collected for.
- Financial data. Restrict access and delete once payments are settled.
- Not personal on its own, but marks this table as holding bank details.

No personal data in: `designation`, `department`, `date_of_joining`

### college_erp.db : students (sensitive)

400 rows, 17 columns.

| Column | Holds | Confidence | Matched in sample | Example (masked) |
|---|---|---|---|---|
| `enrollment_no` | Student / staff ID | high | 400/400 (100%) | XXXXXXX0000 |
| `student_name` | Person's name | high | 400/400 (100%) | H. P. |
| `student_name_gujarati` | Person's name | high | 43/43 (100%) | દ. દ. |
| `dob` | Date of birth | high | 400/400 (100%), 41 under 18 | XX-XX-2005 |
| `gender` | Gender | high | 400/400 (100%) | [hidden] |
| `mobile_no` | Mobile number | high | 400/400 (100%) | XXXXXX2553 |
| `email_id` | Email address | high | 400/400 (100%) | h***@rediffmail.com |
| `aadhaar_no` | Aadhaar number | high | 400/400 (100%) | XXXX XXXX 7485 |
| `apaar_id` | APAAR / ABC ID | high | 400/400 (100%) | XXXXXXXX9119 |
| `category` | Caste / category | high | 400/400 (100%) | [hidden] |
| `pwd_status` | Disability status | high | 400/400 (100%) | [hidden] |
| `address` | Address | high | 400/400 (100%) | [hidden] |
| `pincode` | PIN code | high | 400/400 (100%) | [hidden] |
| `father_name` | Person's name | high | 400/400 (100%) | D. P. |
| `parent_mobile` | Mobile number | high | 400/400 (100%) | XXXXXX8180 |

- Internal ID. Personal data because it points to one person.
- Names make every other field in the row personal data.
- Shows age. Records of anyone under 18 need verifiable parental consent under DPDP.
- Personal data. Collect it only where it is needed.
- Contact data. Use it only for the purpose it was collected for.
- Keep only if a rule requires it. Store the masked form (last 4 digits) wherever possible.
- Lifelong academic ID linked to Aadhaar. Limit who can see it.
- Highly sensitive. Keep it only where reservation or scholarship rules need it, with tight access.
- Health-related and highly sensitive. Restrict to the people who need it.
- Home address. Limit who can see it.
- Part of an address. Fine on its own, sensitive next to a name.

No personal data in: `branch`, `admission_year`

### hostel_allotment.csv

120 rows, 6 columns.

| Column | Holds | Confidence | Matched in sample | Example (masked) |
|---|---|---|---|---|
| `Roll No` | Student / staff ID | high | 120/120 (100%) | XXXXXXX0368 |
| `Name` | Person's name | high | 120/120 (100%) | P. B. |
| `Remarks` | Free text containing Email address, Mobile number | high | 44/92 (48%) | [hidden] |

- Internal ID. Personal data because it points to one person.
- Names make every other field in the row personal data.
- People typed identifiers into a notes field. These are easy to miss when deleting data.

No personal data in: `Hostel Name`, `Room`, `Check In`

### timetable_sem5.csv

20 rows, 5 columns.

No personal data found.

---

_This report shows where personal data appears to be stored, based on a sample of rows. It is a starting point for DPDP Act preparation, not legal advice, and it can miss data or flag columns that are not personal. Values are masked: the report never shows full identifiers._
