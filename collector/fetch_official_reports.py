#!/usr/bin/env python3
"""Download only CSVs linked directly from official NSE report pages.

No undocumented API endpoints, browser impersonation beyond a normal public-page request,
or access-control bypasses are used. If NSE renders download controls client-side or blocks
automated access, the script records that limitation and exits cleanly.
"""
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

OUT = Path("data/official")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NSE-Public-Report-Collector/1.0)",
    "Accept": "text/html,application/xhtml+xml,text/csv,*/*",
}
PAGES = [
    {
        "key": "fii_dii",
        "url": "https://www.nseindia.com/reports/fii-dii",
        "keywords": ("fii", "dii", "download"),
    },
    {
        "key": "participant_oi",
        "url": "https://www.nseindia.com/all-reports-derivatives",
        "keywords": ("participant", "open interest"),
    },
]

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self._href = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            self.links.append((self._href, " ".join(" ".join(self._text).split())))
            self._href = None
            self._text = []

def get(url):
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=25) as response:
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(f"HTTP {response.status}")
        return response.read(5_000_000), response.headers.get("Content-Type", "")

def find_csv_link(page_url, html, keywords):
    parser = LinkParser()
    parser.feed(html.decode("utf-8", errors="replace"))
    candidates = []
    for href, label in parser.links:
        full = urllib.parse.urljoin(page_url, href)
        haystack = (label + " " + full).lower()
        is_csv = ".csv" in urllib.parse.urlparse(full).path.lower() or "csv" in haystack
        matches = sum(1 for word in keywords if word in haystack)
        if is_csv and matches:
            candidates.append((matches, full, label))
    candidates.sort(reverse=True)
    return candidates[0][1:] if candidates else None

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Fetch publicly linked official NSE CSV reports where direct links are present.",
        "trading_recommendations": False,
        "sources": [],
    }
    for item in PAGES:
        entry = {"name": item["key"], "page_url": item["url"], "downloaded": False}
        try:
            page_bytes, content_type = get(item["url"])
            entry["page_reachable"] = True
            entry["page_content_type"] = content_type
            link = find_csv_link(item["url"], page_bytes, item["keywords"])
            if not link:
                entry["note"] = "No matching direct CSV link was present in the public HTML. No hidden API or access control was bypassed."
            else:
                file_url, label = link
                data, file_type = get(file_url)
                # Reject HTML error pages masquerading as CSV.
                prefix = data[:500].lstrip().lower()
                if "text/html" in file_type.lower() or prefix.startswith(b"<!doctype html") or prefix.startswith(b"<html"):
                    entry["note"] = "The linked download returned HTML rather than a CSV; file was not saved."
                else:
                    suffix = ".csv" if ".csv" in urllib.parse.urlparse(file_url).path.lower() else ".dat"
                    path = OUT / f"{item['key']}{suffix}"
                    path.write_bytes(data)
                    entry.update({
                        "downloaded": True,
                        "file": str(path),
                        "bytes": len(data),
                        "content_type": file_type,
                        "download_url": file_url,
                        "link_label": label,
                        "note": "Downloaded from a direct link on the official NSE page; schema and report date still require validation.",
                    })
        except Exception as exc:
            entry["page_reachable"] = False
            entry["note"] = f"Collection unavailable: {type(exc).__name__}: {exc}"
        report["sources"].append(entry)
    report_path = OUT / "collection_status.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
