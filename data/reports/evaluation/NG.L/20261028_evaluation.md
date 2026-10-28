# Market Situation Evaluation: National Grid (NG.L)

**Date Used:** 2026-10-28
**Ticker:** NG.L (National Grid)
**Price:** 1,237.5p
**Data Range:** 2006-10-30 to 2026-10-28 (5,053 rows)
**Sector:** Utilities
**Strategy Reference:** `data/reports/strategies/NG.L/20261027.md`
**Target Strategy:** `bb_meanrev` (BB Mean Reversion)

---

## Executive Summary

**Signal:** HOLD
**Confidence:** Medium

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🟢 BULLISH | 🟢 High | EMA alignment, SuperTrend +1, +DI 3x -DI, price above all MAs |
| **Momentum** | 🟡 CAUTIOUS | 🟡 Medium | RSI 69.4 near overbought, Williams %R -7.2 extreme, MACD still bullish |
| **Return** | 🟢 POSITIVE | 🟢 High | +10.2% 1m, +7.9% 1y, Alpha +0.36, RS FTSE +11.6% outperformance |
| **Structure** | 🟡 CAUTIOUS | 🟡 Medium | Near Donchian high, no confirmed HH/HL, tight BB = breakout imminent |
| **Volatility** | 🔴 HIGH | 🟢 High | BB Width 0.11% extreme compression, ATR percentile 35% — breakout event likely |
| **Volume** | 🟡 MIXED | 🟡 Medium | OBV rising but volume at 15th percentile — low conviction rally |
| **Regime** | 🟡 NEUTRAL | 🟢 High | HMM State 2 (Volatile) at 91.9%, stable 30+ days, zero flips |
| **Overall** | 🟡 HOLD | 🟡 Medium | Bullish trend intact but extreme volatility reading + volatile regime = no clear new entry |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | 1,237.5p | Near 52-week high, +4.4% above EMA20 |
| 52-Week Range | 1,096.5 – 1,428.5p | 42.5% of range, 13.4% below high |
| P/E (TTM) | N/A | No fundamentals data available for NG.L |
| Dividend Yield | N/A | No fundamentals data available for NG.L |
| Beta (20d) | 0.65 | Low volatility vs FTSE 100 (defensive) |
| RS vs FTSE 100 | +11.57% | Outperforming FTSE 100 over 20-day window |

### Strategy Alignment Summary — `bb_meanrev`

#### Entry conditions (from `bb_meanrev`)

| Strategy Element | Current Value | Alignment |
|-----------------|---------------|-----------|
| Close ≤ Bollinger Lower Band (20, 2) | 1,237.5p vs BB Lower 1,119.8p | ❌ NOT MET (price 10.5% above) |
| RSI(14) < 30 | 69.42 | ❌ NOT MET (near overbought) |
| Williams %R(14) < −80 | −7.18 | ❌ NOT MET (near extreme high) |

**Strategy Entry Verdict:** None of the 3 entry conditions are met. The bb_meanrev strategy requires price to dip to the lower Bollinger Band with deeply oversold momentum — the opposite of current conditions. The stock is trading near its upper Bollinger Band (90th percentile) with elevated momentum across all indicators.

#### Exit conditions (from `bb_meanrev`)

| Strategy Element | Current Value | Alignment |
|-----------------|---------------|-----------|
| Close ≥ Bollinger Middle Band (20-day SMA) | 1,237.5p vs BB Middle 1,185.2p | ✅ MET (price 4.4% above middle) |
| RSI(14) > 50 (dual exit) | 69.42 | ✅ MET (overbought territory) |
| Williams %R > −20 (overbought exit) | −7.18 | ✅ MET (extreme overbought) |

**Strategy Exit Verdict:** All exit conditions are met. If holding a position entered via bb_meanrev, it would have been exited on the way up — the price has already reverted to and exceeded the middle Bollinger Band by 4.4%. This confirms the mean-reversion cycle is complete for this cycle.

#### Strategy Context

bb_meanrev achieved **29.86% return, 0.42 Sharpe, 15.69% max drawdown, 70.6% win rate** over 10 years (17 trades). NG.L's mean-reverting behavior makes this the recommended strategy. However, the strategy's value proposition — capturing panic dips to BB Lower — requires exactly the kind of pullback that is NOT happening today.

The 2026 analysis notes: *"BB Width is extremely tight (0.11%), suggesting compression before the next move."* This is consistent with today's readings.

---

### Aggregate Score

| # | Dimension | Signal | Score |
|---|-----------|--------|-------|
| 1 | **Trend** | 🟢 BULLISH | +2.5 |
| 2 | **Momentum** | 🟡 CAUTIOUS | +0.5 |
| 3 | **Return** | 🟢 POSITIVE | +2.0 |
| 4 | **Structure** | 🟡 CAUTIOUS | +1.0 |
| 5 | **Volatility** | 🔴 HIGH | −1.5 |
| 6 | **Volume** | 🟡 MIXED | −0.5 |
| 7 | **Regime** | 🟡 NEUTRAL (Volatile) | +1.0 |
| | **AGGREGATE** | | **+5.0** |

**Aggregate Score: +5.0 — HOLD**

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | DO NOT ENTER | Price near upper BB with volatile regime — poor risk/reward. Wait for pullback to BB Lower (~1,120p) with oversold momentum. |
| **Current holders** | HOLD | Bullish trend intact, SuperTrend +1, no bearish regime shift. Consider taking partial profits near 1,260p resistance. |
| **Traders** | AVOID | Extremely tight BB (0.11%) = breakout event imminent. Direction uncertain in volatile regime — poor setup for either direction. |

- **Entry:** Wait for price ≤ 1,120p (BB Lower) AND RSI(14) < 30 AND Williams %R < −80
- **Stop-Loss:** 1,104.5p (swing low) or 1,119.8p (BB Lower, whichever breaks first)
- **Target:** 1,185p (BB Middle Band) for mean-reversion target; 1,260p (nearest resistance) for trend continuation

### Risk Factors
- **Extreme BB Compression (0.11% width):** This is among the tightest readings in 20 years of data. A breakout is imminent — direction uncertain. A down-break could trigger a sharp move to 1,120p (−9.5%) or lower.
- **HMM Volatile Regime:** State 2 dominates at 91.9% — the market sees NG.L as unusually volatile. This is atypical for a utility stock and suggests structural change in the stock's behavior.
- **Low-Volume Rally:** Volume at 15th percentile despite strong price gains (+10.2% in 1 month). The rally lacks conviction and could reverse on any negative catalyst.

### When This Signal Is Invalidated
- **Price breaks below 1,187p (nearest support):** → Signal becomes **WAIT** (trend structure weakening)
- **Price breaks below 1,120p (BB Lower):** → Signal could become **BUY** (bb_meanrev entry conditions may start aligning if RSI < 30)
- **HMM regime flips to State 1 (Bear):** → Signal becomes **SELL** (bearish regime confirmed)
- **BB Width expands above 5%:** → Signal becomes **BUY** or **SELL** depending on direction (volatility breakout resolved)

---

*Report generated: 2026-10-28 | Data point: 2026-10-28 → 2026-10-28 | Data: `data/analysis-data/NG.L.csv` (5,053 rows) | Strategy: `data/reports/strategies/NG.L/20261027.md` → Target: `bb_meanrev`*
