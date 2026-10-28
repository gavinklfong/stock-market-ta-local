# Market Situation Evaluation: HSBC Holdings (HSBA.L)

**Date Used:** 2026-10-28
**Ticker:** HSBA.L (HSBC Holdings)
**Price:** 1,297p
**Data Range:** 2006-10-30 to 2026-10-28 (5,052 rows)
**Sector:** Financial Services
**Strategy Reference:** `data/reports/strategies/HSBA.L/20261021.md`
**Target Strategy:** `ADX Momentum`

---

## Executive Summary

**Signal:** SELL
**Confidence:** Medium

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🔴 BEARISH | 🟢 High | Price below EMA20/50, SuperTrend DOWN, MA20/50 slopes negative, -DI >> +DI |
| **Momentum** | 🔴 BEARISH | 🟢 High | RSI 28 deeply oversold, MACD strongly negative, ROC -13.4% bearish |
| **Return** | 🟢 POSITIVE | 🟢 High | +23.5% 1Y strong, but -14.1% 1M and -18.3% 3M — recent sharp drawdown |
| **Structure** | 🔴 BEARISH | 🟡 Medium | No HH/HL patterns, price at swing low territory, nearest support only 2.3% away |
| **Volatility** | 🔴 HIGH | 🟢 High | ATR 90th percentile, BB %B -5.1% (below lower band!), GARCH vol 2.02 extreme |
| **Volume** | 🔴 BEARISH | 🟡 Medium | Volume 10th percentile (very thin), OBV steeply declining, MFI -44 |
| **Regime** | 🔴 BEAR | 🟢 High | HMM State 1 (bear) at 77.7%, persistent since Oct 1 |
| **Overall** | 🔴 SELL | 🟡 Medium | 6 bearish, 1 positive; bear regime confirmed, but RSI deeply oversold |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | 1,297p | Sharp decline from Sep 17 high of 1,537p (-15.6% from recent peak); today's close slightly above yesterday's crash (1,291p) |
| 52-Week Range | 1,025 – 1,610p | 69.4% of range — near the bottom half, not at 52-week low |
| P/E (TTM) | N/A | Null in current CSV — no fundamentals in data |
| Dividend Yield | N/A | Null in current CSV — HSBC is a high-yield financial stock |
| Beta (20d) | 2.311 | **Very high** — 2.3x FTSE 100 volatility (amplified moves) |
| RS vs FTSE 100 | 12.12 | Positive RS despite drawdown — still outperforming FTSE 100 relatively |

### Strategy Alignment Summary — `ADX Momentum`

#### Entry conditions (from `ADX Momentum`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| ADX > 25 | 34.9 ✅ | ✅ MET — ADX is well above 25, indicating strong trend |
| +DI > -DI | 13.2 vs 47.8 ❌ | ❌ NOT MET — minus DI dominates by 3.6x, confirming downtrend |
| RSI > 50 | 28.0 ❌ | ❌ NOT MET — deeply oversold, far below 50 threshold |
| MACD > Signal | -44.0 vs -34.8 ❌ | ❌ NOT MET — MACD below signal, momentum negative |

**Strategy Entry Verdict:** 1 of 4 entry conditions MET. The ADX Momentum strategy is a trend-following approach designed to enter when a strong bullish trend is confirmed (ADX > 25 with +DI dominant and bullish momentum). Current conditions are the exact opposite — the stock is in a strong **downtrend** (ADX 34.9 is high, but it's measuring the downtrend, not uptrend) with -DI dominating +DI by 3.6x. **This strategy would NEVER fire an entry signal at current levels.** The high ADX reflects the intensity of the current sell-off, not an opportunity for a bullish entry.

#### Exit conditions (from `ADX Momentum`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| ADX < 20 | 34.9 ❌ | ✅ CONFIRMED (not triggered) — trend still strong |
| +DI < -DI | 13.2 < 47.8 ❌ | ✅ CONFIRMED (not triggered) — bearish trend intact |
| RSI < 40 | 28.0 ✅ | ⚠️ TRIGGERED — RSI deep in oversold territory |

**Strategy Exit Verdict:** The RSI < 40 exit condition is technically triggered, which for an existing position would signal an exit. However, the ADX Momentum strategy is designed to exit when the bullish trend weakens (ADX < 20) or direction flips (+DI < -DI). The RSI exit is meant to capture profits during uptrends before overbought conditions reverse — at RSI 28, this is an extreme oversold reading, not a profit-taking signal. For holders, the bearish trend structure (-DI dominating, price below EMAs, bear regime) suggests further downside risk, but the deeply oversold RSI (28) makes immediate selling at these levels risky — a bounce is statistically likely.

The ADX Momentum strategy is a trend-following approach designed to buy strong uptrends and exit when they weaken. **Current conditions show a strong downtrend — this is the opposite of what the strategy seeks.** The strategy would have been exited long ago during this decline, and would not enter now.

{2–3 sentence narrative explaining the overall signal, who should act, and for whom}

**Narrative:** HSBA.L is in a **strong confirmed downtrend** — the ADX is elevated at 34.9, -DI dominates +DI by 3.6x, and the HMM regime is bearish at 77.7%. For non-holders, this is NOT a buying opportunity for the ADX Momentum strategy (0/4 bullish entry conditions met). For current holders, the trend remains intact with further downside possible, but the deeply oversold RSI (28) and price below the lower Bollinger Band (-5.1% %B) suggest a near-term bounce is likely — selling at these levels could mean selling at the bottom of the move. The signal is SELL due to the overwhelming bearish dimension count, but with the critical caveat that entry conditions for the recommended strategy are nowhere near being met.

---

### Aggregate Score

| # | Dimension | Signal | Score |
|---|-----------|--------|-------|
| 1 | **Trend** | 🔴 BEARISH | -2.5 |
| 2 | **Momentum** | 🔴 BEARISH | -2.0 |
| 3 | **Return** | 🟢 POSITIVE | +1.0 |
| 4 | **Structure** | 🔴 BEARISH | -2.0 |
| 5 | **Volatility** | 🔴 HIGH | -1.5 |
| 6 | **Volume** | 🔴 BEARISH | -1.0 |
| 7 | **Regime** | 🔴 BEAR | -2.0 |
| | **AGGREGATE** | | **-10.0** |

**Aggregate Score: -10.0 — SELL**

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | DO NOT ENTER — 0/4 bullish entry conditions for ADX Momentum | Strong downtrend with -DI >> +DI, RSI oversold, bear regime dominant; trend-following strategy needs bullish trend |
| **Current holders** | CAUTIOUS SELL — further downside risk but oversold bounce likely | Bear regime at 77.7%, ADX strong in downtrend; but RSI 28 + below BB Lower suggests near-term bounce, consider limit orders above 1,350 |
| **Traders** | AVOID — high vol + strong downtrend + oversold = whipsaw risk | Beta 2.3x means violent swings; thin volume (10th percentile) increases slippage; wait for trend reversal confirmation |

- **Entry:** Re-evaluate when ADX > 25 AND +DI > -DI AND RSI > 50 AND MACD > Signal — none of these bullish conditions are met
- **Stop-Loss:** N/A for new entries (not entering); for holders, 1,263 (Donchian Lower, 2.6% below) would confirm breakdown to new lows
- **Target (bounce):** 1,371 (EMA200, 5.7% above), 1,399 (EMA20, 7.9% above); if bounce sustains, 1,445 (EMA50, 11.4% above)

### Risk Factors
- **Deeply oversold (RSI 28, percentile 5%):** RSI at 5th percentile of historical range means 95% of historical readings were higher. This is a statistically extreme oversold level that historically precedes short-term bounces — selling at RSI 28 is often selling at the bottom
- **Beta 2.3x — amplified downside:** HSBA's 20-day beta of 2.31 means it moves 2.3x the FTSE 100. In a volatile/bear regime, this amplifies both gains and losses — the current -15.6% drawdown from the Sep peak is consistent with beta-driven amplification
- **Volume extremely thin (10th percentile):** Only 10th percentile of historical volume means the move lacks broad participation conviction, but also means any bounce could be weak and short-lived. Thin volume increases the risk of erratic price action and slippage

### When This Signal Is Invalidated
- **RSI > 50 AND +DI > -DI AND ADX > 25** → Signal upgrades to BUY (ADX Momentum entry conditions all met — strong bullish trend confirmed)
- **Price closes above EMA20 (1,396p)** → Signal becomes HOLD (short-term trend reversal, but need more confirmation)
- **HMM State 1 (bear) probability drops below 50%** → Signal becomes WAIT (regime shift underway, trend may be stabilizing)

---

*Report generated: 2026-10-28 | Data point: 2026-10-28 → 2026-10-28 | Data: `data/analysis-data/HSBA.L.csv` (5,052 rows) | Strategy: `data/reports/strategies/HSBA.L/20261021.md` → Target: `ADX Momentum`*
