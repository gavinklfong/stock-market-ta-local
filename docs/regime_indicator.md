# Regime Indicators

Unlike traditional technical indicators, regime indicators do not primarily answer:

```text
Should I Buy?
Should I Sell?
```

Instead, they answer:

```text
What type of market am I trading in?
```

Think of the indicator hierarchy as:

```text
EMA        = Direction
RSI        = Momentum
OBV        = Volume Flow
ATR        = Volatility
Market Structure = Price Behaviour

Regime Models = Market Environment
```

A regime model is often used as a filter to determine whether a trading signal is trustworthy.

---

# 1. GARCH Volatility Regime

## What GARCH Measures

GARCH (Generalized Autoregressive Conditional Heteroskedasticity) forecasts future volatility.

It exploits the fact that:

```text
High volatility tends to cluster.

Low volatility tends to cluster.
```

Example:

```text
Quiet Market
↓
Usually remains quiet

Volatile Market
↓
Usually remains volatile
```

---

## Example GARCH Forecast

```text
Tomorrow Volatility = 1.2%
```

or

```text
Tomorrow Volatility = 5.8%
```

This forecast can be used to classify the current market regime.

---

## Low Volatility Regime

```text
Predicted Volatility = 0.8%
```

Interpretation:

```text
Stable market
Controlled price movement
```

Often favourable for:

```text
Trend Following
Breakout Strategies
```

---

## High Volatility Regime

```text
Predicted Volatility = 6%
```

Interpretation:

```text
Risk-off market
Highly unstable conditions
```

Common during:

```text
Market crashes
Major news events
Earnings surprises
Economic shocks
```

---

## Buy Signal Using GARCH

GARCH does not generate a buy signal directly.

Instead, it acts as a confidence filter.

### Example

```text
EMA20 > EMA50 > EMA200
RSI > 55
SuperTrend = BUY

GARCH Volatility = LOW
```

Result:

```text
BUY
```

Reason:

```text
Trend signal is present
Market conditions are favourable
```

---

## Avoid Buy Signal

```text
EMA20 > EMA50
RSI > 60
SuperTrend = BUY

GARCH Volatility = EXTREMELY HIGH
```

Interpretation:

```text
Trend exists

Volatility risk is excessive
```

Result:

```text
NO TRADE
```

---

## Position Sizing Example

Rather than controlling entries, many funds use GARCH for risk management.

### Low Volatility

```text
Position Size = 10%
```

### High Volatility

```text
Position Size = 2%
```

---

# 2. HMM Trend Regime

## What is HMM?

HMM stands for Hidden Markov Model.

The assumption:

```text
Markets move through hidden states.
```

Examples:

```text
Bull Market
Bear Market
Sideways Market
Crisis Market
```

These states are not directly observable.

The HMM attempts to infer them from:

```text
Returns
Volatility
Momentum
Volume
```

---

# Example HMM Output

```text
Bull Market     75%
Bear Market     10%
Sideways Market 10%
Crisis Market    5%
```

Interpretation:

```text
High probability of bull regime
```

---

# Typical Regimes

## State 1: Bull Regime

Characteristics:

```text
Positive returns
Moderate volatility
Higher Highs
Higher Lows
```

Typical strategy:

```text
Trend Following
Momentum Trading
```

---

## State 2: Bear Regime

Characteristics:

```text
Negative returns
Lower Highs
Lower Lows
Increasing volatility
```

Typical strategy:

```text
Short Selling
Defensive Positioning
```

---

## State 3: Sideways Regime

Characteristics:

```text
No clear trend
Range-bound market
Frequent reversals
```

Typical strategy:

```text
Mean Reversion
Range Trading
```

---

## State 4: Crisis Regime

Characteristics:

```text
Extreme volatility
Large gaps
Rapid price swings
```

Typical strategy:

```text
Reduce risk
Cash preservation
```

---

# Bullish HMM Example

```text
Bull Regime Probability = 80%

EMA20 > EMA50 > EMA200
RSI > 55
MACD > Signal
```

Interpretation:

```text
Trend indicators agree

Market regime agrees
```

Result:

```text
BUY
```

---

# Bearish HMM Example

```text
Bear Regime Probability = 78%

EMA20 < EMA50
MACD < Signal
CMF < 0
```

Interpretation:

```text
Bear market likely

Indicators confirm weakness
```

Result:

```text
SELL
```

---

# Sideways Market Example

```text
Bull Regime      = 20%
Sideways Regime  = 70%
Bear Regime      = 10%
```

Trend indicators:

```text
EMA20 > EMA50
```

Without HMM:

```text
BUY
```

With HMM:

```text
IGNORE SIGNAL
```

Reason:

```text
Sideways markets often produce false breakouts.
```

---

# Without vs With Regime Filtering

## Without Regime Model

```text
EMA20 > EMA50
RSI > 55
MACD > Signal

BUY
```

Potential issue:

```text
Many false signals
```

---

## With Regime Model

```text
EMA20 > EMA50
RSI > 55
MACD > Signal

HMM Bull Regime > 70%

GARCH Volatility < Threshold
```

Result:

```text
BUY
```

Higher confidence because both the signal and the environment agree.

---

# Professional Quant Workflow

Most institutional systems follow a layered approach.

```text
Step 1
-------
Determine Market Regime

HMM:
    Bull
    Bear
    Sideways
    Crisis

↓

Step 2
-------
Forecast Volatility

GARCH:
    Low
    Medium
    High

↓

Step 3
-------
Choose Appropriate Strategy

Bull Regime:
    Trend Following

Bear Regime:
    Short Selling

Sideways Regime:
    Mean Reversion

Crisis Regime:
    Risk Reduction

↓

Step 4
-------
Generate Entry Signals

EMA
RSI
MACD
OBV
VWAP
SuperTrend
```

---

# Example Algo Scoring Model

```python
buy_score = 0

# Trend
if ema20 > ema50 > ema200:
    buy_score += 30

# Momentum
if rsi > 55:
    buy_score += 15

if macd > signal:
    buy_score += 15

# Volume
if obv_slope > 0:
    buy_score += 10

if cmf > 0:
    buy_score += 10

# Regime
if hmm_regime == "bull":
    buy_score += 15

if garch_volatility < threshold:
    buy_score += 5
```

---

# Key Takeaway

Regime indicators do **not directly generate buy/sell signals**.

Instead:

```text
EMA / RSI / MACD
    Tell you what the stock is doing.

GARCH / HMM
    Tell you whether current market conditions
    make those signals reliable.
```

### Practical Summary

| Indicator | 