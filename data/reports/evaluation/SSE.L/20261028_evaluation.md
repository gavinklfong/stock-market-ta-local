# Market Situation Evaluation: SSE plc (SSE.L)

**Date Used:** 2026-10-28
**Ticker:** SSE.L (SSE plc)
**Price:** 2,604p
**Data Range:** 2006-10-30 to 2026-10-28 (5,053 rows)
**Sector:** Utilities
**Strategy Reference:** `data/reports/strategies/SSE.L/20261022.md`
**Target Strategy:** `RSI_Pullback`

---

## Executive Summary

**Signal:** HOLD
**Confidence:** High

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🟢 BULLISH | 🟢 High | EMA20>EMA50>EMA200 perfect bullish alignment, SuperTrend UP, both MA20/50 slopes positive |
| **Momentum** | 🟢 BULLISH | 🟡 Medium | RSI 62.9 healthy but approaching overbought, MACD bullish, CCI 112 overbought zone |
| **Return** | 🟡 MIXED | 🟢 High | +37.1% 1Y strong, +11.0% 3M, +6.9% 1M — but -1.4% 6M, recent rally stalled |
| **Structure** | 🟡 CAUTIOUS | 🟡 Medium | Price at Donchian Upper (2,604 = 5-day high), resistance only 0.7% away, no HH/HL/LH/LL patterns |
| **Volatility** | 🔴 HIGH | 🟢 High | ATR 85th percentile, BB %B 102.7% (above upper band!), GARCH vol 1.35 elevated |
| **Volume** | 🟡 MIXED | 🟡 Medium | CMF +0.13 positive but OFI only +1.0, ADL negative, volume 60th percentile moderate |
| **Regime** | 🔴 BEAR | 🟡 Medium | HMM State 2 (volatile) at 72.5%, State 1 (bear) at 27.4%, State 0 (bull) at 0.02% |
| **Overall** | 🟡 HOLD | 🟡 Medium | 2 bullish, 1 bullish/cautious, 1 high-vol, 1 bearish volatile regime |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | 2,604p | At Donchian Upper (5-day high), +5% today from 2,490p close — big up day |
| 52-Week Range | 1,843 – 2,768p | 80.7% of range — near top, not oversold |
| P/E (TTM) | N/A | Null in current CSV — no fundamentals in data |
| Dividend Yield | N/A | Null in current CSV — SSE is a utility with typical utility yield |
| Beta (20d) | 0.654 | Lower volatility than FTSE 100 (defensive utility profile) |
| RS vs FTSE 100 | 24.35 | Strong outperformance vs FTSE 100 index |

### Strategy Alignment Summary — `RSI_Pullback`

#### Entry conditions (from `RSI_Pullback`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| Close > EMA200 | 2,604 > 2,387 ✅ | ✅ MET — clear uptrend, price well above 200-day EMA |
| MA200_slope_20d > 0 | MA50 slope +2.81, MA20 slope +3.74 ✅ | ✅ MET — both short/medium MAs rising (proxy confirms) |
| RSI14 in dip zone (35–45) | 62.9 ❌ | ❌ NOT MET — RSI is deep in bullish zone, nowhere near dip zone |
| Bounce: RSI14 > 45 and ≤ 55 | 62.9 ❌ | ❌ NOT MET — RSI already above the bounce confirmation range |
| MACD_line > MACD_signal | 27.62 > 26.89 ✅ | ✅ MET — momentum is positive |

**Strategy Entry Verdict:** 3 of 5 entry conditions MET. The RSI_Pullback strategy is designed to buy RSI dips (35–45) in an uptrend. Current RSI of 62.9 is the exact opposite of the dip zone — the stock is in the momentum/exit zone, not the entry zone. **This is NOT an entry for this strategy.** The uptrend filter and MACD are satisfied, but the RSI criteria are the core of the strategy and they are completely unmet.

#### Exit conditions (from `RSI_Pullback`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| RSI > 65 (exit overbought) | 62.9 — approaching | ⚠️ CAUTION — near exit zone but not yet triggered |

**Strategy Exit Verdict:** No exit triggered yet, but RSI at 62.9 is approaching the 65 exit threshold. If RSI crosses 65, the strategy would exit a long position to capture profits before a pullback. Price is at the top of the Bollinger Band (102.7% %B) and at the 52-day Donchian high — this is where the RSI_Pullback strategy would look to exit, not enter.

SSE.L is at the top of its recent range with strong momentum — the RSI_Pullback strategy is designed to buy dips in utility uptrends, not chase breakouts. Current conditions are **exit territory, not entry territory**. For holders, the exit is near (RSI approaching 65). For non-holders, the strategy would never fire here.

---

### Aggregate Score

| # | Dimension | Signal | Score |
|---|-----------|--------|-------|
| 1 | **Trend** | 🟢 BULLISH | +2.0 |
| 2 | **Momentum** | 🟢 BULLISH | +1.5 |
| 3 | **Return** | 🟡 MIXED | -1.0 |
| 4 | **Structure** | 🟡 CAUTIOUS | -0.5 |
| 5 | **Volatility** | 🔴 HIGH | -1.5 |
| 6 | **Volume** | 🟡 MIXED | 0.0 |
| 7 | **Regime** | 🔴 BEAT/NEUTRAL | -1.0 |
| | **AGGREGATE** | | **-0.5** |

**Aggregate Score: -0.5 — HOLD**

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | DO NOT ENTER — wait for RSI dip (35–45) | 3/5 entry conditions NOT MET; RSI at 62.9 far from dip zone; price at Donchian high with volatile regime |
| **Current holders** | HOLD — monitor RSI 65 exit threshold | RSI at 62.9 approaching exit zone; price at BB Upper (102.7% %B) suggests near-term pullback risk |
| **Traders** | AVOID new entries — near-term top likely | Price at Donchian Upper, BB above 100%, volatile regime (72.5%) — mean-reversion to lower levels probable |

- **Entry:** Wait for RSI to drop to 35–45 range while price remains above EMA200 — next dip-buying opportunity. With HMM in volatile regime (72.5%), a pullback from current levels is statistically likely.
- **Stop-Loss:** 2,510 (EMA20) or 2,471 (EMA50) — if price breaks below 20-day EMA, short-term uptrend structure may be damaged
- **Target:** 2,768 (52-week high, 6.3% above current) if momentum sustains; otherwise expect pullback to 2,510 (EMA20, 3.6% below)

### Risk Factors
- **Price at Donchian Upper (5-day high):** SSE.L is at its highest level in 5 days after a +5% single-day surge. Combined with BB %B at 102.7% (above upper band), this historically precedes mean-reversion pullbacks to the BB Middle (~2,506p, 3.8% down)
- **Volatile regime dominant (72.5%):** HMM State 2 has been persistent since Oct 16, with State 0 (bull) probability near zero (0.02%). The strategy's uptrend filter is satisfied, but volatile regimes increase the risk of sharp pullbacks after breakouts
- **RSI approaching 65 exit zone:** At 62.9, RSI is within 2 points of the strategy's exit threshold. A continuation rally would trigger an exit (profit-taking), while a pullback would bring RSI closer to the entry zone — but both outcomes mean NOT entering here

### When This Signal Is Invalidated
- **RSI > 65** → Signal stays HOLD but upgrades to SELL for current holders (exit condition fires)
- **HMM State 0 (bull) probability exceeds 50%** → Signal could upgrade to BUY if RSI also drops into dip zone (35–45)
- **Price closes below EMA50 (2,471p)** → Signal becomes SELL (uptrend broken, trend filter fails)

---

*Report generated: 2026-10-28 | Data point: 2026-10-28 → 2026-10-28 | Data: `data/analysis-data/SSE.L.csv` (5,053 rows) | Strategy: `data/reports/strategies/SSE.L/20261022.md` → Target: `RSI_Pullback`*
