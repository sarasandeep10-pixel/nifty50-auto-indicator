#!/usr/bin/env python3
"""Fetch institutional cash-flow data from Upstox's documented Market Information API.

Requires UPSTOX_ACCESS_TOKEN in the environment. This is a separate source adapter:
it does not claim to provide NSE participant-wise Client/Pro/FII/DII open interest.
Amounts returned by the API are INR and are normalized to INR crore.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = "https://api.upstox.com/v2/market"
OUT = Path("data/processed")
IST = ZoneInfo("Asia/Kolkata")
SEGMENTS = [
    "NSE_EQ|CASH",
    "NSE_FO|INDEX_FUTURES",
    "NSE_FO|STOCK_FUTURES",
    "NSE_FO|INDEX_OPTIONS",
    "NSE_FO|STOCK_OPTIONS",
]

def fetch(endpoint, params, token):
    query = urllib.parse.urlencode(params, doseq=True, safe="|")
    request = urllib.request.Request(
        f"{BASE}/{endpoint}?{query}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "nifty50-market-data-learning/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            if response.status != 200:
                raise RuntimeError(f"Upstox {endpoint} returned HTTP {response.status}")
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read(1000).decode("utf-8", errors="replace")
        raise RuntimeError(f"Upstox {endpoint} HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Upstox {endpoint} request failed: {exc}") from exc
    if payload.get("status") != "success" or not isinstance(payload.get("data"), dict):
        raise RuntimeError(f"Upstox {endpoint} response is not a successful data payload")
    return payload["data"]

def normalize(endpoint, data):
    result = {}
    for segment, records in data.items():
        if not isinstance(records, list):
            raise RuntimeError(f"Unexpected records shape for {endpoint} {segment}")
        normalized = []
        for item in records:
            if not isinstance(item, dict) or not isinstance(item.get("time_stamp"), (int, float)):
                raise RuntimeError(f"Missing timestamp in {endpoint} {segment} record")
            if not isinstance(item.get("buy_amount"), (int, float)) or not isinstance(item.get("sell_amount"), (int, float)):
                raise RuntimeError(f"Missing numeric buy/sell amounts in {endpoint} {segment} record")
            date = datetime.fromtimestamp(item["time_stamp"] / 1000, tz=timezone.utc).astimezone(IST).date().isoformat()
            buy_cr = round(item["buy_amount"] / 10_000_000, 4)
            sell_cr = round(item["sell_amount"] / 10_000_000, 4)
            row = {
                "date": date,
                "buy_crore": buy_cr,
                "sell_crore": sell_cr,
                "net_crore_calculated": round(buy_cr - sell_cr, 4),
                "source": "upstox_documented_api",
                "source_segment": segment,
            }
            for field in ("buy_contracts", "sell_contracts", "oi_contracts", "oi_amount",
                          "total_long_contracts", "total_short_contracts",
                          "total_call_long_contracts", "total_put_long_contracts",
                          "total_call_short_contracts", "total_put_short_contracts"):
                if field in item:
                    row[field] = item[field]
            normalized.append(row)
        result[segment] = normalized
    return result

def main():
    token = os.environ.get("UPSTOX_ACCESS_TOKEN", "").strip()
    if not token:
        print("UPSTOX_ACCESS_TOKEN is not set; refusing to make an unauthenticated request.", file=sys.stderr)
        return 2
    params = [("data_type", segment) for segment in SEGMENTS] + [("interval", "1D")]
    try:
        fii = normalize("fii", fetch("fii", params, token))
        dii = normalize("dii", fetch("dii", [("data_type", "NSE_EQ|CASH"), ("interval", "1D")], token))
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if not fii or not dii or not fii.get("NSE_EQ|CASH") or not dii.get("NSE_EQ|CASH"):
        print("Upstox returned no FII/DII cash rows; output not written.", file=sys.stderr)
        return 1
    # Validate arithmetic, plausible date fields, and prevent empty/placeholder snapshots.
    for dataset in (fii, dii):
        for rows in dataset.values():
            for row in rows:
                if not row.get("date") or abs(row["net_crore_calculated"]) > 1_000_000:
                    print("Upstox response failed basic row validation; output not written.", file=sys.stderr)
                    return 1
    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Upstox documented Market Information API",
        "source_urls": [
            "https://upstox.com/developer/api-documentation/get-fii-data/",
            "https://upstox.com/developer/api-documentation/get-dii-data/",
        ],
        "validated": True,
        "validation_note": "Schema, timestamps, numeric buy/sell values, and calculated net arithmetic checked. Cross-source verification is still recommended.",
        "amount_unit": "INR crore (API INR amounts divided by 10,000,000)",
        "coverage_limit": "This API provides FII/DII activity. It does not provide participant-wise Client/Pro/FII/DII OI categories.",
        "fii": fii,
        "dii": dii,
    }
    path = OUT / "upstox_institutional_activity.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"status": "success", "output": str(path), "fii_cash_rows": len(fii["NSE_EQ|CASH"]), "dii_cash_rows": len(dii["NSE_EQ|CASH"]), "participant_wise_oi_included": False}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
