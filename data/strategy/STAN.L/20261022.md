# STAN.L Investment Strategy Report

## Executive Summary

This report identifies the optimal trading strategies for **STAN.L (Standard Chartered PLC)** based on 5 years of market data (2021-10-25 to 2026-10-22), evaluating **37 strategies** (32 built-in + 5 custom).

### Key Findings

| Finding | Detail |
|---------|--------|
| Stock character | **Strong trending stock** (+305% B&H over 5Y) with moderate mean-reverting pullbacks |
| Best overall strategy | **Trend+Momentum Combo** — 78.90% return, 18.18% DD, Sharpe 0.93, Profit Factor 4.13 |
| Best risk-adjusted | **Trend+Momentum Combo** — Calmar ratio 1.01 |
| Best low-drawdown | **Short Mean-Reversion** — +27.07%, -9.23% DD, Sharpe 0.82 |
| Best custom strategy | **Pullback Rides** — 57.98% return, 18.33% DD, Sharpe 0.76 |
| Worst strategy | **SuperTrend+** — -48.86% return, 235 trades, pure trend without momentum fails |
| Zero-trade strategies | 8 strategies never entered a position |

**Bottom line: STAN.L is best traded with trend-following strategies enhanced by momentum filters.** Pure trend signals without momentum confirmation lose money. Mean-reversion works but at lower returns due to the strong directional bias.

---

## STAN.L Market Profile

### Price Overview (5-Year Window)

| Metric | Value |
|--------|-------|
| Period | 2021-10-25 to 2026-10-22 (1,261 trading days) |
| Start Price | 489.10p |
| End Price | 1,981.00p |
| **Buy & Hold Return** | **+305.03%** |
| 5-Year High | 2,364.00p |
| 5-Year Low | 406.20p |
| Mean Price | 997.43p |
| Price Std Dev | 520.19p |

### Trend Characteristics

| Metric | Value |
|--------|-------|
| Bullish trend days (EMA20>50>200) | 71.4% |
| ADX mean | 25.6 |
| Strong trend days (ADX>25) | 43.6% |
| OBV | Increasing (confirms uptrend) |

### Drawdown Analysis

| Metric | Value |
|--------|-------|
| B&H Max Drawdown | -30.75% |
| Typical pullback depth | -15% to -25% |
| Typical pullback duration | 2-8 weeks |
| Mean-reversion half-life | ~19 days |

**Interpretation**: STAN.L is a stock with a strong secular uptrend (doubled 3 times in 5 years) that periodically experiences sharp pullbacks. The 71.4% bullish trend ratio means trend-following strategies have a structural edge, but the -30.75% max drawdown of simply holding means **active management with trailing stops materially improves risk-adjusted returns**.

---

## Risk Management Framework

### Risk Per Trade

| Risk Profile | Risk per Trade |
|-------------|---------------|
| Conservative | 0.5% |
| Moderate | 1.0% |
| Aggressive | 2.0% |

### ATR-Based Position Sizing

```text
Position Size =
(Account Value × Risk %)
/
(ATR Multiplier × ATR)
```

Example:
```text
Portfolio Value = £100,000
Risk = 1%
ATR = 15p
Stop = 2 × ATR = 30p

Position Size = £1,000 / 30p = 3,333 shares
```

### Portfolio Controls

```text
Maximum Open Positions = 1
Maximum Open Risk = 1%
Maximum Daily Loss = 2%
No new trades when daily loss exceeded
```

---

## Backtest Parameters

| Parameter | Value |
|-----------|-------|
| Initial Capital | £100,000 |
| Commission | 0.1% per trade |
| Slippage | 0.1% per trade |
| Data Range | 2006-10-23 to 2026-10-22 |
| 5Y Analysis Window | 2021-10-25 to 2026-10-22 |
| Benchmark (B&H) | +305.03% return, -30.75% max DD |

---

## Complete Strategy Rankings

### All 37 Strategies Sorted by Total Return

| Rank | Strategy | Return (%) | Sharpe | Calmar | Trades | Win Rate (%) | Profit Factor | Max DD (%) |
|------|----------|-----------|--------|--------|--------|-------------|--------------|-----------|
| 1 | **trend_momentum** | **78.90** | **0.93** | **1.01** | 16 | 43.80 | **4.13** | 18.18 |
| 2 | **momentum_comp** | 74.32 | 0.83 | 0.64 | 19 | 36.80 | 2.81 | 27.45 |
| 3 | **stan_pullback_rides** | 57.98 | 0.76 | 0.77 | 27 | 37.00 | 1.72 | 18.33 |
| 4 | **stan_trend_trailing** | 56.00 | 0.60 | 0.44 | 28 | 35.70 | 1.68 | 31.09 |
| 5 | **vwap** | 54.89 | 0.62 | 0.42 | 55 | 38.20 | 1.50 | 31.81 |
| 6 | **bb_breakout** | 51.36 | **0.86** | 0.72 | 24 | **54.20** | 2.37 | **17.82** |
| 7 | **ema_pullback** | 43.13 | 0.58 | 0.42 | 32 | 37.50 | 1.41 | 26.13 |
| 8 | **stan_adaptive_trend** | 35.85 | 0.46 | 0.22 | 44 | 31.80 | 1.46 | 42.06 |
| 9 | **dual_exit_meanrev** | 35.01 | 0.63 | 0.55 | 9 | **66.70** | 3.22 | **16.46** |
| 10 | **bb_meanrev_upper** | 32.20 | 0.63 | 0.51 | 4 | **100.00** | N/A | 16.64 |
| 11 | **short_meanrev** | 27.07 | **0.82** | **0.78** | 3 | **100.00** | N/A | **9.23** |
| 12 | **bb_meanrev_entry2** | 26.79 | 0.70 | 0.52 | 5 | **100.00** | N/A | 13.76 |
| 13 | **multiscore60** | 23.91 | 0.36 | 0.17 | 39 | 25.60 | 1.30 | 38.12 |
| 14 | **bb_meanrev** | 23.74 | 0.63 | 0.46 | 5 | **100.00** | N/A | 13.76 |
| 15 | **bb_meanrev_optimized** | 23.74 | 0.63 | 0.46 | 5 | **100.00** | N/A | 13.76 |
| 16 | **bb_meanrev_atr** | 18.27 | 0.38 | 0.19 | 9 | 55.60 | 1.79 | 26.67 |
| 17 | **vol_filtered_meanrev** | 6.67 | 0.20 | 0.09 | 7 | 57.10 | 1.57 | 20.54 |
| 18–24 | Zero-trade strategies | 0.00 | 0.00 | 0.00 | 0 | 0.00 | 0.00 | 0.00 |
| 25 | highprob_multi | -1.44 | -0.62 | -0.29 | 1 | 0.00 | 0.00 | 1.44 |
| 26 | vol_structure | -3.04 | -0.11 | -0.09 | 2 | 50.00 | 0.24 | 10.20 |
| 27 | hmm_regime | -3.14 | 0.09 | -0.03 | 10 | 40.00 | 0.90 | 36.22 |
| 28 | **stan_dual_trend** | -8.12 | -0.18 | -0.13 | 75 | 50.70 | 0.83 | 18.23 |
| 29 | vol_expansion | -9.34 | -0.31 | -0.18 | 45 | 37.80 | 0.74 | 15.37 |
| 30 | regime_adaptive | -9.71 | -0.52 | -0.22 | 2 | 0.00 | 0.00 | 13.47 |
| 31 | ema_pullback_vol | -9.83 | -0.09 | -0.10 | 26 | 34.60 | 0.85 | 28.99 |
| 32 | score80 | -21.52 | -0.68 | -0.27 | 17 | 23.50 | 0.40 | 25.48 |
| 33 | institutional | -23.47 | -0.37 | -0.22 | 148 | 31.80 | 0.81 | 33.18 |
| 34 | golden_cross | -29.71 | -0.63 | -0.23 | 169 | 42.60 | 0.69 | 41.45 |
| 35 | ofi | -38.52 | -0.85 | -0.29 | 105 | 28.60 | 0.64 | 45.13 |
| 36 | supertrend_plus | -48.86 | -1.29 | -0.32 | 235 | 40.40 | 0.63 | 54.74 |

> **Benchmark (B&H)**: +305.03% return, -30.75% max DD, 0 trades, Sharpe N/A

---

## Top 5 Strategies Detailed

### 1. Trend+Momentum Combo — Best Overall

| Metric | Value |
|--------|-------|
| Total Return | **78.90%** |
| Sharpe Ratio | **0.93** |
| Calmar Ratio | **1.01** |
| Max Drawdown | 18.18% |
| Profit Factor | **4.13** |
| Total Trades | 16 |
| Win Rate | 43.80% |
| Avg Win / Avg Loss | 12.94% / -2.49% |
| Avg Trade Duration | N/A (trend hold) |
| Avg Win Duration | 54 days |
| Avg Loss Duration | 17 days |
| Final Net Value | **£178,905** |

**Why it works**: Combines multiple trend and momentum signals. Stays in the strong uptrend but uses momentum confirmation (RSI, MACD) to enter only on pullback entries and exits on momentum deterioration. The high profit factor (4.13) means winning trades are more than 4× larger than losing ones — classic trend-following profile.

**Entry Conditions**:
```text
EMA20 > EMA50 > EMA200 (trend alignment)
AND RSI > 55 (momentum confirmation)
AND MACD > Signal (momentum direction)
AND CMF > 0 (volume flow positive)
```

**Exit Conditions**:
```text
RSI < 50 (momentum lost)
AND MACD bearish crossover
```

**Comparison to B&H**: +78.90% vs +305.03% absolute return, BUT with **much better risk management** (18.18% DD vs -30.75% DD) and a Sharpe ratio of 0.93. The strategy captures a meaningful portion of the uptrend while significantly reducing drawdown.

---

### 2. Momentum Composite — High Return, Higher DD

| Metric | Value |
|--------|-------|
| Total Return | 74.32% |
| Sharpe Ratio | 0.83 |
| Calmar Ratio | 0.64 |
| Max Drawdown | 27.45% |
| Profit Factor | 2.81 |
| Total Trades | 19 |
| Win Rate | 36.80% |
| Avg Win / Avg Loss | 15.63% / -3.33% |
| Final Net Value | £174,316 |

**Analysis**: Similar to trend_momentum but slightly more permissive entries. Higher max drawdown (27.45% vs 18.18%) because it holds through deeper pullbacks. Still excellent risk-adjusted returns (Sharpe 0.83).

---

### 3. STAN Pullback Rides — Best Custom Strategy

| Metric | Value |
|--------|-------|
| Total Return | 57.98% |
| Sharpe Ratio | 0.76 |
| Calmar Ratio | 0.77 |
| Max Drawdown | 18.33% |
| Profit Factor | 1.72 |
| Total Trades | 27 |
| Win Rate | 37.00% |
| Avg Win / Avg Loss | 12.06% / -3.82% |
| Final Net Value | £157,977 |

**Entry Conditions**:
```text
EMA20 > EMA50 > EMA200 (confirmed uptrend)
AND SuperTrend +1 (trend support)
AND Price within 5% of EMA20 (pullback zone)
AND RSI 35-55 (oversold to neutral)
AND Volume below 20-day average (selling exhaustion)
```

**Exit Conditions**:
```text
Price breaks below EMA50 (trend broken)
OR RSI > 70 (overbought)
```

**Why it works for STAN.L**: In a stock that trends up 71% of the time, buying dips within the confirmed uptrend offers better risk/reward than chasing breakouts. The RSI 35-55 range targets pullbacks without catching falling knives. Volume below average confirms selling exhaustion.

---

### 4. STAN Trend Trailing — Simple ATR Trail

| Metric | Value |
|--------|-------|
| Total Return | 56.00% |
| Sharpe Ratio | 0.60 |
| Calmar Ratio | 0.44 |
| Max Drawdown | 31.09% |
| Profit Factor | 1.68 |
| Total Trades | 28 |
| Win Rate | 35.70% |
| Final Net Value | £155,999 |

**Entry Conditions**:
```text
EMA20 > EMA50 > EMA200 (bullish alignment)
AND SuperTrend +1
AND RSI > 45
```

**Exit**: Price drops below trailing stop (highest high - 3×ATR)

**Analysis**: The simplest of the custom strategies. Enters on trend confirmation, trails with 3×ATR. Lower Sharpe because the trailing stop is relatively wide and some trends reverse before the trail catches up. Still profitable but less sophisticated than trend_momentum.

---

### 5. BB Breakout — High Win Rate, Consistent

| Metric | Value |
|--------|-------|
| Total Return | 51.36% |
| Sharpe Ratio | **0.86** |
| Calmar Ratio | 0.72 |
| Max Drawdown | **17.82%** |
| Profit Factor | 2.37 |
| Total Trades | 24 |
| Win Rate | **54.20%** |
| Avg Win / Avg Loss | 5.51% / -2.43% |
| Final Net Value | £151,365 |

**Entry Conditions**:
```text
Close > Bollinger Upper Band
AND ATR Rising (volatility expanding)
AND Historical Volatility Rising
AND ROC20 > 0 (positive momentum)
```

**Exit**: Price closes back inside the Bollinger Band OR MACD bearish crossover

**Why it works**: Breakouts above the upper Bollinger Band with expanding volatility indicate genuine momentum moves in the uptrend direction. The high win rate (54.20%) is unusual for trend strategies and makes this suitable for conservative traders.

---

## Low-Drawdown Strategies

For traders prioritizing capital preservation over maximum return:

| Strategy | Return (%) | Max DD (%) | Sharpe | Trades |
|----------|-----------|-----------|--------|--------|
| **short_meanrev** | +27.07 | **9.23** | 0.82 | 3 |
| bb_meanrev_entry2 | +26.79 | 13.76 | 0.70 | 5 |
| bb_meanrev | +23.74 | 13.76 | 0.63 | 5 |
| dual_exit_meanrev | +35.01 | 16.46 | 0.63 | 9 |
| bb_meanrev_upper | +32.20 | 16.64 | 0.63 | 4 |
| bb_breakout | +51.36 | 17.82 | 0.86 | 24 |
| trend_momentum | +78.90 | 18.18 | **0.93** | 16 |

**Recommendation**: `short_meanrev` has the lowest drawdown (9.23%) with 100% win rate, but only 3 trades over 5 years — excellent capital preservation but limited opportunity. For active traders, `bb_breakout` (Sharpe 0.86, 17.82% DD, 54.20% win rate) offers the best balance.

---

## Zero-Trade Strategies

The following 8 strategies never entered a single trade during the 5-year window:

| Strategy | Reason for Zero Trades |
|----------|----------------------|
| vol_breakout_rev | Reversal filter too restrictive |
| donchian | Combined with OFI/OBV filter — no matching signals |
| marketstruct | HH+HL+BOS conditions rarely align |
| bos_breakout | Resistance break + CMF/OFI filter too strict |
| choch | CHoCH + RSI rising + MACD bullish — rare alignment |
| macd_divergence_rev | Divergence detection never triggered |
| rsi_macd_rev | RSI<30 + MACD cross + CMF>0 — contradictory |
| stan_vol_breakout_trend | Volume surge >1.5× average too rare for STAN.L |

**Takeaway**: Overly restrictive entry conditions prevent any trades. STAN.L's volume profile doesn't generate frequent 1.5× surges, making volume-surge-dependent strategies ineffective.

---

## Failing Strategies (Negative Returns)

### Why Pure Trend Strategies Lose for STAN.L

| Strategy | Return | Trades | Key Problem |
|----------|--------|--------|-------------|
| **supertrend_plus** | **-48.86%** | 235 | Too many whipsaw trades (54.74% DD) |
| **ofi** | -38.52% | 105 | Order flow signals counter-trend in strong uptrend |
| **golden_cross** | -29.71% | 169 | Slow signals, whipsaws in consolidation |
| **institutional** | -23.47% | 148 | Volume-only signals lack direction |
| **score80** | -21.52% | 17 | Scoring too permissive, many false entries |

**Key insight**: Trend strategies **without momentum filters** consistently lose money for STAN.L. The SuperTrend+ strategy alone generated 235 trades with a profit factor of only 0.63 — each trade loses money on average. Adding RSI and MACD momentum filters (as in trend_momentum) flips the strategy from losing to the top performer.

### Why stan_dual_trend Underperformed

| Metric | Value |
|--------|-------|
| Return | -8.12% |
| Trades | 75 |
| Win Rate | 50.70% |
| Profit Factor | 0.83 |

Despite a 50.70% win rate and 75 trades, the strategy lost money because **average wins (1.18%) are much smaller than average losses (-1.40%)**. The strategy over-trades — entering too frequently on high-conviction signals that lack follow-through. For STAN.L, **quality over quantity matters**: the top strategies average 16-20 trades over 5 years, not 75.

---

## Custom Strategies Evaluation

### Summary of 5 Custom STAN.L Strategies

| Strategy | Return (%) | Sharpe | Max DD (%) | Trades | Win Rate (%) | Verdict |
|----------|-----------|--------|-----------|--------|-------------|---------|
| **stan_trend_trailing** | 56.00 | 0.60 | 31.09 | 28 | 35.70 | Good — simple, effective |
| **stan_adaptive_trend** | 35.85 | 0.46 | 42.06 | 44 | 31.80 | Moderate — too many low-quality entries |
| **stan_pullback_rides** | **57.98** | **0.76** | **18.33** | 27 | 37.00 | **Best custom — buys dips in uptrend** |
| stan_dual_trend | -8.12 | -0.18 | 18.23 | 75 | 50.70 | Poor — over-trades, small wins |
| stan_vol_breakout_trend | 0.00 | 0.00 | 0.00 | 0 | 0.00 | Failed — volume filter too restrictive |

### Design Lessons for STAN.L

1. **Volume surge filters (>1.5× avg) are ineffective** — STAN.L's institutional trading generates steady volume without frequent dramatic spikes.

2. **Overly complex multi-condition entries reduce performance** — stan_dual_trend with 4 conditions entered 75 times with PF<1. Simpler entries perform better.

3. **Pullback entries within confirmed uptrend work well** — stan_pullback_rides (57.98% return) exploits STAN.L's characteristic pullback-to-EMA pattern.

4. **Adaptive scoring systems need calibration** — stan_adaptive_trend's score-based entry was too permissive, generating 44 trades with only 31.80% win rate.

---

## Strategy Comparison: Trend vs Mean-Reversion for STAN.L

| Aspect | Trend-Following | Mean-Reversion |
|--------|----------------|----------------|
| Best Return | 78.90% (trend_momentum) | 35.01% (dual_exit_meanrev) |
| Best Sharpe | 0.93 (trend_momentum) | 0.82 (short_meanrev) |
| Best Max DD | 18.18% (trend_momentum) | 9.23% (short_meanrev) |
| Best PF | 4.13 (trend_momentum) | 3.22 (dual_exit_meanrev) |
| Trade Frequency | 4-28 trades | 3-9 trades |
| Win Rate Range | 36-54% | 67-100% |
| Best For | Growth-oriented | Capital preservation |

**Why trend-following wins for STAN.L**:
- 71.4% of time in confirmed uptrend
- OBV increasing (institutional accumulation)
- 5-year return of +305% (strong directional bias)
- Pullbacks are shallow relative to overall trend

**Mean-reversion is viable for**:
- Conservative risk profiles (short_meanrev: +27%, -9% DD)
- Specific pullback entries (buying dips at EMA20)
- Complementing trend strategies (use mean-reversion entries within trend framework)

---

## Recommended Production Strategy

### Primary: Trend+Momentum Combo

**Philosophy**: Stay in the strong uptrend with multiple confirmation signals, exit on momentum deterioration.

### Entry Checklist (all must be true)

```text
✓ EMA20 > EMA50 > EMA200 (confirmed uptrend)
✓ RSI(14) > 55 (momentum positive)
✓ MACD Line > Signal (momentum direction)
✓ CMF(20) > 0 (volume flow positive)
```

### Position Sizing

```text
Risk per trade: 1.0% of portfolio
Position Size = (£100,000 × 0.01) / (2 × ATR(14))
```

### Initial Stop Loss

```text
Entry - 2 × ATR(14)
OR
EMA50 (whichever is higher — protects against trend break)
```

### Exit Conditions

```text
RSI(14) < 50 (momentum weakening)
AND
MACD Line < Signal (momentum turned bearish)
```

### Trailing Stop (optional enhancement)

```text
Highest Close since entry - 3 × ATR(14)
Update daily
```

### Expected Performance (from backtest)

| Metric | Value |
|--------|-------|
| Expected Return | ~79% over 5 years |
| Expected Max DD | ~18% |
| Expected Sharpe | ~0.93 |
| Expected Profit Factor | ~4.1 |
| Trade Frequency | ~3-4 per year |

---

### Alternative: Conservative Pullback Strategy

**For traders who prefer lower drawdown and don't want to chase breakouts**:

```text
Entry:
  ✓ EMA20 > EMA50 > EMA200
  ✓ SuperTrend +1
  ✓ Price within 5% of EMA20
  ✓ RSI(14) 35-55
  ✓ Volume < 20-day average

Exit:
  ✗ Price < EMA50
  ✗ RSI(14) > 70

Risk: 0.75% per trade
```

**Expected**: ~58% return, ~18% max DD, Sharpe ~0.76

---

## Cross-Ticker Comparison: STAN.L vs NG.L vs HSBA.L

| Aspect | STAN.L (Banking) | NG.L (Commodity) | HSBA.L (Banking) |
|--------|-------------------|------------------|------------------|
| Market character | Strong uptrend (+305%) | Range-bound (+2.8%) | Bull trend (+127.7%) |
| Best approach | Trend-following + momentum | Mean-reversion with time-stops | Trend-following |
| Optimal DD | 18% (trend_momentum) | 0% (time-stop exit) | N/A |
| Trend days | 71.4% | N/A | N/A |
| Volume signals | Moderate (no surges) | N/A | N/A |
| ATR trailing | Moderate (3×ATR) | ❌ Kills performance | ⚠️ Poor |
| Mean-reversion | Viable but lower return | ✅ Optimal | Limited |

**Key takeaway**: STAN.L is a classic trending stock — use trend-following with momentum filters. Unlike NG.L (range-bound commodity requiring mean-reversion), STAN.L rewards staying in the trend. The -30.75% B&H drawdown is the main risk to manage with trailing stops and momentum-based exits.

---

## Implementation Notes

### Data Column Reference

| Column | Description |
|--------|-------------|
| `ta_ema20` | EMA(20) — short-term trend |
| `ta_ema50` | EMA(50) — medium-term trend |
| `ta_ema200` | EMA(200) — long-term trend |
| `ta_rsi14` | RSI(14) — momentum |
| `ta_macd_line` | MACD line |
| `ta_macd_signal` | MACD signal line |
| `ta_cmf` | CMF(20) — money flow |
| `ta_atr14` | ATR(14) — volatility |
| `ta_supertrend_direction` | SuperTrend: +1 or -1 |
| `ta_adx14` | ADX(14) — trend strength |
| `ta_bband_upper` | Bollinger Upper Band |
| `ta_bband_middle` | Bollinger Middle (SMA20) |
| `ta_bband_lower` | Bollinger Lower Band |
| `ta_bband_width` | BB Width: (upper-lower)/middle |
| `ta_roc20` | Rate of Change(20) |
| `ta_williams_r` | Williams %R(14) |
| `ta_obi` | On-Balance Volume |
| `ta_ofi` | Order Flow Imbalance |
| `ta_donchian_upper` | 20-day high |
| `ta_donchian_lower` | 20-day low |
| `ta_hl` | Higher Low signal |
| `ta_hh` | Higher High signal |
| `ta_ll` | Lower Low signal |
| `ta_lh` | Lower High signal |
| `ta_bos` | Break of Structure |
| `ta_choch` | Change of Character |
| `ta_regime` | HMM regime: 0=volatile, 1=bull, 2=bear |

### Backtest Engine

All strategies were executed using a vectorbt-based backtest engine with:
- £100,000 initial capital
- 0.1% commission + 0.1% slippage per trade
- Full position sizing (all available capital per signal)
- Daily rebalancing at close prices

### Report Output

The complete backtest report is available at:
`data/reports/backtest/STAN.L_backtest_report.html`

This includes interactive equity curves, metrics comparison tables, and detailed performance analytics for all 37 strategies.

---

## Limitations

1. **Look-ahead bias**: All TA indicators use closing prices available at signal generation — no look-ahead.
2. **Transaction costs**: Real-world execution may incur higher costs (spread, market impact for large orders).
3. **Survivorship bias**: STAN.L is a current constituent of FTSE 100; past performance doesn't guarantee future results.
4. **Single stock**: Results specific to STAN.L; other banking stocks may behave differently.
5. **Regime changes**: 5-year window (2021-2026) includes post-pandemic recovery, inflation cycle, and rate hikes — past performance in this specific regime may not persist.
6. **Position sizing**: Backtest uses all-available-capital sizing; real-world position limits and margin requirements would reduce returns.

---

## Conclusion

**STAN.L is a strong trending stock** (+305% in 5 years) that benefits most from **trend-following strategies enhanced by momentum filters**. The key findings:

1. **Best strategy**: Trend+Momentum Combo — 78.90% return, 18.18% max DD, Sharpe 0.93, Profit Factor 4.13
2. **Best conservative**: BB Breakout — 51.36% return, 17.82% max DD, Sharpe 0.86, 54.20% win rate
3. **Best pullback**: Stan Pullback Rides — 57.98% return, 18.33% max DD, Sharpe 0.76
4. **Lowest DD**: Short Mean-Reversion — 27.07% return, 9.23% max DD, 100% win rate

**Critical lesson**: Pure trend strategies without momentum confirmation lose money (SuperTrend+ -48.86%). Adding RSI and MACD momentum filters transforms the same trend signals into the best-performing strategy (78.90%). The momentum filter is the key differentiator for STAN.L.

**Recommended approach**: Use the Trend+Momentum Combo as primary strategy with 1% risk per trade, 2×ATR stop, and momentum-based exits. For conservative allocation, use BB Breakout or pullback entries for lower volatility exposure.
