#!/usr/bin/env python3
"""Fail visibly when the scheduled job has no usable official data."""
import json
from pathlib import Path

PROCESSED = Path("data/processed")
OFFICIAL = Path("data/official")

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
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(f"FII/DII status JSON cannot be read: {exc}")

    participant_path = official / "collection_status.json"
    if not participant_path.exists():
        issues.append("Official report collection status is missing.")
    else:
        try:
            status = json.loads(participant_path.read_text(encoding="utf-8"))
            sources = {item.get("name"): item for item in status.get("sources", [])}
            item = sources.get("participant_oi", {})
            if not item.get("downloaded"):
                issues.append("Participant-wise OI CSV was not downloaded.")
            elif not item.get("file") or not Path(item["file"]).exists():
                issues.append("Participant-wise OI file is missing despite download status.")
            else:
                issues.append("Participant-wise OI file exists but schema validation is not implemented; do not treat it as verified.")
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(f"Official collection status cannot be read: {exc}")
    return issues

def main():
    issues = inspect()
    result = {
        "status": "needs_attention" if issues else "ready_for_review",
        "validated_for_research": False,
        "issues": issues,
        "note": "A successful script run is not proof of valid data. Confirm report date, schema, and source before research use.",
    }
    print(json.dumps(result, indent=2))
    if issues:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
