# Market Situation Evaluation: National Grid (NG.L)

**Evaluation Date:** 2026-10-27
**Actual Date Used:** 2026-10-27
**Ticker:** NG.L (National Grid)
**Price:** 1221.0
**Data Range:** 2006-10-27 to 2026-10-27 (5,053 rows)
**Sector:** Utilities
**Strategy Reference:** `data/reports/strategies/NG.L/20261027.md`

---

## Executive Summary

**Signal:** HOLD
**Confidence:** Medium

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🟢 BULLISH | 🟢 High | Price above EMA20/50/200, positive MA slopes, ADX 30.3 with +DI 21.7 > -DI 8.4 — 6 of 7 trend indicators bullish |
| **Momentum** | 🟡 CAUTIOUS | 🟢 High | RSI 65.4 approaching overbought; MACD line 19.16 > signal 13.91 (bullish); Williams %R -11.6 and CCI 92.7 overbought — mixed momentum signals |
| **Return** | 🟢 POSITIVE | 🟢 High | +60.4% 1Y return, +8.3% 1M, +11.4% RS vs FTSE 100; all forward return probabilities >54% |
| **Structure** | 🟡 CAUTIOUS | 🟡 Medium | Consolidation between 1187 support and 1261 resistance; price 2.8% above support, 3.2% below resistance; HH/HL/LH/LL all 0 (no pattern) |
| **Volatility** | 🟡 NORMAL | 🟢 High | ATR normalized 1.85% moderate; BB width 10.7% compressed; price at 82% of bands — elevated but not extreme |
| **Volume** | 🟡 MIXED | 🟡 Medium | CMF +0.09 mild accumulation; OFI +0.18 positive; OBV slope +4.0M; but MFI -42.3 and ADL bearish — 3 bullish vs 2 bearish |
| **Regime** | 🟢 BULL | 🟢 High | HMM state 0 (bull) at 96.4% probability; 30 consecutive days in state 0 — exceptionally stable (unlike SSE.L) |
| **Overall** | 🟡 HOLD | 🟡 Medium | Strong trend and regime vs. overbought momentum and no strategy entry signal — mean-reversion strategy needs a dip |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | 1,221.0 | 2.7% above EMA20 (1,189.4); 3.6% above EMA50 (1,178.1); 2.3% above EMA200 (1,193.2) |
| 52-Week Range | 1,096.5 – 1,428.5 | 70.7% of range from low; 14.5% below 52W high |
| P/E (TTM) | N/A | EPS TTM null — no P/E data available |
| Dividend Yield | N/A | Dividend data null — no yield available |
| Beta (20d) | 0.59 | Defensive — low volatility vs FTSE 100 |
| RS vs FTSE 100 | +11.4% | Outperforming over 20-day window |

### Strategy Alignment Summary

#### Entry conditions

| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| **bb_meanrev: Close ≤ Bollinger Lower Band** | 1,221 > 1,117.7 (BB lower) | ❌ NOT MET — price is ABOVE all Bollinger Bands |
| **bb_meanrev: RSI(14) < 30** | RSI 65.4 | ❌ NOT MET — price is far from oversold |
| **bb_meanrev: Williams %R(14) < -80** | -11.6 | ❌ NOT MET — price is overbought, not extreme oversold |
| **bb_meanrev_entry2: BB Width ≥ 10%** | 10.7% | ✅ MET — sufficient room for reversion |
| **bb_meanrev_entry2: ATR(14) ≥ 15** | 22.59 | ✅ MET — adequate volatility |

**Strategy Verdict:** None of the three bb_meanrev entry conditions are met. The price is at 82% of the Bollinger Band range — the exact opposite of the oversold entry the strategy requires. This is a bullish price environment where the mean-reversion strategy is waiting for a dip that hasn't come. No new positions warranted.

#### Exit conditions

| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| **bb_meanrev: Close ≥ Bollinger Middle Band** | 1,221 > 1,180.6 (BB middle) | ⚠️ CAUTION — price already above middle band |
| **bb_meanrev_entry2: Close ≥ BB Middle** | 1,221 > 1,180.6 | ⚠️ CAUTION — middle band already breached |
| **Key observation: RSI > 50 (dual exit)** | RSI 65.4 > 50 | ⚠️ CAUTION — dual exit condition met |

**Strategy Verdict:** If a bb_meanrev position were held from a previous BB Lower entry, the exit conditions are technically met — price is well above the BB middle band and RSI is above 50. However, since no new entry is possible, the relevant assessment is: existing positions should be exited or trimmed on any bounce (dual exit: BB middle OR RSI > 50).

### Signal Summary

**Current Signal: HOLD / STRATEGY-AWAITING**

NG.L exhibits a strongly bullish technical setup with price above all key EMAs, a rock-solid HMM bull regime (96.4% confidence, 30 consecutive days), and strong 1Y return (+60.4%). However, the recommended bb_meanrev strategy is a mean-reversion approach that profits from dips — and the price is currently at the TOP of its Bollinger Band range, not the bottom. RSI at 65.4 is approaching overbought; Williams %R at -11.6 is nowhere near the -80 oversold threshold. This is a "good stock, wrong setup" scenario: the trend is bullish, but the strategy requires oversold conditions that simply don't exist right now. Non-holders should wait for a pullback to the lower Bollinger Band (~1,118) with RSI < 30. Current holders of active positions can consider exiting on the current bounce using the dual-exit signal (BB middle OR RSI > 50).

---

### Aggregate Score

| # | Dimension | Signal | Score (-3.0 to +3.0) | Weight | Weighted |
|---|-----------|--------|-------------|--------|----------|
| 1 | **Trend** | Bullish | +1.5 | 20% | +0.30 |
| 2 | **Momentum** | Cautious | +0.5 | 15% | +0.08 |
| 3 | **Return** | Positive | +1.5 | 15% | +0.23 |
| 4 | **Structure** | Cautious | +0.0 | 15% | +0.00 |
| 5 | **Volatility** | Normal | -0.5 | 10% | -0.05 |
| 6 | **Volume** | Mixed | -0.5 | 10% | -0.05 |
| 7 | **Regime** | Bull | +2.0 | 15% | +0.30 |
| | **AGGREGATE** | | | **100%** | **+0.81** |

**Aggregate Score: +0.81 — BUY (technical), HOLD (strategy-aligned)**

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | WAIT — no entry signal | All 3 bb_meanrev entry conditions not met (price at top of BB, RSI 65.4). Wait for pullback to BB Lower (~1,118) + RSI < 30 + Williams %R < -80 |
| **Current holders** | EXIT on bounce (dual exit) | BB middle band (1,180.6) already breached; RSI > 50. Mean-reversion exit conditions met. Consider trimming 50%+ on current levels |
| **Traders** | AVOID mean-reversion entries | Price at 82% of BB range — wrong side of the mean. Only suitable setup: deep pullback to lower band |

- **Entry (bb_meanrev):** Close ≤ ta_bband_lower (1,117.7) AND RSI(14) < 30 AND Williams %R(14) < -80. Price target: BB middle ~1,181 (6.2% upside from entry).
- **Entry (bb_meanrev_entry2):** Same as above + BB Width ≥ 10% (✅ currently met) + ATR(14) ≥ 15 (✅ currently met).
- **Stop-Loss:** 1,100 (below 52-week low 1,096.5, provides 0.6% buffer for mean-reversion entry)
- **Target:** 1,181 (BB middle band — primary exit), secondary 1,243 (BB upper band for aggressive exit)

### Risk Factors
- **Overbought Conditions:** RSI at 65.4 with Williams %R at -11.6 and CCI at 92.7 — the price is extended. A pullback of 5–10% (to 1,098–1,099) would bring RSI back to oversold levels and create the bb_meanrev entry setup.
- **BB Compression:** BB Width at 10.7% is compressed. While this means room for reversion, it also signals an impending volatility expansion — NG.L has a history of sharp moves (2020: -9%, 2024: -10%). A breakdown below BB lower could accelerate rapidly.
- **Strategy Limitation:** The bb_meanrev strategy is opportunistic and low-frequency (17 trades over 10 years, ~1.7 per year). The strategy may have zero signals for months during strong uptrends (as seen in 2019 and 2021). Patience is required — this is not a "missed opportunity" but the intended behavior of the strategy.
- **GARCH Volatility Elevation:** GARCH forecast at 1.20 and GARCH² at 1.45 indicate elevated near-term volatility risk. A vol spike could widen drawdowns before mean-reversion kicks in.

### When This Signal Is Invalidated
- **Pullback to BB Lower (~1,118) with RSI < 30 and Williams %R < -80** → Signal becomes **BUY** — bb_meanrev entry conditions met, classic mean-reversion setup
- **Price breaks below 1,096.5 (52-week low) with HMM probability shifting to state 1 or 2** → Signal becomes **SELL** — regime breakdown, support invalidated, bear market possible
- **Price holds above 1,261 resistance with volume surge (volume percentile > 80) and RSI > 70** → Signal becomes **BUY** — breakout confirms new uptrend; alternative trend-following approaches may become viable

---

*Report generated: 2026-10-27 | Data point: 2026-10-27 → `2026-10-27` | Data: `data/analysis-data/NG.L.csv` (5,053 rows) | Strategy: `data/reports/strategies/NG.L/20261027.md`*
