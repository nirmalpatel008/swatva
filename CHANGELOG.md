# Changelog

## 0.1.1 (November 2026)

- **Try it in your browser** at [swatva.org/try.html](https://swatva.org/try.html): choose an Excel, CSV or SQLite file and get the report on the page. Nothing is uploaded.
- Reads files the way college offices really keep them: title rows above the headers, column names in Gujarati or Hindi, phone and ID numbers stored as numbers, and Excel's UTF-16 "Unicode text" exports.
- A clear message for old `.xls` files instead of skipping them silently.
- A real-world style Excel example (`examples/student_list_sem3.xlsx`) and a downloadable sample data bundle.
- Install straight from GitHub: `pip install git+https://github.com/nirmalpatel008/swatva.git openpyxl`.
- Tests run on Python 3.10, 3.12 and 3.14.

## 0.1.0 (November 2026)

- First release of the **Find** step: scans SQLite databases, CSV and Excel files for Indian personal data (Aadhaar with checksum, APAAR, PAN, mobile, email, bank account and IFSC, date of birth with under-18 count, caste or category, income, disability, gender, address, names in English, Gujarati and Hindi) and identifiers typed into notes fields.
- Writes a masked personal data map as Markdown, HTML and JSON.
- A fake college dataset for trying it safely.
- Website at [swatva.org](https://swatva.org).
