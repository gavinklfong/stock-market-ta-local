# Market Situation Evaluation: HSBC Holdings (HSBA.L)

**Evaluation Date:** 2026-10-26
**Actual Date Used:** 2026-10-26
**Ticker:** HSBA.L (HSBC Holdings)
**Price:** 1365.40
**Data Range:** 2006-10-26 to 2026-10-26 (5,052 rows)
**Sector:** Financial Services
**Strategy Reference:** `data/reports/strategies/HSBA.L/20261021.md`

---

## Executive Summary

**Signal:** WAIT
**Confidence:** Medium

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🔴 BEARISH | 🟢 High | SuperTrend=-1, EMA20<EMA50, -DI>DI, ADX=31.4 |
| **Momentum** | 🔴 BEARISH | 🟡 Medium | RSI=35.3, MACD negative, CCI=-117, ROC=-9.96% |
| **Return** | 🟡 MIXED | 🟡 Medium | 1M/3M negative but 6M/1Y positive; alpha=-0.59 |
| **Structure** | 🟡 CAUTIOUS | 🟡 Medium | Testing support at 1359, LL=1 but no recent BOS |
| **Volatility** | 🟢 LOW RISK | 🟡 Medium | ATR at 15th percentile, BB %B=0.17 near lower |
| **Volume** | 🟡 MIXED | 🟡 Medium | CMF=-0.08 selling, OFI=0.58 slight buying |
| **Regime** | 🟡 NEUTRAL | 🔴 Low | Regime 1 with mixed probs; unstable last 30 days |
| **Overall** | 🟠 CAUTION | 🟡 Medium | Bearish trend but oversold near support |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | 1365.40 | Near 52-week low of 1338.60 (98.2% of high) |
| 52-Week Range | 1338.60 – 1551.00 | At 98.2% of 52-week high, near bottom |
| P/E (TTM) | NaN | No fundamentals data available |
| Dividend Yield | NaN | No dividend data available |
| Beta (20d) | 1.99 | Highly volatile vs FTSE 100 (~2x) |
| RS vs FTSE 100 | 12.68 | Underperforming recently |

### Strategy Alignment Summary

| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| ADX Momentum: ADX > 25 | ADX = 31.41 | ✅ MET |
| ADX Momentum: +DI > -DI | +DI=17.25 / -DI=40.41 | ❌ NOT MET |
| ADX Momentum: RSI > 50 | RSI = 35.27 | ❌ NOT MET |
| ADX Momentum: MACD > Signal | MACD=-34.51 / Signal=-30.52 | ❌ NOT MET |
| Momentum Composite: RSI > 55 | RSI = 35.27 | ❌ NOT MET |
| Momentum Composite: EMA20 > EMA50 | EMA20=1418 < EMA50=1458 | ❌ NOT MET |
| SuperTrend strategies | SuperTrend=-1, flips frequently | ❌ AVOID |
| **Best strategy entry** | ADX Momentum conditions not met | ❌ NOT MET |

**Strategy Verdict:** None of the recommended entry conditions from the ADX Momentum strategy are met. The only satisfied condition is ADX > 25 (indicating a strong trend), but the trend is bearish (-DI > +DI), RSI is far below 50, and MACD is below signal. The Momentum Composite entry conditions are even more distant from being satisfied.

### Signal Summary

**Current Signal: WAIT**

HSBA.L is in a clear bearish trend with price 3.7% below EMA20 and 6.3% below EMA50, while SuperTrend has flipped bearish. However, the stock is approaching key structural support at 1359 with ATR at a low 15th percentile — suggesting oversold conditions that could precede a bounce. The HMM regime has been unstable (flipping between states 0, 1, and 2 in the last 30 days), adding uncertainty. All recommended entry conditions from the best backtested strategy (ADX Momentum) are currently unmet. For non-holders: wait for clear bullish reversal signals. For holders: monitor support and consider risk management if support breaks.

---

## 1. Trend Analysis

**Signal:** BEARISH | **Confidence:** HIGH

HSBA.L is in a well-established downtrend. Price has declined from ~1551 (52-week high) to 1365.40 — a loss of ~12% over the past month. The SuperTrend is firmly bearish (-1), and all major moving averages are sloping downward with the bearish alignment intact (EMA20 < EMA50 > EMA200, with EMA200 barely holding above price). ADX at 31.41 confirms a strong trend — but it is a strong downtrend with -DI significantly above +DI.

### Current Indicators

| Indicator | Value | Signal |
|-----------|-------|--------|
| EMA20 | 1418.17 | Price 3.7% below — bearish |
| EMA50 | 1457.76 | Price 6.3% below — bearish |
| EMA200 | 1372.37 | Price 0.5% below — barely below |
| SuperTrend Direction | -1 | Bearish |
| SuperTrend Trail | 309.69 | Extremely loose trail (artifact from regime model) |
| MA20 Slope | -5.90 | Negative — accelerating downtrend |
| MA50 Slope | -2.83 | Negative — declining |
| ADX(14) | 31.41 | Strong trend (>25) |
| +DI / -DI | 17.25 / 40.41 | -DI dominance — bearish |
| Aroon Up / Down | 4.0 / 96.0 | Near-total bearish structure |
| Price vs EMA20 | -3.72% | Below EMA20 |

### Trend Assessment
- **MA Alignment:** EMA20 (1418) < EMA50 (1458) — bearish. EMA200 (1372) is just below price — a critical level to watch. The EMA20 > EMA50 > EMA200 bullish alignment is fully broken.
- **SuperTrend:** Direction = -1 (bearish). The trend has been unstable recently, flipping between +1 and -1 almost daily over the past 30 days (flipped 14+ times), which aligns with the strategy report's finding that SuperTrend is unsuitable for HSBA.L.
- **MA Slopes:** MA20 slope = -5.90 (steeply negative, accelerating downtrend). MA50 slope = -2.83 (negative, moderating decline). Both declining.
- **Trend Strength:** ADX = 31.41 (>25) indicates a **strong trend**. However, -DI (40.41) >> +DI (17.25) confirms this is a strong **downtrend**. Aroon confirms: Aroon Down = 96 (near 100 = strong downtrend), Aroon Up = 4 (near 0 = no uptrend momentum).
- **Donchian Position:** Price (1365.40) is near the lower bound (1338.60) — only 2.0% above Donchian lower. This is a breakdown zone but also a potential bounce zone.
- **Keltner Position:** Price (1365.40) is just above Keltner lower (1362.49) — near the bottom of the Keltner channel.

### Trend Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| EMA Alignment (bearish) | -1.5 | 20% | -0.30 |
| SuperTrend Direction (bearish) | -1.0 | 15% | -0.15 |
| MA Slopes (both negative) | -1.5 | 15% | -0.23 |
| ADX/DI (strong but bearish) | -1.5 | 20% | -0.30 |
| Donchian/Keltner (near bottom) | +0.5 | 15% | +0.08 |
| Aroon (overwhelmingly bearish) | -1.0 | 15% | -0.15 |
| **Trend Score** | | **100%** | **-1.05 / 3.0** |

**Trend Verdict:** Strong bearish trend confirmed by multiple indicators (SuperTrend, ADX, DI, Aroon, MA slopes). However, price is near Donchian lower and Keltner lower, which may indicate oversold conditions — the bearish trend could be nearing exhaustion.

### Strategy Alignment
The ADX Momentum strategy requires +DI > -DI, RSI > 50, and MACD > Signal — all of which are violated. The trend is strong (ADX > 25) but bearish, not bullish. The strategy report explicitly warns against SuperTrend-based strategies for HSBA.L due to excessive noise — and the SuperTrend has been flipping almost daily, confirming this.

---

## 2. Momentum Analysis

**Signal:** BEARISH | **Confidence:** MEDIUM

All major momentum oscillators are in bearish territory. RSI is at 35.27 (weak/oversold), MACD is deeply negative with a declining histogram, ROC is -9.96%, and CCI is at -116.74 (below -100 = oversold). The only slight glimmer is Williams %R at -78.96 (approaching but not yet in oversold < -80 territory). The breadth of bearish momentum signals is concerning, but the fact that RSI, CCI, and Williams %R are all in oversold territory simultaneously suggests the decline may be nearing a temporary bottom.

### Current Indicators

| Indicator | Value | Signal |
|-----------|-------|--------|
| RSI(14) | 35.27 | Weak/oversold (< 40) |
| RSI Z-Score | -0.49 | Below average |
| RSI Percentile | 40.0% | Below median — bearish |
| MACD Line | -34.51 | Deeply negative — bearish |
| MACD Signal | -30.52 | MACD below signal — bearish cross |
| MACD Histogram | -3.99 | Declining (more negative) — worsening |
| ROC(20) | -9.96% | Strong negative momentum |
| Williams %R | -78.96 | Approaching oversold (< -80) |
| CCI(20) | -116.74 | Oversold (< -100) |
| MFI(14) | -54.82 | Neutral/slightly bearish |

### Momentum Assessment
- **RSI Context:** RSI = 35.27 — in the weak zone (30-50). Z-score = -0.49 (below average) and percentile = 40% (below median) confirm this is relatively weak but not at extreme oversold levels. The RSI has been falling from ~43 in mid-September to current 35.3 — a clear deterioration.
- **MACD State:** MACD line = -34.51, signal = -30.52 — MACD is below signal (bearish cross). The histogram = -3.99 is negative and expanding (becoming more negative), indicating accelerating downside momentum. This is the most concerning signal.
- **Oscillator Convergence:** All three major oscillators (RSI, CCI, Williams %R) are in oversold/weak territory. This convergence is significant — multiple independent indicators agree on bearish momentum. However, when multiple oscillators are simultaneously oversold, it often signals a near-term bounce is due.
- **Divergence Check:** Price has been falling (1551 → 1365) while RSI has been falling (43 → 35) — no bullish divergence yet. Need to watch for price making a lower low while RSI makes a higher low.

### Momentum Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| RSI (weak/oversold) | -1.0 | 25% | -0.25 |
| MACD (negative, histogram declining) | -1.5 | 25% | -0.38 |
| ROC/CCI/Williams (all bearish/oversold) | -1.0 | 20% | -0.20 |
| Oscillator convergence (oversold = bounce risk) | +0.5 | 15% | +0.08 |
| MFI (neutral) | 0.0 | 15% | 0.00 |
| **Momentum Score** | | **100%** | **-0.75 / 3.0** |

**Momentum Verdict:** Strongly bearish momentum across all oscillators, but oversold readings suggest a bounce may be imminent. The declining MACD histogram is the most concerning near-term signal as it indicates momentum is still accelerating downward.

### Strategy Alignment
The ADX Momentum strategy requires RSI > 50 and MACD > Signal — both are far from met. The Momentum Composite requires RSI > 55, MACD > Signal, ROC > 0, Williams %R > -50, and CMF > 0 — none of these are met. Momentum conditions are completely misaligned with any recommended entry.

---

## 3. Return Analysis

**Signal:** MIXED | **Confidence:** MEDIUM

HSBA.L shows a mixed return picture. Short-term returns (1M: -9.71%, 3M: -11.82%) are strongly negative, reflecting the recent downtrend. However, medium-term returns (6M: +2.49%, 1Y: +36.00%) remain positive, showing the stock has maintained a strong longer-term uptrend despite recent weakness. Alpha is negative (-0.59) and beta is high (1.99), indicating HSBA is underperforming the FTSE 100 on a risk-adjusted basis and is nearly twice as volatile.

### Past Performance

| Period | Return | Assessment |
|--------|--------|------------|
| 1 Month | -9.71% | Strong negative — recent sell-off |
| 3 Months | -11.82% | Strong negative — deteriorating |
| 6 Months | +2.49% | Slightly positive — holding ground |
| 1 Year | +36.00% | Strong positive — still in long-term bull |

### Risk-Adjusted Metrics

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Alpha(20) | -0.59 | Negative — underperforming benchmark (FTSE 100) |
| Beta(20) | 1.99 | ~2x more volatile than FTSE 100 — high risk |
| RS vs FTSE 100 | 12.68 | Underperforming — declining relative strength |

### Return Assessment
- **Short-term trend:** 1M (-9.71%) and 3M (-11.82%) returns are both strongly negative, confirming the current bearish phase. The 1-month loss is particularly sharp.
- **Medium-term trend:** 6M (+2.49%) is barely positive, and 1Y (+36.00%) remains strong. This shows the longer-term uptrend is intact but being tested.
- **Risk-adjusted:** Alpha = -0.59 (negative) indicates HSBA is underperforming the FTSE 100 on a risk-adjusted basis. Beta = 1.99 means HSBA moves roughly 2x as much as the FTSE 100 — in a down market, it will fall harder.
- **Forward expectations:** Forward return data (ta_return_5d/10d/20d) is NaN — not available. However, the strong 1Y return (+36%) suggests this stock is historically a momentum asset that tends to trend.

### Return Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| 1M/3M returns (negative) | -1.0 | 25% | -0.25 |
| 6M/1Y returns (positive) | +1.0 | 25% | +0.25 |
| Alpha/Beta (underperforming, high beta) | -0.5 | 25% | -0.13 |
| RS vs FTSE 100 (declining) | -0.5 | 25% | -0.13 |
| **Return Score** | | **100%** | **-0.26 / 3.0** |

**Return Verdict:** Mixed — short-term returns are strongly negative but the 1-year trend (+36%) remains robust. High beta works against the stock in this down phase but will amplify gains if the trend reverses.

### Strategy Alignment
The strategy report identifies HSBA.L as a "strong trending/bull stock" with +127.7% 20-year return. This is a momentum asset, not a mean-reversion asset. The current short-term negative returns are consistent with a pullback in a long-term uptrend. The ADX Momentum strategy is well-suited to this character — it waits for strong trending conditions (ADX > 25) with bullish alignment.

---

## 4. Structure Analysis

**Signal:** CAUTIOUS | **Confidence:** MEDIUM

HSBA.L is testing a critical support zone. The nearest support is at 1359.0 (only 0.47% below current price of 1365.40), while resistance is much further away at 1456.0 (+6.64%). A recent swing low was identified at 1368.0 (idx 5039), which price has now broken below. There is one recent LL (lower low) signal but no recent HH or HL — the structure is bearish. However, the support has been touched 48 times historically, suggesting a well-established and resilient floor. Two BOS signals have occurred recently (bearish breaks), and no CHoCH has been triggered yet — a CHoCH would signal a potential trend reversal from bearish to bullish.

### Key Levels

| Level | Value | Distance from Current | Significance |
|-------|-------|----------------------|--------------|
| **Resistance** | 1456.00 | +6.64% | Nearest resistance — significant psychological level |
| **Donchian Upper** | 1537.80 | +12.64% | 20-day breakout level |
| **Support** | 1359.00 | -0.47% | Nearest support — critically close |
| **Donchian Lower** | 1338.60 | -1.93% | 20-day breakdown level / 52-week low |
| **Swing Low** | 1368.00 | +0.19% | Most recent swing low (slightly above price) |

### Structure Signals

| Signal | Value | Interpretation |
|--------|-------|----------------|
| HH (Higher High) | 0 (recent) | No bullish structure |
| HL (Higher Low) | 0 (recent) | No bullish structure |
| LH (Lower High) | 0 (recent) | — |
| LL (Lower Low) | 1 (recent) | Bearish structure confirmed |
| BOS (Break of Structure) | 2 (recent) | Bearish breaks — trend continuation |
| CHoCH (Change of Character) | 0 (recent) | No reversal signal yet |
| Trend Label | -1 | Bearish |
| Support Touches | 48 | Well-established support zone |

### Structure Assessment
- **Pattern:** Bearish — no HH/HL, one LL, two BOS (bearish). The structure is in a downtrend.
- **Key levels:** Price (1365.40) is sandwiched between nearest support (1359.00, -0.47%) and nearest resistance (1456.00, +6.64%). The asymmetry is stark — downside risk is minimal in percentage terms, but the support level is being actively tested.
- **Recent breaks:** Two bearish BOS signals in the recent window. No CHoCH — no sign of reversal yet.
- **Support touches:** 48 historical touches to the nearest support zone — this is a well-tested, well-known floor. If it holds, a strong bounce is plausible.

### Structure Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| Bearish structure (LL, BOS, no CHoCH) | -1.0 | 25% | -0.25 |
| Support proximity (critical test) | -0.5 | 25% | -0.13 |
| Resistance distance (far away) | -0.5 | 20% | -0.10 |
| Historical support resilience (48 touches) | +0.5 | 20% | +0.10 |
| Support/Resistance asymmetry (favors upside) | +0.5 | 10% | +0.05 |
| **Structure Score** | | **100%** | **-0.23 / 3.0** |

**Structure Verdict:** Cautious — bearish structure confirmed but price is at a well-established support zone. A break below 1359 would be bearish confirmation; a bounce from here could signal a reversal setup.

### Strategy Alignment
The ADX Momentum strategy does not explicitly use structural signals, but the strategy report notes that Market Structure and BOS strategies generated too few signals on HSBA.L. The current structure (LL + BOS) confirms the downtrend but doesn't provide any entry signal. A CHoCH would be needed for a structural reversal confirmation.

---

## 5. Volatility Analysis

**Signal:** LOW RISK | **Confidence:** MEDIUM

Volatility is at a historically low level (ATR percentile = 15th), which is unusual for HSBA.L given its high beta of 1.99. Bollinger Bands show price near the lower band (%B = 0.17), and band width is moderate (11.67%). GARCH volatility at 1.62 suggests the model expects volatility to remain elevated. The combination of low ATR percentile with price near BB lower suggests a potential compression → breakout scenario.

### Current Indicators

| Indicator | Value | Assessment |
|-----------|-------|------------|
| ATR(14) | 28.93 | Absolute level — moderate |
| ATR Percentile | 15.0% | Low — unusual for this stock |
| BB Width | 0.1167 | Moderate — not extreme contraction |
| %B | 0.17 | Near lower band — oversold territory |
| BB Upper | 1502.79 | Resistance level — 10.1% above price |
| BB Lower | 1337.05 | Support level — 2.1% below price |
| HV(20) | 0.2738 | Moderate historical volatility |
| Parkinson Vol | 0.2087 | Range-based estimate — moderate |
| GARCH Vol | 1.62 | Elevated forecast — volatility expected |
| ATR Stop Distance | 6.36 | Suggested stop = ~6.36 points below entry |

### Volatility Assessment
- **Volatility Level:** ATR at 15th percentile is low — this is unusual for HSBA.L (beta=1.99). Low volatility often precedes a significant move (either direction).
- **Band Position:** Price at BB %B = 0.17 — near the lower band. Historically, this level has preceded bounces, but not always.
- **Volatility Trend:** HV(20) = 0.274 (moderate), GARCH = 1.62 (elevated forecast) — volatility is expected to increase.
- **Breakout Potential:** BB width = 11.67% is moderate (not extreme compression). However, the low ATR percentile suggests we may be in a compression phase. A breakout (up or down) is likely in the near term.
- **Suggested Stop:** ATR-based stop = 6.36 points. For a long entry at 1365, a stop at ~1359 (nearest support) is tighter than ATR-based; a stop at ~1338 (Donchian lower) is more conservative.

### Volatility Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| Low ATR percentile (15%) — potential breakout | +1.0 | 25% | +0.25 |
| BB %B near lower (oversold bounce potential) | +0.5 | 25% | +0.13 |
| GARCH elevated (volatility expected to rise) | -0.5 | 20% | -0.10 |
| Moderate BB width (not extreme compression) | 0.0 | 20% | 0.00 |
| ATR stop distance (reasonable for position sizing) | +0.5 | 10% | +0.05 |
| **Volatility Score** | | **100%** | **+0.33 / 3.0** |

**Volatility Verdict:** Low volatility risk with bounce potential. Price near BB lower with low ATR percentile suggests a compression → breakout scenario. Direction is uncertain but volatility is favorable for trade setup if a clear signal emerges.

### Strategy Alignment
The strategy report doesn't use volatility-based entries directly, but the ADX Momentum strategy's high win rate (48.9%) and low max drawdown (23.3%) suggest it handles volatility well. The current low volatility environment could set up a favorable entry if the trend reverses bullish.

---

## 6. Volume Analysis

**Signal:** MIXED | **Confidence:** MEDIUM

Volume indicators send mixed signals. CMF is negative (-0.078), indicating mild selling pressure. OBV is deeply negative (-360M) and declining (negative slopes on both 14-day and 7-day windows), confirming distribution. However, OFI is slightly positive (0.58), suggesting some order flow imbalance toward buyers. Volume intensity is above average (Z-score = 0.42, percentile = 65%), indicating active trading — this could be capitulation selling or early accumulation.

### Current Indicators

| Indicator | Value | Assessment |
|-----------|-------|------------|
| OBV | -359,967,885 | Deeply negative — distribution |
| CMF(20) | -0.078 | Mild selling pressure |
| OFI | 0.58 | Slight order flow imbalance toward buyers |
| VWAP | 1418.70 | Price 3.7% below VWAP — bearish |
| ADL | 2,120,051,595 | Positive accumulation level |
| MFI(14) | -54.82 | Neutral/slightly bearish |
| Volume Z-Score | 0.42 | Above average volume |
| Volume Percentile | 65.0% | Moderate-high intensity |
| EMV(14) | -0.000013 | Negative — movement against buyers |
| OBV Slope (14) | -2,391,677 | Declining OBV — distribution |
| OBV Slope (7) | -4,720,221 | Sharply declining OBV — accelerating distribution |

### Volume Assessment
- **Buying/Selling Pressure:** CMF = -0.078 (mild selling) combined with OFI = +0.58 (slight buying) — mixed but slightly leaning toward selling. The OFI positive reading is the only bullish volume signal.
- **Volume Trend:** OBV is declining steeply (both 14-day and 7-day slopes are strongly negative), confirming distribution. This is bearish — volume is confirming the price decline.
- **Volume Intensity:** Z-score = 0.42 and percentile = 65% — above-average volume. In a downtrend, above-average volume can signal either capitulation (bullish if bottom) or strong selling pressure (bearish if continuation).
- **Smart Money:** ADL is positive (2.12B) — suggests some accumulation at these levels. However, the declining OBV slope suggests the dominant flow is still distribution.
- **Divergence Warning:** OBV is declining with price — no bullish divergence yet. If price makes a lower low while OBV makes a higher low, that would be a strong bullish divergence signal.

### Volume Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| CMF (mild selling) | -0.5 | 25% | -0.13 |
| OBV trend (declining, distribution) | -1.0 | 25% | -0.25 |
| OFI (slight buying) | +0.5 | 15% | +0.08 |
| Volume intensity (above average — ambiguous) | 0.0 | 20% | 0.00 |
| VWAP (price below — bearish) | -0.5 | 15% | -0.08 |
| **Volume Score** | | **100%** | **-0.38 / 3.0** |

**Volume Verdict:** Mixed to bearish — selling pressure (CMF, OBV) dominates but OFI suggests some buyer interest. Above-average volume in a downtrend is ambiguous — could be capitulation or continued distribution.

### Strategy Alignment
The ADX Momentum strategy doesn't use volume confirmation explicitly. The Momentum Composite requires CMF > 0 — not met. Volume is not currently supporting a bullish entry. However, if volume continues at above-average levels while price stabilizes, that could signal accumulation.

---

## 7. Regime Analysis

**Signal:** NEUTRAL | **Confidence:** LOW

The HMM regime model is in state 1 with highly mixed probabilities — prob_0 = 40.1%, prob_1 = 5.6%, prob_2 = 54.3%. This is a highly uncertain regime state. The regime has been extremely unstable over the past 30 days, flipping between states 0 (bull), 1 (bear/transition), and 2 (neutral/sideways) almost daily. This instability makes regime-based decisions unreliable and suggests we are in a transition period.

### HMM Regime Probabilities

| Regime State | Probability | Interpretation |
|-------------|-------------|----------------|
| State 0 | 40.1% | Bull-ish — second highest probability |
| State 1 | 5.6% | Bear/Transition — currently dominant regime label |
| State 2 | 54.3% | Neutral/Sideways — highest probability |

### Regime Assessment
- **Dominant Regime:** State 2 (54.3%, neutral/sideways) is the highest probability, but the regime label is State 1 (5.6%). This discrepancy reflects the model's uncertainty — no single state has a commanding probability.
- **Regime Stability:** Extremely unstable. Over the past 30 days, the regime has flipped between all three states:
  - Sep 15-30: Flipped between 0 and 2 (mostly 2 = neutral)
  - Oct 1-16: Locked into state 1 (16 consecutive days)
  - Oct 19-26: Flipping between 1 and 2 again
  This constant regime switching is unusual and indicates a highly uncertain market environment.
- **GARCH Context:** GARCH vol = 1.62 (elevated). Within the current regime 1 state, volatility is elevated, suggesting ongoing uncertainty.
- **Trend vs Regime Divergence:** Trend indicators show a clear downtrend, but the regime model shows no clear consensus (no state > 55%). This divergence suggests the trend may be transitioning — the bearish trend could be losing momentum, consistent with oversold oscillators.

### Regime Score

| Factor | Score | Weight | Weighted |
|--------|-------|--------|----------|
| No dominant regime (highest prob only 54.3%) | -1.0 | 40% | -0.40 |
| Regime instability (14+ flips in 30 days) | -1.0 | 30% | -0.30 |
| Regime label (1) vs highest prob (2) discrepancy | -0.5 | 15% | -0.08 |
| GARCH elevated (uncertainty in current regime) | -0.5 | 15% | -0.08 |
| **Regime Score** | | **100%** | **-0.85 / 3.0** |

**Regime Verdict:** Highly uncertain regime — no clear consensus. The model is struggling to classify the current market state, which adds significant uncertainty to the overall signal. This is a cautionary signal, not a bearish one.

### Strategy Alignment
The strategy report explicitly warns against using HMM Bull strategies for HSBA.L due to overtrading (644 trades, -69% return). The current regime instability confirms this — the HMM model generates too many false signals in the current environment. The ADX Momentum strategy does not rely on regime classification, making it more robust in this uncertain regime.

---

## Signal Synthesis

### Aggregate Score Summary

| # | Dimension | Signal | Score (/3.0) | Weight | Weighted |
|---|-----------|--------|-------------|--------|----------|
| 1 | **Trend** | BEARISH | -1.05 | 20% | -0.21 |
| 2 | **Momentum** | BEARISH | -0.75 | 20% | -0.15 |
| 3 | **Return** | MIXED | -0.26 | 15% | -0.04 |
| 4 | **Structure** | CAUTIOUS | -0.23 | 15% | -0.03 |
| 5 | **Volatility** | LOW RISK | +0.33 | 10% | +0.03 |
| 6 | **Volume** | MIXED | -0.38 | 10% | -0.04 |
| 7 | **Regime** | NEUTRAL | -0.85 | 10% | -0.09 |
| | **AGGREGATE** | | | **100%** | **-0.52** |

### Score Interpretation

**Aggregate Score: -0.52 — WAIT**

The aggregate score of -0.52 falls in the "Neutral / Wait" range. The bearish trend (-1.05) and bearish momentum (-0.75) are the dominant forces, pulling the score negative. However, low volatility risk (+0.33) and mixed returns (+/-0.26) partially offset. The highly uncertain regime (-0.85) significantly drags on the score, reflecting the model's inability to determine whether the downtrend is continuing or reversing.

### Signal Determination
- **Overall Signal:** WAIT
- **Strength:** Weak (scores are mixed, not strongly negative)
- **Confidence:** Medium (data is clear on trend/momentum being bearish, but regime uncertainty and oversold readings add ambiguity)

### Supporting Indicators (Top 3 per Dimension)

| Dimension | Indicator 1 | Indicator 2 | Indicator 3 |
|-----------|------------|------------|------------|
| Trend | ADX/DI (-DI>DI) | SuperTrend=-1 | MA20 Slope (-5.90) |
| Momentum | MACD histogram (-3.99) | RSI (35.3) | CCI (-116.7) |
| Return | 1M return (-9.71%) | 1Y return (+36%) | Beta (1.99) |
| Structure | Support test (1359) | LL=1, BOS=2 | Resistance distance (+6.6%) |
| Volatility | ATR percentile (15%) | BB %B (0.17) | GARCH vol (1.62) |
| Volume | OBV slope (-2.4M) | CMF (-0.078) | OFI (+0.58) |
| Regime | HMM prob (mixed) | Regime stability (unstable) | GARCH vol (1.62) |

### Conflicting Indicators
- **Trend vs Volatility:** Trend is strongly bearish but volatility is at 15th percentile (low) with price at BB lower — this combination often precedes bounces. The bearish trend may be exhausted.
- **Momentum vs Structure:** All momentum oscillators are bearish/oversold, but price is at a well-established support zone (48 touches). This structural support could cause a bounce despite bearish momentum.
- **Regime vs Trend:** Trend indicators clearly show bearish conditions, but the regime model shows no dominant state (no probability > 55%). This suggests the trend may be transitioning.

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | DO NOT ENTER | All ADX Momentum entry conditions unmet; bearish trend intact |
| **Current holders** | HOLD with caution | Support at 1359 is critical; set stop if break below |
| **Traders** | AVOID (WAIT for signal) | Regime uncertainty + oversold readings = too risky |
| **Value investors** | PATIENCE | Monitor for CHoCH + bullish trend confirmation before adding |

- **Entry:** Wait for ADX Momentum entry conditions: (1) +DI crosses above -DI, (2) RSI > 50, (3) MACD crosses above signal. Ideally after price bounces from support (1359) and reclaims EMA20 (~1418).
- **Stop-Loss:** 1338.60 (Donchian lower / 52-week low). A break below this level would confirm continuation of the downtrend. Alternatively, ATR-based stop at 1359 (nearest support).
- **Target:** 1456.00 (nearest resistance, +6.6%) for initial target; 1502.79 (BB upper, +10.1%) for extended target.
- **Position Sizing:** If entering, size conservatively (0.5-1x normal) given regime uncertainty.
- **Max Holding Period:** Monitor weekly — if no trend reversal within 4-6 weeks, reassess.

### Risk Factors
- **Regime shift:** HMM regime could shift to state 0 (bull) at any time given current instability. This would be a positive surprise.
- **Volume declining:** If volume drops below average while price holds support, it could signal the end of distribution and a bounce.
- **Support break:** A close below 1338.60 (Donchian lower / 52-week low) would trigger a bearish breakout with potential for accelerated downside.
- **MACD histogram still declining:** The most dangerous signal — if the histogram continues to deepen, momentum is still accelerating downward.

### When This Signal Is Invalidated
- **Close above EMA20 (1418)** → Signal becomes BUY (trend reversal confirmation)
- **CHoCH signal triggered** → Signal becomes BUY (structural reversal)
- **Close below 1338.60** → Signal becomes SELL (breakout continuation)
- **SuperTrend flips to +1 AND holds for 5+ days** → Signal becomes BUY (trend change)
- **RSI crosses above 50 AND +DI > -DI** → Signal becomes BUY (ADX Momentum entry)

### Key Levels to Watch

| Event | Price Level | Distance | Action Trigger |
|-------|------------|----------|----------------|
| Stop loss trigger | 1338.60 | -1.95% | Close below → SELL signal |
| Support 1 | 1359.00 | -0.47% | Hold → WAIT / Watch for bounce |
| Support 2 | 1368.00 | +0.19% | Break below → bearish continuation |
| Entry zone | 1418–1456 | +3.8–6.6% | Reclaim EMA20 + momentum confirmation |
| Resistance 1 | 1456.00 | +6.64% | Break above → bullish continuation |
| Resistance 2 | 1502.79 | +10.09% | Break above → BB upper breakout |

---

## Next Steps

- **Monitor support at 1359:** Watch for a bounce or hold. A hold with declining volume would be a positive sign (end of distribution).
- **Watch MACD histogram:** If it stops declining and starts rising, momentum may be bottoming. This would be an early bullish signal.
- **Wait for CHoCH or trend confirmation:** A CHoCH signal or SuperTrend holding +1 for 5+ days would confirm a trend reversal.
- **Re-run evaluation if close breaks 1338.60:** A break below Donchian lower/52-week low would change the signal to SELL.
- **Re-run evaluation if RSI crosses above 50 + +DI > -DI:** This would trigger the ADX Momentum entry condition — the best strategy's recommended entry.
- **Set alerts at support (1359) and resistance (1456):** Price action at these levels will determine near-term direction.
- **Long-term perspective:** HSBA.L has a +36% 1-year return and +127.7% 20-year return — this is a strong long-term trending stock. Current weakness may be a healthy pullback in a long-term uptrend.

---

*Report generated: 2026-10-26 | Data point: 2026-10-26 → 2026-10-26 | Data: `data/analysis-data/HSBA.L.csv` (5,052 rows) | Strategy: `data/reports/strategies/HSBA.L/20261021.md`*
