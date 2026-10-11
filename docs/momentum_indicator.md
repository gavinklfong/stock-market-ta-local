# Momentum Indicators for Buy/Sell Signals

Momentum indicators answer a different question than trend indicators.

```text
Trend Indicators:
Which direction is the stock moving?

Momentum Indicators:
How strong is the move?
```

A stock can remain in an uptrend while momentum weakens.

Momentum indicators often provide early warning signals before trend indicators react.

---

# RSI(14) - Relative Strength Index

## What RSI Measures

RSI compares the magnitude of recent gains versus recent losses.

Range:

```text
0 to 100
```

Typical interpretation:

```text
RSI > 70 = Overbought

RSI < 30 = Oversold

RSI = 50 = Neutral
```

---

## Buy Signal #1 - Oversold Reversal

Example:

```text
Day 1: RSI = 25

Day 2: RSI = 32

Day 3: RSI = 38
```

Condition:

```text
RSI crosses above 30
```

Interpretation:

```text
Selling pressure weakening

Buyers returning
```

Signal:

```text
BUY
```

---

## Sell Signal #1 - Overbought Reversal

Example:

```text
Day 1: RSI = 75

Day 2: RSI = 68
```

Condition:

```text
RSI crosses below 70
```

Interpretation:

```text
Buying pressure weakening

Momentum fading
```

Signal:

```text
SELL
```

---

## Buy Signal #2 - RSI Above 50

Many trend-following systems simplify RSI interpretation:

```text
RSI > 50 = Bullish

RSI < 50 = Bearish
```

Example:

```text
RSI = 58
```

Interpretation:

```text
Average gains exceed average losses

Momentum is positive
```

Signal:

```text
BUY
```

---

## Sell Signal #2 - RSI Below 50

Example:

```text
RSI = 42
```

Interpretation:

```text
Average losses exceed average gains

Momentum is negative
```

Signal:

```text
SELL
```

---

## RSI Divergence

One of the most useful early warning signals.

### Bearish Divergence

Price:

```text
100 → 110 → 120
```

RSI:

```text
80 → 75 → 65
```

Interpretation:

```text
Price making higher highs

Momentum making lower highs

Uptrend weakening
```

Signal:

```text
SELL WARNING
```

---

### Bullish Divergence

Price:

```text
120 → 110 → 100
```

RSI:

```text
30 → 35 → 42
```

Interpretation:

```text
Price making lower lows

Momentum strengthening

Potential reversal
```

Signal:

```text
BUY WARNING
```

---

# MACD (Moving Average Convergence Divergence)

## What MACD Measures

MACD measures momentum using moving averages.

Basic formula:

```text
MACD = EMA12 - EMA26

Signal Line = EMA9 of MACD
```

---

## Buy Signal #1 - MACD Crossover

Condition:

```text
MACD crosses ABOVE Signal Line
```

Visual:

```text
MACD      /
         /

Signal   /
```

Example:

```text
Yesterday:

MACD   = -1.2
Signal = -0.8

Today:

MACD   = -0.5
Signal = -0.7
```

Interpretation:

```text
Momentum turning bullish
```

Signal:

```text
BUY
```

---

## Sell Signal #1 - MACD Crossunder

Condition:

```text
MACD crosses BELOW Signal Line
```

Interpretation:

```text
Momentum weakening

Bearish momentum increasing
```

Signal:

```text
SELL
```

---

## Buy Signal #2 - MACD Above Zero

Condition:

```text
MACD > 0
```

Meaning:

```text
EMA12 > EMA26
```

Interpretation:

```text
Short-term trend stronger than long-term trend
```

Signal:

```text
BULLISH
```

---

## Sell Signal #2 - MACD Below Zero

Condition:

```text
MACD < 0
```

Meaning:

```text
EMA12 < EMA26
```

Interpretation:

```text
Short-term weakness
```

Signal:

```text
BEARISH
```

---

## MACD Histogram

Formula:

```text
Histogram = MACD - Signal
```

---

### Bullish Histogram

Example:

```text
1
2
4
6
8
```

Interpretation:

```text
Momentum accelerating upward
```

Signal:

```text
BUY
```

---

### Bearish Histogram

Example:

```text
8
6
4
2
1
```

Interpretation:

```text
Momentum weakening
```

Signal:

```text
SELL WARNING
```

---

# ROC(20) - Rate of Change

## What ROC Measures

ROC measures percentage change compared with the price 20 periods ago.

Formula:

```text
ROC =
((Current Price - Price 20 Days Ago)
 /
 Price 20 Days Ago)
 × 100
```

---

## Example Calculation

```text
Price 20 Days Ago = 100

Today = 120
```

Calculation:

```text
(120 - 100) / 100 × 100

ROC = +20%
```

Interpretation:

```text
Price is 20% higher than 20 days ago
```

Strong momentum.

---

## Buy Signal

Condition:

```text
ROC crosses above 0
```

Example:

```text
Yesterday:
ROC = -2%

Today:
ROC = +1%
```

Interpretation:

```text
Momentum shifts from negative to positive
```

Signal:

```text
BUY
```

---

## Sell Signal

Condition:

```text
ROC crosses below 0
```

Example:

```text
Yesterday:
ROC = +3%

Today:
ROC = -1%
```

Interpretation:

```text
Momentum turns negative
```

Signal:

```text
SELL
```

---

## Strong Momentum Signal

Example:

```text
ROC > 20%
```

Interpretation:

```text
Strong bullish momentum

Possible breakout
```

Signal:

```text
STRONG BUY
```

---

## Strong Negative Momentum

Example:

```text
ROC < -20%
```

Interpretation:

```text
Strong bearish momentum

Possible capitulation selling
```

Signal:

```text
STRONG SELL
```

---

# Using RSI, MACD and ROC Together

Professional systems rarely use only a single momentum indicator.

---

## Bullish Example

```text
RSI(14) = 62

MACD > Signal

ROC(20) = +8%
```

Analysis:

### RSI

```text
Momentum is bullish
```

### MACD

```text
Momentum is increasing
```

### ROC

```text
Price stronger than 20 days ago
```

Result:

```text
STRONG BUY MOMENTUM
```

---

## Bearish Example

```text
RSI(14) = 42

MACD < Signal

ROC(20) = -6%
```

Analysis:

### RSI

```text
Weak momentum
```

### MACD

```text
Momentum turning bearish
```

### ROC

```text
Price weaker than 20 days ago
```

Result:

```text
STRONG SELL MOMENTUM
```

---

# Example Momentum Scoring Model

```python
momentum_score = 0

if rsi > 55:
    momentum_score += 30

if macd > signal:
    momentum_score += 40

if roc20 > 0:
    momentum_score += 30
```

Classification:

```text
80-100 = Strong Bullish Momentum

60-80  = Bullish Momentum

40-60  = Neutral

20-40  = Bearish Momentum

0-20   = Strong Bearish Momentum
```

---

# Practical Algo-Trading Rules

## Buy Candidate

```text
Trend
------
EMA20 > EMA50 > EMA200

Momentum
---------
RSI > 55
MACD > Signal
ROC > 0

Volume
-------
OBV Rising
CMF > 0
Price > VWAP

Result
-------
BUY
```

---

## Sell Candidate

```text
Trend
------
EMA20 < EMA50

Momentum
---------
RSI < 45
MACD < Signal
ROC < 0

Volume
-------
OBV Falling
CMF < 0
Price < VWAP

Result
-------
SELL
```

---

# Key Takeaway

| Indicator | Purpose | Buy Signal | Sell Signal |
|------------|----------|------------|------------|
| RSI(14) | Measures speed of gains vs losses | RSI > 50, cross above 30, bullish divergence | RSI < 50, cross below 70, bearish divergence |
| MACD | Measures trend momentum | MACD > Signal, MACD > 0 | MACD < Signal, MACD < 0 |
| ROC(20) | Measures percentage price change | ROC crosses above 0, ROC > 20% | ROC crosses below 0, ROC < -20% |

---

# Momentum Indicator Summary

```text
RSI
---
Measures momentum strength.

Best for:
    Overbought/Oversold detection
    Divergence signals
    Trend confirmation

MACD
----
Measures momentum acceleration.

Best for:
    Trend confirmation
    Momentum crossovers
    Early reversal detection

ROC
---
Measures percentage change over time.

Best for:
    Momentum ranking
    Breakout detection
    Relative strength analysis
```

The strongest momentum-based buy signal occurs when:

```text
RSI > 55
+
MACD > Signal
+
ROC > 0
```

The strongest momentum-based sell signal occurs when:

```text
RSI < 45
+
MACD < Signal
+
ROC < 0
```

When all three agree, momentum is aligned and the probability of a successful trend-following trade increases significantly.