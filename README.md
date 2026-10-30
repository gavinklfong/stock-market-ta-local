# stock-market-ta-local

Modular pipeline for stock/ETF analysis: download OHLCV data, compute 70+ technical indicators, fetch fundamental metrics, merge everything into unified per-ticker CSVs, and generate interactive Plotly HTML reports.

## Quick Start

```bash
# 1. Activate the virtual environment
source venv/bin/activate

# 2. Download data
python app/download_market_data/download_tickers.py          # OHLCV for all tickers
python app/download_market_data/download_stock_info.py       # P/E, dividends, fundamentals

# 3. Compute TA indicators (parallel, ~7 modules)
python app/calculate_ta/run_calculation.py

# 4. Generate HTML analysis reports
python app/analyse_market_data/run_analysis.py

# Full pipeline (steps 2–4 in one Prefect flow)
python -m app.analysis_pipeline.run_pipeline
```

## Commands at a Glance

| Task | Command |
|------|---------|
| TA subset | `python app/calculate_ta/run_calculation.py trend momentum` |
| Single ticker (TA) | `python app/calculate_ta/run_calculation.py --ticker NG.L` |
| Single ticker (pipeline) | `python -m app.analysis_pipeline.run_pipeline --ticker NG.L --force` |
| Single ticker report | `python app/analyse_market_data/analyse_ticker.py NG.L` |
| All-tickers overview | `python app/analyse_market_data/analyse_all.py` |
| Single sector report | `python app/analyse_market_data/analyse_sector.py Utilities` |
| Backtest single ticker | `python app/backtest/run_backtest.py NG.L` |
| Backtest all tickers | `python app/backtest/backtest_all.py` |
| Dry run (no side effects) | `… --dry-run` (supported by most commands) |
| Tests | `python run_test.py` |

## Architecture

```
Yahoo Finance ──→ OHLCV CSVs (data/market-data/)
Yahoo Finance ──→ P/E & dividend data (data/pe-data/)

TA Modules (parallel):
  trend → momentum → volume → volatility → regime → structure → return
  Each reads raw OHLCV, writes {ticker}_ta_{type}.csv → merged into {ticker}.csv

Pipeline: Prefect flow downloads → runs TA → merges → generates HTML reports

Backtest: Reads merged data/analysis-data/{ticker}.csv, applies strategies, generates reports
```

- **7 TA modules** are fully independent — each reads from raw OHLCV only.
- **Parallel execution** via `ThreadPoolExecutor` across modules and tickers.
- **Incremental TA** — re-runs only compute missing rows; use `--force` for full recalc.
- **Column naming** — all TA output columns use the `ta_` prefix.

## TA Module Index

| Module | Key indicators |
|--------|---------------|
| `trend` | EMA20/50/200, SuperTrend, SMA10/20/50, MA slopes, price/MA ratio, Donchian, Keltner |
| `momentum` | RSI(14), MACD, ROC(20), Williams %R(14), CCI(20), TSI(25,13) |
| `volume` | OBV, CMF(20), VWAP(20), OFI, ADL, MFI(14), EMV(14) |
| `volatility` | ATR(14), Bollinger Bands(20,2), Historical Vol, Parkinson Vol |
| `regime` | GARCH(1,1) vol forecast, 3-state HMM (Bull/Bear/Volatile) |
| `structure` | Swing highs/lows, HH/HL/LH/LL, BOS, CHoCH, S/R clusters |
| `return` | Forward returns (5d/10d/20d), rolling alpha/beta vs ^FTSE |

See `app/calculate_ta/README.md` for the full indicator catalog with formulas and calculation details.

## Data Flow

```
Raw OHLCV      →  TA indicators      →  Merged analysis CSV
data/market-data/  data/ta-data/      data/analysis-data/
{ticker}.csv       {ticker}_ta_*.csv    {ticker}.csv
                                     (market + TA + P/E/fundamentals)
```

- `data/market-data/` — raw OHLCV from yfinance (gitignored, regenerated)
- `data/pe-data/` — daily P/E, dividend yield, EPS time-series
- `data/ta-data/` — per-module TA outputs + merged indicator CSVs
- `data/analysis-data/` — final merged CSV (market + TA + fundamentals)
- `data/reports/` — interactive HTML reports, backtest results

## Tickers

37 instruments in `config/ticker_list.csv` — FTSE 100 constituents, select ETFs, and the ^FTSE benchmark. Suffixes (`.L`) preserved; periods auto-converted (`BRK.B` → `BRK-B`).

## Gotchas

- **Activate venv** before running anything.
- **yfinance CSV header**: Two-row (sometimes three-row) header. `read_yfinance_csv()` auto-detects it.
- **Regime module**: Requires `arch` + `hmmlearn` (heavy ML packages). Install via `pip install -r app/calculate_ta/requirements.txt`.
- **Tests**: Run via `python run_test.py <module>` — the wrapper handles `sys.path` setup.
- **Backtest data**: Reads from `data/analysis-data/{ticker}.csv` (merged), not raw TA data.

## Agent Skills

The project defines two reusable agent skills under `.agents/skills/` that guide AI agents through multi-step analysis workflows.

| Skill | Purpose | Output |
|-------|---------|--------|
| **Investment Strategy** (`.agents/skills/investment-strategy.md`) | Formulate, investigate, evaluate, and backtest investment strategies for a ticker. Runs all 32 built-in strategies, creates custom strategies when needed, optimizes parameters, and recommends the best strategy by risk-adjusted return. | `data/reports/strategies/{ticker}/{latest_date}.md` |
| **Market Situation Review** (`.agents/skills/review-market-situation.md`) | Assess the current market situation across 7 dimensions (trend, momentum, return, structure, volatility, volume, regime) and generate a buy/sell/hold signal. Cross-references findings with the investment strategy report. Supports historical backtesting via `{evaluation_date}` parameter. | `data/reports/evaluation/{ticker}/{date}_evaluation.md` |

**Workflow:** Run the Investment Strategy skill first to generate a strategy report, then run the Market Situation Review skill to evaluate current conditions against the recommended strategy.

## Detailed Docs

| Document | Contents |
|----------|----------|
| `app/calculate_ta/README.md` | Full TA indicator reference with formulas, minimum data, dependencies |
| `AGENTS.md` | Commands, architecture, gotchas for developers and agents |
| `docs/all_technical_analysis.md` | Educational: how algos use each indicator category for buy/sell signals |
| `notebook/` | Jupyter notebooks for exploratory analysis |
