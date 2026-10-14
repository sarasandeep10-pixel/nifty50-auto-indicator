# Nifty 50 Market Data Learning Dashboard — starter kit

## What currently works
- `collector/parse_nse_reports.py` validates and normalizes a participant-wise open-interest CSV supplied by the user and writes a dated JSON file.
- `collector/check_official_sources.py` checks whether the 2 official NSE report pages respond and writes `data/processed/official_source_status.json`.
- `.github/workflows/daily.yml` runs parser tests and the source-page check on weekdays at 18:00 IST, and uploads the source-status JSON as a GitHub Actions artifact.
- `tradingview/nifty_direction_v6.pine` is a chart-only technical dashboard. It does not fetch NSE participant data.

## Important limits
1. **This is not yet a complete automatic NSE data feed.** The scheduled job checks the official pages' availability; it does not download the actual FII/DII or participant-wise OI CSVs, and it does not generate a market outlook.
2. A reachable web page does not prove that its latest report was downloaded, is current, or passed schema validation. Check the artifact's `data_downloaded` and `data_validated` fields; they remain false for the source-status check.
3. Official sources:
   - NSE derivatives daily reports: https://www.nseindia.com/all-reports-derivatives
   - NSE FII/FPI and DII activity: https://www.nseindia.com/reports/fii-dii
   NSE describes its cash-market FII/FPI figures as provisional and subject to change.
4. NSE may change report delivery methods, access controls, file names, and schemas. This implementation does not scrape undocumented endpoints or bypass access controls.
5. TradingView Pine Script cannot fetch arbitrary URLs or read local files. This repository does not claim an automatic NSE-to-TradingView feed.
6. The project is for neutral market-data learning and historical review, not predictions or trading instructions. Participant positioning alone does not determine what the market will do.

## Run the CSV parser locally
Use Python 3.11+. Place an official participant-wise OI CSV in a local folder and run:

```bash
python collector/parse_nse_reports.py --input data/inbox/your_participant_oi.csv --output data/processed
```

The parser fails closed when it cannot safely identify the required columns. Inspect the report date, headers, units, and participant labels before relying on the output.

## View the scheduled source check
Open the repository's **Actions** tab, select **Daily NSE Data Status Check**, open a successful run, and download the `official-nse-source-status` artifact. If NSE blocks GitHub Actions or is temporarily unavailable, the report records the failure rather than guessing.

## Next engineering milestone
Implement and test a supported download path for the actual official report files, with date checks, file integrity checks, schema validation, and a historical archive. Only then can the project truthfully claim automated report collection.
