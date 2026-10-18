# AGENTS.md

## Workspace layout

```
app/
  download-market-data/     # Downloads OHLCV from Yahoo Finance
    download_tickers.py       # Bulk OHLCV → data/market-data/*.csv
    download_stock_info.py    # P/E ratios → data/pe-data/*.csv
  analysis-pipeline/    # Prefect flow orchestrating the full pipeline
  analyse-market-data/  # Analyse market data and generate interactive HTML reports
    run_analysis.py       # Generate market dashboard HTML reports
  calculate-ta/         # TA indicator modules (see README.md for full docs)
    common.py               # Shared: read_yfinance_csv(), main() thread-pool runner
    run_calculation.py      # Orchestrator — runs modules in parallel, then merges
  backtest/               # VectorBT backtesting (NG.L-focused)
config/
  ticker_list.csv         # Tickers: Company, Ticker, Sector
data/
  market-data/            # Input: raw OHLCV CSVs (gitignored, regenerated)
  pe-data/                # Output: {ticker}_PE.csv, {ticker}_fundamentals.csv
  ta-data/                # Output: {ticker}_ta_{type}.csv + merged {ticker}.csv
  analysis-data/          # Final merged CSVs (market + TA + P/E)
```

## Commands

```bash
# 1. Download data (activate venv first)
python app/download-market-data/download_tickers.py
python app/download-market-data/download_stock_info.py

# 2. TA indicators (all modules run in PARALLEL)
python app/calculate-ta/run_calculation.py              # all 7 modules
python app/calculate-ta/run_calculation.py trend momentum  # subset
python app/calculate-ta/run_calculation.py --dry-run     # preview only

# 3. Full Prefect pipeline (downloads + TA + merge analysis)
python -m app.analysis_pipeline.run_pipeline
python -m app.analysis_pipeline.run_pipeline trend momentum

# 4. Analyse market data and generate HTML report (one file per ticker)
python app/analyse-market-data/run_analysis.py              # all tickers
python app/analyse-market-data/run_analysis.py AAPL MSFT    # specific tickers
python app/analyse-market-data/run_analysis.py --dry-run    # show analysis only

# Output: data/reports/{ticker}_analysis.html per ticker

# 5. Backtest (uses data/ta-data/NG.L.csv)
python app/backtest/backtest_ng.py
python app/backtest/backtest_ng.py --strategy supertrend

# 6. Tests
python run_test.py                              # all tests
python run_test.py calculate-ta                 # TA module tests only
python run_test.py download-market-data             # download script tests only
```

## Architecture

- **All 7 TA modules are independent** — each reads raw OHLCV from `data/market-data/`. No inter-module dependency.
- **Parallel execution**: `run_calculation.py` runs modules via `ThreadPoolExecutor(max_workers=7)`, then merges outputs.
- **Output files**: Per-module output `{ticker}_ta_{type}.csv` (Date + only that module's `ta_` columns), merged into `{ticker}.csv` (Date + all `ta_` columns).
- **Full pipeline**: Prefect flow downloads OHLCV + P/E in parallel → runs TA → merges market+TA+PE into `data/analysis-data/{ticker}.csv`.

## Adding a new module

1. Create `app/calculate-ta/calculate_<name>.py` with:
   - `compute_<name>_columns(...)` → dict of `col_name → list`
   - `process_csv(input_path, output_path, total_files, current_file)` → row count
   - Call `main()` from `common.py` at the bottom
2. Register in `run_calculation.py` `MODULES` and `ALL_ORDER` dicts.

## TA module index

| Module | Key indicators |
|--------|---------------|
| `calculate_trend.py` | EMA20/50/200, SuperTrend, SMA10/20/50, MA slopes, price/MA20 ratio |
| `calculate_momentum.py` | RSI(14), MACD (line/signal/histogram), ROC(20) |
| `calculate_volume.py` | OBV, CMF(20), VWAP(20), OFI, log volume |
| `calculate_volatility.py` | ATR(14), Bollinger Bands(20,2) |
| `calculate_regime.py` | GARCH(1,1) vol forecast, 3-state HMM regime |
| `calculate_structure.py` | Swing highs/lows, HH/HL/LH/LL, BOS, CHoCH, S/R |
| `calculate_return.py` | Forward returns: 5d/10d/20d |

All output columns use `ta_` prefix. Module details are in `app/calculate-ta/README.md`.

## Gotchas

- **Activate venv** before running anything.
- **yfinance CSV header**: Two-row (sometimes three-row) header. `read_yfinance_csv()` auto-detects it. Modules read columns by name only (`Date`, `Open`, `High`, `Low`, `Close`, `Volume`).
- **Ticker list**: Edit `config/ticker_list.csv` (columns: Ticker, Company, Major Industry / Sector). Periods auto-converted (`BRK.B` → `BRK-B`). Suffixes like `.L` preserved.
- **Git-ignored**: `data/market-data/*.csv` is gitignored. Other `data/` subdirs contain tracked output files.
- **Regime module**: Requires `arch` + `hmmlearn` (heavy ML packages). Install via `app/calculate-ta/requirements.txt`.
- **Test files**: Located in `app/calculate-ta/tests/` and `app/download-market-data/tests/` subdirectories. Use `run_test.py` for the correct sys.path setup.
- **`conftest.py`** adds `app/calculate-ta/` and `app/download-market-data/` to `sys.path` so tests can import sibling modules directly.
