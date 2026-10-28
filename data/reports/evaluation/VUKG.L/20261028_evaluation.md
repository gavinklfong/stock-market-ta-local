# Market Situation Evaluation: Vanguard FTSE 100 UCITS ETF (Acc) (VUKG.L)

**Date Used:** 2026-10-28
**Ticker:** VUKG.L (Vanguard FTSE 100 UCITS ETF (Acc))
**Price:** 57.66p
**Data Range:** 2019-05-14 to 2026-10-28 (1,885 rows)
**Sector:** ETF
**Strategy Reference:** `data/reports/strategies/VUKG.L/20261021.md`
**Target Strategy:** `Score 3+ / RSI > 75`

---

## Executive Summary

**Signal:** BUY
**Confidence:** Medium

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🟡 CAUTIOUS | 🟡 Medium | EMA20>50>200 bullish alignment but ADX 13.0 weak trend, +DI < -DI |
| **Momentum** | 🟡 CAUTIOUS | 🟡 Medium | RSI 50.8 neutral, MACD bullish crossover confirmed, no extreme readings |
| **Return** | 🟢 POSITIVE | 🟢 High | +12.7% 1Y, +4.7% 6M; short-term (1m/3m) flat-to-negative |
| **Structure** | 🟡 CAUTIOUS | 🟡 Medium | No BOS/CHoCH signals, price trapped between support 57.31 and resistance 57.91 |
| **Volatility** | 🟡 NORMAL | 🟢 High | BB width 5.1% moderate, no extreme compression or expansion |
| **Volume** | 🟢 BULLISH | 🟢 High | CMF +0.10, OFI +0.23, OBV slope 14d positive — sustained buying pressure |
| **Regime** | 🟢 BULL | 🟢 High | HMM State 0 (Bull) at 93.8% — dominant regime |
| **Overall** | 🟢 BUY | 🟡 Medium | 5 bullish, 2 cautious; regime firmly bull; entry conditions met |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | 57.66p | Near 52-week high (58.75), 98.1% of range |
| 52-Week Range | 49.51 – 58.75p | Near top — euphoric territory approaching |
| P/E (TTM) | N/A | ETF — no P/E data available |
| Dividend Yield | N/A | ETF — accumulating; no yield data |
| Beta (20d) | 0.999 | Near-perfect FTSE 100 tracker |
| RS vs FTSE 100 | 0.54 | Slight underperformance vs benchmark |

### Strategy Alignment Summary — `Score 3+ / RSI > 75`

#### Entry conditions (from `Score 3+ / RSI > 75`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| EMA20 > EMA50 | 57.64 > 57.51 ✅ | ✅ MET |
| RSI > 50 | 50.76 ✅ | ✅ MET |
| MACD bullish (line > signal) | 0.109 > 0.085 ✅ | ✅ MET |
| CMF > 0 | +0.100 ✅ | ✅ MET |
| OFI > 0 | +0.234 ✅ | ✅ MET |
| ADX > 20 | 13.0 ❌ | ❌ NOT MET |

**Strategy Entry Verdict:** 5 of 6 entry conditions MET (Score = 5/6 ≥ 3 threshold) — entry criteria satisfied. Only ADX > 20 fails, consistent with VUKG.L's structurally weak-trend behavior (ADX averages low on FTSE 100 tracker).

#### Exit conditions (from `Score 3+ / RSI > 75`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| RSI > 75 | 50.76 ❌ | ✅ CONFIRMED (not triggered) |
| SuperTrend Flip Bearish | SuperTrend UP (57.18) | ✅ CONFIRMED (not triggered) |
| Close < EMA50 | 57.66 > 57.51 | ✅ CONFIRMED (not triggered) |
| EMA20 < EMA50 | 57.64 > 57.51 | ✅ CONFIRMED (not triggered) |

**Strategy Exit Verdict:** No exit conditions triggered. RSI is far from the 75 take-profit threshold, trend remains intact. Position is in early-mid stage of a valid trade cycle.

{2–3 sentence narrative explaining the overall signal, who should act, and for whom}

**Narrative:** VUKG.L presents a classic FTSE 100 tracker setup — firmly in a bull regime with 5 of 6 entry conditions met. The ETF is 98.1% through its 52-week range and the RSI > 75 exit (the strategy's crown jewel) is not yet triggered, meaning there's room for further upside capture before profit-taking. This is primarily suitable for investors who want tactical exposure to the FTSE 100's upside while avoiding the -34% drawdowns the strategy has historically eliminated.

---

### Aggregate Score

| # | Dimension | Signal | Score |
|---|-----------|--------|-------|
| 1 | **Trend** | 🟡 CAUTIOUS | +1.0 |
| 2 | **Momentum** | 🟡 CAUTIOUS | +0.5 |
| 3 | **Return** | 🟢 POSITIVE | +2.0 |
| 4 | **Structure** | 🟡 CAUTIOUS | +0.0 |
| 5 | **Volatility** | 🟡 NORMAL | -1.0 |
| 6 | **Volume** | 🟢 BULLISH | +2.0 |
| 7 | **Regime** | 🟢 BULL | +3.0 |
| | **AGGREGATE** | | **+7.5** |

**Aggregate Score: +7.5 — BUY**

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | ENTER (long VUKG.L) | 5/6 entry conditions met; bull regime at 93.8%; strategy Score = 5/6 |
| **Current holders** | HOLD — monitor for RSI > 75 exit | No exit triggered; RSI far from 75; position has upside room |
| **Traders** | AVOID short — regime too strong | HMM 93.8% bull; no bearish confluence; shorting a tracker is structurally unfavourable |

- **Entry:** Current levels (~57.66p) — strategy entry conditions satisfied
- **Stop-Loss:** 57.18 (SuperTrend level) or 55.83 (swing low / Donchian lower)
- **Target:** 58.75 (52-week high / Donchian upper) → extended if RSI > 75 fires

### Risk Factors
- **Near 52-week high (98.1%):** Limited upside before hitting structural resistance at 58.75; any reversal from highs could trigger mean reversion to the middle of the range (~57.38)
- **Weak trend (ADX 13.0):** VUKG.L is structurally range-bound between trend episodes; mean-reversion moves can whipsaw trend followers
- **RSI > 75 exit rare (22 trades in 7.5 years):** The strategy's primary profit-taking mechanism fires very infrequently; position could experience a prolonged drawdown before the exit condition triggers

### When This Signal Is Invalidated
- **RSI crosses below 45** → Signal becomes HOLD (mild oversold, re-enter only if entry conditions re-satisfy)
- **SuperTrend flips to bearish** → Signal becomes SELL (primary trend exit condition)
- **Close breaks below EMA50** → Signal becomes SELL (defensive exit per strategy)
- **HMM regime shifts to State 1 or 2** (prob > 50%) → Signal becomes WAIT (regime uncertainty)

---

*Report generated: 2026-10-28 | Data point: 2026-10-28 → 2026-10-28 | Data: `data/analysis-data/VUKG.L.csv` (1,885 rows) | Strategy: `data/reports/strategies/VUKG.L/20261021.md` → Target: `Score 3+ / RSI > 75`*
