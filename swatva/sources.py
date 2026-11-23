"""Readers for the places small organizations keep data.

Each reader yields Table objects: a name, column names, a sample of rows and a
total row count. Nothing is copied anywhere; files are only read.
"""

from __future__ import annotations

import csv
import io
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator

SQLITE_EXT = {".db", ".sqlite", ".sqlite3"}
CSV_EXT = {".csv", ".tsv"}
EXCEL_EXT = {".xlsx", ".xlsm"}
OLD_EXCEL_EXT = {".xls"}
SUPPORTED = SQLITE_EXT | CSV_EXT | EXCEL_EXT | OLD_EXCEL_EXT
HEADER_SEARCH_ROWS = 15


@dataclass
class Table:
    source: str  # file path
    kind: str  # sqlite, csv, excel
    name: str  # table, sheet or file name
    columns: list[str]
    rows: list[list[str]]  # sample rows as strings
    total_rows: int

    @property
    def label(self) -> str:
        base = os.path.basename(self.source)
        return base if self.kind == "csv" else f"{base} : {self.name}"

    def column_values(self, i: int) -> list[str]:
        return [r[i] if i < len(r) else "" for r in self.rows]


def _s(v) -> str:
    if v is None or isinstance(v, bytes):
        return ""
    if isinstance(v, float) and v.is_integer() and abs(v) < 1e18:
        return str(int(v))  # Excel often stores phone and ID numbers as 9876543210.0
    if isinstance(v, datetime):
        return v.date().isoformat() if (v.hour, v.minute, v.second) == (0, 0, 0) else v.isoformat(sep=" ")
    return str(v)


def _is_numberish(v: str) -> bool:
    t = v.strip().replace(",", "").replace(" ", "")
    return t.replace(".", "", 1).lstrip("+-").isdigit()


def find_header(rows: list[list[str]]) -> int:
    """Index of the header row among the first rows of a sheet.

    College sheets often start with a title ("ABC Institute ... Student List
    2025-26") and a blank line before the real column names. The header is
    the first row that is about as wide as the table and is mostly words.
    """
    top = rows[:HEADER_SEARCH_ROWS]
    widths = [sum(1 for c in r if c.strip()) for r in top]
    if not widths:
        return 0
    widest = max(widths)
    for i, r in enumerate(top):
        cells = [c for c in r if c.strip()]
        if len(cells) >= max(2, 0.6 * widest):
            words = sum(1 for c in cells if not _is_numberish(c))
            if words >= 0.7 * len(cells):
                return i
    return 0


def _split_header(raw: list[list[str]]) -> tuple[list[str], list[list[str]]]:
    h = find_header(raw)
    header = raw[h] if raw else []
    body = raw[h + 1:]
    width = max([len(header)] + [len(r) for r in body[:50]]) if raw else 0
    cols = []
    for i in range(width):
        name = header[i].strip() if i < len(header) else ""
        cols.append(name or f"column_{i + 1}")
    return cols, body


def read_sqlite(path: Path, sample: int) -> Iterator[Table]:
    import sqlite3  # loaded only when a database is scanned (keeps the browser version light)

    uri = f"file:{path.resolve().as_posix()}?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    try:
        names = [
            r[0]
            for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        for t in names:
            q = t.replace('"', '""')
            cur = con.execute(f'SELECT * FROM "{q}" LIMIT ?', (sample,))
            cols = [d[0] for d in cur.description]
            rows = [[_s(v) for v in r] for r in cur.fetchall()]
            total = con.execute(f'SELECT COUNT(*) FROM "{q}"').fetchone()[0]
            yield Table(str(path), "sqlite", t, cols, rows, total)
    finally:
        con.close()


def _open_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):  # Excel "Unicode text" export
        return raw.decode("utf-16")
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def read_csv(path: Path, sample: int) -> Iterator[Table]:
    text = _open_text(path)
    delim = "\t" if path.suffix.lower() == ".tsv" else ","
    if delim == ",":
        try:
            delim = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|").delimiter
        except csv.Error:
            pass
    all_rows = [r for r in csv.reader(io.StringIO(text), delimiter=delim)]
    if not any(any(c.strip() for c in r) for r in all_rows):
        return
    head = [r for r in all_rows[:HEADER_SEARCH_ROWS + 1]]
    h = find_header(head)
    cols, _ = _split_header(all_rows[: h + 51])
    body = [r for r in all_rows[h + 1:] if any(c.strip() for c in r)]
    yield Table(str(path), "csv", path.stem, cols, body[:sample], len(body))


def read_excel(path: Path, sample: int) -> Iterator[Table]:
    try:
        import openpyxl  # optional
    except ImportError:
        raise RuntimeError("Excel support needs openpyxl: pip install openpyxl")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        for ws in wb.worksheets:
            it = ws.iter_rows(values_only=True)
            head = []
            for r in it:
                head.append([_s(v) for v in r])
                if len(head) > HEADER_SEARCH_ROWS:
                    break
            if not any(any(c.strip() for c in r) for r in head):
                continue
            h = find_header(head)
            cols, body = _split_header(head)
            rows = [r for r in body if any(c.strip() for c in r)]
            total = len(rows)
            for r in it:
                if not any(v not in (None, "") for v in r):
                    continue
                total += 1
                if len(rows) < sample:
                    rows.append([_s(v) for v in r])
            yield Table(str(path), "excel", ws.title, cols, rows[:sample], total)
    finally:
        wb.close()


def discover(paths: list[str]) -> list[Path]:
    """Expand files and folders into the list of supported files."""
    found: list[Path] = []
    for p in paths:
        pp = Path(p)
        if pp.is_dir():
            for root, dirs, files in os.walk(pp):
                dirs[:] = sorted(d for d in dirs if not d.startswith("."))
                for f in sorted(files):
                    fp = Path(root) / f
                    if fp.suffix.lower() in SUPPORTED and not f.startswith("~$"):
                        found.append(fp)
        elif pp.is_file():
            found.append(pp)
        else:
            raise FileNotFoundError(f"Not found: {p}")
    return found


def read_tables(path: Path, sample: int) -> Iterator[Table]:
    ext = path.suffix.lower()
    if ext in SQLITE_EXT:
        yield from read_sqlite(path, sample)
    elif ext in CSV_EXT:
        yield from read_csv(path, sample)
    elif ext in EXCEL_EXT:
        yield from read_excel(path, sample)
    elif ext in OLD_EXCEL_EXT:
        raise ValueError("old .xls format is not supported yet. Open it in Excel and use Save As > .xlsx, then scan again")
    else:
        raise ValueError(f"Unsupported file type: {path.name}")
