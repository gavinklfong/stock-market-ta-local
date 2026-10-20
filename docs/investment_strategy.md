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