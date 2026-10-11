# Volatility Indicators for Buy/Sell Signals

Volatility indicators answer a different question than trend or momentum indicators.

```text
Trend:
Which direction is price moving?

Momentum:
How strong is the move?

Volatility:
How aggressively is price moving?
```

A common mistake is treating volatility indicators as direct buy/sell indicators.

In reality:

```text
ATR = Risk and Volatility Indicator

Bollinger Bands =
    Volatility Indicator
    +
    Mean Reversion Indicator
    +
    Breakout Indicator
```

Volatility indicators are most effective when combined with trend, momentum, and volume indicators.

---

# ATR(14) - Average True Range

## What ATR Measures

ATR measures the average price movement over the past 14 periods.

It measures:

```text
Market Volatility
```

It does NOT measure:

```text
Direction
```

Example:

### Low-Volatility Stock

```text
100 → 101 → 102 → 103

ATR = 1
```

### High-Volatility Stock

```text
100 → 110 → 95 → 115

ATR = 10
```

Interpretation:

```text
Second stock is significantly more volatile.
```

---

# ATR Does Not Directly Generate Buy/Sell

Example:

```text
ATR = 8
```

You still cannot determine:

```text
BUY?
SELL?
```

because ATR only indicates:

```text
High Volatility
```

---

# ATR Buy Signal

ATR is often used to confirm the strength of a breakout.

### Setup

```text
EMA20 > EMA50

MACD > Signal

Price Breaks Resistance

ATR Expands
```

Visual:

```text
Resistance
------------

            Breakout
                ▲

ATR
---
2
2
3
5
7
```

Interpretation:

```text
Price movement is accelerating.

Breakout has energy behind it.
```

Signal:

```text
BUY
```

---

# ATR Sell Signal

### Setup

```text
Support Breaks

ATR Expands
```

Visual:

```text
Support
------------

Price
 ▼
 ▼

ATR
---
2
2
4
6
8
```

Interpretation:

```text
Selling pressure is accelerating.
```

Signal:

```text
SELL
```

---

# ATR Volatility Compression

Example:

```text
ATR:
5
4
3
2
1
```

Interpretation:

```text
Market volatility is shrinking.

Price is compressing.
```

Often followed by:

```text
Large breakout
```

This is not a buy/sell signal but a warning that a substantial move may be coming.

---

# ATR for Stop Losses

A popular institutional approach:

```text
Stop Loss = Entry Price - (2 × ATR)
```

Example:

```text
Entry = 100

ATR = 3

Stop = 94
```

ATR is frequently used more for:

```text
Risk Management
Position Sizing
Stop Placement
```

than actual buy/sell signals.

---

# Bollinger Bands

## What Bollinger Bands Measure

Bollinger Bands consist of:

```text
Upper Band

Middle Band (20 SMA)

Lower Band
```

Visual:

```text
Upper Band
------------------

Middle Band
------------------

Lower Band
------------------
```

The bands:

```text
Expand during high volatility

Contract during low volatility
```

---

# Strategy 1: Mean Reversion

The classic Bollinger Band strategy.

---

## Buy Signal

Price touches or falls below the lower band.

Visual:

```text
Upper Band
------------------

Middle Band
------------------

Lower Band
------------------
Price ▼
```

Interpretation:

```text
Potentially oversold
```

Signal:

```text
BUY
```

---

## Sell Signal

Price touches or exceeds the upper band.

Visual:

```text
Price ▲

Upper Band
------------------

Middle Band
------------------

Lower Band
------------------
```

Interpretation:

```text
Potentially overbought
```

Signal:

```text
SELL
```

---

## Strong Mean-Reversion Buy

Example:

```text
Price = 89

Lower Band = 90

RSI = 25
```

Interpretation:

```text
Price below lower band

RSI oversold
```

Signal:

```text
STRONG BUY
```

---

# Strategy 2: Bollinger Band Breakout

Trend traders use Bollinger Bands differently.

---

## Buy Signal

Price closes above the upper band.

Visual:

```text
Price ▲

Upper Band
------------------
```

Interpretation:

```text
Strong upside breakout

Momentum increasing
```

Signal:

```text
BUY
```

---

## Sell Signal

Price closes below the lower band.

Visual:

```text
Lower Band
------------------

Price ▼
```

Interpretation:

```text
Strong downside breakout
```

Signal:

```text
SELL
```

---

# Strategy 3: Bollinger Band Squeeze

One of the most powerful volatility setups.

Bands become unusually narrow:

```text
Upper Band  -------
Middle Band -------
Lower Band  -------
```

Interpretation:

```text
Volatility Compression
```

Eventually:

```text
Volatility Expansion
```

usually follows.

---

## Bullish Squeeze

Conditions:

```text
Bands Narrow

Price Breaks Upper Band

Volume Increases
```

Signal:

```text
BUY
```

Interpretation:

```text
Potential bullish breakout
```

---

## Bearish Squeeze

Conditions:

```text
Bands Narrow

Price Breaks Lower Band

Volume Increases
```

Signal:

```text
SELL
```

Interpretation:

```text
Potential bearish breakout
```

---

# Professional Interpretation

Example:

```text
Price = 150

EMA20 = 145
EMA50 = 140

RSI = 65

ATR Expanding

Upper Bollinger Band Broken
```

Analysis:

### Trend

```text
Bullish
```

### Momentum

```text
Bullish
```

### Volatility

```text
Expanding
```

### Bollinger

```text
Bullish Breakout
```

Result:

```text
STRONG BUY
```

---

# Bearish Example

```text
Price = 92

EMA20 < EMA50

RSI = 35

ATR Expanding

Price Breaks Lower Bollinger Band
```

Analysis:

### Trend

```text
Bearish
```

### Momentum

```text
Bearish
```

### Volatility

```text
Increasing
```

### Bollinger

```text
Bearish Breakdown
```

Result:

```text
STRONG SELL
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

Volatility
-----------
ATR Rising
Price Breaks Upper Bollinger Band

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

Volume
-------
OBV Falling
CMF < 0
Price < VWAP

Volatility
-----------
ATR Rising
Price Breaks Lower Bollinger Band

Result
-------
SELL
```

---

# Example Volatility Scoring Model

```python
volatility_score = 0

if atr_slope > 0:
    volatility_score += 30

if close > bollinger_upper:
    volatility_score += 40

if bollinger_squeeze_breakout:
    volatility_score += 30
```

Interpretation:

```text
80-100 = Strong Bullish Expansion

60-80  = Bullish Volatility

40-60  = Neutral

20-40  = Bearish Volatility

0-20   = Strong Bearish Expansion
```

---

# Key Takeaway

| Indicator | Purpose | Buy Signal | Sell Signal |
|------------|------------|------------|------------|
| ATR(14) | Volatility Measurement | ATR expands during bullish breakout | ATR expands during bearish breakdown |
| Bollinger Bands | Volatility + Mean Reversion | Lower-band bounce, upper-band breakout, bullish squeeze | Upper-band rejection, lower-band breakdown, bearish squeeze |

---

# Volatility Indicator Summary

```text
ATR
----
Measures volatility and risk.

Useful for:
    Breakout confirmation
    Stop loss calculation
    Position sizing

Not usually a direct entry indicator.

Bollinger Bands
---------------
Measures volatility expansion and contraction.

Useful for:
    Mean reversion trades
    Breakout trades
    Squeeze detection
    Overbought/oversold conditions
```

The most reliable volatility-based trade setups occur when:

```text
Trend
+
Momentum
+
Volume
+
Volatility Expansion

all point in the same direction.
```

For example:

```text
EMA20 > EMA50 > EMA200
RSI > 55
MACD > Signal
OBV Rising
CMF > 0
ATR Rising
Upper Bollinger Breakout

= High-Confidence BUY
```