#!/usr/bin/env python3
"""Conservative parser for an official NSE participant-wise OI CSV.

This script intentionally does not scrape undocumented NSE endpoints. Because report
schemas vary, it recognizes common headings and fails with a helpful error when mapping
is ambiguous. Review the source file and output before using the figures.
"""
import argparse, csv, json, re
from datetime import datetime, timezone
from pathlib import Path

ALIASES = {
    "participant": ["client type", "participant", "category", "clienttype"],
    "future_index_long": ["future index long", "futidxlong", "futures index long", "index futures long"],
    "future_index_short": ["future index short", "futidxshort", "futures index short", "index futures short"],
}

def norm(s):
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())

def find_col(headers, aliases):
    norm_headers = {norm(h): h for h in headers}
    for alias in aliases:
        a = norm(alias)
        for nh, original in norm_headers.items():
            if a == nh or a in nh:
                return original
    return None

def num(v):
    v = (v or "").strip().replace(",", "")
    if v in ("", "-", "NA", "N/A"):
        return None
    try:
        return float(v)
    except ValueError:
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Official participant-wise OI CSV")
    ap.add_argument("--output", default="data/processed")
    ap.add_argument("--report-date", help="YYYY-MM-DD; defaults to today's UTC date")
    args = ap.parse_args()
    src = Path(args.input)
    if not src.exists():
        raise SystemExit(f"Input file not found: {src}")
    # utf-8-sig handles Excel-exported BOM; fall back to latin-1 for legacy exports.
    try:
        f = src.open("r", encoding="utf-8-sig", newline="")
        sample = f.read(4096); f.seek(0)
    except UnicodeDecodeError:
        f = src.open("r", encoding="latin-1", newline="")
        sample = f.read(4096); f.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    rows = list(csv.DictReader(f, dialect=dialect)); f.close()
    if not rows:
        raise SystemExit("CSV has no data rows; refusing to create a report.")
    headers = list(rows[0].keys())
    cols = {k: find_col(headers, aliases) for k, aliases in ALIASES.items()}
    missing = [k for k, v in cols.items() if not v]
    if missing:
        raise SystemExit("Could not safely map required columns: " + ", ".join(missing) + "\nDetected headers: " + repr(headers) + "\nUpdate ALIASES only after inspecting the official report.")
    results = {}
    for row in rows:
        name = (row.get(cols["participant"]) or "").strip().upper()
        if not name:
            continue
        long = num(row.get(cols["future_index_long"]))
        short = num(row.get(cols["future_index_short"]))
        if long is None or short is None:
            continue
        results[name] = {"index_futures_long": long, "index_futures_short": short, "net_long_minus_short": long-short}
    if not results:
        raise SystemExit("No participant rows matched numeric index-futures long/short values; refusing to guess columns.")
    outdir = Path(args.output); outdir.mkdir(parents=True, exist_ok=True)
    report_date = args.report_date or datetime.now(timezone.utc).date().isoformat()
    payload = {"report_date": report_date, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "source_file": src.name, "source_type": "user-supplied official NSE CSV", "validated": False, "validation_note": "Review headers, report date, units, and participant names before use.", "participants": results}
    out = outdir / f"participant_oi_{report_date}.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
