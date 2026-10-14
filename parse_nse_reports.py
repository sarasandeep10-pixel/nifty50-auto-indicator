
#!/usr/bin/env python3
"""
Conservative parser for an NSE participant-wise open-interest CSV.

Reads a user-provided CSV, identifies participant and index-futures
long/short columns, and writes a dated JSON report.

This script does not download NSE data or predict market direction.
Always verify source, date, headers, units, and output before use.
"""

import argparse
import csv
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path


ALIASES = {
    "participant": [
        "client type",
        "participant",
        "participant type",
        "category",
        "clienttype",
    ],
    "future_index_long": [
        "future index long",
        "futidxlong",
        "futures index long",
        "index futures long",
    ],
    "future_index_short": [
        "future index short",
        "futidxshort",
        "futures index short",
        "index futures short",
    ],
}


def normalize(value):
    """Normalize a heading for comparison."""
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def find_column(headers, aliases):
    """Find a column only when a heading matches an approved alias."""
    normalized_headers = {
        normalize(header): header
        for header in headers
        if header is not None
    }

    for alias in aliases:
        key = normalize(alias)
        if key in normalized_headers:
            return normalized_headers[key]

    return None


def parse_number(value):
    """Parse a numeric CSV cell, returning None for missing values."""
    if value is None:
        return None

    value = value.strip().replace(",", "")

    if value.upper() in {"", "-", "NA", "N/A", "NULL"}:
        return None

    try:
        return float(value)
    except ValueError:
        return None


def read_csv_rows(path):
    """Read a CSV while handling common encodings and delimiters."""
    last_error = None

    for encoding in ("utf-8-sig", "latin-1"):
        try:
            with path.open(
                "r", encoding=encoding, newline=""
            ) as file:
                sample = file.read(8192)
                file.seek(0)

                try:
                    dialect = csv.Sniffer().sniff(
                        sample, delimiters=",;\t|"
                    )
                except csv.Error:
                    dialect = csv.excel

                reader = csv.DictReader(file, dialect=dialect)
                rows = list(reader)
                headers = reader.fieldnames or []

            return headers, rows

        except (OSError, UnicodeError, csv.Error) as exc:
            last_error = exc

    raise SystemExit(f"Could not read CSV: {last_error}")


def main():
    parser = argparse.ArgumentParser(
        description="Parse an NSE participant-wise OI CSV."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to a participant-wise OI CSV file",
    )
    parser.add_argument(
        "--output",
        default="data/processed",
        help="Output directory (default: data/processed)",
    )
    parser.add_argument(
        "--report-date",
        default=date.today().isoformat(),
        help="Report date in YYYY-MM-DD format",
    )
    args = parser.parse_args()

    try:
        datetime.strptime(args.report_date, "%Y-%m-%d")
    except ValueError:
        raise SystemExit("Invalid --report-date; use YYYY-MM-DD.")

    source = Path(args.input)

    if not source.is_file():
        raise SystemExit(f"Input CSV not found: {source}")

    headers, rows = read_csv_rows(source)

    if not headers or not rows:
        raise SystemExit("CSV has no headers or data rows.")

    columns = {
        name: find_column(headers, aliases)
        for name, aliases in ALIASES.items()
    }

    missing = [
        name for name, column in columns.items()
        if column is None
    ]

    if missing:
        raise SystemExit(
            "Could not identify required columns: "
            + ", ".join(missing)
            + "\nDetected headers: "
            + repr(headers)
            + "\nInspect the source CSV before updating ALIASES."
        )

    participants = {}

    for row in rows:
        name = (row.get(columns["participant"]) or "").strip().upper()

        if not name:
            continue

        long_value = parse_number(
            row.get(columns["future_index_long"])
        )
        short_value = parse_number(
            row.get(columns["future_index_short"])
        )

        if long_value is None or short_value is None:
            continue

        participants[name] = {
            "index_futures_long": long_value,
            "index_futures_short": short_value,
            "net_long_minus_short": long_value - short_value,
        }

    if not participants:
        raise SystemExit(
            "No participant rows with valid index-futures "
            "long and short values were found."
        )

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(timezone.utc).isoformat()

    report = {
        "report_date": args.report_date,
        "generated_at_utc": generated_at,
        "source_file": source.name,
        "source_verified_official": False,
        "validated": False,
        "validation_note": (
            "Verify the official source, report date, units, "
            "headers, and participant names before relying on figures."
        ),
        "calculation": "net_long_minus_short = long - short",
        "participants": participants,
    }

    output_file = (
        output_dir / f"participant_oi_{args.report_date}.json"
    )
    output_file.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(f"Report written to: {output_file}")
    print(f"Participants parsed: {len(participants)}")
    print("Source verified: No; manual verification is required.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("Cancelled.")
