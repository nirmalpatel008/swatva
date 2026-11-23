"""Turns a scan into a personal-data map: Markdown, HTML and JSON."""

from __future__ import annotations

import html
import json
import os
from pathlib import Path

from . import __version__
from .detectors import DETECTORS_BY_ID
from .scanner import ScanResult, TableResult, label_for

DISCLAIMER = (
    "This report shows where personal data appears to be stored, based on a sample of rows. "
    "It is a starting point for DPDP Act preparation, not legal advice, and it can miss data "
    "or flag columns that are not personal. Values are masked: the report never shows full identifiers."
)

GROUP_ORDER = ["identity", "financial", "sensitive", "contact", "personal"]


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
                "label": "Free text containing " + ", ".join(labels),
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


def to_markdown(r: ScanResult) -> str:
    d = to_dict(r)
    s = d["summary"]
    L = []
    L.append("# Swatva personal data map")
    L.append("")
    L.append(f"Scanned {d['scanned_at'].replace('T', ' ')} with Swatva {d['version']}. "
             f"Up to {d['sample_rows_per_table']} rows sampled per table.")
    L.append("")
    L.append("## Summary")
    L.append("")
    L.append(f"- **{s['tables_with_personal_data']} of {s['tables']}** tables hold personal data, "
             f"across {s['files']} file(s).")
    L.append(f"- **{s['columns_with_personal_data']} of {s['columns']}** columns contain personal data.")
    L.append(f"- **{s['rows_in_tables_with_personal_data']:,}** rows sit in tables with personal data.")
    L.append(f"- **{s['tables_with_sensitive_data']}** table(s) hold sensitive data "
             "(Aadhaar, bank details, caste or category, income, or disability).")
    if s["minors_in_sample"]:
        L.append(f"- **{s['minors_in_sample']}** record(s) in the sample belong to people under 18. "
                 "These need verifiable parental consent under DPDP.")
    L.append("")
    L.append("## What was found")
    L.append("")
    L.append("| Type of personal data | Columns |")
    L.append("|---|---|")
    for k, v in sorted(d["types_found"].items(), key=lambda kv: -kv[1]["columns"]):
        L.append(f"| {v['label']} | {v['columns']} |")
    L.append("")
    L.append("## Table by table")
    for t in d["tables"]:
        L.append("")
        name = os.path.basename(t["source"]) + ("" if t["kind"] == "csv" else f" : {t['name']}")
        flag = " (sensitive)" if t["sensitive"] else ""
        L.append(f"### {name}{flag}")
        L.append("")
        L.append(f"{t['rows']:,} rows, {t['columns']} columns.")
        if not t["findings"]:
            L.append("")
            L.append("No personal data found.")
            continue
        L.append("")
        L.append("| Column | Holds | Confidence | Matched in sample | Example (masked) |")
        L.append("|---|---|---|---|---|")
        for f in t["findings"]:
            extra = f" (also: {', '.join(f['also_in_text'])})" if f["also_in_text"] else ""
            minors = f", {f['minors']} under 18" if f["minors"] else ""
            L.append(f"| `{f['column']}` | {f['label']}{extra} | {f['confidence']} | "
                     f"{f['matched']}/{f['sampled']} ({_pct(f['matched'], f['sampled'])}){minors} | {f['example']} |")
        notes = []
        for f in t["findings"]:
            if f["note"] not in notes:
                notes.append(f["note"])
        L.append("")
        for n in notes:
            L.append(f"- {n}")
        if t["clean_columns"]:
            L.append("")
            L.append("No personal data in: " + ", ".join(f"`{c}`" for c in t["clean_columns"]))
    if d["errors"]:
        L.append("")
        L.append("## Files that could not be read")
        L.append("")
        for e in d["errors"]:
            L.append(f"- {e['file']}: {e['error']}")
    L.append("")
    L.append("---")
    L.append("")
    L.append(f"_{DISCLAIMER}_")
    L.append("")
    return "\n".join(L)


_CSS = """
:root{--bg:#fbfaf7;--fg:#1d1d1b;--muted:#6b6a65;--line:#e4e1d9;--card:#ffffff;--accent:#1f5f5b;
--warn-bg:#fdf1e7;--warn:#9a4a12;--ok:#2f6b3a;--chip:#eef3f2}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--fg:#ecebe6;--muted:#a3a19a;--line:#33322f;
--card:#1e1e1c;--accent:#7cc4bd;--warn-bg:#3a2516;--warn:#f2b183;--ok:#8fd19c;--chip:#23302f}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1040px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:28px;margin:0 0 4px}h2{font-size:19px;margin:36px 0 12px}h3{font-size:16px;margin:0}
.meta{color:var(--muted);margin:0 0 24px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}
.stat b{display:block;font-size:24px;font-variant-numeric:tabular-nums}.stat span{color:var(--muted);font-size:13px}
.stat.warn{background:var(--warn-bg);border-color:transparent}.stat.warn b{color:var(--warn)}
.chips{display:flex;flex-wrap:wrap;gap:8px}.chip{background:var(--chip);border-radius:999px;padding:4px 12px;font-size:13px}
.table{background:var(--card);border:1px solid var(--line);border-radius:10px;margin:14px 0;overflow:hidden}
.thead{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;padding:12px 14px;border-bottom:1px solid var(--line)}
.thead small{color:var(--muted)}.tag{font-size:12px;padding:2px 8px;border-radius:6px;background:var(--warn-bg);color:var(--warn);margin-left:8px}
.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;padding:8px 14px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-weight:500;font-size:12px;text-transform:uppercase;letter-spacing:.03em}
td code,.clean code{font-size:13px}.num{font-variant-numeric:tabular-nums;white-space:nowrap}
.notes{margin:0;padding:10px 14px 12px 32px;color:var(--muted);font-size:13px}
.clean{padding:10px 14px;color:var(--muted);font-size:13px;border-top:1px solid var(--line)}
.none{padding:12px 14px;color:var(--ok)}
.disc{margin-top:40px;color:var(--muted);font-size:13px;border-top:1px solid var(--line);padding-top:16px}
"""


def to_html(r: ScanResult) -> str:
    d = to_dict(r)
    s = d["summary"]
    e = html.escape
    P = []
    P.append("<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>")
    P.append("<meta name='viewport' content='width=device-width,initial-scale=1'>")
    P.append("<title>Swatva personal data map</title>")
    P.append(f"<style>{_CSS}</style></head><body><main>")
    P.append("<h1>Personal data map</h1>")
    P.append(f"<p class='meta'>Scanned {e(d['scanned_at'].replace('T', ' '))} with Swatva {e(d['version'])}. "
             f"Up to {d['sample_rows_per_table']} rows sampled per table.</p>")
    P.append("<div class='stats'>")
    P.append(f"<div class='stat'><b>{s['tables_with_personal_data']}/{s['tables']}</b><span>tables hold personal data</span></div>")
    P.append(f"<div class='stat'><b>{s['columns_with_personal_data']}/{s['columns']}</b><span>columns hold personal data</span></div>")
    P.append(f"<div class='stat'><b>{s['rows_in_tables_with_personal_data']:,}</b><span>rows in those tables</span></div>")
    P.append(f"<div class='stat warn'><b>{s['tables_with_sensitive_data']}</b><span>tables with sensitive data</span></div>")
    if s["minors_in_sample"]:
        P.append(f"<div class='stat warn'><b>{s['minors_in_sample']}</b><span>records of people under 18</span></div>")
    P.append("</div>")
    P.append("<h2>What was found</h2><div class='chips'>")
    for k, v in sorted(d["types_found"].items(), key=lambda kv: -kv[1]["columns"]):
        P.append(f"<span class='chip'>{e(v['label'])} &middot; {v['columns']}</span>")
    P.append("</div><h2>Table by table</h2>")
    for t in d["tables"]:
        name = os.path.basename(t["source"]) + ("" if t["kind"] == "csv" else f" : {t['name']}")
        tag = "<span class='tag'>sensitive</span>" if t["sensitive"] else ""
        P.append("<section class='table'><div class='thead'>")
        P.append(f"<h3>{e(name)}{tag}</h3><small>{t['rows']:,} rows &middot; {t['columns']} columns</small></div>")
        if not t["findings"]:
            P.append("<div class='none'>No personal data found.</div></section>")
            continue
        P.append("<div class='scroll'><table><thead><tr><th>Column</th><th>Holds</th><th>Confidence</th>"
                 "<th>Matched</th><th>Example (masked)</th></tr></thead><tbody>")
        for f in t["findings"]:
            extra = f" <small>(also: {e(', '.join(f['also_in_text']))})</small>" if f["also_in_text"] else ""
            minors = f"<br><small>{f['minors']} under 18</small>" if f["minors"] else ""
            P.append(f"<tr><td><code>{e(f['column'])}</code></td><td>{e(f['label'])}{extra}</td>"
                     f"<td>{e(f['confidence'])}</td><td class='num'>{f['matched']}/{f['sampled']} "
                     f"({_pct(f['matched'], f['sampled'])}){minors}</td><td><code>{e(f['example'])}</code></td></tr>")
        P.append("</tbody></table></div><ul class='notes'>")
        seen = []
        for f in t["findings"]:
            if f["note"] not in seen:
                seen.append(f["note"])
                P.append(f"<li>{e(f['note'])}</li>")
        P.append("</ul>")
        if t["clean_columns"]:
            P.append("<div class='clean'>No personal data in: " +
                     ", ".join(f"<code>{e(c)}</code>" for c in t["clean_columns"]) + "</div>")
        P.append("</section>")
    if d["errors"]:
        P.append("<h2>Files that could not be read</h2><ul>")
        for er in d["errors"]:
            P.append(f"<li>{e(er['file'])}: {e(er['error'])}</li>")
        P.append("</ul>")
    P.append(f"<p class='disc'>{e(DISCLAIMER)}</p></main></body></html>")
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
