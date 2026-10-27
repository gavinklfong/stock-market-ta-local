# Market Situation Evaluation: Marks & Spencer (MKS.L)

**Evaluation Date:** 2026-05-20
**Actual Date Used:** 2026-05-20
**Ticker:** MKS.L (Marks & Spencer)
**Price:** 348.5p
**Data Range:** 2006-10-27 to 2026-05-20 (4941 rows)
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
| **Trend** | 🔴 BEARISH | 🟢 High | Price below EMA50/EMA200; MA slopes negative; SuperTrend bearish |
| **Momentum** | 🟡 CAUTIOUS | 🟡 Medium | RSI 57.5 neutral; MACD histogram turning positive (+2.24); CCI 117.9 overbought |
| **Return** | 🟡 MIXED | 🟡 Medium | Strong 5d (+3.24%) and 10d (+5.42%) bounce; 3m (-11.73%) and 1y (-6.99%) weak |
| **Structure** | 🟡 CAUTIOUS | 🟢 High | Recovering from swing low 301.10 (Apr 29); not yet at swing high 374.85; no HH/HL confirmed |
| **Volatility** | 🔴 HIGH | 🟢 High | ATR 95th percentile; HVol 44.7%; BB width 13.1% — elevated risk environment |
| **Volume** | 🟢 BULLISH | 🟡 Medium | CMF +0.09; OBV positive; volume 95th percentile; but ADL negative — mixed buying pressure |
| **Regime** | 🔴 BEAR | 🟢 High | HMM regime 2 (bear/volatile) with 70.2% probability; GARCH vol 2.22 |
| **Overall** | 🟠 SELL | 🟡 Medium | Exit conditions met for dual_exit_meanrev; price above BB middle — profit target reached |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | 348.5p | Recovered +7.23% from swing low (325.0 on Apr 29); approaching BB upper band (351.24) |
| 52-Week Range | 301.10 – 411.80 | 76.2% of range — well above low, but 15.4% below high |
| P/E (TTM) | 28.33 | Elevated for UK value retailer |
| Dividend Yield | 1.09% | Modest yield; income not primary driver |
| Beta (20d) | 1.59 | High beta — moves ~1.6× FTSE 100, amplifies both gains and losses |
| RS vs FTSE 100 | +3.34 | Outperforming the FTSE 100 over 20 days |

### Strategy Alignment Summary — `dual_exit_meanrev`

#### Entry conditions (from `dual_exit_meanrev`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| Close ≤ Bollinger Band Lower (20, 2) | 348.50 vs BB Lower 308.04 | ❌ NOT MET (price well above BB Lower) |
| RSI(14) < 35 | 57.49 | ❌ NOT MET (RSI in neutral territory) |
| CCI(20) < −100 | 117.87 | ❌ NOT MET (CCI positive, not negative) |
| Strategy context | Price up +7.23% from Apr 29 swing low; recovering from oversold entry | ⚠️ CAUTION — conditions indicate price has moved well past entry zone |

**Strategy Entry Verdict:** All 3 entry conditions are NOT MET. The stock has recovered significantly from the oversold zone where `dual_exit_meanrev` would enter. This is consistent with trade #7's entry on 2026-04-29 @ 325.32 — that entry is now in profit.

#### Exit conditions (from `dual_exit_meanrev`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| Close ≥ BB Middle Band (20-day MA) | 348.50 vs BB Middle 329.64 | ✅ MET (price is 18.86p / 5.73% above BB middle) |
| Close < 3-day high − 3×ATR trail | 3-day high ≈ 351.75; 3×ATR = 38.25; trail = 313.50 | ❌ NOT MET (price 348.50 > trail 313.50) |
| Strategy context | Price near BB upper band (351.24); mean reversion to middle already achieved | ✅ CONFIRMED — primary exit trigger (BB Middle) was crossed on the way up |

**Strategy Exit Verdict:** The primary exit condition (Close ≥ BB Middle) is MET. The price recovered from the oversold zone and crossed above the BB middle band. The ATR trailing stop is not triggered, confirming the price has not reversed downward. Per the backtest trade log, trade #7 would exit on 2026-05-20 @ ~348.15 for +6.81% — this evaluation confirms the exit rationale.

### Signal Summary

**Current Signal: SELL / PROFIT TAKING**

The price has recovered from its oversold entry point and the `dual_exit_meanrev` strategy's primary exit condition (Close ≥ BB Middle Band) is satisfied. This is a profit-taking signal for anyone who entered on the 2026-04-29 dip. New entries are not advisable — the oversold conditions that justified the original entry have disappeared, and the HMM regime remains bearish (70.2% probability) with elevated volatility (ATR 95th percentile). The mean-reversion bounce has largely played out.

---

### Aggregate Score

| # | Dimension | Signal | Score (-3.0 to +3.0) | Weight | Weighted |
|---|-----------|--------|-------------|--------|----------|
| 1 | **Trend** | BEARISH | −2.0 | 15% | −0.300 |
| 2 | **Momentum** | CAUTIOUS | +0.5 | 15% | +0.075 |
| 3 | **Return** | MIXED | −0.5 | 10% | −0.050 |
| 4 | **Structure** | CAUTIOUS | +0.5 | 10% | +0.050 |
| 5 | **Volatility** | HIGH | −1.5 | 10% | −0.150 |
| 6 | **Volume** | BULLISH | +1.0 | 10% | +0.100 |
| 7 | **Regime** | BEAR | −2.5 | 20% | −0.500 |
| | **AGGREGATE** | | | **100%** | **−0.775** |

**Aggregate Score: −0.78 — SELL**

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | DO NOT ENTER | Oversold conditions have disappeared; BB Lower entry zone (308.04) not approached; HMM regime is bearish |
| **Current holders** (entry ~Apr 29) | TAKE PROFIT / REDUCE | Exit condition (BB Middle) met; +6.81% gain realized per trade log; mean-reversion target achieved |
| **Traders** | AVOID NEW LONGS | No fresh entry signal; wait for next oversold dip below BB Lower with RSI < 35 and CCI < −100 |

- **Entry:** Wait for Close ≤ 308.04 (BB Lower) AND RSI < 35 AND CCI < −100 — none currently met
- **Stop-Loss:** 308.04 (BB Lower) — if price falls back below BB Lower, the oversold setup is re-established but requires re-evaluation
- **Target:** 374.85 (swing high) — if trend reverses and price breaks above BB Upper (351.24), next resistance at swing high

### Risk Factors
- **Bear regime persistence (70.2% HMM probability):** The regime model is in state 2 (bear/volatile). A prolonged bear regime could suppress further upside and push price back toward the BB Lower zone.
- **Elevated volatility (ATR 95th percentile):** High ATR means larger price swings in both directions. The 3×ATR trailing stop (38.25p) is wide — a sharp reversal could trigger it unexpectedly.
- **High beta (1.59):** MKS.L amplifies FTSE 100 moves. A broad market decline would likely hit MKS.L harder than the index, potentially triggering a new oversold entry but with higher downside risk.

### When This Signal Is Invalidated
- **Price breaks above BB Upper (351.24) with rising volume** → Signal becomes BUY (trend reversal confirmation)
- **HMM regime shifts to state 0 (bull) with >50% probability** → Signal becomes BUY (regime change validates recovery)
- **Price falls back below BB Lower (308.04) with RSI < 35 and CCI < −100** → Signal becomes BUY for new entry (fresh oversold setup for `dual_exit_meanrev`)

---

*Report generated: 2026-05-20 | Data point: 2026-05-20 → 2026-05-20 | Data: `data/analysis-data/MKS.L.csv` (4941 rows) | Strategy: `data/reports/strategies/MKS.L/2026-10-26.md` → Target: `dual_exit_meanrev`*
