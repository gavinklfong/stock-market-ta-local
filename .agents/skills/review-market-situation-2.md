# Market Situation Review Skill

## Objective

Assess the market situation for `{ticker}` as of `{evaluation_date}` and recommend a buy / sell / hold signal. Evaluate across 7 dimensions: trend, momentum, return, structure, volatility, volume, and regime. Cross-reference findings with the most recent backtested strategy results from `data/strategy/{ticker}/`. Output the evaluation report to `data/reports/evaluation/{ticker}/{evaluation_date}_evaluation.md`.

## Parameters

- `{ticker}` — Ticker symbol (e.g. `NG.L`, `BP.L`, `HSBA.L`)
- `{evaluation_date}` — The date to evaluate as of (format: `YYYY-MM-DD`). Defaults to the latest date in the CSV if not specified. Used for backtesting / historical verification of signals.
- Data source: `data/analysis-data/{ticker}.csv`
- Strategy reference: `data/strategy/{ticker}/` — the most recent `.md` file in this directory (must exist before running this skill)
- TA knowledge base: `docs/all_technical_analysis.md`
- Output: `data/reports/evaluation/{ticker}/{evaluation_date}_evaluation.md` (where `{evaluation_date}` is the specified date or the last date in the CSV)

## Usage Notes

- **Historical verification:** To test whether this skill would have given correct advice on a past date, pass the date as `{evaluation_date}` (e.g. `2025-06-15`). The evaluation will use only data available up to and including that date — no hindsight.
- **Temporal cutoff:** When `{evaluation_date}` is provided, the skill **cuts off all data after that date**. Only rows where `Date <= {evaluation_date}` are used. Rolling indicators (RSI, MACD, ATR, etc.) are read at their values on the evaluation date, reflecting the data available at that time.
- **Date not found:** If the specified date does not exist in the CSV (e.g. weekend/holiday), the skill falls back to the latest available date **on or before** the specified date.
- **Future date:** If the specified date is after the last row in the CSV, the skill uses the latest available date and notes the discrepancy.
- **Default behavior:** If `{evaluation_date}` is omitted, the skill uses the latest date in the CSV (original behavior).

## Prerequisites Check

**Before proceeding, verify that the most recent strategy file exists in `data/strategy/{ticker}/`.**

- List all `.md` files in `data/strategy/{ticker}/` and select the one with the most recent filename (which encodes the date).
- If the directory is empty or does NOT exist, advise the user to run the investment strategy skill first:
  > "Please run the investment strategy skill `.agents/skills/investment-strategy.md` for `{ticker}` first to generate a strategy report in `data/strategy/{ticker}/`. This review skill requires the backtest results to cross-reference current signals with historically optimal strategies."
- Exit the current task until the strategy report is available.
- Record the path of the selected strategy file (e.g. `data/strategy/{ticker}/2025-06-30.md`) and use it throughout the evaluation.

## Relevant Files Reference

| File | Purpose |
|------|---------|
| `data/analysis-data/{ticker}.csv` | Latest market data — OHLCV + all TA indicators (prefixed `ta_`) + P/E fundamentals |
| `data/strategy/{ticker}/{latest_strategy_date}.md` | Most recent backtested strategy results — best strategies, their logic, parameters, and recommended entry/exit rules |
| `docs/all_technical_analysis.md` | TA indicator definitions and interpretation guidelines (12 sections) |
| `app/backtest/strategies/builtins.py` | 32 built-in strategy source code — read entry/exit logic for each category |
| `app/calculate-ta/README.md` | Full TA column reference with formulas and parameters |

## TA Column Quick Reference

All TA columns use the `ta_` prefix. Key columns for each evaluation dimension:

| Dimension | Key Columns |
|-----------|-------------|
| **Trend** | `ta_ema20`, `ta_ema50`, `ta_ema200`, `ta_supertrend_direction`, `ta_ma20_slope`, `ta_ma50_slope`, `ta_ma200_slope`, `ta_donchian_upper`, `ta_donchian_lower`, `ta_keltner_upper`, `ta_keltner_lower`, `ta_adx`, `ta_di_plus`, `ta_di_minus`, `ta_aroon_up`, `ta_aroon_down`, `ta_trend` |
| **Momentum** | `ta_rsi14`, `ta_macd_line`, `ta_macd_signal`, `ta_macd_histogram`, `ta_roc20`, `ta_williams_r`, `ta_cci`, `ta_tsi25_13`, `ta_rsi_zscore_14_20`, `ta_rsi_percentile_14_20` |
| **Return** | `ta_ret_5d`, `ta_ret_10d`, `ta_ret_20d`, `ta_ret_1m`, `ta_ret_3m`, `ta_ret_6m`, `ta_ret_1y`, `ta_alpha20`, `ta_beta20`, `ta_rs_ftse100` |
| **Structure** | `ta_swing_high`, `ta_swing_low`, `ta_hh`, `ta_hl`, `ta_lh`, `ta_ll`, `ta_bos`, `ta_choch`, `ta_nearest_resistance`, `ta_nearest_support` |
| **Volatility** | `ta_atr14`, `ta_bband_upper`, `ta_bband_middle`, `ta_bband_lower`, `ta_bband_width`, `ta_pct_b`, `ta_hvol20`, `ta_park_volv`, `ta_garch_vol`, `ta_atr_stop_dist`, `ta_atr_percentile_14_20` |
| **Volume** | `ta_obv`, `ta_cmf`, `ta_vwap`, `ta_ofi`, `ta_adl`, `ta_mfi14`, `ta_emv14`, `ta_vol_osc_14_28`, `ta_vol_zscore_20`, `ta_vol_percentile_20`, `ta_obv_slope_14`, `ta_obv_slope_7` |
| **Regime** | `ta_hmm_regime_prob_0`, `ta_hmm_regime_prob_1`, `ta_hmm_regime_prob_2`, `ta_regime_label`, `ta_garch_vol` |

## Evaluation Methodology

### Step 1: Load & Inspect Data for Evaluation Date

1. Load `data/analysis-data/{ticker}.csv`
2. **Determine evaluation date:**
   - If `{evaluation_date}` is provided and exists in the CSV, use it.
   - If `{evaluation_date}` is not provided or not found, use `df["Date"].max()` (the latest date).
   - If the specified date is not in the CSV, find the closest date **on or before** the specified date (i.e., the latest available data point at or before that date).
   - Record the actual date used as `{actual_date}`.
3. **CUT OFF FUTURE DATA:** If `{evaluation_date}` was explicitly provided (i.e., not the default latest date), slice the DataFrame to include only rows where `Date <= {actual_date}`. This ensures the evaluation uses only data that was actually available as of that date — no hindsight. The date range for all indicator readings should be from the earliest available date up to `{actual_date}`.
4. Read the row matching `{actual_date}` (the evaluation date) and the preceding ~20 rows for context from the sliced data
5. Record: current price on evaluation date, date range (up to `{actual_date}`), total rows (within the cutoff), column count
6. Check for any NaN values in key columns

