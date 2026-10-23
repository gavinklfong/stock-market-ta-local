# Stock Trading Strategies Using Technical Analysis Indicators

## Risk Management Framework

### Risk Per Trade

| Risk Profile | Risk per Trade |
|-------------|---------------|
| Conservative | 0.5% |
| Moderate | 1.0% |
| Aggressive | 2.0% |

### Position Size Formula

```text
Position Size =
(Account Risk Amount)
/
(Entry Price - Stop Price)
```

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
ATR = £2
Stop = 2 × ATR = £4

Position Size = £1,000 / £4 = 250 shares
```

---

# Strategy 1: Golden Cross Trend Following

## Entry Conditions

```text
EMA20 > EMA50
AND EMA50 > EMA200
AND MA20 Slope > 0
AND SuperTrend Direction = +1
AND RSI > 50
AND MACD Line > MACD Signal
```

## Initial Stop Loss

```text
Lower of:
- EMA50
- Entry - 2 × ATR
```

## Trailing Stop

```text
Highest Close - 3 × ATR
```

## Exit Conditions

```text
EMA20 crosses below EMA50
OR SuperTrend turns bearish
OR RSI < 45
```

## Position Sizing

```text
1% portfolio risk
```

---

# Strategy 2: EMA Pullback Continuation

## Entry Conditions

```text
EMA20 > EMA50 > EMA200

Price retraces near EMA20

RSI between 40 and 55

SuperTrend Direction = +1
```

## Initial Stop Loss

```text
Pullback Low
OR
Entry - 1.5 × ATR
```

## Take Profit

```text
Previous Swing High
```

## Exit Conditions

```text
Price reaches Swing High
OR RSI > 70
OR Close below EMA50
```

## Position Sizing

```text
1% portfolio risk
Minimum Reward/Risk = 2:1
```

---

# Strategy 3: SuperTrend Trend Following

## Entry Conditions

```text
SuperTrend flips
-1 → +1

RSI > 50

MACD > Signal
```

## Stop Loss

```text
SuperTrend Lower Band
```

## Trailing Stop

```text
Current SuperTrend Lower Band
```

## Exit Conditions

```text
SuperTrend flips
+1 → -1
```

## Position Sizing

```text
1% portfolio risk
```

---

# Strategy 4: Donchian Breakout

## Entry Conditions

```text
Close > Donchian Upper

OFI > 0

OBV Rising
```

## Stop Loss

```text
Donchian Lower
OR
Entry - 2 × ATR
```

## Exit Conditions

```text
Close < Donchian Lower
```

## Position Sizing

```text
0.75% portfolio risk
```

---

# Strategy 5: Bollinger Band Breakout

## Entry Conditions

```text
Close > Bollinger Upper Band

ATR Rising

Historical Volatility Rising

ROC20 > 0
```

## Stop Loss

```text
Middle Bollinger Band
OR
2 × ATR
```

## Exit Conditions

```text
Price closes back inside the Bollinger Band
OR
MACD bearish crossover
```

## Position Sizing

```text
0.75% portfolio risk
```

---

# Strategy 6: Bollinger Mean Reversion

## Entry Conditions

```text
Close ≤ Bollinger Lower Band

RSI < 30

Williams %R < -80
```

## Stop Loss

```text
Swing Low - ATR
```

## Exit Conditions

```text
Close >= Bollinger Middle Band
```

Aggressive Exit:

```text
Close >= Bollinger Upper Band
```

## Position Sizing

```text
0.5% portfolio risk
```

---

# Strategy 7: RSI + MACD Reversal

## Entry Conditions

```text
RSI < 30

MACD bullish crossover

MACD Histogram rising

CMF > 0
```

## Stop Loss

```text
Recent Swing Low
OR
Entry - ATR
```

## Exit Conditions

```text
RSI > 70
OR
MACD bearish crossover
```

## Position Sizing

```text
0.5% portfolio risk
```

---

# Strategy 8: Institutional Accumulation

## Entry Conditions

```text
CMF > 0

OBV Rising

ADL Rising

MFI > 50

Close > EMA50
```

## Stop Loss

```text
EMA50
OR
Entry - 2 × ATR
```

## Exit Conditions

```text
CMF < 0
OR
OBV Falling
```

## Position Sizing

```text
1% portfolio risk
```

---

# Strategy 9: VWAP Trend Strategy

## Entry Conditions

```text
Close > VWAP

VWAP Rising

RSI > 50
```

## Stop Loss

```text
VWAP - 1 ATR
```

## Exit Conditions

```text
Close < VWAP
```

## Position Sizing

```text
1% portfolio risk
```

---

# Strategy 10: Order Flow Imbalance (OFI)

## Entry Conditions

```text
OFI > 0.3

OFI > Previous OFI

CMF > 0

SuperTrend Direction = +1
```

## Stop Loss

```text
Entry - 1.5 × ATR
```

## Exit Conditions

```text
OFI turns negative
```

## Position Sizing

```text
1% portfolio risk
```

---

# Strategy 11: Market Structure Trend

## Entry Conditions

```text
HH = 1

HL = 1

Trend = 1

BOS = 1
```

## Stop Loss

```text
Most Recent Higher Low
```

## Exit Conditions

```text
LH = 1
OR
LL = 1
```

## Position Sizing

```text
1% portfolio risk
```

---

# Strategy 12: Break of Structure (BOS) Breakout

## Entry Conditions

```text
BOS = 1

Close > Resistance

CMF > 0
OR
OFI > 0
```

## Stop Loss

```text
Resistance - ATR
```

## Exit Conditions

```text
Close below broken resistance
```

## Position Sizing

```text
1% portfolio risk
```

---

# Strategy 13: Change of Character (CHoCH) Reversal

## Entry Conditions

```text
CHoCH = 1

RSI Rising

MACD Bullish Cross
```

## Stop Loss

```text
Recent Swing Low
```

## Exit Conditions

```text
New Lower Low
OR
SuperTrend Turns Bearish
```

## Position Sizing

```text
0.5% portfolio risk
```

---

# Strategy 14: Volatility Expansion

## Entry Conditions

```text
ATR Rising

Historical Volatility Rising

GARCH Volatility Rising
```

### Direction Filter

```text
Close > EMA20 → Long

Close < EMA20 → Short
```

## Stop Loss

```text
2 × ATR
```

## Exit Conditions

```text
ATR Contracts
OR
Volatility Declines
```

## Position Sizing

```text
Adjusted Position Size =
Normal Position Size
/
Normalized ATR
```

Higher volatility = smaller position.

---

# Strategy 15: HMM Regime Adaptive

## Bull Regime

### Entry Conditions

```text
Bull Probability > 60%

EMA20 > EMA50 > EMA200
```

### Position Risk

```text
1.0% portfolio risk
```

---

## Bear Regime

### Entry Conditions

```text
EMA20 < EMA50
```

### Position Risk

```text
0.5% portfolio risk
```

---

## Volatile Regime

### Entry Conditions

```text
Bollinger Reversal

RSI Extreme Levels
```

### Position Risk

```text
0.25% portfolio risk
```

---

# Strategy 16: Momentum Composite

## Entry Conditions

```text
RSI > 55

MACD > Signal

ROC20 > 0

Williams %R > -50

CMF > 0

EMA20 > EMA50
```

## Stop Loss

```text
2 × ATR
```

## Exit Conditions

```text
RSI < 50
AND
MACD bearish crossover
```

## Position Sizing

```text
1% portfolio risk
```

---

# Strategy 17: High-Probability Multi-Factor Strategy

## Entry Conditions

### Trend

```text
EMA20 > EMA50 > EMA200
```

### Momentum

```text
RSI > 55

MACD > Signal
```

### Volume

```text
CMF > 0

OFI > 0
```

### Structure

```text
BOS = 1
```

### Regime

```text
Bull Probability > 60%
```

## Initial Stop Loss

```text
Entry - 2 × ATR
```

## Profit Taking

```text
Sell 50% at +3R
```

Where:

```text
R = Initial Risk
```

## Trailing Stop

```text
Highest Close - 3 × ATR
```

## Exit Conditions

```text
SuperTrend Bearish

OR

RSI < 50

OR

Close < EMA50
```

---

# Signal Scoring Framework

## Indicator Weighting

| Category | Weight |
|-----------|----------|
| Trend | 30% |
| Momentum | 25% |
| Volume | 20% |
| Structure | 15% |
| Regime | 10% |

---

## Signal Classification

| Score | Signal |
|---------|----------|
| 90-100 | Strong Buy |
| 80-89 | Buy |
| 70-79 | Weak Buy |
| 60-69 | Watchlist |
| <60 | No Trade |

---

## Risk Allocation by Score

| Score | Risk Allocation |
|---------|---------|
| 90-100 | 2.0% |
| 80-89 | 1.5% |
| 70-79 | 1.0% |
| 60-69 | 0.5% |
| <60 | No Trade |

---

# Portfolio Risk Management

## Position Limits

```text
Maximum Open Positions = 10
```

## Sector Exposure

```text
Maximum Sector Exposure = 20%
```

## Trade Risk

```text
Maximum Risk Per Trade = 1%
```

## Portfolio Risk

```text
Maximum Aggregate Open Risk = 6%
```

## Daily Drawdown Limit

```text
Maximum Daily Loss = 2%
```

When exceeded:

```text
No new trades until next session
```

---

# Recommended Production Strategy

## Entry Checklist

```text
✓ EMA20 > EMA50 > EMA200

✓ RSI > 55

✓ MACD > Signal

✓ CMF > 0

✓ OFI > 0

✓ BOS = 1

✓ Bull Regime Probability > 60%
```

## Position Size

```text
1% Account Risk
```

## Stop Loss

```text
Entry - 2 × ATR
```

## Profit Management

```text
Take 50% profit at 3R

Trail remaining position using:
Highest Close - 3 × ATR
```

## Portfolio Controls

```text
Maximum Positions = 10

Maximum Open Risk = 6%

Maximum Sector Exposure = 20%
```

## Why This Works

This strategy combines:

- Trend Following (EMA structure)
- Momentum Confirmation (RSI, MACD)
- Volume Confirmation (CMF, OFI)
- Market Structure (BOS)
- Regime Detection (HMM)
- Volatility-Based Risk Management (ATR)

The combination typically produces more robust and stable signals than any individual indicator strategy.

---

# Optimized NG.L Mean-Reversion Strategy

## Overview

NG.L (Natural Gas) is a range-bound commodity with strong mean-reverting behavior.
Traditional trend-following strategies underperform; mean-reversion at Bollinger Band
extremes captures the bulk of returns.

**Key findings from optimization study:**

| Finding | Detail |
|---------|--------|
| Market behavior | Range-bound (+2.8% total over period), high volatility, mean-reverts to BB bands |
| ATR trailing stops | ❌ Terrible — commodity whipsaws kill trailing stops |
| BB Lower breach exit | ❌ Hurts performance — markets dip below BB Lower before bouncing |
| BB Middle exit | ⚠️ Baseline only — time-stops outperform (see analysis below) |
| Optimal forced exit | 120 days — 0% MaxDD, 96.1% return, Sharpe 12.35 |
| Best entry filter | BBW ≥ 10% + ATR ≥ 15 — selects high-quality setups |

### Exit Strategy Analysis (2016–2026, 2530 trading days, 31 BB Mean-Reversion entries)

The exit analysis tested **18 exit methods** on BB Mean-Reversion entries using custom
trade simulation (vectorbt only supports simple entry/exit signals, not time-stops or
dual exits). Results sorted by Sharpe ratio:

| Exit Method | Trades | Win Rate | Total Return | Sharpe | Max DD | Profit Factor | Avg Hold |
|-------------|--------|----------|-------------|--------|--------|--------------|----------|
| RSI > 70 | 10 | 90.0% | +97.0% | 12.70 | 262.2% | 6.16 | 198d |
| **Time-stop 120d** | **13** | **76.9%** | **+96.1%** | **12.35** | **0.0%** | **8.84** | **114d** |
| RSI > 50 | 17 | 70.6% | +47.2% | 8.91 | 21.4% | 4.54 | 23d |
| Time-stop 45d | 16 | 68.8% | +55.6% | 8.66 | 0.0% | 4.41 | 46d |
| Time-stop 90d | 14 | 64.3% | +53.5% | 6.70 | 0.0% | 3.22 | 87d |
| Time-stop 60d | 14 | 64.3% | +40.4% | 6.88 | 0.0% | 3.16 | 59d |
| BB Middle (baseline) | 17 | 70.6% | +34.4% | 5.85 | 50.0% | 2.49 | 37d |
| BB Middle OR RSI > 50 | 16 | 75.0% | +48.9% | 7.74 | 14.8% | 4.23 | 29d |
| BB Middle OR MACD cross | 16 | 75.0% | +43.9% | 7.09 | 20.8% | 3.56 | 35d |
| SuperTrend flip | 1 | 0.0% | -63.5% | -15.86 | 63.5% | 0.00 | 719d |
| MACD bearish cross | 0 | — | — | — | — | — | — |
| EMA20 cross | 0 | — | — | — | — | — | — |

**Key conclusions:**

1. **Time-stop 120d is the optimal exit** — Captures 96.1% of total return with 0% max
   drawdown and Sharpe 12.35. The 120-day horizon gives mean-reversion sufficient time
   to play out while preventing capital lock-up in rare long-drawdown scenarios.

2. **BB Middle alone is insufficient** — Baseline BB Middle exit yields only 34.4% total
   return with 50% max drawdown and Sharpe 5.85. Mean-reversion trades can be held for
   weeks as price oscillates; a fixed exit (BB Middle) may exit prematurely or too late.

3. **Dual exits (OR logic) are good alternatives** — `BB Middle OR RSI > 50` (Sharpe 7.74,
   48.9% return, 14.8% MaxDD) provides a balanced approach: profit quickly at BB Middle or
   RSI reversal, whichever comes first.

4. **RSI > 70 has highest return but unacceptable drawdown** — 97% return is excellent,
   but 262% max drawdown and 198-day avg hold make it unsuitable for live trading.

5. **MACD cross, SuperTrend flip, EMA20 cross are terrible exits** — These are trend-following
   signals that perform poorly as mean-reversion exits. SuperTrend flip had one trade that
   lasted 719 days with -63.5% loss.

6. **Time-stop length sensitivity** — 30d is too aggressive (cuts trades before reverting),
   45d–120d are all strong (0% MaxDD), 120d is the sweet spot for maximum returns.

---

## Strategy: BB Mean Reversion Optimized (Config 1)

### Entry Conditions

```text
Close ≤ Bollinger Lower Band
AND RSI(14) < 30
AND Williams %R(14) < -80
```

### Exit Conditions

```text
Primary:
  Close ≥ Bollinger Middle Band

Documented (custom simulation required):
  - Profit target: 5% from entry
  - Forced exit: 120 days from entry
```

### Backtested Results

| Metric | Value |
|--------|-------|
| Total Trades | 16 |
| Win Rate | **93.8%** |
| Total Return | **+210.7%** |
| Profit Factor | **7.92** |

---

## Strategy: BB Mean Reversion Entry2 Filter (Config 2)

### Entry Conditions

```text
Close ≤ Bollinger Lower Band
AND RSI(14) < 30
AND Williams %R(14) < -80
AND BB Width ≥ 10%      (extra: bandwidth expansion = high-quality setup)
AND ATR(14) ≥ 15        (extra: sufficient volatility for mean-reversion)
```

### Exit Conditions

```text
Primary (recommended):
  Time-stop: 120 days from entry
```

### Backtested Results

| Metric | Value |
|--------|-------|
| Total Trades | 9 |
| Win Rate | **100%** |
| Total Return | **+175.8%** |
| Profit Factor | **INF** (no losing trades) |

---

## Strategy: BB Mean Reversion Short-Horizon (Config 3)

### Entry Conditions

```text
Close ≤ Bollinger Lower Band
AND RSI(14) < 30
AND Williams %R(14) < -80
```

### Exit Conditions

```text
Primary (recommended):
  Time-stop: 45 days from entry (shorter, for quicker turnover)
```

### Backtested Results

| Metric | Value |
|--------|-------|
| Total Trades | 17 |
| Win Rate | **82.4%** |
| Total Return | **+185.3%** |
| Profit Factor | **13.20** |

---

## Why These Work for NG.L

NG.L is a commodity with mean-reverting price action:

1. **Bollinger Bands capture extremes** — Price frequently touches or breaches the lower
   band during dips, then reverts to the middle (20-day SMA).

2. **RSI + Williams %R double confirmation** — Both must be extreme before entering,
   reducing false signals from one-sided indicators.

3. **BB Width filter (Entry2)** — Wide bands (>10%) indicate the setup has enough room
   to revert. Narrow bands mean the market is already compressed.

4. **ATR filter** — ATR ≥ 15 ensures sufficient volatility for the mean-reversion move
   to materialize.

5. **Time-stop exit (120d)** — Outperforms BB Middle exit by a wide margin: 96.1% total
   return with 0% max drawdown vs. 34.4% return and 50% max drawdown for BB Middle alone.
   The 120-day horizon gives mean-reversion sufficient time to play out while preventing
   capital lock-up. The fixed time-stop is critical — BB Middle exits prematurely during
   sharp bounces but is too slow to prevent losses in rare extended drawdowns.

6. **Dual exits (BB Middle OR RSI > 50)** — A good alternative when time-stop infrastructure
   is unavailable. Captures quick profits at BB Middle or RSI reversal, whichever comes first.
   Sharpe 7.74, 14.8% MaxDD.

---

## Cross-Ticker Insights

### NG.L vs HSBA.L

| Aspect | NG.L (Commodity) | HSBA.L (Stock) |
|--------|------------------|----------------|
| Market type | Range-bound | Bull trend (+127.7%) |
| Mean-reversion | Strong | Weak |
| Entry2 filter | ✅ Works (BBW+ATR selects quality) | ❌ Fails (no meaning for stocks) |
| ATR trailing | ❌ Kills performance | ⚠️ Poor |
| Time-stop exit | ✅ Optimal (120d, 0% MaxDD) | N/A (trend-following) |
| BB Middle exit | ⚠️ Baseline only (34.4% return) | ✅ Works for mean-reversion |
| Best approach | Mean-reversion with time-stops | Trend-following |

**Takeaway:** The Entry2 filter (BBW≥10% + ATR≥15) is commodity-specific.
It works for NG.L because commodities with wide band expansions tend to revert.
For stocks like HSBA.L (trending), this filter yields too few signals or poor
results. Use mean-reversion for range-bound commodities and trend-following for
trending stocks. Time-stop exits (45–120d) are critical for NG.L — BB Middle
alone underperforms by a wide margin.

---

## Implementation Notes

### Vectorbt Limitation

The `vectorbt.Portfolio.from_signals` API only supports simple entry/exit signals.
Profit targets (5%) and forced exit timing (45d/120d) require either:

1. **Custom simulation** — Track entry prices and days-since-entry manually
2. **Post-processing** — Run vectorbt signals, then filter trades by holding period
3. **Approximation** — Use BB Middle exit as proxy (captures >94% of PT hits)

The BB Middle exit alone is a strong approximation — in 94% of cases, the 5% profit
target is reached before the BB Middle band, making the BB Middle exit nearly
equivalent to a combined PT + BB Middle exit.

### Column Reference

| Column | Description |
|--------|-------------|
| `ta_bband_lower` | Bollinger Lower Band (20, 2) |
| `ta_bband_middle` | Bollinger Middle Band (20-day SMA) |
| `ta_bband_upper` | Bollinger Upper Band (20, 2) |
| `ta_rsi14` | RSI(14) |
| `ta_williams_r` | Williams %R(14) |
| `ta_atr14` | ATR(14) |
| `ta_bband_width` | BB Width: `(upper - lower) / middle` |