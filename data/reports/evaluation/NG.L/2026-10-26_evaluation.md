# Market Situation Evaluation: National Grid (NG.L)

**Evaluation Date:** 2026-10-26
**Actual Date Used:** 2026-10-26
**Ticker:** NG.L (National Grid)
**Price:** 1222.5
**Data Range:** 2006-10-26 to 2026-10-26 (5053 rows)
**Sector:** Utilities
**Strategy Reference:** `data/reports/strategies/NG.L/20261021.md`

---

## Executive Summary

**Signal:** BUY
**Confidence:** Medium

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🟢 BULLISH | 🟢 High | EMA20>EMA50>EMA200 alignment, SuperTrend +1, strong DI+/DI- ratio |
| **Momentum** | 🟢 BULLISH | 🟡 Medium | MACD bullish cross with rising histogram, RSI approaching overbought |
| **Return** | 🟡 MIXED | 🟡 Medium | Strong 1M (+8.5%) but negative 6M (-6.0%); positive alpha |
| **Structure** | 🟢 BULLISH | 🟡 Medium | Price above swing high (1158.5), nearest support at 1187 |
| **Volatility** | 🔴 BEARISH | 🟡 Medium | Price at 86% of BB upper band — overbought position |
| **Volume** | 🟡 MIXED | 🟡 Medium | Rising OBV confirms uptrend but volume below average (-1.43 z-score) |
| **Regime** | 🟡 NEUTRAL | 🟢 High | HMM State 2 at 88.7% — neutral/sideways regime |
| **Overall** | 🟢 BUY | 🟡 Medium | 5 bullish, 1 bearish, 1 neutral |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | 1222.5 | Near 52-week high of 1428.5 (85.6% of high) |
| 52-Week Range | 1096.5 – 1428.5 | At 85.6% of high, 11.5% below peak |
| P/E (TTM) | N/A | Data unavailable |
| Dividend Yield | N/A | Data unavailable |
| Beta (20d) | 0.61 | Less volatile than FTSE 100 |
| RS vs FTSE 100 | 11.35 | Outperforming FTSE 100 |

### Strategy Alignment Summary

The strategy report was optimized for NG.L (National Grid) with a focus on mean-reversion strategies at Bollinger Band extremes, as well as trend-following approaches. The strategies are evaluated below for relevance to the current market conditions.

| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| EMA20 > EMA50 > EMA200 (Golden Cross) | ✅ 1186 > 1176 > 1193 — partially | ⚠️ EMA50 < EMA200 breaks golden cross |
| SuperTrend Direction = +1 | ✅ +1 (bullish) | ✅ MET |
| RSI > 55 | ✅ 66.1 | ✅ MET |
| MACD > Signal | ✅ 18.81 > 12.60 | ✅ MET |
| CMF > 0 | ✅ 0.099 | ✅ MET |
| OFI > 0 | ❌ -0.162 | ❌ NOT MET |
| BOS = 1 | ❌ 0 (no break of structure) | ❌ NOT MET |
| Bull Regime Probability > 60% | ❌ 9.5% (State 0) | ❌ NOT MET |

**Strategy Verdict:** Most recommended production strategy entry conditions are NOT MET. Current conditions are bullish for trend-following approaches but do not match the mean-reversion entry criteria (price is near highs, not at Bollinger lower band). The Golden Cross and Momentum Composite strategies are more aligned with the current trend.

### Signal Summary

**Current Signal: BUY**

National Grid exhibits strong bullish trend characteristics across five of seven dimensions. The stock is in an uptrend with price above key moving averages, confirmed by SuperTrend, MACD, and rising OBV. However, momentum is approaching overbought levels (RSI 66.1, Williams %R -8.6), volume is below average (suggesting limited participation), and the HMM regime model indicates a neutral/sideways regime (88.7% probability). For non-holders, a pullback to the EMA20 (~1186) would offer a better risk-reward entry. Current holders can maintain positions with a trailing stop below EMA50.

---

## 1. Trend Analysis

**Signal:** BULLISH | **Confidence:** HIGH

National Grid is in a well-defined uptrend with all major moving averages aligned and SuperTrend confirming bullish direction. The ADX of 29.2 indicates a moderately strong trend, and the DI+ to DI- ratio is decisively bullish at 3.2:1. The price is trading near the Donchian upper band, suggesting breakout potential.

### Current Indicators

| Indicator | Value | Signal |
|-----------|-------|--------|
| EMA20 | 1186.02 | Price 3.08% above — bullish |
| EMA50 | 1176.34 | Price 3.92% above — bullish |
| EMA200 | 1192.94 | Price 2.48% above — bullish |
| SuperTrend Direction | +1 | Bullish |
| SuperTrend Trail | 1310.84 | Price 7.1% below — not yet triggered |
| MA20 Slope | +3.39 | Positive — accelerating uptrend |
| MA50 Slope | +0.28 | Positive — steady uptrend |
| ADX(14) | 29.17 | Strong trend (>25) |
| DI+ / DI- | 23.06 / 7.23 | Bullish dominance (3.2:1 ratio) |
| Price vs EMA20 | +3.08% | Above — bullish |

### Trend Assessment
- **MA Alignment:** EMA20 > EMA50 but EMA200 > EMA50 (1193 > 1176). Partial golden cross — 20/50 bullish alignment but 200-day MA still above 50-day, suggesting longer-term consolidation.
- **SuperTrend:** Direction +1 (bullish). No recent flips in the last 30 rows — stable bullish signal. Trail at 1310.84 provides wide stop buffer.
- **MA Slopes:** MA20 slope +3.39 (strong acceleration), MA50 slope +0.28 (gentle slope) — short-term trend stronger than medium-term.
- **Trend Strength:** ADX 29.2 (>25) = strong trend. DI+ (23.1) >> DI- (7.2) confirms directional bias toward bulls.
- **Donchian Position:** Price (1222.5) near Donchian upper (1231.0) = breakout attempt. Only 0.7% below upper bound.
- **Keltner Position:** Price (1222.5) near Keltner upper (1230.8), slightly below — approaching overbought territory.

### Trend Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| MA Alignment (EMA20>EMA50) | +1.0 | 30% | +0.30 |
| SuperTrend Direction | +1.0 | 25% | +0.25 |
| MA Slopes (acceleration) | +0.5 | 15% | +0.08 |
| ADX/DI Strength | +1.0 | 20% | +0.20 |
| Donchian/Keltner Position | +0.5 | 10% | +0.05 |
| **Trend Score** | | **100%** | **+0.88** (+2.64) |

**Trend Verdict:** Strong bullish trend with clear MA alignment and momentum. The only caveat is EMA200 still sitting above EMA50, suggesting the longer-term downtrend (6-month -6.0% performance) has not fully reversed.

### Strategy Alignment
Strategy Data → SuperTrend = +1: Current +1 → Match ✅. Strategy Data → EMA20 > EMA50: Current 1186 > 1176 → Match ✅. Strategy Data → MA20 Slope > 0: Current +3.39 → Match ✅. The Golden Cross entry condition is partially met (EMA20>EMA50 but EMA200 is above EMA50). SuperTrend confirms bullish direction.

---

## 2. Momentum Analysis

**Signal:** BULLISH | **Confidence:** MEDIUM

Momentum is clearly bullish but showing signs of approaching overbought extremes. MACD is in a strong bullish configuration with a rising histogram, while RSI at 66.1 is in the bullish zone but approaching the 70 overbought threshold. Multiple oscillators confirm positive momentum, though Williams %R and CCI suggest the stock may be due for a short-term consolidation.

### Current Indicators

| Indicator | Value | Signal |
|-----------|-------|--------|
| RSI(14) | 66.1 | Bullish zone (50–70), approaching overbought |
| RSI Z-Score(14,20) | +1.01 | Above average — bullish |
| RSI Percentile(14,20) | 80.0% | Top 20% of 20-day range |
| MACD Line | +18.81 | Bullish |
| MACD Signal | +12.60 | MACD above signal — bullish cross confirmed |
| MACD Histogram | +6.21 | Rising — momentum accelerating |
| ROC(20) | +8.43% | Positive momentum |
| Williams %R | -8.63 | Near overbought (>-20 would be overbought) |
| CCI(20) | +109.69 | Slightly overbought (>100) |
| MFI(14) | 54.49 | Neutral — volume-weighted RSI in mid-range |

### Momentum Assessment
- **RSI Context:** At 66.1 with z-score +1.01 and 80th percentile, RSI is firmly in bullish territory but elevated. Not yet overbought (>70), but room for consolidation is limited.
- **MACD State:** Strong bullish configuration — line well above signal (18.81 vs 12.60). Histogram at +6.21 is positive and rising, confirming accelerating upward momentum.
- **Oscillator Convergence:** RSI (66.1), ROC (+8.4%), and MACD histogram (+6.21) all agree — bullish. Williams %R (-8.63) and CCI (+109.7) suggest overbought conditions. MFI (54.5) is neutral, suggesting volume hasn't fully participated.
- **Divergence Check:** No price-momentum divergence. All momentum indicators move in the same direction as price.

### Momentum Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| MACD Configuration | +1.0 | 30% | +0.30 |
| RSI Level & Z-Score | +0.5 | 25% | +0.13 |
| ROC Positive Momentum | +1.0 | 20% | +0.20 |
| Oscillator Convergence (CCI, WR, MFI) | +0.0 | 15% | +0.00 |
| Histogram Direction (rising) | +1.0 | 10% | +0.10 |
| **Momentum Score** | | **100%** | **+0.60** (+1.80) |

**Momentum Verdict:** Clearly bullish momentum confirmed by MACD and ROC, but overbought signals from Williams %R and CCI suggest near-term consolidation is likely. No divergence — momentum still supports the uptrend.

### Strategy Alignment
Strategy Data → RSI > 55: Current 66.1 → Match ✅. Strategy Data → MACD > Signal: Current 18.81 > 12.60 → Match ✅. Strategy Data → ROC20 > 0: Current +8.43% → Match ✅. Strategy Data → Williams %R > -50: Current -8.6 → Match ✅. Strategy Data → CMF > 0: Current 0.099 → Match ✅. Strategy Data → BOS = 1: Current 0 → ❌ NOT MET. 5 out of 6 momentum/trend conditions are met.

---

---

## 3. Return Analysis

**Signal:** MIXED | **Confidence:** MEDIUM

Short-term returns are strong (+8.5% in 1 month) but the 6-month return is negative (-6.0%), reflecting a V-shaped recovery from lows near 1100. The 1-year return is modestly positive at +6.4%. Alpha is slightly positive, indicating the stock has been outperforming the FTSE 100 benchmark on a risk-adjusted basis. Beta of 0.61 means the stock is less volatile than the broader market.

### Past Performance

| Period | Return | Assessment |
|--------|--------|------------|
| 1 Month | +8.47% | Strong recent rally |
| 3 Months | +0.37% | Flat — recent rally offset prior weakness |
| 6 Months | -5.96% | Negative — significant correction from highs |
| 1 Year | +6.40% | Modestly positive |

### Risk-Adjusted Metrics

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Alpha(20) | +0.386 | Slightly outperforming benchmark |
| Beta(20) | 0.61 | Less volatile than FTSE 100 (defensive stock) |
| RS vs FTSE 100 | 11.35 | Strongly outperforming FTSE 100 |

### Forward Return Context

*Computed from `recent_context` (last 30 rows):*

| Forward Period | Mean Return | Std Dev | Assessment |
|---------------|-------------|---------|------------|
| 5 days | +1.12% | 1.85% | Positive bias, moderate dispersion |
| 10 days | +1.87% | 3.12% | Positive continuation likely |
| 20 days | +3.24% | 5.41% | Moderate upside, wider variance |

*Computation: Iterated `recent_context` array — collected all `ta_return_5d`, `ta_return_10d`, `ta_return_20d` values. Mean = sum/count, Std = sqrt(mean((x - mean)^2)).*

### Return Assessment
- **Short-term trend:** 1M (+8.5%) strongly positive; 3M (+0.4%) flat — the rally is recent and accelerating.
- **Medium-term trend:** 6M (-6.0%) negative, 1Y (+6.4%) positive — V-shaped recovery from September lows near 1100 to current 1222.5.
- **Risk-adjusted:** Positive alpha (+0.386) and strong relative strength (11.35) confirm outperformance vs FTSE 100 despite low beta (0.61).
- **Forward expectations:** Positive mean forward returns across all periods suggest continuation is more likely than reversal.

### Return Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| Short-term momentum (1M return) | +1.0 | 30% | +0.30 |
| Medium-term recovery (3M/6M) | 0.0 | 25% | +0.00 |
| Alpha/Beta profile | +0.5 | 25% | +0.13 |
| RS vs FTSE 100 | +1.0 | 20% | +0.20 |
| **Return Score** | | **100%** | **+0.40** (+1.20) |

**Return Verdict:** Mixed — strong recent momentum but offset by 6-month weakness. Risk-adjusted metrics (alpha, RS) are solidly positive.

### Strategy Alignment
Strategy Data → Preferred holding period: The optimized strategies assume short-term mean-reversion trades (45–120 days). Current 1M return of +8.5% reflects momentum. For a trend-following approach (Golden Cross, Momentum Composite), the positive forward returns support continued holding.

---

## 4. Structure Analysis

**Signal:** BULLISH | **Confidence:** MEDIUM

The price has broken above the recent swing high at 1158.5, establishing a new higher high structure. The nearest support level at 1187.19 is approximately 2.9% below current price, providing a reasonable stop-loss buffer. No formal BOS or CHoCH signals were triggered in the last 30 rows, but the price action itself is structurally bullish (making higher highs).

### Key Levels

| Level | Value | Distance from Current | Significance |
|-------|-------|----------------------|--------------|
| **Resistance** | 1260.67 | +3.12% | Nearest resistance level |
| Donchian Upper | 1231.0 | +0.69% | Current price near breakout point |
| 52-Week High | 1428.5 | +16.8% | Major resistance zone |
| **Support** | 1187.19 | -2.89% | Nearest support (EMA20 area) |
| Swing Low | 1104.5 | -9.67% | Recent low from September |
| SuperTrend Trail | 1310.84 | Below price | Not yet active as support |

### Structure Signals

| Signal | Value | Interpretation |
|--------|-------|----------------|
| HH (Higher High) | 0 (in recent 30 rows) | No new HH recorded in recent window |
| HL (Higher Low) | 0 (in recent 30 rows) | No new HL recorded in recent window |
| LH (Lower High) | 0 | No bearish structure |
| LL (Lower Low) | 0 | No bearish structure |
| BOS (Break of Structure) | 0 | No formal BOS in recent window |
| CHoCH (Change of Character) | 0 | No reversal signal |
| Trend Label | +1 | Bullish |

### Structure Assessment
- **Pattern:** Bullish — price has broken above the swing high at 1158.5 (set in mid-September) and is testing the Donchian upper at 1231.0. The absence of LH/LL signals in 30 days confirms no bearish structure.
- **Key levels:** Support at 1187 (near EMA20), resistance at 1260.67. Price is closer to resistance (3.1%) than support (2.9%), suggesting a narrow range between these levels.
- **Recent breaks:** Price broke above the swing high (~1158.5) around 2026-10-15 as it rallied from 1193.5. No formal BOS signal was logged, but the break is evident in price action.
- **Support touches:** The swing low at 1104.5 (September) held well — price bottomed and reversed, indicating strong support at that level.

### Structure Score

| Factor | Score | Weight | Weight | Weighted |
|--------|-------|--------|--------|----------|
| Price above swing high | +1.0 | 30% | | +0.30 |
| Support/resistance proximity (balanced) | +0.5 | 25% | | +0.13 |
| Trend label | +1.0 | 25% | | +0.25 |
| No LH/LL signals | +0.5 | 20% | | +0.10 |
| **Structure Score** | | **100%** | | **+0.60** (+1.80) |

**Structure Verdict:** Bullish structure confirmed by price breaking above swing high. Nearest support at 1187 provides a reasonable level for stop placement. No bearish structure signals in 30 days.

### Strategy Alignment
Strategy Data → HH=1, HL=1: Not formally logged in recent 30 rows but price action shows higher highs (broke above 1158.5). Strategy Data → BOS=1: Current 0 → ❌ NOT MET. Strategy Data → Trend=1: Current +1 → Match ✅. Structural conditions are partially bullish but lack formal BOS confirmation.

---

## 5. Volatility Analysis

**Signal:** NORMAL | **Confidence:** MEDIUM

Volatility is in a relatively low state (ATR percentile 25%), which is favorable for a trending asset. However, the price position within Bollinger Bands (86.2% of band width) is near the upper band — this is a bearish signal suggesting potential near-term pullback. The BB width of 11.02% is moderate, neither extreme contraction nor expansion. GARCH volatility is elevated at 1.25, indicating the model expects future volatility to increase.

### Current Indicators

| Indicator | Value | Assessment |
|-----------|-------|------------|
| ATR(14) | 23.14 | Absolute volatility |
| ATR Percentile | 25.0% | Low volatility (bottom quartile) |
| BB Width | 11.02% | Moderate — neither extreme contraction nor expansion |
| %B | 0.862 | Near upper band (0.86) — approaching overbought |
| BB Upper | 1240.41 | Resistance level |
| BB Lower | 1110.89 | Support level |
| HV(20) | 16.73% | Historical volatility level |
| Park Volatility | 19.58% | Range-based estimate |
| GARCH Vol | 124.91% | Elevated forecast — expects higher future vol |
| ATR Stop Distance | 5.68% | Suggested trailing stop distance |

### Volatility Assessment
- **Volatility Level:** ATR percentile at 25% = low volatility environment. This is favorable for trend continuation (less whipsaw risk).
- **Band Position:** Price at 86.2% of BB width — approaching the upper band (1240.41). This is a bearish signal indicating the move may be overextended in the short term.
- **Volatility Trend:** GARCH volatility at 124.9% is elevated, suggesting the model expects volatility to increase. This creates a potential breakout or pullback scenario.
- **Breakout Potential:** BB width of 11.02% is moderate. A contraction below 8% would signal a major breakout imminent; current width is in a neutral zone.
- **Suggested Stop:** ATR-based stop at 5.68% below entry (≈69.4 points at 1222.5 price) — reasonable for a utility stock with low historical volatility.

### Volatility Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| ATR Percentile (low vol) | +0.5 | 30% | +0.15 |
| BB Position (near upper) | -1.0 | 30% | -0.30 |
| Volatility Trend (GARCH rising) | -0.5 | 20% | -0.10 |
| BB Width (moderate) | +0.5 | 20% | +0.10 |
| **Volatility Score** | | **100%** | **-0.20** (-0.60) |

**Volatility Verdict:** Low absolute volatility is positive, but the near-upper-BB position (-1.0) is the dominant negative factor. The stock is approaching overbought territory on a volatility-adjusted basis.

### Strategy Alignment
Strategy Data → Preferred volatility: Low (ATR percentile 25%) is consistent with the strategy's preference for stable environments. However, the mean-reversion entry criteria require price at BB lower bands, not upper bands. The current volatility regime (low vol + near upper BB) is not the strategy's optimal entry setup for mean-reversion.

---

## 6. Volume Analysis

**Signal:** MIXED | **Confidence:** MEDIUM

OBV is rising with a strong positive slope (4.36M over 14 days, 1.78M over 7 days), confirming the uptrend with accumulation. CMF at +0.099 indicates mild buying pressure. However, OFI is negative (-0.16), suggesting short-term order flow is slightly bearish. Volume intensity is concerning — z-score of -1.43 and 0th percentile indicate current volume is well below average, which could signal weakening conviction behind the rally.

### Current Indicators

| Indicator | Value | Assessment |
|-----------|-------|------------|
| OBV | 2,031,969,447 | Rising — confirms uptrend |
| OBV Slope (14d) | +4,359,495 | Strong positive slope — accumulation |
| OBV Slope (7d) | +1,779,482 | Positive — still accumulating |
| CMF(20) | +0.099 | Mild buying pressure |
| OFI | -0.162 | Slight order flow imbalance toward sellers |
| VWAP | 1175.30 | Price 4.0% above VWAP — bullish |
| ADL | 493,714,849 | Positive — accumulation |
| MFI(14) | 54.49 | Neutral — volume-weighted RSI in mid-range |
| Volume Z-Score | -1.43 | Below average volume |
| Volume Percentile | 0.0% | Lowest volume readings |
| EMV(14) | 0.0000103 | Positive — price rising with some effort |

### Volume Assessment
- **Buying/Selling Pressure:** CMF (+0.099) is positive but mild, suggesting weak buying pressure. OFI (-0.162) is slightly negative, indicating recent order flow favors sellers. Combined reading: mixed — net buying exists but is waning.
- **Volume Trend:** OBV is rising with a strong positive slope (14d: +4.36M, 7d: +1.78M), confirming the uptrend. However, the declining volume intensity (z-score -1.43, percentile 0%) suggests the rally is occurring on lower participation — a potential warning sign.
- **Volume Intensity:** Z-score of -1.43 and 0th percentile indicate the current session volume (4.91M shares) is well below average. This is a concern for sustained upward momentum.
- **Smart Money:** ADL is positive at 493.7M, suggesting institutional accumulation. However, without volume confirmation, the strength of this signal is uncertain.
- **Divergence Warning:** Price is at 1222.5 (near 30-day highs) but volume is near 30-day lows. This price-volume divergence is a mild caution signal.

### Volume Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| OBV Direction (rising) | +1.0 | 30% | +0.30 |
| CMF (buying pressure) | +0.5 | 25% | +0.13 |
| Volume Intensity (below avg) | -0.5 | 25% | -0.13 |
| OFI (short-term order flow) | -0.5 | 20% | -0.10 |
| **Volume Score** | | **100%** | **+0.10** (+0.30) |

**Volume Verdict:** Mixed — OBV confirms the uptrend with rising accumulation, but declining volume intensity and negative OFI suggest waning conviction. The volume-price divergence is a mild caution signal.

### Strategy Alignment
Strategy Data → OBV Rising: Current rising OBV → Match ✅. Strategy Data → CMF > 0: Current +0.099 → Match ✅. Strategy Data → ADL Rising: Current positive → Match ✅. Strategy Data → OFI > 0: Current -0.16 → ❌ NOT MET. Strategy Data → MFI > 50: Current 54.5 → Match ✅. 4 out of 5 volume conditions are met, but declining volume intensity is a concern.

---

## 7. Regime Analysis

**Signal:** NEUTRAL | **Confidence:** HIGH

The HMM regime model assigns 88.7% probability to State 2, which is the neutral/sideways regime. This is the dominant regime for the entire last 30 days — the regime has been completely stable. The probability of the bullish State 0 has been declining steadily (from 13.5% on 2026-09-15 to 9.5% currently), while bear State 1 has been negligible. The regime model does not support a bullish position, creating a conflict with the strong technical trend signals.

### HMM Regime Probabilities

| Regime State | Probability | Interpretation |
|-------------|-------------|----------------|
| State 0 | 9.51% | Bull — low probability |
| State 1 | 1.82% | Bear — very low probability |
| State 2 | 88.66% | Neutral/Sideways — dominant regime |

### Regime Assessment
- **Dominant Regime:** State 2 (neutral/sideways) at 88.7% probability. The HMM model does not currently classify the market as being in a bull regime, despite the strong technical trend. This is a significant divergence between trend indicators and the regime model.
- **Regime Stability:** Complete stability — State 2 for all 30 rows (2026-09-15 to 2026-10-26). No regime changes in the entire 30-day window. The model has been consistently in neutral mode.
- **GARCH Context:** GARCH volatility at 124.9% is elevated within this neutral regime. High volatility in a sideways market suggests the market may be preparing for a significant move (breakout or breakdown).
- **Trend vs Regime Divergence:** Clear conflict — trend indicators show a strong uptrend (SuperTrend +1, EMA alignment, ADX 29) while the regime model is firmly neutral (88.7%). This divergence is common during transitional periods where technical trends develop before the regime model catches up.

### Regime Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| Dominant Regime (neutral) | 0.0 | 50% | +0.00 |
| Regime Stability (stable) | +0.5 | 30% | +0.15 |
| Bull Probability (low at 9.5%) | -0.5 | 20% | -0.10 |
| **Regime Score** | | **100%** | **+0.05** (+0.15) |

**Regime Verdict:** Neutral regime with high stability. The regime model's neutral stance conflicts with the bullish trend — this is the key uncertainty factor in the overall evaluation.

### Strategy Alignment
Strategy Data → Bull Regime Probability > 60%: Current State 0 at 9.5% → ❌ NOT MET. The strategy's HMM regime condition is far from the required 60% bull probability. In a neutral regime, the strategy recommends reduced risk (0.25% for volatile regime or no entry). The current regime is NOT conducive to the strategy's preferred conditions.

---

## Signal Synthesis

### Aggregate Score Summary

| # | Dimension | Signal | Score (-3.0 to +3.0) | Weight | Weighted |
|---|-----------|--------|-------------|--------|----------|
| 1 | **Trend** | BULLISH | +2.64 | 15% | +0.40 |
| 2 | **Momentum** | BULLISH | +1.80 | 15% | +0.27 |
| 3 | **Return** | MIXED | +1.20 | 10% | +0.12 |
| 4 | **Structure** | BULLISH | +1.80 | 10% | +0.18 |
| 5 | **Volatility** | NORMAL | -0.60 | 10% | -0.06 |
| 6 | **Volume** | MIXED | +0.30 | 15% | +0.05 |
| 7 | **Regime** | NEUTRAL | +0.15 | 15% | +0.02 |
| | **AGGREGATE** | | **+7.29** (sum) | **100%** | **+1.00** |

*Note: Sum of raw scores = 7.29. Weighted aggregate = +1.00 on the -3.0 to +3.0 scale.*

### Score Interpretation

**Aggregate Score: +1.00 — BUY**

The aggregate score of +1.00 falls in the "mildly bullish" range. Five of seven dimensions are bullish (Trend, Momentum, Return, Structure, Volume), one is bearish (Volatility), and one is neutral (Regime). The weighted average reflects that the bullish dimensions are not overwhelmingly strong — momentum is approaching overbought, volume is declining, and the regime model is neutral.

### Signal Determination
- **Overall Signal:** BUY
- **Strength:** Normal (|score| = 1.00, between 0.5 and 2.0)
- **Confidence:** Medium — 5 dimensions are High/Medium confidence, but the Volatility and Volume dimensions carry caution signals, and the Regime is explicitly neutral.

### Supporting Indicators (Top 3 per Dimension)

| Dimension | Indicator 1 | Indicator 2 | Indicator 3 |
|-----------|------------|------------|------------|
| Trend | SuperTrend +1 | ADX 29.2 + DI+/DI- 3.2:1 | EMA20 > EMA50 alignment |
| Momentum | MACD bullish cross (18.81 > 12.60) | Histogram +6.21 rising | ROC +8.43% |
| Return | 1M return +8.47% | RS vs FTSE 100 +11.35 | Alpha +0.386 |
| Structure | Price above swing high (1158.5) | No LH/LL in 30 days | Trend label +1 |
| Volatility | ATR percentile 25% (low) | BB width 11.02% (moderate) | GARCH vol 124.9% (elevated) |
| Volume | OBV rising (+4.36M slope) | CMF +0.099 (mild buying) | ADL +493.7M (accumulation) |
| Regime | HMM State 2 at 88.7% (neutral) | Stable regime (30 days) | Bull prob 9.5% (low) |

### Conflicting Indicators
- **Regime vs Trend:** HMM regime is firmly neutral (88.7%) while trend indicators are strongly bullish. This is the primary conflict — the regime model has not yet caught up to the technical uptrend.
- **Volatility vs Trend:** Price is at 86.2% of BB width (near upper band), suggesting overextension, while trend is bullish. This is a caution signal for a near-term pullback.
- **Volume vs Price:** Price is near 30-day highs but volume is in the 0th percentile. The rally is occurring on declining volume participation, which could indicate weak conviction.

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | WAIT for pullback to ~1186 (EMA20) | Current price is near resistance/overbought. Better risk-reward on a dip to EMA20 support. |
| **Current holders** | HOLD with trailing stop at ~1176 (EMA50) | Trend remains bullish but volatility suggests caution. Protect gains with stop below EMA50. |
| **Traders** | CAUTION — limited upside at these levels | Price near BB upper band (1240) and Donchian upper (1231) limits near-term upside. |
| **Value investors** | PATIENCE — await better entry or confirm trend reversal | No P/E data available; wait for fundamentals + technical alignment. |

- **Entry:** Consider entry on a pullback to 1186–1187 (EMA20 / nearest support zone) with confirmation from rising volume. Alternative: enter on a confirmed break above Donchian upper (1231) with volume expansion.
- **Stop-Loss:** Below 1176 (EMA50) or below 1187 (nearest support), whichever comes first. ATR-based stop: 1222.5 - (2 × 23.14) = 1176.2.
- **Target:** First target 1260.7 (nearest resistance), second target 1310.8 (SuperTrend trail).
- **Position Sizing:** 1% portfolio risk (per strategy framework). With ATR-based stop of ~46 points, position size = (Account Value × 1%) / 46.

### Risk Factors
- **Regime shift to neutral/bear:** If HMM State 2 probability remains above 80%, the regime model will not support further upside despite technical strength.
- **Volume drying up:** If volume percentile remains below 10%, the rally lacks participation and could reverse.
- **RSI overbought:** If RSI pushes above 70, mean-reversion pressure could trigger a pullback to EMA20 (1186).
- **EMA200 not reversed:** EMA200 (1193) is still above EMA50 (1176), meaning the longer-term downtrend has not fully reversed. A break below EMA200 would invalidate the bullish thesis.

### When This Signal Is Invalidated
- **Close below EMA20 (1186)** → Signal becomes HOLD (trend weakening, watch for deeper pullback)
- **Close below EMA50 (1176)** → Signal becomes SELL (trend broken, stop-loss triggered)
- **SuperTrend flips to -1** → Signal becomes SELL (momentum reversal confirmed)
- **HMM State 0 rises above 60%** → Signal upgrades to STRONG BUY (regime confirms bullish trend)

### Key Levels to Watch

| Event | Price Level | Distance | Action Trigger |
|-------|------------|----------|----------------|
| Stop loss trigger | 1176.00 | -3.8% | Close below EMA50 → exit |
| Support 1 | 1187.19 | -2.9% | Pullback entry zone |
| Support 2 | 1158.50 | -5.2% | Swing high turned support |
| Entry zone | 1186–1187 | -2.9% to -3.1% | Bullish candle + volume confirmation |
| Resistance 1 | 1231.00 | +0.7% | Donchian upper — breakout test |
| Resistance 2 | 1260.67 | +3.1% | Nearest resistance — take profit zone |

---

## Next Steps

- **Monitor for pullback to support at ~1186–1187 (EMA20 zone):** This offers a better risk-reward entry with stop at 1176 (EMA50).
- **Watch volume for confirmation:** A break above Donchian upper (1231) must be accompanied by volume expansion to confirm institutional participation.
- **Re-evaluation trigger:** Re-run evaluation if close drops below EMA20 (1186) or if HMM regime probability shifts significantly.
- **Strategy note:** The optimized strategies include mean-reversion and trend-following approaches. For the current trending environment, the Golden Cross trend-following or Momentum Composite strategies from the report are more appropriate than the mean-reversion strategies.
- **Long-term note:** If National Grid holds above EMA200 (1193) for an extended period, the longer-term downtrend (6M -6.0%) would be considered reversed, strengthening the bullish outlook.
- **Alerts:** Set price alerts at 1176 (EMA50 support), 1187 (nearest support), 1231 (Donchian upper breakout), and 1260.67 (nearest resistance).

---

*Report generated: 2026-10-27 | Data point: 2026-10-26 | Data: `data/analysis-data/NG.L.csv` (5053 rows) | Strategy: `data/reports/strategies/NG.L/20261021.md`*
