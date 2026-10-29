# Investment Strategy Skill

This skill defines a structured approach to formulating, investigating, evaluating, and backtesting investment strategies.

## Objective

Investigate and recommend the best investment strategy (maximum return / minimum drawdown) for `{ticker}` based on `{year}` of market data. Create and evaluate custom strategies when built-in ones are insufficient. Output findings to `data/reports/strategies/{ticker}/{latest_date}.md`, where `{latest_date}` is the last date in the market data CSV (formatted `YYYY-MM-DD`).

## Parameters

- `{ticker}` — Ticker symbol (e.g. `NG.L`, `BP.L`, `HSBA.L`). Look up data at `data/analysis-data/{ticker}.csv`.
- `{year}` — Number of years of lookback data. Default: 10. Set cutoff date as `pd.Timestamp("YYYY-MM-DD")` where YYYY-MM-DD is `{current_date}` minus `{year}` years.
- `{latest_date}` — The last date in `data/analysis-data/{ticker}.csv` (`df["Date"].max()`), formatted `YYYY-MM-DD`. Used as the date component in the output filename.

## Running Python Code

**All code blocks in this skill are reference examples.** To execute any Python code, use the **`shell` tool** — never the `execute` (Code Mode) tool, as Code Mode does not support `import` statements.

### Preferred approach: Use `run_backtest_analysis.py` (primary) or `run_strategy_backtest.py` (backtest-only)

**Two portable helper scripts handle all path resolution and work from any working directory (including `/tmp/`). Avoid writing ad-hoc Python scripts with relative imports.**

#### Primary: `run_backtest_analysis.py` — All-in-one analysis

This is the **recommended entry point** for Phase 2 analysis. It combines data snapshot, indicators, forward returns, yearly performance, AND backtest results in a single JSON output:

```bash
# Full analysis: data snapshot + all built-in strategies (recommended for Phase 2)
python app/backtest/run_backtest_analysis.py {ticker} --cutoff YYYY-MM-DD --json --no-report

# Data snapshot only (no backtest) — fast, for Phase 1
python app/backtest/run_backtest_analysis.py {ticker} --no-backtest --json

# Forward returns stats only
python app/backtest/run_backtest_analysis.py {ticker} --forward-returns

# Yearly performance only
python app/backtest/run_backtest_analysis.py {ticker} --yearly

# Include custom strategies
python app/backtest/run_backtest_analysis.py {ticker} --cutoff YYYY-MM-DD --custom NG.L_custom --json --no-report

# Only a specific strategy group
python app/backtest/run_backtest_analysis.py {ticker} --group mean-reversion --json --no-report
```

> **Why prefer this script?** It replaces separate calls to `get_evaluation_data.py` + `run_strategy_backtest.py` — giving you metadata, indicators, forward returns, yearly performance, AND backtest results in one JSON output.
>
> **⚠️ `--dry-run` does NOT exist on this script.** To preview strategies without running backtests, use `--list` on `run_strategy_backtest.py` or `--no-backtest` on `run_backtest_analysis.py` for data-only output.

#### Secondary: `run_strategy_backtest.py` — Backtest-only

For focused backtest runs without the data snapshot overhead:

```bash
# List available strategies WITHOUT running a backtest (NEW — use this first!)
python app/backtest/run_strategy_backtest.py {ticker} --list
python app/backtest/run_strategy_backtest.py {ticker} --list --custom ba_defense_meanrev

# All built-in strategies
python app/backtest/run_strategy_backtest.py {ticker}

# With custom cutoff
python app/backtest/run_strategy_backtest.py {ticker} --cutoff YYYY-MM-DD

# With specific custom strategies (by module file name — NOT strategy name, NOT truncated)
python app/backtest/run_strategy_backtest.py {ticker} --custom ba_defense_meanrev

# Multiple custom modules
python app/backtest/run_strategy_backtest.py {ticker} --custom ba_defense_meanrev ba_regime_filter

# Combine built-ins + custom
python app/backtest/run_strategy_backtest.py {ticker} --custom ba_defense_meanrev --cutoff 2016-10-26

# JSON output for programmatic consumption
python app/backtest/run_strategy_backtest.py {ticker} --cutoff YYYY-MM-DD --json

# Skip HTML report generation
python app/backtest/run_strategy_backtest.py {ticker} --no-report

# Only built-in strategies (no custom)
python app/backtest/run_strategy_backtest.py {ticker} --builtins-only

# Only strategies matching a group name
python app/backtest/run_strategy_backtest.py {ticker} --group mean-reversion
```

> **⚠️ IMPORTANT — `--custom` takes module file names, not strategy names:**
> - File: `ba_defense_meanrev.py` → CLI: `--custom ba_defense_meanrev` (NOT `--custom ba_defense`, NOT `--custom signal_ba_defense_meanrev`)
> - Use `--list` before running to verify the module names are correct
> - `--dry-run` does **NOT** exist on this script — use `--list` instead

> **Why use the helpers?** Both scripts resolve all import paths from their own location, so they work whether you run them from the project root, `/tmp/`, or anywhere else. No `sys.path` hacks needed. The `_NumpyEncoder` in `run_backtest_analysis.py` ensures numpy int64/floating values serialize correctly to JSON.

### When you must write custom Python code

If you need more control than the CLI provides, use one of these patterns:

```bash
# Option A: Inline with python -c (short scripts)
python -c "
import pandas as pd
from app.backtest.framework.engine import BacktestEngine
engine = BacktestEngine('data/analysis-data/NG.L.csv', cutoff_date=pd.Timestamp('2016-10-26'))
results = engine.run_batch(signal_fns={'golden_cross': golden_cross})
print(len(results), 'strategies ran')
"

# Option B: Write a script and run it (recommended for longer code)
# 1. Use the `write` tool to create a temporary script, e.g. /tmp/_run_backtest.py
# 2. Use the `shell` tool: python /tmp/_run_backtest.py
# 3. Delete the script after: rm /tmp/_run_backtest.py
```

When writing ad-hoc scripts, **always** add these path imports at the top:
```python
import sys
from pathlib import Path

# Resolve project root from script location — works from any CWD
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR  # or parent of project root if script is nested
sys.path.insert(0, str(_PROJECT_ROOT))

# NOW imports work
from app.backtest.framework.engine import BacktestEngine
from app.backtest.strategies.builtins import STRATEGIES
```

### What NOT to do

- **Do NOT** try to run Python code blocks directly in Code Mode (`execute`) — it will fail with `SyntaxError: Imports and exports aren't supported`
- **Do NOT** use `execute` for any code containing `import`, `from ... import`, or `open()`
- **Do NOT** use `execute` for code that imports `pandas`, `vectorbt`, `numpy`, or any project module
- **Do NOT** write ad-hoc scripts that rely on relative imports without adding project root to `sys.path` — always use the helper script when possible

---

## Data Retrieval with `get_evaluation_data.py`

All data retrieval for this skill should use the helper script:
```bash
python app/analyse-market-data/get_evaluation_data.py {ticker} [date] [options]
```

> **Note:** `get_evaluation_data.py` **outputs JSON by default** — no `--json` flag needed. The `--json` flag is accepted as a no-op alias for compatibility with other backtest scripts (e.g. `run_backtest_analysis.py`, `run_strategy_backtest.py`). Similarly, `--no-report` is a no-op since no HTML is generated.

### Essential commands

| Command | Purpose |
|---------|---------|
| `get_evaluation_data.py {ticker}` | Latest snapshot: OHLCV, all indicators, metadata (52w range, company name) |
| `get_evaluation_data.py {ticker} --cutoff YYYY-MM-DD` | Same but truncated to cutoff date (for backtest alignment) |
| `get_evaluation_data.py {ticker} --cutoff YYYY-MM-DD --latest-30` | Snapshot + last 30 rows context (regime changes, recent price action) |
| `get_evaluation_data.py {ticker} --full-df --cutoff YYYY-MM-DD` | Full DataFrame as JSON rows (for programmatic use in Python) |
| `get_evaluation_data.py {ticker} --ohlcv --cutoff YYYY-MM-DD` | OHLCV rows as list of dicts (for VectorBT portfolio creation) |
| `get_evaluation_data.py {ticker} --forward-returns` | Forward return statistics (5d/10d/20d) for Phase 1 asset classification |
| `get_evaluation_data.py {ticker} --yearly --cutoff YYYY-MM-DD` | Year-by-year buy-and-hold performance for Phase 6 |
| `get_evaluation_data.py {ticker} --list-columns` | All available columns grouped by category |
| `get_evaluation_data.py {ticker} --custom-strategies` | **Discover custom strategies for this ticker** — returns JSON with relevant module names |

### Typical usage in Python (Phase 1 data loading)

```python
import subprocess, json

result = subprocess.run([
    "python", "app/analyse-market-data/get_evaluation_data.py",
    "NG.L", "--cutoff", "2016-10-26"
], capture_output=True, text=True)
data = json.loads(result.stdout)

# Metadata
company = data["company_name"]       # "National Grid"
sector = data["sector"]              # "Utilities"
date_range = data["date_range"]      # {"start": "...", "end": "..."}

# Latest indicators (at cutoff date)
indicators = data["indicators"]      # {ta_rsi14: 45.2, ta_ema20: 1150.3, ...}
latest = data["latest"]              # {date: "...", close: 1150.0, ...}

# Full DataFrame for backtesting
result = subprocess.run([
    "python", "app/analyse-market-data/get_evaluation_data.py",
    "NG.L", "--cutoff", "2016-10-26", "--full-df"
], capture_output=True, text=True)
full_data = json.loads(result.stdout)
df = pd.DataFrame(full_data["data"])
```

### Typical usage in Python (Phase 5: custom strategy backtest)

```python
import subprocess, json
import pandas as pd
import vectorbt as vbt
from app.backtest.framework.engine import INITIAL_CAPITAL, COMMISSION, SLIPPAGE
from vectorbt.portfolio.enums import SizeType

# Get OHLCV data for VectorBT
result = subprocess.run([
    "python", "app/analyse-market-data/get_evaluation_data.py",
    "NG.L", "--cutoff", "2016-10-26", "--ohlcv"
], capture_output=True, text=True)
ohlcv = json.loads(result.stdout)

# Build Series for VectorBT
close = pd.Series(
    [d["close"] for d in ohlcv["ohlcv"]],
    index=pd.to_datetime([d["date"] for d in ohlcv["ohlcv"]]),
)

# Apply custom strategy signals
entry = (close < close.rolling(20).mean() * 0.98) & (close.pct_change().shift(1) < -0.03)
exit_ = (close > close.rolling(20).mean() * 1.02) | (close.pct_change().shift(1) > 0.05)

pf = vbt.Portfolio.from_signals(
    close=close,
    entries=entry.astype(int),
    exits=exit_.astype(int) * -1,
    init_cash=INITIAL_CAPITAL,
    freq="1D",
    slippage=SLIPPAGE,
    size=1.0,
    size_type=SizeType.Percent,
    fees=COMMISSION,
)
```

### Typical usage in Python (Phase 6: year-by-year comparison)

```python
result = subprocess.run([
    "python", "app/analyse-market-data/get_evaluation_data.py",
    "NG.L", "--cutoff", "2026-10-28", "--yearly"
], capture_output=True, text=True)
yearly = json.loads(result.stdout)["yearly_performance"]
# yearly is a list of dicts: [{"year": 2020, "return_pct": 12.3, ...}, ...]
```

## Strategy Types

Trend following · Mean reversion · Momentum · Contrarian · Dividend income · Breakout

## Pre-flight: Resolve Ticker Identity

**Before any analysis, resolve the ticker to its real company name and sector.**

1. Run `get_evaluation_data.py` which auto-resolves from `config/ticker_list.csv`:
   ```bash
   python app/analyse-market-data/get_evaluation_data.py {ticker}
   ```
   The output includes `company_name` and `sector` — these are the **authoritative** identifiers.
2. **NEVER guess** what a ticker represents based on its symbol alone (e.g. `NG.L` is **National Grid**, not "Natural Gas"; `BP.L` is **BP**, not "Bond Pricing")
3. Use the resolved company name throughout the report instead of the raw ticker symbol where narrative context is needed
4. **Constraint:** If `company_name` is `null` in the output, the ticker is not found in `config/ticker_list.csv` — note this as a data issue and proceed with the ticker symbol only — do not fabricate a company name.

## Directory Quick Reference

| Directory | Purpose | Naming convention | Example |
|-----------|---------|-------------------|---------|
| `app/backtest/custom/{ticker}/` | Strategy module files (registered with `@register_custom`) — per-ticker subdirectories | `{function}.py` | `meanrev.py` |
| `app/backtest/custom_scripts/` | One-off analysis / backtest scripts | `{Ticker}_{function}.py` | `NG.L_backtest.py` |
| `app/backtest/configs/` | Per-ticker YAML configs | `{Ticker}_{function}.yaml` | `NG_L_optimized.yaml` |

## Relevant Files Reference

| File | Purpose |
|------|---------|
| `app/backtest/framework/engine.py` | `BacktestEngine` class, signal resolution, `run_batch()` |
| `app/backtest/framework/signal.py` | `SignalBase` ABC, helper functions (`_rising`, `_falling`, `_bullish_cross`, etc.) |
| `app/backtest/framework/metrics.py` | `calculate_metrics()`, `pick_best()`, `rank_strategies()`, `summarize_table()` |
| `app/backtest/framework/extensions.py` | `@register_custom` decorator, `load_custom_strategies()`, `validate_custom_strategies()` |
| `app/backtest/framework/report.py` | `generate_report()` — creates HTML backtest reports |
| `app/backtest/strategies/builtins.py` | 32 built-in strategies across 4 groups, `STRATEGIES` registry, `STRATEGY_LABELS`, `STRATEGY_GROUPS` |
| `app/backtest/run_backtest.py` | CLI entry point (`python app/backtest/run_backtest.py {ticker} --cutoff YYYY-MM-DD`) |
| `app/backtest/run_backtest_analysis.py` | **Primary helper — works from ANY directory** — combines data snapshot, indicators, forward returns, yearly performance, AND backtest results in one JSON. Recommended for Phase 2. |
| `app/backtest/run_strategy_backtest.py` | **Portable backtest-only helper** — handles all path resolution, outputs JSON. Use for focused backtest runs. |
| `app/backtest/custom/template_strategy.py` | Template for custom strategies (copy into ticker subdirectory) |
| `app/backtest/custom_scripts/NG.L_backtest.py` | NG.L-focused reference (32 strategies, optimization notes) |
| `docs/all_technical_analysis.md` | Complete TA indicator reference (all 12 sections, 1268 lines) |
| `data/analysis-data/{ticker}.csv` | Input data: OHLCV + all `ta_` prefixed columns + P/E data |

## Built-in Strategy Groups (32 total)

1. **Individual (17):** `golden_cross`, `ema_pullback`, `supertrend_plus`, `donchian`, `bb_breakout`, `bb_meanrev`, `rsi_macd_rev`, `institutional`, `vwap`, `ofi`, `marketstruct`, `bos_breakout`, `choch`, `vol_expansion`, `hmm_regime`, `momentum_comp`, `highprob_multi`
2. **Combinations (3):** `trend_momentum`, `vol_structure`, `score80`
3. **Improved (10):** `bb_meanrev_upper`, `bb_meanrev_atr`, `vol_filtered_meanrev`, `regime_adaptive`, `short_meanrev`, `vol_breakout_rev`, `ema_pullback_vol`, `multiscore60`, `dual_exit_meanrev`, `macd_divergence_rev`
4. **NG.L Optimized (2):** `bb_meanrev_optimized`, `bb_meanrev_entry2`

## TA Column Reference

All TA columns use the `ta_` prefix. **Always verify columns with** `get_evaluation_data.py {ticker} --list-columns` **before referencing them.** Key columns (full list in `docs/all_technical_analysis.md`):

| Category | Key Columns |
|----------|-------------|
| Trend | `ta_ema20`, `ta_ema50`, `ta_ema200`, `ta_supertrend_direction`, `ta_ma20_slope`, `ta_ma50_slope`, `ta_ma200_slope`, `ta_donchian_upper/lower`, `ta_keltner_upper/lower`, `ta_adx14`, `ta_aroon_up/down` |
| Momentum | `ta_rsi14`, `ta_macd_line`, `ta_macd_signal`, `ta_macd_histogram`, `ta_roc20`, `ta_williams_r`, `ta_cci`, `ta_tsi`, `ta_rsi_zscore`, `ta_rsi_percentile`, `ta_mfi14`, `ta_stoch_k/d` |
| Volume | `ta_obv`, `ta_cmf`, `ta_vwap`, `ta_ofi`, `ta_adl`, `ta_emv14`, `ta_volume_osc`, `ta_volume_zscore`, `ta_volume_percentile`, `ta_log_volume` |
| Volatility | `ta_atr14`, `ta_normalized_atr14`, `ta_bband_upper/middle/lower`, `ta_bband_width`, `ta_bband_pctb`, `ta_hvol20`, `ta_parkinson_vol`, `ta_garch_vol`, `ta_atr_stop_dist`, `ta_atr_percentile` |
| Regime | `ta_hmm_regime_prob_0/1/2`, `ta_hmm_regime`, `ta_regime_label` |
| Structure | `ta_swing_high/low`, `ta_hh`, `ta_hl`, `ta_lh`, `ta_ll`, `ta_bos`, `ta_choch`, `ta_nearest_resistance/support`, `ta_trend` |
| Return | `ta_return_5d/10d/20d`, `ta_performance_1m/3m/6m/1y`, `ta_alpha20`, `ta_beta20`, `ta_rs_ftse100` |
| Fundamentals | `ta_pe`, `ta_eps_ttm`, `ta_div_ttm`, `ta_div_yield` |
| Time | `weekday` |

### Weekday Effect (day-of-week)

`weekday` column: day of week from Date index, `0=Monday … 4=Friday, 5=Saturday, 6=Sunday`.

| Day | Behaviour | Strategy action |
|-----|-----------|-----------------|
| Monday | Weekend news gaps down | Potential dip-buying if fundamentals solid |
| Tuesday | Low volatility | Ideal entry day for new positions |
| Wednesday | Mid-week profit-taking | Watch for reversals |
| Thursday | Options expiry volatility (where applicable) | Caution on wide stops |
| Friday | Pre-weekend risk | Reduce exposure or exit before weekend |
| Sat/Sun | No trading | N/A — gaps priced in Monday open |

## Methodology

### Phase 1: Data Preparation & Understanding

1. Get the full data snapshot via `get_evaluation_data.py`:
   ```bash
   python app/analyse-market-data/get_evaluation_data.py {ticker} --cutoff YYYY-MM-DD
   ```
   This gives you: company name, sector, date range, row count, OHLCV, all indicators, and 52-week range.
2. Check forward returns statistics:
   ```bash
   python app/analyse-market-data/get_evaluation_data.py {ticker} --forward-returns
   ```
3. Verify available columns:
   ```bash
   python app/analyse-market-data/get_evaluation_data.py {ticker} --list-columns
   ```
4. **Use the resolved company name** from the Pre-flight step — e.g. "National Grid (NG.L) is a regulated UK utility…" not "NG.L is a commodity…"
5. Examine forward returns (`ta_return_5d`, `ta_return_10d`, `ta_return_20d`) and past performance (`ta_performance_1m`, `ta_performance_3m`, `ta_performance_6m`, `ta_performance_1y`) to understand the asset's behavior
6. Look at P/E data for valuation context (check if `ta_pe`, `ta_eps_ttm` are populated)
7. Determine asset characteristics from the return data:
   - Is it trending (strong directional moves)? → favor trend-following strategies
   - Is it mean-reverting (oscillates around a range)? → favor mean-reversion strategies
   - Is it volatile with wide swings? → favor volatility-based strategies
   - Is it low-vol with range-bound? → favor conservative mean-reversion
8. **Contextualize the asset type** using the resolved company name and sector (e.g. "National Grid is a regulated utility, not a commodity — mean-reversion strategies designed for commodities do not directly apply")

### Phase 2: Baseline Strategy Evaluation

Run all 32 built-in strategies. **Use `run_backtest_analysis.py` as the primary entry point** — it returns data snapshot + backtest results in one JSON output:

```bash
# Primary: data snapshot + backtest results (recommended for Phase 2)
python app/backtest/run_backtest_analysis.py {ticker} --cutoff YYYY-MM-DD --json --no-report

# Alternative: backtest-only (faster, no data snapshot)
python app/backtest/run_strategy_backtest.py {ticker} --cutoff YYYY-MM-DD --json --no-report

# Specific group only
python app/backtest/run_strategy_backtest.py {ticker} --cutoff YYYY-MM-DD --group mean-reversion --json --no-report
```

Or use the original CLI:
```bash
python app/backtest/run_backtest.py {ticker} --cutoff YYYY-MM-DD
```

Alternatively, run the framework programmatically (preferred for collecting metrics). Load data via `get_evaluation_data.py` and pass the file path to the engine:

```python
import subprocess, json, pandas as pd

# Get the data file path via the helper script
result = subprocess.run([
    "python", "app/analyse-market-data/get_evaluation_data.py",
    "{ticker}", "--cutoff", "2016-10-26"
], capture_output=True, text=True)
data = json.loads(result.stdout)

from app.backtest.framework.engine import BacktestEngine
from app.backtest.framework.metrics import summarize_table
from app.backtest.strategies.builtins import STRATEGIES, STRATEGY_LABELS

# BacktestEngine reads the CSV internally — pass file path and cutoff_date to __init__
engine = BacktestEngine(
    "data/analysis-data/{ticker}.csv",   # file path string (NOT a DataFrame)
    cutoff_date=pd.Timestamp("2016-10-26")
)

# run_batch() takes a dict[str, Callable] mapping strategy name → signal function
# STRATEGIES is already a dict[str, Callable] from builtins.py
results = engine.run_batch(signal_fns=STRATEGIES)

# summarize_table() uses the DataFrame index for strategy names — set 'Strategy' column as index
df_results = pd.DataFrame(results).set_index('Strategy')
print(summarize_table(df_results))
```

> **Important:**
> - `BacktestEngine` takes a **file path string** (`str` or `Path`), not a DataFrame. It loads the CSV internally.
> - Pass `cutoff_date` to `__init__`, not as a separate argument.
> - `run_batch(signal_fns=...)` takes a **single dict** mapping strategy name → signal function. There are no `tickers`, `cutoff`, or `ticker_names` parameters. The engine already knows which ticker data to use from `data_path`.
> - `summarize_table(df)` uses the **DataFrame index** for strategy names. Always call `pd.DataFrame(results).set_index('Strategy')` first — the results dict has a "Strategy" column but a default integer index.

**Record results in `data/reports/strategies/{ticker}/{latest_date}.md`:**

For each strategy, capture:
- Strategy name (key from `STRATEGIES`) and label (from `STRATEGY_LABELS`)
- Total Return (%), Sharpe Ratio, Max Drawdown (%), Profit Factor
- Win Rate (%), Total Trades
- Rank position (by Total Return descending, then Profit Factor, then Min Drawdown)

### Phase 3: Strategy Deep Dive — Top 5

Select the top 5 strategies by performance (balanced: return + risk). For each:

1. Read the source code in `app/backtest/strategies/builtins.py` to understand the logic
2. **Strategy functions use `signal_` prefix:** The function names are `signal_bb_meanrev`, `signal_golden_cross`, etc. — **NOT** bare names like `bb_meanrev` or `golden_cross`. Use `grep "def signal_bb_meanrev"` or `grep "^def signal_"` to find them.
3. Analyze entry/exit conditions and their rationale
4. Check which TA columns they use — verify those indicators are relevant for this ticker
5. Note edge cases (e.g., strategies that use HMM regime but that ticker may not have regime data)

### Phase 4: Custom Strategy Creation (if needed)

If no built-in strategy achieves satisfactory results, or if a specific pattern is evident from the data:

1. First, discover which custom strategies already exist for your ticker:
   ```bash
   python app/analyse-market-data/get_evaluation_data.py {ticker} --custom-strategies
   ```
   This returns a JSON with `custom_strategies` grouped by ticker — e.g. `"BA.L": ["ba_defense_meanrev", "ba_regime_filter_meanrev", ...]`.
2. Copy `app/backtest/custom/template_strategy.py` to `app/backtest/custom/{ticker}/{custom_name}.py` (create the ticker subdirectory if needed)
3. Create a new signal function with `@register_custom("custom_name")` decorator
4. Function signature: `def custom_name(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]`
5. Return entries (int 1s) and exits (int -1s)
6. Reference TA columns via `df["ta_column_name"]`
7. Test with `--list` on `run_strategy_backtest.py` to verify loading, then full backtest

**Loading custom strategies programmatically:**

```python
# The load_custom_strategies function is now portable — works from any CWD.
# No sys.path manipulation needed.
from app.backtest.framework.extensions import load_custom_strategies

# CORRECT: pass a DIRECTORY path, not a file path
# The ticker parameter filters to modules for the given ticker (case-insensitive)
custom = load_custom_strategies("app/backtest/custom", ticker="NG.L")
print("Loaded strategies:", list(custom.keys()))

# To load only specific module files:
custom = load_custom_strategies(
    "app/backtest/custom",
    module_names=["sbry_bb"],
    ticker="SBRY.L"   # also filters by ticker prefix
)
```

> **IMPORTANT — `load_custom_strategies` is now portable:**
> - The internal `_resolve_framework_import()` function finds the project root from `__file__`, so it works from any working directory (including `/tmp/`).
> - No need to add project root to `sys.path` before calling it.
> - The shared `_custom_registry` is correctly linked across all import paths.

> **CRITICAL — Do NOT load all custom strategies at once:**
> - There are 20+ custom strategy files covering 10+ different tickers. Loading them all produces 100+ irrelevant strategies.
> - **Always load only strategies relevant to the target ticker.**
> - **Step 1:** Discover relevant custom strategies: `python app/analyse-market-data/get_evaluation_data.py {ticker} --custom-strategies`
> - **Step 2:** Use the discovered module names with `--list` to verify: `python app/backtest/run_strategy_backtest.py {ticker} --list --custom {module1} {module2}`
> - **Step 3:** Pass those module file names via `module_names=["ba_defense_meanrev", "ba_regime_filter"]` to `load_custom_strategies()`.
> - Generic strategies (not ticker-specific) can be loaded separately if needed.

> **IMPORTANT — `load_custom_strategies` gotcha:**
> - **Always pass a directory path**, never a file path. The function globs for `*.py` files inside the directory.
> - It **clears the registry first** (`_custom_registry.clear()`), then loads all `.py` files from the directory.
> - Only files with functions decorated by `@register_custom()` will appear in the returned dict.
> - Files without `@register_custom` decorators are loaded (for side effects) but contribute no strategies.
> - If a custom strategy doesn't appear in results, check: (1) is it in the custom/ directory? (2) does it have `@register_custom("name")`? (3) are the import paths correct (`from framework.extensions import register_custom`)?

**Common custom strategy patterns to try:**

- **Trend + Volume confirmation:** Combine EMA alignment with volume indicators (OBV rising, CMF > 0)
- **Mean reversion with volatility filter:** BB Lower + RSI < 30 + GARCH vol filter (avoid catching falling knives)
- **Regime-adaptive:** Switch between trend-following and mean-reversion based on HMM regime probability
- **Multi-signal scoring:** Weighted score system across trend, momentum, volume, structure, and regime signals
- **ATR-based trailing exit:** Use ATR multiples for dynamic exit instead of fixed band/indicator exits
- **Dual-exit strategy:** Combine indicator-based exit with ATR trailing stop for better risk management

### Phase 5: Parameter Optimization

For promising custom strategies, test multiple parameter variants. Load data via `get_evaluation_data.py` (or use `BacktestEngine` which reads the same file):

```python
import subprocess, json
import pandas as pd
import vectorbt as vbt
from app.backtest.framework.engine import INITIAL_CAPITAL, COMMISSION, SLIPPAGE
from vectorbt.portfolio.enums import SizeType

# Option A: Use BacktestEngine (preferred — reads the same CSV)
from app.backtest.framework.engine import BacktestEngine

engine = BacktestEngine("data/analysis-data/NG.L.csv", cutoff_date=pd.Timestamp("2016-10-26"))
df = engine.load_data()

# Option B: Use get_evaluation_data.py output directly
result = subprocess.run([
    "python", "app/analyse-market-data/get_evaluation_data.py",
    "NG.L", "--cutoff", "2016-10-26", "--ohlcv"
], capture_output=True, text=True)
ohlcv_data = json.loads(result.stdout)
close = pd.Series(
    [d["close"] for d in ohlcv_data["ohlcv"]],
    index=pd.to_datetime([d["date"] for d in ohlcv_data["ohlcv"]]),
)

# Apply signals and backtest
for atr_mult in [2.0, 3.0, 4.0, 5.0]:
    highest_close = df["Close"].rolling(5).max()
    atr_trail = highest_close - atr_mult * df["ta_atr14"]
    entry = (df["Close"] <= df["ta_bband_lower"]) & (df["ta_rsi14"] < 30)
    exit_ = (df["Close"] < atr_trail) | (df["Close"] >= df["ta_bband_middle"])
    
    pf = vbt.Portfolio.from_signals(
        close=df["Close"],
        entries=entry.astype(int),
        exits=exit_.astype(int) * -1,
        init_cash=INITIAL_CAPITAL,
        freq="1D",
        slippage=SLIPPAGE,
        size=1.0,
        size_type=SizeType.Percent,
        fees=COMMISSION
    )
    
    # CORRECT way to get trade count and metrics:
    total_trades = pf.stats()["Total Trades"]          # or pf.trades.count()
    total_return = pf.total_return()
    sharpe = pf.sharpe_ratio()
    max_dd = pf.max_drawdown()
    win_rate = pf.win_rate()
    profit_factor = pf.profit_factor()
    
    print(f"ATR{atr_mult}x: Return={total_return:.2%}, Trades={total_trades}, Sharpe={sharpe:.2f}")
```

Run each variant and compare. Use `pick_best()` from `metrics.py` for automated ranking.

> **IMPORTANT — VectorBT API gotchas:**
> - **Trade count**: Use `pf.stats()["Total Trades"]` or `pf.trades.count()`. **NOT** `pf.trades().total()` (trades is an object, not a callable) and **NOT** `pf.trades.total` (no such attribute).
> - **Portfolio creation**: Always pass `freq="1D"` for daily data so Sharpe/Calmar/Omega ratios compute correctly.
> - **Signal types**: Entries and exits must be `int` Series (1 for entry, -1 for exit). Use `.astype(int)`.
> - **Size type**: Use `SizeType.Percent` with `size=1.0` for full-capital allocation.
> - **Constants**: `INITIAL_CAPITAL=100000`, `COMMISSION=0.001`, `SLIPPAGE=0.001` (import from `app.backtest.framework.engine`).

### Phase 6: Final Recommendation

Compile findings into a recommendation:

1. **Best overall strategy** — highest risk-adjusted return (Sharpe or Calmar)
2. **Highest return strategy** — maximum total return (accepting higher drawdown)
3. **Lowest drawdown strategy** — maximum capital preservation
4. **Best custom strategy** — if any custom strategy outperforms built-ins
5. **Recommended entry/exit rules** — the logic behind the top pick
6. **Risk considerations** — conditions where the strategy may fail

## Output Report Format

Write the report to `data/reports/strategies/{ticker}/{latest_date}.md`. Structure:

```markdown
# Investment Strategy Report: {Company Name} ({ticker})

## Executive Summary
- **Company:** {Company Name} ({ticker})
- **Sector:** {Sector from config/ticker_list.csv}
- **Analysis Period:** {year} years
- **Best Overall:** {strategy_name} — {return}% return, {sharpe} Sharpe, {drawdown}% drawdown
- **Highest Return:** {strategy_name} — {return}% return
- **Lowest Drawdown:** {strategy_name} — {drawdown}% max drawdown
- **Recommended:** {strategy_name}

## Data Summary
- Date range: {start_date} to {end_date}
- Rows: {count}
- Asset type: {Sector} stock — {brief description based on company name, e.g. "regulated utility" / "pharmaceutical" / "banking"}
- Asset characteristics: {trending / mean-reverting / volatile / range-bound}

## Phase 1: Data Analysis
- Forward return statistics
- Past performance summary
- P/E valuation context
- Asset behavior classification
- **Sector-appropriate analysis:** {interpret findings in the context of the company's sector — e.g. "National Grid as a regulated utility has stable cash flows but limited growth upside, making mean-reversion more appropriate than aggressive trend-following"}

## Phase 2: Baseline Results (All 32 Built-in Strategies)
| Rank | Strategy | Label | Return% | Sharpe | Max DD% | Profit Factor | Win Rate% | Trades |
|------|----------|-------|---------|--------|---------|---------------|-----------|--------|
| 1 | ... | ... | ... | ... | ... | ... | ... | ... |

## Phase 3: Top 5 Strategy Deep Dive
### 1. {strategy_name} — {label}
- **Logic:** {description from source code}
- **Entry conditions:** {bullet list}
- **Exit conditions:** {bullet list}
- **Results:** {metrics}
- **Analysis:** {why it worked for this ticker}

## Phase 4: Custom Strategies
### {custom_strategy_name}
- **Logic:** {description}
- **Entry/Exit rules:** {bullet list}
- **Results:** {metrics}
- **Improvements over built-ins:** {analysis}

## Phase 5: Parameter Optimization
### {custom_strategy_name} — Variant Analysis
| Variant | Return% | Sharpe | Max DD% | Notes |
|---------|---------|--------|---------|-------|

## Phase 6: Final Recommendation
- **Best overall:** {strategy} with rationale
- **Entry rules:** {exact conditions}
- **Exit rules:** {exact conditions}
- **Risk management:** {position sizing, stop loss, max holding period}
- **When it fails:** {market conditions where this strategy underperforms}
- **Suggested improvements:** {ideas for further refinement}

## Year-by-Year Performance
Compare Buy-and-Hold benchmark against the top 5 strategies using per-strategy yearly performance data. Get ALL strategy yearly returns in one call:
```bash
python app/backtest/run_strategy_backtest.py {ticker} --yearly --cutoff YYYY-MM-DD --json --no-report
```
This returns JSON with `yearly_performance` — an array of per-strategy objects, each containing `strategy` name and a `years` array with `year`, `start_date`, `end_date`, `start_net_value`, `end_net_value`, and `return_pct`. Strategies are sorted by last year's return descending.

For buy-and-hold baseline only, use:
```bash
python app/analyse-market-data/get_evaluation_data.py {ticker} --cutoff YYYY-MM-DD --yearly
```

| Year | Buy & Hold | {strategy_1} | {strategy_2} | {strategy_3} | {strategy_4} | {strategy_5} |
|------|------------|--------------|--------------|--------------|--------------|--------------|
| 20XX | {return}%  | {return}%    | {return}%    | {return}%    | {return}%    | {return}%    |

**Key observations per year:**
- Highlight years where strategies diverged significantly from Buy-and-Hold
- Note crash years where crash-protected / mean-reversion strategies outperformed
- Note recovery years where trend-following strategies caught up
- Bold the best-performing strategy per row (or the crash-protected one in crash years)
```

## Token Limit Handling

When writing the report to `data/reports/strategies/{ticker}/{latest_date}.md`, follow this **exact 6-step write pattern** to avoid output truncation:

### Step-by-step report writing

**Step 1 — Create file with header + executive summary (~150 words)**
```python
# First call: use write() to create the file
content = """# Investment Strategy Report: {Company} ({ticker})

## Executive Summary
- Company: ...
- Best Overall: ...
- Recommended: ...
"""
```

**Step 2 — Append Phase 1 (Data Analysis, ~200 words)**
```python
# Second call: use edit() to insert after Executive Summary
```

**Step 3 — Append Phase 2 (Baseline Results table, ~300 words)**
```python
# Third call: use edit() to insert after Phase 1
```

**Step 4 — Append Phase 3 (Top 5 Deep Dive, ~500 words)**
```python
# Fourth call: use edit() to insert after Phase 2
```

**Step 5 — Append Phase 4–6 + Year-by-Year (~600 words)**
```python
# Fifth call: use edit() to insert after Phase 3
```

**Step 6 — Verify file completeness**
```bash
wc -l data/reports/strategies/{ticker}/{latest_date}.md
# Should be ~100–200 lines total
# Check the last few lines are not truncated
tail -5 data/reports/strategies/{ticker}/{latest_date}.md
```

### Critical rules to avoid truncation

1. **Never attempt a single `write()` for the full report.** The full report (~2000 words) will exceed output limits.
2. **Each `write()` or `edit()` call should handle ≤ 350 words** — headers, one phase, or one table.
3. **Use `write()` only for Step 1** (create file). Use `edit()` for all subsequent steps.
4. **Use `edit(oldString)` to find an existing heading** and insert the new section after it. Example:
   ```
   oldString: "## Phase 1: Data Analysis\n"
   newString: "## Phase 1: Data Analysis\n- Content here...\n\n## Phase 2: Baseline Results\n"
   ```
5. **For tables, write the full table markdown in one `edit()` call** — tables are dense but compact.
6. **If you see "output was too long" or truncation**, stop immediately — the file is incomplete. Delete it and restart with smaller chunks.
7. **Never use `echo >> file` or shell append** — always use the `edit` tool for reliability.

## Strategy Design Reference

These are design targets for custom strategies — encode the desired behavior in your entry/exit signals.

### Position Sizing
- Risk no more than 2% of portfolio per trade
- Use ATR-based stop distances (e.g., 2×ATR)
- Scale into positions on confirmation signals

### Exit Rules
- **Stop loss**: ATR-based (2×–3×ATR below entry for longs)
- **Take profit**: Risk-reward ratio ≥ 2:1
- **Time stop**: Exit if no progress after N trading days
- **Signal reversal**: Exit when primary indicator flips (e.g., SuperTrend change)

### Evaluation Targets
Use these thresholds to guide whether a strategy is worth pursuing (adjust per ticker):

| Metric | Target | Notes |
|--------|--------|-------|
| Sharpe ratio | ≥ 0.5 | Risk-adjusted return |
| Max drawdown | ≤ 20% | Largest peak-to-trough |
| Win rate | ≥ 45% | Percentage of profitable trades |
| Profit factor | ≥ 1.5 | Gross profit / gross loss |
| Calmar ratio | ≥ 1.0 | Return / max drawdown |

## Execution Steps

1. **Pre-flight** — Resolve ticker identity (see Pre-flight section above).
2. **Phase 1** — Load and analyze data characteristics.
3. **Phase 2** — Run all 32 built-in strategies, collect metrics.
4. **Phase 3** — Deep dive into top 5 strategies.
5. **Phase 4** — Create custom strategies if needed.
6. **Phase 5** — Optimize parameters for promising custom strategies.
7. **Phase 6** — Compile final recommendation.
8. **Write report** — Output to `data/reports/strategies/{ticker}/{latest_date}.md` in chunks (see Output Report Format above).
9. **Verify** — Confirm the file was written completely, is well-structured, and correctly identifies the company.

## Constraints & Gotchas

- **Activate venv** before running any Python scripts
- **Data retrieval:** Use `get_evaluation_data.py` for all data loading. It provides metadata, indicators, OHLCV, forward returns, yearly performance, column listings, and custom strategy discovery (`--custom-strategies`)
- **TA columns** all have the `ta_` prefix — verify column names with `get_evaluation_data.py {ticker} --list-columns` or `docs/all_technical_analysis.md`
- **Regime module** requires `arch` + `hmmlearn` — strategies using HMM columns will fail if not installed
- **Default cutoff** is `2016-10-15` (~10 years) — adjust based on `{year}` parameter
- **Initial capital:** £100,000, **Commission:** 0.1%, **Slippage:** 0.1% (from `app.backtest.framework.engine`)
- **vectorbt** simulates portfolios — signals must return `int` Series (1, 0, -1)
- **Custom strategies** in `app/backtest/custom/{ticker}/` (per-ticker subdirectories) must use `@register_custom("name")` decorator and import `from framework.extensions import register_custom`
- **Strategy function** signature: `def name(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]`
- **Built-in strategy functions** use `signal_` prefix: `signal_bb_meanrev`, `signal_golden_cross`, etc. Use `grep "def signal_"` to find them, NOT `grep "def bb_meanrev"`.
- **Ticker identity:** Always resolve via `get_evaluation_data.py` (reads `config/ticker_list.csv`). Never guess company names from ticker symbols. `NG.L` = **National Grid** (Utilities), not "Natural Gas".
- **Don't** hardcode to NG.L — this skill must work for any ticker

### Custom Strategy CLI Gotchas

| Mistake | Correct |
|---------|---------|
| `--custom ba_defense` (truncated) | `--custom ba_defense_meanrev` (exact module stem) |
| `--custom signal_bb_meanrev` (strategy name) | `--custom bb_meanrev` (module file name without `.py`) |
| `--dry-run` on `run_strategy_backtest.py` | `--list` to preview, or `--dry-run` on `run_backtest.py` only |
| Loading all 20+ custom files | Use `--custom-strategies` to discover relevant ones first |

### VectorBT API Reference

When creating portfolios or reading trade metrics:

| What you want | Correct | Wrong |
|---|---|---|
| Total trade count | `pf.stats()["Total Trades"]` or `pf.trades.count()` | `pf.trades().total()` or `pf.trades.total` |
| Total return | `pf.total_return()` | `pf.total_return * 100` (missing call) |
| Sharpe ratio | `pf.sharpe_ratio()` | — (requires `freq="1D"` in `from_signals`) |
| Max drawdown | `pf.max_drawdown()` | — |
| Win rate | `pf.win_rate()` | — |
| Profit factor | `pf.profit_factor()` | — |
| Daily returns | `pf.daily_returns()` | — |
| Final value | `pf.final_value()` | — |
| Trades PnL | `pf.trades.pnl` (MappedArray) | `pf.trades().pnl` |
| Trade count from trades | `pf.trades.count()` | `pf.trades.size` (returns MappedArray, not int) |

> `pf.trades` is an `ExitTrades` object — **not a callable**. Do not use `pf.trades()`.
> When computing Sharpe/Calmar/Omega ratios, always pass `freq="1D"` to `Portfolio.from_signals()`.

### Custom Strategy Loading

#### `--custom` flag on CLI helpers

- `--custom` on `run_strategy_backtest.py` and `run_backtest_analysis.py` takes **module file names WITHOUT `.py`** — NOT individual strategy names, NOT truncated names.
  - **Correct:** `--custom ba_defense_meanrev` (loads all strategies from `ba_defense_meanrev.py`)
  - **Wrong:** `--custom ba_defense` (truncated — file not found)
  - **Wrong:** `--custom ba_defense_meanrev signal_bb_meanrev` (strategy name, not module name)
  - **Multiple modules:** `--custom ba_defense_meanrev ba_regime_filter` (space-separated, no `.py`)
- The script globs for `{module_name}.py` inside the custom directory. The **exact** stem must match.

#### `--list` flag (NEW — use this before running)

- `run_strategy_backtest.py` now supports `--list` to show which custom strategies would load without running a backtest:
  ```bash
  python app/backtest/run_strategy_backtest.py BA.L --list
  python app/backtest/run_strategy_backtest.py BA.L --list --custom ba_defense_meanrev
  ```
- This is the **safe way to verify** your module names are correct before running expensive backtests.

#### `--dry-run` does NOT exist on `run_strategy_backtest.py`

- `--dry-run` exists ONLY on `run_backtest.py` (the original CLI).
- On `run_strategy_backtest.py` and `run_backtest_analysis.py`, use `--list` instead to preview what would run.

#### `load_custom_strategies()` programmatically

- `load_custom_strategies("app/backtest/custom")` takes a **directory**, not a file path.
- It clears the registry then uses `rglob("*.py")` — discovers all `.py` files recursively in per-ticker subdirectories.
- Only functions decorated with `@register_custom("name")` appear in the returned dict.
- To load only strategies for a specific ticker: `load_custom_strategies("app/backtest/custom", ticker="NG.L")` (case-insensitive prefix match).
- To load specific modules only: `load_custom_strategies("app/backtest/custom", module_names=["NG.L_custom", "NG.L_variants"], ticker="NG.L")`
- If a custom strategy doesn't show up, verify: (1) file is in the correct `{ticker}/` subdirectory, (2) has `@register_custom("name")`, (3) imports `register_custom` from `framework.extensions`, (4) the decorator name matches the intended strategy key.
