#!/usr/bin/env python3
"""Download NSE reports by interacting with the public report UI in a real browser.

This intentionally uses the visible official website controls rather than guessing API
endpoints. UI changes are recorded as diagnostics; no downloaded file is marked validated
until a separate parser checks its contents.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path("data/official/browser")
OUT.mkdir(parents=True, exist_ok=True)
STATUS = OUT / "browser_download_status.json"

def main():
    status = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": "Playwright interactions with public NSE report UI",
        "validated": False,
        "downloads": [],
        "errors": [],
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-http2"])
        page = browser.new_page(accept_downloads=True, ignore_https_errors=False, user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", extra_http_headers={"Accept-Language": "en-US,en;q=0.9"})
        try:
            page.goto("https://www.nseindia.com/reports/fii-dii", wait_until="commit", timeout=60000)
            page.wait_for_timeout(3000)
            status["fii_dii_page_title"] = page.title()
            status["fii_dii_page_url"] = page.url
            # The first visible Download (.csv) is the NSE-only capital-market table.
            buttons = page.get_by_text("Download (.csv)", exact=True)
            if buttons.count() == 0:
                raise RuntimeError("FII/DII CSV download control was not found in the rendered page.")
            try:
                with page.expect_download(timeout=30000) as download_info:
                    buttons.first.click()
                download = download_info.value
                dest = OUT / (download.suggested_filename or "fii_dii_download.csv")
                download.save_as(dest)
                status["downloads"].append({
                    "report": "fii_dii",
                    "file": str(dest),
                    "suggested_filename": download.suggested_filename,
                    "bytes": dest.stat().st_size,
                    "validated": False,
                })
            except Exception as exc:
                status["errors"].append("FII/DII CSV download: " + str(exc))
        except Exception as exc:
            status["errors"].append("FII/DII page: " + str(exc))
            try:
                status["fii_dii_diagnostic_url"] = page.url
                (OUT / "fii_dii_error.html").write_text(page.content(), encoding="utf-8")
            except Exception:
                pass

        try:
            page.goto("https://www.nseindia.com/all-reports-derivatives", wait_until="commit", timeout=60000)
            page.wait_for_timeout(3000)
            status["derivatives_page_title"] = page.title()
            status["derivatives_page_url"] = page.url
            # Filter the visible report list, select the named report, then use NSE's
            # visible multi-file download action. These selectors are deliberately
            # diagnostic and will fail loudly if NSE changes its UI.
            search = page.get_by_placeholder("Enter a keyword")
            if search.count():
                search.first.fill("Participant wise Open Interest")
                page.wait_for_timeout(1500)
            report_item = page.get_by_text("F&O - Participant wise Open Interest(csv)", exact=False)
            if report_item.count() == 0:
                report_item = page.get_by_text("Participant wise Open Interest(csv)", exact=False)
            if report_item.count() == 0:
                raise RuntimeError("Participant-wise Open Interest report was not found after filtering the visible report list.")
            report_item.first.click()
            page.wait_for_timeout(500)
            download_button = page.get_by_text("Multiple file Download", exact=False)
            if download_button.count() == 0:
                raise RuntimeError("Visible multi-file download control was not found.")
            with page.expect_download(timeout=30000) as download_info:
                download_button.first.click()
            download = download_info.value
            dest = OUT / (download.suggested_filename or "participant_open_interest_download")
            download.save_as(dest)
            status["downloads"].append({
                "report": "participant_open_interest",
                "file": str(dest),
                "suggested_filename": download.suggested_filename,
                "bytes": dest.stat().st_size,
                "validated": False,
            })
        except Exception as exc:
            status["errors"].append("Participant OI download: " + str(exc))
            try:
                status["derivatives_diagnostic_url"] = page.url
                (OUT / "derivatives_error.html").write_text(page.content(), encoding="utf-8")
            except Exception:
                pass
        finally:
            browser.close()

    status["download_count"] = len(status["downloads"])
    status["status"] = "downloaded_unvalidated" if status["downloads"] else "download_failed"
    STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(json.dumps(status, indent=2))
    # Preserve diagnostics and artifacts even when the NSE interface changes.
if __name__ == "__main__":
    main()
