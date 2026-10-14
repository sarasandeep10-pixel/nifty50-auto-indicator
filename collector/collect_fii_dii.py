#!/usr/bin/env python3
"""Fetch and normalize visible FII/DII tables from NSE's public report page.

Only server-rendered, publicly accessible HTML is read. The script does not call private or
undocumented endpoints. It stores raw-source metadata alongside parsed rows and refuses to
mark data validated unless dates, participant labels, and numeric columns are present.
"""
import csv
import json
import re
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

URL = "https://www.nseindia.com/reports/fii-dii"
OUT = Path("data/processed")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NSE-Public-Data-Learning/1.0)",
    "Accept": "text/html,application/xhtml+xml",
}

def clean(s):
    return re.sub(r"\s+", " ", (s or "").replace("\xa0", " ")).strip()

def number(s):
    s = clean(s).replace(",", "").replace("₹", "").strip()
    if s in ("", "-", "—", "NA", "N/A"):
        return None
    try:
        return float(s)
    except ValueError:
        return None

class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.table = None
        self.row = None
        self.cell = None
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "table":
            self.table = []
        elif self.table is not None and tag == "tr":
            self.row = []
        elif self.table is not None and tag in ("td", "th"):
            self.cell = []
    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)
    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(clean(" ".join(self.cell)))
            self.cell = None
        elif tag == "tr" and self.row is not None and self.table is not None:
            if any(self.row):
                self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.table is not None:
            if self.table:
                self.tables.append(self.table)
            self.table = None

def parse_page(html):
    parser = TableParser()
    parser.feed(html)
    parsed = []
    rejected = []
    for ti, table in enumerate(parser.tables):
        header_index = None
        for ri, row in enumerate(table):
            h = " ".join(row).lower()
            if ("category" in h and "date" in h and "buy" in h and "sell" in h and "net" in h):
                header_index = ri
                break
        if header_index is None:
            continue
        header = [re.sub(r"[^a-z]+", "", x.lower()) for x in table[header_index]]
        def col_index(*terms):
            for i, value in enumerate(header):
                if all(term in value for term in terms):
                    return i
            return None
        category_i = col_index("category")
        date_i = col_index("date")
        buy_i = next((i for i, x in enumerate(header) if "buy" in x and "value" in x), None)
        sell_i = next((i for i, x in enumerate(header) if "sell" in x and "value" in x), None)
        net_i = next((i for i, x in enumerate(header) if "net" in x and "value" in x), None)
        if None in (category_i, date_i, buy_i, sell_i, net_i):
            rejected.append({"table": ti, "reason": "required_headers_not_mapped", "headers": table[header_index]})
            continue
        for row in table[header_index + 1:]:
            if max(category_i, date_i, buy_i, sell_i, net_i) >= len(row):
                continue
            category = row[category_i].upper()
            if "FII" not in category and "DII" not in category:
                continue
            nums = [number(row[i]) for i in (buy_i, sell_i, net_i)]
            if not all(v is not None for v in nums):
                rejected.append({"table": ti, "row": row, "reason": "non_numeric_values"})
                continue
            buy, sell, net = nums
            calculated = round(buy - sell, 2)
            parsed.append({
                "category": "FII/FPI" if "FII" in category else "DII",
                "date": row[date_i],
                "buy_crore": buy,
                "sell_crore": sell,
                "net_crore_reported": net,
                "net_crore_calculated": calculated,
                "net_matches_buy_minus_sell": abs(net - calculated) <= 0.02,
                "source_table_index": ti,
            })
    unique = {}
    for row in parsed:
        key = (row["category"], row["date"], row["buy_crore"], row["sell_crore"], row["net_crore_reported"])
        unique[key] = row
    return list(unique.values()), rejected

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": URL,
        "source_type": "public NSE HTML report page",
        "purpose": "neutral market-data learning and historical review",
        "trading_recommendations": False,
        "downloaded_csv": False,
        "validated": False,
        "rows": [],
        "errors": [],
    }
    request = urllib.request.Request(URL, headers=HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            status = response.status
            body = response.read(5_000_000)
            content_type = response.headers.get("Content-Type", "")
        report["http_status"] = status
        report["content_type"] = content_type
        if status < 200 or status >= 300:
            raise RuntimeError(f"Unexpected HTTP status {status}")
        rows, rejected = parse_page(body.decode("utf-8", errors="replace"))
        report["rows"] = rows
        report["rejected_rows"] = rejected[:30]
        # Validation checks structure and arithmetic consistency; the figures are still
        # provisional as noted by NSE and are not investment guidance.
        report["validated"] = bool(rows) and all(r["net_matches_buy_minus_sell"] for r in rows)
        report["validation_note"] = (
            "Structure and arithmetic checked. NSE labels cash-market FII/FPI figures provisional; "
            "confirm report date and source before any research use."
        )
        if not rows:
            report["errors"].append("No recognizable FII/DII data rows found in public HTML.")
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = OUT / f"fii_dii_{stamp}.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    latest_path = OUT / "fii_dii_latest.json"
    latest_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if report["rows"]:
        with (OUT / "fii_dii_latest.csv").open("w", newline="", encoding="utf-8") as f:
            fields = list(report["rows"][0].keys())
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(report["rows"])
    print(json.dumps(report, indent=2))
    # Collection failure is recorded for inspection and should not hide the artifact.
if __name__ == "__main__":
    main()
