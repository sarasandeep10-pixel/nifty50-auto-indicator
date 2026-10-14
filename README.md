# Nifty 50 Direction System — starter kit

## What is included
- `tradingview/nifty_direction_v6.pine`: Pine Script v6 chart-only trend dashboard with EMA, VWAP, MACD, prior-day levels, a transparent score, and alerts.
- `collector/parse_nse_reports.py`: validates and normalizes an NSE participant-wise OI CSV that is placed in `data/inbox/` and writes a dated JSON summary.
- `.github/workflows/daily.yml`: scheduled GitHub Actions scaffold to run the parser and preserve output artifacts.

## Important limitations
1. This is a starter kit, not a deployed service. No GitHub repository, credentials, or hosting have been configured.
2. The parser deliberately does not scrape undocumented NSE endpoints. NSE may change access controls, file naming, and report schemas; use official reports and validate every file.
3. TradingView Pine Script cannot fetch arbitrary URLs or read local files. `request.seed()` is the Pine Seeds route for custom EOD series, but TradingView's current documentation says creation of new Pine Seeds repositories is suspended. Therefore this kit does NOT claim a fully automatic NSE-to-Pine feed. A compatible existing Pine Seeds feed or a supported custom market-data provider is needed for external metrics to appear inside Pine.
4. The Pine indicator calculates chart-derived technical signals only. External FII/DII/Client/PRO figures are not secretly inferred from price.
5. Treat scores as research aids, not predictions or trading instructions. Test on historical data before use.

## Run parser locally
Use Python 3.11+ and install `pandas` if desired; the script itself uses only the standard library.

Place the official NSE participant-wise OI CSV in `data/inbox/`, then run:

```bash
python collector/parse_nse_reports.py --input data/inbox/your_participant_oi.csv --output data/processed
```

The parser tries to recognize common column names and fails closed if required fields cannot be identified. Inspect the JSON and adjust mappings only after checking the report headers.

## Next integration milestone
First validate the parser on a current official NSE CSV. Then choose a TradingView-compatible custom feed. Do not use `request.seed()` for a brand-new repository unless TradingView restores new-repository creation or confirms an alternative path.
