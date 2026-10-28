# Market Situation Evaluation: Standard Chartered (STAN.L)

**Date Used:** 2026-10-28
**Ticker:** STAN.L (Standard Chartered)
**Price:** 2,068p
**Data Range:** 2006-10-30 to 2026-10-28 (5,053 rows)
**Sector:** Financial Services
**Strategy Reference:** `data/reports/strategies/STAN.L/20261022.md`
**Target Strategy:** `trend_momentum`

---

## Executive Summary

**Signal:** SELL
**Confidence:** Medium

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🟡 CAUTIOUS | 🟢 High | Price below EMA20/50 but above EMA200 — pullback in longer uptrend; MA20/50 slopes negative; SuperTrend still UP but trend=-1 |
| **Momentum** | 🔴 BEARISH | 🟢 High | RSI 44 below 50, MACD negative and below signal, ROC -10% — all momentum indicators negative |
| **Return** | 🟡 MIXED | 🟢 High | +36.4% 1Y strong but -11.2% 1M and -6.7% 3M; alpha -0.58 negative |
| **Structure** | 🟡 CAUTIOUS | 🟡 Medium | Price below nearest support (2,091p); no HH/HL patterns; swing low at 2,090p |
| **Volatility** | 🔴 HIGH | 🟢 High | ATR 95th percentile (extreme), GARCH vol 2.1 elevated, BB %B 37% (lower half of bands) |
| **Volume** | 🔴 BEARISH | 🟡 Medium | CMF -0.11 (money outflow), OFI -0.63 (order flow bearish), volume at 80th percentile = selling pressure |
| **Regime** | 🟡 NEUTRAL/VOLATILE | 🟡 Medium | HMM State 2 (volatile) at 65.6% dominant but declining from 87%; State 0 (bull) rising from 11% to 31.5% — transitional |
| **Overall** | 🔴 SELL | 🟡 Medium | 0 bullish, 2 bearish, 2 cautious/bearish, 1 mixed, 2 neutral/volatile — no entry conditions met for trend strategy |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | 2,068p | Sharp decline from 5-week high of 2,338p on Sep 17 (-11.5%); recovered from Oct 23 low of 1,959p (+5.6%) |
| 52-Week Range | 1,472 – 2,364p | 66.8% of range from low — well off the 52-week high, in the middle of the range |
| P/E (TTM) | N/A | Null in current CSV — no fundamentals in data |
| Dividend Yield | N/A | Null in current CSV — Standard Chartered is a banking stock with typical dividend yield |
| Beta (20d) | 1.83 | High — 1.8x FTSE 100 volatility (amplified moves) |
| RS vs FTSE 100 | 19.34 | Positive RS despite drawdown — still outperforming FTSE 100 relatively |

### Strategy Alignment Summary — `trend_momentum`

#### Entry conditions (from `trend_momentum`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| EMA20 > EMA50 > EMA200 (confirmed uptrend) | 2,100 < 2,150 > 1,979 ❌ | ❌ NOT MET — EMA20 has crossed below EMA50 (death cross on short/medium term); only EMA200 alignment holds |
| RSI(14) > 55 (momentum positive) | 44.1 ❌ | ❌ NOT MET — RSI below 50, momentum is negative, nowhere near 55 threshold |
| MACD Line > Signal (momentum direction) | -57.2 vs -50.5 ❌ | ❌ NOT MET — MACD below signal, momentum turned bearish |
| CMF(20) > 0 (volume flow positive) | -0.11 ❌ | ❌ NOT MET — money flowing out, negative volume confirmation |

**Strategy Entry Verdict:** 0 of 4 entry conditions MET. The trend_momentum strategy requires ALL four conditions to fire — confirmed uptrend alignment, positive momentum (RSI>55), bullish MACD direction, and positive volume flow. Current conditions are the exact opposite of what this strategy seeks. **This strategy would never enter at current levels.** The stock is in a pullback phase within a larger uptrend, and all momentum/volume signals are negative.

#### Exit conditions (from `trend_momentum`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| RSI(14) < 50 (momentum weakening) | 44.1 ✅ | ✅ TRIGGERED — momentum has weakened below the 50 threshold |
| MACD Line < Signal (momentum turned bearish) | -57.2 < -50.5 ✅ | ✅ TRIGGERED — MACD is below signal, bearish momentum confirmed |

**Strategy Exit Verdict:** Both exit conditions are triggered. For any existing position entered under this strategy, the current conditions would signal an exit — momentum has deteriorated (RSI < 50) and MACD has turned bearish (MACD < Signal). The combination of both conditions firing simultaneously is a strong sell signal for trend-following strategies, indicating the momentum that fueled the uptrend has been exhausted.

0/4 entry conditions met, 2/2 exit conditions triggered. The trend_momentum strategy would have exited this position and is looking for conditions to re-enter (all 4 entry conditions must be satisfied again). Current market structure shows a deep pullback from the September peak that has damaged the short-term trend alignment.

For non-holders: The strategy would never fire an entry signal here — all conditions are unmet. For holders: Both exit conditions are triggered, signaling the trend has broken in the short term. However, the long-term trend (EMA200) remains intact and the volatile regime is slowly transitioning toward bullish (bull probability rising from 11% to 31.5%), which suggests this pullback may eventually offer a re-entry opportunity if the trend recovers.

---

### Aggregate Score

| # | Dimension | Signal | Score |
|---|-----------|--------|-------|
| 1 | **Trend** | 🟡 CAUTIOUS | -1.0 |
| 2 | **Momentum** | 🔴 BEARISH | -2.0 |
| 3 | **Return** | 🟡 MIXED | -0.5 |
| 4 | **Structure** | 🟡 CAUTIOUS | -1.0 |
| 5 | **Volatility** | 🔴 HIGH | -1.5 |
| 6 | **Volume** | 🔴 BEARISH | -1.0 |
| 7 | **Regime** | 🟡 NEUTRAL/VOLATILE | -0.5 |
| | **AGGREGATE** | | **-7.5** |

**Aggregate Score: -7.5 — SELL**

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | DO NOT ENTER — 0/4 entry conditions for trend_momentum; all momentum/volume signals negative | Short-term trend broken (EMA20 < EMA50), RSI 44 below 50, MACD bearish, CMF negative; wait for trend alignment to recover |
| **Current holders** | EXIT — both trend_momentum exit conditions triggered | RSI < 50 AND MACD < Signal both fire; short-term trend broken; hold only long-term conviction above EMA200 (1,979p) |
| **Traders** | AVOID — high vol + bearish momentum + volatile regime = whipsaw risk | Beta 1.8x amplifies moves; ATR at 95th percentile means wide swings; thin trend structure increases risk of false breakouts |

- **Entry (future):** Re-evaluate when EMA20 > EMA50 > EMA200 (trend alignment restored) AND RSI > 55 AND MACD > Signal AND CMF > 0 — none of these bullish conditions are currently met. Watch for RSI to stabilize above 50 and MACD to cross above signal as early signs of momentum recovery.
- **Stop-Loss (for holders still considering):** 1,979 (EMA200, 4.3% below) — if price breaks below the 200-day EMA, the long-term uptrend is broken and the thesis fails. Secondary support at 1,920 (Donchian Lower).
- **Target (bounce):** 2,100 (EMA20, 1.6% above), 2,150 (EMA50, 3.9% above). If momentum recovers, 2,300 (Donchian Upper area, 11% above). However, bounce quality will be questionable without volume confirmation (CMF must turn positive).

### Risk Factors
- **Short-term trend broken (EMA20 < EMA50):** The short/medium-term EMA alignment that defines the uptrend has been damaged. EMA20 at 2,100 has fallen below EMA50 at 2,150 — a bearish death cross on these timeframes. This is the core structural change that invalidates the trend_momentum entry thesis.
- **Extreme volatility (ATR 95th percentile):** ATR is at the 95th percentile of its historical range, and GARCH volatility is 2.1 — both indicate an unusually turbulent trading environment. Combined with Beta 1.8x, this means STAN.L could swing 5-10p in a single day. Trading in this environment carries elevated risk of stop-outs and whipsaw price action.
- **Volatile regime with ambiguous transition:** HMM State 2 (volatile) at 65.6% is dominant but declining (from 87% on Oct 22), while State 0 (bull) is rising (31.5% from 11%). This transitional phase is inherently uncertain — the market could continue falling (State 1/bear confirmation) or recover (State 0/bull confirmation). The 31.5% bull probability is encouraging for long-term holders but insufficient for entry signals.

### When This Signal Is Invalidated
- **EMA20 > EMA50 > EMA200 AND RSI > 55 AND MACD > Signal AND CMF > 0** → Signal upgrades to BUY (all 4 trend_momentum entry conditions met — trend and momentum fully aligned)
- **Price closes above EMA50 (2,150p) with rising volume** → Signal becomes WAIT (short-term trend stabilizing, but need more confirmation)
- **Price closes below EMA200 (1,979p)** → Signal becomes STRONG SELL (long-term uptrend broken, trend thesis fails entirely)

---

*Report generated: 2026-10-28 | Data point: 2026-10-28 → 2026-10-28 | Data: `data/analysis-data/STAN.L.csv` (5,053 rows) | Strategy: `data/reports/strategies/STAN.L/20261022.md` → Target: `trend_momentum`*