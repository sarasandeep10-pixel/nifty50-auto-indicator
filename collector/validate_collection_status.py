#!/usr/bin/env python3
"""Validate collected NSE report files; page reachability alone is never enough."""
import csv
import json
import re
from pathlib import Path

PROCESSED = Path("data/processed")
OFFICIAL = Path("data/official")

def norm(value):
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())

def validate_participant_csv(path):
    """Return a diagnostic string or None when required participant OI fields are usable."""
    if not path.exists():
        return "Participant-wise OI file is missing."
    if path.suffix.lower() != ".csv":
        return f"Participant-wise OI file is {path.suffix or 'extensionless'}, not a CSV; archive extraction/schema validation is not implemented."
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            sample = stream.read(4096)
            stream.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            except csv.Error:
                dialect = csv.excel
            rows = list(csv.DictReader(stream, dialect=dialect))
    except (OSError, UnicodeError, csv.Error) as exc:
        return f"Participant-wise OI CSV could not be read: {exc}"
    if not rows:
        return "Participant-wise OI CSV has no data rows."
    headers = list(rows[0].keys())
    normalized = {norm(h): h for h in headers if h}
    def find(aliases):
        for alias in aliases:
            key = norm(alias)
            for normalized_header, original in normalized.items():
                if normalized_header == key or key in normalized_header:
                    return original
        return None
    participant = find(["client type", "participant", "category", "clienttype"])
    long_col = find(["future index long", "futidxlong", "futures index long", "index futures long"])
    short_col = find(["future index short", "futidxshort", "futures index short", "index futures short"])
    missing = [name for name, col in (("participant", participant), ("future index long", long_col), ("future index short", short_col)) if col is None]
    if missing:
        return "Participant-wise OI CSV is missing required columns: " + ", ".join(missing) + f". Headers found: {headers!r}"
    usable = 0
    for row in rows:
        name = (row.get(participant) or "").strip()
        try:
            long_value = float((row.get(long_col) or "").replace(",", "").strip())
            short_value = float((row.get(short_col) or "").replace(",", "").strip())
        except (TypeError, ValueError):
            continue
        if name and long_value >= 0 and short_value >= 0:
            usable += 1
    if not usable:
        return "Participant-wise OI CSV has no rows with participant names and numeric long/short values."
    return None

def inspect(processed=PROCESSED, official=OFFICIAL):
    issues = []
    fii_path = processed / "fii_dii_latest.json"
    if not fii_path.exists():
        issues.append("FII/DII status JSON is missing.")
    else:
        try:
            report = json.loads(fii_path.read_text(encoding="utf-8"))
            rows = report.get("rows", [])
            if not report.get("validated") or not rows:
                issues.append("FII/DII report has no validated data rows.")
            if any(not row.get("net_matches_buy_minus_sell", False) for row in rows):
                issues.append("At least one FII/DII row failed net = buy - sell validation.")
            if rows and any(not row.get("date") for row in rows):
                issues.append("At least one FII/DII row is missing its report date.")
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(f"FII/DII status JSON cannot be read: {exc}")

    candidates = []
    collection_path = official / "collection_status.json"
    if collection_path.exists():
        try:
            status = json.loads(collection_path.read_text(encoding="utf-8"))
            for item in status.get("sources", []):
                if item.get("name") == "participant_oi" and item.get("downloaded") and item.get("file"):
                    candidates.append(Path(item["file"]))
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(f"Official collection status cannot be read: {exc}")

    browser_status_path = official / "browser" / "browser_download_status.json"
    if browser_status_path.exists():
        try:
            browser_status = json.loads(browser_status_path.read_text(encoding="utf-8"))
            for item in browser_status.get("downloads", []):
                if item.get("report") == "participant_open_interest" and item.get("file"):
                    candidates.append(Path(item["file"]))
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(f"Browser download status cannot be read: {exc}")

    if not candidates:
        issues.append("Participant-wise OI report was not downloaded.")
    else:
        validated = False
        diagnostics = []
        for candidate in candidates:
            problem = validate_participant_csv(candidate)
            if problem is None:
                validated = True
                break
            diagnostics.append(problem)
        if not validated:
            issues.extend(diagnostics or ["Participant-wise OI report did not pass schema validation."])
    return issues

def main():
    issues = inspect()
    result = {
        "status": "needs_attention" if issues else "validated",
        "validated_for_research": not issues,
        "issues": issues,
        "note": "Validation checks file presence, required columns, usable rows, report dates, and FII/DII arithmetic. Confirm source context and report freshness before analysis.",
    }
    print(json.dumps(result, indent=2))
    if issues:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
