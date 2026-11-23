# Swatva

[![tests](https://github.com/nirmalpatel008/swatva/actions/workflows/ci.yml/badge.svg)](https://github.com/nirmalpatel008/swatva/actions/workflows/ci.yml)

**Find the personal data your organization holds, on your own machine, for free.**

[Website](https://swatva.org) | [Try it in your browser](https://swatva.org/try.html) | [Sample report](https://swatva.org/sample-report.html) | [Changelog](CHANGELOG.md)

Swatva (स्वत्व, "what is one's own") is an open-source toolkit that helps small Indian organizations get ready for the Digital Personal Data Protection (DPDP) Act, 2023. It starts with colleges.

From **13 May 2027**, every organization in India that holds personal data has to give proper notices, keep that data safe, report breaches within 72 hours, and answer when someone asks to see, correct or delete their data. There's no exemption for being small. Large companies will buy software and hire consultants. A college with a two-person IT team can't, and the first question it can't answer is simple: **where is our personal data?**

That's what this first version does.

> **Status:** early prototype (v0.1). The scanner works today. Tracking changes, handling data requests and generating notices are on the roadmap below.

## What it does

Point Swatva at a college's databases and spreadsheets. It reads a sample of each table, works out which columns hold personal data, and writes a **personal data map** as Markdown, HTML and JSON.

```
$ swatva scan sample_data

Scanned 4 file(s), 8 table(s).
Personal data found in 6 table(s).

  college_erp.db : students  (400 rows)  [sensitive]
    - enrollment_no: Student / staff ID
    - student_name_gujarati: Person's name
    - dob: Date of birth
    - aadhaar_no: Aadhaar number
    - apaar_id: APAAR / ABC ID
    - category: Caste / category
    - pwd_status: Disability status
    ...
  hostel_allotment.csv  (120 rows)
    - Remarks: Email address (inside free text), Mobile number (inside free text)

  82 record(s) in the sample belong to people under 18.
```

See a full example in [`docs/sample-report.md`](docs/sample-report.md).

## The privacy promise

- **Nothing leaves your machine.** No cloud, no upload, no telemetry. The installed tool makes no network calls at all. The [browser version](https://swatva.org/try.html) downloads Swatva's code once, then scans your file inside the page without sending it anywhere.
- **Files are opened read-only.** Swatva never changes your data.
- **Reports never show full values.** Every example is masked (`XXXXXXXX3898`, `r***@gmail.com`, `R. P.`), so a report is safe to share with your principal or your auditor.
- **No dependencies** beyond Python itself (Excel support needs `openpyxl`).

## Quick start

**No install at all:** open [swatva.org/try.html](https://swatva.org/try.html), choose an Excel, CSV or SQLite file, and the report appears in your browser. The file is read and scanned on the page itself and never uploaded.

To run it on your own computer, you need Python 3.10 or newer.

**Fastest way, no git needed:**

```bash
pip install git+https://github.com/nirmalpatel008/swatva.git openpyxl
```

Download the [sample files](https://swatva.org/swatva-sample-data.zip) (all fake), unzip them, and run:

```bash
python -m swatva scan swatva-sample-data
```

**Or from a clone, for development:**

```bash
git clone https://github.com/nirmalpatel008/swatva.git
cd swatva
pip install -e ".[excel]"

# Try it on a fake college, no real data needed
swatva scan sample_data
swatva scan examples/student_list_sem3.xlsx

# Then on your own files
swatva scan path/to/erp.db path/to/admissions.xlsx path/to/folder -o my-report
```

Open `my-report/swatva-report.html` in a browser.

**On Windows:** if `swatva` is not recognised after installing, use `python -m swatva` instead. It does exactly the same thing:

```
python -m swatva scan sample_data
start swatva-report\swatva-report.html
```

Options: `--sample 5000` reads more rows per table, `--format html` writes only one format, `-q` skips the terminal summary.

### What's in the sample data

Everything is made up: no real person's data is in this repo.

| File | What it shows |
|---|---|
| `sample_data/college_erp.db` | A fake college database: students, scholarships, staff, marks, courses |
| `sample_data/admissions_2026.csv` | An admissions office export |
| `sample_data/hostel_allotment.csv` | Phone numbers typed into a Remarks column |
| `sample_data/timetable_sem5.csv` | No personal data, so Swatva should stay quiet |
| `examples/student_list_sem3.xlsx` | A real-world style Excel sheet: title rows above the headers, numbers stored as numbers, and a second sheet with Gujarati column names |

`python scripts/make_sample_data.py` rebuilds all of them.

## What it finds

| Kind | Examples | How it decides |
|---|---|---|
| Aadhaar number | `2345 6789 0124` | 12 digits, valid Verhoeff checksum, works even without a helpful column name |
| APAAR / ABC ID | 12-digit academic ID | 12 digits in a column named like `apaar` or `abc_id` |
| PAN | `ABCPE1234F` | Format plus a valid holder-type letter |
| Mobile number | `98765 43210`, `+91...` | Indian mobile format |
| Email | | Address format |
| Bank account, IFSC | | IFSC by format; account numbers only when the column name says so |
| Date of birth | | Dates in a DOB column; **counts people under 18** |
| Caste / category | `OBC`, `SC`, `ST`, `SEBC`, `EWS` | Known category values or column name |
| Family income, disability, gender, address, PIN | | Column name plus a value check |
| Person's name | English, Gujarati and Hindi script | Column name, skipping things like `subject_name` or `hostel_name` |
| Student / staff ID | enrolment no, roll no, emp code | Column name |
| **Identifiers typed into notes** | "call father on 98250..." | Searches remarks and comments fields |

That last row matters. The data people forget about when they delete a student's records is usually sitting in a notes column.

It reads **SQLite** databases, **CSV / TSV** files (including Excel's UTF-16 "Unicode text" exports), **Excel** workbooks (every sheet), and whole folders of them. It copes with the way college sheets are really kept: title rows above the headers, column names in Gujarati or Hindi, and phone or ID numbers stored as numbers. Old `.xls` files need to be saved as `.xlsx` first.

## Limits

This is a starting point, not a compliance certificate.

- It looks at a sample of rows (1,000 by default), so rare values can be missed.
- Detection uses formats and column names. A column called `x1` holding names won't be found yet.
- It doesn't yet connect to MySQL, PostgreSQL, Google Drive or college ERP systems directly. Export to CSV for now.
- It is not legal advice.

## Read the law

- [Digital Personal Data Protection Act, 2023](https://www.indiacode.nic.in/bitstream/123456789/22037/2/a2023-22.pdf) on India Code
- [Digital Personal Data Protection Rules, 2025](https://www.meity.gov.in/documents/act-and-policies/digital-personal-data-protection-rules-2025-gDOxUjMtQWa?pageTitle=Digital-Personal-Data-Protection-Rules-2025) on MeitY's site
- [DPDP Rules, 2025 Notified](https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc20251117695301.pdf), the government's plain-language explainer from PIB

Swatva is not legal advice.

## Similar tools

Other open-source projects work on parts of the same problem, and they're worth knowing about:

- [truScanner](https://github.com/truconsent/truscanner) by truConsent scans **source code** for over 300 kinds of personal data, with optional AI providers.
- [dpdp-scan](https://github.com/statecheck-security/dpdp-scan) finds Indian identifiers such as Aadhaar, PAN, UPI and IFSC in **code, schemas, fixtures and logs**, and maps findings to the DPDP Act.
- [tsi-dpdp-cms](https://github.com/tsi-coop/tsi-dpdp-cms) is an open-source **consent management** system for the DPDP Act.
- [PrivacyHub](https://github.com/privacypriority/privacyanalyzer) uses AI to explain websites' **privacy policies** to the people who use them.
- [Microsoft Presidio](https://github.com/microsoft/presidio) is a general-purpose framework for detecting and anonymising personal data in text.

Swatva's focus is different. It looks at the data an organization **already holds**, in the spreadsheets, exports and databases where offices actually keep it, and it is built for the non-technical staff who run small colleges, clinics and NGOs: a browser version with nothing to install, Gujarati and Hindi support, and a report a principal can read. If one of these tools fits your need better, use it.

## Roadmap

Swatva is planned in four parts:

1. **Find** (this release): map where personal data lives.
2. **Track**: keep a change log of personal data using change data capture, so an organization can prove what happened to a record and when.
3. **Act**: answer "show me everything you hold on me" in one search, carry out deletions with proof, flag data kept past its retention period, and walk staff through a 72-hour breach report.
4. **Explain**: generate plain-language notices and consent forms in English, Gujarati and Hindi.

Next for the scanner: MySQL and PostgreSQL connectors, a small local model for names in free text, and a simple web dashboard for non-technical staff.

The plan is to build all of this **with** the colleges that use it. Their IT staff will decide what it checks first.

## Contributing

Issues and pull requests are welcome, especially:

- detectors for identifiers we've missed (voter ID, driving licence, ration card, UDISE+ IDs)
- better Gujarati, Hindi and other Indian-language support
- real-world column names from college ERPs (names only, never data)

Run the tests with `pip install -e ".[dev]" && pytest`. The browser version in `docs/try/` runs a copy of the same code: after changing anything in `swatva/`, run `python scripts/sync_web.py` (a test checks the copy is current).

**Never commit real personal data**, not even in an issue. Use `scripts/make_sample_data.py` to build test data. Every value it makes is fake.

## License

MIT. Free to use, change and share.
