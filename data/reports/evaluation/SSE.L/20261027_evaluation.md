# Market Situation Evaluation: SSE (SSE.L)

**Evaluation Date:** 2026-10-27
**Actual Date Used:** 2026-10-27
**Ticker:** SSE.L (SSE)
**Price:** 2490.0
**Data Range:** 2006-10-27 to 2026-10-27 (5,053 rows)
**Sector:** Utilities
**Strategy Reference:** `data/reports/strategies/SSE.L/20261022.md`

---

## Executive Summary

**Signal:** HOLD
**Confidence:** Medium

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🟢 BULLISH | 🟡 Medium | Price above EMA50/200 with positive MA slopes, but SuperTrend bearish and ADX weak (11.8) |
| **Momentum** | 🟡 CAUTIOUS | 🟢 High | RSI 50.1 at exact midpoint; MACD histogram negative (-4.7); 5/6 momentum indicators show no clear bias |
| **Return** | 🟢 POSITIVE | 🟢 High | +31.8% 1Y return, +7.2% 3M, outperforming FTSE 100 by +23.3% |
| **Structure** | 🟡 CAUTIOUS | 🟡 Medium | Consolidation between 2399 support and 2526 resistance (1.5% away); no BOS/CHoCH detected |
| **Volatility** | 🟡 NORMAL | 🟢 High | ATR normalized 2.15% elevated but percentile at 10th (historically low); BB width 6.5%, price at 44% of bands |
| **Volume** | 🔴 BEARISH | 🟡 Medium | MFI -42.3 deeply negative; ADL -81.5M outflows; only CMF +0.08 marginally positive — 3 of 8 volume indicators bearish |
| **Regime** | 🔴 BEAR | 🟡 Medium | HMM state 2 (bearish) at 54.4%; regime flips constantly between states 0 and 2 over past month |
| **Overall** | 🟡 HOLD | 🟡 Medium | Mixed: strong 1Y return and intact uptrend vs. bearish volume, flat momentum, unstable regime |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | 2,490.0 | 0.4% below EMA20 (2500.7), 1.0% above EMA50 (2465.3) |
| 52-Week Range | 1,843.0 – 2,767.5 | 71.2% of range from low; 9.9% below 52W high |
| P/E (TTM) | N/A | EPS TTM null — no P/E data available |
| Dividend Yield | N/A | Dividend data null — no yield available |
| Beta (20d) | 0.57 | Defensive — low volatility vs FTSE 100 |
| RS vs FTSE 100 | +23.3% | Strong outperformance over 20-day window |

### Strategy Alignment Summary

#### Entry conditions

| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| **RSI_Pullback: Close > EMA200** | 2490 > 2385.1 | ✅ MET |
| **RSI_Pullback: MA200_slope_20d > 0** | 2.79 > 0 | ✅ MET |
| **RSI_Pullback: RSI14 35–45 dip zone** | RSI 50.1 — outside range | ❌ NOT MET |
| **RSI_Pullback: MACD_line > MACD_signal** | 22.0 < 26.7 — MACD below signal | ❌ NOT MET |
| **Score3+: EMA20 > EMA50** | 2500.7 < 2465.3 | ❌ NOT MET |
| **Score3+: RSI14 > 50** | RSI 50.1 (barely) | ⚠️ CAUTION |
| **Score3+: MACD_line > MACD_signal** | ❌ (same as RSI_Pullback) | ❌ NOT MET |
| **Score3+: CMF20 > 0** | +0.08 | ✅ MET |
| **Score3+: OFI > 0** | +0.175 | ✅ MET |
| **Key observation: ADX trend strength** | 11.8 — weak trend zone | ⚠️ CAUTION — not ideal for strategy execution |

**Strategy Verdict:** Neither RSI_Pullback nor Score3+ entry criteria are currently met. RSI at 50.1 is above the 35–45 pullback zone and MACD remains below signal line. Score3+ composite is 2/5 factors (CMF, OFI, borderline RSI) — below the 3+ threshold needed for entry. No new positions warranted.

#### Exit conditions

| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| **RSI_Pullback: RSI > 65 (exit)** | RSI 50.1 — far from exit | ✅ NOT MET (no exit) |
| **Score3+: Score drops below 1** | Score 2/5 — above threshold | ✅ NOT MET (no exit) |
| **Key observation: Regime stability** | HMM flipping daily between states 0 and 2 | ⚠️ CAUTION — regime noise may trigger false exits |

**Strategy Verdict:** No exit conditions are triggered. Current holders of active RSI_Pullback or Score3+ positions should remain in their positions — neither exit signal is active. However, the constant regime flipping means any existing positions should have tight stops.

### Signal Summary

**Current Signal: HOLD / NEUTRAL-CAUTIOUS**

SSE.L is in a consolidation phase within a longer-term uptrend. The 200-day EMA at 2385 remains intact and price is 4.4% above it, supporting the bull case. However, near-term momentum is flat (RSI at 50), volume is bearish (MFI -42.3, ADL outflows), and the HMM regime is stuck flipping between states 0 and 2 daily — making this a poor environment for initiating new positions. Non-holders should wait for either a deeper pullback to the EMA200 (2385) with RSI 35–45 for an RSI_Pullback entry, or a decisive break above 2526 resistance with volume confirmation for a trend-following entry. Current holders can maintain positions with a stop at 2385 (EMA200).

---

### Aggregate Score

| # | Dimension | Signal | Score (-3.0 to +3.0) | Weight | Weighted |
|---|-----------|--------|-------------|--------|----------|
| 1 | **Trend** | Bullish | +1.0 | 20% | +0.20 |
| 2 | **Momentum** | Neutral | +0.0 | 15% | +0.00 |
| 3 | **Return** | Positive | +1.5 | 15% | +0.23 |
| 4 | **Structure** | Cautious | +0.5 | 15% | +0.08 |
| 5 | **Volatility** | Normal | -0.5 | 10% | -0.05 |
| 6 | **Volume** | Bearish | -1.0 | 10% | -0.10 |
| 7 | **Regime** | Bear | -2.0 | 15% | -0.30 |
| | **AGGREGATE** | | | **100%** | **+0.06** |

**Aggregate Score: +0.06 — HOLD**

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | WAIT for better entry | Neither RSI_Pullback nor Score3+ entry criteria met; RSI not in 35–45 pullback zone; MACD below signal. Wait for pullback to ~2385 (EMA200) or break above 2526 resistance with volume |
| **Current holders** | HOLD — monitor 2385 (EMA200) | Uptrend intact above EMA200; +31.8% YTD outperformance. No exit signal from either strategy. Watch HMM regime stabilization |
| **Traders** | AVOID new entries | Weak ADX (11.8), mixed volume signals (3 bearish vs 2 bullish), and regime flipping every 1–2 days create an uncertain trading environment |

- **Entry (RSI_Pullback):** RSI 35–45 + Close > EMA200 + MACD crossing above signal. Price targets: ~2385 (EMA200) or ~2399 (swing low).
- **Entry (Score3+):** Score 3+/5 with EMA20 > EMA50, RSI > 50, MACD > signal, CMF > 0, OFI > 0. None currently aligned.
- **Stop-Loss:** 2350 (below swing low 2399 and EMA200 2385, provides 1.4% buffer)
- **Target:** 2586 (Donchian upper / swing high), secondary 2767.5 (52-week high)

### Risk Factors
- **HMM Regime Instability:** Regime has flipped between states 0 and 2 on virtually every trading day over the past month (Sep 22 → Oct 27). The HMM cannot settle into a clear directional bias. The strategy report confirms HMM-based approaches were disastrous on SSE.L (-73.5% return, 261 trades). This regime noise undermines all regime-dependent signals.
- **MACD Dead Cross Persistence:** MACD histogram is -4.7 (line 22.0 below signal 26.7). If this persists, momentum could deteriorate toward the EMA50 (2465) and then EMA200 (2385), a 4.4% downside from current levels.
- **Volume Divergence:** MFI at -42.3 and ADL at -81.5M suggest institutional selling pressure despite price holding above key EMAs. A breakdown in support could accelerate as stop losses trigger below 2385.
- **Resistance at 2526:** Price is within 1.5% (37 points) of nearest resistance. A rejection here sends price back toward 2399 support (3.7% downside).

### When This Signal Is Invalidated
- **Break above 2586 (Donchian high / swing high) with volume percentile > 80 and rising RSI** → Signal becomes **BUY** — trend resumes, Donchian breakout confirms new leg higher
- **Break below 2385 (EMA200) with HMM settling to state 2 (prob > 70%) for 3+ consecutive days** → Signal becomes **SELL** — primary uptrend broken, defensive position required
- **RSI drops below 40 with MACD histogram turning more negative and MFI below -50** → Signal becomes **SELL** — pullback worsens from corrective to trend-change territory; RSI_Pullback entry criteria met only with deteriorating momentum

---

*Report generated: 2026-10-27 | Data point: 2026-10-27 → `2026-10-27` | Data: `data/analysis-data/SSE.L.csv` (5,053 rows) | Strategy: `data/reports/strategies/SSE.L/20261022.md`*
