# AGENTS.md

## Workspace layout

```
app/
  ticker-retriever/     # Downloads daily OHLCV from Yahoo Finance → app/data/market-data/*.csv
  calculate-ta/         # Computes TA indicators on market-data CSVs → app/data/ta-data/*.csv
  data/
    market-data/        # Input: raw OHLCV CSVs (one per ticker)
    ta-data/            # Output: TA-enriched CSVs (created by calculate_ta.py)
```

## Commands

```bash
# 1. Download market data (requires venv activated)
python app/ticker-retriever/download_tickers.py

# 2. Calculate technical indicators
python app/calculate-ta/calculate_ta.py
```

Run in order: download first, then calculate.

## Gotchas

- **Virtual env**: `venv/` exists at repo root. Activate it before running any script.
- **Data format**: CSVs from yfinance have a two-row header (ticker name + price labels). `calculate_ta.py` reads columns by name only (`Date`, `Open`, `High`, `Low`, `Close`, `Volume`), so this works, but don't assume standard CSV headers.
- **Tickers**: Edit `app/ticker-retriever/ticker_list.csv` to add tickers. Period format dots (e.g. `BRK.B`) are auto-converted to Yahoo format (`BRK-B`). Suffixes like `.L` are kept as-is.
- **TA output columns**: `ta_rsi14`, `ta_macd_line`, `ta_macd_signal`, `ta_macd_histogram`, `ta_ema20`, `ta_log_return`, `ta_atr14`, `ta_ofi`, `ta_ma20`, `ta_ma50`, `ta_sma10`, `ta_sma50`, `ta_ma20_slope`, `ta_ma50_slope`, `ta_price_ma20_ratio`, `ta_log_volume`, `ta_normalized_atr14`.
- **Parallelism**: `calculate_ta.py` uses 10 threads via `ThreadPoolExecutor`.
- **`data/market-data/*.csv`** is git-ignored; regenerated from Yahoo Finance each run.
