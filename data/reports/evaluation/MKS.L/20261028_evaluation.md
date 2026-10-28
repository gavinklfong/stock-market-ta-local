# Market Situation Evaluation: Marks & Spencer (MKS.L)

**Date Used:** 2026-10-28
**Ticker:** MKS.L (Marks & Spencer)
**Price:** 406.0p
**Data Range:** 2006-10-30 to 2026-10-28 (5,053 rows)
**Sector:** Retail
**Strategy Reference:** `data/reports/strategies/MKS.L/2026-10-26.md`
**Target Strategy:** `vol_filtered_meanrev` (Vol-Filtered Mean Reversion)

---

## Executive Summary

**Signal:** HOLD
**Confidence:** Medium

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🟢 BULLISH | 🟢 High | Price above all EMAs, SuperTrend +1, MA20 slope +2.21 rising |
| **Momentum** | 🟡 CAUTIOUS | 🟡 Medium | RSI 53.1 neutral, MACD histogram −0.33 flat, MFI 182.5 extreme |
| **Return** | 🟡 MIXED | 🟡 Medium | +6.4% 1m, +23.0% 6m, but −0.1% 1y flat, Alpha +0.25 positive |
| **Structure** | 🟡 CAUTIOUS | 🟡 Medium | Pulled back from 52-week high 429.4p, no confirmed HH/HL/BOS |
| **Volatility** | 🟡 NORMAL | 🟡 Medium | ATR percentile 0% compressed, BB width 14.8% moderate |
| **Volume** | 🔴 BEARISH | 🟡 Medium | CMF −0.018, OFI −0.79, volume at 10th percentile — distribution |
| **Regime** | 🟢 BULL | 🟢 High | HMM State 0 (Bull) at 98.0%, stable 30+ days, zero flips |
| **Overall** | 🟡 HOLD | 🟡 Medium | Bullish trend and regime intact but no mean-reversion entry setup |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | 406.0p | 0.0% above EMA20 (406.0), +2.8% above EMA50 |
| 52-Week Range | 301.1 – 429.4p | 93.8% of range, 5.4% below 52-week high |
| P/E (TTM) | N/A | No fundamentals data available for MKS.L |
| Dividend Yield | N/A | No fundamentals data available for MKS.L |
| Beta (20d) | 0.37 | Very low volatility vs FTSE 100 (defensive) |
| RS vs FTSE 100 | +3.80% | Mildly outperforming FTSE 100 over 20-day window |

### Strategy Alignment Summary — `vol_filtered_meanrev`

#### Entry conditions (from `vol_filtered_meanrev`)

| Strategy Element | Current Value | Alignment |
|-----------------|---------------|-----------|
| Close ≤ Bollinger Band Lower (20, 2) | 406.0p vs BB Lower 374.4p | ❌ NOT MET (price 8.4% above) |
| RSI(14) < 35 | 53.14 | ❌ NOT MET (neutral zone) |
| CCI(20) < −100 | 23.99 | ❌ NOT MET (positive momentum) |
| GARCH(1,1) vol ≤ previous day | 1.68 ≤ 2.83 (prev²) | ✅ MET (volatility declining) |

**Strategy Entry Verdict:** 3 of 4 entry conditions are NOT MET. The `vol_filtered_meanrev` strategy requires a deep oversold dip — price touching the lower Bollinger Band with RSI below 35 and CCI below −100. MKS.L is currently trading near its 20-day moving average (0.0% above) and 52-week high (only 5.4% below), the exact opposite of the entry zone. The sole met condition — declining GARCH volatility — confirms the stock is not in a high-volatility panic phase, but on its own is insufficient.

#### Exit conditions (from `vol_filtered_meanrev`)

| Strategy Element | Current Value | Alignment |
|-----------------|---------------|-----------|
| Close ≥ BB Middle Band (20-day MA) | 406.0p vs BB Middle 404.4p | ✅ MET (0.4% above — barely) |
| ATR trailing stop (3-day high − 3×ATR) | 422.4p − 27.6 = 394.8p | ✅ MET (price 406.0 > 394.8, no trigger) |

**Strategy Exit Verdict:** The primary exit condition is marginally met (price 0.4% above BB Middle at 404.4p). If a position were held from a BB Lower entry, the mean-reversion target has been reached. The ATR trailing stop at 394.8p has not been triggered, so the position would still be open. The price being right at the BB Middle is the canonical exit point for this strategy.

#### Strategy Context

`vol_filtered_meanrev` achieved **17.71% return, 0.88 Sharpe, 11.29% max DD, 66.7% win rate** over ~1.75 years (6 trades). The recommended strategy for MKS.L due to its balanced risk-adjusted profile. The GARCH volatility filter reduced signal frequency from 8 to 6 trades and eliminated the worst loss-making entries.

MKS.L is characterized as a range-bound FTSE 100 retail stock that oscillates between ~300p and ~420p. Mean-reversion strategies are superior during drawdown years (2025: +4.12% vs B&H −15.23%), while momentum strategies excel during recoveries (2026: vwap +19.39% vs B&H +27.66%).

---

### Aggregate Score

| # | Dimension | Signal | Score |
|---|-----------|--------|-------|
| 1 | **Trend** | 🟢 BULLISH | +2.0 |
| 2 | **Momentum** | 🟡 CAUTIOUS | +0.0 |
| 3 | **Return** | 🟡 MIXED | +0.5 |
| 4 | **Structure** | 🟡 CAUTIOUS | +0.5 |
| 5 | **Volatility** | 🟡 NORMAL | +0.5 |
| 6 | **Volume** | 🔴 BEARISH | −1.0 |
| 7 | **Regime** | 🟢 BULL | +2.5 |
| | **AGGREGATE** | | **+5.0** |

**Aggregate Score: +5.0 — HOLD**

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | DO NOT ENTER | Price near 52-week high (429.4p) with no oversold conditions. Wait for pullback to BB Lower (~374p) with RSI < 35 and CCI < −100. |
| **Current holders** | HOLD | Bullish trend and regime (98.0% bull) intact. Consider trimming 25-30% of position near 420-429p resistance, then re-accumulating on dips. |
| **Traders** | WAIT | Price at BB Middle (404.4p) — neither oversold nor overbought. No edge for mean-reversion entry. Watch for a break above 429.4p (new high) as a trend continuation signal. |

- **Entry:** Wait for Close ≤ 374.4p (BB Lower) AND RSI(14) < 35 AND CCI(20) < −100 AND declining GARCH vol
- **Stop-Loss:** 370.6p (nearest support) or 374.4p (BB Lower, whichever breaks first)
- **Target:** 404.4p (BB Middle Band — primary target); 429.4p (52-week high — extended target)

### Risk Factors
- **Bearish Volume Divergence:** CMF −0.018 and OFI −0.79 with volume at 10th percentile despite the recent rally from 355p to 429p. The price gain (+21% from Sept low) is not confirmed by money flow — a reversal signal.
- **MFI(14) at 182.5 (extreme):** This is exceptionally elevated and suggests overbought conditions that could precede a short-term pullback to the BB Middle (~404p) or lower.
- **No Structure Confirmation:** Zero HH/HL/LH/LL/BOS/CHoCH signals in the structure module — MKS.L remains in a range-bound oscillation without confirmed trend structure. A break below 370p would break the recent uptrend.

### When This Signal Is Invalidated
- **Price breaks below 370.6p (nearest support):** → Signal becomes **SELL** (trend structure breaks, HMM Bull confidence threatened)
- **Price breaks above 429.4p (52-week high) with volume surge:** → Signal becomes **BUY** (breakout from range, new trend potential)
- **HMM regime flips to State 1 (Bear):** → Signal becomes **SELL** (bull regime lost, trend reversal confirmed)
- **RSI drops below 35 + price hits BB Lower:** → Signal becomes **BUY** (`vol_filtered_meanrev` entry conditions aligning)

---

*Report generated: 2026-10-28 | Data point: 2026-10-28 → 2026-10-28 | Data: `data/analysis-data/MKS.L.csv` (5,053 rows) | Strategy: `data/reports/strategies/MKS.L/2026-10-26.md` → Target: `vol_filtered_meanrev`*
