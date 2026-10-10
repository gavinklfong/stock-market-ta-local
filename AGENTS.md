# AGENTS.md

## Workspace layout

```
app/
  ticker-retriever/     # Downloads daily OHLCV from Yahoo Finance → data/market-data/*.csv
  calculate-ta/         # Modular TA indicator scripts → data/ta-data/*.csv (merged)
  data/
    market-data/        # Input: raw OHLCV CSVs (one per ticker)
    ta-data/            # Output: progressively enriched CSVs
```

## Commands

```bash
# 1. Download market data (activate venv first)
python app/ticker-retriever/download_tickers.py

# 2. Run TA scripts in order — each adds columns to the same CSVs
python app/calculate-ta/calculate_ta.py          # core: RSI, MACD, ATR, OFI, MAs, log return/vol, normalized ATR
python app/calculate-ta/calculate_trend.py       # trend: EMA20/50/200, SuperTrend (ATR-based)
python app/calculate-ta/calculate_momentum.py    # momentum: RSI, MACD, ROC(20)
python app/calculate-ta/calculate_volume.py      # volume: OBV, CMF(20), VWAP
python app/calculate-ta/calculate_volatility.py  # volatility: ATR(14), Bollinger Bands(20,2) → ta_atr14, ta_bband_upper/middle/lower
```

Each module reads from `data/market-data/`, appends its columns to the corresponding file in `data/ta-data/`, and merges with whatever columns already exist from prior modules.

## Architecture

- **Modular pipeline**: `calculate_ta.py` is the base; other modules are additive. Each module's `process_csv()` detects if the output CSV already exists and merges (preserves prior columns).
- **Column naming convention**: All TA columns use the `ta_` prefix (e.g. `ta_rsi14`, `ta_ema20`, `ta_bband_upper`).
- **Parallelism**: All `main()` functions use `ThreadPoolExecutor(max_workers=10)`.
- **Output**: Sorted by `Date`, one CSV per ticker in `data/ta-data/`.
- **Functions to copy when adding indicators**: Each module exports `compute_<indicator>()` and `compute_<category>_columns()` plus `process_csv()` and `main()`.

## Gotchas

- **Activate venv** before running anything.
- **yfinance CSV header**: Two-row header (ticker name + price labels). Modules read columns by name only (`Date`, `Open`, `High`, `Low`, `Close`, `Volume`).
- **Ticker list**: Edit `app/ticker-retriever/ticker_list.csv`. Periods auto-converted (`BRK.B` → `BRK-B`). Suffixes like `.L` preserved.
- **Git-ignored**: `data/market-data/*.csv` (regenerated each download).
- **TA output order matters**: Run `calculate_ta.py` first, then trend/momentum/volume/volatility modules in any order after that.
- **Tests**: Run per-module tests with `pytest app/calculate-ta/test_calculate_*.py`.
