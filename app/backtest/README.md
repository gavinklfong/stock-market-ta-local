# Backtest Framework

A reusable, ticker-agnostic backtesting framework built on [vectorbt](https://vectorbt.dev/) for simulating trading strategies against historical OHLCV + TA data.

## Overview

The framework evaluates trading strategies, extracts performance metrics, and generates interactive HTML reports with:

- **Ranked strategy table** sorted by any metric
- **Equity curves** with buy & hold benchmark comparison
- **Key metrics bar chart** (return, Sharpe, profit factor, win rate, max drawdown, total trades)
- **Best strategy detail** with trade P&L distribution histogram

## Architecture

```
app/backtest/
├── run_backtest.py              # CLI entry point — single ticker
├── run_backtest_analysis.py     # All-in-one helper — data + indicators + backtest results
├── run_strategy_backtest.py     # Portable backtest-only helper — works from ANY directory
├── backtest_all.py              # Batch runner — all tickers from ticker_list.csv
├── framework/                   # Core reusable modules
│   ├── __init__.py              # Public API exports
│   ├── engine.py                # BacktestEngine — vectorbt portfolio simulation
│   ├── metrics.py               # Metric extraction from Portfolio objects
│   ├── signal.py                # SignalBase — optional OOP wrapper
│   ├── extensions.py            # Custom strategy loader + registry
│   └── report.py                # Plotly HTML report generator
├── strategies/
│   └── builtins.py              # 32 built-in strategies + group registry
├── configs/
│   ├── default.yaml             # All 32 strategies
│   ├── NG.L_optimized.yaml        # NG.L optimized (10 mean-reversion strategies). Ticker-specific config — use `{Ticker}_{function}.yaml`
│   └── trend_stock.yaml         # Trend-following for stock tickers
└── custom/
    ├── template_strategy.py     # Starter template
    └── NG.L_custom.py             # Example custom strategies. Ticker-specific scripts — use `{Ticker}_{function}.py`
└── custom_scripts/              # Ticker-specific scripts — use `{Ticker}_{function}.py`
```

### Data Flow

```
data/analysis-data/{ticker}.csv  (OHLCV + TA columns prefixed ta_)
        │
        ▼
┌─────────────────────┐
│   BacktestEngine    │  Reads CSV, filters by cutoff date
│   .run_batch()      │  Applies each strategy → vectorbt Portfolio
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  calculate_metrics  │  Extracts return, Sharpe, drawdown, win rate, etc.
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  generate_report    │  Produces multi-tab HTML report with Plotly charts
└─────────────────────┘
```

## Framework Components

> **Note for AI agents:** All code examples in this README are reference snippets. To run them, use the `shell` tool with `python -c "..."` or write a script file — **never** use Code Mode (`execute`) for Python code with imports.

### BacktestEngine

The core engine that runs strategies via vectorbt:

```python
from framework.engine import BacktestEngine

engine = BacktestEngine(
    data_path="data/analysis-data/NG.L.csv",
    cutoff_date=pd.Timestamp("2016-10-15"),  # ~10 years of data
    initial_capital=100_000,
    commission=0.001,                        # 0.1% round-trip
    slippage=0.001,                          # 0.1%
    trailing_pct=0.05,                       # Optional trailing stop
)

# Pass a dict[str, Callable] mapping strategy name → signal function
results = engine.run_batch(signal_fns={"golden_cross": golden_cross})
```

**Key parameters:**

| Parameter | Default | Description |
|---|---|---|
| `data_path` | — | Path to `{ticker}.csv` in `data/analysis-data/` |
| `cutoff_date` | `2016-10-15` | Only use data on/after this date (pass `None` for full history) |
| `initial_capital` | `100,000` | Starting cash in GBP |
| `commission` | `0.001` | Round-trip commission rate |
| `slippage` | `0.001` | Slippage rate per trade |
| `trailing_pct` | `None` | If set, uses `TrailingStopPortfolio` with this percentage |

### `BacktestEngine` Method Reference

| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `BacktestEngine(data_path, cutoff_date=…, initial_capital=100000, commission=0.001, slippage=0.001, trailing_pct=None)` | Construct engine with file path and config. Loads CSV lazily via `.df` or `.load_data()`. |
| `load_data` | `.load_data() → pd.DataFrame` | Load and clean the CSV (sort by Date, drop NaN Close/High/Low, apply cutoff). |
| `run` | `.run(signal_fn) → vbt.Portfolio` | Run a **single** strategy, return vectorbt Portfolio object. |
| `run_and_metrics` | `.run_and_metrics(signal_fn) → (Portfolio, dict)` | Run one strategy and return (portfolio, metrics_dict). |
| `run_batch` | `.run_batch(signal_fns: dict[str, Callable]) → list[dict]` | Run **multiple** strategies. Each key→callable pair is tested. Returns list of metric dicts (each with a "Strategy" key). |
| `get_signals` | `.get_signals(signal_fn) → (pd.Series, pd.Series)` | Resolve a signal function to (entries, exits) int Series. |
| `get_benchmark_returns` | `.get_benchmark_returns() → pd.Series` | Buy-and-hold daily returns of the ticker. |
| `get_strategy_returns` | `.get_strategy_returns(signal_fn) → pd.Series` | Daily returns from running a single strategy. |
| `aligned_returns` | `.aligned_returns(strategy_ret) → (pd.Series, pd.Series)` | Align strategy and benchmark returns to common index. |

> **Critical `run_batch()` gotcha:** It only accepts `signal_fns` — a dict mapping strategy name strings to callable signal functions. There are **no** `tickers`, `cutoff`, or `ticker_names` parameters. The ticker data is already determined by `data_path` in `__init__`.

### `calculate_metrics`

```python
from framework.metrics import calculate_metrics, pick_best, rank_strategies

metrics = calculate_metrics(portfolio)        # dict of 6 key metrics
best = pick_best(results)                      # best result dict from run_batch() output
ranked = rank_strategies(results, sort_by="Total Return (%)")  # sorted list
```

### Metrics

Extracts 6 key metrics from each portfolio:

| Metric | Description |
|---|---|
| `Total Return (%)` | Cumulative return over the period |
| `Annualized Return (%)` | Compounded annual return |
| `Sharpe Ratio` | Risk-adjusted return (risk-free rate: 5%) |
| `Max Drawdown (%)` | Largest peak-to-trough decline |
| `Win Rate (%)` | Percentage of profitable trades |
| `Profit Factor` | Gross profit / gross loss |

Plus secondary metrics: total trades, avg trade length, trade P&L stats.

### SignalBase (OOP)

An optional abstract base class for strategies that prefer object-oriented design:

```python
from framework.signal import SignalBase

class MyStrategy(SignalBase):
    name = "my_strategy"
    display_name = "My Custom Strategy"
    category = "custom"

    def signal(self, df):
        rsi = df["ta_rsi14"]
        entries = (rsi > 30) & (rsi.shift(1) <= 30)
        exits = (rsi < 50) & (rsi.shift(1) >= 50)
        return entries.astype(int), exits.astype(int)
```

### Extensions (Custom Strategy Loader)

Discovers and loads custom strategy Python files from a directory:

```python
# The extensions module is now portable — works from any working directory.
# No sys.path manipulation needed.
from framework.extensions import register_custom, load_custom_strategies

# Loading all .py files from a directory (20+ files → 100+ strategies)
custom_strategies = load_custom_strategies("app/backtest/custom/")

# Loading only specific module files (recommended — avoids loading irrelevant strategies)
custom_strategies = load_custom_strategies(
    "app/backtest/custom",
    module_names=["ba_defense_meanrev", "ba_regime_filter_meanrev"]
)
```

> **⚠️ Do NOT load all custom strategies for a single-ticker backtest.** There are 20+ files covering 10+ different tickers, producing 100+ strategies. Most are irrelevant. Use `python app/analyse-market-data/get_evaluation_data.py {ticker} --custom-strategies` to discover relevant ones, then load only those via `module_names`.

> **Note:** The `load_custom_strategies()` function internally resolves the project root from its own file location (`Path(__file__).parents[3]`), so it works correctly even when called from scripts in `/tmp/` or any other directory. The `_resolve_framework_import()` function pre-populates `sys.modules` to ensure a single `_custom_registry` across all import paths.

> **JSON serialization:** The `run_backtest_analysis.py` helper includes a `_NumpyEncoder` class that handles numpy int64/floating types (e.g., `ta_supertrend_direction`) so they serialize correctly to JSON. All `json.dumps()` calls in the script use `cls=_NumpyEncoder`.

### Report Generator

Produces a multi-tab HTML report:

```python
from framework.report import generate_report

report_path = generate_report(
    results=results,
    df=pd.read_csv("data/analysis-data/NG.L.csv"),
    ticker="NG.L",
    output_dir="data/reports/backtest",
    top_n=15,          # strategies shown on charts
    sort_by="Total Return (%)",
)
# → data/reports/backtest/NG.L_backtest_report.html
```

## Running Backtests

### Quick Start — Primary Helper: `run_backtest_analysis.py`

**Recommended entry point for investment-strategy Phase 2.** Combines data snapshot, indicators, forward returns, yearly performance, and backtest results in one JSON output. Works from any working directory.

```bash
# Full analysis: data snapshot + all built-in strategies (recommended)
python app/backtest/run_backtest_analysis.py NG.L --cutoff YYYY-MM-DD --json --no-report

# Data snapshot only (no backtest) — fast, for Phase 1
python app/backtest/run_backtest_analysis.py NG.L --no-backtest --json

# Forward returns stats only
python app/backtest/run_backtest_analysis.py NG.L --forward-returns

# Yearly performance only
python app/backtest/run_backtest_analysis.py NG.L --yearly

# With custom strategies
python app/backtest/run_backtest_analysis.py NG.L --cutoff YYYY-MM-DD --custom NG.L_custom --json --no-report

# Only a specific group
python app/backtest/run_backtest_analysis.py NG.L --group mean-reversion --json --no-report

# Verbose per-strategy details (human-readable)
python app/backtest/run_backtest_analysis.py NG.L --cutoff YYYY-MM-DD --verbose --no-report
```

### Quick Start — Portable Backtest Helper: `run_strategy_backtest.py`

For focused backtest runs without the data snapshot overhead. **Works from any directory.**

```bash
# List available strategies WITHOUT running a backtest (use this first!)
python app/backtest/run_strategy_backtest.py NG.L --list
python app/backtest/run_strategy_backtest.py NG.L --list --custom NG.L_custom

# All built-in strategies
python app/backtest/run_strategy_backtest.py NG.L

# With custom cutoff
python app/backtest/run_strategy_backtest.py NG.L --cutoff YYYY-MM-DD

# With custom strategies (by module file name WITHOUT .py)
python app/backtest/run_strategy_backtest.py NG.L --custom NG.L_custom

# Multiple custom modules
python app/backtest/run_strategy_backtest.py NG.L --custom ba_defense_meanrev ba_regime_filter

# JSON output for programmatic consumption
python app/backtest/run_strategy_backtest.py NG.L --cutoff YYYY-MM-DD --json --no-report

# Skip HTML report generation
python app/backtest/run_strategy_backtest.py NG.L --no-report

# Built-ins only (no custom)
python app/backtest/run_strategy_backtest.py NG.L --builtins-only

# Filter by group name
python app/backtest/run_strategy_backtest.py NG.L --group mean-reversion

# Verbose: print per-strategy details
python app/backtest/run_strategy_backtest.py NG.L --verbose --no-report
```

> **⚠️ IMPORTANT — `--custom` takes module file names, NOT strategy names:**
> - File: `ba_defense_meanrev.py` → CLI: `--custom ba_defense_meanrev`
> - Wrong: `--custom ba_defense` (truncated) or `--custom signal_ba_defense_meanrev` (strategy name)
> - Use `--list` before running to verify your module names are correct
> - `--dry-run` does **NOT** exist on this script — use `--list` instead

### Single Ticker (Original CLI)

```bash
# Default config (all 32 strategies)
python app/backtest/run_backtest.py NG.L

# Specific config
python app/backtest/run_backtest.py NG.L -c app/backtest/configs/NG.L_optimized.yaml

# With custom strategies
python app/backtest/run_backtest.py NG.L --custom-dir app/backtest/custom

# Override trailing stop
python app/backtest/run_backtest.py NG.L --trailing-pct 0.05

# Custom cutoff date
python app/backtest/run_backtest.py NG.L --cutoff 2018-01-01

# Preview only (no actual backtest)
python app/backtest/run_backtest.py --dry-run NG.L

# Skip HTML report
python app/backtest/run_backtest.py NG.L --no-report
```

### Batch (All Tickers)

```bash
# All tickers, all strategies
python app/backtest/backtest_all.py

# Specific tickers only
python app/backtest/backtest_all.py --tickers NG.L BP.L

# Specific strategy groups
python app/backtest/backtest_all.py --groups Individual Improved

# With trailing stop
python app/backtest/backtest_all.py --trailing-pct 0.03

# Custom output paths
python app/backtest/backtest_all.py \
    --data-dir data/analysis-data \
    --output-dir data/reports/backtest \
    --results-file data/reports/custom_results.csv

# CSV only (no HTML reports)
python app/backtest/backtest_all.py --csv-only
```

## YAML Configuration

Customize which strategies to run with a YAML config file:

```yaml
# strategies: list of module names to run
strategies:
  - module: golden_cross
    label: "Golden Cross (Custom Label)"   # optional display name
  - module: bb_meanrev
  - module: trend_momentum

# custom_dir: relative path to directory containing .py strategy files
custom_dir: ../custom

# trailing_pct: trailing stop percentage (overrides CLI)
trailing_pct: 0.05
```

### Built-in Configs

| Config | Strategies | Use Case |
|---|---|---|
| `configs/default.yaml` | All 32 | Full evaluation |
| `configs/NG.L_optimized.yaml` | 10 mean-reversion | NG.L crude oil |
| `configs/trend_stock.yaml` | 17 trend-following | UK stock tickers |

## Custom Strategies

### Quick Start

1. **Copy the template** and rename it:
   ```bash
   cp app/backtest/custom/template_strategy.py app/backtest/custom/my_strategy.py
   ```

2. **Implement your strategy function** using the `@register_custom` decorator:
   ```python
   from framework.extensions import register_custom

   @register_custom("my_strategy")
   def my_strategy(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
       # Your logic here
       entries = df["ta_rsi14"] < 30          # Buy when oversold
       exits = df["ta_rsi14"] > 70            # Sell when overbought
       return entries.astype(int), exits.astype(int)
   ```

3. **Reference it in your YAML config**:
   ```yaml
   strategies:
     - module: my_strategy
       label: "My Oversold/Overbought"

   custom_dir: ../custom
   ```

4. **Run the backtest**:
   ```bash
   python app/backtest/run_backtest.py NG.L -c my_config.yaml
   ```

### Strategy Function Signature

Every strategy must be a function with this exact signature:

```python
def my_strategy(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    ...
    return entries, exits
```

- **`df`**: A pandas DataFrame containing OHLCV + TA columns from `data/analysis-data/{ticker}.csv`
- **Returns**: A tuple of two pandas Series of type `int`:
  - `entries`: `1` where you want to enter a long position, `0` otherwise
  - `exits`: `-1` where you want to exit, `0` otherwise

### Accessing TA Columns

All TA indicators use the `ta_` prefix. Common columns:

| Column | Indicator | Source Module |
|---|---|---|
| `ta_rsi14` | RSI (14) | momentum |
| `ta_macd_line` / `ta_macd_signal` / `ta_macd_hist` | MACD | momentum |
| `ta_ema20` / `ta_ema50` / `ta_ema200` | Exponential moving averages | trend |
| `ta_supertrend_direction` | SuperTrend signal (1=up, -1=down) | trend |
| `ta_bband_lower` / `ta_bband_middle` / `ta_bband_upper` | Bollinger Bands | volatility |
| `ta_atr14` | Average True Range (14) | volatility |
| `ta_obv` | On-Balance Volume | volume |
| `ta_cci20` | Commodity Channel Index (20) | momentum |
| `ta_roc20` | Rate of Change (20) | momentum |
| `ta_adx14` / `ta_di_plus` / `ta_di_minus` | ADX & Directional Indicators | trend |
| `ta_hmm_regime` | HMM regime (0/1/2) | regime |

See `app/calculate-ta/README.md` for the full column list.

### Example: RSI Bounce

```python
from framework.extensions import register_custom

@register_custom("rsi_bounce")
def rsi_bounce(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Buy when RSI crosses above 30 (emerging from oversold).
       Sell when RSI crosses below 50 (momentum fading).
    """
    rsi = df["ta_rsi14"]

    # RSI crossed above 30 today (was at or below 30 yesterday)
    entry = (rsi > 30) & (rsi.shift(1) <= 30)

    # RSI crossed below 50 today (was at or above 50 yesterday)
    exit_ = (rsi < 50) & (rsi.shift(1) >= 50)

    return entry.astype(int), exit_.astype(int)
```

### Example: Multi-Indicator Strategy

```python
@register_custom("multi_indicator_long")
def multi_indicator_long(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Trend + momentum confirmation entry."""
    # Trend: price above EMA50
    trend_up = df["ta_close"] > df["ta_ema50"]

    # Momentum: RSI rising but not overbought
    rsi_rising = (df["ta_rsi14"] > df["ta_rsi14"].shift(1)) & (df["ta_rsi14"] < 70)

    # Volume confirmation
    vol_ok = df["ta_volume"] > df["ta_volume"].rolling(20).mean() * 1.2

    entry = trend_up & rsi_rising & vol_ok
    exit_ = df["ta_rsi14"] > 80  # Sell on extreme overbought

    return entry.astype(int), exit_.astype(int)
```

### File Naming Convention

When a file (strategy, config, or custom script) is specific to a particular ticker, its name must follow this pattern:

```
{ticker}_{function}.py    # Python strategy or script
{ticker}_{function}.yaml  # YAML config file
```

**Rules:**

1. **`{ticker}`** — The ticker ID **in uppercase**, as it appears in `config/ticker_list.csv` and `data/analysis-data/`. For example: `LGEN.L`, `NG.L`, `BP.L`, `AZN.L`.
   - **Correct:** `LGEN.L_crash_protected.py`, `NG.L_backtest.py`
   - **Incorrect:** `lgen_crash_protected.py`, `ng_backtest.py`, `Lgen.L_strategy.py`
2. **`{function}`** — A short descriptive name of the file's purpose (lowercase, underscore-separated).
   - Examples: `backtest`, `optimized`, `crash_protected`, `exit_analysis`, `deep_analysis`
3. **Location:** Place ticker-specific scripts in `app/backtest/custom_scripts/`. Place ticker-specific custom strategies in `app/backtest/custom/`. Place ticker-specific YAML configs in `app/backtest/configs/`.

| File | Purpose | Correct Name |
|------|---------|-------------|
| Custom strategy for LGEN.L | Crash-protected mean reversion | `app/backtest/custom/LGEN.L_crash_protected.py` |
| Custom backtest script | Deep dive into LGEN.L exits | `app/backtest/custom_scripts/LGEN.L_exit_analysis.py` |
| YAML config | NG.L mean-reversion focused | `app/backtest/configs/NG.L_meanrev.yaml` |
| Custom script | AZN.L optimized parameters | `app/backtest/custom_scripts/AZN.L_optimized.py` |

**Note:** Built-in strategies (in `strategies/builtins.py`) are **ticker-agnostic** — they are not named with a ticker prefix. Only files that are **specific to a single ticker** (custom strategies, one-off scripts, per-ticker configs) should follow this naming convention.

### File Organization

- Custom strategies live in any directory specified by `custom_dir` in the YAML config or `--custom-dir` CLI flag
- Each `.py` file is imported once and its `@register_custom`-decorated functions are collected
- File names and function names are independent — only the decorator name matters for lookups
- Multiple files can register strategies with the same name; the last-loaded one wins

## Built-in Strategy Groups

The 32 built-in strategies are organized into groups:

| Group | Description | Count |
|---|---|---|
| **Individual** | Single-indicator or single-concept strategies | 15 |
| **Combinations** | Multi-factor combos combining trend, momentum, volume, structure | 3 |
| **Improved** | Refined versions of individual strategies with better filters | 11 |
| **NG.L Optimized** | Best-performing strategies tuned for NG.L crude oil | 3 |

### Group contents

**Individual strategies:**
`golden_cross`, `ema_pullback`, `supertrend_plus`, `donchian`, `bb_breakout`, `bb_meanrev`, `rsi_macd_rev`, `institutional`, `vwap`, `ofi`, `marketstruct`, `bos_breakout`, `choch`, `vol_expansion`, `hmm_regime`

**Combinations:**
`trend_momentum`, `vol_structure`, `score80`

**Improved:**
`bb_meanrev_upper`, `bb_meanrev_atr`, `vol_filtered_meanrev`, `regime_adaptive`, `short_meanrev`, `vol_breakout_rev`, `ema_pullback_vol`, `multiscore60`, `dual_exit_meanrev`, `macd_diverge`, `highprob_multi`

**NG.L Optimized:**
`bb_meanrev_optimized`, `bb_meanrev_entry2`, `rsi_macd_rev`

Run a specific group via CLI:
```bash
python app/backtest/backtest_all.py --groups Individual Improved
```

## Report Output

Reports are saved to `data/reports/backtest/{ticker}_backtest_report.html`.

### Report Tabs

1. **Summary** — All strategies ranked by the chosen metric (default: Total Return %), with a sortable table of all metrics.

2. **Equity Curves** — 1200×800px chart showing cumulative returns for the top strategies alongside a buy & hold benchmark (black dotted line). Drawdowns shown in a separate pane below.

3. **Metrics** — 1200×600px grouped bar chart comparing the top strategies across 6 key metrics: Total Return, Sharpe Ratio, Profit Factor, Win Rate, Max Drawdown, Total Trades.

4. **Best Strategy** — Summary stats of the top-ranked strategy plus a histogram of its trade P&L distribution.

### Report Customization

The report generator accepts these parameters:

```python
generate_report(
    results=results,       # list of metric dicts from engine.run_batch()
    df=df,                 # full OHLCV+TA DataFrame (for benchmark)
    ticker="NG.L",         # ticker symbol for titles
    output_dir="data/reports/backtest",
    top_n=15,              # strategies shown on charts
    sort_by="Total Return (%)",
    title="Custom Report Title",
)
```
