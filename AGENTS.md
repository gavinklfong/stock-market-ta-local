# AGENTS.md

## Workspace layout

```
app/
  ticker-retriever/     # Downloads daily OHLCV from Yahoo Finance → data/market-data/*.csv
    download_tickers.py  # Bulk OHLCV download from ticker_list.csv
    download-stock-info.py  # P/E ratio from quarterly/annual EPS → data/pe-data/*.csv
    ticker_list.csv      # Ticker list: Company, Ticker, Major Industry / Sector
  calculate-ta/         # Modular TA indicator scripts → data/ta-data/*.csv (merged)
    common.py            # Shared: read_yfinance_csv(), main() pipeline runner, progress bars
    run_calculation.py   # Orchestrator — runs all modules in dependency order
data/
  market-data/          # Input: raw OHLCV CSVs (one per ticker) — gitignored
  pe-data/              # Output: P/E ratio CSVs (Date, Close, ta_eps_ttm, ta_pe)
  ta-data/              # Output: progressively enriched CSVs
```

## Commands

```bash
# 1. Download market data (activate venv first)
python app/ticker-retriever/download_tickers.py

# 1b. Download P/E ratios from quarterly/annual EPS → data/pe-data/*.csv
python app/ticker-retriever/download-stock-info.py

# 2. Run all TA modules in order (or pick specific ones)
python app/calculate-ta/run_calculation.py              # all, in dependency order
python app/calculate-ta/run_calculation.py trend momentum  # subset

# 3. Or run individual modules
python app/calculate-ta/calculate_trend.py
python app/calculate-ta/calculate_momentum.py
python app/calculate-ta/calculate_volume.py
python app/calculate-ta/calculate_volatility.py
python app/calculate-ta/calculate_regime.py
python app/calculate-ta/calculate_structure.py
python app/calculate-ta/calculate_return.py
```

## Pipeline dependency order

```
trend → momentum → volume → volatility → regime → structure → return
```

- **`calculate_trend.py`** must run first — it creates the initial TA CSV from raw market data.
- **`calculate_return.py`** is independent — it only needs raw OHLCV, can run anytime.
- All other modules read from `data/market-data/` and merge-add columns to `data/ta-data/*.csv`.

## What each module computes

| Module | Indicators |
|--------|-----------|
| `calculate_trend.py` | EMA20/50/200, SuperTrend (+ direction/upper/lower bands), SMA10/20/50, MA slopes (20/50), price/MA20 ratio |
| `calculate_momentum.py` | RSI(14), MACD (+ signal + histogram), ROC(20) |
| `calculate_volume.py` | OBV, CMF(20), VWAP, OFI, log volume |
| `calculate_volatility.py` | ATR(14), Bollinger Bands(20,2) |
| `calculate_regime.py` | GARCH(1,1) vol forecast, 3-state HMM regime, log return |
| `calculate_structure.py` | Swing highs/lows, HH/HL/LH/LL, BOS, CHoCH, nearest support/resistance |
| `calculate_return.py` | Forward returns: 5d/10d/20d |

All output columns use `ta_` prefix (e.g. `ta_rsi14`, `ta_ema20`).

## Architecture

- **Modular pipeline**: Each module's `process_csv()` detects if the output CSV exists and merges (preserves prior columns).
- **Shared infrastructure**: `common.py` exports `main()` (ThreadPoolExecutor, max_workers=10), `read_yfinance_csv()`, and progress helpers.
- **Adding a new module**: Copy the pattern from an existing `calculate_*.py` — implement `compute_*`, `compute_*_columns()`, `process_csv()`, and call `main()` from the `if __name__ == "__main__"` block. Register the module in `run_calculation.py` MODULES/ALL_ORDER dicts.
- **Output**: One CSV per ticker in `data/ta-data/`, sorted by `Date`.

## Gotchas

- **Activate venv** before running anything.
- **yfinance CSV header**: Two-row header (ticker name + price labels). `read_yfinance_csv()` auto-detects it — modules read columns by name only (`Date`, `Open`, `High`, `Low`, `Close`, `Volume`).
- **Ticker list**: Edit `app/ticker-retriever/ticker_list.csv` (columns: Company, Ticker, Major Industry / Sector). Periods auto-converted (`BRK.B` → `BRK-B`). Suffixes like `.L` preserved.
- **Git-ignored**: `data/market-data/*.csv` (regenerated each download). `data/ta-data/` is NOT gitignored.
- **Regime module deps**: `calculate_regime.py` requires `arch` and `hmmlearn` — heavy ML packages.
- **Tests**: Run per-module with `pytest app/calculate-ta/test_calculate_*.py`.
