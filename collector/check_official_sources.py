#!/usr/bin/env python3
"""Create a neutral, auditable NSE source-status report.

This deliberately reports source availability only. It does not infer market direction,
produce trade recommendations, or treat a web page's availability as proof that its data
has been downloaded or validated.
"""
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SOURCES = [
    {
        "name": "NSE derivatives daily reports",
        "url": "https://www.nseindia.com/all-reports-derivatives",
        "purpose": "Official page for participant-wise open interest and FII derivatives statistics",
    },
    {
        "name": "NSE FII/FPI and DII activity",
        "url": "https://www.nseindia.com/reports/fii-dii",
        "purpose": "Official page for provisional cash-market FII/FPI and DII activity",
    },
]

def check_source(source):
    req = urllib.request.Request(
        source["url"],
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; NSE-Data-Status-Checker/1.0)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            status = response.status
            content_type = response.headers.get("Content-Type", "")
            body = response.read(200_000)
        # Do not parse/guess data from HTML. Only report whether the official page responds.
        return {
            **source,
            "http_status": status,
            "reachable": 200 <= status < 300,
            "content_type": content_type,
            "bytes_sampled": len(body),
            "data_downloaded": False,
            "data_validated": False,
            "note": "Page availability only; report files must be downloaded and schema-validated separately.",
        }
    except Exception as exc:
        return {
            **source,
            "http_status": None,
            "reachable": False,
            "content_type": None,
            "bytes_sampled": 0,
            "data_downloaded": False,
            "data_validated": False,
            "note": f"Source check failed: {type(exc).__name__}: {exc}",
        }

def main():
    out = Path("data/processed")
    out.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "report_type": "official_source_status",
        "interpretation": "This is a connectivity check, not market analysis or a trading signal.",
        "sources": [check_source(source) for source in SOURCES],
    }
    path = out / "official_source_status.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    # Network restrictions or temporary NSE blocks should be visible, but should not make
    # code-quality CI fail. The workflow artifact preserves the details for inspection.

if __name__ == "__main__":
    main()
