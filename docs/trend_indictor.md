# Trend Indicators for Buy/Sell Signals

Trend indicators help answer a simple question:

```text
Which direction is the stock moving?
```

The most commonly used trend indicators are:

```text
EMA20   = Short-Term Trend
EMA50   = Medium-Term Trend
EMA200  = Long-Term Trend
SuperTrend = Entry / Exit Trigger
```

Professional traders often combine all four to build a high-confidence trend-following system.

---

# EMA20 (20-Period Exponential Moving Average)

## What It Measures

EMA20 tracks the average price over the last 20 periods while giving more weight to recent prices.

```text
Fast-moving indicator
Responds quickly to price changes
```

Example:

```text
Price  = 105
EMA20  = 100
```

Interpretation:

```text
Price > EMA20

Short-term trend is bullish
```

---

## Buy Signal

Price crosses above EMA20.

Example:

```text
Yesterday:
Price = 98
EMA20 = 100

Today:
Price = 102
EMA20 = 100
```

Signal:

```text
BUY
```

Interpretation:

```text
Short-term momentum turning bullish
```

---

## Sell Signal

Price crosses below EMA20.

Example:

```text
Yesterday:
Price = 102
EMA20 = 100

Today:
Price = 98
EMA20 = 100
```

Signal:

```text
SELL
```

Interpretation:

```text
Short-term momentum turning bearish
```

---

## Limitation

EMA20 is sensitive to noise.

In sideways markets it may generate:

```text
BUY
SELL
BUY
SELL
```

false signals.

---

# EMA50 (50-Period Exponential Moving Average)

## What It Measures

EMA50 reflects the medium-term trend.

```text
Slower than EMA20
Filters market noise
```

Many institutional traders use EMA50 as the trend boundary.

---

## Buy Signal

### Method 1

```text
Price > EMA50
```

Interpretation:

```text
Medium-term trend is bullish
```

### Method 2

```text
EMA20 crosses above EMA50
```

Example:

```text
EMA20 = 120
EMA50 = 115
```

Signal:

```text
BUY
```

Interpretation:

```text
Short-term momentum overtakes medium-term trend
```

---

## Sell Signal

```text
EMA20 crosses below EMA50
```

Example:

```text
EMA20 = 105
EMA50 = 108
```

Signal:

```text
SELL
```

Interpretation:

```text
Momentum weakening
```

---

# EMA200 (200-Period Exponential Moving Average)

## What It Measures

EMA200 represents the long-term market direction.

Many institutions use EMA200 as the primary bull/bear filter.

---

## Bullish Market

```text
Price > EMA200
```

Example:

```text
Price = 150
EMA200 = 120
```

Interpretation:

```text
Long-term uptrend
```

Signal:

```text
BUY BIAS
```

---

## Bearish Market

```text
Price < EMA200
```

Example:

```text
Price = 90
EMA200 = 120
```

Interpretation:

```text
Long-term downtrend
```

Signal:

```text
SELL BIAS
```

---

# Golden Cross

One of the strongest long-term bullish signals.

Condition:

```text
EMA50 crosses above EMA200
```

Visual:

```text
EMA50
   /
  /
 /
---------------- EMA200
```

Signal:

```text
STRONG BUY
```

Interpretation:

```text
Long-term trend reversal upward
```

---

# Death Cross

One of the strongest long-term bearish signals.

Condition:

```text
EMA50 crosses below EMA200
```

Visual:

```text
EMA50 \
       \
        \
--------- EMA200
```

Signal:

```text
STRONG SELL
```

Interpretation:

```text
Long-term trend reversal downward
```

---

# SuperTrend

## What It Measures

SuperTrend combines:

```text
Price
+
ATR (Average True Range)
```

to produce:

```text
Trend Direction
Trailing Stop
```

Unlike moving averages, SuperTrend adapts to volatility.

---

## Buy Signal

Price closes above the SuperTrend line.

Example:

```text
Price      = 105
SuperTrend = 100
```

Visual:

```text
Price
  ▲

------------
