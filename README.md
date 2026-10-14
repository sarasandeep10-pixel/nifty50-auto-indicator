# Nifty 50 Market Data Learning Dashboard — starter kit

## Current components
- `collector/check_official_sources.py`: checks whether official NSE report pages respond.
- `collector/fetch_official_reports.py`: searches the official pages' public HTML for direct CSV links and downloads a matching file only when a direct link is available. It does not guess hidden endpoints or bypass access controls.
- `collector/parse_nse_reports.py`: validates and normalizes a participant-wise OI CSV supplied by the user and writes a dated JSON file.
- `collector/fetch_upstox_institutional_data.py`: optional adapter for Upstox's documented FII/DII Market Information API. It requires the `UPSTOX_ACCESS_TOKEN` GitHub secret and writes a separate normalized JSON file.
- `.github/workflows/daily.yml`: runs tests and the collection attempt on weekdays at 18:00 IST, then uploads a status artifact.
- `nifty_direction_v6.pine`: educational chart-context overlay with EMA/VWAP, previous-day levels, internal/external swing markers, swing-level sweep observations, 3-candle FVG zones, candle-body gaps, MACD context, and higher-timeframe context. It does not issue buy/sell alerts or fetch external NSE data.

## Important limitations
1. **Automated report downloads are best-effort and not yet guaranteed.** NSE may render download controls with client-side scripts, require a session, or change its page structure. When no direct public CSV link is available, the collector records that result instead of guessing a hidden endpoint.
2. A page being reachable is not proof that its data is current or validated. The collection status records downloaded files separately from validation status.
3. Official sources:
   - NSE derivatives daily reports: https://www.nseindia.com/all-reports-derivatives
   - NSE FII/FPI and DII activity: https://www.nseindia.com/reports/fii-dii
   NSE notes that cash-market FII/FPI figures are provisional and subject to change.
4. The workflow uploads the source and collection status as an artifact. It does not commit raw reports into the repository.
5. TradingView Pine Script cannot fetch arbitrary URLs or read local files. This repository does not claim a live NSE-to-TradingView feed.
6. This project is for neutral market-data learning and historical review. It does not produce predictions or trading instructions. Participant positioning alone does not determine future market movement.

## Optional Upstox API source

The Upstox adapter uses the documented `/v2/market/fii` and `/v2/market/dii` endpoints. To enable it in GitHub Actions, add a repository Actions secret named `UPSTOX_ACCESS_TOKEN` and a repository Actions variable named `ENABLE_UPSTOX_API` with value `true`. Do not paste access tokens into chat or commit them to the repository. The API returns FII activity by market segment and DII cash activity; it does **not** provide the full participant-wise Client/Pro/FII/DII OI table. Output is stored separately as `data/processed/upstox_institutional_activity.json`. The adapter has not been authenticated or live-tested from this environment because no access token is available.

## Run the parser locally
Use Python 3.11+. For a manually downloaded official participant-wise OI CSV:

```bash
python collector/parse_nse_reports.py --input data/inbox/your_participant_oi.csv --output data/processed
```

The parser fails closed when required columns cannot be mapped. Inspect the report date, headers, units, and participant labels before using its output.

## Check the scheduled run
Open **Actions** in the repository, select **Daily NSE Data Status Check**, open the latest run, and download the `official-nse-data-status` artifact. It contains `collection_status.json` and source-status details. If the public pages do not expose direct CSV links to the runner, the report records that limitation.

## Current status and next priorities
1. **Data ingestion remains incomplete.** The latest verified run reached both official NSE pages, but the collector found no recognizable FII/DII rows and no direct CSV links for participant OI. A green test run is not proof of successful data collection.
2. The Pine Script is a chart-context overlay only. Copy `nifty_direction_v6.pine` into the Pine Editor in TradingView and add it to a chart. Pine cannot read the GitHub workflow artifacts or arbitrary NSE URLs directly.
3. Next engineering work is to use a documented/public report download path, validate the actual downloaded CSVs and report dates, and then build a historical dashboard. Do not show missing or stale data as current.

## Indicator notes
- Internal swings use 3-bar pivots; external swings use 5-bar pivots.
- Sweep markers indicate a prior confirmed swing level was crossed and the candle closed back inside.
- FVG boxes mark a three-candle price imbalance; body-gap markers identify non-overlapping real bodies.
- These are chart observations for learning, not validated predictions or instructions. Test on historical charts and understand that pivot markers appear only after the right-side confirmation bars.

## Alternative public data sources to test

NSE access from a hosted runner can fail even when the report is available in a normal browser. These public pages are candidate cross-checks, not yet verified automated feeds:

- **FNOScan FII/DII data:** https://www.fnoscan.com/fii-dii-data — displays cash-market FII/DII activity and participant-wise derivatives OI. Its published methodology says the underlying datasets come from NSE and BSE. Automated collection, export availability, terms, and schema still need verification before using it in this project.
- **Moneycontrol OI participants:** https://www.moneycontrol.com/markets/fii-dii-data/oi-participants/ — public display of participant categories. Use as a comparison source unless an approved export or documented access method is confirmed.
- **NSDL latest FPI report:** https://www.fpi.nsdl.co.in/web/Reports/Latest.aspx — cross-check for FPI investment data; it does not replace DII cash figures or the full participant-wise derivatives OI report.
- **CDSL FII/FPI reports:** https://www.cdslindia.com/Publications/FIIDailyData.aspx — another depository source for FPI investment data.

### Fallback policy

1. Keep the original source URL, retrieval timestamp, report date, and dataset label with every imported record.
2. Do not combine cash-market FII/DII values with derivatives participant OI; they measure different things.
3. Do not silently substitute a third-party snapshot for an official report. Mark its source and provisional status, and compare values/dates before accepting it.
4. Do not scrape undocumented endpoints or bypass access controls. Prefer a public CSV export, documented API, or permitted public page. The alternative pages above are candidates only until an automated test confirms retrieval and schema validation.
5. A green workflow means data is usable only if source, date, schema, and row checks pass.
