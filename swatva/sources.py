"""Readers for the places small organizations keep data.

Each reader yields Table objects: a name, column names, a sample of rows and a
total row count. Nothing is copied anywhere; files are only read.
"""

from __future__ import annotations

import csv
import io
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

SQLITE_EXT = {".db", ".sqlite", ".sqlite3"}
CSV_EXT = {".csv", ".tsv"}
EXCEL_EXT = {".xlsx", ".xlsm"}
SUPPORTED = SQLITE_EXT | CSV_EXT | EXCEL_EXT


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
    if v is None:
        return ""
    if isinstance(v, bytes):
        return ""
    return str(v)


def read_sqlite(path: Path, sample: int) -> Iterator[Table]:
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
    reader = csv.reader(io.StringIO(text), delimiter=delim)
    header = next(reader, None)
    if not header:
        return
    rows, total = [], 0
    for r in reader:
        if not any(c.strip() for c in r):
            continue
        total += 1
        if len(rows) < sample:
            rows.append(r)
    yield Table(str(path), "csv", path.stem, [h.strip() for h in header], rows, total)


def read_excel(path: Path, sample: int) -> Iterator[Table]:
    try:
        import openpyxl  # optional
    except ImportError:
        raise RuntimeError("Excel support needs openpyxl: pip install openpyxl")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        for ws in wb.worksheets:
            it = ws.iter_rows(values_only=True)
            header = next(it, None)
            if not header:
                continue
            cols = [_s(h).strip() or f"column_{i + 1}" for i, h in enumerate(header)]
            rows, total = [], 0
            for r in it:
                if not any(v not in (None, "") for v in r):
                    continue
                total += 1
                if len(rows) < sample:
                    rows.append([_s(v) for v in r])
            yield Table(str(path), "excel", ws.title, cols, rows, total)
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
    else:
        raise ValueError(f"Unsupported file type: {path.name}")
