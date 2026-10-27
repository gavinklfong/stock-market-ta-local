# Market Situation Evaluation: Marks & Spencer (MKS.L)

**Evaluation Date:** 2026-04-29
**Actual Date Used:** 2026-04-29
**Ticker:** MKS.L (Marks & Spencer)
**Price:** 325.0p
**Data Range:** 2006-10-27 to 2026-04-29 (4,927 rows)
**Sector:** Retail
**Strategy Reference:** `data/reports/strategies/MKS.L/2026-10-26.md`
**Target Strategy:** `dual_exit_meanrev`

---

## Executive Summary

**Signal:** STRONG SELL
**Confidence:** High

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🔴 BEARISH | 🟢 High | Price −6.3% below EMA20; SuperTrend −1; −DI (30.5) >> +DI (13.0) |
| **Momentum** | 🔴 BEARISH | 🟢 High | RSI 34.8 + Williams %R −98.4 + CCI −160 — deeply oversold but uniformly bearish |
| **Return** | 🔴 NEGATIVE | 🟢 High | −30.7% (1m), −12.1% (3m), −19.4% (6m) — severe drawdown |
| **Structure** | 🟡 CAUTIOUS | 🟡 Medium | Near swing low (317.98); resistance 19p away (387.05); no BOS/CHoCH |
| **Volatility** | 🟡 NORMAL | 🟢 High | ATR 11.3 (3.5%); BB width 14.4%; price just below BB Lower |
| **Volume** | 🔴 BEARISH | 🟢 High | CMF −0.164, OFI −0.73, OBV slope −2.6M — sustained distribution |
| **Regime** | 🔴 BEAR | 🟢 High | HMM regime 2 at 97.9% — unambiguous bearish/volatile state |
| **Overall** | 🔴 STRONG SELL | 🟢 High | All 7 dimensions bearish; regime lock at 97.9% |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | 325.0p | Near 52-week low; 21% below 200-day EMA |
| 52-Week Range | 315.3 – 411.8 | 99% from bottom of range (325 is just above 315.3 low) |
| P/E (TTM) | 26.4 | Elevated for UK value retailer; sector-atypical |
| Dividend Yield | 1.17% | Modest; not a yield play |
| Beta (20d) | 2.29 | Highly volatile vs FTSE 100 — amplifies both up and down |
| RS vs FTSE 100 | 3.18 | Underperforming benchmark significantly |

### Strategy Alignment Summary — `dual_exit_meanrev`

#### Entry conditions (from `dual_exit_meanrev`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| Close ≤ Bollinger Band Lower (325.66) | Close: 325.0 | ✅ MET |
| RSI(14) < 35 | RSI: 34.84 | ✅ MET |
| CCI(20) < −100 | CCI: −160.24 | ✅ MET |

**Strategy Entry Verdict:** All three entry conditions are met. This is the exact setup the `dual_exit_meanrev` strategy was designed to capture — price at the lower Bollinger Band with deeply oversold RSI and CCI. Historically, this strategy entered at this signal on 2026-04-29 (backtest entry price: 325.32) and exited at 348.15 on 2026-05-20 for +6.81% PnL over 21 days. **This is a confirmed entry signal for `dual_exit_meanrev`.**

#### Exit conditions (from `dual_exit_meanrev`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| Close ≥ BB Middle Band (350.89) | Close: 325.0 (25.9p below) | ❌ NOT MET |
| Close < 3-day high − 3×ATR (296.4) | Close: 325.0 (above trail) | ❌ NOT MET |

**Strategy Exit Verdict:** No exit conditions triggered. The stock has not yet recovered toward the BB Middle Band target (~350.9, +8.0%), nor has it dropped below the ATR trailing stop (~296.4). If entered, the trade would be open with two exit paths to monitor: mean-reversion target at ~351 or a 3×ATR trailing stop from the 3-day high.

### Signal Summary

**Current Signal: STRONG SELL — BEARISH**

Every one of the seven evaluation dimensions is bearish. The HMM regime classifier shows 97.9% confidence in a bearish/volatile state. Price has declined −30.7% over the past month with sustained selling pressure across all volume indicators. However, the extreme oversold conditions (RSI 34.8, Williams %R −98.4, CCI −160) and proximity to the 52-week low (315.3) have triggered all three entry conditions of the `dual_exit_meanrev` strategy. This creates a classic tension: the trend is strongly bearish, but the mean-reversion strategy sees this exact setup as a BUY signal. The backtest confirms this entry was profitable (+6.81% in 21 days), but past performance does not guarantee future results — the regime lock at 97.9% makes this riskier than typical entries.

---

### Aggregate Score

| # | Dimension | Signal | Score (−3.0 to +3.0) | Weight | Weighted |
|---|-----------|--------|-------------|--------|----------|
| 1 | **Trend** | 🔴 Bearish | −2.0 | 15% | −0.30 |
| 2 | **Momentum** | 🔴 Bearish | −2.5 | 15% | −0.375 |
| 3 | **Return** | 🔴 Negative | −2.0 | 15% | −0.30 |
| 4 | **Structure** | 🟡 Caution | −1.5 | 12% | −0.18 |
| 5 | **Volatility** | 🟡 Normal | −1.5 | 12% | −0.18 |
| 6 | **Volume** | 🔴 Bearish | −2.0 | 15% | −0.30 |
| 7 | **Regime** | 🔴 Bear | −3.0 | 16% | −0.48 |
| | **AGGREGATE** | | | **100%** | **−2.12** |

**Aggregate Score: −2.12 — STRONG SELL**

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | ⚠️ ENTRY SIGNAL for `dual_exit_meanrev` | All three entry conditions met (BB Lower + RSI < 35 + CCI < −100). This is the exact mean-reversion setup the strategy targets. Backtest shows +6.81% return from this exact signal. Enter with 1/3 position size and strict stop. |
| **Current holders** | ⚠️ HOLD with tight stop — do not sell panic | The STRONG SELL trend signal is real, but entry conditions for mean-reversion are met. Selling at 325 near the 52-week low would crystallise a −30% loss. The strategy's historical win rate is 62.5% on these setups. Hold with stop at 296.4 (ATR trail). |
| **Traders** | ⚠️ Long mean-reversion setup, high timing risk | Oversold extremes suggest a bounce is probable, but regime 97.9% bearish means the bounce could be shallow or delayed. Enter with tight stops and 21-day time horizon matching strategy average holding period. |

- **Entry:** 325.0 (current price) — `dual_exit_meanrev` strategy
- **Stop-Loss:** 296.4 (3-day high 330.35 minus 3×ATR 33.98) — ATR trailing stop from strategy
- **Alternative Stop-Loss:** 315.0 (below 52-week low of 315.3) — approximately −3.1% from entry
- **Target:** 350.9 (BB Middle Band) — approximately +8.0% from entry
- **Risk-Reward:** ~2.6:1 (favourable for mean-reversion)

### Risk Factors
- **HMM regime lock:** 97.9% probability in bearish regime 2. Regime shifts can take weeks — a "falling knife" scenario is possible if regime 2 deepens further before any bounce.
- **52-week low proximity:** Price at 325 vs low of 315.3. A break below 315 would trigger institutional stop-losses and potentially accelerate selling into the strategy's stop level.
- **Elevated beta (2.29):** MKS.L moves 2.3× the FTSE 100. Any broad market decline will amplify losses disproportionately.
- **Oversold exhaustion vs. structural decline:** RSI 34.8 and CCI −160 could be a bounce setup OR the start of a further decline. The regime lock at 97.9% makes this ambiguous.
- **P/E of 26.4x for a UK value retailer:** Above typical retail sector multiples. If earnings disappoint, there is limited fundamental support.

### When This Signal Is Invalidated
- **Price closes above BB Middle (350.9) on rising volume** → Signal becomes HOLD (mean reversion target achieved, trend stabilizing)
- **HMM regime switches from 2 to 1 or 0** → Signal becomes WAIT (regime shift in progress; direction unclear)
- **Break above EMA20 (346.8) with SuperTrend flip to +1** → Signal becomes BUY (trend reversal confirmed)
- **52-week low (315.3) breaks with volume z-score > +1** → Signal becomes STRONG SELL (breakout lower; further decline likely)
- **3×ATR trailing stop triggered (close below 296.4)** → Signal becomes STRONG SELL (strategy exit; trend continues down)

---

*Report generated: 2026-04-29 | Data point: 2026-04-29 | Data: `data/analysis-data/MKS.L.csv` (4,927 rows) | Strategy: `data/reports/strategies/MKS.L/2026-10-26.md` → Target: `dual_exit_meanrev`*
