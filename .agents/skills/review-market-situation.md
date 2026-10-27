# Market Situation Review Skill

## Objective

Assess the market situation for `{ticker}` as of `{evaluation_date}` and recommend a buy / sell / hold signal. Evaluate across 7 dimensions: trend, momentum, return, structure, volatility, volume, and regime. Cross-reference findings with the most recent backtested strategy results from `data/reports/strategies/{ticker}/`. Output the evaluation report to `data/reports/evaluation/{ticker}/{evaluation_date}_evaluation.md`.

## Parameters

- `{ticker}` — Ticker symbol (e.g. `NG.L`, `BP.L`, `HSBA.L`)
- `{evaluation_date}` — The date to evaluate as of (format: `YYYY-MM-DD`). Defaults to the latest date in the CSV if not specified. Used for backtesting / historical verification of signals.
- Data source: `data/analysis-data/{ticker}.csv`
- Strategy reference: `data/reports/strategies/{ticker}/` — the most recent `.md` file in this directory (must exist before running this skill)
- TA knowledge base: `docs/all_technical_analysis.md`
- Output: `data/reports/evaluation/{ticker}/{evaluation_date}_evaluation.md` (where `{evaluation_date}` is the specified date or the last date in the CSV)

## Data Loading — Use Direct File Tools (Do NOT Write Inline Python)

These CSV files have **108 columns** and **1,800–3,600 rows** (~7–8 MB each). Never write inline Python via `shell` to read them — it spawns a new Python process each time, takes 15–30s per call, and is fragile.

**Fastest approach — use the companion script (one call, all data):**

```bash
python app/analyse-market-data/get_evaluation_data.py {ticker} 2025-06-15 --latest-30
```

This outputs a single JSON with: `latest` row, all `indicators` (100+ TA columns), `52week` range, and `recent_context` (last 30 rows). Parse the JSON to extract values for each dimension.

**Date resolution:** If the specified date does not exist in the CSV (e.g. weekend/holiday), the companion script automatically falls back to the latest available date **on or before** the specified date. If the specified date is after the last row, the script uses the latest available date and notes the discrepancy in `date_range`. The `{actual_date}` field in the output reflects the resolved date. See `{actual_date}` in Step 1 for how to use the resolved date.

**NaN/null handling:** The companion script filters NaN values from the CSV output. Missing indicator values appear as `null`/`None` in the JSON. See Step 1 point 3 ("Handle missing data") for rules on how to score dimensions with null indicators.

**Fallback for columns not in companion script output:** If you need a specific column not present in the `recent_context` or `indicators` JSON output, read the raw CSV:
```bash
tail -30 data/analysis-data/{ticker}.csv
```

**Use `read` for:**
- Strategy reports in `data/reports/strategies/{ticker}/` — use `read` to read the full markdown file directly (these are text files, not CSVs)
- The TA reference doc `docs/all_technical_analysis.md` — use `read` with `limit` to get sections you need
- Any other `.md`, `.csv` (small files), or config file

## Usage Notes

- **Historical verification:** Pass `{evaluation_date}` (e.g. `2025-06-15`) to test whether this skill would have given correct advice on a past date. The evaluation uses only data available up to and including that date — no hindsight.
- **Temporal cutoff:** When `{evaluation_date}` is provided, only rows where `Date <= {evaluation_date}` are used. Rolling indicators are read at their values on the evaluation date, reflecting the data available at that time.
- **Historical data:** The companion script loads ~10 years of market data automatically.
- **Default behavior:** If `{evaluation_date}` is omitted, the script uses the latest date in the CSV (original behavior).
- **Company metadata:** The companion script resolves `company_name` and `sector` from `config/ticker_list.csv` — you do not need to manually look these up unless the script returns `null`.

## Prerequisites Check

**Before proceeding, verify that the most recent strategy file exists in `data/reports/strategies/{ticker}/`.**

- List all `.md` files in `data/reports/strategies/{ticker}/` and select the one with the most recent filename (which encodes the date).
- If the directory is empty or does NOT exist, advise the user to run the investment strategy skill first:
  > "Please run the investment strategy skill `.agents/skills/investment-strategy.md` for `{ticker}` first to generate a strategy report in `data/reports/strategies/{ticker}/`. This review skill requires the backtest results to cross-reference current signals with historically optimal strategies."
- Exit the current task until the strategy report is available.
- Record the path of the selected strategy file (e.g. `data/reports/strategies/{ticker}/2025-06-30.md`) and use it throughout the evaluation.

## Relevant Files Reference

| File | Purpose |
|------|---------|
| `data/analysis-data/{ticker}.csv` | Latest market data — OHLCV + all TA indicators (prefixed `ta_`) + P/E fundamentals |
| `data/reports/strategies/{ticker}/{latest_strategy_date}.md` | Most recent backtested strategy results — best strategies, their logic, parameters, and recommended entry/exit rules |
| `docs/all_technical_analysis.md` | TA indicator definitions and interpretation guidelines (12 sections) |
| `app/backtest/strategies/builtins.py` | 32 built-in strategy source code — read entry/exit logic for each category |
| `app/calculate-ta/README.md` | Full TA column reference with formulas and parameters |

## TA Column Quick Reference

All TA columns use the `ta_` prefix. These are the **actual CSV column names** from `data/analysis-data/{ticker}.csv`. When referencing indicators in the companion script JSON, use the same column name as the `indicators` object key.

| Dimension | Key Columns (actual CSV names) |
|-----------|-------------------------------|
| **Trend** | `ta_ema20`, `ta_ema50`, `ta_ema200`, `ta_supertrend_direction`, `ta_supertrend`, `ta_supertrend_upper`, `ta_supertrend_lower`, `ta_ma20_slope`, `ta_ma50_slope`, `ta_donchian_upper`, `ta_donchian_lower`, `ta_keltner_upper`, `ta_keltner_lower`, `ta_adx14`, `ta_plus_di14`, `ta_minus_di14`, `ta_aroon_up`, `ta_aroon_down`, `ta_price_dist_ema20`, `ta_price_dist_ema50`, `ta_price_dist_ema200`, `ta_price_ma20_ratio` |
| **Momentum** | `ta_rsi14`, `ta_macd_line`, `ta_macd_signal`, `ta_macd_histogram`, `ta_roc20`, `ta_stoch_k`, `ta_stoch_d`, `ta_williams_r`, `ta_cci`, `ta_tsi`, `ta_rsi_zscore`, `ta_rsi_percentile`, `ta_mfi14` |
| **Return** | `ta_return_5d`, `ta_return_10d`, `ta_return_20d`, `ta_performance_1m`, `ta_performance_3m`, `ta_performance_6m`, `ta_performance_1y`, `ta_alpha20`, `ta_beta20`, `ta_rs_ftse100` |
| **Structure** | `ta_swing_high`, `ta_swing_low`, `ta_swing_high_idx`, `ta_swing_low_idx`, `ta_hh`, `ta_hl`, `ta_lh`, `ta_ll`, `ta_trend`, `ta_bos`, `ta_choch`, `ta_nearest_resistance`, `ta_nearest_support`, `ta_dist_resistance`, `ta_dist_support`, `ta_breakout_strength`, `ta_support_touches` |
| **Volatility** | `ta_atr14`, `ta_normalized_atr14`, `ta_bband_upper`, `ta_bband_middle`, `ta_bband_lower`, `ta_bband_width`, `ta_bband_pctb`, `ta_hvol20`, `ta_parkinson_vol`, `ta_garch_vol`, `ta_garch_sq`, `ta_atr_stop_dist`, `ta_atr_percentile`, `ta_atr_position`, `ta_rr_ratio` |
| **Volume** | `ta_obv`, `ta_cmf`, `ta_vwap`, `ta_ofi`, `ta_log_volume`, `ta_adl`, `ta_mfi14`, `ta_emv14`, `ta_volume_osc`, `ta_volume_zscore`, `ta_volume_percentile`, `ta_obv_slope_14`, `ta_obv_slope_7` |
| **Regime** | `ta_hmm_regime`, `ta_hmm_regime_prob_0`, `ta_hmm_regime_prob_1`, `ta_hmm_regime_prob_2`, `ta_regime_label`, `ta_garch_vol`, `ta_garch_sq` |
| **Fundamentals** | `ta_eps_ttm`, `ta_pe`, `ta_div_ttm`, `ta_div_yield` |

**Note:** `ta_mfi14` and `ta_garch_vol` / `ta_garch_sq` appear in multiple dimensions (MFI is both momentum and volume; GARCH is both volatility and regime). Score each dimension independently using that dimension's interpretation — do not skip a dimension just because the column was used elsewhere.

**Common column name pitfalls (do NOT use these):**

| ❌ Wrong | ✅ Correct | ❌ Wrong | ✅ Correct |
|----------|-----------|----------|-----------|
| `ta_adx` | `ta_adx14` | `ta_ret_5d` | `ta_return_5d` |
| `ta_di_plus` | `ta_plus_di14` | `ta_ret_1m` | `ta_performance_1m` |
| `ta_di_minus` | `ta_minus_di14` | `ta_ret_3m` | `ta_performance_3m` |
| `ta_tsi25_13` | `ta_tsi` | `ta_ret_6m` | `ta_performance_6m` |
| `ta_rsi_zscore_14_20` | `ta_rsi_zscore` | `ta_ret_1y` | `ta_performance_1y` |
| `ta_rsi_percentile_14_20` | `ta_rsi_percentile` | `ta_pct_b` | `ta_bband_pctb` |
| `ta_park_volv` | `ta_parkinson_vol` | `ta_vol_osc_14_28` | `ta_volume_osc` |
| `ta_atr_percentile_14_20` | `ta_atr_percentile` | `ta_vol_zscore_20` | `ta_volume_zscore` |
| — | — | `ta_vol_percentile_20` | `ta_volume_percentile` |
| — | — | `ta_ofi_slope` | `ta_obv_slope_14` (use OBV slope instead) |

## Evaluation Methodology

### Token Limit Handling

When writing evaluation report:
- Write the file in sections using separate write/edit calls
- Start with the header and executive summary
- Append step 1, 2, 3, etc. separately
- Each chunk should be self-contained and no more than ~2000 words
- Use `edit` to insert sections between existing content, or `write` to overwrite with growing content

### Report Depth Guidelines

Choose report depth based on signal agreement across the 7 dimensions:

| Agreement Level | Condition | Report Structure |
|----------------|-----------|-----------------|
| **Full detail** | 5+ dimensions agree AND signal is clear (BUY/SELL) OR signals are mixed | Executive Summary (all tables) + all 7 detailed sections + Signal Synthesis. Use the full template. |
| **Condensed** | 5+ dimensions agree, signal is clear | Executive Summary (all tables) + **only the 3 most decisive dimensions** detailed + Signal Synthesis. Other 4 dimensions summarized as: "{Dimension}: {Signal} ({score}/100%). See Dimension Overview table." |
| **Minimal** | 6+ dimensions agree, signal is STRONG BUY/SELL | Executive Summary with full tables + Signal Synthesis only. One-liner per dimension: "**{Dimension}**: {Signal} {score}. {1-sentence rationale}." No detailed sections. |
| **Expanded** | <4 dimensions agree in either direction (highly mixed) | Full detail + add a "**Divergence Analysis**" subsection under Signal Synthesis explaining why dimensions conflict and which dimensions should take priority. |

**Rule of thumb:** If the executive summary tables alone convey the signal clearly (5+ agree, score >+1.5 or <-1.5), you can condense. If the signal depends on nuanced interpretation or conflicts exist, expand all 7 sections fully.

### Scoring Scale — Unified -3.0 to +3.0

All 7 dimensions use the **same weighted scoring system**: each factor is rated from **-1.0 to +1.0**, weighted by importance (weights per dimension sum to 100%). The weighted sum is scaled to produce a final score from **-3.0 to +3.0**.

**How to compute per-dimension scores:**

1. Identify 3–5 key factors for the dimension (e.g., for Trend: MA alignment, SuperTrend, MA slopes, ADX strength)
2. Rate each factor: **+1.0** = strongly bullish, **+0.5** = mildly bullish, **0.0** = neutral, **-0.5** = mildly bearish, **-1.0** = strongly bearish
3. Assign weights that sum to 100% (e.g., MA alignment 40%, SuperTrend 30%, ADX 30%)
4. Compute weighted score = Σ(factor_rating × weight) × 3
   - Weights must sum to 100% (e.g., MA alignment 40%, SuperTrend 30%, ADX 30%)
   - The `× 3` scales the weighted sum (range -1.0 to +1.0) to the final -3.0 to +3.0 range
   - Example: 3 factors rated +1.0 each, weights 40/30/30 → (0.4 + 0.3 + 0.3) × 3 = **+3.0**
   - Shortcut: since weights sum to 1.0 and all factors share the same rating, `score = rating × 3`
5. The total will be between **-3.0** (all factors strongly bearish) and **+3.0** (all factors strongly bullish)

**Per-dimension interpretation:**

| Score | Signal | Meaning |
|-------|--------|---------|
| +2.0 to +3.0 | Strong Bullish | All indicators aligned — bullish conviction |
| +0.5 to +1.9 | Mildly Bullish | Bias toward longs, but not all indicators agree |
| -0.4 to +0.4 | Neutral | Mixed signals, no clear directional bias |
| -1.9 to -0.5 | Mildly Bearish | Bias against longs, monitor for reversal |
| -3.0 to -2.0 | Strong Bearish | All indicators negative — avoid longs |

**Per-dimension confidence:**
- **High**: 4+ indicators agree, <1 null
- **Medium**: 2–3 indicators agree, or 1–2 null
- **Low**: Conflicting indicators, or >3 null values in this dimension's key columns

**Aggregate score**: Sum of all 7 weighted dimension scores. The aggregate determines the final signal (see Step 9).

### Step 1: Load & Inspect Data for Evaluation Date

1. **Run the companion script** to get all data in one call:
   ```bash
   python app/analyse-market-data/get_evaluation_data.py {ticker} {evaluation_date} --latest-30
   ```
   The script handles date resolution internally — use `{actual_date}` (extracted in Step 1.2) as the effective evaluation date for all scoring.

2. **Extract the following from the JSON:**
   - `{actual_date}` = `date_range.end` — the effective evaluation date (see Data Loading section for date resolution rules)
   - `{price}` = `latest.close` — current price on the evaluation date
   - `{data_range_start}` = `date_range.start` — earliest date in the dataset
   - `{total_rows}` = `total_rows` — total rows in the file (for reporting; historical cutoff count is not tracked by the script)
   - `{high_52w}` = `52week.high_52w`, `{low_52w}` = `52week.low_52w`
   - `{indicators}` = the `indicators` object — all 81+ TA column values as key-value pairs
   - `{recent_context}` = the `recent_context` array — last 30 rows for regime/volatility trend checks

3. **Handle missing data:**
   - If any indicator value is `null`/`None`, **skip that indicator** in scoring
   - If >3 indicators in a dimension are null, mark that dimension's confidence as **Low**
   - The companion script already filters NaN values from the CSV output

4. **Multi-row computations — General rule:** Whenever a step asks for trend direction, rising/falling assessment, counts, averages, or recent behavior (e.g., "is volatility rising?", "note recent flips", "compute average", "check for BOS signals"), use the following approach:

    **Primary: `recent_context` from companion script (already fetched in Step 1.1)**
    - `recent_context` is the JSON array of the last 30 rows — iterate it to compute:
      - **Directional trend** (rising/falling): Compare entry index 0 (oldest) vs index -1 (newest). `newest > oldest × 1.05` = rising; `newest < oldest × 0.95` = falling
      - **Counts** (e.g., number of HH, HL, BOS, CHoCH in recent window): Sum/count boolean or integer values across all entries
      - **Averages** (e.g., average forward return): Sum values and divide by count
      - **Stability** (e.g., regime changes): Count unique values across all entries. >2 = unstable
      - **Recent flips** (e.g., SuperTrend direction changes): Count transitions between +1/-1 between consecutive entries
    - Example (conceptual): iterate `recent_context` array, collect `ta_regime_label` values, count unique → `len(set(entry["ta_regime_label"] for entry in recent_context))`

    **Fallback: `tail` when companion script data is insufficient**
    - If `recent_context` doesn't contain a needed column, use `tail -30 data/analysis-data/{ticker}.csv` as fallback
    - `recent_context` includes `date`, `close`, and regime columns; the full CSV has all columns (volume, BB, MACD, OBV, swing points, etc.)
    - Apply the same computation patterns (directional, counts, averages, stability, flips)

5. **For company name and sector** (needed in the report header):
   - Read `config/ticker_list.csv` using `read` to find the row matching `{ticker}`
   - Extract the company name and sector columns

6. **Extract strategy data ONCE** (read the strategy report here, reference in Steps 2–8):
    - Read the latest strategy file from `data/reports/strategies/{ticker}/` (path recorded in Prerequisites Check) using `read`
    - Extract the following into a structured summary for use in all subsequent steps:

    ```
    Strategy Data (from Step 1):
    - Best strategy name: {name}
    - Strategy type: {trend-following / mean-reversion / breakout / volatility / other}
    - Entry conditions:
      a) {condition 1} → Current: {value} → Match: ✅/❌
      b) {condition 2} → Current: {value} → Match: ✅/❌
      c) {condition 3} → Current: {value} → Match: ✅/❌
    - Exit/stop conditions: {summary}
    - Preferred regime: {bull/bear/neutral/all}
    - Preferred volatility: {low/medium/high}
    - Volume requirements: {confirmation needed? / no volume filter / etc.}
    - Holding period: {short-term/medium/long-term}
    ```

    **Use this Strategy Data block throughout Steps 2–8.** Do NOT re-read the strategy file. For each dimension, check whether the current state matches the strategy's entry/exit/regime requirements. Use the format: "Strategy Data → {condition}: Current {value} → Match ✅/❌". Each dimension step below has a specific question to answer.

### Step 2: Evaluate Trend (Score: -3.0 to +3.0)

Read the latest values and compute signals:

1. **EMA alignment**: Is `ta_ema20 > ta_ema50 > ta_ema200`? (bullish) or reversed? (bearish)
2. **SuperTrend**: `ta_supertrend_direction` — +1 = bullish, -1 = bearish. Note recent flips using the multi-row computation approach (Step 1.4).
3. **MA slopes**: `ta_ma20_slope`, `ta_ma50_slope` — positive = uptrend, negative = downtrend
4. **ADX/DI**: `ta_adx14` > 25 = strong trend. `ta_plus_di14 > ta_minus_di14` = bullish trend, reversed = bearish
5. **Donchian**: Is price near `ta_donchian_upper` (breakout) or `ta_donchian_lower` (breakdown)?
6. **Keltner**: Is price above/below the Keltner bands?
7. **Price vs MAs**: Calculate `price / ta_ema20 - 1` — positive = price above EMA20

**Strategy Alignment:** Check if the current trend ({bullish/bearish/neutral}) matches the strategy's trend-following entry criteria. Format: "Strategy Data → {condition}: Current {value} → Match ✅/❌"

**Output:** Trend score (-3.0 to +3.0), key indicator values, alignment with best strategy.

### Step 3: Evaluate Momentum (Score: -3.0 to +3.0)

1. **RSI(14)**: `<30` oversold, `30–50` weak, `50–70` normal, `>70` overbought. Also check `ta_rsi_zscore` and `ta_rsi_percentile` for statistical context.
2. **MACD**: `ta_macd_line > ta_macd_signal` = bullish. Check histogram direction (`ta_macd_histogram` rising/falling) using the multi-row computation approach (Step 1.4).
3. **ROC(20)**: `ta_roc20 > 0` = positive momentum
4. **Williams %R**: `ta_williams_r > -20` overbought, `< -80` oversold
5. **CCI**: `ta_cci > 100` overbought, `< -100` oversold
6. **TSI**: Check sign and slope of `ta_tsi`
7. **MFI(14)**: `ta_mfi14 > 80` overbought, `< 20` oversold (volume-weighted RSI)

**Strategy Alignment:** Check if current momentum ({bullish/bearish/neutral}) is consistent with the strategy's momentum-based entry conditions. Format: "Strategy Data → {condition}: Current {value} → Match ✅/❌"

**Output:** Momentum score (-3.0 to +3.0), key indicator values, overbought/oversold assessment, alignment with best strategy.

### Step 4: Evaluate Return (Score: -3.0 to +3.0)

1. **Recent performance**: `ta_performance_1m`, `ta_performance_3m`, `ta_performance_6m`, `ta_performance_1y`
   - Strong positive = momentum continues, watch for exhaustion
   - Strong negative = potential reversal opportunity or continued downtrend
2. **Forward returns (context)**: `ta_return_5d`, `ta_return_10d`, `ta_return_20d`
   - These are historical forward returns — compute average across recent periods using the multi-row computation approach (Step 1.4)
   - If most recent 5d/10d/20d forward returns have been positive, trend may continue
3. **Alpha/Beta**: `ta_alpha20`, `ta_beta20` vs ^FTSE
   - Positive alpha = outperforming benchmark
   - Beta > 1 = more volatile than market; Beta < 1 = less volatile
4. **Relative strength**: `ta_rs_ftse100`
   - Rising = outperforming FTSE 100; Falling = underperforming. Check trend using the multi-row computation approach (Step 1.4).

**Strategy Alignment:** Check if current return characteristics match the strategy's preferred holding period ({short-term/medium/long-term}) and style ({mean-reversion/momentum}). Format: "Strategy Data → {condition}: Current {value} → Match ✅/❌"

**Output:** Return score (-3.0 to +3.0), performance summary, alpha/beta context, alignment with best strategy.

### Step 5: Evaluate Structure (Score: -3.0 to +3.0)

1. **Swing points**: Check `ta_swing_high` and `ta_swing_low` for recent swings. Count occurrences using the multi-row computation approach (Step 1.4).
2. **HH/HL vs LH/LL**:
   - `ta_hh` and `ta_hl` = bullish structure; `ta_lh` and `ta_ll` = bearish structure. Count occurrences using the multi-row computation approach (Step 1.4).
3. **Break of Structure (BOS)**: `ta_bos` — bullish break above previous high, or bearish break below previous low. Count recent events using the multi-row computation approach (Step 1.4).
4. **Change of Character (CHoCH)**: `ta_choch` — signals trend reversal. Count recent events using the multi-row computation approach (Step 1.4).
5. **Support/Resistance**: `ta_nearest_support`, `ta_nearest_resistance`
   - Current price proximity to these levels
6. **Trend label**: `ta_trend` — if available, direct trend classification

**Strategy Alignment:** Check if current structural conditions ({bullish/bearish/range}) align with the strategy's structural entry rules (BOS, CHoCH, HH/HL). Format: "Strategy Data → {condition}: Current {value} → Match ✅/❌"

**Output:** Structure score (-3.0 to +3.0), swing analysis, S/R levels, alignment with best strategy.

### Step 6: Evaluate Volatility (Score: -3.0 to +3.0)

1. **ATR(14)**: `ta_atr14` — absolute volatility level. Compare to historical percentile `ta_atr_percentile`
2. **Bollinger Bands**:
   - `ta_bband_pctb` — position within bands (0 = lower band, 1 = upper band)
   - `ta_bband_width` — band width contraction = potential breakout; expansion = trend acceleration
   - Price near lower band = potential bounce; near upper = potential pullback
3. **Historical Volatility**: `ta_hvol20` — rising or falling? Check using the multi-row computation approach (Step 1.4).
4. **Parkinson Volatility**: `ta_parkinson_vol` — range-based volatility estimate
5. **GARCH forecast**: `ta_garch_vol` — predicted future volatility
6. **ATR Stop Distance**: `ta_atr_stop_dist` — suggested stop distance
7. **ATR Percentile**: `ta_atr_percentile` — where current ATR sits historically

**Strategy Alignment:** Check if current volatility conditions ({low/normal/high}) match the strategy's preferred volatility regime. Format: "Strategy Data → {condition}: Current {value} → Match ✅/❌"

**Output:** Volatility score (-3.0 to +3.0), current level, trend in volatility, breakout/bounce probability, alignment with best strategy.

### Step 7: Evaluate Volume (Score: -3.0 to +3.0)

1. **OBV**: `ta_obv` — rising OBV confirms price trend, falling OBV warns of divergence. Check trend using the multi-row computation approach (Step 1.4).
2. **CMF(20)**: `ta_cmf` — `>0` = buying pressure, `<0` = selling pressure. Strength proportional to magnitude.
3. **VWAP**: `ta_vwap` — price above VWAP = bullish intraday trend
4. **OFI**: `ta_ofi` — `>0` = order flow imbalance favoring buyers. Check `ta_obv_slope_14` (OBV slope).
5. **ADL**: `ta_adl` — accumulating/distributing pressure
6. **MFI(14)**: `ta_mfi14` — volume-weighted RSI, `>80` overbought, `<20` oversold
7. **Volume metrics**: `ta_volume_zscore`, `ta_volume_percentile` — is current volume above/below average?
8. **EMV(14)**: `ta_emv14` — ease of movement, positive = price rising with little effort

**Strategy Alignment:** Check if current volume conditions ({bullish/mixed/bearish}) support the price direction, per the strategy's volume confirmation requirements. Format: "Strategy Data → {condition}: Current {value} → Match ✅/❌"

**Output:** Volume score (-3.0 to +3.0), buying/selling pressure assessment, confirmation/divergence with price, alignment with best strategy.

### Step 8: Evaluate Regime (Score: -3.0 to +3.0)

1. **HMM Regime Probabilities**:
   - `ta_hmm_regime_prob_0` — probability of state 0 (typically bullish)
   - `ta_hmm_regime_prob_1` — probability of state 1 (typically bearish)
   - `ta_hmm_regime_prob_2` — probability of state 2 (typically neutral/sideways)
   - Highest probability = dominant regime
2. **Regime label**: `ta_regime_label` — if available, direct classification
3. **GARCH vol trend**: Rising GARCH vol in bear regime = high risk; falling = stabilization
4. **Regime stability**: Check if regime has changed recently (scan the last ~30 rows) using the multi-row computation approach (Step 1.4).

**Strategy Alignment:** Check if the current regime ({bull/bear/neutral}) matches the regime where the strategy performs best. Format: "Strategy Data → {condition}: Current {value} → Match ✅/❌"

**Output:** Regime score (-3.0 to +3.0), dominant regime, regime stability, alignment with best strategy.

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
5. **Strategy alignment**: Does current data match the entry conditions from the Strategy Data extracted in Step 1?
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
**Strategy Reference:** `data/reports/strategies/{ticker}/{latest_strategy_date}.md`

---

## Executive Summary

**Signal:** STRONG BUY / BUY / HOLD / WAIT / SELL / STRONG SELL
**Confidence:** High / Medium / Low

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🟢 BULLISH / 🟡 CAUTIOUS / 🔴 BEARISH | 🟢 High / 🟡 Medium / 🔴 Low | {1-line key driver} |
| **Momentum** | 🟢 BULLISH / 🟡 CAUTIOUS / 🔴 BEARISH | 🟢 High / 🟡 Medium / 🔴 Low | {1-line key driver} |
| **Return** | 🟢 POSITIVE / 🟡 MIXED / 🔴 NEGATIVE | 🟢 High / 🟡 Medium / 🔴 Low | {1-line key driver} |
| **Structure** | 🟢 BULLISH / 🟡 CAUTIOUS / 🔴 BEARISH | 🟢 High / 🟡 Medium / 🔴 Low | {1-line key driver} |
| **Volatility** | 🟢 LOW / 🟡 NORMAL / 🔴 HIGH | 🟢 High / 🟡 Medium / 🔴 Low | {1-line key driver} |
| **Volume** | 🟢 BULLISH / 🟡 MIXED / 🔴 BEARISH | 🟢 High / 🟡 Medium / 🔴 Low | {1-line key driver} |
| **Regime** | 🟢 BULL / 🟡 NEUTRAL / 🔴 BEAR | 🟢 High / 🟡 Medium / 🔴 Low | {1-line key driver} |
| **Overall** | 🟢 STRONG BUY / 🟢 BUY / 🟡 HOLD / 🟠 WAIT / 🟠 SELL / 🔴 STRONG SELL | 🟢 High / 🟡 Medium / 🔴 Low | {1-line key driver} |

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

**Strategy Verdict:** {1-2 sentences: whether current conditions match the entry criteria from the Strategy Data extracted in Step 1}

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
| **Trend Score** | | **100%** | **+/−{total}** (range: -3.0 to +3.0) |

**Trend Verdict:** {1-sentence summary}

### Strategy Alignment
{1-2 sentences: Check if the current trend matches the strategy's trend-following entry criteria. Use format: "Strategy Data → {condition}: Current {value} → Match ✅/❌"}

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
| **Momentum Score** | | **100%** | **+/−{total}** (range: -3.0 to +3.0) |

**Momentum Verdict:** {1-sentence summary}

### Strategy Alignment
{1-2 sentences: Check if current momentum conditions are consistent with the strategy's entry conditions. Use format: "Strategy Data → {condition}: Current {value} → Match ✅/❌"}

---

## 3. Return Analysis

**Signal:** POSITIVE / MIXED / NEGATIVE | **Confidence:** HIGH / MEDIUM / LOW

### Past Performance

| Period | Return | Assessment |
|--------|--------|------------|
| 1 Month | {ta_performance_1m}% | {assessment} |
| 3 Months | {ta_performance_3m}% | {assessment} |
| 6 Months | {ta_performance_6m}% | {assessment} |
| 1 Year | {ta_performance_1y}% | {assessment} |

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

*Compute mean and std dev by iterating `recent_context` array: collect all `ta_return_5d` values → mean = sum/count, std = sqrt(mean((x - mean)^2)). Repeat for 10d and 20d columns.*

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
| **Return Score** | | **100%** | **+/−{total}** (range: -3.0 to +3.0) |

**Return Verdict:** {1-sentence summary}

### Strategy Alignment
{1-2 sentences: Check if current return characteristics match the strategy's preferred holding period ({short-term/medium/long-term}) and style ({mean-reversion/momentum}). Use format: "Strategy Data → {condition}: Current {value} → Match ✅/❌"}

---

## 4. Structure Analysis

**Signal:** BULLISH / CAUTIOUS / BEARISH | **Confidence:** HIGH / MEDIUM / LOW

### Key Levels

| Level | Value | Distance from Current | Significance |
|-------|-------|----------------------|--------------|
| **Resistance** | {value} | {+pct}% | {e.g., Donchian upper, 52-week high} |
| Nearest Resistance | {ta_nearest_resistance} | {+pct}% | {closest resistance level} |
| **Support** | {value} | {−pct}% | {e.g., SuperTrend trail, BB lower} |
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
| **Structure Score** | | **100%** | **+/−{total}** (range: -3.0 to +3.0) |

**Structure Verdict:** {1-sentence summary}

### Strategy Alignment
{1-2 sentences: Check if current structural conditions align with the strategy's structural entry rules. Use format: "Strategy Data → {condition}: Current {value} → Match ✅/❌"}

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
| **Volatility Score** | | **100%** | **+/−{total}** (range: -3.0 to +3.0) |

**Volatility Verdict:** {1-sentence summary}

### Strategy Alignment
{1-2 sentences: Check if current volatility conditions match the strategy's preferred volatility regime. Use format: "Strategy Data → {condition}: Current {value} → Match ✅/❌"}

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
| **Volume Score** | | **100%** | **+/−{total}** (range: -3.0 to +3.0) |

**Volume Verdict:** {1-sentence summary}

### Strategy Alignment
{1-2 sentences: Check if current volume conditions support the price direction per the strategy's volume requirements. Use format: "Strategy Data → {condition}: Current {value} → Match ✅/❌"}

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
- **Regime Stability:** {Has the regime changed in the last ~30 rows? How long has it been in the current state?}
- **GARCH Context:** {Volatility trend within current regime}
- **Trend vs Regime Divergence:** {Any conflict between trend indicators and regime model?}

### Regime Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| {Factor 1} | +/-{n} | {n}% | +/−{value} |
| {Factor 2} | +/-{n} | {n}% | +/−{value} |
| {Factor 3} | +/-{n} | {n}% | +/−{value} |
| **Regime Score** | | **100%** | **+/−{total}** (range: -3.0 to +3.0) |

**Regime Verdict:** {1-sentence summary}

### Strategy Alignment
{1-2 sentences: Check if the current regime ({bull/bear/neutral}) matches the regime where the strategy performs best. Use format: "Strategy Data → {condition}: Current {value} → Match ✅/❌"}

---

## Signal Synthesis

### Aggregate Score Summary

| # | Dimension | Signal | Score (-3.0 to +3.0) | Weight | Weighted |
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
| **-0.4 to +0.4** | **Neutral / Wait** | **Mixed signals — do not initiate new positions** |
| -1.9 to -0.5 | Mildly Bearish | Caution warranted, consider reducing exposure |
| -3.0 to -2.0 | Strong Bearish | All dimensions negative — avoid longs |

**Aggregate Score: {+/−val} — {SIGNAL}**

{1-2 sentence narrative explaining how the aggregate score was reached.}

### Signal Determination
- **Overall Signal:** BUY / SELL / HOLD / WAIT
- **Strength:** Strong (|score| > 2.0) / Normal (0.5 < |score| ≤ 2.0) / Weak (|score| ≤ 0.5)
- **Confidence:** Derived from per-dimension confidence — **High** if ≥ 5 dimensions rated High; **Medium** if ≥ 4 dimensions rated High or Medium (and none Low); **Low** if ≥ 3 dimensions rated Low, or if there are > 2 conflicting dimensions

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
- **{Strategy note}:** {e.g., "If entering, use entry rules from the Strategy Data extracted in Step 1"}
- **{Long-term note}:** {e.g., "Consider as long-term hold if applicable"}
- **{Alerts}:** {e.g., "Set alerts at support X and resistance Y"}

---

*Report generated: {actual_date} | Data point: {evaluation_date} → `{actual_date}` | Data: `data/analysis-data/{ticker}.csv` ({total_rows} rows) | Strategy: `data/reports/strategies/{ticker}/{latest_strategy_date}.md`*
