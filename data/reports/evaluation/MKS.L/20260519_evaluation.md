# Market Situation Evaluation: Marks & Spencer (MKS.L)

**Evaluation Date:** 2026-05-19
**Actual Date Used:** 2026-05-19
**Ticker:** MKS.L (Marks & Spencer)
**Price:** 326.8p
**Data Range:** 2006-10-27 to 2026-05-19 (4940 rows)
**Sector:** Retail
**Strategy Reference:** `data/reports/strategies/MKS.L/2026-10-26.md`
**Target Strategy:** `dual_exit_meanrev`

---

## Executive Summary

**Signal:** HOLD
**Confidence:** Medium

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🔴 BEARISH | 🟢 High | Price below all 3 EMAs; MA20 slope −1.84; SuperTrend bearish; DI− > DI+ |
| **Momentum** | 🟡 CAUTIOUS | 🟡 Medium | RSI 45.7 neutral zone; MACD histogram barely positive (+0.40); CCI −5.6 near zero |
| **Return** | 🟡 MIXED | 🟡 Medium | Surprisingly strong 5d (+11.26%) and 10d (+12.70%) bounce from May 12 low (308.90); 3m (−18.85%) and 1y (−11.10%) weak |
| **Structure** | 🟡 CAUTIOUS | 🟢 High | Recovering from swing low 301.10 (May 12 @ 308.90); not yet at swing high 374.85; no HH/HL confirmed |
| **Volatility** | 🟢 LOW | 🟢 High | ATR at 5th percentile (10.87); HVol 38.7% — calmest volatility in months; BB width 13.5% |
| **Volume** | 🟡 MIXED | 🟡 Medium | CMF −0.01 (flat); OFI negative; ADL negative; volume 80th percentile — no clear conviction |
| **Regime** | 🔴 BEAR | 🟢 High | HMM regime 2 (bear/volatile) with 92.6% probability — strongest bear signal in recent history |
| **Overall** | 🟡 HOLD | 🟡 Medium | Bear regime intact but price near support; no entry or exit signals triggered |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | 326.8p | Recovering from May 12 low (308.90) — up +5.78% in 5 days; still below EMA20 (329.95) |
| 52-Week Range | 301.10 – 411.80 | 62.5% of range — near bottom end of 52-week band |
| P/E (TTM) | 26.57 | Elevated for UK value retailer |
| Dividend Yield | 1.16% | Modest yield; income not primary driver |
| Beta (20d) | 1.35 | High beta — moves ~1.4× FTSE 100, amplifies both gains and losses |
| RS vs FTSE 100 | +3.16 | Outperforming the FTSE 100 over 20 days |

### Strategy Alignment Summary — `dual_exit_meanrev`

#### Entry conditions (from `dual_exit_meanrev`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| Close ≤ Bollinger Band Lower (20, 2) | 326.80 vs BB Lower 307.57 | ❌ NOT MET (price is 19.23p / 6.25% above BB Lower) |
| RSI(14) < 35 | 45.69 | ❌ NOT MET (RSI in neutral territory) |
| CCI(20) < −100 | −5.56 | ❌ NOT MET (CCI near zero, not negative) |
| Strategy context | Price recovered from May 12 low (308.90); still well within bear regime (92.6%) | ⚠️ CAUTION — oversold bounce is underway but not deep enough for entry |

**Strategy Entry Verdict:** All 3 entry conditions are NOT MET. The stock is not in the oversold zone required by `dual_exit_meanrev`. While price is relatively near the swing low (308.90 on May 12), it has already bounced +5.78% and the RSI/CCI have recovered from oversold levels. An entry would require a deeper pullback back toward or below BB Lower (307.57) with RSI < 35 and CCI < −100.

#### Exit conditions (from `dual_exit_meanrev`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| Close ≥ BB Middle Band (20-day MA) | 326.80 vs BB Middle 329.81 | ❌ NOT MET (price is 3.01p / 0.91% below BB middle) |
| Close < 3-day high − 3×ATR trail | 3-day high ≈ 334.0 (May 18); 3×ATR = 32.62; trail = 301.38 | ❌ NOT MET (price 326.80 > trail 301.38) |
| Strategy context | Price below BB Middle but approaching; ATR trail far below — no exit pressure | ⚠️ CAUTION — if price breaks above BB Middle (329.81), exit condition triggers |

**Strategy Exit Verdict:** Neither exit condition is MET. For a holder who entered on 2026-04-29 (per trade #7 in the backtest, entry 325.32), the position is currently in profit (+0.43%) but has NOT yet reached the BB Middle exit target. The price is only 3.01p below BB Middle (329.81) — a break above this level would trigger the primary exit. The ATR trailing stop (301.38) is far below, giving ample room for further upside.

### Signal Summary

**Current Signal: HOLD / WAITING FOR EXIT SIGNAL**

Price is in a transitional state — recovering from the May 12 swing low but still within a strong bear regime (92.6% HMM probability). The `dual_exit_meanrev` strategy would NOT enter here (no oversold signal) and would NOT exit yet (price below BB Middle). For holders of the Apr 29 entry (trade #7), this is a near-breakeven position (+0.43%) with the BB Middle exit target just 0.91% away. A break above 329.81 would trigger the exit. A new entry would require the price to fall back below BB Lower (~307.57) with RSI < 35 and CCI < −100 — conditions not currently present.

---

### Aggregate Score

| # | Dimension | Signal | Score (-3.0 to +3.0) | Weight | Weighted |
|---|-----------|--------|-------------|--------|----------|
| 1 | **Trend** | BEARISH | −2.0 | 15% | −0.300 |
| 2 | **Momentum** | CAUTIOUS | +0.5 | 15% | +0.075 |
| 3 | **Return** | MIXED | −0.5 | 10% | −0.050 |
| 4 | **Structure** | CAUTIOUS | +0.5 | 10% | +0.050 |
| 5 | **Volatility** | LOW | +1.0 | 10% | +0.100 |
| 6 | **Volume** | MIXED | +0.0 | 10% | +0.000 |
| 7 | **Regime** | BEAR | −3.0 | 20% | −0.600 |
| | **AGGREGATE** | | | **100%** | **−0.725** |

**Aggregate Score: −0.73 — HOLD**

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | DO NOT ENTER | No entry signal; RSI 45.7 / CCI −5.6 far from oversold thresholds; bear regime at 92.6% |
| **Current holders** (entry ~Apr 29) | HOLD — WATCH BB MIDDLE | Near-breakeven (+0.43%); BB Middle exit target at 329.81 is 3.01p away — likely to trigger soon if bounce continues |
| **Traders** | WAIT FOR DIP | No actionable signal; wait for pullback to BB Lower (~307.57) with RSI < 35 and CCI < −100 for a fresh entry |

- **Entry:** Wait for Close ≤ 307.57 (BB Lower) AND RSI < 35 AND CCI < −100 — none currently met
- **Stop-Loss:** 301.38 (3-day high − 3×ATR trail) — if price falls back to this level, exit to preserve capital
- **Target:** 329.81 (BB Middle) — primary exit for holders; +0.91% from current price

### Risk Factors
- **Extreme bear regime (92.6% HMM probability):** The regime model is in state 2 with the highest confidence seen in recent history. A sustained bear regime means any bounce may be short-lived and sell-off pressure likely to resume.
- **Volume lacks conviction (CMF flat at −0.01):** The current bounce from May 12 lacks institutional buying confirmation — CMF is negative and OFI is negative. A bounce without volume support is more likely to fail.
- **Low ATR percentile (5th):** While low volatility is favorable for the trailing stop, it can compress quickly. A volatility expansion event could trigger large downward moves before the ATR trail adjusts.

### When This Signal Is Invalidated
- **Price breaks above BB Middle (329.81)** → Signal becomes SELL for existing holders (primary exit condition triggered; take profit)
- **HMM regime shifts to state 0 or 1 (bull/neutral) with >50% probability** → Signal becomes WAIT/BUY (regime change would validate a sustained recovery)
- **Price falls back below BB Lower (307.57) with RSI < 35 and CCI < −100** → Signal becomes BUY for new entry (fresh oversold setup for `dual_exit_meanrev`)

---

*Report generated: 2026-05-19 | Data point: 2026-05-19 → 2026-05-19 | Data: `data/analysis-data/MKS.L.csv` (4940 rows) | Strategy: `data/reports/strategies/MKS.L/2026-10-26.md` → Target: `dual_exit_meanrev`*
