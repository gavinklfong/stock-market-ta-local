# Market Situation Evaluation: National Grid (NG.L)

**Evaluation Date:** 2026-10-27
**Actual Date Used:** 2026-10-27
**Ticker:** NG.L (National Grid)
**Price:** 1221.0p
**Data Range:** 2006-10-27 to 2026-10-27 (5,053 rows)
**Sector:** Utilities
**Strategy Reference:** `data/reports/strategies/NG.L/20261027.md`

---

## Executive Summary

**Signal:** HOLD / WAIT
**Confidence:** Medium

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🟢 BULLISH | 🟡 Medium | EMA alignment + ADX 30.3 + DI+ dominance |
| **Momentum** | 🟢 BULLISH | 🟡 Medium | MACD bullish cross, RSI 65.4, ROC +8.7% |
| **Return** | 🟢 POSITIVE | 🟡 Medium | +8.29% 1M, positive alpha, strong RS |
| **Structure** | 🟡 CAUTIOUS | 🟡 Medium | Range-bound between swing high/low |
| **Volatility** | 🔴 HIGH RISK | 🟡 Medium | Overbought BB position, tight compression |
| **Volume** | 🟢 BULLISH | 🟢 High | OBV slope strongly positive (+4.0M) |
| **Regime** | 🟢 BULL | 🟢 High | HMM state 0 at 96.4%, stable |
| **Overall** | 🟡 HOLD / WAIT | 🟡 Medium | Bullish backdrop, but strategy entry NOT MET |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | 1221.0p | Near 52-week high (1231.0 Donchian upper) |
| 52-Week Range | 1124.0 – 1231.0 | At 99.1% of Donchian high — breakout zone |
| P/E (TTM) | N/A | No P/E data available |
| Dividend Yield | N/A | No dividend data available |
| Beta (20d) | 0.59 | Low volatility vs FTSE 100 |
| RS vs FTSE 100 | 11.43 | Outperforming FTSE 100 significantly |

### Strategy Alignment Summary

| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| Close ≤ ta_bband_lower (1117.67) | 1221.0 — well above | ❌ NOT MET |
| ta_rsi14 < 30 | 65.4 — moderately bullish | ❌ NOT MET |
| ta_williams_r < -80 | -11.6 — near overbought | ❌ NOT MET |
| Price near upper BB (1243.43) | At 82% of band | ⚠️ CAUTION (overbought) |
| HMM Regime = Bull (State 0) | 96.4% State 0 | ✅ CONFIRMED |

**Strategy Verdict:** All three bb_meanrev entry conditions are NOT MET. The stock is near its upper Bollinger Band with RSI at 65.4 and Williams %R at -11.6 — the exact opposite of the oversold conditions the strategy requires. This is the wrong environment for mean-reversion entries.

### Signal Summary

**Current Signal: HOLD / WAIT**

The broader market backdrop is bullish — HMM regime is strongly bull (96.4%), trend indicators confirm uptrend, volume shows accumulation, and the stock is up +8.29% over the past month. However, the recommended bb_meanrev strategy requires oversold entry conditions (price below lower BB, RSI < 30, Williams %R < -80) that are **not present**. Entering a mean-reversion trade at the top of the range would be dangerous. Holders should stay put; non-holders should wait for a pullback to the lower Bollinger Band.

---

## 1. Trend Analysis

**Signal:** BULLISH | **Confidence:** MEDIUM

The trend picture is broadly bullish but with one contradictory signal. Price is trading above all three key EMAs, the ADX confirms moderate trend strength, and directional indicators strongly favor bulls. However, the SuperTrend direction reads -1, which contradicts the rest of the trend signal suite. This is likely a lagging artifact from the wide SuperTrend trail (550.30p) which is unusually far below price.

### Current Indicators

| Indicator | Value | Signal |
|-----------|-------|--------|
| EMA20 | 1189.35 | Price 2.66% above — bullish |
| EMA50 | 1178.09 | Price 3.64% above — bullish |
| EMA200 | 1193.22 | Price 2.33% above — bullish |
| SuperTrend Direction | -1 | Bearish flag (contradictory) |
| SuperTrend Trail | 550.30 | Far below price (unusual) |
| MA20 Slope | +3.54 | Positive — uptrend accelerating |
| MA50 Slope | +0.36 | Positive — gentle uptrend |
| ADX(14) | 30.25 | Moderate-strong trend |
| DI+ / DI- | 21.69 / 8.36 | DI+ dominates — bullish |
| Aroon Up / Down | 96 / 20 | Strong uptrend |
| Price vs EMA20 | +2.66% | Above |
| Price vs EMA200 | +2.33% | Above |
| Donchian Upper | 1231.0 | Price at 99.2% — breakout zone |
| Donchian Lower | 1124.0 | Distance: 8.6% below high |
| Keltner Upper | 1232.59 | Price at 98.8% — near upper edge |
| Keltner Lower | 1144.01 | Distance: 6.8% below |

### Trend Assessment
- **MA Alignment:** EMA20 (1189) > EMA50 (1178) < EMA200 (1193). EMA200 slightly above EMA50 creates a mild bearish crossover pattern, but price is above all three MAs — overall **mildly bullish with caution**.
- **SuperTrend:** Direction -1 is contradictory. The trail at 550.30p is 54.9% below price, which is unusually wide. This may indicate stale SuperTrend state. Ignore as outlier; other indicators are more reliable.
- **MA Slopes:** MA20 slope (+3.54) is strong and positive. MA50 slope (+0.36) is weak but positive. The large gap between the two slopes suggests the uptrend is **accelerating**.
- **Trend Strength:** ADX at 30.3 (>25) confirms **moderate-strong trend**. DI+ (21.7) far exceeds DI- (8.4) — clear bullish dominance.
- **Donchian Position:** Price at 1221 is 99.2% of Donchian upper (1231) — at the **breakout zone**. A break above 1231 would signal a new uptrend leg.
- **Keltner Position:** Price at 1221 is 98.8% of Keltner upper (1232.6) — near the upper edge, suggesting potential resistance.

### Trend Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| EMA Alignment | +0.5 | 25% | +0.125 |
| SuperTrend | -0.5 | 15% | -0.075 |
| MA Slopes | +1.0 | 20% | +0.200 |
| ADX/DI Strength | +1.0 | 20% | +0.200 |
| Donchian/Keltner | +0.5 | 20% | +0.100 |
| **Trend Score** | | **100%** | **+0.550** (range: -3.0 to +3.0) |

**Trend Verdict:** Moderately bullish with accelerating slope and strong DI+ dominance. The SuperTrend -1 reading is an outlier — the weight of evidence favors bulls. However, price is at Donchian upper, suggesting potential resistance.

### Strategy Alignment

The bb_meanrev strategy does not require specific trend conditions — it works in any regime. However, the current bullish trend (price at Donchian upper, +8.29% 1M return) is **not conducive** to mean-reversion entries, which require price to pull back. Strategy Data → Trend: Current bullish with price near resistance → ❌ NOT favorable for mean-reversion entry.

---

## 2. Momentum Analysis

**Signal:** BULLISH | **Confidence:** MEDIUM

Momentum indicators are broadly bullish. MACD is in a clear bullish cross, RSI is at a healthy 65.4 (not yet overbought), and the rate of change is strong at +8.73%. However, several oscillators are approaching overbought territory — Williams %R at -11.6 and CCI at 92.7 suggest the momentum is running hot. For a mean-reversion strategy, this is problematic: entries require oversold conditions (RSI < 30, Williams %R < -80) that are nowhere in sight.

### Current Indicators

| Indicator | Value | Signal |
|-----------|-------|--------|
| RSI(14) | 65.37 | Moderately bullish (not overbought) |
| RSI Z-Score(14,20) | 0.863 | Above average — bullish |
| RSI Percentile(14,20) | 70.0% | 70th percentile — moderately high |
| MACD Line | 19.16 | Above signal — bullish |
| MACD Signal | 13.91 | Bullish cross active |
| MACD Histogram | 5.25 | Positive and rising |
| ROC(20) | +8.73% | Strong positive momentum |
| Williams %R | -11.56 | Overbought zone (near -20) |
| CCI(20) | 92.69 | Near overbought (100 threshold) |
| MFI(14) | 54.70 | Neutral (40-60 range) |

### Momentum Assessment
- **RSI Context:** RSI at 65.4 with z-score of +0.86 and 70th percentile — moderately bullish. Not yet in overbought territory (>70), but approaching. For mean-reversion, we need RSI < 30.
- **MACD State:** Clear bullish cross — MACD line (19.16) > signal (13.91). Histogram is positive at 5.25. The MACD has been rising for ~30 days (based on recent_context: from ~8 to ~19), showing sustained momentum.
- **Oscillator Convergence:** RSI and MACD agree on bullish. Williams %R and CCI are approaching overbought extremes. MFI is neutral, suggesting volume-weighted momentum is less extreme than price-based indicators.
- **Divergence Check:** No price-MACD or price-RSI divergence — price and momentum are aligned, both bullish.

### Momentum Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| RSI + Z-Score | +0.5 | 30% | +0.150 |
| MACD Cross | +1.0 | 25% | +0.250 |
| ROC(20) | +1.0 | 20% | +0.200 |
| Williams %R / CCI | -0.5 | 15% | -0.075 |
| MFI / Overall | +0.0 | 10% | +0.000 |
| **Momentum Score** | | **100%** | **+0.525** (range: -3.0 to +3.0) |

**Momentum Verdict:** Moderately bullish. MACD and RSI confirm uptrend; oscillator extremes (Williams %R, CCI) suggest momentum may be getting stretched. For mean-reversion strategy, all entry conditions are NOT MET.

### Strategy Alignment

The bb_meanrev strategy requires RSI < 30 and Williams %R < -80 as entry conditions. Current RSI at 65.4 and Williams %R at -11.6 are the exact opposite. Strategy Data → Momentum: RSI 65.4 (need <30) → ❌ NOT MET; Williams %R -11.6 (need <-80) → ❌ NOT MET. The current environment is bullish, not oversold.

---

## 3. Return Analysis

**Signal:** POSITIVE | **Confidence:** MEDIUM

Recent returns are strongly positive: +8.29% in the past month, +2.35% over 3 months, and +6.04% over 1 year. Alpha is positive (0.41) and beta is low (0.59), meaning NG.L has been outperforming the FTSE 100 with less volatility. However, these strong returns are precisely why mean-reversion entries are not warranted — the strategy needs oversold pullbacks, not extended runs. Forward return context from the last 30 days shows overwhelmingly positive forward returns (80-100% positive), consistent with sustained momentum.

### Past Performance

| Period | Return | Assessment |
|--------|--------|------------|
| 1 Month | +8.29% | Strong — uptrend in progress |
| 3 Months | +2.35% | Moderate positive |
| 6 Months | -4.59% | Mildly negative — prior pullback |
| 1 Year | +6.04% | Modest positive |

### Risk-Adjusted Metrics

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Alpha(20) | +0.41 | Positive — outperforming benchmark |
| Beta(20) | 0.59 | Low volatility — less sensitive to FTSE 100 swings |
| RS vs FTSE 100 | 11.43 | Strong outperformance vs FTSE 100 |

### Forward Return Context (Last 30 Days)

| Forward Period | Mean Return | Std Dev | P(Return > 0) | Assessment |
|---------------|-------------|---------|---------------|------------|
| 5 days | +0.012% | 2.0% | 80.0% | Slightly positive — high consistency |
| 10 days | +0.031% | 2.5% | 90.0% | Positive — very consistent |
| 20 days | +0.062% | 2.1% | 100.0% | Strongly positive — all positive |

*Based on last 30 rows of historical forward returns. The high % positive (80-100%) reflects the current sustained uptrend.*

### Return Assessment
- **Short-term trend:** Strong positive — +8.29% in 1 month. The stock has recovered well from its 6-month low.
- **Medium-term trend:** Mildly positive — +6.04% over 1 year. The 6-month negative return (-4.59%) was followed by a strong recovery, typical of NG.L's mean-reverting behavior.
- **Risk-adjusted:** Positive alpha (0.41) and low beta (0.59) indicate NG.L is generating excess returns with less volatility than the market. This is excellent for risk-adjusted performance.
- **Forward expectations:** Forward returns are slightly positive on average with high consistency (80-100% positive in the last 30 days). This suggests the uptrend may continue, but for mean-reversion strategy, this means no oversold entry opportunity.

### Return Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| 1M / 3M Performance | +1.0 | 30% | +0.300 |
| 6M / 1Y Context | +0.0 | 20% | +0.000 |
| Alpha / Beta / RS | +1.0 | 30% | +0.300 |
| Forward Return Consistency | +0.5 | 20% | +0.100 |
| **Return Score** | | **100%** | **+0.700** (range: -3.0 to +3.0) |

**Return Verdict:** Strong recent returns with excellent risk-adjusted metrics. However, the positive returns are precisely what makes mean-reversion entries inappropriate — the stock needs to pull back to oversold levels.

### Strategy Alignment

The bb_meanrev strategy is a short-term mean-reversion approach that profits from pullbacks. Current +8.29% 1M return and +0.41 alpha mean the stock is extended, not oversold. Strategy Data → Return: Current +8.29% 1M return (need pullback to BB lower) → ❌ NOT MET. The strategy's short-term holding period is appropriate for NG.L, but the entry timing is wrong.

---

## 4. Structure Analysis

**Signal:** CAUTIOUS | **Confidence:** MEDIUM

NG.L is currently range-bound between its 20-day swing high (1158.5) and swing low (1104.5), but the price has broken above this range and is now at the Donchian upper (1231.0). The absence of higher highs (HH) and higher lows (HL) in the recent window suggests the trend structure is not firmly established. There are no BOS or CHoCH signals in the recent data. The nearest support is at 1187.19 (below the EMA20/50 cluster) and nearest resistance at 1260.67 (beyond current price).

### Key Levels

| Level | Value | Distance from Current | Significance |
|-------|-------|----------------------|--------------|
| **Resistance (Donchian Upper)** | 1231.0 | +0.8% | 20-day breakout level |
| Nearest Resistance | 1260.67 | +3.2% | Next structural resistance |
| **Support (EMA20/50 cluster)** | 1178-1189 | -3.4% to -3.5% | Dynamic support zone |
| Nearest Support | 1187.19 | -2.8% | Static support level |
| Swing Low | 1104.5 | -9.5% | Major support |
| SuperTrend Trail | 550.30 | -54.9% | Extreme distance (unusual) |
| BB Lower | 1117.67 | -8.5% | Mean-reversion entry zone |

### Structure Signals

| Signal | Value | Interpretation |
|--------|-------|----------------|
| HH (Higher High) | 0.0 (recent) | No higher highs — range-bound |
| HL (Higher Low) | 0.0 (recent) | No higher lows — no bullish structure |
| LH (Lower High) | 0.0 (recent) | No lower highs |
| LL (Lower Low) | 0.0 (recent) | No lower lows |
| BOS (Break of Structure) | 0.0 | No recent breaks |
| CHoCH (Change of Character) | 0.0 | No reversals |
| Trend Label | +1.0 | Bullish (but weakly) |
| Swing High | 1158.5 | Price above — breakout |
| Swing Low | 1104.5 | Distance: 10.5% |
| Support Touches | N/A | Insufficient data |

### Structure Assessment
- **Pattern:** Range-bound with breakout potential. Price has moved above the recent swing high (1158.5) and is testing the Donchian upper (1231.0). No clear HH/HL structure in the recent window.
- **Key levels:** Price is between nearest support (1187.19) and nearest resistance (1260.67). The Donchian upper at 1231 is the immediate level to watch — a break above could signal a new leg up.
- **Recent breaks:** No BOS or CHoCH signals in the recent data. The structure is neutral.
- **Support quality:** The EMA20/50 cluster at 1178-1189 provides dynamic support. The BB lower at 1117.67 would be the mean-reversion entry zone.

### Structure Score

| Factor | Score | Weight | Weight | Weighted |
|--------|-------|--------|--------|----------|
| Price Position in Range | +0.5 | 25% | | +0.125 |
| Support/Resistance Quality | +0.5 | 25% | | +0.125 |
| HH/HL / BOS Signals | -0.5 | 25% | | -0.125 |
| Breakout Potential | +0.5 | 25% | | +0.125 |
| **Structure Score** | | **100%** | | **+0.250** (range: -3.0 to +3.0) |

**Structure Verdict:** Cautiously neutral. Price is range-bound but testing breakout levels. No clear structural trend signals, but the Donchian upper breakout could signal continuation.

### Strategy Alignment

The bb_meanrev strategy benefits from moderate-to-high volatility (wider BB = larger profit potential) and requires price at the lower BB. Current %B = 0.822 (near upper) with BB width at 0.107% (extreme compression) is the worst possible combination for mean-reversion. Strategy Data → Volatility: Current %B 0.822 (need <0.0 at lower BB) → ❌ NOT MET; BB width 0.11% (compression = breakout imminent, not mean-reversion) → ❌ NOT MET.

---

## 6. Volume Analysis

**Signal:** BULLISH | **Confidence:** HIGH

Volume indicators are strongly bullish. The OBV slope is positive over both 7-day (+1.56M) and 14-day (+4.02M) windows, indicating sustained accumulation. CMF is positive at 0.093, showing mild buying pressure. The Order Flow Imbalance is positive (0.158), confirming buyer aggression. Price is trading above VWAP (1179.67), which is a bullish intraday signal. However, volume z-score is slightly negative (-0.66), meaning today's volume is below average — not a concern, but not a confirmation of strength.

### Current Indicators

| Indicator | Value | Assessment |
|-----------|-------|------------|
| OBV | 2,020.37M | Rising — accumulation |
| OBV Slope (14d) | +4.02M | Strong accumulation |
| OBV Slope (7d) | +1.56M | Sustained buying |
| CMF(20) | 0.093 | Mild buying pressure |
| OFI | 0.158 | Buyer-favorable order flow |
| VWAP | 1179.67 | Price above VWAP (1221) — bullish |
| ADL | 500.09M | Positive — accumulation |
| MFI(14) | 54.70 | Neutral (volume-weighted RSI) |
| Volume Z-Score | -0.66 | Below average volume |
| Volume Percentile | 35.0% | Low volume intensity |
| EMV(14) | 0.000011 | Slightly positive ease of movement |

### Volume Assessment
- **Buying/Selling Pressure:** CMF at 0.093 is mildly positive, and OFI at 0.158 confirms buyer-side order flow imbalance. Combined, these indicate **mild but consistent buying pressure**.
- **Volume Trend:** OBV slope is strongly positive (+4.02M over 14 days, +1.56M over 7 days), confirming the price uptrend. OBV has been consistently rising, which is a **bullish confirmation** of the price trend.
- **Volume Intensity:** Volume z-score of -0.66 and percentile at 35% mean today's volume is below average. This is not a concern for the uptrend (rising OBV confirms accumulation) but suggests the move is not accompanied by heavy institutional volume.
- **Smart Money:** ADL at 500.09M is positive, and the rising OBV slope suggests smart money accumulation. The consistent OBV slope (both 7d and 14d positive) indicates this is not a one-day spike but sustained accumulation.
- **Divergence Warning:** No price-volume divergence. Both price and OBV are rising, confirming the uptrend.

### Volume Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| OBV Slope (14d) | +1.0 | 30% | +0.300 |
| OBV Slope (7d) | +1.0 | 20% | +0.200 |
| CMF + OFI | +0.5 | 25% | +0.125 |
| Price vs VWAP | +0.5 | 15% | +0.075 |
| Volume Intensity | +0.0 | 10% | +0.000 |
| **Volume Score** | | **100%** | **+0.700** (range: -3.0 to +3.0) |

**Volume Verdict:** Bullish. Strong OBV accumulation confirms the uptrend. Low volume intensity is not a concern given the consistent OBV trend.

### Strategy Alignment

The bb_meanrev strategy does not have explicit volume filters, but rising OBV during a price uptrend means smart money is supporting the higher prices. This is neutral for mean-reversion — if volume continues to accumulate, any pullback may be shallow. Strategy Data → Volume: OBV slope +4.02M (accumulation) → ⚠️ CONFIRMED but not helpful for entry timing. Volume confirms the uptrend but does not signal an oversold condition.

---

## 5. Volatility Analysis

**Signal:** HIGH RISK | **Confidence:** MEDIUM

Volatility conditions are concerning for new entries. The Bollinger Band width is extremely tight at 0.11% — one of the most compressed readings possible. Price is at 82% of the band (near the upper), which means the stock is extended relative to its recent volatility range. ATR percentile is only at the 20th percentile, indicating low absolute volatility. However, this compression suggests a breakout is imminent — either direction. For mean-reversion strategy, tight bands with price near the upper is the worst possible entry environment.

### Current Indicators

| Indicator | Value | Assessment |
|-----------|-------|------------|
| ATR(14) | 22.59 | Moderate absolute level |
| ATR Percentile | 20.0% | Low — volatility is compressed |
| BB Width | 0.107% | Extremely tight — compression |
| %B | 0.822 | Near upper band (1.0 = upper band) |
| BB Upper | 1243.43 | Immediate resistance |
| BB Lower | 1117.67 | Entry zone for mean-reversion |
| BB Middle (SMA20) | 1180.55 | Mean-reversion target |
| HV(20) | 16.59% | Moderate — falling from prior highs |
| Park Volatility | 19.27% | Range-based estimate |
| GARCH Vol | 1.204 | Forecast slightly elevated |
| GARCH Sq | 1.450 | Variance forecast |
| ATR Stop Distance | 5.55 | Suggested stop: 5.55p below entry |
| Normalized ATR | 1.85% | Low relative to price |

### Volatility Assessment
- **Volatility Level:** ATR at the 20th percentile means volatility is in the bottom fifth of its historical range. This is a compression environment.
- **Band Position:** Price at %B = 0.822 means it's near the upper Bollinger Band (1243.43). The distance from the band is only 1.8% (22.43p). This is an overbought position within the band.
- **Volatility Trend:** Historical volatility at 16.59% is moderate and appears to be falling (consistent with BB width contraction). GARCH forecast (1.204) suggests volatility may rise slightly.
- **Breakout Potential:** BB width at 0.107% is extremely tight. This is a classic volatility squeeze — a breakout is likely imminent. The direction is uncertain: mean-reversion would profit from a breakdown back to the middle band (1180.55), while trend-following would profit from a break above the upper band (1243.43).
- **Suggested Stop:** ATR-based stop distance is 5.55p. For a mean-reversion entry at BB lower (1117.67), the stop would be at ~1112.12.

### Volatility Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| BB Position (%B) | -1.0 | 30% | -0.300 |
| BB Width (Compression) | -0.5 | 25% | -0.125 |
| ATR Percentile | -0.5 | 20% | -0.100 |
| GARCH Forecast | +0.0 | 15% | +0.000 |
| HV Trend | -0.5 | 10% | -0.050 |
| **Volatility Score** | | **100%** | **-0.575** (range: -3.0 to +3.0) |

**Volatility Verdict:** High risk for new entries. Price is overextended within an extremely compressed volatility environment. The volatility squeeze suggests an impending breakout, but the direction is uncertain. Mean-reversion entries at current levels would be dangerous.

### Strategy Alignment

The bb_meanrev strategy benefits from moderate-to-high volatility (wider BB = larger profit potential) and requires price at the lower BB. Current %B = 0.822 (near upper) with BB width at 0.107% (extreme compression) is the worst possible combination for mean-reversion. Strategy Data → Volatility: Current %B 0.822 (need <0.0 at lower BB) → ❌ NOT MET; BB width 0.11% (compression = breakout imminent, not mean-reversion) → ❌ NOT MET.

---

## 7. Regime Analysis

**Signal:** BULL | **Confidence:** HIGH

The Hidden Markov Model shows overwhelming confidence in the bull regime. State 0 (bull) has a 96.4% probability, while State 1 (bear) is at only 1.2% and State 2 (neutral) at 2.4%. The regime has been stable in State 0 for the entire 30-day observation window — there have been zero regime changes. GARCH volatility is moderate (1.204), and the trend label is +1.0, confirming the bull regime aligns with the technical trend.

### HMM Regime Probabilities

| Regime State | Probability | Interpretation |
|-------------|-------------|----------------|
| State 0 (Bull) | 96.4% | Dominant bull regime |
| State 1 (Bear) | 1.2% | Negligible |
| State 2 (Neutral) | 2.4% | Negligible |

### Regime Assessment
- **Dominant Regime:** State 0 (bull) at 96.4% — this is an extremely strong bull signal. The HMM model is very confident in the current regime.
- **Regime Stability:** The regime has been in State 0 for the entire 30-day observation window (all 30 recent_context entries show HMM state 0). This is the most stable regime reading possible.
- **GARCH Context:** GARCH volatility at 1.204 is moderate, and GARCH squared (variance) at 1.450 is not extreme. Volatility is contained within the bull regime.
- **Trend vs Regime Alignment:** The trend label is +1.0 (bullish), and the HMM confirms State 0 (bull). There is **no divergence** between trend indicators and the regime model — both agree on bullish.

### Regime Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| HMM State 0 Probability | +1.0 | 50% | +0.500 |
| Regime Stability | +1.0 | 30% | +0.300 |
| GARCH Vol Context | +0.0 | 20% | +0.000 |
| **Regime Score** | | **100%** | **+0.800** (range: -3.0 to +3.0) |

**Regime Verdict:** Strong bull regime with 96.4% HMM confidence and zero regime changes in 30 days. This is the most stable and confident regime reading possible. The bull regime is supportive of holding positions but does not directly help mean-reversion entries.

### Strategy Alignment

The bb_meanrev strategy works in any regime but tends to perform better in neutral/sideways environments where mean-reversion is more frequent. A strong bull regime (State 0 at 96.4%) is less ideal for mean-reversion because prices tend to trend upward rather than oscillate. Strategy Data → Regime: Current State 0 at 96.4% (bull regime, less mean-reversion) → ⚠️ CAUTION. The bull regime supports holding but reduces the frequency of mean-reversion signals.

---

## Signal Synthesis

### Aggregate Score Summary

| # | Dimension | Signal | Score (-3.0 to +3.0) | Weight | Weighted |
|---|-----------|--------|-------------|--------|----------|
| 1 | **Trend** | 🟢 BULLISH | +0.550 | 15% | +0.083 |
| 2 | **Momentum** | 🟢 BULLISH | +0.525 | 15% | +0.079 |
| 3 | **Return** | 🟢 POSITIVE | +0.700 | 15% | +0.105 |
| 4 | **Structure** | 🟡 CAUTIOUS | +0.250 | 10% | +0.025 |
| 5 | **Volatility** | 🔴 HIGH RISK | -0.575 | 15% | -0.086 |
| 6 | **Volume** | 🟢 BULLISH | +0.700 | 10% | +0.070 |
| 7 | **Regime** | 🟢 BULL | +0.800 | 20% | +0.160 |
| | **AGGREGATE** | | | **100%** | **+0.436** |

### Score Interpretation

| Range | Signal | Interpretation |
|-------|--------|---------------|
| +2.0 to +3.0 | Strong Bullish | All dimensions aligned — strong buy signal |
| +0.5 to +1.9 | Mildly Bullish | Trend favors longs but monitor for reversals |
| **-0.4 to +0.4** | **Neutral / Wait** | **Mixed signals — do not initiate new positions** |
| -1.9 to -0.5 | Mildly Bearish | Caution warranted, consider reducing exposure |
| -3.0 to -2.0 | Strong Bearish | All dimensions negative — avoid longs |

**Aggregate Score: +0.436 — HOLD / WAIT**

The aggregate score of +0.436 falls in the "Neutral / Wait" zone. While 5 out of 7 dimensions are bullish (Trend, Momentum, Return, Volume, Regime), the negative Volatility score (-0.575) and cautious Structure (+0.250) pull the aggregate below the buy threshold (+0.5). This is precisely the right environment to **hold existing positions** but **not initiate new ones**.

### Signal Determination
- **Overall Signal:** HOLD / WAIT
- **Strength:** Normal (0.5 > |score| = 0.436 ≤ 2.0)
- **Confidence:** Medium — 3 dimensions rated Medium, 2 rated High, 2 rated Medium. No dimension rated Low, but the signal depends on nuanced interpretation of mixed signals.

### Supporting Indicators (Top 3 per Dimension)

| Dimension | Indicator 1 | Indicator 2 | Indicator 3 |
|-----------|------------|------------|------------|
| Trend | DI+ 21.7 > DI- 8.4 | MA20 slope +3.54 | ADX 30.3 (strong trend) |
| Momentum | MACD 19.16 > 13.91 | ROC +8.73% | RSI 65.4, z-score +0.86 |
| Return | +8.29% 1M | Alpha +0.41 | RS vs FTSE 100 +11.43 |
| Structure | Donchian upper 1231 | Support at 1187 | Trend label +1.0 |
| Volatility | %B 0.822 (overbought) | BB width 0.11% (compression) | ATR percentile 20% |
| Volume | OBV slope +4.02M | CMF 0.093 | Price > VWAP |
| Regime | HMM State 0 96.4% | 30-day stable | Trend label +1.0 |

### Conflicting Indicators
- **Trend vs Volatility:** Trend indicators are bullish (EMA alignment, ADX 30.3) while volatility indicators warn of overbought conditions (%B 0.822, BB compression). Price is extended within a compressed range.
- **Momentum vs Strategy Entry:** Momentum is bullish (MACD cross, RSI 65.4) but the bb_meanrev strategy requires oversold momentum (RSI < 30, Williams %R < -80). These are diametrically opposed.
- **Structure vs Trend:** Price is at Donchian upper (breakout zone) suggesting potential upside, but no HH/HL/BOS signals confirm structural strength. The breakout may be false.

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | DO NOT ENTER | All bb_meanrev entry conditions NOT MET. Price is at the top of the range with no oversold signal. Wait for pullback to BB lower (1117.67). |
| **Current holders** | HOLD | Strong regime (96.4% bull) and bullish trend support holding. Consider trailing stop at EMA20 (1189) to protect gains. |
| **Traders** | AVOID NEW TRADES | Volatility squeeze suggests breakout imminent but direction uncertain. Wait for confirmation. |
| **Value investors** | HOLD / ACCUMULATE ON DIP | NG.L is a stable utility with low beta (0.59). Accumulate on pullbacks to EMA50 (1178) or BB lower (1117). |

- **Entry:** Wait for price to pull back to **BB lower (1117.67)** AND RSI < 30 AND Williams %R < -80. This would be a ~8.5% pullback from current levels.
- **Stop-Loss:** For mean-reversion entries at BB lower (1117.67), stop at **1112.12** (ATR-based, ~5.55p below). For current holders, trail stop at **EMA20 (1189)**.
- **Target:** For mean-reversion entries, target **BB middle (1180.55)** — the 20-day SMA. This is the mean-reversion target.
- **Position Sizing:** If entering on pullback, use 1-2% risk per position (stop distance ~5.5p).

### Risk Factors
- **Regime shift to bear:** If HMM prob_1 (bear) rises above 10%, the bull regime could be ending. Currently at 1.2%.
- **Volume drying up:** Volume z-score is -0.66 (below average). If volume continues to decline, the uptrend may lose steam.
- **BB compression breakout:** BB width at 0.11% is extremely tight. A breakout above 1243 (BB upper) would be bullish; a breakdown below 1117 (BB lower) would trigger the mean-reversion entry.

### When This Signal Is Invalidated
- **Close below EMA20 (1189)** → Signal changes to **CAUTIOUS** — monitor for pullback to entry zone
- **RSI drops below 30** → Signal changes to **BUY (bb_meanrev entry)** — oversold condition met
- **SuperTrend flips to +1** → Signal changes to **STRONG HOLD** — confirms uptrend acceleration
- **HMM prob_1 rises above 20%** → Signal changes to **SELL** — regime shift to bear

### Key Levels to Watch

| Event | Price Level | Distance | Action Trigger |
|-------|------------|----------|----------------|
| Stop loss trigger | 1189.00 | -2.7% | Trail stop for holders |
| Support 1 | 1180.55 | -3.3% | EMA20 / BB middle — first pullback target |
| Support 2 | 1178.09 | -3.5% | EMA50 — deeper pullback support |
| Entry zone | 1100-1118 | -8.5% to -9.2% | bb_meanrev entry: price ≤ 1117.67 + RSI < 30 |
| Resistance 1 | 1231.00 | +0.8% | Donchian upper — breakout level |
| Resistance 2 | 1260.67 | +3.2% | Next structural resistance |

---

## Next Steps

- **Monitor for pullback:** Watch for price to drop to BB lower (1117.67) with RSI < 30 — this would trigger the bb_meanrev entry signal.
- **Set alerts at key levels:** Alert at 1189 (EMA20) for holders to consider trimming; alert at 1117.67 for mean-reversion entry; alert at 1231 (Donchian upper) for breakout confirmation.
- **Re-evaluation trigger:** Re-run evaluation if close drops below EMA20 (1189) or if RSI drops below 40 (signaling early pullback).
- **Strategy note:** If entering on pullback, use the three-condition entry from the bb_meanrev strategy: Close ≤ BB lower AND RSI < 30 AND Williams %R < -80. Exit at BB middle (1180.55).
- **Long-term note:** NG.L is a stable utility with low beta (0.59). Consider as a long-term hold for income/dividend purposes, regardless of short-term technical signals.
- **Alerts:** Set alerts at support 1189 (EMA20) and resistance 1231 (Donchian upper).

---

*Report generated: 2026-10-27 | Data point: 2026-10-27 | Data: `data/analysis-data/NG.L.csv` (5,053 rows) | Strategy: `data/reports/strategies/NG.L/20261027.md`*
