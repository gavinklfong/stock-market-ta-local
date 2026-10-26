# Market Situation Evaluation: Legal & General (LGEN.L)

**Evaluation Date:** 2026-10-26
**Actual Date Used:** 2026-10-26
**Ticker:** LGEN.L (Legal & General)
**Price:** £300.90
**Data Range:** 2006-10-26 to 2026-10-26 (5,053 rows)
**Sector:** Financials (Insurance & Asset Management)
**Strategy Reference:** `data/reports/strategies/LGEN.L/2026-10-23.md`

---

## Executive Summary

**Signal:** WAIT
**Confidence:** Medium

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🟡 CAUTIOUS | 🟡 Medium | EMA alignment bullish but ADX only 11.1 (weak trend) |
| **Momentum** | 🟡 CAUTIOUS | 🟡 Medium | RSI 60 rising, MACD bullish but near overbought extremes |
| **Return** | 🟢 POSITIVE | 🟢 High | +19.4% 6M, +23.5% 1Y — strong momentum |
| **Structure** | 🟡 CAUTIOUS | 🟡 Medium | Near resistance (£309), no BOS signal active |
| **Volatility** | 🟡 NORMAL | 🟡 Medium | Low ATR percentile (0%), narrow BB width (6.9%) |
| **Volume** | 🟡 MIXED | 🟡 Medium | Volume at 45th percentile — average participation |
| **Regime** | 🟢 BULL | 🟢 High | HMM regime 0 (bull) 76.8%, stable 18 days |
| **Overall** | 🟠 CAUTION | 🟡 Medium | Strong regime and returns undermined by lack of strategy entry signals |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | £300.90 | 83.0% of 52-week high, near upper range |
| 52-Week Range | £217.20 – £318.10 | At 83% of range — near resistance zone |
| P/E (TTM) | N/A | Insufficient data for P/E on latest row |
| Dividend Yield | N/A | Insufficient data on latest row (strategy: ~8.4%) |
| Beta (20d) | 1.01 | Near market — tracks FTSE 100 closely |
| RS vs FTSE 100 | 2.79 | Modest outperformance of FTSE 100 |

### Strategy Alignment Summary

| Strategy Element | Current Value | Alignment |
|-----------------|---------------|-----------|
| Close ≤ BB Lower Band (£282.92) | £300.90 (+6.4% above) | ❌ NOT MET |
| RSI < 35 (oversold entry) | RSI 60.17 | ❌ NOT MET |
| CCI < -100 (extreme sell-off) | CCI 119.04 (overbought) | ❌ NOT MET |
| Crash filter: no >10% drop in 20d | Price rose ~5.6% from Oct low | ✅ MET (no crash risk) |
| HMM regime not bear | Regime 0 (bull) at 76.8% | ✅ MET |
| **Overall Strategy Fit** | — | ⚠️ **Strategy is mean-reversion; current position is opposite of entry zone** |

**Strategy Verdict:** The recommended `lgen_crash_protected_upper` strategy is a Bollinger Band mean-reversion strategy that profits from price dips to the lower band. Current conditions are the **opposite** of the ideal setup — price is near the BB upper (£303.28), RSI is elevated (60), and CCI is overbought (119). The strategy's entry conditions are **all NOT MET**. This is a WAIT signal: the strong bullish regime and excellent returns are positive, but entering a mean-reversion strategy at the upper end of the range is counter to the strategy's logic.

### Signal Summary

**Current Signal: WAIT**

LGEN.L exhibits a strong bullish regime (76.8% bull probability) and has delivered exceptional returns (+23.5% over 1 year). However, the recommended strategy is a **mean-reversion** approach that profits from dips to the lower Bollinger Band — current price is near the upper band. For holders, this is a comfortable position to maintain. For non-holders, the optimal entry point (price near £283 with oversold momentum) does not exist yet. Wait for a pullback to the BB lower band or a mean-reversion entry opportunity.

---

## 1. Trend Analysis

**Signal:** CAUTIOUS | **Confidence:** MEDIUM

LGEN.L shows a technically bullish EMA alignment (EMA20 > EMA50 > EMA200) but with notably weak trend strength (ADX = 11.1). The SuperTrend is bullish, but price is approaching the Donchian upper band and Bollinger Band upper — suggesting the move may be nearing resistance. The MA20 slope is barely positive (0.006) while MA50 slope is slightly negative (-0.175), indicating the recent uptrend has not yet been confirmed by the medium-term trend line.

### Current Indicators

| Indicator | Value | Signal |
|-----------|-------|--------|
| EMA20 | 295.44 | Price £300.90 is 1.85% above — bullish |
| EMA50 | 293.80 | Price £300.90 is 2.42% above — bullish |
| EMA200 | 279.24 | Price £300.90 is 7.76% above — bullish |
| SuperTrend Direction | +1 | Bullish (stable, no recent flip) |
| SuperTrend Trail | 297.01 | Price 1.33% above trail — bullish |
| MA20 Slope | 0.006 | Barely positive — weak uptrend |
| MA50 Slope | -0.175 | Slightly negative — not yet confirmed |
| ADX(14) | 11.12 | Well below 25 — weak trend |
| DI+ / DI- | 24.21 / 18.02 | Bullish dominance (+DI > -DI) |
| Aroon Up / Down | 100.0 / 36.0 | Strong upward pressure |
| Price vs EMA20 | +1.85% | Above — bullish |

### Trend Assessment
- **MA Alignment:** EMA20 (295.44) > EMA50 (293.80) > EMA200 (279.24) — **bullish alignment** ✓
- **SuperTrend:** Direction +1 (bullish), trail at £297.01, price 1.33% above — **stable bullish** ✓
- **MA Slopes:** MA20 slope 0.006 (barely positive), MA50 slope -0.175 (slightly negative) — **recent uptrend not yet confirmed by medium-term** ⚠️
- **Trend Strength:** ADX 11.12 — **well below 25, weak trend**. Strategy report confirms LGEN.L has historically weak trend (ADX avg ~21.6). Not ideal for trend-following.
- **Donchian Position:** Price £300.90 vs Donchian upper £302.30 — **near upper, potential resistance** ⚠️
- **Keltner Position:** Price £300.90 vs Keltner upper £303.90 — **inside Keltner bands** ✓

### Trend Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| MA Alignment (EMA20>EMA50>EMA200) | +2 | 25% | +0.50 |
| SuperTrend Direction (bullish) | +1 | 15% | +0.15 |
| MA Slopes (mixed: MA20+, MA50-) | 0 | 15% | 0.00 |
| ADX Trend Strength (weak) | -1 | 25% | -0.25 |
| Donchian/Keltner Position (near resistance) | -1 | 20% | -0.20 |
| **Trend Score** | | **100%** | **+0.20 / 3.0** |

**Trend Verdict:** Technically bullish alignment but weak trend strength — CAUTIOUS. LGEN.L is historically a mean-reversion asset, not a trend asset. The weak ADX (11.1) confirms this.

### Strategy Alignment
The recommended `lgen_crash_protected_upper` strategy does not rely on trend strength — it uses Bollinger Band mean-reversion. The weak trend (low ADX) is actually **consistent** with the strategy's design, as mean-reversion works best in weak-trend, range-bound environments. However, the current price position (near BB upper, not lower) is the opposite of the strategy's entry zone.

---

## 2. Momentum Analysis

**Signal:** CAUTIOUS | **Confidence:** MEDIUM

Momentum indicators show mixed signals. RSI at 60 is in neutral territory, MACD is bullish with a positive histogram, but several oscillators (Williams %R, CCI, Stochastic) are flashing overbought signals. The recent 20-day RSI rose from 49.2 to 60.2, confirming the price rally from £294 to £300.90. However, the strategy's entry conditions require oversold momentum (RSI < 35, CCI < -100), which are the **opposite** of current readings.

### Current Indicators

| Indicator | Value | Signal |
|-----------|-------|--------|
| RSI(14) | 60.17 | Neutral — above 50 but below overbought |
| RSI Z-Score(14,20) | 1.38 | Above average — 90th percentile |
| RSI Percentile(14,20) | 90.0% | High — RSI elevated vs 20-day window |
| MACD Line | 1.85 | Bullish (above signal) |
| MACD Signal | 0.76 | MACD above signal — bullish cross maintained |
| MACD Histogram | 1.09 | Positive, stable (peaked 1.33 on Oct 21, now cooling slightly) |
| ROC(20) | 1.38% | Positive momentum |
| Williams %R | -7.53 | Overbought (< -20 = overbought) |
| CCI(20) | 119.04 | Overbought (> +100) |
| MFI(14) | -136.35 | ⚠️ Anomalous (typically 0–100) — data issue, ignore |
| Stochastic %K / %D | 100.0 / 90.04 | Overbought |

### Momentum Assessment
- **RSI Context:** RSI at 60.17, z-score 1.38, 90th percentile — **elevated but not extreme**. Recent 20-day move from 49.2 to 60.2 confirms the price rally.
- **MACD State:** Line (1.85) > Signal (0.76), histogram positive (1.09) — **bullish cross maintained**. Histogram peaked at 1.33 on Oct 21 and is now slightly cooling (1.09), suggesting momentum may be peaking.
- **Oscillator Convergence:** Williams %R (-7.53), CCI (119), Stochastic (100/90) all **overbought**. RSI (60) and ROC (1.38%) are **neutral**. Mixed convergence — short-term overbought but not extreme.
- **Divergence Check:** Price has rallied from £285.60 (Oct 1) to £300.90 (Oct 26) while momentum indicators are also rising — **no divergence**. Momentum confirms price action.
- **Strategy Fit:** The strategy requires RSI < 35 and CCI < -100 for entry. Current RSI = 60.17, CCI = 119.04 — **exact opposite** of entry conditions.

### Momentum Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| MACD State (bullish cross maintained) | +1 | 25% | +0.25 |
| RSI Context (neutral, elevated) | 0 | 20% | 0.00 |
| Oscillator Overbought Signals (Williams, CCI, Stoch) | -1 | 25% | -0.25 |
| Momentum Confirmation of Price Rally | +1 | 15% | +0.15 |
| Strategy Entry Alignment (RSI/CCI opposite) | -1 | 15% | -0.15 |
| **Momentum Score** | | **100%** | **+0.00 / 3.0** |

**Momentum Verdict:** NEUTRAL — bullish MACD but multiple overbought oscillators cancel out the positive. Momentum confirms the recent rally but offers no fresh bullish signal.

### Strategy Alignment
The strategy's entry conditions require **oversold** momentum (RSI < 35, CCI < -100). Current momentum is **overbought** across multiple oscillators — the complete opposite of the strategy's entry requirements. This is a key reason for the WAIT signal.

---

## 3. Return Analysis

**Signal:** POSITIVE | **Confidence:** HIGH

LGEN.L has delivered exceptional returns across all timeframes: +1.14% over 1 month, +19.43% over 6 months, and +23.47% over 1 year. The positive alpha (0.031) confirms outperformance vs the FTSE 100 benchmark, while beta of 1.01 indicates near-market volatility. Relative strength vs FTSE 100 stands at 2.79, modest outperformance. However, the strategy report identifies LGEN.L as a **mean-reversion asset** — strong past returns do not imply continuation; mean-reversion assets tend to revert after strong moves.

### Past Performance

| Period | Return | Assessment |
|--------|--------|------------|
| 1 Month | +1.14% | Modest — recent consolidation after rally |
| 3 Months | +1.14% | Same as 1M (price flat over 3M) — range-bound |
| 6 Months | +19.43% | Strong — excellent medium-term performance |
| 1 Year | +23.47% | Excellent — strong long-term performance |

### Risk-Adjusted Metrics

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Alpha(20) | 0.031 | Positive — modest outperformance of FTSE 100 |
| Beta(20) | 1.01 | Near market — moves in line with FTSE 100 |
| RS vs FTSE 100 | 2.79 | Modest outperformance of FTSE 100 |

### Forward Return Context

| Forward Period | Mean Return | Std Dev | Assessment |
|---------------|-------------|---------|------------|
| 5 days | +0.36% | 2.97% | Near-zero — no directional bias |
| 10 days | +0.71% | 3.85% | Near-zero — no directional bias |
| 20 days | +1.33% | 4.76% | Slightly positive but high variance |

### Return Assessment
- **Short-term trend:** 1M at +1.14% and 3M at +1.14% — **flat consolidation**. The stock has not moved much over the past 3 months despite the 1Y gain.
- **Medium-term trend:** 6M at +19.43% and 1Y at +23.47% — **strong past performance**. However, this is a mean-reversion asset; past returns may reverse.
- **Risk-adjusted:** Alpha 0.031 (positive), Beta 1.01 (market-like), RS 2.79 (modest outperformance) — **reasonable risk-adjusted returns**.
- **Forward expectations:** Forward returns mean near-zero across all periods — **no directional bias expected**. This is consistent with a mean-reversion asset.

### Return Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| 6M/1Y Returns (strong) | +2 | 30% | +0.60 |
| 1M/3M Returns (flat) | 0 | 20% | 0.00 |
| Alpha (positive, 0.031) | +1 | 20% | +0.20 |
| Beta (near market, 1.01) | 0 | 15% | 0.00 |
| Forward Return Bias (near-zero) | -1 | 15% | -0.15 |
| **Return Score** | | **100%** | **+0.65 / 3.0** |

**Return Verdict:** POSITIVE — strong historical returns with positive alpha, but forward expectations are near-zero (consistent with mean-reversion asset). Past performance does not guarantee continuation.

### Strategy Alignment
The strategy report explicitly identifies LGEN.L as a **mean-reversion asset**. The strategy `lgen_crash_protected_upper` is designed to profit from price dips, not momentum continuation. The strong past returns (+19.4% 6M) actually increase the likelihood of mean reversion — the stock may pull back from current elevated levels. The near-zero forward returns confirm this: the market does not expect continuation.

---

## 4. Structure Analysis

**Signal:** CAUTIOUS | **Confidence:** MEDIUM

LGEN.L is currently trading near its resistance zone. The nearest resistance is at £309.27 (2.78% above), and the Donchian upper band sits at £302.30 (just 0.46% above price). The swing high is at £308.54. Support is closer at £294.90 (1.99% below), with the SuperTrend trail providing additional support at £297.01. No clear higher-high/higher-low structure is detected (HH=0, HL=0), and the trend label is -1 (bearish), which conflicts with the bullish EMA alignment — indicating the structural picture is mixed.

### Key Levels

| Level | Value | Distance from Current | Significance |
|-------|-------|----------------------|--------------|
| **Resistance** | £309.27 | +2.78% | Nearest resistance (swing pivot) |
| Donchian Upper | £302.30 | +0.46% | 20-day breakout level — very close |
| 52-Week High | £318.10 | +5.71% | Annual resistance |
| **Support** | £294.90 | -1.99% | Nearest structural support |
| SuperTrend Trail | £297.01 | -1.33% | SuperTrend support level |
| BB Lower | £282.92 | -6.03% | Strategy entry zone (BB mean-reversion) |
| Nearest Support | £294.90 | -1.99% | Closest support level |

### Structure Signals

| Signal | Value | Interpretation |
|--------|-------|----------------|
| HH (Higher High) | 0 | No higher high detected — no bullish structure |
| HL (Higher Low) | 0 | No higher low detected — no bullish structure |
| LH (Lower High) | 0 | No lower high — no bearish structure |
| LL (Lower Low) | 0 | No lower low — no bearish structure |
| BOS (Break of Structure) | 0 | No break of structure — range-bound |
| CHoCH (Change of Character) | 0 | No trend reversal signal |
| Swing High | £308.54 | Recent peak — resistance level |
| Swing Low | £283.30 | Recent trough — support level |
| Trend Label | -1 | Bearish — conflicts with EMA alignment |
| Support Touches | 63 | Well-established support (historical) |

### Structure Assessment
- **Pattern:** No HH/HL or LH/LL signals detected, BOS = 0, CHoCH = 0 — **range-bound** with no clear directional structure.
- **Key levels:** Price £300.90 is sandwiched between resistance at £309.27 (+2.78%) and support at £294.90 (-1.99%). The Donchian upper at £302.30 is just 0.46% away — a breakout above this would signal a new short-term high.
- **Recent breaks:** No BOS or CHoCH signals — structure is intact but directionless.
- **Support touches:** 63 historical support touches — **well-established support** level. The swing low at £283.30 aligns with the BB lower band (£282.92), which is the strategy's entry zone.

### Structure Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| Support proximity (£294.90, 1.99%) | +1 | 20% | +0.20 |
| Near Donchian upper (resistance) | -1 | 25% | -0.25 |
| No BOS/CHoCH (range-bound) | 0 | 20% | 0.00 |
| Trend label conflicts with EMA (-1 vs bullish) | -1 | 25% | -0.25 |
| Strategy entry zone alignment (price far from BB lower) | -1 | 10% | -0.10 |
| **Structure Score** | | **100%** | **-0.40 / 3.0** |

**Structure Verdict:** CAUTIOUS — price near resistance with no clear breakout signal. Structural picture is mixed; trend label is bearish despite bullish EMAs.

### Strategy Alignment
The recommended strategy relies on BB mean-reversion, which requires price to reach the lower band (£282.92). Current structural position near the upper band (£302.30 Donchian) is **not aligned** with the strategy's entry requirements. A pullback of ~£18 to £283 would be needed to reach the strategy's entry zone.

---

## 5. Volatility Analysis

**Signal:** NORMAL | **Confidence:** MEDIUM

Volatility is currently very low — ATR is at the 0th percentile (historically lowest), and Bollinger Band width is narrow at 6.95%. Price sits at 88.3% of the Bollinger Bands (%B = 0.88), near the upper band. GARCH volatility forecast (1.085) suggests mild volatility expansion expected. This combination of low ATR percentile and narrow BB width often precedes a breakout — but direction is uncertain.

### Current Indicators

| Indicator | Value | Assessment |
|-----------|-------|------------|
| ATR(14) | 4.48 | Low absolute level |
| ATR Percentile | 0% | Extremely low — historically lowest volatility |
| BB Width | 6.95% | Narrow — potential breakout setup |
| %B | 0.88 | Near upper band (0 = lower, 1 = upper) |
| BB Upper | £303.28 | Near-term resistance |
| BB Lower | £282.92 | Near-term support (strategy entry zone) |
| HV(20) | 13.98% | Moderate historical volatility |
| Park Volatility | 15.70% | Range-based estimate — similar to HV |
| GARCH Vol | 1.085 | Forecast mild expansion |
| ATR Stop Distance | 4.47 | Suggested stop ~4.5 points below entry |

### Volatility Assessment
- **Volatility Level:** ATR at 0th percentile — **extremely low volatility**. This is unusual and often precedes a significant move.
- **Band Position:** Price at 88.3% of BB (%B = 0.88) — **near upper band**, close to resistance. BB width of 6.95% is narrow — potential squeeze.
- **Volatility Trend:** HV(20) at 13.98%, GARCH at 1.085 — **mild expansion expected**. GARCH > 1 suggests slightly higher future volatility.
- **Breakout Potential:** Narrow BB width + extremely low ATR = **potential breakout imminent**. Direction uncertain — could be up (continuation) or down (mean reversion).
- **Suggested Stop:** ATR-based stop distance of 4.47 points. For a mean-reversion entry at £283, stop would be at ~£278.5.

### Volatility Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| Low ATR Percentile (breakout setup) | +1 | 25% | +0.25 |
| %B near upper band (overextended) | -1 | 25% | -0.25 |
| GARCH forecast (mild expansion) | 0 | 20% | 0.00 |
| BB Width narrow (squeeze) | +1 | 15% | +0.15 |
| Strategy volatility fit (normal for BB mean-reversion) | 0 | 15% | 0.00 |
| **Volatility Score** | | **100%** | **+0.15 / 3.0** |

**Volatility Verdict:** NORMAL — extremely low volatility creates a breakout setup, but the direction is unclear. Price near BB upper favors mean-reversion (downside) over breakout (upside).

### Strategy Alignment
The `lgen_crash_protected_upper` strategy uses BB mean-reversion, which works best in moderate-to-low volatility environments. Current low volatility (ATR 0th percentile) is **consistent** with the strategy's optimal conditions. However, the entry requires price at the BB lower — current price at BB upper means the volatility setup is correct but the price position is wrong.

---

## 6. Volume Analysis

**Signal:** MIXED | **Confidence:** MEDIUM

Volume is moderate at the 45th percentile — not extreme but not negligible. OBV has been rising strongly (up £129.6M over 20 days), confirming the price rally. CMF just turned positive (0.031) after being negative throughout early October, suggesting a shift in buying pressure. OFI is positive (0.216), and price trades above VWAP (£292.58). However, MFI(14) at -136.35 is anomalous (typically 0–100) and likely a data issue — it should be disregarded.

### Current Indicators

| Indicator | Value | Assessment |
|-----------|-------|------------|
| OBV | 1,674,340,142 | Rising strongly (+£129.6M over 20 days) — confirms price trend |
| CMF(20) | 0.031 | Just turned positive — buying pressure emerging |
| OFI | 0.216 | Positive — order flow favors buyers |
| VWAP | £292.58 | Price £300.90 is 2.88% above VWAP — bullish |
| ADL | -1,260,540,142 | Negative — distribution pressure (mixed) |
| MFI(14) | -136.35 | ⚠️ Anomalous — data issue, ignore |
| Volume Z-Score | -0.22 | Slightly below average |
| Volume Percentile | 45th | Average volume intensity |
| EMV(14) | 2.99e-07 | Near zero — ease of movement neutral |
| OBV Slope(14) | +7,871,485 | Strongly positive — volume confirms rally |

### Volume Assessment
- **Buying/Selling Pressure:** CMF turned positive (0.031) from negative (-0.189 on Sep 29) — **shifting toward buying**. OFI positive at 0.216 confirms.
- **Volume Trend:** OBV rising strongly (+£129.6M over 20 days) — **volume confirms price trend**. OBV slope both 14-day and 7-day positive.
- **Volume Intensity:** Z-Score -0.22 (slightly below average), Percentile 45th — **average volume**. Not a high-conviction move.
- **Smart Money:** ADL negative (-1.26B) — **distribution pressure**. This is a divergence signal: price rising but ADL falling.
- **Divergence Warning:** ADL is negative while OBV is positive — **mixed volume signals**. OBV confirms the rally, but ADL suggests some distribution. CMF just turned positive — buying pressure is emerging but not yet strong.

### Volume Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| OBV Trend (strongly rising) | +1 | 25% | +0.25 |
| CMF turned positive (buying pressure) | +1 | 20% | +0.20 |
| Price above VWAP (bullish) | +1 | 20% | +0.20 |
| ADL negative (distribution divergence) | -1 | 20% | -0.20 |
| Volume intensity (average, z-score -0.22) | 0 | 15% | 0.00 |
| **Volume Score** | | **100%** | **+0.25 / 3.0** |

**Volume Verdict:** MIXED — OBV and CMF confirm buying, but ADL divergence and average volume intensity temper enthusiasm. Buying pressure is emerging but not yet dominant.

### Strategy Alignment
The `lgen_crash_protected_upper` strategy does not have specific volume entry conditions. However, the emerging buying pressure (CMF positive, OBV rising) supports the current price level and reduces the likelihood of an immediate sharp mean-reversion pullback. If a pullback does occur, volume should diminish for a healthy correction.

---

## 7. Regime Analysis

**Signal:** BULL | **Confidence:** HIGH

The HMM regime model shows a firmly bullish regime with 76.8% probability in state 0 (bullish), 0.2% in state 1 (bearish), and 23.0% in state 2 (neutral/sideways). The regime has been stable in state 0 for 18 consecutive days, with only one brief excursion to state 2 on Oct 1 (neutral, 74% probability) that quickly reverted to state 0. This is the most stable bullish regime reading in the 30-day window. The strategy report's crash filter is satisfied — no crash risk in the current regime.

### HMM Regime Probabilities

| Regime State | Probability | Interpretation |
|-------------|-------------|----------------|
| State 0 (Bull) | 76.81% | **Dominant regime** — strong bullish probability |
| State 1 (Bear) | 0.22% | Negligible — no bearish risk detected |
| State 2 (Neutral) | 22.97% | Moderate — some sideways probability |

### Regime Assessment
- **Dominant Regime:** State 0 (bull) at 76.81% — **strongly bullish**. State 1 (bear) probability is negligible at 0.22%.
- **Regime Stability:** Regime has been state 0 (bull) for **18 consecutive days** (since Oct 2). One brief excursion to state 2 on Oct 1 (after the dip to £285.60) that quickly reverted to state 0. The 30-day window shows 6 regime changes early in the period, but stability has increased significantly in the last 18 days.
- **GARCH Context:** GARCH vol at 1.085 — mild expansion but within bull regime. Not a concern for regime stability.
- **Trend vs Regime Divergence:** Trend indicators are mixed (EMA alignment bullish but ADX weak, trend label -1). However, the regime model is **strongly bullish (76.8%)**. The regime model's conviction outweighs the mixed trend signals — the regime model is designed to filter out noise.

### Regime Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| HMM Prob State 0 (76.8% bull) | +2 | 40% | +0.80 |
| Regime Stability (18 days stable) | +1 | 30% | +0.30 |
| Negligible bear probability (0.22%) | +1 | 20% | +0.20 |
| Mild GARCH expansion | 0 | 10% | 0.00 |
| **Regime Score** | | **100%** | **+1.30 / 3.0** |

**Regime Verdict:** BULL — strong and stable bullish regime with negligible bear risk. The most favorable regime reading in the 30-day window.

### Strategy Alignment
The `lgen_crash_protected_upper` strategy includes a crash filter (skip entries when price dropped >10% in 20 days). The current bullish regime (76.8% bull, 0.22% bear) with stable 18-day consistency means the **crash filter is satisfied** — no crash risk. This is one of the strategy conditions that IS MET. The strategy performs best in bull regimes with low crash probability, which is exactly the current setup.

---

## Signal Synthesis

### Aggregate Score Summary

| # | Dimension | Signal | Score (/3.0) | Weight | Weighted |
|---|-----------|--------|-------------|--------|----------|
| 1 | **Trend** | CAUTIOUS | +0.20 | 15% | +0.03 |
| 2 | **Momentum** | NEUTRAL | 0.00 | 15% | 0.00 |
| 3 | **Return** | POSITIVE | +0.65 | 15% | +0.10 |
| 4 | **Structure** | CAUTIOUS | -0.40 | 10% | -0.04 |
| 5 | **Volatility** | NORMAL | +0.15 | 10% | +0.02 |
| 6 | **Volume** | MIXED | +0.25 | 10% | +0.03 |
| 7 | **Regime** | BULL | +1.30 | 25% | +0.33 |
| | **AGGREGATE** | | | **100%** | **+0.47** |

### Score Interpretation

| Range | Signal | Interpretation |
|-------|--------|---------------|
| +2.0 to +3.0 | Strong Bullish | All dimensions aligned — strong buy signal |
| +0.5 to +1.9 | Mildly Bullish | Trend favors longs but monitor for reversals |
| **-0.5 to +0.4** | **Neutral / Wait** | **Mixed signals — do not initiate new positions** |
| -0.5 to -1.9 | Mildly Bearish | Caution warranted, consider reducing exposure |
| -2.0 to -3.0 | Strong Bearish | All dimensions negative — avoid longs |

**Aggregate Score: +0.47 — WAIT**

The aggregate score of +0.47 falls in the "Neutral / Wait" range. While the bullish regime (0.33 weighted contribution) and positive returns (0.10) push the score slightly positive, the structure dimension (-0.04) and neutral momentum (0.00) pull it back. The score is borderline — the market is not clearly bullish enough for a BUY signal, but not bearish enough for a SELL either. The critical factor is that the recommended strategy is a **mean-reversion** approach that requires price at the lower Bollinger Band (£282.92) with oversold momentum, and current conditions are the exact opposite (price near BB upper at £303.28 with overbought oscillators).

### Signal Determination
- **Overall Signal:** WAIT
- **Strength:** Weak (score barely above neutral)
- **Confidence:** Medium (regime is clear, but strategy entry conditions not met)

### Supporting Indicators (Top 3 per Dimension)

| Dimension | Indicator 1 | Indicator 2 | Indicator 3 |
|-----------|------------|------------|------------|
| Trend | EMA alignment (bullish) | SuperTrend (+1) | ADX (weak — caution) |
| Momentum | MACD bullish cross | RSI 60 (neutral) | Overbought oscillators (caution) |
| Return | 6M/1Y returns (strong) | Alpha +0.031 (positive) | Near-zero forward returns |
| Structure | Support proximity | Near resistance (caution) | Trend label -1 (conflict) |
| Volatility | Low ATR percentile (0%) | %B at 0.88 (near upper) | BB width 6.9% (narrow) |
| Volume | OBV rising (+£129.6M) | CMF turned positive | ADL divergence (caution) |
| Regime | HMM prob 0 (76.8%) | 18-day stability | Negligible bear prob (0.22%) |

### Conflicting Indicators
- **Trend vs Structure:** EMA alignment is bullish (EMA20 > EMA50 > EMA200) but the trend label is -1 (bearish). This conflict reflects the weak trend (ADX 11.1) — the market is technically aligned but structurally directionless.
- **Price vs Strategy:** The regime and returns are strongly bullish, but the recommended strategy (BB mean-reversion) requires oversold conditions at the lower band. Current price at BB upper is the **opposite** of the entry zone.
- **Volume Signals:** OBV is strongly rising (bullish confirmation) but ADL is negative (distribution), suggesting mixed smart money activity. CMF just turned positive — buying pressure is emerging but not yet dominant.

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | DO NOT ENTER | Strategy entry conditions (BB lower, RSI < 35, CCI < -100) are NOT MET. Price is near BB upper, not lower. |
| **Current holders** | HOLD | Strong regime and positive returns support holding. No exit signal present. |
| **Traders** | AVOID | Range-bound with low ADX — not suitable for trend-following trades. Wait for clearer signal. |
| **Value investors** | PATIENCE | If the strategy's entry conditions are met (price near £283), this would be a good entry for long-term holders given the 8.4% dividend yield. |

- **Entry:** Wait for price to pull back to BB lower band (~£283) with RSI < 35, CCI < -100, and crash filter satisfied. This represents a ~5.9% pullback from current levels.
- **Stop-Loss:** Below £275 (approximately 2x ATR below BB lower, or ~£283 - £8 = £275).
- **Target:** Nearest resistance at £303 (BB upper) to £309 (swing high). Upside of ~6.9–8.7% from entry.
- **Position Sizing:** Standard — the strategy has demonstrated 115% total return with 23% max DD over 10 years.
- **Max Holding Period:** 20–60 days (consistent with the strategy's backtested holding periods).

### Risk Factors
- **Regime shift to bear:** If HMM prob_1 rises above 30% or regime flips to state 1, the bullish thesis is invalidated.
- **Price breakdown below SuperTrend (£297):** Would signal trend reversal and invalidate current bullish structure.
- **Momentum exhaustion:** Overbought oscillators (Williams %R, CCI, Stochastic) suggest the current rally may be overextended — a pullback could occur even without a regime change.
- **Mean-reversion timing:** If price continues to grind higher in the bull regime, the mean-reversion strategy will underperform. The entry may not materialize for an extended period.

### When This Signal Is Invalidated
- **Close below £283 (BB lower)** → Signal becomes **BUY** (strategy entry conditions met)
- **Close above £318 (52-week high)** → Signal becomes **HOLD/CAUTION** (breakout but overextended)
- **HMM regime flips to state 1 (bear)** → Signal becomes **SELL** (regime shift invalidates bull thesis)
- **RSI drops below 35** → Signal becomes **WAIT/BUY-ZONE** (oversold mean-reversion entry setup)

### Key Levels to Watch

| Event | Price Level | Distance | Action Trigger |
|-------|------------|----------|----------------|
| Stop loss trigger | £275.00 | −8.5% | If BB lower entry taken and price drops below |
| Support 1 | £294.90 | −2.0% | Hold if tested and bounced |
| Support 2 (BB lower) | £282.92 | −6.0% | **Strategy entry zone** — buy if RSI < 35, CCI < -100 |
| Entry zone (BB lower) | £283–£285 | −5.4% to −4.9% | Wait for oversold momentum confirmation |
| Resistance 1 (Donchian) | £302.30 | +0.5% | Break above = near-term breakout |
| Resistance 2 (swing high) | £309.27 | +2.8% | Break above = new short-term high |
| Resistance 3 (52-week high) | £318.10 | +5.7% | Break above = annual resistance test |

---

## Next Steps

- **Monitor for pullback to BB lower band (~£283):** This is the strategy's entry zone. Watch for price to drop ~6% from current levels with oversold RSI (< 35) and CCI (< -100).
- **Watch MACD histogram for reversal:** Current histogram at 1.09 is cooling from its peak of 1.33 on Oct 21. A reversal to negative histogram would confirm momentum exhaustion and increase the likelihood of a pullback.
- **Track regime stability:** If HMM regime flips from state 0 to state 1 (bear), signal becomes SELL. Current 18-day stability is a positive indicator.
- **Re-run evaluation if:** Close drops below £294.90 (support) — check for mean-reversion entry opportunity. Or if Close rises above £309.27 (resistance) — reassess breakout potential.
- **If entering, use `lgen_crash_protected_upper` entry rules:** BB lower band touch + RSI < 35 + CCI < -100 + no crash in last 20 days. Stop at £275, target £303–£309.
- **Consider as long-term hold:** LGEN.L has delivered +23.5% over 1 year with strong dividend yield (~8.4%). For long-term holders, current levels are acceptable for holding but not aggressive new entries.
- **Set alerts:** Price alerts at £283 (buy zone), £294.90 (support), £309.27 (resistance), and £318.10 (52-week high). Regime alert if HMM state changes.
- **Re-evaluation:** Run this evaluation again in 1–2 weeks, or immediately if any key level is breached (support or resistance).

---

*Report generated: 2026-10-26 | Data point: 2026-10-26 → 2026-10-26 | Data: `data/analysis-data/LGEN.L.csv` (5,053 rows) | Strategy: `data/reports/strategies/LGEN.L/2026-10-23.md`*
