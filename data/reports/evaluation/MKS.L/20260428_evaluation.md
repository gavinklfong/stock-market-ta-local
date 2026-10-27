# Market Situation Evaluation: Marks & Spencer (MKS.L)

**Evaluation Date:** 2026-04-28
**Actual Date Used:** 2026-04-28
**Ticker:** MKS.L (Marks & Spencer)
**Price:** 329.6p
**Data Range:** 2006-10-27 to 2026-04-28 (4926 rows)
**Sector:** Retail
**Strategy Reference:** `data/reports/strategies/MKS.L/2026-10-26.md`
**Target Strategy:** `dual_exit_meanrev`

---

## Executive Summary

**Signal:** HOLD (approaching BUY)
**Confidence:** Medium

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🔴 BEARISH | 🟢 High | Price 5.58% below EMA20; all 3 EMAs above price; SuperTrend at 669.52 >> price; ADX 23.06 with DI- > DI+ |
| **Momentum** | 🟡 CAUTIOUS | 🟢 High | RSI 36.81 (approaching <35 oversold); CCI −141.35 strongly oversold; Williams %R −89.34 near −90; MACD histogram −2.39 still negative |
| **Return** | 🟡 MIXED | 🟡 Medium | 20d return +9.16% (prior pullback from 368.70 high); 10d return −5.55% (declining); 1m/3m/6m all negative |
| **Structure** | 🔴 BEARISH | 🟢 High | Price 329.60 within 1.94% of swing low 317.98; no HH/HL; price near Donchian lower 324.00; nearest resistance 387.05 (+17.4%) |
| **Volatility** | 🟡 NORMAL | 🟢 High | ATR 12.10 at 70th percentile; BB width 13.5%; price at BB %B = 4.2% (near lower band); Parkinson vol 0.31 moderate |
| **Volume** | 🔴 BEARISH | 🟢 High | CMF −0.047 negative; OFI −0.243 negative; OBV slope 14d −2.09M declining; ADL −544.6M negative; volume at 60th percentile |
| **Regime** | 🔴 BEAR | 🟢 High | HMM regime 2 (bear/volatile) at 97.34% — extremely high probability; regime stable at state 2 for entire Mar–Apr period |
| **Overall** | 🟡 HOLD | 🟡 Medium | Near entry threshold for `dual_exit_meanrev` — 2 of 3 conditions met; price 4.2% above BB Lower; RSI 36.81 vs <35 threshold |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | 329.6p | 1.95% below May 19 (326.80) — wait, actually 1.95% above that level; 12.19% below Apr 17 high (368.70); approaching entry zone |
| 52-Week Range | 315.30 – 411.80 | 75.0% of range — near 52-week low (only 4.54% above low), 20.0% below high |
| P/E (TTM) | 26.79 | Elevated; up from ~25.5 as price has declined less than earnings |
| Dividend Yield | 1.15% | Diluted by price drop from highs; income not primary driver |
| Beta (20d) | 2.31 | Extremely high — amplifies both gains and losses vs FTSE 100 significantly |
| RS vs FTSE 100 | +3.19 | Slightly outperforming the FTSE 100 over 20 days |

### Strategy Alignment Summary — `dual_exit_meanrev`

#### Entry conditions (from `dual_exit_meanrev`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| Close ≤ Bollinger Band Lower (20, 2) | 329.60 vs BB Lower 327.61 | ⚠️ NEARLY MET (price 1.99p / 0.61% above BB Lower — extremely close) |
| RSI(14) < 35 | 36.81 | ⚠️ NEARLY MET (RSI 1.81 points above 35 threshold; at 5th percentile) |
| CCI(20) < −100 | −141.35 | ✅ MET (CCI well below −100; strong negative momentum deviation) |
| Strategy context | Price declining from Apr 17 high (368.70) to 329.60 (−10.6%); HMM regime at 97.34% bear; Williams %R −89.34 near −90 oversold extreme | ⚠️ CAUTION — entry conditions are nearly aligned; price may cross into entry zone tomorrow |

**Strategy Entry Verdict:** Two of three entry conditions are nearly met — price is just 0.61% above BB Lower (329.60 vs 327.61) and RSI is 1.81 points above the <35 threshold (36.81). CCI at −141.35 already satisfies its condition. This is the last day *before* the entry triggers (trade #7 entered on 2026-04-29 @ 325.32, which was below BB Lower). The current state suggests a BUY entry is imminent — likely within 1 trading day — if price continues to decline toward the BB Lower. A slight bounce could delay entry by a few more days.

#### Exit conditions (from `dual_exit_meanrev`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|------------|
| Close ≥ BB Middle Band (20-day MA) | 329.60 vs BB Middle 351.32 | ❌ NOT MET (price 21.72p / 6.18% below BB Middle) |
| Close < 3-day high − 3×ATR trail | 3-day high ≈ 335.05 (Apr 28); 3×ATR = 36.30; trail = 298.75 | ❌ NOT MET (price 329.60 >> trail 298.75; no stop loss concern) |
| Strategy context | No active position; entry not yet triggered; price near BB Lower but above it | ❌ NOT MET — no position to exit; exit conditions only apply after entry |

**Strategy Exit Verdict:** No exit conditions apply — there is no active position. The trade has not yet entered. The primary exit condition (Close ≥ BB Middle at 351.32) is far from met, and the ATR trailing stop (298.75) is well below current price. If a position were to enter tomorrow (as trade #7 did at 325.32), the exit target would be BB Middle at 351.32 (~7.9% upside potential).

### Signal Summary

**Current Signal: HOLD / IMMINENT BUY**

As of 2026-04-28, MKS.L is standing at the threshold of a `dual_exit_meanrev` entry. Price at 329.60 is only 0.61% above BB Lower (327.61) and RSI at 36.81 is just 1.81 points above the <35 oversold threshold. CCI at −141.35 already satisfies its condition. The price closed at 329.60 on Apr 28, and the next trading day (Apr 29) saw the price drop further to 325.32 — which *was* below BB Lower — triggering the entry signal. The current state represents a near-term decision point: either wait for the conditions to fully align (1 day away) or prepare to enter once they do. For existing holders, no action is required. For non-holders, this is a pre-entry observation — the actual entry triggers when all three conditions are simultaneously MET.

---

### Aggregate Score

| # | Dimension | Signal | Score (-3.0 to +3.0) | Weight | Weighted |
|---|-----------|--------|-------------|--------|----------|
| 1 | **Trend** | BEARISH | −2.0 | 15% | −0.300 |
| 2 | **Momentum** | CAUTIOUS | −0.5 | 15% | −0.075 |
| 3 | **Return** | MIXED | +0.5 | 10% | +0.050 |
| 4 | **Structure** | BEARISH | −1.5 | 10% | −0.150 |
| 5 | **Volatility** | NORMAL | +0.0 | 10% | +0.000 |
| 6 | **Volume** | BEARISH | −1.0 | 10% | −0.100 |
| 7 | **Regime** | BEAR | −2.5 | 20% | −0.500 |
| | **AGGREGATE** | | | **100%** | **−1.075** |

**Aggregate Score: −1.08 — HOLD (approaching entry for mean-reversion strategy)**

*Note: The aggregate score is bearish (−1.08) reflecting the strong downtrend and bearish regime. However, this is exactly the environment where mean-reversion strategies like `dual_exit_meanrev` operate — they profit from oversold bounces within a bearish regime. The negative aggregate score signals caution for trend-following strategies but sets up the mean-reversion entry conditions.*

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | PREPARE TO BUY (1 day) | Entry conditions nearly met; price at BB Lower threshold; RSI approaching <35; CCI already <−100; entry triggers if price dips slightly |
| **Current holders** | HOLD | No position triggered yet; no action required; wait for entry confirmation |
| **Traders** | WATCH FOR ENTRY CONFIRMATION | Monitor price action — if Close ≤ 327.61 (BB Lower) AND RSI < 35, enter per `dual_exit_meanrev` rules |

- **Entry:** Close ≤ 327.61 (BB Lower) AND RSI < 35 AND CCI < −100 — conditions nearly met; actual entry occurred 2026-04-29 @ 325.32
- **Stop-Loss:** 325.32 − 3×ATR trail ≈ 288.90 (3-day high − 3×ATR); ATR trailing stop from 3-day high
- **Target:** 351.32 (BB Middle) — primary exit target; ~6.6% upside from entry zone

### Risk Factors
- **Regime extremely bearish (97.34% HMM probability):** The regime model is at near-maximum bear probability. Mean-reversion entries in such regimes carry gap-down risk — the bounce may be shallow or delayed.
- **Price near 52-week low (315.30):** At 329.60, only 4.54% above 52-week low. Break below swing low 317.98 could accelerate selling into the absolute lows.
- **High beta (2.31):** MKS.L amplifies market moves 2.3×. Any FTSE 100 decline would push MKS.L lower faster, increasing drawdown risk before the bounce materializes.

### When This Signal Is Invalidated
- **Price breaks below swing low 317.98** → Signal becomes WAIT (further downside likely; mean-reversion premature; wait for stabilization)
- **HMM regime shifts to state 0 (bull) with >50% probability** → Signal becomes BUY (regime confirmation for sustained recovery; entry conditions may be redundant)
- **Price bounces above BB Middle (351.32) without entry triggering** → Signal becomes SELL (failed mean-reversion setup; trend may have shifted upward without oversold entry)

---

*Report generated: 2026-04-28 | Data point: 2026-04-28 → 2026-04-28 | Data: `data/analysis-data/MKS.L.csv` (4926 rows) | Strategy: `data/reports/strategies/MKS.L/2026-10-26.md` → Target: `dual_exit_meanrev`*
