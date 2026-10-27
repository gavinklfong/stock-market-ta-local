# Investment Strategy Skill

This skill defines a structured approach to formulating, investigating, evaluating, and backtesting investment strategies.

## Objective

Investigate and recommend the best investment strategy (maximum return / minimum drawdown) for `{ticker}` based on `{year}` of market data. Create and evaluate custom strategies when built-in ones are insufficient. Output findings to `data/reports/strategies/{ticker}/{latest_date}.md`, where `{latest_date}` is the last date in the market data CSV (formatted `YYYY-MM-DD`).

## Parameters

- `{ticker}` — Ticker symbol (e.g. `NG.L`, `BP.L`, `HSBA.L`). Look up data at `data/analysis-data/{ticker}.csv`.
- `{year}` — Number of years of lookback data. Default: 10. Set cutoff date as `pd.Timestamp("YYYY-MM-DD")` where YYYY-MM-DD is `{current_date}` minus `{year}` years.
- `{latest_date}` — The last date in `data/analysis-data/{ticker}.csv` (`df["Date"].max()`), formatted `YYYY-MM-DD`. Used as the date component in the output filename.

## Strategy Types

Trend following · Mean reversion · Momentum · Contrarian · Dividend income · Breakout

## Pre-flight: Resolve Ticker Identity

**Before any analysis, resolve the ticker to its real company name and sector.**

1. Read `config/ticker_list.csv` (columns: `Ticker`, `Company`, `Major Industry / Sector`)
2. Look up the exact `{ticker}` string (e.g. `NG.L`, `BP.L`, `HSBA.L`)
3. Record the `Company` and `Sector` values — these are the **authoritative** identifiers
4. **NEVER guess** what a ticker represents based on its symbol alone (e.g. `NG.L` is **National Grid**, not "Natural Gas"; `BP.L` is **BP**, not "Bond Pricing")
5. Use the resolved company name throughout the report instead of the raw ticker symbol where narrative context is needed
6. **Constraint:** If the ticker is not found in `config/ticker_list.csv`, note this as a data issue and proceed with the ticker symbol only — do not fabricate a company name.

## Directory Quick Reference

| Directory | Purpose | Naming convention | Example |
|-----------|---------|-------------------|---------|
| `app/backtest/custom/` | Strategy module files (registered with `@register_custom`) | `{custom_name}.py` | `my_strategy.py` |
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
| `app/backtest/custom/template_strategy.py` | Template for custom strategies |
| `app/backtest/custom_scripts/NG.L_backtest.py` | NG.L-focused reference (32 strategies, optimization notes) |
| `docs/all_technical_analysis.md` | Complete TA indicator reference (all 12 sections, 1268 lines) |
| `data/analysis-data/{ticker}.csv` | Input data: OHLCV + all `ta_` prefixed columns + P/E data |

## Built-in Strategy Groups (32 total)

1. **Individual (17):** `golden_cross`, `ema_pullback`, `supertrend_plus`, `donchian`, `bb_breakout`, `bb_meanrev`, `rsi_macd_rev`, `institutional`, `vwap`, `ofi`, `marketstruct`, `bos_breakout`, `choch`, `vol_expansion`, `hmm_regime`, `momentum_comp`, `highprob_multi`
2. **Combinations (3):** `trend_momentum`, `vol_structure`, `score80`
3. **Improved (10):** `bb_meanrev_upper`, `bb_meanrev_atr`, `vol_filtered_meanrev`, `regime_adaptive`, `short_meanrev`, `vol_breakout_rev`, `ema_pullback_vol`, `multiscore60`, `dual_exit_meanrev`, `macd_divergence_rev`
4. **NG.L Optimized (2):** `bb_meanrev_optimized`, `bb_meanrev_entry2`

## TA Column Reference

All TA columns use the `ta_` prefix. Key columns (full list in `docs/all_technical_analysis.md`):

| Category | Key Columns |
|----------|-------------|
| Trend | `ta_ema20`, `ta_ema50`, `ta_ema200`, `ta_supertrend_direction`, `ta_ma20_slope`, `ta_ma50_slope`, `ta_ma200_slope`, `ta_donchian_upper/lower`, `ta_keltner_upper/lower` |
| Momentum | `ta_rsi14`, `ta_macd_line`, `ta_macd_signal`, `ta_macd_histogram`, `ta_roc20`, `ta_williams_r`, `ta_cci`, `ta_tsi25_13`, `ta_rsi_zscore`, `ta_rsi_percentile` |
| Volume | `ta_obv`, `ta_cmf`, `ta_vwap`, `ta_ofi`, `ta_adl`, `ta_mfi14`, `ta_emv14`, `ta_vol_osc`, `ta_vol_zscore`, `ta_vol_percentile` |
| Volatility | `ta_atr14`, `ta_bband_upper`, `ta_bband_middle`, `ta_bband_lower`, `ta_bband_width`, `ta_pct_b`, `ta_hvol20`, `ta_park_volv`, `ta_garch_vol`, `ta_atr_stop_dist`, `ta_atr_percentile` |
| Regime | `ta_hmm_regime_prob_0`, `ta_hmm_regime_prob_1`, `ta_hmm_regime_prob_2`, `ta_regime_label` |
| Structure | `ta_swing_high`, `ta_swing_low`, `ta_hh`, `ta_hl`, `ta_lh`, `ta_ll`, `ta_bos`, `ta_choch`, `ta_nearest_resistance`, `ta_nearest_support`, `ta_trend` |
| Return | `ta_ret_5d`, `ta_ret_10d`, `ta_ret_20d`, `ta_ret_1m`, `ta_ret_3m`, `ta_ret_6m`, `ta_ret_1y`, `ta_alpha20`, `ta_beta20`, `ta_rs_ftse100` |
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

1. Verify the data file exists: `data/analysis-data/{ticker}.csv`
2. Check data date range, column count, and missing values
3. **Use the resolved company name** from the Pre-flight step — e.g. "National Grid (NG.L) is a regulated UK utility…" not "NG.L is a commodity…"
4. Examine forward returns (`ta_ret_5d`, `ta_ret_10d`, `ta_ret_20d`) and past performance (`ta_ret_1m`, `ta_ret_3m`, `ta_ret_6m`, `ta_ret_1y`) to understand the asset's behavior
5. Look at P/E data for valuation context
6. Determine asset characteristics from the return data:
   - Is it trending (strong directional moves)? → favor trend-following strategies
   - Is it mean-reverting (oscillates around a range)? → favor mean-reversion strategies
   - Is it volatile with wide swings? → favor volatility-based strategies
   - Is it low-vol with range-bound? → favor conservative mean-reversion
7. **Contextualize the asset type** using the resolved company name and sector (e.g. "National Grid is a regulated utility, not a commodity — mean-reversion strategies designed for commodities do not directly apply")

### Phase 2: Baseline Strategy Evaluation

Run all 32 built-in strategies via the CLI or framework:

```bash
# Run all built-in strategies with custom cutoff
python app/backtest/run_backtest.py {ticker} --cutoff YYYY-MM-DD

# Or run a focused subset (e.g. mean-reversion first)
python app/backtest/run_backtest.py {ticker} --cutoff YYYY-MM-DD --dry-run
```

Alternatively, run the framework programmatically (preferred for collecting metrics):

```python
from app.backtest.framework.engine import BacktestEngine
from app.backtest.framework.metrics import summarize_table
from app.backtest.strategies.builtins import STRATEGIES, STRATEGY_LABELS
import pandas as pd

engine = BacktestEngine(
    "data/analysis-data/MKS.L.csv",    # file path, NOT a DataFrame
    cutoff_date=pd.Timestamp("2016-10-26")
)

results = engine.run_batch(
    tickers=["MKS.L"],
    strategies=STRATEGIES,
    cutoff=pd.Timestamp("2016-10-26"),
    ticker_names={"MKS.L": "MKS.L"}
)
print(summarize_table(results, "MKS.L"))
```

> **Important:** `BacktestEngine` takes a **file path string** (`str` or `Path`), not a DataFrame.
> It loads the CSV internally. Pass `cutoff_date` to `__init__`, not as a separate step.

**Record results in `data/reports/strategies/{ticker}/{latest_date}.md`:**

For each strategy, capture:
- Strategy name (key from `STRATEGIES`) and label (from `STRATEGY_LABELS`)
- Total Return (%), Sharpe Ratio, Max Drawdown (%), Profit Factor
- Win Rate (%), Total Trades
- Rank position (by Total Return descending, then Profit Factor, then Min Drawdown)

### Phase 3: Strategy Deep Dive — Top 5

Select the top 5 strategies by performance (balanced: return + risk). For each:

1. Read the source code in `app/backtest/strategies/builtins.py` to understand the logic
2. Analyze entry/exit conditions and their rationale
3. Check which TA columns they use — verify those indicators are relevant for this ticker
4. Note edge cases (e.g., strategies that use HMM regime but that ticker may not have regime data)

### Phase 4: Custom Strategy Creation (if needed)

If no built-in strategy achieves satisfactory results, or if a specific pattern is evident from the data:

1. Copy `app/backtest/custom/template_strategy.py` to `app/backtest/custom/{custom_name}.py`
2. Create a new signal function with `@register_custom("custom_name")` decorator
3. Function signature: `def custom_name(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]`
4. Return entries (int 1s) and exits (int -1s)
5. Reference TA columns via `df["ta_column_name"]`
6. Test with `--dry-run` first, then full backtest

**Loading custom strategies programmatically:**

```python
from app.backtest.framework.extensions import load_custom_strategies

# CORRECT: pass a DIRECTORY path, not a file path
custom = load_custom_strategies("app/backtest/custom")
print("Loaded strategies:", list(custom.keys()))

# To load only specific module files:
custom = load_custom_strategies(
    "app/backtest/custom",
    module_names=["sbry_bb"]   # only loads sbry_bb.py
)
```

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

For promising custom strategies, test multiple parameter variants:

```python
from app.backtest.framework.engine import BacktestEngine, INITIAL_CAPITAL, COMMISSION, SLIPPAGE
from vectorbt.portfolio.enums import SizeType
import pandas as pd
import vectorbt as vbt

engine = BacktestEngine("data/analysis-data/NG.L.csv", cutoff_date=pd.Timestamp("2016-10-26"))
df = engine.load_data()

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
Compare Buy-and-Hold benchmark against the top 5 strategies by Total Return (ranked from Phase 2 / Phase 4 results):

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
- **TA columns** all have the `ta_` prefix — verify column names in `docs/all_technical_analysis.md`
- **Regime module** requires `arch` + `hmmlearn` — strategies using HMM columns will fail if not installed
- **Default cutoff** is `2016-10-15` (~10 years) — adjust based on `{year}` parameter
- **Initial capital:** £100,000, **Commission:** 0.1%, **Slippage:** 0.1% (from `app.backtest.framework.engine`)
- **vectorbt** simulates portfolios — signals must return `int` Series (1, 0, -1)
- **Custom strategies** in `app/backtest/custom/` must use `@register_custom("name")` decorator and import `from framework.extensions import register_custom`
- **Strategy function** signature: `def name(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]`
- **Ticker identity:** Always resolve from `config/ticker_list.csv` before writing any report. Never guess company names from ticker symbols. `NG.L` = **National Grid** (Utilities), not "Natural Gas".
- **Don't** hardcode to NG.L — this skill must work for any ticker

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

- `load_custom_strategies("app/backtest/custom")` takes a **directory**, not a file path.
- It clears the registry then globs `*.py` files — all files in the directory are loaded.
- Only functions decorated with `@register_custom("name")` appear in the returned dict.
- If a custom strategy doesn't show up, verify: (1) file is in the custom/ directory, (2) has `@register_custom("name")`, (3) imports `register_custom` from `framework.extensions`, (4) the decorator name matches the intended strategy key.
