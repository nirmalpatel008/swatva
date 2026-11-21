"""Runs the detectors over every table and collects the results."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from .detectors import DETECTORS_BY_ID, ColumnFinding, classify_column, scan_free_text
from .sources import Table, discover, read_tables


@dataclass
class ColumnResult:
    column: str
    finding: Optional[ColumnFinding]
    free_text_types: list[str] = field(default_factory=list)
    free_text_rows: int = 0
    sampled: int = 0

    @property
    def is_personal(self) -> bool:
        return self.finding is not None or bool(self.free_text_types)


@dataclass
class TableResult:
    table: Table
    columns: list[ColumnResult]

    @property
    def personal_columns(self) -> list[ColumnResult]:
        return [c for c in self.columns if c.is_personal]

    @property
    def sensitive(self) -> bool:
        return any(c.finding and c.finding.detector.sensitive for c in self.columns)

    @property
    def minors(self) -> int:
        return max((c.finding.minors for c in self.columns if c.finding), default=0)


@dataclass
class ScanResult:
    started: datetime
    today: date
    tables: list[TableResult]
    errors: list[tuple[str, str]]
    sample_size: int

    @property
    def files(self) -> int:
        return len({t.table.source for t in self.tables})

    def type_counts(self) -> dict[str, int]:
        """How many columns hold each kind of personal data."""
        counts: dict[str, int] = {}
        for t in self.tables:
            for c in t.columns:
                if c.finding:
                    counts[c.finding.detector.id] = counts.get(c.finding.detector.id, 0) + 1
                for k in c.free_text_types:
                    key = f"free_text:{k}"
                    counts[key] = counts.get(key, 0) + 1
        return counts

    def rows_with_personal_data(self) -> int:
        return sum(t.table.total_rows for t in self.tables if t.personal_columns)


# Columns where people type notes: worth searching for hidden identifiers.
_FREE_TEXT_HINT = ("remark", "note", "comment", "description", "detail", "reason", "message", "feedback", "address")


def scan_table(table: Table, today: date) -> TableResult:
    results = []
    for i, col in enumerate(table.columns):
        vals = table.column_values(i)
        finding = classify_column(col, vals, today=today)
        ft_types, ft_rows = [], 0
        is_free = finding is None or finding.detector.id == "address"
        if is_free and (any(h in col.lower() for h in _FREE_TEXT_HINT) or finding is None):
            ft_types, ft_rows = scan_free_text(vals)
            if finding is not None:
                # an address column holding a phone number is still worth flagging
                ft_types = [t for t in ft_types if t != finding.detector.id]
        nonempty = sum(1 for v in vals if v and v.strip())
        results.append(ColumnResult(col, finding, ft_types, ft_rows, nonempty))
    return TableResult(table, results)


def scan(paths: list[str], sample: int = 1000, today: Optional[date] = None) -> ScanResult:
    started = datetime.now()
    ref = today or started.date()
    tables: list[TableResult] = []
    errors: list[tuple[str, str]] = []
    for f in discover(paths):
        try:
            for t in read_tables(Path(f), sample):
                tables.append(scan_table(t, ref))
        except Exception as e:  # keep going: one broken file should not stop the scan
            errors.append((str(f), f"{type(e).__name__}: {e}"))
    return ScanResult(started, ref, tables, errors, sample)


def label_for(type_key: str) -> str:
    if type_key.startswith("free_text:"):
        inner = DETECTORS_BY_ID[type_key.split(":", 1)[1]].label
        return f"{inner} (inside free text)"
    return DETECTORS_BY_ID[type_key].label
