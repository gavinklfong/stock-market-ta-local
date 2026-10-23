# Investment Strategy Investigation Skill

## Objective

Investigate and recommend the best investment strategy (maximum return / minimum drawdown) for `{ticker}` based on `{year}` of market data. Create and evaluate custom strategies when built-in ones are insufficient. Output findings to `data/strategy/{ticker}/{latest_date}.md`, where `{latest_date}` is the last date in the market data CSV (formatted `YYYY-MM-DD`). This date represents the latest market data the strategy was formulated against.

## Parameters

- `{ticker}` — Ticker symbol (e.g. `NG.L`, `BP.L`, `HSBA.L`). Look up data at `data/analysis-data/{ticker}.csv`.
- `{year}` — Number of years of lookback data. Default: 10. Set cutoff date as `pd.Timestamp("YYYY-MM-DD")` where YYYY-MM-DD is `{current_date}` minus `{year}` years.
- `{latest_date}` — The last date in `data/analysis-data/{ticker}.csv` (`df["Date"].max()`), formatted `YYYY-MM-DD`. Used as the date component in the output filename.

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
| `app/backtest/backtest_ng.py` | NG.L-focused reference (32 strategies, optimization notes) |
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

## Methodology

### Phase 1: Data Preparation & Understanding

1. Verify the data file exists: `data/analysis-data/{ticker}.csv`
2. Check data date range, column count, and missing values
3. Examine forward returns (`ta_ret_5d`, `ta_ret_10d`, `ta_ret_20d`) and past performance (`ta_ret_1m`, `ta_ret_3m`, `ta_ret_6m`, `ta_ret_1y`) to understand the asset's behavior
4. Look at P/E data for valuation context
5. Determine asset characteristics from the return data:
   - Is it trending (strong directional moves)? → favor trend-following strategies
   - Is it mean-reverting (oscillates around a range)? → favor mean-reversion strategies
   - Is it volatile with wide swings? → favor volatility-based strategies
   - Is it low-vol with range-bound? → favor conservative mean-reversion

### Phase 2: Baseline Strategy Evaluation

Run all 32 built-in strategies via the CLI or framework:

```bash
# Run all built-in strategies with custom cutoff
python app/backtest/run_backtest.py {ticker} --cutoff YYYY-MM-DD

# Or run a focused subset (e.g. mean-reversion first)
python app/backtest/run_backtest.py {ticker} --cutoff YYYY-MM-DD --dry-run
```

Alternatively, run the framework programmatically:

```python
from app.backtest.run_backtest import main
# or import directly:
from app.backtest.framework.engine import BacktestEngine
from app.backtest.strategies.builtins import STRATEGIES, STRATEGY_LABELS
```

**Record results in `data/strategy/{ticker}/{latest_date}.md`:**

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
# Example: Test different RSI thresholds for mean reversion
# RSI threshold: 25, 30, 35
# ATR stop: 2x, 3x, 4x
# BB entry: Close <= Lower, Close <= Lower - 0.5*ATR
```

Run each variant and compare. Use `pick_best()` from `metrics.py` for automated ranking.

### Phase 6: Final Recommendation

Compile findings into a recommendation:

1. **Best overall strategy** — highest risk-adjusted return (Sharpe or Calmar)
2. **Highest return strategy** — maximum total return (accepting higher drawdown)
3. **Lowest drawdown strategy** — maximum capital preservation
4. **Best custom strategy** — if any custom strategy outperforms built-ins
5. **Recommended entry/exit rules** — the logic behind the top pick
6. **Risk considerations** — conditions where the strategy may fail

## Output Format for `data/strategy/{ticker}/{latest_date}.md`

Write the output file in chunks to avoid token limits. Structure:

```markdown
# Investment Strategy Report: {Ticker}

## Executive Summary
- **Ticker:** {Ticker} ({ticker})
- **Analysis Period:** {year} years
- **Best Overall:** {strategy_name} — {return}% return, {sharpe} Sharpe, {drawdown}% drawdown
- **Highest Return:** {strategy_name} — {return}% return
- **Lowest Drawdown:** {strategy_name} — {drawdown}% max drawdown
- **Recommended:** {strategy_name}

## Data Summary
- Date range: {start_date} to {end_date}
- Rows: {count}
- Asset characteristics: {trending / mean-reverting / volatile / range-bound}

## Phase 1: Data Analysis
- Forward return statistics
- Past performance summary
- P/E valuation context
- Asset behavior classification

## Phase 2: Baseline Results (All 32 Built-in Strategies)
| Rank | Strategy | Label | Return% | Sharpe | Max DD% | Profit Factor | Win Rate% | Trades |
|------|----------|-------|---------|--------|---------|---------------|-----------|--------|
| 1 | ... | ... | ... | ... | ... | ... | ... | ... |
| ...

## Phase 3: Top 5 Strategy Deep Dive
### 1. {strategy_name} — {label}
- **Logic:** {description from source code}
- **Entry conditions:** {bullet list}
- **Exit conditions:** {bullet list}
- **Results:** {metrics}
- **Analysis:** {why it worked for this ticker}

### 2. {strategy_name} — {label}
...

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
| Config 1 | ... | ... | ... | ... |
| Config 2 | ... | ... | ... | ... |

## Phase 6: Final Recommendation
- **Best overall:** {strategy} with rationale
- **Entry rules:** {exact conditions}
- **Exit rules:** {exact conditions}
- **Risk management:** {position sizing, stop loss, max holding period}
- **When it fails:** {market conditions where this strategy underperforms}
- **Suggested improvements:** {ideas for further refinement}
```

## Execution Steps

1. **Read data** — load `data/analysis-data/{ticker}.csv`, analyze characteristics
2. **Run baseline** — execute all 32 built-in strategies, collect metrics
3. **Rank results** — sort by Total Return, then Profit Factor, then Min Drawdown
4. **Deep dive top 5** — understand why top strategies worked
5. **Create custom strategies** — if needed, write to `app/backtest/custom/`
6. **Optimize parameters** — test variants of promising custom strategies
7. **Compile report** — write findings to `data/strategy/{ticker}/{latest_date}.md` in chunks
8. **Verify report** — confirm the file was written completely and is well-structured

## Token Limit Handling

When writing `data/strategy/{ticker}/{latest_date}.md`:
- Write the file in sections using separate write/edit calls
- Start with the header and executive summary
- Append Phase 1, 2, 3, etc. separately
- Each chunk should be self-contained and no more than ~2000 words
- Use `edit` to insert sections between existing content, or `write` to overwrite with growing content

## Constraints & Gotchas

- **Activate venv** before running any Python scripts
- **TA columns** all have `ta_` prefix — verify column names in `docs/all_technical_analysis.md`
- **Regime module** requires `arch` + `hmmlearn` — strategies using HMM columns will fail if not installed
- **Default cutoff** is `2016-10-15` (~10 years) — adjust based on `{year}` parameter
- **Initial capital:** £100,000, **Commission:** 0.1%, **Slippage:** 0.1%
- **vectorbt** simulates portfolios — signals must return `int` Series (1, 0, -1)
- **Custom strategy files** must use `@register_custom("name")` decorator and import `from framework.extensions import register_custom`
- **Strategy function** signature: `def name(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]`
- **Don't** hardcode to NG.L — this skill must work for any ticker
