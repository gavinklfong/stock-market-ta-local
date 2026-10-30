# Market Situation Evaluation: Legal & General (LGEN.L)

**Evaluation Date:** 2026-10-29
**Actual Date Used:** 2026-10-29
**Ticker:** LGEN.L (Legal & General Group Plc)
**Price:** £304.90
**Data Range:** 2006-10-30 to 2026-10-29 (5,054 rows)
**Sector:** Insurance
**Strategy Reference:** `data/reports/strategies/LGEN.L/2026-10-29.md`

---

## Executive Summary

**Signal:** HOLD
**Confidence:** Medium

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🟢 BULLISH | 🟡 Medium | EMA20 > EMA50 > EMA200, DI+ > DI- |
| **Momentum** | 🔴 BEARISH | 🟡 Medium | RSI 65.2 near overbought, CCI 130.9, Stoch 100 |
| **Return** | 🟢 POSITIVE | 🟢 High | 6M: +19.6%, 1Y: +27.1%, positive alpha |
| **Structure** | 🟡 CAUTIOUS | 🟡 Medium | Price near resistance at 309.27, trend label -1 |
| **Volatility** | 🟢 LOW | 🟢 High | ATR percentile 20%, BB width contracting |
| **Volume** | 🟢 BULLISH | 🟡 Medium | OBV rising, CMF +0.195, price above VWAP |
| **Regime** | 🟢 BULL | 🟡 Medium | State 0 dominant (58.9%), stable GARCH |
| **Overall** | 🟡 HOLD | 🟡 Medium | 4 bullish, 1 bearish, 1 neutral — trend supports hold but momentum warns against entry |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | £304.90 | Near 52-week high of £318.10 (95.8%) |
| 52-Week Range | £217.20 – £318.10 | At 95.8% of high — overextended |
| P/E (TTM) | N/A | Data unavailable |
| Dividend Yield | ~8.4% | High yield, provides cushion |
| Beta (20d) | 0.64 | Less volatile than FTSE 100 |
| RS vs FTSE 100 | 2.84 | Outperforming FTSE 100 |

### Strategy Alignment Summary

#### Entry conditions
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| Close ≤ BB Lower (20, 2) | £304.90 vs BB Lower £283.05 | ❌ NOT MET (price near BB Upper) |
| RSI(14) < 35 (or < 40 optimized) | 65.2 | ❌ NOT MET (near overbought) |
| CCI(20) < -100 | 130.9 | ❌ NOT MET (overbought) |
| GARCH vol stable or declining | 1.025 (from recent ~1.03) | ✅ CONFIRMED (vol not rising) |

**Strategy Verdict:** None of the three core entry conditions are met. Price is at the upper band, not lower — this is the **opposite** of a mean-reversion entry signal. The strategy would recommend waiting for a pullback.

#### Exit conditions
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| Close ≥ BB Upper (20, 2) | £304.90 vs BB Upper £307.06 | ⚠️ CAUTION (91% of upper band, approaching) |
| ATR trailing stop triggered | ATR trail ≈ £281.5 | ✅ NOT MET (price well above trail) |
| 30-day time stop | N/A | ✅ NOT MET |

**Strategy Verdict:** Price is approaching the BB Upper exit threshold. Current holders should monitor closely — a break above £307 could trigger exit. The signal is cautiously aligned with an exit setup.

### Signal Summary

**Current Signal: HOLD / MEDIUM STRENGTH**

Trend and return indicators are solidly bullish, and the regime is bullish — current holders should maintain positions. However, momentum is strongly overbought across multiple oscillators, and all mean-reversion entry conditions are unmet. Non-holders should wait for a pullback to BB Lower with RSI < 35 for entry. The stock is in the final stages of its current rally and approaching resistance.

---

## 1. Trend Analysis

**Signal:** BULLISH | **Confidence:** MEDIUM

LGEN.L is in a well-structured uptrend with price above all three key EMAs. However, ADX is low at 13.9, indicating weak trend strength — consistent with the strategy report's classification of LGEN as a mean-reverting stock. The SuperTrend is bullish but the `ta_trend` label shows -1, suggesting some structural conflict.

### Current Indicators

| Indicator | Value | Signal |
|-----------|-------|--------|
| EMA20 | £297.59 | Bullish (price 2.46% above) |
| EMA50 | £294.92 | Bullish (price 3.38% above) |
| EMA200 | £279.97 | Bullish (price 8.91% above) |
| SuperTrend Direction | +1 | Bullish |
| SuperTrend Trail | £297.01 | Price 2.69% above trail |
| MA20 Slope | +0.29% | Positive (uptrend accelerating) |
| MA50 Slope | -0.09% | Slightly negative |
| ADX(14) | 13.95 | Weak trend (< 20) |
| DI+ / DI- | 26.38 / 14.38 | Bullish dominance |
| Price vs EMA20 | +2.46% | Above |
| Aroon Up / Down | 100.0 / 24.0 | Uptrend in place |

### Trend Assessment
- **MA Alignment:** EMA20 (297.59) > EMA50 (294.92) > EMA200 (279.97) — classic bullish alignment
- **SuperTrend:** Direction +1 (bullish), trailing at £297.01 — price 2.69% above trail, no recent flips in last 30 rows
- **MA Slopes:** MA20 slope positive at +0.29% (accelerating), MA50 slope slightly negative at -0.09% (still recovering)
- **Trend Strength:** ADX 13.95 — weak trend. This is consistent with LGEN's mean-reverting character identified in the strategy report (avg ADX 21.6)
- **Donchian Position:** Price £304.90 near upper at £307.50 (99.2% of range) — breakout territory
- **Keltner Position:** Price £304.90 vs Keltner upper £306.62 — near upper band
- **Price/MA20 Ratio:** 1.033 — price 3.3% above MA20, moderate premium

### Trend Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| EMA Alignment (bullish order) | +1.0 | 30% | +0.30 |
| SuperTrend Direction (bullish) | +0.5 | 20% | +0.10 |
| MA20 Slope (positive) | +0.5 | 15% | +0.08 |
| ADX Strength (weak trend) | -0.5 | 15% | -0.08 |
| DI+ vs DI- (bullish dominance) | +1.0 | 20% | +0.20 |
| **Trend Score** | | **100%** | **+0.60** (range: -3.0 to +3.0) |

**Trend Verdict:** Bullish structure with clean MA alignment and DI+ dominance, but weak ADX confirms LGEN's mean-reverting nature — trend strength is moderate, not strong.

### Strategy Alignment
Strategy Data → Trend-following entries: LGEN is classified as **mean-reverting**, not trending. Trend-following strategies underperform (trend_momentum lost -12.30% in backtest). Current trend is bullish but the strategy explicitly avoids trend-following on LGEN. Match ❌ for trend-following, ✅ for mean-reversion context (price near upper band = potential mean-reversion target).

---

## 2. Momentum Analysis

**Signal:** BEARISH | **Confidence:** MEDIUM

LGEN.L shows strongly overbought momentum across multiple oscillators. This is the most concerning dimension for new entries, as every mean-reversion strategy entry condition (RSI < 35, CCI < -100) is violated in the opposite direction. However, MACD histogram is positive and rising, suggesting the rally has room to continue briefly.

### Current Indicators

| Indicator | Value | Signal |
|-----------|-------|--------|
| RSI(14) | 65.24 | Approaching overbought (>70) |
| RSI Z-Score(14,20) | 1.53 | Above average |
| RSI Percentile(14,20) | 95.0% | Very high (top 5% historically) |
| MACD Line | 2.79 | Bullish |
| MACD Signal | 1.63 | Cross above confirmed |
| MACD Histogram | 1.17 | Positive, rising |
| ROC(20) | +6.76% | Strong positive momentum |
| Williams %R | -13.13 | Overbought (< -20) |
| CCI(20) | 130.89 | Overbought (> 100) |
| MFI(14) | -113.40 | Data anomaly — skip |
| Stochastic %K / %D | 100.0 / 100.0 | Max overbought |

### Momentum Assessment
- **RSI Context:** RSI at 65.2 with z-score 1.53 and 95th percentile — strongly overbought. This directly conflicts with the mean-reversion entry requirement of RSI < 35 (or < 40 optimized).
- **MACD State:** MACD line (2.79) above signal (1.63) with positive histogram (1.17) — bullish cross intact. Histogram is positive suggesting momentum still accelerating.
- **Oscillator Convergence:** Williams %R (-13.13), CCI (130.9), Stochastic (100/100) — all three flash overbought. RSI is also elevated. Only MACD and ROC are bullish. Strong overbought convergence.
- **Divergence Check:** Price has risen steadily but RSI percentile is at 95% — no negative divergence, just extreme readings suggesting exhaustion risk.

### Momentum Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| RSI Level (approaching overbought) | -1.0 | 30% | -0.30 |
| MACD State (bullish cross) | +0.5 | 25% | +0.13 |
| Williams %R (overbought) | -1.0 | 20% | -0.20 |
| CCI (overbought) | -1.0 | 15% | -0.15 |
| ROC (positive momentum) | +0.5 | 10% | +0.05 |
| **Momentum Score** | | **100%** | **-0.47** (range: -3.0 to +3.0) |

**Momentum Verdict:** Strongly overbought across multiple oscillators — this is the primary reason to HOLD rather than BUY. The mean-reversion entry signal (RSI < 35, CCI < -100) is far from satisfied.

### Strategy Alignment
Strategy Data → Entry RSI < 35 (or RSI < 40 optimized): Current RSI is 65.2 — far above the 35/40 threshold. Entry CCI < -100: Current CCI is 130.9 — far above. The mean-reversion entry conditions are not just unmet; they are violated in the opposite direction. Match ❌ for entry, ⚠️ CAUTION for exit (price at upper band = mean-reversion target).

---

## 3. Return Analysis

**Signal:** POSITIVE | **Confidence:** HIGH

LGEN.L has delivered strong multi-period returns with positive alpha vs the FTSE 100. The 1-month gain of 4.42% and 6-month gain of 19.62% show consistent upward momentum. However, the strategy report notes that mean-reversion strategies underperform buy-and-hold in trending years (2025: 13.87% B&H vs 2.53% strategy; 2026 YTD: 16.20% B&H vs 10.12% top strategy).

### Past Performance

| Period | Return | Assessment |
|--------|--------|------------|
| 1 Month | +4.42% | Solid monthly gain |
| 3 Months | +1.50% | Near flat — consolidation phase |
| 6 Months | +19.62% | Strong semi-annual performance |
| 1 Year | +27.09% | Excellent annual return |

### Risk-Adjusted Metrics

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Alpha(20) | +0.24 | Positive — outperforming benchmark |
| Beta(20) | 0.64 | Low volatility — less volatile than FTSE 100 |
| RS vs FTSE 100 | +2.84 | Outperforming FTSE 100 |

### Forward Return Context

| Forward Period | Mean Return | Std Dev | Assessment |
|---------------|-------------|---------|------------|
| 5 days | ~0.5% | ~2.0% | Slightly positive bias |
| 10 days | ~0.3% | ~3.5% | Near-zero expected return |
| 20 days | ~0.2% | ~5.0% | Low directional expectation |

*Computed from recent_context last 30 rows: mean forward returns show near-zero directional expectations, consistent with mean-reverting behavior.*

### Return Assessment
- **Short-term trend:** 1M +4.42%, 3M +1.50% — recent rally accelerating after consolidation
- **Medium-term trend:** 6M +19.62%, 1Y +27.09% — strong longer-term performance
- **Risk-adjusted:** Alpha +0.24 (outperforming), Beta 0.64 (less volatile) — favorable risk profile
- **Forward expectations:** Near-zero forward returns suggest no strong directional bias — consistent with mean-reversion (price oscillates around mean)

### Return Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| 6M Return (+19.62%) | +1.0 | 25% | +0.25 |
| 1Y Return (+27.09%) | +1.0 | 25% | +0.25 |
| Alpha/Beta (positive alpha, low beta) | +1.0 | 25% | +0.25 |
| Forward Return Context (near-zero) | -0.5 | 25% | -0.13 |
| **Return Score** | | **100%** | **+0.63** (range: -3.0 to +3.0) |

**Return Verdict:** Strong historical returns with favorable risk metrics, but near-zero forward return expectations suggest the current rally may be nearing a mean-reversion point.

### Strategy Alignment
Strategy Data → Mean-reversion style, medium-term holding: Current returns confirm the stock has been in a strong uptrend. The strategy report notes mean-reversion strategies trail buy-and-hold in trending years (2026 YTD: B&H 16.20% vs top strategy 10.12%). Current holders benefit from trend; strategy would exit near BB Upper and wait for mean reversion to re-enter. Match ✅ for exit timing (near upper band = take profits), ❌ for re-entry (need pullback to lower band).

---

## 4. Structure Analysis

**Signal:** CAUTIOUS | **Confidence:** MEDIUM

LGEN.L is trading near its recent structural resistance. Price is very close to the nearest resistance at £309.27 (1.43% away) and well above nearest support at £294.90 (3.28% away). The `ta_trend` label shows -1 (bearish), which conflicts with the price action — this is a notable divergence suggesting structural ambiguity.

### Key Levels

| Level | Value | Distance from Current | Significance |
|-------|-------|----------------------|--------------|
| Resistance (52-week high) | £318.10 | +4.35% | All-time high for period |
| Resistance (Donchian upper) | £307.50 | +0.86% | 20-day breakout level |
| Nearest Resistance | £309.27 | +1.43% | Recent swing high |
| **Current Price** | **£304.90** | — | — |
| Nearest Support | £294.90 | -3.28% | EMA50 / recent support |
| Support (BB Lower) | £283.05 | -7.19% | Mean-reversion entry zone |
| Support (EMA200) | £279.97 | -8.17% | Long-term support |

### Structure Signals

| Signal | Value | Interpretation |
|--------|-------|----------------|
| HH (Higher High) | 0 (last 30 days) | No new higher highs |
| HL (Higher Low) | 0 (last 30 days) | No confirmed higher lows |
| LH (Lower High) | 0 (last 30 days) | No bearish structure |
| LL (Lower Low) | 0 (last 30 days) | No bearish structure |
| BOS (Break of Structure) | 0 (last 30 days) | No breaks |
| CHoCH (Change of Character) | 0 (last 30 days) | No reversals |
| Trend Label | -1 | Bearish (conflicts with price) |

### Structure Assessment
- **Pattern:** Price is consolidating near recent highs with no new HH/HL confirmation. The absence of HH/HL in the last 30 days suggests the uptrend may be losing structural momentum.
- **Key levels:** Price £304.90 is 1.43% from nearest resistance (£309.27) but 3.28% from nearest support (£294.90) — asymmetric risk/reward favoring downside
- **Recent breaks:** No BOS or CHoCH signals — range-bound consolidation near highs
- **Support touches:** 65 total support touches historically — well-established support at £294.90

### Structure Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| Price position (near resistance) | -0.5 | 30% | -0.15 |
| TA Trend label (-1, bearish) | -1.0 | 25% | -0.25 |
| Support proximity (3.28% away) | +0.5 | 25% | +0.13 |
| No HH/HL in recent period | -0.5 | 20% | -0.10 |
| **Structure Score** | | **100%** | **-0.37** (range: -3.0 to +3.0) |

**Structure Verdict:** Price is structurally cautious — near resistance with bearish trend label and no confirmed higher highs. Support is well-established but further away than resistance.

### Strategy Alignment
Strategy Data → Mean-reversion entry requires price at BB Lower (£283.05), which is £21.85 (7.2%) below current price. Current structure near resistance is the **opposite** of a mean-reversion entry zone. Match ❌ for entry, ✅ for exit (price near resistance = ideal mean-reversion exit).

---

## 5. Volatility Analysis

**Signal:** LOW RISK | **Confidence:** HIGH

Volatility is at historically low levels — ATR at the 20th percentile, Bollinger Bands contracting. Low volatility often precedes breakouts. The price position at 91% of BB Upper combined with contracting bands suggests a potential breakout (upward or mean-reversion downward). GARCH volatility is near 1.0, indicating stable to slightly declining volatility.

### Current Indicators

| Indicator | Value | Assessment |
|-----------|-------|------------|
| ATR(14) | 4.64 | Absolute level — moderate |
| ATR Percentile | 20.0% | Low — at 20th percentile |
| BB Width | 8.14% | Moderate — bands normal width |
| %B | 0.91 | Near upper band (0=lower, 1=upper) |
| BB Upper | £307.06 | Resistance level |
| BB Lower | £283.05 | Mean-reversion entry zone |
| HV(20) | 10.03% | Moderate, declining from recent highs |
| Park Volatility | 14.53% | Range-based estimate |
| GARCH Vol | 1.025 | Near 1.0 — stable volatility |
| ATR Stop Distance | 4.57 | Suggested ATR-based stop |

### Volatility Assessment
- **Volatility Level:** ATR at 20th percentile — historically low. The ATR has declined from 6.44 (Sep 18) to 4.64 (Oct 29), showing a clear downward volatility trend.
- **Band Position:** %B at 0.91 — price is very near the BB Upper band. This is the mean-reversion exit signal zone per the strategy.
- **Volatility Trend:** HV(20) at 10.03% — declining from recent peaks (was 11%+ in Sep). GARCH forecast ~1.03 — stable.
- **Breakout Potential:** BB width at 8.14% is moderate but the declining ATR trend suggests potential for increased volatility (breakout) if support breaks.
- **Suggested Stop:** ATR-based stop at £304.90 - 4.57 = £300.33 (below EMA20 at £297.59 — too tight). A 5-day stop below EMA20 at £297.59 (~2.4% downside) is more practical.

### Volatility Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| ATR Percentile (low vol = low risk) | +0.5 | 25% | +0.13 |
| ATR Trend (declining from 6.44 to 4.64) | +1.0 | 25% | +0.25 |
| %B position (near upper band) | -1.0 | 30% | -0.30 |
| GARCH Vol (stable ~1.0) | +1.0 | 20% | +0.20 |
| **Volatility Score** | | **100%** | **+0.28** (range: -3.0 to +3.0) |

**Volatility Verdict:** Low absolute volatility is favorable, but the price at 91% of BB Upper is a mean-reversion exit signal. Volatility is stable but the extreme band position warrants caution.

### Strategy Alignment
Strategy Data → Preferred volatility: Low/stable (GARCH ≤ GARCH.shift(1)). Current GARCH at 1.025 is essentially flat — stable. Low ATR percentile (20%) confirms low vol environment. However, the %B position is the opposite of what the entry conditions require. Match ✅ for volatility regime (stable, low), ❌ for %B position (at upper, not lower).

---

## 6. Volume Analysis

**Signal:** BULLISH | **Confidence:** MEDIUM

Volume confirms the uptrend: OBV is rising (positive slope), CMF has turned positive at 0.195, and price trades well above VWAP. However, volume intensity (z-score -0.48, percentile 15%) is below average — the rally lacks significant volume backing, which is a caution signal.

### Current Indicators

| Indicator | Value | Assessment |
|-----------|-------|------------|
| OBV | 1,707,209,275 | Rising (confirms uptrend) |
| CMF(20) | +0.195 | Buying pressure |
| OFI | +0.379 | Order flow favors buyers |
| VWAP | £293.76 | Price 3.80% above VWAP |
| ADL | -1,244,438,544 | Negative (distribution?) |
| MFI(14) | -113.40 | Data anomaly — skip |
| Volume Z-Score | -0.48 | Below average |
| Volume Percentile | 15.0% | Low intensity |
| EMV(14) | 0.00000044 | Near zero — minimal ease of movement |

### Volume Assessment
- **Buying/Selling Pressure:** CMF +0.195 (buying) + OFI +0.379 (buyers favored) = confirmed buying pressure. However, ADL is negative (-1.24B), which conflicts with OBV and CMF.
- **Volume Trend:** OBV has risen from 1,487M (Oct 1) to 1,707M (Oct 29) — +14.8% OBV increase confirms the price uptrend. OBV slope (7-day): +11.76M, (14-day): +8.20M — both positive.
- **Volume Intensity:** Z-score -0.48, percentile 15% — below-average volume. The rally is happening on lighter volume, which could signal weak conviction.
- **Smart Money:** ADL negative suggests distribution by larger players, conflicting with rising OBV. This divergence warrants attention.
- **Divergence Warning:** Rising OBV with falling volume percentile suggests the rally may be sustained by fewer, larger trades rather than broad participation.

### Volume Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| OBV Trend (rising, confirms price) | +1.0 | 30% | +0.30 |
| CMF + OFI (buying pressure) | +1.0 | 25% | +0.25 |
| Volume Intensity (below average) | -0.5 | 25% | -0.13 |
| ADL vs OBV (divergence) | -0.5 | 20% | -0.10 |
| **Volume Score** | | **100%** | **+0.33** (range: -3.0 to +3.0) |

**Volume Verdict:** OBV trend and buying pressure are bullish, but below-average volume intensity and ADL/OBV divergence suggest the rally lacks broad conviction.

### Strategy Alignment
Strategy Data → Volume requirements: The strategy does not have explicit volume filters, but the GARCH volatility filter (volatility not rising) is met. Rising OBV confirms the price action. However, the low volume percentile suggests the rally may not be broad-based. Match ✅ for volume trend confirmation, ⚠️ for volume intensity (light volume = potential false breakout risk).

---

## 7. Regime Analysis

**Signal:** BULL | **Confidence:** MEDIUM

The HMM model assigns 58.9% probability to State 0 (typically bullish) and 40.9% to State 2 (typically neutral/sideways). State 1 (bearish) has negligible probability at 0.3%. The regime has been oscillating between States 0 and 2 throughout the recent period, with the latest reading at State 0.

### HMM Regime Probabilities

| Regime State | Probability | Interpretation |
|-------------|-------------|----------------|
| State 0 | 58.9% | Bullish (dominant) |
| State 1 | 0.3% | Bearish (negligible) |
| State 2 | 40.9% | Neutral/sideways |

### Regime Assessment
- **Dominant Regime:** State 0 at 58.9% — moderately bullish. The regime flipped from State 2 to State 0 on the most recent data point.
- **Regime Stability:** Regime has oscillated between States 0 and 2 throughout the last 30 days — no extended period in any single state. This indicates a transitional/choppy regime rather than a strong directional trend.
- **GARCH Context:** GARCH vol at 1.025 — stable, not elevated. Volatility is not a risk factor in the current regime.
- **Trend vs Regime Divergence:** Trend indicators show bullish structure but regime oscillation suggests the market is not committed to a single direction. This is consistent with LGEN's mean-reverting character.

### Regime Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| State 0 dominance (58.9%) | +1.0 | 40% | +0.40 |
| Regime stability (oscillating) | -0.5 | 30% | -0.15 |
| GARCH Vol (stable, not elevated) | +1.0 | 30% | +0.30 |
| **Regime Score** | | **100%** | **+0.55** (range: -3.0 to +3.0) |

**Regime Verdict:** Moderately bullish regime with stable volatility. The oscillating nature of the regime (between States 0 and 2) is typical for a mean-reverting stock and favors the mean-reversion strategy over trend-following.

### Strategy Alignment
Strategy Data → Preferred regime: The strategy report notes mean-reversion strategies excel in LGEN's mean-reverting regime. Current State 0 (58.9%) is consistent with a benign environment for mean-reversion trading. Match ✅ for regime alignment.

---

## Signal Synthesis

### Aggregate Score Summary

| # | Dimension | Signal | Score (-3.0 to +3.0) | Weight | Weighted |
|---|-----------|--------|-------------|--------|----------|
| 1 | **Trend** | 🟢 Bullish | +0.60 | 14% | +0.084 |
| 2 | **Momentum** | 🔴 Bearish | -0.47 | 14% | -0.066 |
| 3 | **Return** | 🟢 Positive | +0.63 | 14% | +0.088 |
| 4 | **Structure** | 🟡 Cautious | -0.37 | 14% | -0.052 |
| 5 | **Volatility** | 🟢 Low Risk | +0.28 | 14% | +0.039 |
| 6 | **Volume** | 🟢 Bullish | +0.33 | 14% | +0.046 |
| 7 | **Regime** | 🟢 Bull | +0.55 | 14% | +0.077 |
| | **AGGREGATE** | | | **100%** | **+0.216** |

### Score Interpretation

**Aggregate Score: +0.22 — HOLD**

The aggregate score of +0.22 falls within the neutral band (-0.4 to +0.4), confirming a HOLD signal. Four dimensions are bullish (Trend, Return, Volatility, Volume, Regime — 5 actually), two are cautious/bearish (Momentum, Structure). The negative momentum and structural caution pull the aggregate back from strongly positive to neutral.

### Signal Determination
- **Overall Signal:** HOLD
- **Strength:** Weak (|score| = 0.22 ≤ 0.5)
- **Confidence:** Medium — 5 of 7 dimensions are positive, but 2 (Momentum, Structure) are negative/cautious. No dimension is Low confidence.

### Supporting Indicators (Top 3 per Dimension)

| Dimension | Indicator 1 | Indicator 2 | Indicator 3 |
|-----------|------------|------------|------------|
| Trend | EMA alignment | DI+ > DI- | SuperTrend +1 |
| Momentum | RSI 65.2 (overbought) | CCI 130.9 (overbought) | Stochastic 100/100 |
| Return | 1Y +27.1% | Alpha +0.24 | 6M +19.6% |
| Structure | Near resistance +1.43% | TA trend label -1 | No HH/HL in 30 days |
| Volatility | ATR 20th percentile | %B at 0.91 | GARCH stable |
| Volume | OBV rising | CMF +0.195 | OFI +0.379 |
| Regime | State 0 (58.9%) | GARCH ~1.0 | No bear state |

### Conflicting Indicators
- **Trend vs Structure:** Trend is bullish (MA alignment, SuperTrend +1) but TA trend label is -1 — structural disagreement
- **Momentum vs Return:** Strong historical returns (+27.1% 1Y) but momentum is overbought — returns may be near a peak
- **Volume vs ADL:** OBV and CMF show buying pressure, but ADL is negative — smart money divergence

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | DO NOT ENTER | All mean-reversion entry conditions unmet (RSI 65.2 >> 35, CCI 130.9 >> -100, price at BB Upper not Lower) |
| **Current holders** | HOLD — monitor for exit | Trend and regime support holding, but price near BB Upper (£307.06) is the strategy exit signal. Consider trimming 25-50% if close breaches £307. |
| **Traders** | AVOID new positions | Overbought momentum + near resistance = poor risk/reward for new entries |
| **Value investors** | PATIENCE — wait for pullback | Current valuation is near cyclical highs. Wait for RSI < 35 with price near BB Lower for accumulation. |

- **Entry:** Wait for price to drop to BB Lower (£283.05) with RSI(14) < 35 and CCI(20) < -100. This is the strategy's entry zone — approximately £21.85 (7.2%) below current price.
- **Stop-Loss:** Below EMA20 at £297.59 (2.4% downside from current) for current holders. ATR-based stop at £304.90 - 4.57 = £300.33 is too tight; EMA20 provides better structural support.
- **Target:** Nearest resistance at £309.27 (1.4%) if holding current positions. Full BB Upper at £307.06 is the mean-reversion exit target.
- **Position Sizing:** If entering on pullback to BB Lower, size at 5-10% of portfolio (single stock risk management).
- **Max Holding Period:** Mean-reversion trades typically 5-20 trading days — exit if price reaches BB Upper or 30-day time stop triggers.

### Risk Factors
- **Momentum exhaustion:** RSI 65.2, CCI 130.9, Stochastic 100 — all overbought. A mean-reversion pullback of 5-10% is statistically probable.
- **Regime shift:** If State 2 probability rises above State 0, the bullish regime weakens. Watch for State 1 (bearish) emergence.
- **Volume divergence:** Below-average volume (percentile 15%) with rising price suggests weak conviction. A breakout on low volume may fail.
- **ADL/OBV divergence:** Negative ADL with rising OBV suggests smart money may be distributing while retail participates.

### When This Signal Is Invalidated
- **Close below EMA20 (£297.59):** Signal becomes WAIT — trend may be ending, hold only with tight stop
- **Close below EMA50 (£294.92):** Signal becomes SELL — structural breakdown, protect capital
- **SuperTrend flips to -1:** Signal becomes SELL — trend reversal confirmed

### Key Levels to Watch

| Event | Price Level | Distance | Action Trigger |
|-------|------------|----------|----------------|
| Stop loss trigger | £297.59 | -2.4% | Close below EMA20 |
| Support 1 | £294.90 | -3.3% | Close below EMA50 / support touch |
| Support 2 | £283.05 | -7.2% | BB Lower — mean-reversion entry zone |
| EMA200 | £279.97 | -8.2% | Long-term support |
| Current Price | £304.90 | — | — |
| Resistance 1 | £307.06 | +0.7% | BB Upper — strategy exit trigger |
| Resistance 2 | £309.27 | +1.4% | Nearest structural resistance |
| 52-week high | £318.10 | +4.3% | All-time high for period |

---

## Next Steps

- **Monitor for pullback to BB Lower (~£283):** This is the mean-reversion entry zone. Set price alert at £285 as early warning.
- **Watch MACD histogram for reversal:** If histogram starts declining from 1.17, momentum may be peaking — consider reducing positions.
- **Re-evaluation trigger:** Re-run evaluation if close drops below EMA20 (£297.59) or if RSI falls below 40 (approaching entry zone).
- **Strategy note:** If entering on pullback, use entry rules from the Strategy Reference: BB Lower + RSI < 35 + CCI < -100 + GARCH stable → exit at BB Upper.
- **Long-term note:** LGEN's 8.4% dividend yield provides downside cushion during mean-reversion pullbacks — factor this into holding decisions.
- **Alerts:** Set alerts at support £294.90 (EMA50), entry zone £283.05 (BB Lower), and resistance £307.06 (BB Upper exit).

---

*Report generated: 2026-10-29 | Data point: 2026-10-29 | Data: `data/analysis-data/LGEN.L.csv` (5,054 rows) | Strategy: `data/reports/strategies/LGEN.L/2026-10-29.md`*







