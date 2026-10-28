# Market Situation Evaluation: Legal & General (LGEN.L)

**Date Used:** 2026-10-28
**Ticker:** LGEN.L (Legal & General)
**Price:** 303.2p
**Data Range:** 2006-10-30 to 2026-10-28 (5,053 rows)
**Sector:** Insurance
**Strategy Reference:** `data/reports/strategies/LGEN.L/2026-10-23.md`
**Target Strategy:** `lgen_crash_protected_upper`

---

## Executive Summary

**Signal:** HOLD
**Confidence:** High

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🟢 BULLISH | 🟡 Medium | EMA20>EMA50>EMA200 bullish alignment, SuperTrend UP, but ADX 12.8 weak trend, MA50 slope negative |
| **Momentum** | 🟢 BULLISH | 🟢 High | RSI 63.1 overbought-leaning, MACD strongly bullish, CCI 125 overbought, Williams %R -14.8 strong |
| **Return** | 🟡 MIXED | 🟢 High | +26.0% 1Y, +20.5% 6M strong; but +3.0% 1M, +1.1% 3M — recent rally has slowed |
| **Structure** | 🟡 CAUTIOUS | 🟡 Medium | Price near swing high 308.5, resistance only 2.0% away at 309.3; no HH/HL or LH/LL patterns |
| **Volatility** | 🔴 HIGH | 🟢 High | BB %B 88.7% — price at upper band; BB width 8.0% elevated; GARCH vol 1.06 elevated |
| **Volume** | 🟢 BULLISH | 🟡 Medium | CMF +0.14 positive, OFI +0.11 positive, OBV slope 14d/7d strongly positive; but volume only 20th percentile |
| **Regime** | 🟡 NEUTRAL | 🟡 Medium | HMM State 0 (bull) at 61.9%, State 2 (volatile) at 37.8% — bull is dominant but volatile regime close |
| **Overall** | 🟡 HOLD | 🟢 High | 3 bullish, 2 cautious/mixed, 1 high-vol; strategy entry conditions NOT met (mean-reversion at highs) |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | 303.2p | Near 52-week high (318.1p), 95.3% of range — mean-reversion entry zone NOT in play |
| 52-Week Range | 217.2 – 318.1p | Upper end of range — not oversold |
| P/E (TTM) | N/A | Null in current CSV — strategy report noted P/E data unavailable for LGEN.L |
| Dividend Yield | N/A | Null in current CSV — strategy report noted ~8.4% yield (exceptionally high) |
| Beta (20d) | 0.868 | Lower volatility than FTSE 100 (defensive for insurance) |
| RS vs FTSE 100 | 2.84 | Slight outperformance vs FTSE 100 |

### Strategy Alignment Summary — `lgen_crash_protected_upper`

#### Entry conditions (from `lgen_crash_protected_upper`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| Price ≤ BB Lower (20, 2) | 303.2 > 282.3 ❌ | ❌ NOT MET — price at upper end of BB, far from lower band |
| RSI(14) < 35 | 63.1 ❌ | ❌ NOT MET — RSI at 95th percentile, overbought |
| CCI(20) < -100 | 125.0 ❌ | ❌ NOT MET — CCI strongly positive, extreme bullish |
| GARCH vol NOT rising | 1.056 — unknown vs yesterday | ⚠️ CAUTION — cannot verify without yesterday's value, but current level elevated |
| Crash filter: 20d return > -10% | ROC(20) +3.8% > -10% ✅ | ✅ MET — no crash conditions |

**Strategy Entry Verdict:** 1 of 5 entry conditions MET. The strategy is a **dip-buying mean-reversion** strategy designed to enter when LGEN.L is oversold (price at BB Lower, RSI < 35, CCI < -100). Current conditions are the exact opposite — the stock is at the TOP of its Bollinger Band range with RSI at 63 and CCI at 125. **This is a NOT a buying opportunity for this strategy.** The strategy would never fire an entry signal at current levels.

#### Exit conditions (from `lgen_crash_protected_upper`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| Price ≥ BB Upper (20, 2) | 303.2 < 305.9 ✅ | ✅ CONFIRMED (not triggered — price near but not above BB Upper) |

**Strategy Exit Verdict:** No exit condition triggered for an existing position. Price (303.2p) is approaching BB Upper (305.9p) and is 88.7% of the way through the band. If the price touches or exceeds 305.9p, the strategy's exit fires — capturing the full mean-reversion range.

{2–3 sentence narrative explaining the overall signal, who should act, and for whom}

**Narrative:** LGEN.L is trading near the top of its Bollinger Band range with strong momentum — the exact opposite of where the recommended `lgen_crash_protected_upper` strategy wants to enter. This is a **classic mean-reversion trap zone**: buying here would mean entering at the exit, not the entry. The strategy's entry criteria (BB Lower + RSI < 35 + CCI < -100) are nowhere near being met. For current holders, the strategy doesn't have an exit triggered yet (price hasn't reached BB Upper), so holding is appropriate. For non-holders, the recommendation is clear: **do not enter** — wait for a pullback to the BB Lower band with RSI < 35 and CCI < -100 before considering entry.

---

### Aggregate Score

| # | Dimension | Signal | Score |
|---|-----------|--------|-------|
| 1 | **Trend** | 🟢 BULLISH | +1.5 |
| 2 | **Momentum** | 🟢 BULLISH | +2.5 |
| 3 | **Return** | 🟡 MIXED | -1.0 |
| 4 | **Structure** | 🟡 CAUTIOUS | 0.0 |
| 5 | **Volatility** | 🔴 HIGH | -1.5 |
| 6 | **Volume** | 🟢 BULLISH | +1.0 |
| 7 | **Regime** | 🟡 NEUTRAL | +0.0 |
| | **AGGREGATE** | | **+2.5** |

**Aggregate Score: +2.5 — HOLD**

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | DO NOT ENTER | Strategy entry conditions 4/5 NOT MET; price at BB Upper, RSI overbought, CCI strongly positive — entering here is buying the top of a mean-reversion range |
| **Current holders** | HOLD — monitor for BB Upper exit | Price approaching BB Upper (305.9p); if hit, strategy exit fires for profit capture |
| **Traders** | AVOID — mean-reversion strategy not active at these levels | LGEN.L is range-bound; at current overbought levels, a pullback to BB Lower is more likely than a breakout |

- **Entry:** Wait for pullback to BB Lower (282.3p) AND RSI < 35 AND CCI < -100 — conditions not met, next entry signal may be weeks/months away
- **Stop-Loss:** 296.8 (EMA20) — if price breaks below 20-day EMA, mean-reversion uptrend may be broken
- **Target:** 305.9 (BB Upper, 0.9% above current) → 318.1 (52-week high, 4.9% above) if momentum sustains

### Risk Factors
- **Overbought at BB Upper (88.7% %B):** LGEN.L is a mean-reverting stock by nature (weak trend, ADX avg 21.6). Price at the top of the Bollinger Band historically tends to pull back — the probability of a mean-reversion move to BB Middle (~294p, 3.1% down) or BB Lower (~282p, 7.0% down) is elevated
- **RSI at 95th percentile:** RSI of 63.1 with a z-score of 1.41 and percentile of 95 indicates this is near the top of LGEN.L's historical RSI range — mean-reversion to lower RSI levels is statistically likely
- **Regime split:** HMM shows 61.9% bull / 37.8% volatile — while bull is dominant, the volatile regime is close enough that a regime shift could accelerate a pullback

### When This Signal Is Invalidated
- **Price reaches BB Upper (305.9p)** → Signal upgrades to BUY for current holders (strategy exit fires, capturing profit)
- **HMM State 1 (bear) probability exceeds 50%** → Signal becomes SELL (regime shift, trend may be broken)
- **Price closes below EMA20 (296.8p)** → Signal becomes SELL (mean-reversion uptrend broken, trend reversal)
- **Price drops to BB Lower (282.3p) with RSI < 35** → Signal upgrades to BUY for non-holders (strategy entry conditions met)

---

*Report generated: 2026-10-28 | Data point: 2026-10-28 → 2026-10-28 | Data: `data/analysis-data/LGEN.L.csv` (5,053 rows) | Strategy: `data/reports/strategies/LGEN.L/2026-10-23.md` → Target: `lgen_crash_protected_upper`*
