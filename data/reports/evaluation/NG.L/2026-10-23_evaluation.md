# NG.L Market Situation Evaluation

**Date:** 2026-10-23
**Ticker:** NG.L (National Grid)
**Data Source:** `data/analysis-data/NG.L.csv` (5,055 rows, 108 columns)
**Strategy Reference:** `data/strategy/NG.L/20261021.md` (BB Mean Reversion optimized strategies)
**52-Week Range:** 1,105.0p – 1,400.0p

---

## Executive Summary

| Category | Signal | Confidence |
|----------|--------|------------|
| Trend | Mixed/Neutral | Medium |
| Momentum | Bullish | Medium |
| Return | Flat/No Direction | Low |
| Structure | Bullish (no BOS/CHoCH) | Medium |
| Volatility | Moderate (BBW 10.97%) | High |
| Volume | Weakly Bullish (CMF +0.042) | Low |
| Regime | Bull-dominant (62.45%) | Medium |

**Overall Assessment: HOLD / WAIT FOR BETTER ENTRY**

NG.L is in a conflicted state. The HMM regime favors bulls (62.45%) and momentum indicators are bullish, but trend alignment is mixed — EMA20 and EMA50 are both below the EMA200, suggesting the long-term trend remains under pressure. Price (1,221.0p) sits near the top of the Bollinger Band range (89% of width) and 93% of the Donchian range, which is the opposite of where the recommended BB Mean Reversion strategy would want to enter. The SuperTrend indicator is flipping daily (~99 flips/100 days), making it unreliable. No strong directional conviction exists right now.

**Strategy Alignment: NOT MATCHED** — The recommended BB Mean Reversion strategy requires price at or below the Bollinger Lower Band with RSI < 30. Current price is at 89% of BB width (near upper band), RSI is 65.75, and Williams %R is not at extreme levels. Entry conditions are completely unmet.

---

## 1. Trend Analysis

### Current Signal: Mixed / Neutral

| Indicator | Value | Reading |
|-----------|-------|---------|
| Close | 1,221.0p | — |
| EMA20 | 1,182.2p | Price above (+3.3%) |
| EMA50 | 1,174.5p | Price above (+4.0%) |
| EMA200 | 1,192.6p | Price above (+2.4%) |
| EMA Alignment | 20 > 50 but both < 200 | Mixed |
| SuperTrend Direction | -1 (bearish) | Bearish (but unreliable — see below) |
| SuperTrend Lower | 1,310.84p | — |
| ADX | 27.39 | Moderate trend strength |
| DI+ | 23.96 | Bullish dominance |
| DI- | 7.67 | Weak bearish pressure |

### Analysis

**EMA Alignment Conflict:** EMA20 (1,182.2) > EMA50 (1,174.5) indicates a short-term bullish arrangement. However, both are below EMA200 (1,192.6), creating a classic "below long-term" picture. This is not a clean golden cross formation — it is a transitional zone.

**SuperTrend Quality Issue:** The SuperTrend has flipped direction nearly every single day over the past 100 trading days (99 flips recorded). This extreme whipsaw behavior makes the SuperTrend signal essentially useless for NG.L at current volatility regimes. The current direction of -1 (bearish) with a lower band at 1,310.84p (above the current price) is contradictory to the price being above all EMAs. This inconsistency highlights the indicator's unreliability for this ticker.

**ADX/DI Picture:** ADX at 27.39 indicates a moderate trend exists (above 25 threshold). DI+ at 23.96 significantly exceeds DI- at 7.67 (ratio of 3.1:1), suggesting that when trend does manifest, it tends to be bullish. However, the ADX is not in strong territory (>40), confirming the trend is present but not forceful.

**Verdict:** Mixed signals. Short-term structure favors bulls, long-term remains pressured. The SuperTrend should be disregarded for NG.L due to chronic whipsawing. Rely on EMA crossovers and price structure for trend decisions.

---

## 2. Momentum Analysis

### Current Signal: Bullish

| Indicator | Value | Reading |
|-----------|-------|---------|
| RSI(14) | 65.75 | Bullish, approaching overbought |
| MACD Line | 17.95 | Bullish |
| MACD Signal | 11.05 | — |
| MACD Histogram | 6.90 | Rising, bullish momentum |
| ROC(20) | (positive) | Positive momentum |
| Williams %R(14) | (not extreme) | Neutral zone |
| CCI(20) | — | — |
| TSI(25,13) | — | — |

### Analysis

RSI at 65.75 is in bullish territory (above 50) but approaching overbought (>70). This suggests upward momentum is present but could be nearing a short-term top.

MACD is clearly bullish: the MACD line (17.95) is well above the signal line (11.05), and the histogram (6.90) is positive and rising. This is a strong momentum signal that aligns with the RSI reading.

**25-Day Context:** Over the past 25 trading days, momentum has been building from oversold conditions. The MACD histogram transition from negative to positive has been sustained, indicating momentum is not a one-day anomaly but a developing trend.

**Verdict:** Bullish momentum, but RSI approaching 70 suggests caution. Momentum alone is not sufficient for entry — it needs confirmation from trend and structure.

---

## 3. Return Analysis

### Current Signal: Flat / No Clear Direction

| Metric | Value | Interpretation |
|--------|-------|---------------|
| 5d Forward Return Mean | ~0.18% | Flat |
| 10d Forward Return Mean | ~0.19% | Flat |
| 20d Forward Return Mean | ~-0.60% | Slightly bearish |
| 1M Past Return | — | — |
| 3M Past Return | — | — |
| 6M Past Return | — | — |
| 1Y Past Return | — | — |

### Analysis

Forward returns are essentially flat across horizons (5d: +0.18%, 10d: +0.19%), with a slightly negative 20d outlook (-0.60%). This suggests the market does not expect a strong directional move in either direction from current levels.

The flat forward return profile is consistent with the mixed trend picture and the price trading in the upper portion of its range — there is limited room for upside before hitting resistance, but downside could also be limited given the support level at 1,187p.

**Verdict:** No strong directional conviction from returns. This supports a wait-and-see approach.

---
## 4. Market Structure Analysis

### Current Signal: Bullish (no BOS/CHoCH)

| Indicator | Value | Reading |
|-----------|-------|---------|
| Trend | 1 (bullish) | Bullish |
| HH (Higher High) | Last recorded | — |
| HL (Higher Low) | Last recorded | — |
| BOS (Break of Structure) | None recent | No breakout |
| CHoCH (Change of Character) | None | No reversal |
| Nearest Resistance | 1,260.67p | ~3.2% above current |
| Nearest Support | 1,187.19p | ~2.8% below current |
| Donchian Range Position | 93.2% | Near recent highs |
| Donchian Upper | 1,260.67p | Resistance |
| Donchian Lower | 826.50p | Support |

### Analysis

The market structure shows a bullish bias with `trend=1`, but there have been no recent Break of Structure (BOS) or Change of Character (CHoCH) events. This means the stock is in a consolidation or gradual uptrend phase without decisive breakouts.

Price is at 93.2% of the Donchian channel range — extremely near the upper boundary (1,229.5p actual vs. 1,260.67p upper). This is a critical observation: the stock is trading very close to its recent highs, which is the WORST zone for a mean-reversion strategy. Mean-reversion strategies thrive when price is near the lower end of its range, not the upper.

Support at 1,187.19p is approximately 2.8% below current price, providing a reasonable downside buffer. Resistance at 1,260.67p is about 3.2% above, offering limited upside room in the near term.

**Verdict:** Bullish structure but near-term range-bound. The high Donchian position (93.2%) makes this a poor entry point for mean-reversion but could be a breakout zone for trend-following strategies if price clears 1,260.67p with volume.

---

## 5. Volatility Analysis

### Current Signal: Moderate

| Indicator | Value | Reading |
|-----------|-------|---------|
| Bollinger Band Width | 10.97% | Wide (favorable for MR) |
| %B | 0.89 | Near upper band |
| BB Upper | 1,235.15p | Immediate resistance |
| BB Middle | 1,170.90p | 20-day SMA |
| BB Lower | 1,106.65p | Theoretical MR entry zone |
| ATR(14) | — | Moderate volatility |
| Historical Volatility(20) | — | — |
| Parkinson Volatility(20) | — | — |
| ATR Percentile(14,20) | — | — |

### Analysis

Bollinger Band Width at 10.97% is above the 10% threshold identified as optimal for mean-reversion setups in the strategy document. Wide bands indicate the stock has sufficient room to revert, which is favorable for the BB Mean Reversion strategy's Entry2 filter.

However, %B at 0.89 means the price is at 89% of the distance from the lower to the upper band — very close to the upper band (1,235.15p). This is the exact opposite of where mean-reversion traders want to enter. The entry zone would be near the lower band (1,106.65p) with %B near 0.0 or below.

The gap between BB Lower (1,106.65p) and current price (1,221.0p) represents approximately 10.3% upside for a mean-reversion trade to complete — significant potential but requires the price to drop first.

**Verdict:** Volatility conditions (BBW > 10%) are favorable for mean-reversion, but price position within the band is wrong. Wait for price to approach the lower band before considering entry.

---

## 6. Volume Analysis

### Current Signal: Weakly Bullish

| Indicator | Value | Reading |
|-----------|-------|---------|
| CMF(20) | +0.042 | Weak buying pressure |
| OFI | -0.304 | Negative order flow |
| OBV | Rising | Accumulation signal |
| MFI(14) | — | — |
| EMV(14) | — | — |
| Volume Oscillator(14,28) | — | — |
| Volume Z-Score(20) | — | — |
| Volume Percentile(20) | — | — |

### Analysis

The volume picture is mixed. CMF at +0.042 indicates slight buying pressure (positive Chaikin Money Flow), but the value is very close to zero, suggesting weak conviction behind the buying.

OFI at -0.304 is notably negative, indicating that order flow is skewed toward selling pressure. This contradicts the CMF reading and suggests that while money flow is slightly positive, the actual order flow (aggressive buying vs. selling) is negative.

OBV (On-Balance Volume) is rising, which is a positive accumulation signal — smart money may be gradually accumulating positions even as short-term order flow is negative.

**25-Day Context:** Over the past 25 days, volume patterns have been inconsistent, with no clear accumulation or distribution pattern emerging. This is consistent with the range-bound, indecisive market state.

**Verdict:** Weakly bullish but contradictory signals (CMF positive, OFI negative). No strong conviction behind current price movement. Not a volume-backed rally.

---

## 7. Regime Analysis

### Current Signal: Bull-Dominant (Moderate Confidence)

| HMM State | Probability | Reading |
|-----------|-------------|---------|
| State 0 (Bull) | 62.45% | Bullish regime |
| State 1 (Bear) | 2.66% | Very low bear probability |
| State 2 (Neutral) | 34.90% | Significant neutral overlay |

### Analysis

The 3-state HMM model assigns a 62.45% probability to the bull regime, which is above the 60% threshold specified in the recommended strategies (Strategy 15: HMM Regime Adaptive, Strategy 17: High-Probability Multi-Factor).

However, the 34.90% neutral state probability is substantial — nearly one-third of the probability mass is in the neutral/volatile state. This means the regime is not strongly bullish but rather a bull-dominant environment with significant uncertainty.

For the HMM Regime Adaptive strategy (Strategy 15), the bull regime entry condition (Bull Probability > 60% AND EMA20 > EMA50 > EMA200) is partially met:
- Bull Probability 62.45% > 60% threshold: **MET**
- EMA20 (1,182.2) > EMA50 (1,174.5): **MET**
- EMA50 (1,174.5) > EMA200 (1,192.6): **NOT MET**

The EMA50 < EMA200 condition fails, so the HMM Bull Regime entry would not trigger despite favorable HMM probabilities.

**Verdict:** Regime favors bulls but the secondary EMA50 > EMA200 filter is not met. Moderate confidence in bull regime but not strong enough for unconditional long positioning.

---

---

## Strategy Cross-Reference

### Recommended Strategy from Backtest: BB Mean Reversion Optimized

The backtest results in `data/strategy/NG.L/20261021.md` identify **BB Mean Reversion** as the optimal strategy for NG.L, with the Entry2 filter (Config 2) being the best-performing variant.

### Entry Condition Checklist

| Condition | Strategy Requirement | Current Value | Met? |
|-----------|---------------------|---------------|------|
| Close ≤ BB Lower Band | ≤ 1,106.65p | 1,221.0p | **❌ NO** (10.3% above) |
| RSI(14) < 30 | < 30 | 65.75 | **❌ NO** |
| Williams %R(14) < -80 | < -80 | (not extreme) | **❌ NO** |
| BB Width ≥ 10% (Entry2) | ≥ 10% | 10.97% | **✅ YES** |
| ATR(14) ≥ 15 (Entry2) | ≥ 15p | — | **? Unknown** |

**Entry Status: ALL PRIMARY CONDITIONS FAILED (3/3)**

The recommended BB Mean Reversion strategy is completely out of favor right now. Price is 10.3% above the lower band, RSI is in bullish territory (65.75 vs. required < 30), and Williams %R is not at extreme levels.

### Exit Condition Alignment

If a BB Mean Reversion trade were somehow entered (which it shouldn't be), the exit conditions would be:
- **Primary (recommended):** Time-stop 120 days from entry
- **Alternative:** BB Middle band (1,170.90p) — but price is currently ABOVE this, so no trade to exit
- **Avoid:** SuperTrend flip (historically terrible — one trade lasted 719 days, -63.5%)

### Alternative Strategy Evaluation

| Strategy | Entry Met? | Viability |
|----------|-----------|-----------|
| Golden Cross Trend Following | ❌ (EMA50 < EMA200) | Low |
| EMA Pullback Continuation | ❌ (EMA50 < EMA200, price not at EMA200) | Low |
| SuperTrend Trend Following | ❌ (SuperTrend unreliable, frequent flips) | Very Low |
| Donchian Breakout | ❌ (Close < Donchian Upper 1,260.67) | Medium — watch for breakout |
| BB Breakout | ❌ (Close < BB Upper 1,235.15) | Low |
| Institutional Accumulation | ⚠️ (CMF > 0, OBV rising, but other conditions mixed) | Medium |
| VWAP Trend Strategy | — | — |
| Momentum Composite | ❌ (EMA50 < EMA200, no BOS) | Low |
| High-Probability Multi-Factor | ❌ (Multiple conditions unmet) | Low |
| HMM Regime Adaptive (Bull) | ❌ (EMA50 < EMA200) | Partial |

### Signal Scoring (per framework in strategy doc)

Using the weighted scoring framework (Trend 30%, Momentum 25%, Volume 20%, Structure 15%, Regime 10%):

| Category | Score (0-100) | Weight | Weighted |
|----------|--------------|--------|----------|
| Trend | 45 (mixed) | 30% | 13.5 |
| Momentum | 70 (bullish) | 25% | 17.5 |
| Volume | 45 (weak) | 20% | 9.0 |
| Structure | 60 (bullish, no BOS) | 15% | 9.0 |
| Regime | 62 (bull-dominant) | 10% | 6.2 |
| **Total Score** | | **100%** | **55.2** |

**Score: 55.2 → No Trade** (below 60 threshold)

---

## Fundamentals Context

| Metric | Value | Interpretation |
|--------|-------|---------------|
| P/E Ratio | 18.37 | Moderate valuation |
| Dividend Yield | 4.03% | Attractive income |
| EPS (TTM) | 0.655p | — |

The 4.03% dividend yield provides a reasonable income floor, which is typical for utility/infrastructure stocks like National Grid. The P/E of 18.37 is moderate — not cheap but not expensive for a regulated utility.

---

## Risk Assessment

### Key Risks

1. **SuperTrend Whipsaw Risk:** The SuperTrend indicator flips almost daily (99 flips in 100 days). Any strategy relying on SuperTrend signals for entry/exit should be avoided for NG.L. This has been confirmed by backtest results (SuperTrend flip exit: one trade lasting 719 days, -63.5%).

2. **EMA Conflict Risk:** The mixed EMA alignment (20 > 50 but both < 200) creates ambiguity about trend direction. This is a transitional zone where breakouts or breakdowns could be sharp.

3. **Mean-Reversion Timing Risk:** While the BB Mean Reversion strategy is backtested as optimal, entering before price reaches the lower band (1,106.65p) means waiting for a potential 10%+ drawdown. The opportunity cost of waiting is real.

4. **Regime Transition Risk:** The 34.9% neutral regime probability suggests the market could shift to a volatile regime, which would increase whipsaw risk and potentially break current support/resistance levels.

### Position Sizing (if trade were to occur)

| Parameter | Value |
|-----------|-------|
| Strategy Risk | 0.5% (BB Mean Reversion standard) |
| Account Risk | 0.5% (Conservative for unaligned signals) |
| Stop Loss | Swing Low - ATR (if entry at BB Lower) |
| Entry Price (hypothetical) | ~1,106.65p (BB Lower) |
| Stop Price (hypothetical) | ~1,090p (approx.) |
| Position Size (per £100k account) | ~520 shares |

---

## Conclusion and Action Plan

### Current State: NO TRADE SIGNAL

The evaluation score of 55.2 falls below the 60-point threshold for any trade recommendation. Multiple critical conditions for the recommended strategy are unmet:

1. **Price is at the wrong end of the range** — Near BB upper (89%) and Donchian upper (93%), opposite of mean-reversion entry zone
2. **Momentum is bullish** — RSI at 65.75 vs. required < 30
3. **Trend is conflicted** — EMA50 < EMA200 fails key trend filters
4. **Volume conviction is weak** — Conflicting CMF/OFI signals

### What to Watch For

**Bullish Trigger (Mean Reversion Entry Setup):**
- Price drops to BB Lower Band (~1,106p) or lower
- RSI(14) falls below 30
- Williams %R(14) falls below -80
- Re-check BB Width ≥ 10% and ATR ≥ 15 for Entry2 filter
- Consider this a potential 10%+ upside opportunity with time-stop exit (120d)

**Bullish Trigger (Breakout):**
- Price clears Donchian Upper at 1,260.67p
- Volume confirms (CMF > 0.1, OFI > 0.3)
- BOS event confirmed
- This would open trend-following strategy pathways

**Bearish Warning:**
- Price breaks below Support at 1,187.19p with volume
- EMA20 crosses below EMA50
- RSI drops below 50 with MACD histogram turning negative

### Recommended Monitoring Cadence

- **Daily:** Monitor price relative to BB bands (Upper: 1,235.15, Middle: 1,170.90, Lower: 1,106.65)
- **Weekly:** Check RSI levels and volume indicators (CMF, OBV)
- **Monthly:** Review HMM regime probabilities and forward return distributions
- **Trigger-based:** Act when BB Lower Band entry conditions are met (expected: 10-15% drawdown from current levels)

---

*Report generated: 2026-10-23 | Data as of 2026-10-23 | Next review: when price approaches BB Lower Band or key support/resistance levels*
