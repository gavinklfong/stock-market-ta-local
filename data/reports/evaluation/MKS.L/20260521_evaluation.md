# Market Situation Evaluation: Marks & Spencer (MKS.L)

**Evaluation Date:** 2026-05-21
**Actual Date Used:** 2026-05-21
**Ticker:** MKS.L (Marks & Spencer)
**Price:** 350.8p
**Data Range:** 2006-10-27 to 2026-05-21 (4942 rows)
**Sector:** Retail
**Strategy Reference:** `data/reports/strategies/MKS.L/2026-10-26.md`
**Target Strategy:** `dual_exit_meanrev`

---

## Executive Summary

**Signal:** SELL
**Confidence:** Medium

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🟢 BULLISH | 🟡 Medium | Price above EMA20 (333.53); DI+ > DI−; SuperTrend bullish; but below EMA50/EMA200 |
| **Momentum** | 🟢 BULLISH | 🟢 High | RSI 58.5 rising; MACD histogram +3.49 strong positive divergence; CCI 169.6 overbought |
| **Return** | 🟡 MIXED | 🟡 Medium | 5d (+1.45%) and 10d (+4.08%) positive; 20d (−0.83%) still negative from prior period |
| **Structure** | 🟡 CAUTIOUS | 🟢 High | Recovered from swing low 301.10 to 350.80 (+16.5%); nearest support 344.90; no HH/HL confirmed |
| **Volatility** | 🟡 NORMAL | 🟢 High | ATR at 95th percentile (12.81); volatility expanded sharply from May 19; BB width 13.4% |
| **Volume** | 🟢 BULLISH | 🟡 Medium | CMF +0.14 turning positive; OFI +0.37 strongly positive; volume 60th percentile |
| **Regime** | 🔴 BEAR | 🟢 High | HMM regime 2 (bear/volatile) at 79.98% — improved from 92.6% on May 19 but still dominant |
| **Overall** | 🟠 SELL | 🟡 Medium | Trade #7 already exited per backtest; price at 97.7% BB position; overbought momentum; exit conditions MET |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | 350.8p | 7.3% above May 19 (326.80); 7.8% above trade #7 entry (325.32); at upper BB region |
| 52-Week Range | 301.10 – 411.80 | 74.1% of range — recovering but still 14.8% below 52-week high |
| P/E (TTM) | 28.52 | Elevated — up from 26.57 as price recovered |
| Dividend Yield | 1.08% | Diluted by higher price; income not primary driver |
| Beta (20d) | 1.59 | Very high beta — amplifies both gains and losses vs FTSE 100 |
| RS vs FTSE 100 | +3.36 | Outperforming the FTSE 100 over 20 days |

### Strategy Alignment Summary — `dual_exit_meanrev`

#### Entry conditions (from `dual_exit_meanrev`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| Close ≤ Bollinger Band Lower (20, 2) | 350.80 vs BB Lower 307.73 | ❌ NOT MET (price is 43.07p / 14.0% above BB Lower) |
| RSI(14) < 35 | 58.52 | ❌ NOT MET (RSI in overbought-approaching territory) |
| CCI(20) < −100 | 169.62 | ❌ NOT MET (CCI deeply positive, not negative) |
| Strategy context | Price surged from May 12 low (308.90) to 350.80 (+13.6%); BB %B at 97.7% near upper band | ❌ NOT MET — all entry conditions are opposite of current state |

**Strategy Entry Verdict:** All 3 entry conditions are NOT MET. The stock has moved dramatically away from oversold territory and is now near the upper Bollinger Band (BB %B = 97.7%). The RSI has jumped from 45.7 on May 19 to 58.5, and CCI has swung from −5.6 to +169.6. An entry would require a pullback to BB Lower (~307.73) with RSI < 35 and CCI < −100 — conditions not remotely present.

#### Exit conditions (from `dual_exit_meanrev`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| Close ≥ BB Middle Band (20-day MA) | 350.80 vs BB Middle 329.76 | ✅ MET (price is 21.04p / 6.38% above BB middle) |
| Close < 3-day high − 3×ATR trail | 3-day high ≈ 354.30 (May 21); 3×ATR = 38.43; trail = 315.87 | ❌ NOT MET (price 350.80 >> trail 315.87) |
| Strategy context | Trade #7 exited at 348.15 on May 20 per backtest; current price 350.80 (+6.81% from entry) | ✅ CONFIRMED — exit already triggered by BB Middle on May 20/21 |

**Strategy Exit Verdict:** Primary exit condition (Close ≥ BB Middle) is MET — price at 350.80 is 6.38% above the BB Middle at 329.76. Per the backtest trade log, trade #7 (entry 2026-04-29 @ 325.32) exited at 348.15 on 2026-05-20 (+6.81%) when the BB Middle exit triggered. The price has continued slightly higher to 350.80 on May 21. The ATR trailing stop (315.87) is far below and not a concern. **For any remaining position holders, the exit signal has been fully triggered and profit has been realized.**

### Signal Summary

**Current Signal: SELL / TRADE ALREADY EXITED**

The `dual_exit_meanrev` strategy has already completed trade #7. Entry was on 2026-04-29 @ 325.32 and exit was triggered on 2026-05-20 @ 348.15, realizing a +6.81% return over 21 days. As of 2026-05-21, the price has moved to 350.80 (+7.81% from entry), but the trade has already closed per the backtest engine. The BB Middle exit condition is firmly MET (price 6.38% above), and all entry conditions are the exact opposite of current state. No new entry signal is present — a fresh entry would require a pullback to BB Lower (~307.73) with RSI < 35 and CCI < −100, which is not indicated at current overbought levels.

---

### Aggregate Score

| # | Dimension | Signal | Score (-3.0 to +3.0) | Weight | Weighted |
|---|-----------|--------|-------------|--------|----------|
| 1 | **Trend** | BULLISH | +1.0 | 15% | +0.150 |
| 2 | **Momentum** | BULLISH | +1.5 | 15% | +0.225 |
| 3 | **Return** | MIXED | +0.5 | 10% | +0.050 |
| 4 | **Structure** | CAUTIOUS | +0.5 | 10% | +0.050 |
| 5 | **Volatility** | NORMAL | +0.0 | 10% | +0.000 |
| 6 | **Volume** | BULLISH | +0.5 | 10% | +0.050 |
| 7 | **Regime** | BEAR | −2.0 | 20% | −0.400 |
| | **AGGREGATE** | | | **100%** | **+0.125** |

**Aggregate Score: +0.13 — SELL (trade exited)**

*Note: The aggregate score is slightly positive (+0.13) reflecting the recent bullish momentum and price recovery, but the HOLD-to-SELL signal reflects that the trade has already exited per `dual_exit_meanrev` rules. A positive aggregate would suggest a potential re-entry opportunity ONLY if a pullback occurs to reset entry conditions.*

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | DO NOT ENTER | All entry conditions failed; RSI 58.5 / CCI 169.6 overbought; price at upper BB |
| **Current holders** (post-exit) | NO POSITION — TRADE COMPLETE | Trade #7 already exited at 348.15 on May 20 (+6.81%); no position to manage |
| **Traders** | WAIT FOR PULLBACK | No actionable signal; wait for pullback to BB Lower (~307.73) with RSI < 35 and CCI < −100 for a fresh entry |

- **Entry:** Wait for Close ≤ 307.73 (BB Lower) AND RSI < 35 AND CCI < −100 — all far from met; next opportunity requires ~12% pullback
- **Stop-Loss:** 315.87 (3-day high − 3×ATR trail) — if a new entry were taken, this would be the trailing stop
- **Target:** 329.76 (BB Middle) — primary exit target; if price were to pull back and re-enter, this is the first profit target

### Risk Factors
- **Regime still bearish (79.98% HMM probability):** Despite the strong bounce, the regime model remains in state 2 (bear/volatile) at 80% probability. Any rally may be short-lived — mean-reversion strategies are designed for exactly this environment.
- **Overbought momentum (RSI 58.5, CCI 169.6):** The sharp 2-day surge (+7.3% from May 19 to May 21) has created overbought conditions. A pullback toward BB Middle (329.76) or BB Lower (307.73) is statistically likely.
- **ATR expansion (95th percentile):** Volatility has surged from the 5th percentile on May 19 to the 95th percentile on May 21. ATR-based trailing stops need time to adjust, increasing gap risk.

### When This Signal Is Invalidated
- **Price breaks above swing high 374.85** → Signal becomes WAIT (trend change would invalidate mean-reversion premise; trend-riding strategy would be more appropriate)
- **HMM regime shifts to state 0 (bull) with >50% probability** → Signal becomes WAIT/BUY (regime confirmation for sustained recovery; entry conditions could trigger on a pullback within a bull regime)
- **Price pulls back to BB Lower (~307.73) with RSI < 35 and CCI < −100** → Signal becomes BUY for new entry (fresh oversold setup for `dual_exit_meanrev`)

---

*Report generated: 2026-05-21 | Data point: 2026-05-21 → 2026-05-21 | Data: `data/analysis-data/MKS.L.csv` (4942 rows) | Strategy: `data/reports/strategies/MKS.L/2026-10-26.md` → Target: `dual_exit_meanrev`*
