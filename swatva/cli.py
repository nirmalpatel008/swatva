"""Command line: swatva scan <files or folders>"""

from __future__ import annotations

import argparse
import os
import sys

from . import __version__
from .report import write_reports
from .scanner import label_for, scan


def _print_summary(r) -> None:
    w = sys.stdout.write
    personal = [t for t in r.tables if t.personal_columns]
    w(f"\nScanned {r.files} file(s), {len(r.tables)} table(s).\n")
    w(f"Personal data found in {len(personal)} table(s).\n\n")
    for t in personal:
        flag = "  [sensitive]" if t.sensitive else ""
        w(f"  {t.table.label}  ({t.table.total_rows:,} rows){flag}\n")
        for c in t.personal_columns:
            if c.finding:
                label = c.finding.detector.label
                if c.free_text_types:
                    label += " + " + ", ".join(label_for("free_text:" + k) for k in c.free_text_types)
            else:
                label = ", ".join(label_for("free_text:" + k) for k in c.free_text_types)
            w(f"    - {c.column}: {label}\n")
        w("\n")
    minors = sum(t.minors for t in r.tables)
    if minors:
        w(f"  {minors} record(s) in the sample belong to people under 18.\n\n")
    for f, e in r.errors:
        w(f"  Could not read {f}: {e}\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="swatva",
        description="Find personal data in your own databases and files. Nothing leaves your computer.",
    )
    ap.add_argument("--version", action="version", version=f"swatva {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("scan", help="scan files or folders and write a personal data map")
    sp.add_argument("paths", nargs="+", help="SQLite databases, CSV or Excel files, or folders")
    sp.add_argument("-o", "--out", default="swatva-report", help="folder for the reports (default: swatva-report)")
    sp.add_argument("--sample", type=int, default=1000, help="rows to sample per table (default: 1000)")
    sp.add_argument("--format", default="md,html,json", help="comma list of md, html, json (default: all)")
    sp.add_argument("-q", "--quiet", action="store_true", help="do not print the summary")

    args = ap.parse_args(argv)
    if args.cmd == "scan":
        try:
            result = scan(args.paths, sample=max(1, args.sample))
        except FileNotFoundError as e:
            print(f"swatva: {e}", file=sys.stderr)
            return 2
        formats = [f.strip().lower() for f in args.format.split(",") if f.strip()]
        written = write_reports(result, args.out, formats)
        if not args.quiet:
            _print_summary(result)
            for p in written:
                print(f"Report written: {os.path.relpath(p)}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
