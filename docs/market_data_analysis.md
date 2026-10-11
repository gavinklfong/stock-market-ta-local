# How an Algo Agent Determines the Movement Trend of a Stock

An algorithmic trading agent does not "know" the future direction of a stock. Instead, it estimates the probability that a stock is moving in an upward, downward, or sideways trend using historical and real-time market data.

---

## 1. Price Action Trend Detection

One of the simplest approaches is analysing price history.

### Moving Averages

A stock is generally considered bullish when:

```text
Current Price > 50-day MA > 200-day MA
```

Example:

| Metric | Value |
|----------|----------|
| Price | £120 |
| 50-day MA | £115 |
| 200-day MA | £100 |

This suggests an upward trend.

### Common Signals

**Golden Cross**

```text
50-day MA crosses above 200-day MA
```

Interpretation: Bullish signal

**Death Cross**

```text
50-day MA crosses below 200-day MA
```

Interpretation: Bearish signal

---

## 2. Market Structure Analysis

Many trading agents analyse highs and lows rather than averages.

### Uptrend

A stock is in an uptrend when it forms:

- Higher Highs (HH)
- Higher Lows (HL)

Example:

```text
100 → 105 → 102 → 110 → 107 → 115
      HH    HL    HH    HL    HH
```

### Downtrend

A stock is in a downtrend when it forms:

- Lower Highs (LH)
- Lower Lows (LL)

This approach often provides a clearer view of market behaviour than moving averages.

---

## 3. Statistical Trend Models

### Linear Regression Slope

A regression line is fitted to historical prices:

```text
Price = a + bt
```

Where:

- `b > 0` → Uptrend
- `b < 0` → Downtrend

Example:

```text
Slope = +0.32
R² = 0.87
```

Interpretation:

- Positive slope
- Strong trend consistency

This method is widely used in quantitative trading systems.

---

## 4. Momentum Indicators

Momentum measures the strength of price movement.

### Rate of Change (ROC)

Formula:

```text
ROC = (Current Price - Old Price) / Old Price
```

Example:

```text
30-day ROC = +15%
```

Interpretation:

- Positive momentum
- Bullish bias

### RSI (Relative Strength Index)

```text
RSI > 50 → Bullish
RSI < 50 → Bearish
```

### MACD

```text
MACD > Signal Line
```

Interpretation:

- Upward momentum
- Potential bullish trend

---

## 5. Volume Confirmation

Price movement without volume is often considered weak.

### Strong Trend

```text
Price ↑ 5%
Volume ↑ 80%
```

### Weak Trend

```text
Price ↑ 5%
Volume ↓ 60%
```

Many trading systems require both:

```text
Trend = Price Signal AND Volume Signal
```

---

## 6. Machine Learning Approaches

Modern AI-driven agents create features such as:

```text
MA20
MA50
RSI
MACD
ATR
Volume
News Sentiment
Options Flow
```

These features are fed into models such as:

- XGBoost
- Random Forest
- LightGBM
- LSTM
- Transformers

Example output:

```text
P(Up)   = 72%
P(Down) = 18%
P(Flat) = 10%
```

The agent makes decisions based on probabilities rather than fixed labels.

---

## 7. Regime Detection Using Hidden Markov Models (HMM)

Advanced systems attempt to determine the current market regime.

Possible states:

```text
State 1 = Bull Market
State 2 = Bear Market
State 3 = Sideways Market
State 4 = High Volatility Market
```

Example probabilities:

```text
Bull Market      = 65%
Bear Market      = 15%
Sideways Market  = 20%
```

Many hedge funds perform regime detection before applying trading strategies.

---

## 8. Multi-Timeframe Confirmation

Professional systems rarely rely on a single timeframe.

Example:

```text
Daily Trend = Up
4H Trend    = Up
1H Trend    = Pullback
```

Decision:

```text
Buy the pullback within the larger uptrend
```

This approach often reduces false signals.

---

# Example Trend Scoring System

A practical trend-following agent may combine multiple signals:

```python
trend_score = (
    0.3 * MA_signal +
    0.3 * momentum_signal +
    0.2 * volume_signal +
    0.2 * regime_signal
)

if trend_score > 0.7:
    trend = "STRONG_UP"
elif trend_score > 0.55:
    trend = "UP"
elif trend_score < 0.3:
    trend = "DOWN"
else:
    trend = "SIDEWAYS"
```

---

# Production-Grade Quantitative Approach

For advanced quantitative trading systems:

```text
1. Detect volatility regime (GARCH / FIGARCH)
2. Detect trend regime (HMM or Kalman Filter)
3. Measure momentum strength
4. Enter trades only when:

   Trend Strength > Threshold
   AND
   Volatility Regime is Favourable
```

Benefits:

- Avoids trading during noisy market conditions
- Filters false breakouts
- Adapts to changing market regimes
- Generally more robust than simple moving-average crossover systems

---

# Key Takeaway

A sophisticated algo agent typically combines:

- Trend indicators (Moving Averages, Regression Slope)
- Momentum indicators (RSI, MACD, ROC)
- Volume analysis
- Market structure (HH/HL or LH/LL)
- Regime detection (HMM, Kalman Filter)
- Volatility forecasting (GARCH/FIGARCH)
- Machine learning probability models

Rather than predicting the future with certainty, the agent continuously updates the probability that a stock is in an upward, downward, or sideways trend and trades according to a predefined risk-management framework.