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

### Step 2: Evaluate Trend (Score: 1–5)

Read the latest values and compute signals:

1. **EMA alignment**: Is `ta_ema20 > ta_ema50 > ta_ema200`? (bullish) or reversed? (bearish)
2. **SuperTrend**: `ta_supertrend_direction` — +1 = bullish, -1 = bearish. Note recent flips.
3. **MA slopes**: `ta_ma20_slope`, `ta_ma50_slope` — positive = uptrend, negative = downtrend
4. **ADX/DI**: `ta_adx` > 25 = strong trend. `ta_di_plus > ta_di_minus` = bullish trend, reversed = bearish
5. **Donchian**: Is price near `ta_donchian_upper` (breakout) or `ta_donchian_lower` (breakdown)?
6. **Keltner**: Is price above/below the Keltner bands?
7. **Price vs MAs**: Calculate `price / ta_ema20 - 1` — positive = price above EMA20

**Cross-reference with strategy report:**
- Read the recommended entry/exit rules from the latest strategy file in `data/strategy/{ticker}/`
- Check if current conditions match the recommended strategy's entry criteria
- If the best strategy is trend-following, is the trend aligned?

**Output:** Trend score (1–5), key indicator values, alignment with best strategy.

### Step 3: Evaluate Momentum (Score: 1–5)

1. **RSI(14)**: `<30` oversold, `30–50` weak, `50–70` normal, `>70` overbought. Also check `ta_rsi_zscore_14_20` and `ta_rsi_percentile_14_20` for statistical context.
2. **MACD**: `ta_macd_line > ta_macd_signal` = bullish. Check histogram direction (`ta_macd_histogram` rising/falling). Note any bullish/bearish crosses.
3. **ROC(20)**: `ta_roc20 > 0` = positive momentum
4. **Williams %R**: `ta_williams_r > -20` overbought, `< -80` oversold
5. **CCI**: `ta_cci > 100` overbought, `< -100` oversold
6. **TSI**: Check sign and slope of `ta_tsi25_13`
7. **MFI(14)**: `ta_mfi14 > 80` overbought, `< 20` oversold (volume-weighted RSI)

**Cross-reference with strategy report:**
- What RSI thresholds does the best strategy use for entries/exits?
- Is the current momentum consistent with the strategy's entry conditions?
- Reference the latest strategy file in `data/strategy/{ticker}/`.

**Output:** Momentum score (1–5), key indicator values, overbought/oversold assessment, alignment with best strategy.

### Step 4: Evaluate Return (Score: 1–5)

1. **Recent performance**: `ta_ret_1m`, `ta_ret_3m`, `ta_ret_6m`, `ta_ret_1y`
   - Strong positive = momentum continues, watch for exhaustion
   - Strong negative = potential reversal opportunity or continued downtrend
2. **Forward returns (context)**: `ta_ret_5d`, `ta_ret_10d`, `ta_ret_20d`
   - These are historical forward returns — compute average for recent periods
   - If most recent 5d/10d/20d forward returns have been positive, trend may continue
3. **Alpha/Beta**: `ta_alpha20`, `ta_beta20` vs ^FTSE
   - Positive alpha = outperforming benchmark
   - Beta > 1 = more volatile than market; Beta < 1 = less volatile
4. **Relative strength**: `ta_rs_ftse100`
   - Rising = outperforming FTSE 100; Falling = underperforming

**Cross-reference with strategy report:**
- Does the strategy report mention return expectations or holding periods?
- Is the ticker historically more of a mean-reversion or momentum asset?
- Reference the latest strategy file in `data/strategy/{ticker}/`.

**Output:** Return score (1–5), performance summary, alpha/beta context, alignment with best strategy.

### Step 5: Evaluate Structure (Score: 1–5)

1. **Swing points**: Check `ta_swing_high` and `ta_swing_low` for recent swings
2. **HH/HL vs LH/LL**:
   - `ta_hh` and `ta_hl` = bullish structure
   - `ta_lh` and `ta_ll` = bearish structure
3. **Break of Structure (BOS)**: `ta_bos` — bullish break above previous high, or bearish break below previous low
4. **Change of Character (CHoCH)**: `ta_choch` — signals trend reversal
5. **Support/Resistance**: `ta_nearest_support`, `ta_nearest_resistance`
   - Current price proximity to these levels
6. **Trend label**: `ta_trend` — if available, direct trend classification

**Cross-reference with strategy report:**
- Does the best strategy use structural signals (BOS, CHoCH, HH/HL)?
- Are structural conditions currently aligned with entry rules?
- Reference the latest strategy file in `data/strategy/{ticker}/`.

**Output:** Structure score (1–5), swing analysis, S/R levels, alignment with best strategy.

### Step 6: Evaluate Volatility (Score: 1–5)

1. **ATR(14)**: `ta_atr14` — absolute volatility level. Compare to historical percentile `ta_atr_percentile_14_20`
2. **Bollinger Bands**:
   - `ta_pct_b` — position within bands (0 = lower band, 1 = upper band)
   - `ta_bband_width` — band width contraction = potential breakout; expansion = trend acceleration
   - Price near lower band = potential bounce; near upper = potential pullback
3. **Historical Volatility**: `ta_hvol20` — rising or falling?
4. **Parkinson Volatility**: `ta_park_volv` — range-based volatility estimate
5. **GARCH forecast**: `ta_garch_vol` — predicted future volatility
6. **ATR Stop Distance**: `ta_atr_stop_dist` — suggested stop distance
7. **ATR Percentile**: `ta_atr_percentile_14_20` — where current ATR sits historically

**Cross-reference with strategy report:**
- Does the best strategy have volatility-based entries or exits?
- Is current volatility consistent with the strategy's optimal conditions?
- Note any ATR-based position sizing mentioned in the strategy.
- Reference the latest strategy file in `data/strategy/{ticker}/`.

**Output:** Volatility score (1-5), current level, trend in volatility, breakout/bounce probability, alignment with best strategy.

### Step 7: Evaluate Volume (Score: 1–5)

1. **OBV**: `ta_obv` — rising OBV confirms price trend, falling OBV warns of divergence
2. **CMF(20)**: `ta_cmf` — `>0` = buying pressure, `<0` = selling pressure. Strength proportional to magnitude.
3. **VWAP**: `ta_vwap` — price above VWAP = bullish intraday trend
4. **OFI**: `ta_ofi` — `>0` = order flow imbalance favoring buyers. Check `ta_ofi_slope` (OBV slope).
5. **ADL**: `ta_adl` — accumulating/distributing pressure
6. **MFI(14)**: `ta_mfi14` — volume-weighted RSI, `>80` overbought, `<20` oversold
7. **Volume metrics**: `ta_vol_zscore_20`, `ta_vol_percentile_20` — is current volume above/below average?
8. **EMV(14)**: `ta_emv14` — ease of movement, positive = price rising with little effort

**Cross-reference with strategy report:**
- Does the best strategy use volume confirmation (CMF, OBV, OFI)?
- Is volume currently supporting the price direction?
- Reference the latest strategy file in `data/strategy/{ticker}/`.

**Output:** Volume score (1–5), buying/selling pressure assessment, confirmation/divergence with price, alignment with best strategy.

### Step 8: Evaluate Regime (Score: 1–5)

1. **HMM Regime Probabilities**:
   - `ta_hmm_regime_prob_0` — probability of state 0 (typically bullish)
   - `ta_hmm_regime_prob_1` — probability of state 1 (typically bearish)
   - `ta_hmm_regime_prob_2` — probability of state 2 (typically neutral/sideways)
   - Highest probability = dominant regime
2. **Regime label**: `ta_regime_label` — if available, direct classification
3. **GARCH vol trend**: Rising GARCH vol in bear regime = high risk; falling = stabilization
4. **Regime stability**: Check if regime has changed recently (scan last ~30 days)

**Cross-reference with strategy report:**
- Does the best strategy include regime-adaptive logic?
- What regime does the strategy perform best in?
- If the current regime differs from what the strategy prefers, flag as a concern.
- Reference the latest strategy file in `data/strategy/{ticker}/`.

**Output:** Regime score (1–5), dominant regime, regime stability, alignment with best strategy.

### Step 9: Signal Synthesis — Buy / Sell / Hold

Aggregate all 7 dimension scores:

| Signal | Criteria |
|--------|----------|
| **BUY** | 5 or 6 dimensions Bullish, none strongly Bearish, regime not Bear |
| **STRONG BUY** | All 7 dimensions Bullish, regime is Bull |
| **SELL** | 5 or 6 dimensions Bearish, none strongly Bullish, regime not Bull |
| **STRONG SELL** | All 7 dimensions Bearish, regime is Bear |
| **HOLD** | Mixed signals (3-4 Bullish, 3-4 Bearish), or regime is Neutral |
| **WAIT** | High uncertainty — e.g., low volume, extreme volatility, regime shift imminent |

**Final signal must include:**

1. **Signal**: BUY / SELL / HOLD (with strength)
2. **Score breakdown**: Table showing each dimension's score and weight
3. **Key supporting indicators**: Top 3 indicators per dimension that drive the signal
4. **Key conflicting indicators**: Any indicators that contradict the overall signal
5. **Strategy alignment**: Does current data match the entry conditions of the recommended strategy from the latest file in `data/strategy/{ticker}/`?
6. **Confidence level**: High / Medium / Low (based on agreement across dimensions)
7. **Risk factors**: What could invalidate this signal (e.g., regime shift, volume drying up, structural break)
8. **Recommended action**: Exact entry conditions to watch for, suggested stop-loss level (using ATR), suggested target (using S/R levels or BB)

### Step 10: Generate Report

Write the evaluation report to `data/reports/evaluation/{ticker}/{actual_date}_evaluation.md` using the standardized template below, broken into chunks.

## Standardized Output Report Template

Write the report using this unified structure (based on SVT.L and VUKG.L evaluation examples):

```markdown
# Market Situation Evaluation: {company_name} ({Ticker})

**Evaluation Date:** {evaluation_date}
**Actual Date Used:** {actual_date}
**Ticker:** {Ticker} ({company_name})
**Price:** {close_price}
**Data Range:** {first_date} to {last_date} ({total_rows} rows)
**Sector:** {sector}
**Strategy Reference:** `data/strategy/{ticker}/{latest_strategy_date}.md`

---

## Executive Summary

**Signal:** BUY / SELL / HOLD / WAIT
**Confidence:** High / Medium / Low

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🟢 BULLISH / 🟡 CAUTIOUS / 🔴 BEARISH | High / Medium / Low | {1-line key driver} |
| **Momentum** | 🟢 BULLISH / 🟡 CAUTIOUS / 🔴 BEARISH | High / Medium / Low | {1-line key driver} |
| **Return** | 🟢 POSITIVE / 🟡 MIXED / 🔴 NEGATIVE | High / Medium / Low | {1-line key driver} |
| **Structure** | 🟢 BULLISH / 🟡 CAUTIOUS / 🔴 BEARISH | High / Medium / Low | {1-line key driver} |
| **Volatility** | 🟢 LOW / 🟡 NORMAL / 🔴 HIGH | High / Medium / Low | {1-line key driver} |
| **Volume** | 🟢 BULLISH / 🟡 MIXED / 🔴 BEARISH | High / Medium / Low | {1-line key driver} |
| **Regime** | 🟢 BULL / 🟡 NEUTRAL / 🔴 BEAR | High / Medium / Low | {1-line key driver} |
| **Overall** | 🟢 STRONG BUY / 🟡 BUY / 🟠 CAUTION / 🔴 SELL | High / Medium / Low | {1-line key driver} |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | {price} | {context: e.g., "Near 52-week high of X"} |
| 52-Week Range | {low} – {high} | {position: e.g., "At 98.8% of high"} |
| P/E (TTM) | {pe_ttm} | {comparison to historical average} |
| Dividend Yield | {yield}% | {assessment} |
| Beta (20d) | {beta} | {vs FTSE 100} |
| RS vs FTSE 100 | {rs} | {outperforming/underperforming} |

### Strategy Alignment Summary

| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| {Strategy entry condition 1} | {current value} | ✅ MET / ❌ NOT MET |
| {Strategy entry condition 2} | {current value} | ✅ MET / ❌ NOT MET |
| {Strategy entry condition 3} | {current value} | ✅ MET / ❌ NOT MET |
| {Key strategy observation} | {context} | ✅ CONFIRMED / ⚠️ CAUTION / ❌ NOT MET |

**Strategy Verdict:** {1-2 sentences: whether current conditions match the recommended strategy's entry criteria}

### Signal Summary

**Current Signal: {SIGNAL} / {STRENGTH}**

{2-3 sentence narrative explaining the overall signal, who should act, and for whom (holders vs non-holders).}

---

## 1. Trend Analysis

**Signal:** BULLISH / CAUTIOUS / BEARISH | **Confidence:** HIGH / MEDIUM / LOW

{1-2 sentence opening context paragraph.}

### Current Indicators

| Indicator | Value | Signal |
|-----------|-------|--------|
| EMA20 | {value} | {above/below price, distance} |
| EMA50 | {value} | {above/below price, distance} |
| EMA200 | {value} | {above/below price, distance} |
| SuperTrend Direction | {1/-1} | {Bullish/Bearish} |
| SuperTrend Trail | {value} | {distance from price} |
| MA20 Slope | {value} | {positive/negative} |
| MA50 Slope | {value} | {positive/negative} |
| ADX(14) | {value} | {strong/weak trend} |
| DI+ / DI- | {value} / {value} | {bullish/bearish dominance} |
| Price vs EMA20 | {pct}% | {above/below} |

### Trend Assessment
- **MA Alignment:** {EMA20 > EMA50 > EMA200 = bullish / reversed = bearish / mixed}
- **SuperTrend:** {current direction, stability, trail level}
- **MA Slopes:** {trend acceleration or deceleration}
- **Trend Strength:** {ADX interpretation: >25 strong, 20–25 moderate, <20 weak}
- **Donchian Position:** {Near upper = breakout / Near lower = breakdown / Middle = range}
- **Keltner Position:** {Price above/below Keltner bands}

### Trend Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| {Factor 1} | +/-{n} | {n}% | +/−{value} |
| {Factor 2} | +/-{n} | {n}% | +/−{value} |
| {Factor 3} | +/-{n} | {n}% | +/−{value} |
| {Factor 4} | +/-{n} | {n}% | +/−{value} |
| {Factor 5} | +/-{n} | {n}% | +/−{value} |
| **Trend Score** | | **100%** | **+/−{total} / 3.0** |

**Trend Verdict:** {1-sentence summary}

### Strategy Alignment
{1-2 sentences: Do current trend conditions match the recommended strategy's entry criteria from the strategy report?}

---

## 2. Momentum Analysis

**Signal:** BULLISH / CAUTIOUS / BEARISH | **Confidence:** HIGH / MEDIUM / LOW

### Current Indicators

| Indicator | Value | Signal |
|-----------|-------|--------|
| RSI(14) | {value} | {Oversold/<30 / Normal / Overbought/>70} |
| RSI Z-Score(14,20) | {value} | {Above/below average} |
| RSI Percentile(14,20) | {value}% | {Percentile interpretation} |
| MACD Line | {value} | {Bullish/Bearish} |
| MACD Signal | {value} | {Cross status} |
| MACD Histogram | {value} | {Rising/Falling/Declining} |
| ROC(20) | {value}% | {Positive/Negative} |
| Williams %R | {value} | {Overbought/>-20 / Oversold/<-80} |
| CCI(20) | {value} | {Overbought/>100 / Oversold/<-100} |
| MFI(14) | {value} | {Overbought/>80 / Oversold/<20} |

### Momentum Assessment
- **RSI Context:** {Current RSI, z-score, percentile interpretation}
- **MACD State:** {Cross status, histogram direction, divergence check}
- **Oscillator Convergence:** {Are multiple oscillators aligned? Any extremes?}
- **Divergence Check:** {Price vs RSI/MACD divergence if any}

### Momentum Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| {Factor 1} | +/-{n} | {n}% | +/−{value} |
| {Factor 2} | +/-{n} | {n}% | +/−{value} |
| {Factor 3} | +/-{n} | {n}% | +/−{value} |
| {Factor 4} | +/-{n} | {n}% | +/−{value} |
| {Factor 5} | +/-{n} | {n}% | +/−{value} |
| **Momentum Score** | | **100%** | **+/−{total} / 3.0** |

**Momentum Verdict:** {1-sentence summary}

### Strategy Alignment
{1-2 sentences: Do current momentum conditions match the recommended strategy's entry criteria?}

---

## 3. Return Analysis

**Signal:** POSITIVE / MIXED / NEGATIVE | **Confidence:** HIGH / MEDIUM / LOW

### Past Performance

| Period | Return | Assessment |
|--------|--------|------------|
| 1 Month | {ta_ret_1m}% | {assessment} |
| 3 Months | {ta_ret_3m}% | {assessment} |
| 6 Months | {ta_ret_6m}% | {assessment} |
| 1 Year | {ta_ret_1y}% | {assessment} |

### Risk-Adjusted Metrics

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Alpha(20) | {ta_alpha20} | {Positive/negative = outperforming/underperforming} |
| Beta(20) | {ta_beta20} | {>1 = more volatile / <1 = less volatile than benchmark} |
| RS vs FTSE 100 | {ta_rs_ftse100} | {Rising = outperforming / Falling = underperforming} |

### Forward Return Context

| Forward Period | Mean Return | Std Dev | Assessment |
|---------------|-------------|---------|------------|
| 5 days | {mean}% | {std}% | {assessment} |
| 10 days | {mean}% | {std}% | {assessment} |
| 20 days | {mean}% | {std}% | {assessment} |

### Return Assessment
- **Short-term trend:** {1m/3m direction}
- **Medium-term trend:** {6m/1y direction}
- **Risk-adjusted:** {Alpha/Beta/RS interpretation}
- **Forward expectations:** {Near-zero = no directional bias; positive = continuation likely}

### Return Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| {Factor 1} | +/-{n} | {n}% | +/−{value} |
| {Factor 2} | +/-{n} | {n}% | +/−{value} |
| {Factor 3} | +/-{n} | {n}% | +/−{value} |
| {Factor 4} | +/-{n} | {n}% | +/−{value} |
| **Return Score** | | **100%** | **+/−{total} / 3.0** |

**Return Verdict:** {1-sentence summary}

### Strategy Alignment
{1-2 sentences: Does the strategy indicate this ticker is more mean-reversion or momentum-driven?}

---

## 4. Structure Analysis

**Signal:** BULLISH / CAUTIOUS / BEARISH | **Confidence:** HIGH / MEDIUM / LOW

### Key Levels

| Level | Value | Distance from Current | Significance |
|-------|-------|----------------------|--------------|
| **Resistance** | {value} | {+pct}% | {e.g., Donchian upper, 52-week high} |
| **Support** | {value} | {−pct}% | {e.g., SuperTrend trail, BB lower} |
| Support | {value} | {−pct}% | {e.g., Structural support} |
| Nearest Support | {ta_nearest_support} | {−pct}% | {closest support level} |

### Structure Signals

| Signal | Value | Interpretation |
|--------|-------|----------------|
| HH (Higher High) | {bool/count} | Bullish structure |
| HL (Higher Low) | {bool/count} | Bullish structure |
| LH (Lower High) | {bool/count} | Bearish structure |
| LL (Lower Low) | {bool/count} | Bearish structure |
| BOS (Break of Structure) | {bool/count} | Trend continuation |
| CHoCH (Change of Character) | {bool/count} | Potential reversal |
| Trend Label | {ta_trend} | {Bullish/Bearish} |

### Structure Assessment
- **Pattern:** {Uptrend (HH/HL), Downtrend (LH/LL), or Range-bound}
- **Key levels:** {Price position relative to support/resistance}
- **Recent breaks:** {Any BOS or CHoCH signals}
- **Support touches:** {How well-established the support is}

### Structure Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| {Factor 1} | +/-{n} | {n}% | +/−{value} |
| {Factor 2} | +/-{n} | {n}% | +/−{value} |
| {Factor 3} | +/-{n} | {n}% | +/−{value} |
| {Factor 4} | +/-{n} | {n}% | +/−{value} |
| **Structure Score** | | **100%** | **+/−{total} / 3.0** |

**Structure Verdict:** {1-sentence summary}

### Strategy Alignment
{1-2 sentences: Does the recommended strategy rely on structural signals? Are they aligned?}

---

## 5. Volatility Analysis

**Signal:** LOW RISK / NORMAL / HIGH RISK | **Confidence:** HIGH / MEDIUM / LOW

### Current Indicators

| Indicator | Value | Assessment |
|-----------|-------|------------|
| ATR(14) | {value} | {Absolute level} |
| ATR Percentile | {value}% | {Low/Normal/High} |
| BB Width | {value} | {Contraction / Expansion / Moderate} |
| %B | {value} | {0=lower band, 0.5=middle, 1=upper} |
| BB Upper | {value} | {Resistance level} |
| BB Lower | {value} | {Support level} |
| HV(20) | {value}% | {Rising / Falling / Stable} |
| Park Volatility | {value}% | {Range-based estimate} |
| GARCH Vol | {value} | {Forecast direction} |
| ATR Stop Distance | {value} | {Suggested stop level} |

### Volatility Assessment
- **Volatility Level:** {ATR percentile interpretation}
- **Band Position:** {Price position within Bollinger Bands}
- **Volatility Trend:** {HV and GARCH direction}
- **Breakout Potential:** {BB width contraction = potential breakout; expansion = trend acceleration}
- **Suggested Stop:** {ATR-based stop distance and level}

### Volatility Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| {Factor 1} | +/-{n} | {n}% | +/−{value} |
| {Factor 2} | +/-{n} | {n}% | +/−{value} |
| {Factor 3} | +/-{n} | {n}% | +/−{value} |
| {Factor 4} | +/-{n} | {n}% | +/−{value} |
| **Volatility Score** | | **100%** | **+/−{total} / 3.0** |

**Volatility Verdict:** {1-sentence summary}

### Strategy Alignment
{1-2 sentences: Does the strategy use volatility-based entries/exits? Is current volatility favorable?}

---

## 6. Volume Analysis

**Signal:** BULLISH / MIXED / BEARISH | **Confidence:** HIGH / MEDIUM / LOW

### Current Indicators

| Indicator | Value | Assessment |
|-----------|-------|------------|
| OBV | {value} | {Rising / Falling / Stable} |
| CMF(20) | {value} | {Buying / Selling pressure} |
| OFI | {value} | {Order flow imbalance} |
| VWAP | {value} | Price vs VWAP: {above/below} |
| ADL | {value} | {Accumulation / Distribution} |
| MFI(14) | {value} | {Overbought / Normal / Oversold} |
| Volume Z-Score | {value} | {Above / Below average} |
| Volume Percentile | {value}% | {Intensity} |
| EMV(14) | {value} | {Ease of movement} |

### Volume Assessment
- **Buying/Selling Pressure:** {CMF + OFI combined reading}
- **Volume Trend:** {OBV direction vs price direction — confirmation or divergence?}
- **Volume Intensity:** {Z-Score and percentile}
- **Smart Money:** {ADL direction — accumulation or distribution}
- **Divergence Warning:** {Price vs volume divergence if present}

### Volume Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| {Factor 1} | +/-{n} | {n}% | +/−{value} |
| {Factor 2} | +/-{n} | {n}% | +/−{value} |
| {Factor 3} | +/-{n} | {n}% | +/−{value} |
| {Factor 4} | +/-{n} | {n}% | +/−{value} |
| **Volume Score** | | **100%** | **+/−{total} / 3.0** |

**Volume Verdict:** {1-sentence summary}

### Strategy Alignment
{1-2 sentences: Does the recommended strategy use volume confirmation? Is volume supporting the price action?}

---

## 7. Regime Analysis

**Signal:** BULL / NEUTRAL / BEAR | **Confidence:** HIGH / MEDIUM / LOW

### HMM Regime Probabilities

| Regime State | Probability | Interpretation |
|-------------|-------------|----------------|
| State 0 | {ta_hmm_regime_prob_0}% | {Bull/Bear/Neutral} |
| State 1 | {ta_hmm_regime_prob_1}% | {Bull/Bear/Neutral} |
| State 2 | {ta_hmm_regime_prob_2}% | {Bull/Bear/Neutral} |

### Regime Assessment
- **Dominant Regime:** {Highest probability state and what it means}
- **Regime Stability:** {Has the regime changed in the last ~30 days? How long has it been in current state?}
- **GARCH Context:** {Volatility trend within current regime}
- **Trend vs Regime Divergence:** {Any conflict between trend indicators and regime model?}

### Regime Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| {Factor 1} | +/-{n} | {n}% | +/−{value} |
| {Factor 2} | +/-{n} | {n}% | +/−{value} |
| {Factor 3} | +/-{n} | {n}% | +/−{value} |
| **Regime Score** | | **100%** | **+/−{total} / 3.0** |

**Regime Verdict:** {1-sentence summary}

### Strategy Alignment
{1-2 sentences: What regime does the recommended strategy perform best in? Is the current regime aligned?}

---

## Signal Synthesis

### Aggregate Score Summary

| # | Dimension | Signal | Score (/3.0) | Weight | Weighted |
|---|-----------|--------|-------------|--------|----------|
| 1 | **Trend** | {Signal} | {+/−val} | {n}% | {+/−val} |
| 2 | **Momentum** | {Signal} | {+/−val} | {n}% | {+/−val} |
| 3 | **Return** | {Signal} | {+/−val} | {n}% | {+/−val} |
| 4 | **Structure** | {Signal} | {+/−val} | {n}% | {+/−val} |
| 5 | **Volatility** | {Signal} | {+/−val} | {n}% | {+/−val} |
| 6 | **Volume** | {Signal} | {+/−val} | {n}% | {+/−val} |
| 7 | **Regime** | {Signal} | {+/−val} | {n}% | {+/−val} |
| | **AGGREGATE** | | | **100%** | **+/−{total}** |

### Score Interpretation

| Range | Signal | Interpretation |
|-------|--------|---------------|
| +2.0 to +3.0 | Strong Bullish | All dimensions aligned — strong buy signal |
| +0.5 to +1.9 | Mildly Bullish | Trend favors longs but monitor for reversals |
| **-0.5 to +0.4** | **Neutral / Wait** | **Mixed signals — do not initiate new positions** |
| -0.5 to -1.9 | Mildly Bearish | Caution warranted, consider reducing exposure |
| -2.0 to -3.0 | Strong Bearish | All dimensions negative — avoid longs |

**Aggregate Score: {+/−val} — {SIGNAL}**

{1-2 sentence narrative explaining how the aggregate score was reached.}

### Signal Determination
- **Overall Signal:** BUY / SELL / HOLD / WAIT
- **Strength:** Strong / Normal / Weak
- **Confidence:** High / Medium / Low

### Supporting Indicators (Top 3 per Dimension)

| Dimension | Indicator 1 | Indicator 2 | Indicator 3 |
|-----------|------------|------------|------------|
| Trend | {name} | {name} | {name} |
| Momentum | {name} | {name} | {name} |
| Return | {name} | {name} | {name} |
| Structure | {name} | {name} | {name} |
| Volatility | {name} | {name} | {name} |
| Volume | {name} | {name} | {name} |
| Regime | {name} | {name} | {name} |

### Conflicting Indicators
- **{Conflict 1}:** {description — what contradicts what}
- **{Conflict 2}:** {description}
- **{Conflict 3}:** {description}

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | {e.g., DO NOT ENTER} | {reason} |
| **Current holders** | {e.g., HOLD / REDUCE} | {reason} |
| **Traders** | {e.g., AVOID} | {reason} |
| **Value investors** | {e.g., PATIENCE} | {reason} |

- **Entry:** {Specific conditions to trigger entry}
- **Stop-Loss:** {Level, e.g., "Below nearest support or ATR-based"}
- **Target:** {Level, e.g., "Nearest resistance or BB upper"}
- **Position Sizing:** {If applicable}
- **Max Holding Period:** {If applicable}

### Risk Factors
- **{Risk 1}:** {e.g., "Regime shift to bear if HMM prob_1 rises above prob_0"}
- **{Risk 2}:** {e.g., "Volume declining — potential false breakout"}
- **{Risk 3}:** {e.g., "RSI overbought — mean reversion risk"}

### When This Signal Is Invalidated
- **{Condition 1}:** {e.g., "Close below EMA200"} → Signal becomes {NEW_SIGNAL}
- **{Condition 2}:** {e.g., "RSI drops below 30"} → Signal becomes {NEW_SIGNAL}
- **{Condition 3}:** {e.g., "SuperTrend flips to -1"} → Signal becomes {NEW_SIGNAL}

### Key Levels to Watch

| Event | Price Level | Distance | Action Trigger |
|-------|------------|----------|----------------|
| Stop loss trigger | {value} | {−pct}% | {condition} |
| Support 1 | {value} | {−pct}% | {condition} |
| Support 2 | {value} | {−pct}% | {condition} |
| Entry zone | {low–high} | {range} | {condition} |
| Resistance 1 | {value} | {+pct}% | {condition} |
| Resistance 2 | {value} | {+pct}% | {condition} |

---

## Next Steps

- **{Action item 1}:** {e.g., "Monitor for pullback to support at ~X"}
- **{Action item 2}:** {e.g., "Watch MACD histogram for reversal"}
- **{Re-evaluation trigger}:** {e.g., "Re-run evaluation if close below EMA20 or above resistance"}
- **{Strategy note}:** {e.g., "If entering, use {strategy_name} entry rules from strategy report"}
- **{Long-term note}:** {e.g., "Consider as long-term hold if applicable"}
- **{Alerts}:** {e.g., "Set alerts at support X and resistance Y"}

---

*Report generated: {actual_date} | Data point: {evaluation_date} → `{actual_date}` | Data: `data/analysis-data/{ticker}.csv` ({total_rows} rows) | Strategy: `data/strategy/{ticker}/{latest_strategy_date}.md`*
