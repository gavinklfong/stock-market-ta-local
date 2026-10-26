# Market Situation Evaluation: National Grid (NG.L)

**Evaluation Date:** 2026-10-26
**Actual Date Used:** 2026-10-26
**Ticker:** NG.L (National Grid)
**Price:** £1,222.50
**Data Range:** 2006-10-26 to 2026-10-26 (5,053 rows)
**Sector:** Utilities
**Strategy Reference:** `data/reports/strategies/NG.L/20261021.md`

---

## Executive Summary

**Signal:** HOLD
**Confidence:** Medium

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🟢 BULLISH | 🟢 High | Strong MA alignment, ADX > 25, DI+ >> DI- |
| **Momentum** | 🟢 BULLISH | 🟡 Medium | RSI 66 rising, MACD bullish with rising histogram |
| **Return** | 🟡 MIXED | 🟡 Medium | +8.5% 1M but -6.0% 6M; positive alpha |
| **Structure** | 🟢 BULLISH | 🟡 Medium | Bullish HH/HL, near Donchian upper breakout |
| **Volatility** | 🟡 NORMAL | 🟡 Medium | Low ATR percentile (25) but price near BB upper |
| **Volume** | 🔴 BEARISH | 🟢 High | Volume at 0th percentile — no participation |
| **Regime** | 🟡 NEUTRAL | 🟢 High | HMM regime 2 (neutral) 88.7%, stable 30 days |
| **Overall** | 🟠 CAUTION | 🟡 Medium | Mixed: bullish structure undermined by low volume and neutral regime |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | £1,222.50 | Near 52-week high of £1,428.50, at 39.8% position in range |
| 52-Week Range | £1,096.50 – £1,428.50 | 39.8% above low, 14.4% below high |
| P/E (TTM) | N/A | Insufficient data for P/E on latest row |
| Dividend Yield | N/A | Insufficient data on latest row |
| Beta (20d) | 0.61 | Low — less volatile than FTSE 100 (defensive utility) |
| RS vs FTSE 100 | 11.35 | Outperforming FTSE 100 |

### Strategy Alignment Summary

| Strategy Element | Current Value | Alignment |
|-----------------|---------------|-----------|
| Close ≤ BB Lower Band (entry condition) | £1,222.50 vs £1,110.89 | ❌ NOT MET |
| RSI(14) < 30 (entry condition) | RSI = 66.1 | ❌ NOT MET |
| Williams %R < -80 (entry condition) | -8.6 | ❌ NOT MET |
| BB Width ≥ 10% (Entry2 filter) | 11.0% | ✅ MET |
| ATR(14) ≥ 15 (Entry2 filter) | 23.14 | ✅ MET |
| **Recommended strategy is BB Mean-Reversion** | Price is far above BB Lower, RSI is high | ❌ ENTRY CONDITIONS NOT MET |

**Strategy Verdict:** The recommended BB Mean-Reversion strategy is not applicable at current levels. NG.L is trending upward (+8.5% in the past month) and is near its Bollinger Band upper. The mean-reversion entry criteria (price below BB Lower + RSI < 30 + Williams %R < -80) are all NOT met. Holding the Golden Cross Trend Following strategy (Strategy 1) entry conditions are largely aligned (EMA20 > EMA50, RSI > 50, MACD > Signal), but SuperTrend trail is above price, and the HMM neutral regime weakens conviction. **No new positions recommended.**

### Signal Summary

**Current Signal: HOLD**

NG.L is in a short-term uptrend (+8.5% in 1 month) with bullish technical structure, but volume is vanishing (0th percentile) and the HMM regime model is firmly neutral (88.7% confidence). The recommended BB Mean-Reversion strategy from the strategy report requires deep oversold conditions that are nowhere near present. The price is near the Donchian upper band and Bollinger upper band — either a breakout or pullback is likely. For existing holders, hold and watch for volume confirmation on the uptrend. For non-holders, wait for either a pullback to support or a high-volume breakout above £1,231.

---

## 1. Trend Analysis

**Signal:** BULLISH | **Confidence:** HIGH

NG.L shows a clear short-term bullish trend with strong trend strength indicators, though the 200-day EMA sits above the 50-day EMA creating a slight long-term tension. The SuperTrend remains positive but the trail level is above the current price, suggesting the trend trail is still lagging the recent rally.

### Current Indicators

| Indicator | Value | Signal |
|-----------|-------|--------|
| EMA20 | £1,186.02 | Price 3.1% above — bullish |
| EMA50 | £1,176.34 | Price 3.9% above — bullish |
| EMA200 | £1,192.94 | Price 2.5% above — bullish |
| SuperTrend Direction | +1 | Bullish |
| SuperTrend Trail | £1,310.84 | Above price (trail lagging) |
| MA20 Slope | 3.39 | Positive — accelerating uptrend |
| MA50 Slope | 0.277 | Positive — stable uptrend |
| ADX(14) | 29.2 | >25 = strong trend |
| DI+ / DI- | 23.06 / 7.23 | Bullish dominance (3.2x) |
| Price vs EMA20 | +3.08% | Above EMA20 |

### Trend Assessment
- **MA Alignment:** EMA20 (£1,186) > EMA50 (£1,176) but EMA50 < EMA200 (£1,193). Short-term bullish, but EMA50 has not yet recovered above EMA200 — partial bullish alignment. All three EMAs are now below price which is positive.
- **SuperTrend:** Direction is +1 (bullish), but the trail (£1,310.84) sits above the current price, meaning the SuperTrend signal is based on older data before the recent sharp rally. The trail will need to catch up.
- **MA Slopes:** MA20 slope = 3.39 (strong positive) and MA50 slope = 0.277 (mild positive). The MA20 is accelerating faster than the MA50, confirming recent momentum.
- **Trend Strength:** ADX = 29.2 (>25 = strong trend), DI+ (23.06) >> DI- (7.23) — strong bullish trend dominance.
- **Donchian Position:** Price (£1,222.50) is very close to Donchian upper (£1,231), just 0.7% away — near breakout territory.
- **Keltner Position:** Price (£1,222.50) is inside the Keltner bands (£1,139–£1,231), 98.6% of the way to the upper band.

### Trend Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| MA Alignment (short-term) | +1.5 | 20% | +0.30 |
| SuperTrend Direction | +1.0 | 15% | +0.15 |
| MA Slopes | +1.5 | 15% | +0.23 |
| ADX/DI Strength | +2.0 | 25% | +0.50 |
| Donchian/Keltner Position | +1.0 | 25% | +0.25 |
| **Trend Score** | | **100%** | **+1.43 / 3.0** |

**Trend Verdict:** Strong bullish trend with ADX > 25 and dominant DI+. The MA alignment is partially bullish (EMA20 > EMA50 but EMA50 < EMA200), and the SuperTrend trail is still catching up after the recent rally. Price is at Donchian upper — either breakout or pullback incoming.

### Strategy Alignment
The Golden Cross Trend Following strategy (Strategy 1) entry conditions are partially met: EMA20 > EMA50 ✅, RSI > 50 ✅, MACD > Signal ✅, SuperTrend +1 ✅. However, EMA50 > EMA200 is NOT met (EMA50 at £1,176 < EMA200 at £1,193). The HMM Regime Adaptive strategy (Strategy 15) requires Bull Probability > 60%, but current p0 = 9.5% — regime is not bull.

---

## 2. Momentum Analysis

**Signal:** BULLISH | **Confidence:** MEDIUM

Momentum indicators are broadly bullish with RSI in the upper-normal range, MACD showing a confirmed bullish cross with a rising histogram, and ROC positive. However, Williams %R and CCI are approaching overbought territory, suggesting the short-term rally may be getting extended.

### Current Indicators

| Indicator | Value | Signal |
|-----------|-------|--------|
| RSI(14) | 66.1 | Upper-normal — not overbought yet |
| RSI Z-Score(14,20) | 1.01 | Above average — bullish |
| RSI Percentile(14,20) | 80% | 80th percentile — approaching extreme |
| MACD Line | 18.81 | Bullish (above signal) |
| MACD Signal | 12.60 | Bullish cross confirmed |
| MACD Histogram | 6.21 | Rising — momentum accelerating |
| ROC(20) | 8.43% | Positive momentum |
| Williams %R | -8.6 | Overbought (> -20) |
| CCI(20) | 109.7 | Slightly overbought (>100) |
| MFI(14) | 54.5 | Normal — no extreme |
| Stochastic K/D | 98.1 / 98.1 | Extremely overbought |

### Momentum Assessment
- **RSI Context:** RSI = 66.1 is in the upper-normal range, not yet overbought (70+). Z-score of 1.01 and 80th percentile confirm this is elevated but not extreme. Watch for RSI > 70 as a warning.
- **MACD State:** MACD line (18.81) well above signal (12.60), histogram (6.21) is positive and rising. This is a strong bullish momentum signal with no bearish divergence.
- **Oscillator Convergence:** Mixed — RSI is bullish but not extreme, MACD is strongly bullish, but Williams %R (-8.6) and CCI (109.7) are overbought. Stochastic at 98 is at extreme levels.
- **Divergence Check:** No divergence detected — price and momentum are moving together. However, the very low volume (see Volume section) means this momentum may not be sustainable.

### Momentum Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| RSI Position | +1.5 | 25% | +0.38 |
| MACD State | +2.0 | 30% | +0.60 |
| Oscillator Convergence | +0.5 | 20% | +0.10 |
| ROC(20) | +1.0 | 15% | +0.15 |
| Stochastic Warning | -0.5 | 10% | -0.05 |
| **Momentum Score** | | **100%** | **+1.18 / 3.0** |

**Momentum Verdict:** Bullish momentum driven by strong MACD and rising histogram, but Stochastic at 98 and Williams %R at -8.6 are overbought. RSI at 66 is not yet extreme but approaching. No divergence detected.

### Strategy Alignment
The Momentum Composite strategy (Strategy 16) entry conditions: RSI > 55 ✅, MACD > Signal ✅, ROC20 > 0 ✅, Williams %R > -50 ✅, CMF > 0 ✅ (CMF = 0.099), EMA20 > EMA50 ✅ — ALL conditions are MET. However, the recommended strategy is BB Mean-Reversion, not momentum-following. The momentum signals are bullish but not aligned with the primary recommended strategy's mean-reversion entry.

---

## 3. Return Analysis

**Signal:** MIXED | **Confidence:** MEDIUM

NG.L shows strong recent performance (+8.5% in 1 month) but the 6-month view is negative (-6.0%). The 1-year return is modestly positive (+6.4%). Risk-adjusted metrics are solid with positive alpha and low beta, indicating NG.L outperforms the FTSE 100 on a risk-adjusted basis while being less volatile.

### Past Performance

| Period | Return | Assessment |
|--------|--------|------------|
| 1 Month | +8.47% | Strong recent momentum — sharp rally from £1,123 |
| 3 Months | +0.37% | Flat overall — the 1-month rally erased 3-month losses |
| 6 Months | -5.96% | Negative medium-term — underlying weakness |
| 1 Year | +6.40% | Modestly positive — defensive utility holding ground |

### Risk-Adjusted Metrics

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Alpha(20) | 0.386 | Positive — outperforming FTSE 100 on risk-adjusted basis |
| Beta(20) | 0.609 | <1 — less volatile than FTSE 100 (defensive utility) |
| RS vs FTSE 100 | 11.35 | Rising — outperforming FTSE 100 |

### Forward Return Context

| Forward Period | Mean Return | Std Dev | Assessment |
|---------------|-------------|---------|------------|
| 5 days | N/A | N/A | NaN — not available for latest row |
| 10 days | N/A | N/A | NaN — not available for latest row |
| 20 days | N/A | N/A | NaN — not available for latest row |

> Note: Forward returns (`ta_return_5d/10d/20d`) are NaN for the latest row as these require future data points for computation. The recent 1-month return of +8.47% suggests continuation bias in the short term, but the 6-month negative return of -5.96% indicates the current rally may be a recovery rather than a new uptrend establishment.

### Return Assessment
- **Short-term trend:** +8.5% in 1 month — strong upward momentum
- **Medium-term trend:** -6.0% in 6 months — still in recovery mode; the 1-month rally has erased the 3-month loss
- **Risk-adjusted:** Positive alpha (0.386) with low beta (0.609) — outperforming FTSE 100 with less volatility. RS vs FTSE 100 at 11.35 indicates strong outperformance.
- **Forward expectations:** The recent rally from £1,123 to £1,222 in ~4 weeks is sharp. Without forward return data, we rely on past performance suggesting continuation bias in the short term.

### Return Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| 1-Month Performance | +1.5 | 30% | +0.45 |
| 6-Month/1-Year Performance | -0.5 | 25% | -0.13 |
| Alpha/Beta/RS | +1.5 | 25% | +0.38 |
| Forward Context | 0.0 | 20% | 0.00 |
| **Return Score** | | **100%** | **+0.70 / 3.0** |

**Return Verdict:** Mixed — strong short-term momentum (+8.5% 1M) is offset by the negative 6-month context (-6.0%). Positive alpha and low beta are encouraging. The rally may be a recovery rather than a new trend establishment.

### Strategy Alignment
The strategy report identifies NG.L as a mean-reversion asset with strong BB Mean-Reversion backtests. The 6-month negative return (-6.0%) is consistent with mean-reversion character — the stock dips significantly then recovers. The current +8.5% rally could be such a recovery. The strategy report does not recommend trend-following for NG.L as it underperforms.

---

## 4. Structure Analysis

**Signal:** BULLISH | **Confidence:** MEDIUM

The structural picture is bullish with higher highs and higher lows forming in the recent uptrend. Price is near the Donchian upper band and very close to the nearest resistance level. No BOS or CHoCH signals are currently active, suggesting the trend is in a holding pattern near a potential breakout point.

### Key Levels

| Level | Value | Distance from Current | Significance |
|-------|-------|----------------------|--------------|
| **Resistance** | £1,260.67 | +3.12% | Nearest resistance — next target |
| **Donchian Upper** | £1,231.00 | +0.70% | Breakout level |
| **Support** | £1,187.19 | -2.89% | Nearest support |
| **SuperTrend Trail** | £1,310.84 | +7.24% | Above price (lagging) |
| **BB Lower** | £1,110.89 | -9.14% | Major support — mean-reversion target |
| **Nearest Support** | £1,187.19 | -2.89% | Closest structural support |

### Structure Signals

| Signal | Value | Interpretation |
|--------|-------|----------------|
| HH (Higher High) | 0 | No HH signal on latest row |
| HL (Higher Low) | 0 | No HL signal on latest row |
| LH (Lower High) | 0 | No LH signal |
| LL (Lower Low) | 0 | No LL signal |
| BOS (Break of Structure) | 0 | No BOS signal |
| CHoCH (Change of Character) | 0 | No CHoCH signal |
| Trend Label | 1 | Bullish trend |
| Swing High | £1,158.50 | Recent swing high (index 5025) |
| Swing Low | £1,104.50 | Recent swing low (index 5033) |
| Support Touches | 86 | Well-established support level |
| Breakout Strength | 0 | Not yet broken out |

### Structure Assessment
- **Pattern:** The `ta_trend = 1` indicates a bullish trend label. Recent price action from £1,123 (Sep 29) to £1,222 (Oct 26) shows higher highs and higher lows — a classic uptrend pattern.
- **Key levels:** Price (£1,222.50) is sandwiched between nearest support (£1,187.19, -2.9%) and nearest resistance (£1,260.67, +3.1%). Very close to Donchian upper (£1,231, +0.7%).
- **Recent breaks:** No BOS or CHoCH signals active. The price has not yet broken above the Donchian upper — a breakout above £1,231 would trigger a BOS signal.
- **Swing analysis:** Recent swing low at £1,104.50 (index 5033, ~Oct 15) has been held firmly. The swing high at £1,158.50 was broken, confirming bullish structure. The current high of £1,222.50 is the highest in ~4 weeks.

### Structure Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| Trend Label (Bullish) | +1.5 | 25% | +0.38 |
| Support Level (Held Firmly) | +1.5 | 25% | +0.38 |
| Near Resistance/Donchian Upper | +0.5 | 25% | +0.13 |
| No BOS/CHoCH Active | 0.0 | 25% | 0.00 |
| **Structure Score** | | **100%** | **+0.88 / 3.0** |

**Structure Verdict:** Bullish structure with price holding above support and trending toward resistance. The lack of BOS signals means we're at a decision point — a breakout above £1,231 would confirm bullish continuation, while rejection at resistance would signal a pullback.

### Strategy Alignment
The Market Structure Trend strategy (Strategy 11) requires HH=1, HL=1, Trend=1, BOS=1. Currently: Trend=1 ✅, but HH=0, HL=0, BOS=0 ❌. The BOS Breakout strategy (Strategy 12) also NOT triggered — BOS=0, price not yet above resistance. The Donchian Breakout strategy (Strategy 4) requires Close > Donchian Upper — price is 0.7% away but NOT yet above £1,231. **No structural entry signals active.**

---

## 5. Volatility Analysis

**Signal:** NORMAL | **Confidence:** MEDIUM

Volatility is at a low percentile (25th), suggesting subdued volatility. The Bollinger Band width is 11.0% (adequate), and price is at 86.2% of the band height — near the upper band. This combination of low ATR percentile but high %B suggests the market has compressed and could be building energy for a breakout or reversal.

### Current Indicators

| Indicator | Value | Assessment |
|-----------|-------|------------|
| ATR(14) | 23.14 | Absolute level — moderate |
| ATR Percentile | 25% | Low — volatility below historical average |
| BB Width | 11.0% | Moderate — adequate for mean-reversion |
| %B | 0.862 | Near upper band (0=lower, 1=upper) |
| BB Upper | £1,240.41 | Resistance level — +1.5% above price |
| BB Middle | £1,175.65 | 20-day SMA — support at -3.8% |
| BB Lower | £1,110.89 | Major support — -9.1% below price |
| HV(20) | 16.73% | Moderate historical volatility |
| Park Volatility | 19.58% | Range-based estimate — consistent with HV |
| GARCH Vol | 1.249 | Forecast — moderate |
| ATR Stop Distance | 5.68 | Suggested stop = £5.68 (0.46%) |

### Volatility Assessment
- **Volatility Level:** ATR percentile at 25% is LOW — volatility is below historical average. This is favorable for trend continuation but unfavorable for mean-reversion entries.
- **Band Position:** Price (£1,222.50) is at 86.2% of the Bollinger Band range — near the upper band (£1,240.41). This is close to resistance within the band.
- **Volatility Trend:** HV(20) = 16.73% is moderate. GARCH forecast of 1.249 suggests moderate future volatility. ATR at 23.14 is not expanding — no breakout energy yet.
- **Breakout Potential:** BB Width of 11.0% is adequate (Entry2 filter requires ≥10%). Low ATR percentile could mean compression building toward a breakout.
- **Suggested Stop:** ATR-based stop distance of £5.68 (0.46%) is very tight. A 2×ATR stop would be £11.36 (0.93%). The nearest support at £1,187.19 (-2.89%) is a more practical stop level.

### Volatility Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| ATR Percentile (Low = compressing) | +1.0 | 25% | +0.25 |
| BB Width (Adequate) | +1.0 | 25% | +0.25 |
| %B Position (Near upper) | -0.5 | 25% | -0.13 |
| GARCH Vol (Moderate) | +0.5 | 25% | +0.13 |
| **Volatility Score** | | **100%** | **+0.50 / 3.0** |

**Volatility Verdict:** Normal volatility with low ATR percentile suggesting compression. Price near BB upper is a caution signal — either breakout or pullback likely. The 11% BB width is adequate but not wide enough for high-quality mean-reversion setups (Entry2 filter prefers wider).

### Strategy Alignment
The BB Mean-Reversion strategy (Strategy 6) works best with wide BB Width (≥10%) and high ATR (≥15) — both Entry2 filters are MET. However, the strategy requires price at the LOWER band, not the upper. The Volatility Expansion strategy (Strategy 14) requires ATR rising and HV rising — ATR is not clearly rising at low percentile. **Current volatility is not favorable for any entry in the recommended strategy.**

---

## 6. Volume Analysis

**Signal:** BEARISH | **Confidence:** HIGH

Volume is the most concerning dimension in this evaluation. Volume is at the 0th percentile (z-score = -1.43), meaning the latest session had the lowest volume in the lookback period. Despite this, OBV is rising and CMF just turned positive — but without volume confirmation, the recent rally lacks conviction.

### Current Indicators

| Indicator | Value | Assessment |
|-----------|-------|------------|
| OBV | 2.03B | Rising — confirms uptrend |
| CMF(20) | 0.099 | Just turned positive — mild buying pressure |
| OFI | -0.162 | Negative — order flow favors sellers |
| VWAP | £1,175.30 | Price well above VWAP (+4.0%) — bullish |
| ADL | 493.7M | Accumulation pressure |
| MFI(14) | 54.5 | Normal — no volume extreme |
| Volume Z-Score | -1.43 | Below average — significantly |
| Volume Percentile | 0% | Lowest volume in lookback — no participation |
| EMV(14) | 0.0000103 | Positive — easy movement |
| OBV Slope(14) | 4.36M | Rising — accumulation trend |
| OBV Slope(7) | 1.78M | Rising — recent accumulation |
| Volume Osc | -587,686 | Negative volume deviation |

### Volume Assessment
- **Buying/Selling Pressure:** CMF just turned positive (0.099) after being negative for most of the recent rally. OFI is still negative (-0.162), suggesting the latest session had net selling pressure despite the price rise. This is a caution signal.
- **Volume Trend:** OBV is rising (both 14-day and 7-day slopes are positive) — this confirms the uptrend at an accumulation level. However, the rising OBV with extremely low volume is a weak signal — it takes less volume to push OBV up when no one is trading.
- **Volume Intensity:** Volume z-score of -1.43 and 0th percentile mean the latest session had virtually no participation. This is the most bearish signal in the entire evaluation — price rose to £1,222.50 on the lowest volume in the period.
- **Smart Money:** ADL is at 493.7M — accumulation territory. MFI at 54.5 is neutral. The combination suggests some accumulation but not broad participation.
- **Divergence Warning:** **PRICE-VOLUME DIVERGENCE DETECTED.** Price has risen +8.5% in 1 month but volume is at the 0th percentile. The rally is being driven by thin trading, not broad participation. This is a classic warning sign of a potential pullback.

### Volume Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| OBV Rising (Accumulation) | +1.0 | 25% | +0.25 |
| CMF Just Positive | +0.5 | 20% | +0.10 |
| Volume Z-Score/Percentile (0th) | -2.0 | 35% | -0.70 |
| OFI Negative | -1.0 | 20% | -0.20 |
| **Volume Score** | | **100%** | **-0.55 / 3.0** |

**Volume Verdict:** Bearish — volume is at the 0th percentile with price at a 4-week high. The rally is being driven by thin trading with no broad participation. OBV rising is the only positive signal, but it is weak in context. **This is the weakest dimension and the primary reason for the HOLD signal.**

### Strategy Alignment
The Institutional Accumulation strategy (Strategy 8) requires CMF > 0 ✅, OBV Rising ✅, ADL Rising ✅, MFI > 50 ✅, Close > EMA50 ✅ — ALL conditions are met. However, this strategy is not the recommended one (BB Mean-Reversion is). The Order Flow strategy (Strategy 10) requires OFI > 0.3 — current OFI = -0.162 ❌. The Momentum Composite strategy (Strategy 16) requires CMF > 0 ✅. Volume confirmation is marginal at best.

---

## 7. Regime Analysis

**Signal:** NEUTRAL | **Confidence:** HIGH

The HMM regime model is firmly in State 2 (neutral) with 88.7% probability — the highest confidence reading in the entire evaluation. The regime has not changed in 30 consecutive days, indicating extreme stability. While the neutral regime doesn't preclude trading, it means regime-based strategies that require Bull probability > 60% cannot be activated.

### HMM Regime Probabilities

| Regime State | Probability | Interpretation |
|-------------|-------------|----------------|
| State 0 (Bull) | 9.5% | Low — not dominant |
| State 1 (Bear) | 1.8% | Very low — negligible bear risk |
| State 2 (Neutral) | 88.7% | Dominant — firm sideways/consolidation |

### Regime Assessment
- **Dominant Regime:** State 2 (neutral) at 88.7% — the model is extremely confident the market is in a neutral/sideways regime. State 0 (bull) at 9.5% is low, and State 1 (bear) at 1.8% is negligible.
- **Regime Stability:** Zero regime changes in the last 30 days. State 2 probability peaked at 98.7% on Oct 5–6 (during the low-point of the recent dip) and has since moderated to 88.7% as the rally gained traction. The regime remains firmly neutral.
- **GARCH Context:** GARCH volatility at 1.249 is moderate. Within the neutral regime, moderate volatility is typical — neither the high volatility of bear regimes nor the stable low volatility of bull regimes.
- **Trend vs Regime Divergence:** **Notable divergence detected.** Technical trend indicators (EMA alignment, ADX, SuperTrend) are all bullish, but the HMM regime model says neutral. This divergence is the key reason for caution — the trend may be a short-term oscillation within a broader neutral regime, not the start of a new bull phase.

### Regime Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| Neutral Dominance (88.7%) | -0.5 | 40% | -0.20 |
| Regime Stability (30 days no change) | +1.0 | 30% | +0.30 |
| Trend vs Regime Divergence | -0.5 | 30% | -0.15 |
| **Regime Score** | | **100%** | **-0.05 / 3.0** |

**Regime Verdict:** Neutral regime with high stability. The divergence between bullish technical trends and neutral HMM regime is the key risk — the uptrend may not be sustainable outside a confirmed bull regime.

### Strategy Alignment
The HMM Regime Adaptive strategy (Strategy 15) requires Bull Probability > 60% for the Bull regime (1.0% risk), or at least neutral conditions for reduced-risk trading. Current p0 = 9.5% is far below the 60% threshold. **Regime-based entry is NOT available.** The neutral regime means any trend-following entry carries higher risk of failure if the regime shifts.

---

## Signal Synthesis

### Aggregate Score Summary

| # | Dimension | Signal | Score (/3.0) | Weight | Weighted |
|---|-----------|--------|-------------|--------|----------|
| 1 | **Trend** | 🟢 BULLISH | +1.43 | 20% | +0.29 |
| 2 | **Momentum** | 🟢 BULLISH | +1.18 | 15% | +0.18 |
| 3 | **Return** | 🟡 MIXED | +0.70 | 10% | +0.07 |
| 4 | **Structure** | 🟢 BULLISH | +0.88 | 15% | +0.13 |
| 5 | **Volatility** | 🟡 NORMAL | +0.50 | 10% | +0.05 |
| 6 | **Volume** | 🔴 BEARISH | -0.55 | 15% | -0.08 |
| 7 | **Regime** | 🟡 NEUTRAL | -0.05 | 15% | -0.01 |
| | **AGGREGATE** | | | **100%** | **+0.63** |

### Score Interpretation

| Range | Signal | Interpretation |
|-------|--------|---------------|
| +2.0 to +3.0 | Strong Bullish | All dimensions aligned — strong buy signal |
| +0.5 to +1.9 | Mildly Bullish | Trend favors longs but monitor for reversals |
| **-0.5 to +0.4** | **Neutral / Wait** | **Mixed signals — do not initiate new positions** |
| -0.5 to -1.9 | Mildly Bearish | Caution warranted, consider reducing exposure |
| -2.0 to -3.0 | Strong Bearish | All dimensions negative — avoid longs |

**Aggregate Score: +0.63 — Mildly Bullish**

The aggregate score is mildly bullish (+0.63) — the top of the "mildly bullish" range. However, this score is heavily influenced by the Trend (+1.43) and Momentum (+1.18) dimensions, which are both strong. The Volume dimension (-0.55) and Regime dimension (-0.05) provide meaningful headwinds. The neutral HMM regime and vanishing volume create enough uncertainty that despite the mildly bullish aggregate score, a HOLD signal is warranted.

### Signal Determination
- **Overall Signal:** HOLD
- **Strength:** Normal
- **Confidence:** Medium

The HOLD signal reflects:
1. **Bullish technicals** (Trend, Momentum, Structure) vs **bearish volume** and **neutral regime**
2. The recommended BB Mean-Reversion strategy entry conditions are NOT met — no valid entry exists
3. The trend-following strategies have partially aligned conditions but are weakened by the neutral regime
4. Price is at a decision point near Donchian upper — breakout or pullback equally possible

### Supporting Indicators (Top 3 per Dimension)

| Dimension | Indicator 1 | Indicator 2 | Indicator 3 |
|-----------|------------|------------|------------|
| Trend | ADX = 29.2 | DI+ >> DI- | MA20 slope = 3.39 |
| Momentum | MACD histogram = +6.21 | RSI = 66.1 | ROC(20) = 8.4% |
| Return | 1M return = +8.5% | Alpha(20) = 0.386 | RS vs FTSE 100 = 11.35 |
| Structure | Trend label = 1 (bullish) | Support held at £1,104 | Near Donchian upper |
| Volatility | ATR percentile = 25% | BB Width = 11.0% | %B = 0.862 |
| Volume | Volume percentile = 0% | OBV rising | CMF just positive |
| Regime | HMM p2 = 88.7% | 30 days stability | Trend/Regime divergence |

### Conflicting Indicators
- **Volume vs Price:** Price rose +8.5% in 1 month but volume is at the 0th percentile. Classic thin-trading rally that may reverse.
- **Trend vs Regime:** ADX, EMA alignment, and SuperTrend all say bullish, but HMM regime is firmly neutral (88.7%). The trend may be a short-term oscillation within a broader neutral regime.
- **Williams %R vs RSI:** Williams %R (-8.6) is overbought, but RSI (66.1) is not yet extreme. If RSI follows Williams %R above 70, expect a pullback.
- **OBV vs Volume:** OBV is rising (bullish) but volume is at 0th percentile (bearish). The OBV rise may be an artifact of low liquidity rather than genuine accumulation.

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | DO NOT ENTER | No strategy entry conditions met; volume too low to confirm rally |
| **Current holders** | HOLD | Bullish structure intact; no exit signals triggered |
| **Traders** | AVOID | Thin volume + neutral regime = poor risk/reward for new positions |
| **Value investors** | PATIENCE | Wait for pullback to BB Lower or CMF > 0 with volume confirmation |

- **Entry (if considered):** Wait for one of two scenarios:
  1. **Breakout entry:** Close > £1,231 (Donchian upper) WITH volume z-score > 0 and CMF > 0. This would confirm genuine breakout participation.
  2. **Pullback entry:** Price retraces to £1,187 (nearest support) or £1,176 (EMA50) with RSI 45-55, CMF > 0, and volume normalization. This would offer better risk/reward.
- **Stop-Loss:** £1,187 (nearest support, -2.9%) or 2×ATR below entry (£1,222.50 - £11.36 = £1,211)
- **Target:** £1,260.67 (nearest resistance, +3.1%) or £1,240.41 (BB upper, +1.5%)
- **Position Sizing:** 0.5% portfolio risk (conservative, per BB Mean-Reversion strategy sizing)
- **Max Holding Period:** 45 days (per Strategy 3 time-stop recommendation)

### Risk Factors
- **Volume collapse:** If volume remains at 0th percentile, the rally could reverse sharply on any negative catalyst
- **Regime shift to bear:** If HMM p1 (bear probability) rises above 20%, the current uptrend may be a dead-cat bounce within a bear regime
- **RSI overbought:** If RSI crosses 70, expect mean-reversion pullback (especially given the mean-reversion nature of NG.L identified in the strategy report)
- **Donchian rejection:** Failure to break above £1,231 could trigger a pullback to £1,187 support

### When This Signal Is Invalidated
- **Close > £1,231 with volume z-score > 0:** → Signal upgrades to BUY (confirmed breakout with participation)
- **Close < £1,187 (nearest support):** → Signal degrades to SELL (support broken, trend damaged)
- **RSI > 70:** → Signal becomes WAIT (overbought, expect pullback)
- **HMM p1 rises above 20%:** → Signal degrades to SELL (bear regime emerging)
- **SuperTrend flips to -1:** → Signal degrades to SELL (trend reversal confirmed)

### Key Levels to Watch

| Event | Price Level | Distance | Action Trigger |
|-------|------------|----------|----------------|
| Stop loss trigger | £1,187.19 | -2.89% | Close below support → SELL |
| Support 1 | £1,175.65 (EMA50/BB Mid) | -3.84% | Hold = bullish continuation |
| Support 2 | £1,110.89 (BB Lower) | -9.14% | Major support — mean-reversion entry zone |
| Entry zone (breakout) | £1,231–£1,240 | +0.7–1.5% | Breakout above Donchian + volume → BUY |
| Resistance 1 | £1,240.41 (BB Upper) | +1.50% | Rejection here → pullback likely |
| Resistance 2 | £1,260.67 | +3.12% | Breakout target if support breaks |

---

## Next Steps

- **Monitor volume:** The 0th percentile volume is the most concerning signal. Watch for volume z-score to move above -0.5 — this would confirm genuine market participation.
- **Watch £1,231 (Donchian upper):** A close above this level with volume would confirm breakout. Rejection with continued low volume would signal pullback.
- **Re-run evaluation if:** Close drops below £1,187 (support broken) or RSI crosses above 70 (overbought).
- **If entering:** Use the Golden Cross Trend Following strategy entry rules (EMA20 > EMA50, RSI > 55, MACD > Signal, CMF > 0, OFI > 0, BOS confirmed) — but wait for volume confirmation first.
- **Consider mean-reversion:** The recommended BB Mean-Reversion strategy will become actionable when price pulls back to the BB Lower band with RSI < 30 and Williams %R < -80. This is more likely to happen than the breakout scenario, given NG.L's mean-reversion character.
- **Set alerts:** Alert at £1,231 (breakout), £1,187 (support break), and £1,110 (BB Lower mean-reversion zone).

---

*Report generated: 2026-10-26 | Data point: 2026-10-26 | Data: data/analysis-data/NG.L.csv (5,053 rows) | Strategy: data/reports/strategies/NG.L/20261021.md*