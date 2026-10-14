# Nifty 50 Market Data Learning Dashboard — starter kit

## Current components
- `collector/check_official_sources.py`: checks whether official NSE report pages respond.
- `collector/fetch_official_reports.py`: searches the official pages' public HTML for direct CSV links and downloads a matching file only when a direct link is available. It does not guess hidden endpoints or bypass access controls.
- `collector/parse_nse_reports.py`: validates and normalizes a participant-wise OI CSV supplied by the user and writes a dated JSON file.
- `.github/workflows/daily.yml`: runs tests and the collection attempt on weekdays at 18:00 IST, then uploads a status artifact.
- `tradingview/nifty_direction_v6.pine`: chart-only technical dashboard; it does not fetch external NSE data.

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

## Run the parser locally
Use Python 3.11+. For a manually downloaded official participant-wise OI CSV:

```bash
python collector/parse_nse_reports.py --input data/inbox/your_participant_oi.csv --output data/processed
```

The parser fails closed when required columns cannot be mapped. Inspect the report date, headers, units, and participant labels before using its output.

## Check the scheduled run
Open **Actions** in the repository, select **Daily NSE Data Status Check**, open the latest run, and download the `official-nse-data-status` artifact. It contains `collection_status.json` and source-status details. If the public pages do not expose direct CSV links to the runner, the report records that limitation.

## Remaining engineering work
The next step is to validate downloaded report schemas and dates, normalize the official FII/DII CSV, and create a historical dashboard. A stable automatic report feed can only be claimed after successful real-file collection and validation on repeated runs.
