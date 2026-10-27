# Market Situation Evaluation: Marks & Spencer (MKS.L)

**Evaluation Date:** 2026-10-27
**Actual Date Used:** 2026-10-27
**Ticker:** MKS.L (Marks & Spencer)
**Price:** 413.2p
**Data Range:** 2006-10-27 to 2026-10-27 (5,053 rows)
**Sector:** Retail
**Strategy Reference:** `data/reports/strategies/MKS.L/2026-10-26.md`

---

## Executive Summary

**Signal:** WAIT
**Confidence:** Medium

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🟢 BULLISH | 🟡 Medium | EMA alignment bullish, but SuperTrend flips daily (range-bound) |
| **Momentum** | 🟡 CAUTIOUS | 🟡 Medium | RSI 59.9 moderate, MACD positive, but MFI 177 extreme |
| **Return** | 🟢 POSITIVE | 🟢 High | +9.4% in 1M, +27.1% in 6M, positive forward returns |
| **Structure** | 🟡 CAUTIOUS | 🟡 Medium | Price near resistance (1.2%), no HH/HL confirmation |
| **Volatility** | 🔴 HIGH RISK | 🟢 High | Near 52-week high, low ATR percentile, BB squeeze potential |
| **Volume** | 🟡 MIXED | 🟡 Medium | OBV rising (+6.7%), but CMF and OFI negative — mixed signals |
| **Regime** | 🟢 BULL | 🟢 High | HMM State 0 at 98.6%, stable for 30 days |
| **Overall** | 🟠 WAIT | 🟡 Medium | +0.945 aggregate — all strategy entry conditions NOT MET |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | 413.2p | Near 52-week high of 429.4p (96.2%) |
| 52-Week Range | 301.1 – 429.4p | At 96.2% of high |
| P/E (TTM) | N/A | No fundamentals data available |
| Dividend Yield | N/A | No fundamentals data available |
| Beta (20d) | 0.35 | Low volatility vs FTSE 100 |
| RS vs FTSE 100 | +3.87 | Outperforming FTSE 100 |

### Strategy Alignment Summary

| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| Close ≤ BB Lower (372.3) | 413.2 — 11.0% above | ❌ NOT MET |
| RSI(14) < 35 | 59.9 — moderate | ❌ NOT MET |
| CCI(20) < −100 | 60.2 — positive | ❌ NOT MET |
| GARCH vol ≤ previous | 1.68 — declining from prior | ✅ CONFIRMED |
| Price near resistance | 1.2% below nearest resistance | ⚠️ CAUTION |

**Strategy Verdict:** None of the three required entry conditions for the recommended `vol_filtered_meanrev` strategy are met. Price is near the top of its range, not at oversold levels. The strategy would not trigger any entry signal at this price.

### Signal Summary

**Current Signal: WAIT**

Marks & Spencer has rallied strongly over the past month (+9.4%) and is trading near its 52-week high. The bull regime is solid (98.6% HMM confidence), but the recommended mean-reversion strategy requires the stock to be near or below its Bollinger Band Lower — which is 372.3p, approximately 11% below the current price. Neither holders nor new investors should act now. Holders may consider trimming. Non-holders should wait for a pullback to the BB lower zone (370–380p) with oversold RSI (<35) and CCI (<−100) before considering entry.

---

## 1. Trend Analysis

**Signal:** BULLISH | **Confidence:** MEDIUM

Marks & Spencer exhibits a classic range-bound uptrend: moving averages are bullish and aligned, but the SuperTrend indicator flips direction nearly every day, confirming the stock's oscillating character. The underlying trend is positive, but trend-following indicators are unreliable for this asset.

### Current Indicators

| Indicator | Value | Signal |
|-----------|-------|--------|
| EMA20 | 406.0 | Price 1.78% above |
| EMA50 | 394.6 | Price 4.72% above |
| EMA200 | 375.8 | Price 9.94% above |
| SuperTrend Direction | -1 | Bearish (daily flip) |
| SuperTrend Trail | 101.6 | 75.4% below price (extremely wide — unreliable) |
| MA20 Slope | +2.29 | Positive — accelerating |
| MA50 Slope | +0.36 | Positive — gentle |
| ADX(14) | 31.3 | Strong trend strength (>25) |
| DI+ / DI- | 24.2 / 12.4 | Bullish dominance (2:1 ratio) |
| Price vs EMA20 | +1.78% | Above |
| Donchian Upper | 429.4 | Price 3.8% below — near breakout |
| Donchian Lower | 375.3 | Price 10.1% above — well off bottom |
| Keltner Upper | 423.7 | Price 2.5% below — approaching upper band |
| Keltner Lower | 388.1 | Price 6.5% above |
| Aroon Up / Down | 80 / 8 | Strong bullish (up trending down) |

### Trend Assessment
- **MA Alignment:** ✅ Bullish — EMA20 (406.0) > EMA50 (394.6) > EMA200 (375.8). Classic uptrend alignment.
- **SuperTrend:** ⚠️ Unreliable — flips +1/-1 every single trading day over the last 30 days. The 75% distance from the trail (101.6 vs 413.2) confirms it is far too loose to be meaningful. This is expected for a range-bound retail stock.
- **MA Slopes:** Both positive. MA20 slope (+2.29) > MA50 slope (+0.36), indicating short-term acceleration.
- **Trend Strength:** ADX at 31.3 indicates strong trend *strength*, but in a range-bound asset this means strong oscillation rather than sustained direction. DI+/DI- ratio of ~2:1 favors bulls.
- **Donchian Position:** Price at 413.2, 3.8% below the 200-day upper bound (429.4) and 10.1% above the lower (375.3). Approaching breakout zone.
- **Keltner Position:** Price between the bands, closer to the upper (423.7) than the lower (388.1).
- **Aroon:** Up at 80 (strong), Down at 8 (weak) — confirms the underlying uptrend despite daily SuperTrend noise.

### Trend Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| MA Alignment (EMA20>EMA50>EMA200) | +1.0 | 30% | +0.30 |
| MA Slopes (both positive, accelerating) | +0.5 | 20% | +0.10 |
| SuperTrend (daily flips — unreliable) | -0.5 | 15% | -0.075 |
| ADX/DI (strong trend, bull bias) | +1.0 | 20% | +0.20 |
| Donchian/Keltner Position (near top) | -0.5 | 15% | -0.075 |
| **Trend Score** | | **100%** | **+0.45** (range: -3.0 to +3.0) |

**Trend Verdict:** Underlying trend is bullish (MA alignment, DI+ dominance, Aroon strength), but SuperTrend daily flips and Donchian proximity to upper bound signal a range-bound market where trend-following signals are unreliable.

### Strategy Alignment
The `vol_filtered_meanrev` strategy does not require specific trend alignment (it is a mean-reversion strategy, not trend-following). However, the SuperTrend direction flip (currently -1) does NOT match the trend-riding custom strategy (`mks_trend_rider`) which requires SuperTrend = +1. The trend context supports mean-reversion entries at the lower band but does not support trend-riding entries at current levels.

---

## 2. Momentum Analysis

**Signal:** CAUTIOUS | **Confidence:** MEDIUM

Momentum indicators are mixed — RSI and MACD show moderate bullishness, but the extreme MFI reading of 177 is a serious warning sign of overbought conditions. The Williams %R and CCI are in neutral territory, offering no extreme signals to support mean-reversion entries.

### Current Indicators

| Indicator | Value | Signal |
|-----------|-------|--------|
| RSI(14) | 59.9 | Moderate — approaching overbought (>70) |
| RSI Z-Score(14,20) | -0.35 | Below average |
| RSI Percentile(14,20) | 30% | Below median — not extreme |
| MACD Line | 9.77 | Bullish (above signal) |
| MACD Signal | 8.95 | Cross status: bullish |
| MACD Histogram | 0.82 | Rising — momentum strengthening |
| ROC(20) | 8.28% | Positive momentum |
| Williams %R | -39.1 | Neutral (range: -20 to -80) |
| CCI(20) | 60.2 | Neutral (range: -100 to +100) |
| MFI(14) | 177.4 | ⚠️ EXTREME — far above 80 |

### Momentum Assessment
- **RSI Context:** RSI at 59.9 is in the moderate range, approaching overbought (>70). The z-score of -0.35 and 30th percentile suggest this RSI reading is below the recent 20-day average — slightly bullish in relative terms, but not extreme.
- **MACD State:** MACD line (9.77) above signal (8.95) with a positive histogram (0.82) that is rising — this confirms the underlying bullish momentum. The histogram is expanding, suggesting acceleration.
- **Oscillator Convergence:** Mixed. RSI (moderate bullish) and MACD (bullish) agree on bullish momentum, but MFI (177.4) is at extreme overbought levels, suggesting excessive buying pressure. Williams %R (-39.1) and CCI (60.2) are neutral — no extreme readings.
- **Divergence Check:** No price-MACD divergence visible — price has risen from 355 to 422 while MACD is positive and rising, confirming the uptrend.

### Momentum Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| RSI (moderate, not extreme) | +0.5 | 25% | +0.125 |
| MACD (positive cross, histogram rising) | +0.5 | 25% | +0.125 |
| MFI (extreme overbought — warning) | -1.0 | 25% | -0.250 |
| Williams %R + CCI (neutral, no extreme) | 0.0 | 25% | 0.000 |
| **Momentum Score** | | **100%** | **+0.000** (range: -3.0 to +3.0) |

**Momentum Verdict:** Mixed — bullish MACD and moderate RSI are offset by the extreme MFI reading of 177.4, which is a serious warning of overbought conditions. The oscillator consensus is neutral: neither strongly bullish nor bearish.

### Strategy Alignment
The `vol_filtered_meanrev` strategy requires RSI(14) < 35 for entry — current RSI of 59.9 is far above this threshold (❌ NOT MET). Williams %R at -39.1 does not match the oversold requirement for mean-reversion entries (❌ NOT MET). CCI at 60.2 does not match the CCI < −100 entry condition (❌ NOT MET). Momentum is currently supportive of holding positions but NOT of initiating mean-reversion entries.

---

## 3. Return Analysis

**Signal:** POSITIVE | **Confidence:** HIGH

Marks & Spencer has delivered strong returns over the past 6 months (+27.1%), with a particularly strong 1-month performance (+9.4%). The stock is outperforming the FTSE 100 with positive alpha and low beta. Forward returns over the past 30 observation windows have been consistently positive, suggesting the uptrend may continue.

### Past Performance

| Period | Return | Assessment |
|--------|--------|------------|
| 1 Month | +9.43% | Strong — rapid recovery phase |
| 3 Months | −1.92% | Negative — includes the September dip from 381→355 |
| 6 Months | +27.14% | Very strong — major recovery from 2025 lows |
| 1 Year | +2.53% | Modest — flat overall when including 2025 drawdown |

### Risk-Adjusted Metrics

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Alpha(20) | +0.40 | Positive — outperforming FTSE 100 benchmark |
| Beta(20) | 0.35 | Low — only 35% as volatile as FTSE 100 |
| RS vs FTSE 100 | +3.87 | Outperforming — rising relative strength |

### Forward Return Context

| Forward Period | Mean Return | Std Dev | Assessment |
|---------------|-------------|---------|------------|
| 5 days | +2.72% | 2.19% | Positive — continuation likely |
| 10 days | +6.04% | 2.54% | Strongly positive |
| 20 days | +12.41% | 2.19% | Very strong — trend persistence |

*Based on rolling forward returns from the last 30 trading days (25/20/10 observations respectively due to NaN values at the start).*

### Return Assessment
- **Short-term trend:** +9.4% in 1 month shows strong recent momentum, but 3-month return of −1.9% reflects the September capitulation (355→381 dip) that has since been fully recovered and exceeded.
- **Medium-term trend:** +27.1% over 6 months is the dominant story — the stock has recovered strongly from the 2025 sector-wide drawdown. +2.5% over 1 year is modest, reflecting the 2025 losses.
- **Risk-adjusted:** Alpha is positive (+0.40) and beta is low (0.35), meaning MKS.L is outperforming its benchmark while being less volatile — an attractive combination for defensive investors. Relative strength vs FTSE 100 is rising (+3.87).
- **Forward expectations:** All forward return windows (5d, 10d, 20d) show positive mean returns with relatively low std dev. This suggests the uptrend has persistence and continuation is likely, but also that mean-reversion entries are not indicated — the stock is in a momentum phase, not an oversold phase.

### Return Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| 6-month return (+27.1%) | +1.0 | 25% | +0.25 |
| 1-month return (+9.4%) | +0.5 | 25% | +0.125 |
| Alpha/Beta (positive alpha, low beta) | +0.5 | 25% | +0.125 |
| Forward returns (positive mean across all windows) | +0.5 | 25% | +0.125 |
| **Return Score** | | **100%** | **+0.625** (range: -3.0 to +3.0) |

**Return Verdict:** Strong positive returns across multiple time horizons, with favorable risk-adjusted metrics (positive alpha, low beta). However, the 3-month negative return and the fact that forward returns are positive (suggesting the rally may be exhausted) warrant caution.

### Strategy Alignment
The `vol_filtered_meanrev` strategy is designed for mean-reversion entries — buying oversold dips. Current returns show the stock is in a momentum/upward phase, not an oversold dip. The strategy's entry conditions would NOT be triggered. For the trend-riding strategy (`mks_trend_rider`), the positive returns and rising RS would be favorable, but that strategy requires specific MA alignment + SuperTrend +1 conditions that are not simultaneously met. The return context supports holding existing positions but not initiating new entries under the recommended strategy.

---

## 4. Structure Analysis

**Signal:** CAUTIOUS | **Confidence:** MEDIUM

Marks & Spencer is trading near its 200-day resistance level with a clear support zone ~10% below. The structural signals show one higher low (bullish) and two breakouts of structure in the last 30 days, but no higher highs — the stock has not yet confirmed a new structural high. One CHoCH signal was detected, indicating a potential reversal point that has since been overcome.

### Key Levels

| Level | Value | Distance from Current | Significance |
|-------|-------|----------------------|--------------|
| **Resistance** | 429.4 (Donchian Upper / Swing High) | +3.8% | 200-day high, 52-week high |
| Nearest Resistance | 418.3 | +1.2% | Immediate overhead supply |
| **Support** | 375.3 (Donchian Lower / Swing Low) | −10.1% | 200-day low |
| Nearest Support | 370.6 | −10.3% | Deeper support level |
| BB Lower (Strategy Entry Zone) | 372.3 | −10.1% | vol_filtered_meanrev entry trigger |
| EMA20 | 406.0 | −1.7% | Dynamic support |
| EMA50 | 394.6 | −4.5% | Medium-term support |

### Structure Signals

| Signal | Value | Interpretation |
|--------|-------|----------------|
| HH (Higher High) | 0 | No — price has not made a new high in 30 days |
| HL (Higher Low) | 1 | Yes — one higher low detected |
| LH (Lower High) | 0 | No — no lower highs in recent window |
| LL (Lower Low) | 0 | No — no lower lows in recent window |
| BOS (Break of Structure) | 2 | Two breakouts — trend continuation signals |
| CHoCH (Change of Character) | 1 | One reversal signal — later overcome |
| Trend Label | +1 | Bullish classification |

### Structure Assessment
- **Pattern:** Range-bound uptrend. The stock oscillated from a low of 355 (Sept 18) to a high of 422 (Oct 22), currently pulling back from that high to 413.2. The absence of HH signals but presence of one HL and two BOS confirms a range-bound environment with bullish bias.
- **Key levels:** Price is only 1.2% below the nearest resistance at 418.3 and 3.8% below the Donchian upper at 429.4. The gap to nearest support is 10.3% — a large air gap suggests any break above resistance could trigger a quick move to 429.4, while a break below EMA20 (406.0) could see a rapid 4.5% decline to EMA50 (394.6).
- **Recent breaks:** Two BOS signals in the last 30 days confirm trend continuation events. One CHoCH signal was detected (likely the Sept 18 dip to 355 was seen as a potential reversal but was overcome).
- **Support touches:** The swing low at 375.3 and nearest support at 370.6 have not been tested recently, suggesting support is intact but untested at current levels.

### Structure Score

| Factor | Score | Weight | Weight | Weighted |
|--------|-------|--------|--------|----------|
| Near resistance (3.8% below Donchian upper) | −0.5 | 30% |  | −0.15 |
| Support intact (no LL, HL present) | +0.5 | 25% |  | +0.125 |
| BOS count (2 bullish breaks) | +0.5 | 25% |  | +0.125 |
| CHoCH presence (1 reversal signal) | −0.5 | 20% |  | −0.10 |
| **Structure Score** | | **100%** |  | **+0.000** (range: -3.0 to +3.0) |

**Structure Verdict:** Neutral-cautious — price is near resistance with a large gap to support. The structural signals are mixed: bullish BOS count and HL presence are offset by proximity to resistance and a recent CHoCH signal. The nearest resistance at 418.3 is only 1.2% away, making breakouts possible but pullbacks equally likely.

### Strategy Alignment
The `vol_filtered_meanrev` strategy requires Close ≤ BB Lower (372.3) for entry. Current price at 413.2 is 10.1% above this level — ❌ NOT MET. The structure does not support mean-reversion entries at current levels. The BOS signals (2 in 30 days) indicate trend continuation opportunities, but the nearest resistance at 418.3 is approaching, making breakout entries risky. The CHoCH signal (1) suggests a potential reversal point exists, but it was already overcome.

---

## 5. Volatility Analysis

**Signal:** HIGH RISK | **Confidence:** HIGH

Volatility conditions are a concern. The ATR percentile is at the 0th percentile — extremely low by historical standards — which often precedes a breakout (either up or down). With the stock near its 52-week high and the Bollinger Bands at moderate width, a volatility expansion event is likely. The GARCH forecast of declining volatility provides some comfort, but the extreme ATR percentile is a warning sign.

### Current Indicators

| Indicator | Value | Assessment |
|-----------|-------|------------|
| ATR(14) | 9.30 | ~2.25% of price — moderate absolute level |
| ATR Percentile | 0.0% | ⚠️ EXTREMELY LOW — 0th percentile historically |
| BB Width | 15.4% | Moderate — not at extreme contraction |
| %B | 0.66 | Price in upper third of bands |
| BB Upper | 434.4 | Resistance level |
| BB Lower | 372.3 | Support / strategy entry zone |
| HV(20) | 20.1% | Moderate — stable |
| Park Volatility | 23.5% | Range-based estimate, moderate |
| GARCH Vol | 1.68 | Forecast — declining from prior |
| ATR Stop Distance | 6.76 | ~1.6% of price — tight stop needed |

### Volatility Assessment
- **Volatility Level:** ATR percentile at 0% is the most notable feature — this means current volatility is at or near the lowest level in the entire ~20-year dataset. Extremely low volatility often precedes significant price moves (breakouts or breakdowns).
- **Band Position:** Price at %B = 0.66, in the upper third of the Bollinger Bands (372.3–434.4). This is bullish but not at an extreme. The BB width of 15.4% is moderate — not at extreme contraction, but ATR is at its lowest.
- **Volatility Trend:** HV(20) at 20.1% is moderate. GARCH vol at 1.68 suggests declining volatility going forward, which supports the low-ATR reading. This is a "calm before the storm" scenario.
- **Breakout Potential:** High — the combination of extremely low ATR percentile, price near resistance, and moderate BB width suggests a breakout event is probable. The direction is uncertain: could be up (continuation) or down (mean-reversion to BB lower at 372.3).
- **Suggested Stop:** ATR-based stop distance is 6.76p (~1.6%). A stop at 406.0 (EMA20, −1.7%) would be tighter than ATR-based. A more conservative stop at 394.6 (EMA50, −4.5%) allows for normal volatility noise.

### Volatility Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| ATR Percentile (extremely low — breakout imminent) | −0.5 | 30% | −0.15 |
| BB Position (%B = 0.66, upper third) | +0.0 | 20% | 0.00 |
| GARCH Vol (declining — calm before storm) | −0.5 | 20% | −0.10 |
| Stop Distance (tight at 1.6%) | −0.5 | 15% | −0.075 |
| HV/Park (moderate, stable) | +0.5 | 15% | +0.075 |
| **Volatility Score** | | **100%** | **−0.250** (range: -3.0 to +3.0) |

**Volatility Verdict:** High risk due to extremely low ATR percentile — a breakout event is likely, but direction is uncertain. The low volatility environment makes mean-reversion entries risky (breakdown could be sharp) and trend-following entries risky (false breakout possible). Caution is warranted.

### Strategy Alignment
The `vol_filtered_meanrev` strategy includes a GARCH volatility filter: GARCH vol ≤ previous day's value. Current GARCH vol at 1.68 meets this condition ✅ (vol is declining). However, the extremely low ATR percentile means that if the stock does pull back to BB Lower, the move could be sharp and sustained — the low volatility environment is more conducive to breakout than to gentle mean-reversion bounces. The volatility context partially supports the strategy but introduces risk of a false entry if a breakout occurs in the wrong direction.

---

## 6. Volume Analysis

**Signal:** MIXED | **Confidence:** MEDIUM

Volume indicators send mixed signals for Marks & Spencer. OBV is rising (+6.7% over 30 days), confirming the price uptrend — this is a positive sign. However, CMF is slightly negative (−0.007) and OFI is also negative (−0.48), indicating that recent daily flows show slight selling pressure. ADL is negative (−547M), suggesting institutional distribution. Volume intensity is below average (z-score: −0.65, percentile: 25%).

### Current Indicators

| Indicator | Value | Assessment |
|-----------|-------|------------|
| OBV | 898.1M | Rising — confirmed with price (+6.7% in 30d) |
| OBV Slope (14d) | +3.13M | Positive slope — accumulation |
| OBV Slope (7d) | +2.14M | Positive slope — still accumulating |
| CMF(20) | −0.007 | Slight selling pressure |
| OFI | −0.48 | Selling order flow imbalance |
| VWAP | 401.9 | Price 2.9% above — bullish intraday |
| ADL | −546.5M | Distribution — institutional selling |
| MFI(14) | 177.4 | ⚠️ Extreme overbought |
| Volume Z-Score | −0.65 | Below average volume |
| Volume Percentile | 25% | Low intensity |
| EMV(14) | 2.69e-06 | Near zero — little ease of movement |

### Volume Assessment
- **Buying/Selling Pressure:** Mixed. CMF at −0.007 shows slight selling pressure on balance, and OFI at −0.48 confirms order flow is slightly tilted toward sellers. This is notable because price has been rising — the selling pressure suggests some profit-taking.
- **Volume Trend:** OBV is rising (+6.7% over 30 days) with positive slopes in both 14-day and 7-day windows. This confirms the price uptrend — volume supports the rally. This is the most positive volume signal.
- **Volume Intensity:** Volume z-score of −0.65 and percentile of 25% indicate below-average volume. The rally is not being driven by high volume participation, which can be a warning sign — rallies on low volume are more prone to reversal.
- **Smart Money:** ADL at −546.5M suggests institutional distribution — large players may be taking profits. This conflicts with the rising OBV, which suggests net accumulation.
- **Divergence Warning:** Price is rising but CMF and OFI are both negative — a mild bearish divergence. This is not a strong divergence (CMF is only slightly negative), but it is a cautionary signal, especially combined with the extreme MFI reading.

### Volume Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| OBV trend (rising, confirms price) | +0.5 | 30% | +0.15 |
| CMF + OFI (both negative — selling pressure) | −0.5 | 25% | −0.125 |
| Volume intensity (below average) | −0.5 | 25% | −0.125 |
| ADL (institutional distribution) | −0.5 | 20% | −0.10 |
| **Volume Score** | | **100%** | **−0.200** (range: -3.0 to +3.0) |

**Volume Verdict:** Mixed — OBV confirms the uptrend, but CMF, OFI, and ADL all point to selling pressure and distribution. Below-average volume intensity suggests the rally lacks broad participation. The mild bearish divergence between price and volume flows is a cautionary signal.

### Strategy Alignment
The `vol_filtered_meanrev` strategy does not include a specific volume filter in its recommended entry rules (the custom `mks_meanrev_v2` adds CMF > −0.05, which is NOT met at −0.007 — ❌ NOT MET). The current volume conditions (slight selling pressure, below-average volume) do not support new entries at this level. For the OFI momentum strategy (ranked #5 in backtests), the negative OFI (−0.48) does not meet the entry requirement of OFI > 0.3 — ❌ NOT MET. Volume is not supportive of any strategy entry at current levels.

---

## 7. Regime Analysis

**Signal:** BULL | **Confidence:** HIGH

The HMM regime model shows overwhelming confidence in a bullish regime. State 0 (bull) probability is 98.6% and has been stable at this level for the entire 30-day window. There have been zero regime changes — the market is in a stable bull phase. This is the strongest single signal in the evaluation.

### HMM Regime Probabilities

| Regime State | Probability | Interpretation |
|-------------|-------------|----------------|
| State 0 | 98.61% | 🟢 Bull — dominant regime |
| State 1 | 0.55% | Bear — negligible |
| State 2 | 0.85% | Neutral/Sideways — negligible |

### Regime Assessment
- **Dominant Regime:** State 0 (bull) at 98.6% — near-total certainty. The market is firmly in a bull regime.
- **Regime Stability:** The HMM has been in State 0 for all 30 days in the recent context window, with the probability ranging from 96.1% to 99.8%. Zero regime changes — extremely stable.
- **GARCH Context:** GARCH vol at 1.68 with declining trend — volatility is moderate and decreasing within the bull regime. This is a healthy bull market characteristic (low, declining volatility).
- **Trend vs Regime Alignment:** No divergence — both trend indicators (bullish MA alignment, ADX 31.3) and regime model (State 0 at 98.6%) agree on a bull environment. The only tension is the SuperTrend daily flips, which are unreliable in this range-bound asset.

### Regime Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| HMM State 0 probability (98.6%) | +1.0 | 60% | +0.60 |
| Regime stability (zero flips in 30 days) | +1.0 | 30% | +0.30 |
| GARCH vol context (declining, moderate) | +0.0 | 10% | 0.00 |
| **Regime Score** | | **100%** | **+0.900** (range: -3.0 to +3.0) |

**Regime Verdict:** Strong bull regime with near-certainty (98.6%) and complete stability over 30 days. This is the most reliable signal in the entire evaluation and strongly supports the underlying bullish context.

### Strategy Alignment
The `vol_filtered_meanrev` strategy performs best in a bull regime with declining volatility — both conditions are met ✅. In fact, the strategy's 2026 performance (+13.05%) was its best year, and it was the only mean-reversion strategy to outperform others in the recovery year. The bull regime supports mean-reversion entries because pullbacks to BB Lower are likely to bounce rather than continue lower. The regime is perfectly aligned with the strategy's preferred operating conditions.

---

## Signal Synthesis

### Aggregate Score Summary

| # | Dimension | Signal | Score (-3.0 to +3.0) | Weight | Weighted |
|---|-----------|--------|-------------|--------|----------|
| 1 | **Trend** | 🟢 BULLISH | +0.450 | 15% | +0.068 |
| 2 | **Momentum** | 🟡 CAUTIOUS | +0.000 | 15% | 0.000 |
| 3 | **Return** | 🟢 POSITIVE | +0.625 | 15% | +0.094 |
| 4 | **Structure** | 🟡 CAUTIOUS | +0.000 | 10% | 0.000 |
| 5 | **Volatility** | 🔴 HIGH RISK | −0.250 | 10% | −0.025 |
| 6 | **Volume** | 🟡 MIXED | −0.200 | 10% | −0.020 |
| 7 | **Regime** | 🟢 BULL | +0.900 | 25% | +0.225 |
| | **AGGREGATE** | | | **100%** | **+0.343** |

### Score Interpretation

| Range | Signal | Interpretation |
|-------|--------|---------------|
| +2.0 to +3.0 | Strong Bullish | All dimensions aligned — strong buy signal |
| +0.5 to +1.9 | Mildly Bullish | Trend favors longs but monitor for reversals |
| **+0.1 to +0.4** | **Neutral / Wait** | **Mixed signals — do not initiate new positions** |
| -0.4 to +0.0 | Neutral / Wait | Mixed signals — do not initiate new positions |
| -1.9 to -0.5 | Mildly Bearish | Caution warranted, consider reducing exposure |
| -3.0 to -2.0 | Strong Bearish | All dimensions negative — avoid longs |

**Aggregate Score: +0.343 — WAIT**

The aggregate score of +0.343 falls in the neutral/wait range. While the underlying trend and regime are strongly bullish (+0.450 and +0.900 respectively), the current price position (near resistance, far from BB Lower entry zone) and mixed momentum/volume signals prevent a BUY recommendation. The recommended `vol_filtered_meanrev` strategy would not trigger any entry at this price. The signal is not negative enough for SELL, but it is not positive enough for BUY — WAIT for a pullback.

### Signal Determination
- **Overall Signal:** WAIT
- **Strength:** Weak (|score| = 0.343, ≤ 0.5)
- **Confidence:** Medium — 3 dimensions rated High confidence (Regime, Return, Volatility), 3 rated Medium (Trend, Momentum, Volume, Structure)

### Supporting Indicators (Top 3 per Dimension)

| Dimension | Indicator 1 | Indicator 2 | Indicator 3 |
|-----------|------------|------------|------------|
| Trend | EMA alignment (bullish) | DI+/DI- ratio (2:1 bull) | ADX (31.3 strong) |
| Momentum | MACD (positive cross) | RSI (moderate, 59.9) | MFI (177.4 ⚠️ extreme) |
| Return | 6M return (+27.1%) | Alpha (positive, +0.40) | Beta (low, 0.35) |
| Structure | BOS count (2 bullish) | HL presence (1) | Proximity to resistance (1.2%) |
| Volatility | ATR percentile (0% ⚠️) | GARCH vol (declining) | BB %B position (0.66) |
| Volume | OBV trend (rising +6.7%) | CMF (−0.007 ⚠️) | Volume percentile (25%) |
| Regime | HMM State 0 (98.6%) | Regime stability (30 days) | GARCH vol context (declining) |

### Conflicting Indicators
- **Regime vs. Price Position:** HMM regime is strongly bullish (98.6%), but price is at the top of its range (96.2% of 52-week high) with all strategy entry conditions unmet. This is a regime-price divergence — the regime supports the stock being higher, but the current price suggests the rally may be exhausted.
- **OBV vs. CMF/OFI:** OBV is rising (+6.7%), confirming the uptrend, but CMF and OFI are both negative, indicating recent selling pressure. Volume confirms the trend in aggregate but not in recent daily flows.
- **SuperTrend vs. MA Alignment:** SuperTrend flips daily (unreliable, currently -1), but MA alignment is classic bullish (EMA20>EMA50>EMA200). The SuperTrend is a false negative in a range-bound asset.

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | DO NOT ENTER | All three vol_filtered_meanrev entry conditions are unmet. Price is near resistance, not at oversold levels. |
| **Current holders** | HOLD (trim if concerned) | Bull regime is intact, but price is near 52-week high. Consider trimming 25-30% of position to lock in gains. |
| **Traders** | AVOID NEW POSITIONS | Range-bound market with low volatility and approaching resistance. No clear edge for either direction. |
| **Value investors** | WAIT FOR PULLBACK | Target entry zone: 370–380p (BB Lower area) with oversold RSI (<35) and CCI (<−100). |

- **Entry:** Wait for all three `vol_filtered_meanrev` conditions: Close ≤ BB Lower (~372p), RSI(14) < 35, CCI(20) < −100. This represents a ~10% pullback from current levels.
- **Stop-Loss:** Below swing low at 370.6p or EMA50 at 394.6p (whichever is lower). ATR-based stop: 372.3 − 3×9.3 = 344.4p (too wide for practical use).
- **Target:** BB Middle Band (403.4p) for quick mean-reversion play, or Donchian upper (429.4p) for full recovery.
- **Position Sizing:** Max 2% portfolio risk per trade (≈1/15th of capital). Smaller size if entering on a partial pullback only.
- **Max Holding Period:** ~30 days average (per strategy backtest). Exit manually if no progress within 30 days.

### Risk Factors
- **Breakout to the downside:** ATR percentile at 0% means a volatility expansion event is imminent. If it breaks down instead of up, the stock could rapidly fall to 372.3 (BB Lower) or below.
- **False breakout above resistance:** Price is only 1.2% below nearest resistance (418.3). A breakout could be fake, leading to a sharp reversal.
- **MFI at extreme (177.4):** The extreme MFI reading suggests excessive buying pressure that could reverse abruptly.
- **Institutional distribution:** ADL is negative (−547M), suggesting large players may be taking profits.
- **Range-bound nature:** MKS.L has no sustained trend (SuperTrend flips daily). Trend-following approaches are unlikely to succeed.

### When This Signal Is Invalidated
- **Close breaks below EMA50 (394.6p):** Bull regime may be weakening → signal becomes CAUTIOUS
- **Close breaks below swing low (370.6p):** Support broken, potential trend reversal → signal becomes BEARISH
- **HMM State 0 probability drops below 80%:** Regime stability compromised → signal becomes WAIT/CAUTIOUS
- **SuperTrend sustains -1 for >5 consecutive days:** Trend structure may be breaking → signal becomes CAUTIOUS

### Key Levels to Watch

| Event | Price Level | Distance | Action Trigger |
|-------|------------|----------|----------------|
| Stop loss trigger | 370.6 | −10.3% | Close below → exit position |
| Support 1 (EMA50) | 394.6 | −4.5% | Monitor for bounce |
| Support 2 (BB Lower) | 372.3 | −10.1% | Strategy entry zone |
| Entry zone (BB Lower + oversold) | 370–380 | −10% to −8% | Full vol_filtered_meanrev entry |
| Resistance 1 | 418.3 | +1.2% | Breakout test |
| Resistance 2 (Donchian upper) | 429.4 | +3.8% | 52-week high, major resistance |

---

## Next Steps

- **Monitor for pullback to 370–380p zone:** This is where the recommended `vol_filtered_meanrev` strategy would trigger entry. Set price alerts at 380p and 370p.
- **Watch MACD histogram:** If the histogram (currently +0.82) starts declining, it signals momentum weakening — a precursor to pullback.
- **Re-evaluation trigger:** Re-run this evaluation if MKS.L closes below EMA50 (394.6p) or if the HMM State 0 probability drops below 80%.
- **Strategy note:** If entering, use the full `vol_filtered_meanrev` entry rules: BB Lower + RSI < 35 + CCI < −100 + GARCH vol not rising. Do not enter on partial conditions alone.
- **Long-term note:** MKS.L is a FTSE 100 retail stock with low beta (0.35) — suitable as a defensive holding. The 6-month return of +27.1% is strong, but the 1-year return of +2.5% reflects the 2025 sector drawdown. Mean-reversion entries at support levels are historically profitable for this asset.
- **Alerts:** Set alerts at 380p (approaching entry zone) and 429.4p (52-week high breakout test).

---

*Report generated: 2026-10-27 | Data point: 2026-10-27 | Data: `data/analysis-data/MKS.L.csv` (5,053 rows) | Strategy: `data/reports/strategies/MKS.L/2026-10-26.md`*
