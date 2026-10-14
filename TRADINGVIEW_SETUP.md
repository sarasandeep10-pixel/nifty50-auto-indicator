# TradingView indicator setup

There are two different scripts in this project workflow. They are not interchangeable.

## 1. Existing dashboard: Nifty Direction Dashboard — Technical Core

This is the script currently shown in the user's TradingView screenshots. It calculates chart-only EMA/VWAP/MACD conditions and a 0–100 score, then displays bullish/bearish bias labels and alert conditions.

Important:
- The score is a rule-based score, not a probability or a verified win rate.
- The previous-day high/low checks are not a complete SMC/ICT market-structure model.
- On a 3-minute chart, bias can switch repeatedly, creating many labels.
- Its alerts are technical state-change notifications, not validated trade recommendations.
- It does not ingest NSE FII/DII or participant-wise open-interest data.

## 2. Project context overlay: nifty_direction_v6.pine

This is the separate educational context overlay maintained in this repository. It includes EMA/VWAP, previous-day levels, 3-bar internal pivots, 5-bar external pivots, prior-swing sweep observations, three-candle FVG boxes, candle-body gap markers, MACD context, higher-timeframe context, and a dashboard.

It deliberately does not issue buy/sell alerts and does not fetch external NSE data. It has not been compiler-verified in TradingView; confirm by adding it in Pine Editor and checking the compiler result.

## Add the repository script to TradingView

1. Open the [TradingView chart](https://www.tradingview.com/chart/).
2. Open **Pine Editor**.
3. Create a new indicator, then copy the complete contents of [nifty_direction_v6.pine](https://github.com/sarasandeep10-pixel/nifty50-auto-indicator/blob/main/nifty_direction_v6.pine) into the editor.
4. Save it, then choose **Add to chart**.
5. Test first on historical bars. Check the compiler message and confirm the visible plots/markers before relying on any observation.
6. To avoid a crowded chart, temporarily hide the older Technical Core indicator while testing the context overlay.

## Known project limitation

The NSE collector and TradingView script are not connected. A successful GitHub Actions run means the workflow checks completed, not that official reports were necessarily downloaded or validated. Do not treat missing or stale report data as current.
