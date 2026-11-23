"""Turns a scan into a personal-data map: Markdown, HTML and JSON."""

from __future__ import annotations

import html
import json
import os
from datetime import datetime
from pathlib import Path

from . import __version__
from .detectors import DETECTORS_BY_ID
from .scanner import ScanResult, TableResult, label_for

DISCLAIMER = (
    "This report shows where personal data appears to be stored, based on a sample of rows. "
    "It is a starting point for DPDP Act preparation, not legal advice, and it can miss data "
    "or flag columns that are not personal. Values are masked: the report never shows full identifiers."
)

def _summary(r: ScanResult) -> dict:
    personal_tables = [t for t in r.tables if t.personal_columns]
    n_cols = sum(len(t.columns) for t in r.tables)
    n_personal = sum(len(t.personal_columns) for t in r.tables)
    minors = sum(t.minors for t in r.tables)
    return {
        "files": r.files,
        "tables": len(r.tables),
        "tables_with_personal_data": len(personal_tables),
        "columns": n_cols,
        "columns_with_personal_data": n_personal,
        "rows_in_tables_with_personal_data": r.rows_with_personal_data(),
        "tables_with_sensitive_data": sum(1 for t in r.tables if t.sensitive),
        "minors_in_sample": minors,
    }


def _finding_rows(t: TableResult) -> list[dict]:
    out = []
    for c in t.personal_columns:
        if c.finding:
            d = c.finding.detector
            out.append({
                "column": c.column,
                "type": d.id,
                "label": d.label,
                "group": d.group,
                "sensitive": d.sensitive,
                "confidence": c.finding.confidence,
                "matched": c.finding.matched,
                "sampled": c.finding.sampled,
                "example": c.finding.example,
                "minors": c.finding.minors,
                "note": d.note,
                "also_in_text": [DETECTORS_BY_ID[k].label for k in c.free_text_types],
            })
        else:
            labels = [DETECTORS_BY_ID[k].label for k in c.free_text_types]
            out.append({
                "column": c.column,
                "type": "free_text",
                "label": "Typed into notes (" + ", ".join(labels) + ")",
                "group": "contact",
                "sensitive": "aadhaar" in c.free_text_types,
                "confidence": "high",
                "matched": c.free_text_rows,
                "sampled": c.sampled,
                "example": "[hidden]",
                "minors": 0,
                "note": "People typed identifiers into a notes field. These are easy to miss when deleting data.",
                "also_in_text": [],
            })
    return out


def to_dict(r: ScanResult) -> dict:
    return {
        "tool": "swatva",
        "version": __version__,
        "scanned_at": r.started.isoformat(timespec="seconds"),
        "sample_rows_per_table": r.sample_size,
        "summary": _summary(r),
        "types_found": {k: {"label": label_for(k), "columns": v} for k, v in sorted(r.type_counts().items())},
        "tables": [
            {
                "source": t.table.source,
                "kind": t.table.kind,
                "name": t.table.name,
                "rows": t.table.total_rows,
                "columns": len(t.columns),
                "sensitive": t.sensitive,
                "minors_in_sample": t.minors,
                "findings": _finding_rows(t),
                "clean_columns": [c.column for c in t.columns if not c.is_personal],
            }
            for t in r.tables
        ],
        "errors": [{"file": f, "error": e} for f, e in r.errors],
        "disclaimer": DISCLAIMER,
    }


def _pct(m: int, n: int) -> str:
    return f"{round(100 * m / n)}%" if n else "-"


_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"]


def _nice_date(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
    except ValueError:
        return iso
    return f"{dt.day} {_MONTHS[dt.month - 1]} {dt.year} at {dt:%H:%M}"


def _table_name(t: dict) -> tuple[str, str]:
    """(file, table) for display. CSV files have no separate table name."""
    base = os.path.basename(t["source"])
    return (base, "") if t["kind"] == "csv" else (base, t["name"])


def _files_phrase(d: dict) -> str:
    names = []
    for t in d["tables"]:
        b = os.path.basename(t["source"])
        if b not in names:
            names.append(b)
    if not names:
        return "No files"
    if len(names) == 1:
        return names[0]
    if len(names) <= 4:
        return ", ".join(names[:-1]) + " and " + names[-1]
    return f"{names[0]} and {len(names) - 1} other files"


def _plural(n: int, one: str, many: str | None = None) -> str:
    return f"{n:,} {one if n == 1 else (many or one + 's')}"


def _kinds(d: dict) -> list[dict]:
    """One row per kind of personal data: how many columns, where, and what to do."""
    rows: dict[str, dict] = {}
    for t in d["tables"]:
        file, table = _table_name(t)
        where = table or file
        for f in t["findings"]:
            r = rows.setdefault(f["label"], {"label": f["label"], "columns": 0, "where": [],
                                             "note": f["note"], "sensitive": f["sensitive"]})
            r["columns"] += 1
            if where not in r["where"]:
                r["where"].append(where)
    return sorted(rows.values(), key=lambda r: (-r["columns"], r["label"]))


def _summary_sentences(d: dict) -> list[str]:
    s = d["summary"]
    out = [
        f"Personal data was found in **{s['tables_with_personal_data']} of {s['tables']} tables** "
        f"and **{s['columns_with_personal_data']} of {s['columns']} columns**, "
        f"covering {_plural(s['rows_in_tables_with_personal_data'], 'row')}."
    ]
    if s["tables_with_sensitive_data"]:
        out.append(
            f"{_plural(s['tables_with_sensitive_data'], 'table holds', 'tables hold')} sensitive data, "
            "such as Aadhaar numbers, bank details, caste or category, family income or disability status."
        )
    if s["minors_in_sample"]:
        out.append(
            f"{_plural(s['minors_in_sample'], 'record belongs', 'records belong')} to people under 18. "
            "Under the DPDP Act, their data needs verifiable consent from a parent or guardian."
        )
    return out


def to_markdown(r: ScanResult) -> str:
    d = to_dict(r)
    L = ["# Personal data map", ""]
    L.append(f"{_files_phrase(d)}. Scanned on {_nice_date(d['scanned_at'])} with Swatva {d['version']}, "
             f"reading up to {d['sample_rows_per_table']:,} rows from each table.")
    L.append("")
    for line in _summary_sentences(d):
        L.append(line)
        L.append("")
    kinds = _kinds(d)
    if kinds:
        L += ["## What was found", "", "| Personal data | Columns | Found in | What to do |", "|---|--:|---|---|"]
        for k in kinds:
            L.append(f"| {k['label']} | {k['columns']} | {', '.join(k['where'])} | {k['note']} |")
        L.append("")
    L += ["## Table by table"]
    for t in d["tables"]:
        file, table = _table_name(t)
        L += ["", f"### {file}" + (f" / {table}" if table else "")]
        meta = f"{_plural(t['rows'], 'row')}, {_plural(t['columns'], 'column')}."
        if t["sensitive"]:
            meta += " Holds sensitive data."
        L += ["", meta]
        if not t["findings"]:
            L += ["", "No personal data found."]
            continue
        L += ["", "| Column | Holds | Found in sample | Example (masked) |", "|---|---|---|---|"]
        for f in t["findings"]:
            holds = f["label"] + (f", plus {', '.join(f['also_in_text'])} in the text" if f["also_in_text"] else "")
            found = f"{f['matched']:,} of {f['sampled']:,}"
            if f["minors"]:
                found += f", {f['minors']} under 18"
            if f["confidence"] != "high":
                holds += f" ({f['confidence']} confidence)"
            L.append(f"| `{f['column']}` | {holds} | {found} | `{f['example']}` |")
        if t["clean_columns"]:
            L += ["", "No personal data in " + ", ".join(f"`{c}`" for c in t["clean_columns"]) + "."]
    if d["errors"]:
        L += ["", "## Files that could not be read", ""]
        L += [f"- {os.path.basename(e['file'])}: {e['error']}" for e in d["errors"]]
    L += ["", "---", "", DISCLAIMER, ""]
    return "\n".join(L)


_CSS = """
:root{--bg:#fff;--fg:#1e2330;--muted:#5b6476;--faint:#8a93a6;--rule:#e3e7ee;--ink:#1b2f7a;
--mark:#ffe36e;--mark-fg:#1e2330;--code:#f3f5f9}
@media (prefers-color-scheme:dark){:root{--bg:#12161f;--fg:#e6e9f2;--muted:#a3abbd;--faint:#7d869a;
--rule:#2a3144;--ink:#a9b8ff;--mark:#6b5a0f;--mark-fg:#fff3b8;--code:#1c2233}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:15.5px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,Roboto,sans-serif;-webkit-font-smoothing:antialiased}
main{max-width:980px;margin:0 auto;padding:48px 24px 72px}
.serif,h1,h2{font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;font-weight:400;color:var(--ink)}
.top{display:flex;justify-content:space-between;align-items:baseline;gap:16px;margin-bottom:40px;
font-size:14px;color:var(--muted)}
.top .serif{font-size:20px}
.top a{color:var(--muted)}
h1{font-size:40px;line-height:1.1;margin:0 0 10px;letter-spacing:-.01em}
.meta{color:var(--muted);margin:0;max-width:70ch}
.lead{margin:32px 0 0;padding:24px 0 0;border-top:1px solid var(--rule);max-width:68ch}
.lead p{margin:0 0 10px;font-size:18px;line-height:1.55}
.lead p:first-child{font-size:21px;line-height:1.45}
mark{background:linear-gradient(transparent 18%,var(--mark) 18%,var(--mark) 88%,transparent 88%);
color:var(--mark-fg);padding:0 2px}
h2{font-size:26px;margin:56px 0 14px}
table{border-collapse:collapse;width:100%;font-size:14.5px}
th,td{text-align:left;padding:9px 16px 9px 0;border-bottom:1px solid var(--rule);vertical-align:top}
th{font-weight:500;color:var(--muted);font-size:13px;border-bottom-color:var(--fg)}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td.where,td.todo{color:var(--muted);font-size:13.5px}
code{font:13px/1.4 ui-monospace,"SF Mono",Menlo,Consolas,monospace}
td code.col{color:var(--fg)}
td code.ex{color:var(--muted)}
.wrap{overflow-x:auto}
section.t{margin:34px 0 0;break-inside:avoid-page}
h3{font-size:16px;font-weight:600;margin:0}
h3 .sub{color:var(--muted);font-weight:400}
.tmeta{color:var(--muted);font-size:14px;margin:2px 0 10px}
.sens{color:var(--fg);background:linear-gradient(transparent 62%,var(--mark) 62%);padding:0 1px}
.small{display:block;color:var(--faint);font-size:12.5px}
.clean,.none{color:var(--muted);font-size:13.5px;margin:10px 0 0}
.errors li{color:var(--muted)}
footer{margin-top:64px;padding-top:18px;border-top:1px solid var(--rule);color:var(--muted);font-size:13px;max-width:78ch}
@media (max-width:640px){main{padding:28px 16px 48px}h1{font-size:32px}.lead p:first-child{font-size:19px}
th,td{padding-right:12px}.top{margin-bottom:28px}
table.kinds thead{display:none}table.kinds tr{display:grid;grid-template-columns:1fr auto;column-gap:12px;
padding:12px 0;border-bottom:1px solid var(--rule)}table.kinds td{border:0;padding:0}
table.kinds td.where,table.kinds td.todo{grid-column:1/-1;padding-top:4px}
table.cols thead{display:none}table.cols tr{display:grid;grid-template-columns:1fr auto;column-gap:12px;row-gap:3px;
padding:11px 0;border-bottom:1px solid var(--rule)}table.cols td{border:0;padding:0}
table.cols td.c{grid-row:1;grid-column:1}table.cols td.n{grid-row:1;grid-column:2}
table.cols td.h,table.cols td.x{grid-column:1/-1}}
@media print{:root{--bg:#fff;--fg:#000;--muted:#444;--rule:#ccc;--ink:#1b2f7a;--mark:#ffe36e;--mark-fg:#000}
main{padding:0;max-width:none}.top a{display:none}tr{break-inside:avoid}}
"""


def _md_bold_to_mark(s: str, e) -> str:
    parts = s.split("**")
    return "".join(f"<mark>{e(p)}</mark>" if i % 2 else e(p) for i, p in enumerate(parts))


def to_html(r: ScanResult, home_url: str | None = None) -> str:
    d = to_dict(r)
    e = html.escape
    P = ["<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
         "<meta name='viewport' content='width=device-width,initial-scale=1'>",
         "<title>Personal data map</title>", f"<style>{_CSS}</style></head><body><main>"]
    home = f"<a href='{e(home_url)}'>swatva.org</a>" if home_url else f"version {e(d['version'])}"
    P.append(f"<div class='top'><span class='serif'>Swatva</span><span>{home}</span></div>")
    P.append("<h1>Personal data map</h1>")
    P.append(f"<p class='meta'>{e(_files_phrase(d))}. Scanned on {e(_nice_date(d['scanned_at']))} "
             f"with Swatva {e(d['version'])}, reading up to {d['sample_rows_per_table']:,} rows from each table.</p>")
    P.append("<div class='lead'>" + "".join(f"<p>{_md_bold_to_mark(s, e)}</p>" for s in _summary_sentences(d)) + "</div>")

    kinds = _kinds(d)
    if kinds:
        P.append("<h2>What was found</h2><div class='wrap'><table class='kinds'><thead><tr><th>Personal data</th>"
                 "<th class='n'>Columns</th><th>Found in</th><th>What to do</th></tr></thead><tbody>")
        for k in kinds:
            label = f"<span class='sens'>{e(k['label'])}</span>" if k["sensitive"] else e(k["label"])
            P.append(f"<tr><td>{label}</td><td class='n'>{k['columns']}</td>"
                     f"<td class='where'>{e(', '.join(k['where']))}</td><td class='todo'>{e(k['note'])}</td></tr>")
        P.append("</tbody></table></div>")

    P.append("<h2>Table by table</h2>")
    for t in d["tables"]:
        file, table = _table_name(t)
        sub = f" <span class='sub'>/ {e(table)}</span>" if table else ""
        meta = f"{_plural(t['rows'], 'row')}, {_plural(t['columns'], 'column')}."
        if t["sensitive"]:
            meta += " <span class='sens'>Holds sensitive data.</span>"
        P.append(f"<section class='t'><h3>{e(file)}{sub}</h3><p class='tmeta'>{meta}</p>")
        if not t["findings"]:
            P.append("<p class='none'>No personal data found.</p></section>")
            continue
        P.append("<div class='wrap'><table class='cols'><thead><tr><th>Column</th><th>Holds</th><th class='n'>Found in sample</th>"
                 "<th>Example (masked)</th></tr></thead><tbody>")
        for f in t["findings"]:
            also = (f"<span class='small'>plus {e(', '.join(f['also_in_text']))} in the text</span>"
                    if f["also_in_text"] else "")
            minors = f"<span class='small'>{f['minors']} under 18</span>" if f["minors"] else ""
            conf = (f"<span class='small'>{e(f['confidence'])} confidence</span>"
                    if f["confidence"] != "high" else "")
            P.append(f"<tr><td class='c'><code class='col'>{e(f['column'])}</code></td><td class='h'>{e(f['label'])}{also}{conf}</td>"
                     f"<td class='n'>{f['matched']:,} of {f['sampled']:,}{minors}</td>"
                     f"<td class='x'><code class='ex'>{e(f['example'])}</code></td></tr>")
        P.append("</tbody></table></div>")
        if t["clean_columns"]:
            P.append("<p class='clean'>No personal data in " +
                     ", ".join(f"<code>{e(c)}</code>" for c in t["clean_columns"]) + ".</p>")
        P.append("</section>")
    if d["errors"]:
        P.append("<h2>Files that could not be read</h2><ul class='errors'>")
        P += [f"<li>{e(os.path.basename(x['file']))}: {e(x['error'])}</li>" for x in d["errors"]]
        P.append("</ul>")
    P.append(f"<footer>{e(DISCLAIMER)}</footer></main></body></html>")
    return "".join(P)


def write_reports(r: ScanResult, out_dir: str, formats: list[str]) -> list[Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    if "md" in formats:
        p = out / "swatva-report.md"
        p.write_text(to_markdown(r), encoding="utf-8")
        written.append(p)
    if "html" in formats:
        p = out / "swatva-report.html"
        p.write_text(to_html(r), encoding="utf-8")
        written.append(p)
    if "json" in formats:
        p = out / "swatva-report.json"
        p.write_text(json.dumps(to_dict(r), indent=2, ensure_ascii=False), encoding="utf-8")
        written.append(p)
    return written
