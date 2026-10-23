# Market Situation Review Skill

## Objective

Assess the current market situation for `{ticker}` based on the latest available data and recommend a buy / sell / hold signal. Evaluate across 7 dimensions: trend, momentum, return, structure, volatility, volume, and regime. Cross-reference findings with the most recent backtested strategy results from `data/strategy/{ticker}/`. Output the evaluation report to `data/reports/evaluation/{ticker}/{latest_market_data_date}_evaluation.md`.

## Parameters

- `{ticker}` — Ticker symbol (e.g. `NG.L`, `BP.L`, `HSBA.L`)
- Data source: `data/analysis-data/{ticker}.csv`
- Strategy reference: `data/strategy/{ticker}/` — the most recent `.md` file in this directory (must exist before running this skill)
- TA knowledge base: `docs/all_technical_analysis.md`
- Output: `data/reports/evaluation/{ticker}/{latest_date}_evaluation.md` (where `{latest_date}` is the last date in the CSV, formatted as `YYYY-MM-DD`)

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

### Step 1: Load & Inspect Latest Data

1. Load `data/analysis-data/{ticker}.csv`
2. Identify the latest date (`df["Date"].max()`) — this becomes `{latest_date}` in the output filename
3. Read the LAST row (most recent data point) and the preceding ~20 rows for context
4. Record: current price, date range, total rows, column count
5. Check for any NaN values in key columns

### Step 2: Evaluate Trend (Score: Bearish / Neutral / Bullish)

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

**Output:** Trend score (1-5), key indicator values, alignment with best strategy.

### Step 3: Evaluate Momentum (Score: Bearish / Neutral / Bullish)

1. **RSI(14)**: `<30` oversold, `30-50` weak, `50-70` normal, `>70` overbought. Also check `ta_rsi_zscore_14_20` and `ta_rsi_percentile_14_20` for statistical context.
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

**Output:** Momentum score (1-5), key indicator values, overbought/oversold assessment, alignment with best strategy.

### Step 4: Evaluate Return (Score: Bearish / Neutral / Bullish)

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

**Output:** Return score (1-5), performance summary, alpha/beta context, alignment with best strategy.

### Step 5: Evaluate Structure (Score: Bearish / Neutral / Bullish)

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

**Output:** Structure score (1-5), swing analysis, S/R levels, alignment with best strategy.

### Step 6: Evaluate Volatility (Score: Low / Normal / High — and implication)

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

### Step 7: Evaluate Volume (Score: Bearish / Neutral / Bullish)

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

**Output:** Volume score (1-5), buying/selling pressure assessment, confirmation/divergence with price, alignment with best strategy.

### Step 8: Evaluate Regime (Score: Bull / Bear / Sideways)

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

**Output:** Regime score (1-5), dominant regime, regime stability, alignment with best strategy.

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

Write the evaluation report to `data/reports/evaluation/{ticker}/{latest_date}_evaluation.md` using the following template, broken into chunks.

## Output Report Template

```markdown
# Market Situation Evaluation: {Ticker}

**Date:** {latest_date}
**Ticker:** {Ticker}
**Price:** {close_price}
**Data Range:** {first_date} to {latest_date} ({total_rows} rows)
**Strategy Reference:** `data/strategy/{ticker}/{latest_strategy_date}.md`

---

## Executive Summary

**Signal:** BUY / SELL / HOLD / WAIT (strength: strong/normal/weak)
**Confidence:** High / Medium / Low

| Dimension | Score | Assessment |
|-----------|-------|------------|
| Trend | {1-5} | {Bullish/Neutral/Bearish} |
| Momentum | {1-5} | {Bullish/Neutral/Bearish} |
| Return | {1-5} | {Bullish/Neutral/Bearish} |
| Structure | {1-5} | {Bullish/Neutral/Bearish} |
| Volatility | {1-5} | {Low/Normal/High + implication} |
| Volume | {1-5} | {Bullish/Neutral/Bearish} |
| Regime | {1-5} | {Bull/Bear/Sideways} |

**Summary:** {2-3 sentence summary of why this signal was generated}

---

## 1. Trend Analysis

### Current Indicators
| Indicator | Value | Signal |
|-----------|-------|--------|
| EMA20 | {value} | |
| EMA50 | {value} | |
| EMA200 | {value} | |
| SuperTrend Direction | {1/-1} | |
| MA20 Slope | {value} | |
| MA50 Slope | {value} | |
| MA200 Slope | {value} | |
| ADX | {value} | |
| DI+ / DI- | {value} / {value} | |
| Price vs EMA20 | {pct} | |

### Trend Assessment
- **Alignment:** {EMA20 > EMA50 > EMA200 = bullish / reversed = bearish}
- **SuperTrend:** {description of current direction and recent flips}
- **Momentum of MAs:** {MA slopes trending up or down}
- **Trend Strength:** {ADX interpretation: >25 strong, <20 weak}
- **Donchian Position:** {Near upper = breakout / Near lower = breakdown}

### Strategy Alignment
{Reference the entry/exit rules from the latest strategy file in `data/strategy/{ticker}/`. Are current trend conditions consistent with the recommended strategy's entry criteria?}

---

## 2. Momentum Analysis

### Current Indicators
| Indicator | Value | Signal |
|-----------|-------|--------|
| RSI(14) | {value} | {Oversold/<30 / Normal / Overbought/>70} |
| MACD Line | {value} | |
| MACD Signal | {value} | |
| MACD Histogram | {value} | {Rising / Falling} |
| ROC(20) | {value} | |
| Williams %R | {value} | {Oversold/<-80 / Normal / Overbought/>-20} |
| CCI | {value} | {Oversold/<-100 / Normal / Overbought/>100} |
| MFI(14) | {value} | {Oversold/<20 / Normal / Overbought/>80} |

### Momentum Assessment
- **RSI Context:** {Current RSI, z-score, and percentile interpretation}
- **MACD State:** {Cross status, histogram direction, divergence check}
- **Momentum Strength:** {Combined reading of RSI, MACD, ROC, Williams %R}
- **Divergence Check:** {Price vs RSI/MACD divergence if any}

### Strategy Alignment
{Reference strategy's momentum thresholds from the strategy report.}

---

## 3. Return Analysis

### Performance Metrics
| Period | Return | Assessment |
|--------|--------|------------|
| 1 Month | {ta_ret_1m}% | |
| 3 Months | {ta_ret_3m}% | |
| 6 Months | {ta_ret_6m}% | |
| 1 Year | {ta_ret_1y}% | |

### Risk-Adjusted Metrics
| Metric | Value | Interpretation |
|--------|-------|----------------|
| Alpha(20) | {ta_alpha20} | {Positive = outperforming} |
| Beta(20) | {ta_beta20} | {>1 = more volatile} |
| RS vs FTSE100 | {ta_rs_ftse100} | {Rising = outperforming} |

### Return Assessment
- **Short-term momentum:** {1m/3m trend direction}
- **Medium-term trend:** {6m/1y trend direction}
- **Benchmark comparison:** {Alpha/Beta/RS interpretation}

### Strategy Alignment
{Does the strategy report indicate this ticker is more mean-reverting or momentum-driven?}

---

## 4. Structure Analysis

### Key Levels
| Level | Value | Note |
|-------|-------|------|
| Nearest Support | {ta_nearest_support} | Distance: {pct}% |
| Nearest Resistance | {ta_nearest_resistance} | Distance: {pct}% |
| Swing High (recent) | {ta_swing_high} | |
| Swing Low (recent) | {ta_swing_low} | |

### Structure Signals
| Signal | Value | Interpretation |
|--------|-------|----------------|
| HH (Higher High) | {bool} | Bullish structure |
| HL (Higher Low) | {bool} | Bullish structure |
| LH (Lower High) | {bool} | Bearish structure |
| LL (Lower Low) | {bool} | Bearish structure |
| BOS (Break of Structure) | {bool} | Trend continuation |
| CHoCH (Change of Character) | {bool} | Potential reversal |
| Trend Label | {ta_trend} | |

### Structure Assessment
- **Pattern:** {Uptrend (HH/HL), Downtrend (LH/LL), or Range-bound}
- **Key levels:** {Price position relative to support/resistance}
- **Recent breaks:** {Any BOS or CHoCH signals in recent data}

### Strategy Alignment
{Does the recommended strategy rely on structural signals? Are they currently aligned?}

---

## 5. Volatility Analysis

### Current Indicators
| Indicator | Value | Assessment |
|-----------|-------|------------|
| ATR(14) | {value} | |
| ATR Percentile | {value}% | {Low/Normal/High} |
| BB Width | {value} | {Contraction / Expansion} |
| %B | {value} | {Position in BB: 0=lower, 1=upper} |
| HV(20) | {value} | {Rising / Falling} |
| Park Volatility | {value} | |
| GARCH Vol | {value} | {Forecast direction} |
| ATR Stop Distance | {value} | Suggested stop level |

### Volatility Assessment
- **Volatility Level:** {Current ATR percentile interpretation}
- **Band Position:** {Price position within Bollinger Bands}
- **Volatility Trend:** {HV and GARCH direction}
- **Breakout Potential:** {BB width contraction/expansion}
- **Suggested Stop:** {ATR-based stop distance}

### Strategy Alignment
{Does the strategy use volatility-based entries/exits? Is current volatility favorable?}

---

## 6. Volume Analysis

### Current Indicators
| Indicator | Value | Assessment |
|-----------|-------|------------|
| OBV | {value} | {Rising / Falling} |
| CMF(20) | {value} | {Buying / Selling pressure} |
| OFI | {value} | {Order flow imbalance} |
| VWAP | {value} | Price vs VWAP: {above/below} |
| ADL | {value} | {Accumulation / Distribution} |
| MFI(14) | {value} | {Overbought / Normal / Oversold} |
| Volume Z-Score | {value} | {Above / Below average} |
| EMV(14) | {value} | {Ease of movement} |

### Volume Assessment
- **Buying/Selling Pressure:** {CMF + OFI combined reading}
- **Volume Trend:** {OBV direction vs price direction — confirmation or divergence?}
- **Volume Intensity:** {Z-Score and percentile}
- **Smart Money:** {ADL direction — accumulation or distribution}

### Strategy Alignment
{Does the recommended strategy use volume confirmation? Is volume currently supporting the price action?}

---

## 7. Regime Analysis

### HMM Regime Probabilities
| Regime | Probability | Interpretation |
|--------|-------------|----------------|
| State 0 | {ta_hmm_regime_prob_0} | {Bull / Bear / Neutral} |
| State 1 | {ta_hmm_regime_prob_1} | {Bull / Bear / Neutral} |
| State 2 | {ta_hmm_regime_prob_2} | {Bull / Bear / Neutral} |

### Regime Assessment
- **Dominant Regime:** {Highest probability state}
- **Regime Stability:** {Has the regime changed in the last ~30 days?}
- **GARCH Context:** {Volatility trend within current regime}

### Strategy Alignment
{What regime does the recommended strategy perform best in? Is the current regime aligned?}

---

## Signal Synthesis

### Score Summary
| Dimension | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Trend | {1-5} | 20% | |
| Momentum | {1-5} | 15% | |
| Return | {15%} | 15% | |
| Structure | {1-5} | 15% | |
| Volatility | {1-5} | 10% | |
| Volume | {1-5} | 15% | |
| Regime | {1-5} | 10% | |
| **TOTAL** | | **100%** | **{weighted sum}** |

### Signal Determination
- **Overall Signal:** BUY / SELL / HOLD / WAIT
- **Strength:** Strong / Normal / Weak
- **Confidence:** High / Medium / Low

### Supporting Indicators (Top 3 per dimension)
| Dimension | Indicator 1 | Indicator 2 | Indicator 3 |
|-----------|------------|------------|------------|
| Trend | | | |
| Momentum | | | |
| Return | | | |
| Structure | | | |
| Volatility | | | |
| Volume | | | |
| Regime | | | |

### Conflicting Indicators
{List any indicators that contradict the overall signal, with explanation}

### Recommended Action
- **Entry:** {Specific conditions to trigger entry}
- **Stop-Loss:** {Level, e.g., "Below nearest support or X% using ATR stop"}
- **Target:** {Level, e.g., "Nearest resistance or X% using BB upper}
- **Position Sizing:** {If mentioned in strategy report, reference it}
- **Max Holding Period:** {If applicable}

### Risk Factors
- {Risk 1: e.g., "Regime shift to bear if HMM prob_1 rises above prob_0"}
- {Risk 2: e.g., "Volume declining — potential false breakout"}
- {Risk 3: e.g., "RSI overbought — mean reversion risk"}

### When This Signal Is Invalidated
- {Condition 1: e.g., "Close below EMA200"}
- {Condition 2: e.g., "RSI drops below 30"}
- {Condition 3: e.g., "SuperTrend flips to -1"}

---

## Next Steps
- {Action items, e.g., "Monitor for breakout above resistance at X"}
- {Re-evaluation trigger, e.g., "Re-run this evaluation if {condition}"}}
- {Strategy-specific note, e.g., "If entering, use {strategy_name} entry rules from strategy report"}
```

## Chunked Write Instructions

Due to token limits, write the report file in multiple chunks:

1. **Chunk 1:** Write header + Executive Summary table
2. **Chunk 2:** Add Trend Analysis section (Step 2 results)
3. **Chunk 3:** Add Momentum + Return sections (Step 3 + Step 4)
4. **Chunk 4:** Add Structure + Volatility sections (Step 5 + Step 6)
5. **Chunk 5:** Add Volume + Regime sections (Step 7 + Step 8)
6. **Chunk 6:** Add Signal Synthesis and Recommended Action (Step 9)
7. **Chunk 7:** Add Next Steps (closing)

Use `edit` to insert sections into the existing file content. Each chunk should be ~500-800 words maximum.

## Execution Steps

1. **Verify prerequisites** — check the most recent `.md` file in `data/strategy/{ticker}/` exists; exit with advice if not
2. **Load data** — read `data/analysis-data/{ticker}.csv`, identify latest date
3. **Load strategy report** — read the latest strategy file from `data/strategy/{ticker}/` for cross-referencing
4. **Evaluate each dimension** (Steps 1-8) — compute scores, note key indicators
5. **Synthesize signal** (Step 9) — aggregate scores, determine BUY/SELL/HOLD
6. **Write report in chunks** (Step 10) — use the template, write in 7 chunks
7. **Verify report** — confirm the file was written completely
