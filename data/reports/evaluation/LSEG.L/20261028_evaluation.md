# Market Situation Evaluation: London Stock Exchange Group (LSEG.L)

**Date Used:** 2026-10-28
**Ticker:** LSEG.L (London Stock Exchange Group)
**Price:** 9,186p
**Data Range:** 2006-10-30 to 2026-10-28 (5,053 rows)
**Sector:** Financial Services
**Strategy Reference:** `data/reports/strategies/LSEG.L/2026-10-23.md`
**Target Strategy:** `VWAP + Regime Filter`

---

## Executive Summary

**Signal:** HOLD
**Confidence:** Medium

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🟢 BULLISH | 🟢 High | EMA20>EMA50, SuperTrend UP, ADX 23.7 with +DI 31.5 >> -DI 16.6 |
| **Momentum** | 🟢 BULLISH | 🟢 High | RSI 61.7 healthy uptrend, MACD bullish, ROC +12.6% strong |
| **Return** | 🟡 MIXED | 🟢 High | +12.3% 1M but -3.8% 6M, -3.0% 1Y — recent rally vs longer-term weakness |
| **Structure** | 🟡 CAUTIOUS | 🟡 Medium | No BOS/CHoCH signals, resistance only 3.7% away at 9,530p |
| **Volatility** | 🔴 HIGH | 🟢 High | ATR 85th percentile, BB width 19.5% — elevated, GARCH vol 2.47 extreme |
| **Volume** | 🟡 MIXED | 🟡 Medium | CMF +0.04 marginally positive, OFI slightly negative, volume only 20th percentile |
| **Regime** | 🟡 NEUTRAL | 🔴 Low | HMM State 2 (volatile) at 44%, but State 0 (bull) 29% and State 1 (bear) 27% — no dominant regime |
| **Overall** | 🟡 HOLD | 🟡 Medium | 2 bullish, 1 bullish, 2 mixed/cautious, 1 high-vol, 1 uncertain regime |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | 9,186p | Down from Oct 23 high of 9,510p, pulled back 3.4% from recent peak |
| 52-Week Range | 6,684 – 10,140p | 68.6% of range — mid-to-upper range, not at extreme |
| P/E (TTM) | N/A | Null in current CSV — data may have changed since strategy report (P/E ~240 in 2026-10-23 report) |
| Dividend Yield | N/A | Null in current CSV — strategy report noted ~1.36% |
| Beta (20d) | 0.831 | Lower volatility than FTSE 100 (defensive for financials) |
| RS vs FTSE 100 | 85.89 | Strong outperformance vs FTSE 100 index |

### Strategy Alignment Summary — `VWAP + Regime Filter`

#### Entry conditions (from `VWAP + Regime Filter`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| Close > VWAP | 9,186 > 8,775 ✅ | ✅ MET |
| VWAP rising | MA20 slope +40.8 ✅ | ✅ MET |
| RSI(14) between 50 and 65 | 61.7 ✅ | ✅ MET (upper end of range) |
| CMF > 0 (volume confirms) | +0.038 ✅ | ✅ MET (marginal — very close to zero) |
| Bull regime dominant (HMM state 0 prob highest) | State 2 at 44%, State 0 at 29% ❌ | ❌ NOT MET — volatile regime is dominant |
| EMA20 > EMA50 > EMA200 | 8,842 > 8,674 but 8,674 < 8,812 ❌ | ❌ NOT MET — EMA50 < EMA200 (medium-term trend not fully aligned) |

**Strategy Entry Verdict:** 4 of 6 entry conditions MET. Two failures — the regime filter (volatile regime at 44%, not bull) and EMA200 alignment (EMA50 below EMA200). This is a **marginal entry**: trend and momentum are strong, but the regime uncertainty and medium-term trend structure don't fully satisfy the strategy's conservative requirements. Entering here would be counter to the strategy rules.

#### Exit conditions (from `VWAP + Regime Filter`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| Close < VWAP | 9,186 > 8,775 ✅ | ✅ CONFIRMED (not triggered) |
| ATR trailing stop hit | 9,186 > 9,230 (10d high - 3xATR) ✅ | ✅ CONFIRMED (not triggered) |
| Regime shift to bear (HMM state 1 dominant) | State 2 at 44%, State 1 at 27% ✅ | ✅ CONFIRMED (not triggered) |

**Strategy Exit Verdict:** No exit conditions triggered. Price remains above VWAP, no bear regime dominance. However, the volatile regime (44%) is close to the bull regime (29%) — a regime shift to bear would quickly activate the exit.

{2–3 sentence narrative explaining the overall signal, who should act, and for whom}

**Narrative:** LSEG.L presents a **hold** signal — the trend and momentum are strong, but the strategy entry conditions are not fully met due to regime uncertainty (volatile regime at 44% vs bull at 29%). For current holders, there is no exit signal, so holding is appropriate. For non-holders, the missing regime filter and EMA200 alignment mean it's better to wait for the regime to clarify before entering. This is particularly relevant for LSEG.L's high volatility regime — the strategy's HMM filter is designed specifically to avoid entering during uncertain regimes.

---

### Aggregate Score

| # | Dimension | Signal | Score |
|---|-----------|--------|-------|
| 1 | **Trend** | 🟢 BULLISH | +2.0 |
| 2 | **Momentum** | 🟢 BULLISH | +2.0 |
| 3 | **Return** | 🟡 MIXED | -1.0 |
| 4 | **Structure** | 🟡 CAUTIOUS | +0.0 |
| 5 | **Volatility** | 🔴 HIGH | -1.0 |
| 6 | **Volume** | 🟡 MIXED | +0.5 |
| 7 | **Regime** | 🟡 NEUTRAL | +0.0 |
| | **AGGREGATE** | | **+2.5** |

**Aggregate Score: +2.5 — HOLD**

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | WAIT — do NOT enter yet | 2/6 entry conditions NOT MET (regime filter, EMA200 alignment); regime uncertain at 44% volatile |
| **Current holders** | HOLD — no exit triggered | Price above VWAP, no bear regime, no ATR stop hit; wait for regime clarity |
| **Traders** | AVOID new entries — regime uncertain | High vol + ambiguous HMM regime = whipsaw risk; wait for regime to resolve to clear bull or bear |

- **Entry:** Re-evaluate when HMM State 0 (bull) probability exceeds 44% AND EMA50 crosses back above EMA200
- **Stop-Loss:** 8,775 (VWAP) or 8,674 (EMA50) — whichever breaks first
- **Target:** 9,530 (nearest resistance, 3.7% above) → extended to 10,140 (52-week high) if momentum sustains

### Risk Factors
- **Regime uncertainty:** HMM probabilities are split 44%/29%/27% — the regime could flip to bear (State 1) at any point, triggering the strategy's primary exit condition
- **High volatility (ATR 85th percentile):** Normalized ATR of 3.25% per bar is elevated — price swings of 200–300p are routine, making position sizing critical
- **RSI at 61.7 (upper entry band):** The strategy's RSI cap is 65 — entering from here leaves minimal room before the RSI exits the optimal range, increasing the risk of buying into an overbought condition

### When This Signal Is Invalidated
- **HMM State 1 (bear) probability exceeds 44% and becomes dominant** → Signal becomes SELL (primary exit trigger for VWAP+Regime strategy)
- **Close breaks below VWAP (8,775)** → Signal becomes SELL (trend reversal exit)
- **HMM resolves to clear Bull (State 0 > 60%)** → Signal upgrades to BUY (entry conditions may then be satisfied)

---

*Report generated: 2026-10-28 | Data point: 2026-10-28 → 2026-10-28 | Data: `data/analysis-data/LSEG.L.csv` (5,053 rows) | Strategy: `data/reports/strategies/LSEG.L/2026-10-23.md` → Target: `VWAP + Regime Filter`*
