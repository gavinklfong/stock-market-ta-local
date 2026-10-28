# Market Situation Evaluation: Rolls-Royce Holdings (RR.L)

**Date Used:** 2026-10-28
**Ticker:** RR.L (Rolls-Royce Holdings)
**Price:** 1,263p
**Data Range:** 2006-10-30 to 2026-10-28 (5,052 rows)
**Sector:** Aerospace & Defence
**Strategy Reference:** `data/reports/strategies/RR.L/2026-10-28.md`
**Target Strategy:** `bb_breakout`

---

## Executive Summary

**Signal:** SELL
**Confidence:** High

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🔴 BEARISH | 🟢 High | Price below all EMAs (EMA20: 1,330, EMA50: 1,391, EMA200: 1,327); SuperTrend -1 (bearish); MA20/MA50 slopes both negative; ADX 21.7 — downtrend confirmed |
| **Momentum** | 🔴 BEARISH | 🟢 High | RSI 37.4 (oversold), MACD -57.5 below signal -47.2 (bearish cross), histogram -10.4 (widening negative), ROC -13.6%, CCI -99.5 (near extreme), Williams %R -74.4 (oversold) |
| **Return** | 🟡 MIXED | 🟢 High | +8.9% 1Y positive but -14.7% 1M and -13.7% 3M sharp decline; alpha -0.75 negative; beta 1.29 amplifies downside |
| **Structure** | 🔴 BEARISH | 🟢 High | Price below nearest support (1,424p); nearest support broken (1,405 swing low breached); no HH/HL patterns; Aroon Down 88 >>> Aroon Up 64 |
| **Volatility** | 🔴 HIGH | 🟢 High | ATR 70th percentile (elevated), GARCH vol 3.47 extreme (vs ~1.0 baseline), BB %B 24.1% (lower quartile), HV rising 44.6%, Parkinson vol 48.4% |
| **Volume** | 🔴 BEARISH | 🟡 Medium | CMF -0.11 (money outflow), OFI +0.51 (anomalous — short-term order flow slightly positive despite selling), volume at 5th percentile (capitulation-level low volume = no buying interest), OBV slope -7d negative |
| **Regime** | 🔴 BEAR | 🟢 High | HMM State 1 (bear) at 72.4% — sharp transition from State 2 (volatile) at 65% on Oct 22 to bear state at 72.4% on Oct 28; bear regime probability rising rapidly |
| **Overall** | 🔴 SELL | 🟢 High | 0 bullish, 4 bearish, 1 mixed, 1 bear — all momentum/volume/trend signals negative; regime shifted bearish; BB Breakout entry conditions not met |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | 1,263p | Sharp decline from 5-week high of 1,478p on Oct 12 (-14.5%); dropped to 1,164p on Oct 23 (all-time low in recent period), now recovering to 1,263p (+8.5% from low) |
| 52-Week Range | 990 – 1,586p | 72.9% of range from low; well off the 52-week high; price in lower-middle of range |
| P/E (TTM) | N/A | Null in current CSV — RR.L has volatile earnings due to turnaround cycle; strategy report shows historical P/E range 4.9 to 196.3 |
| Dividend Yield | N/A | Null in current CSV — RR.L is transitioning back to dividend payments post-turnaround |
| Beta (20d) | 1.29 | Higher than FTSE 100 — 1.3x benchmark volatility amplifies both upside and downside |
| RS vs FTSE 100 | 11.81 | Positive RS — despite the selloff, RR.L still relatively outperforming FTSE 100 on a 20d basis |

### Strategy Alignment Summary — `bb_breakout`

**Strategy Logic:** Enter when price closes above Bollinger Band Upper with rising volatility and positive momentum. Exit when price falls below BB Middle or MACD turns bearish. Results: 19.59% return, 1.44 Sharpe, 4.22% MaxDD, 15.18 Profit Factor, 66.7% win rate, 6 trades.

#### Entry conditions (from `bb_breakout`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| Close > Bollinger Band Upper (20, 2) | 1,263 vs 1,515.8 ❌ | ❌ NOT MET — price 16.6% below BB Upper; price is actually in the lower quartile of BB bands (%B 24.1%) |
| ATR(14) rising (current > previous) | 55.49 — need prior bar | ⚠️ CAUTION — ATR elevated at 70th percentile; likely elevated but cannot confirm directionality without prior bar data |
| Historical volatility rising | HV(20) = 0.446, rising | ✅ MET — HV at 44.6% of max, described as rising in the recent context |
| ROC(20) > 0 (positive momentum) | -13.59% ❌ | ❌ NOT MET — strongly negative momentum; price declining 13.6% over 20 days |

**Strategy Entry Verdict:** 1 of 4 entry conditions met (rising HV), 2 definitively NOT MET, 1 uncertain. The `bb_breakout` strategy is fundamentally a breakout-long strategy that requires price to be breaking ABOVE the Bollinger Band Upper — the exact opposite of what is happening. Current price (1,263) is in the lower 24% of the Bollinger Band. The strategy would never fire an entry signal here. The only condition that could potentially be met is rising volatility, but without the other entry filters (price breakout + positive momentum), this alone is insufficient. **This strategy is not active and would not generate an entry.**

#### Exit conditions (from `bb_breakout`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| Close < Bollinger Band Middle (20-period SMA) | 1,263 < 1,349.2 ✅ | ✅ TRIGGERED — price is 6.3% below BB Middle; the price has been below the BB Middle since early October |
| MACD line < signal line (bearish cross) | -57.5 < -47.2 ✅ | ✅ TRIGGERED — MACD is below signal with a widening negative histogram (-10.4); bearish momentum confirmed |

**Strategy Exit Verdict:** Both exit conditions are triggered. For any position held under the `bb_breakout` strategy, the current conditions would signal an exit. The BB Middle cross is a key structural breakdown — price has fallen well below the 20-period SMA (1,349), confirming the loss of the short-term uptrend. Combined with the MACD bearish cross (MACD line -57.5 below signal -47.2), both exit mechanisms are firing simultaneously. This is a strong confirmation that the strategy's trend has broken and any remaining position should be exited.

The most recent `bb_breakout` trade entered on 2026-08-03 at 1,508.31 and exited on 2026-08-19 at 1,517.88 (+0.43%). That trade is complete. The strategy has not re-entered since the price has been falling below BB Middle since early October.

{2–3 sentence narrative explaining the overall signal, who should act, and for whom}

**Bottom line:** RR.L is in a sharp downtrend — down 14.5% from its October 12 peak and transitioning from a volatile regime (65%) into a confirmed bear regime (72.4%). The `bb_breakout` strategy, which is the recommended strategy for this stock, has both exit conditions firing and no entry conditions met. For non-holders: this is not an entry opportunity — the stock needs to show signs of stabilization before any breakout strategy could consider entry. For holders: the bear regime confirmation and broken trend structure suggest risk management is warranted. For traders: the high volatility (ATR 70th percentile, GARCH 3.47) creates wide swings that could offer short opportunities but carry significant whipsaw risk.

---

### Aggregate Score

| # | Dimension | Signal | Score |
|---|-----------|--------|-------|
| 1 | **Trend** | 🔴 BEARISH | -3.0 |
| 2 | **Momentum** | 🔴 BEARISH | -2.0 |
| 3 | **Return** | 🟡 MIXED | -1.0 |
| 4 | **Structure** | 🔴 BEARISH | -2.0 |
| 5 | **Volatility** | 🔴 HIGH | -1.5 |
| 6 | **Volume** | 🔴 BEARISH | -1.5 |
| 7 | **Regime** | 🔴 BEAR | -2.0 |
| | **AGGREGATE** | | **-13.0** |

**Aggregate Score: -13.0 — SELL**

---

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | DO NOT ENTER — 1/4 `bb_breakout` entry conditions met (rising HV only); price below BB Middle, negative momentum across all indicators | Down 14.5% from Oct 12 high; bear regime (72.4%) just confirmed; wait for price to reclaim BB Middle (1,349) and MACD to turn positive before considering entry |
| **Current holders** | REDUCE / EXIT — both `bb_breakout` exit conditions triggered; bear regime confirmed; price recovering from Oct 23 low (1,164) but trend remains broken | Short-term bounce from 1,164 to 1,263 (+8.5%) may offer an exit opportunity; if holding for longer-term recovery, set stop below 1,164 (Oct 23 low) |
| **Traders** | CAUTION — high vol + bear regime = wide swings in both directions; short positions aligned with trend have better odds | GARCH vol 3.47 extreme; ATR 70th percentile; potential for sharp bounces (RSI 37.4 approaching oversold) but downtrend dominates; if shorting, use tight stops above 1,330 (EMA20) |

- **Entry (future):** Re-evaluate when price closes above BB Middle (1,349) AND MACD turns positive (line > signal) AND ROC(20) turns positive — none of these conditions are currently met. A more aggressive entry signal would be a `bb_breakout` setup: price closing above BB Upper (1,516) with rising ATR and rising HV — this would require a significant rally from current levels (~20% move).
- **Stop-Loss (for holders still considering):** 1,164 (Oct 23 low) — a break below this level would signal further downside, potentially toward the 52-week low area at 990p.
- **Target (bounce):** 1,330 (EMA20, 5.3% above), 1,349 (BB Middle, 6.8% above), 1,405 (swing low/support area, 11.3% above). If momentum recovers, 1,478 (Oct 12 high, 17.1% above). However, any bounce is likely to face strong resistance at these levels given the recent breakdown.

### Risk Factors
- **Bear regime just confirmed:** The HMM model shifted from State 2 (volatile, 65% on Oct 22) to State 1 (bear, 72.4% on Oct 28) in just 5 trading days. This rapid regime transition indicates a fundamental change in market dynamics. Historically, once the bear regime is established, it tends to persist until clear signs of reversal emerge (rising bull probability, price reclaiming EMA200).
- **Extreme GARCH volatility (3.47):** The GARCH volatility forecast is 3.47, which is well above normal levels (baseline ~1.0). Combined with RR.L's already high annualized volatility of 41.34%, this means extreme daily swings are possible. A 50p+ single-day move is not unusual in this environment. This creates both risk and opportunity — directional bets can move fast in either direction.
- **Volume at 5th percentile:** Trading volume is at the 5th percentile, indicating extremely low participation. Low-volume selling is often a capitulation signal (sellers exhausted), but it also means there is no buying interest to provide support. A volume spike is needed to confirm any reversal — without it, any bounce may be shallow and short-lived.

### When This Signal Is Invalidated
- **Price closes above BB Middle (1,349) AND MACD turns positive (line > signal) AND RSI crosses above 50** → Signal upgrades to WAIT (early signs of stabilization; need more confirmation for BUY)
- **Price closes above EMA20 (1,330) on rising volume (volume percentile > 50%) AND HMM State 0 (calm) or State 2 (volatile) probability rises above 60%** → Signal becomes BUY (trend reversal confirmed with volume and regime confirmation)
- **Price closes below 1,164 (Oct 23 low)** → Signal becomes STRONG SELL (break of recent swing low confirms bear market continuation; downside target shifts to 52-week low area at 990p)

---

*Report generated: 2026-10-28 | Data point: 2026-10-28 → 2026-10-28 | Data: `data/analysis-data/RR.L.csv` (5,052 rows) | Strategy: `data/reports/strategies/RR.L/2026-10-28.md` → Target: `bb_breakout`*
