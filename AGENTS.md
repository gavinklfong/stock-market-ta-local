# AGENTS.md

## Workspace layout

```
app/
  download_market_data/     # Downloads OHLCV from Yahoo Finance
    download_tickers.py       # Bulk OHLCV → data/market-data/*.csv
    download_stock_info.py    # P/E ratios → data/pe-data/*.csv
  analysis_pipeline/    # Prefect flow: download → TA → merge → HTML reports
  analyse_market_data/  # Interactive HTML report generation
    analyse_ticker.py     # Single ticker
    run_analysis.py       # All tickers + sectors + overview
    analyse_sector.py     # Single sector
    analyse_all.py        # All-tickers overview (sorted by 1Y return)
  calculate_ta/         # TA indicator modules (see README.md for full docs)
    common.py               # Shared: read_yfinance_csv(), main() thread-pool runner
    run_calculation.py      # Orchestrator — runs modules in parallel, then merges
  backtest/               # VectorBT backtesting framework
    run_backtest.py         # Single-ticker backtest with YAML config
    backtest_all.py         # Batch backtest all tickers
    strategies/builtins.py  # Built-in strategies
    custom/                 # Custom strategy Python files
    custom_scripts/         # One-off backtest scripts (NG.L, AZN.L, etc.)
    framework/              # Engine, metrics, report, signal, extensions
config/
  ticker_list.csv         # Tickers: Company, Ticker, Sector (37 entries incl. ^FTSE, ETFs)
data/
  market-data/            # Input: raw OHLCV CSVs (gitignored, regenerated)
  pe-data/                # Output: {ticker}_PE.csv, {ticker}_fundamentals.csv
  ta-data/                # Output: {ticker}_ta_{type}.csv + merged {ticker}.csv
  analysis-data/          # Final merged CSVs (market + TA + P/E)
  reports/                # HTML reports + backtest results + strategy evaluations
```

## Commands

```bash
# 1. Download data (activate venv first)
python app/download_market_data/download_tickers.py
python app/download_market_data/download_tickers.py --ticker NG.L        # single ticker
python app/download_market_data/download_stock_info.py
python app/download_market_data/download_stock_info.py --ticker NG.L

# 2. TA indicators (all modules run in PARALLEL)
python app/calculate_ta/run_calculation.py                              # all 7 modules
python app/calculate_ta/run_calculation.py trend momentum               # subset
python app/calculate_ta/run_calculation.py --ticker NG.L                # single ticker
python app/calculate_ta/run_calculation.py --dry-run                    # preview only

# 3. Full Prefect pipeline (download → TA → merge → HTML reports)
python -m app.analysis_pipeline.run_pipeline
python -m app.analysis_pipeline.run_pipeline trend momentum             # TA subset
python -m app.analysis_pipeline.run_pipeline --ticker NG.L              # single ticker
python -m app.analysis_pipeline.run_pipeline --ticker NG.L trend        # single ticker + TA subset
python -m app.analysis_pipeline.run_pipeline --force                    # force full TA recalc
python -m app.analysis_pipeline.run_pipeline --ticker NG.L --force

# 4. Analyse market data → HTML reports

# 4a. Single ticker report
python app/analyse_market_data/analyse_ticker.py NG.L                   # single ticker
python app/analyse_market_data/analyse_ticker.py --dry-run NG.L         # show data only

# 4b. All tickers + sectors + overview (default), or filtered set
python app/analyse_market_data/run_analysis.py
python app/analyse_market_data/run_analysis.py --tickers NG.L BP.L      # specific tickers
python app/analyse_market_data/run_analysis.py --no-sector              # skip sector reports
python app/analyse_market_data/run_analysis.py --dry-run                # data only, no HTML

# 4c. Single sector report
python app/analyse_market_data/analyse_sector.py Utilities
python app/analyse_market_data/analyse_sector.py --dry-run Utilities

# 4d. All-tickers overview (sorted by 1Y return descending)
python app/analyse_market_data/analyse_all.py
python app/analyse_market_data/analyse_all.py --dry-run

# 5. Backtest (reads data/analysis-data/{ticker}.csv)
python app/backtest/run_backtest.py NG.L                                # single ticker
python app/backtest/run_backtest.py NG.L --dry-run                      # show strategies/data
python app/backtest/run_backtest.py NG.L -c app/backtest/configs/NG.L_optimized.yaml
python app/backtest/run_backtest.py NG.L --no-report                    # run but skip HTML
python app/backtest/run_backtest.py NG.L --cutoff 2024-01-01            # restrict data
python app/backtest/backtest_all.py                                     # all tickers in ticker_list.csv
python app/backtest/backtest_all.py --no-report                         # skip HTML generation

# 6. Tests
python run_test.py                              # all tests
python run_test.py calculate_ta  # TA module tests only
python run_test.py download_market_data             # download script tests only
```

## Architecture

- **7 TA modules are independent** — each reads raw OHLCV from `data/market-data/`. No inter-module dependency.
- **Parallel execution**: `run_calculation.py` uses `ThreadPoolExecutor`; `common.py`'s `main()` uses a separate pool (max_workers=10) per module.
- **Output**: Per-module `{ticker}_ta_{type}.csv` → merged into `{ticker}.csv` (Date + all `ta_` columns).
- **Pipeline**: Prefect flow runs downloads in parallel → sequential TA → merge → HTML reports.
- **Backtest framework**: `run_backtest.py` reads merged analysis CSVs, applies strategies from `strategies/builtins.py` or `custom/`, generates HTML reports. `backtest_all.py` iterates over all tickers in `ticker_list.csv`.
- **Custom backtests**: `app/backtest/custom_scripts/` contains one-off scripts (e.g. `NG.L_backtest.py`, `AZN.L_backtest.py`).

## Adding a new TA module

1. Create `app/calculate_ta/calculate_<name>.py` with:
   - `compute_<name>_columns(...)` → dict of `col_name → list`
   - `process_csv(input_path, output_path, total_files, current_file)` → row count
   - Call `main()` from `common.py` at the bottom
2. Register in `run_calculation.py` `MODULES` and `ALL_ORDER` dicts.

## TA module index

| Module | Key indicators |
|--------|---------------|
| `calculate_trend.py` | EMA20/50/200, SuperTrend, SMA10/20/50, MA slopes, price/MA20 ratio, Donchian, Keltner |
| `calculate_momentum.py` | RSI(14), MACD (line/signal/histogram), ROC(20), Williams %R(14), CCI(20), TSI(25,13) |
| `calculate_volume.py` | OBV, CMF(20), VWAP(20), OFI, log volume, ADL, MFI(14), EMV(14) |
| `calculate_volatility.py` | ATR(14), Bollinger Bands(20,2), Historical Vol(20), Parkinson Vol(20) |
| `calculate_regime.py` | GARCH(1,1) vol forecast, 3-state HMM regime (Bull/Bear/Volatile) |
| `calculate_structure.py` | Swing highs/lows, HH/HL/LH/LL, BOS, CHoCH, S/R clusters |
| `calculate_return.py` | Forward returns (5d/10d/20d); rolling alpha/beta vs ^FTSE |

All output columns use `ta_` prefix. Full details in `app/calculate_ta/README.md`.

## Gotchas

- **Activate venv** before running anything. All scripts expect the project virtual environment.
- **yfinance CSV header**: Two-row (sometimes three-row) header. `read_yfinance_csv()` auto-detects it. Modules read columns by name only (`Date`, `Open`, `High`, `Low`, `Close`, `Volume`).
- **Ticker list**: Edit `config/ticker_list.csv` (columns: Ticker, Company, Major Industry / Sector). Periods auto-converted (`BRK.B` → `BRK-B`). Suffixes like `.L` preserved.
- **Git-ignored**: `data/market-data/*.csv` and `venv/` are gitignored. Other `data/` subdirs contain tracked output files.
- **Regime module**: Requires `arch` + `hmmlearn` (heavy ML packages). Install via `pip install -r app/calculate_ta/requirements.txt`.
- **Prefect env**: `.env` sets `PREFECT_SERVER_ANALYTICS_ENABLED=false` (telemetry opt-out).
- **Tests**: Use `python run_test.py <module>` — the wrapper handles `sys.path` setup via root `conftest.py`, which inserts `app/calculate_ta/` and `app/download_market_data/` into the path. Tests live in `app/{module}/tests/`.
- **Backtest data source**: Backtest scripts read from `data/analysis-data/{ticker}.csv` (merged market+TA+P/E), not raw TA data.
- **Incremental TA**: TA modules support incremental recalculation. Use `--force` to skip incrementality (full recalc).
