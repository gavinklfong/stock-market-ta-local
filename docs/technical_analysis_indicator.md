# Technical Analysis Indicators for Buy/Sell Signals

For an algo trading agent, it's useful to group indicators by purpose. A robust trading system typically combines multiple indicator categories rather than relying on a single signal.

---

# Trend Indicators

These indicators help identify the overall market direction.

| Indicator | Buy Signal | Sell Signal |
|------------|------------|------------|
| SMA (Simple Moving Average) | Price above SMA | Price below SMA |
| EMA (Exponential Moving Average) | Price above EMA | Price below EMA |
| Moving Average Crossover | Short MA crosses above Long MA (Golden Cross) | Short MA crosses below Long MA (Death Cross) |
| SuperTrend | Price closes above SuperTrend | Price closes below SuperTrend |
| Parabolic SAR | SAR dots move below price | SAR dots move above price |
| Ichimoku Cloud | Price above cloud | Price below cloud |
| Linear Regression Slope | Positive slope | Negative slope |

---

# Momentum Indicators

These measure the strength and speed of price movement.

| Indicator | Buy Signal | Sell Signal |
|------------|------------|------------|
| RSI (Relative Strength Index) | RSI crosses above 30 | RSI crosses below 70 |
| MACD | MACD crosses above Signal Line | MACD crosses below Signal Line |
| Stochastic Oscillator | %K crosses above %D below 20 | %K crosses below %D above 80 |
| ROC (Rate of Change) | ROC > 0 | ROC < 0 |
| CCI (Commodity Channel Index) | CCI crosses above -100 | CCI crosses below +100 |
| Williams %R | Leaves oversold zone | Leaves overbought zone |

---

# Volume Indicators

These confirm whether a price move is supported by strong participation.

| Indicator | Buy Signal | Sell Signal |
|------------|------------|------------|
| OBV (On Balance Volume) | OBV rising with price | OBV falling with price |
| Chaikin Money Flow (CMF) | CMF > 0 | CMF < 0 |
| Accumulation/Distribution Line | Rising trend | Falling trend |
| Volume Spike | Breakout on high volume | Breakdown on high volume |
| VWAP | Price above VWAP | Price below VWAP |

---

# Volatility Indicators

These measure market expansion and contraction.

| Indicator | Buy Signal | Sell Signal |
|------------|------------|------------|
| Bollinger Bands | Bounce from lower band | Rejection from upper band |
| ATR (Average True Range) | ATR expanding during breakout | ATR expanding during breakdown |
| Keltner Channel | Price closes above upper channel | Price closes below lower channel |
| Donchian Channel | Breaks upper channel | Breaks lower channel |

---

# Market Structure Indicators

Pure price action analysis without relying on technical indicators.

| Pattern | Buy Signal | Sell Signal |
|----------|----------|----------|
| Higher Highs / Higher Lows | Confirmed uptrend | Structure breaks |
| Lower Highs / Lower Lows | Reversal upward | Confirmed downtrend |
| Break of Structure (BOS) | Bullish BOS | Bearish BOS |
| Change of Character (CHoCH) | Bullish CHoCH | Bearish CHoCH |
| Support / Resistance | Bounce from support | Rejection at resistance |

---

# Candlestick Signals

## Bullish Patterns (Buy)

- Bullish Engulfing
- Hammer
- Morning Star
- Piercing Line
- Three White Soldiers

## Bearish Patterns (Sell)

- Bearish Engulfing
- Shooting Star
- Evening Star
- Dark Cloud Cover
- Three Black Crows

---

# Quantitative Indicators

Frequently used in systematic and institutional trading.

| Indicator | Buy Signal | Sell Signal |
|------------|------------|------------|
| Z-Score Mean Reversion | Z-Score < -2 | Z-Score > +2 |
| Kalman Trend Filter | Trend becomes positive | Trend becomes negative |
| Hurst Exponent | Persistent trend (> 0.5) | Anti-persistent (< 0.5) |
| Hidden Markov Model (HMM) | Bull regime detected | Bear regime detected |
| GARCH / FIGARCH Volatility Regime | Trend with favourable volatility | High-risk volatility regime |

---

# Relative Strength Indicators

Useful for ranking stocks against benchmarks.

| Indicator | Buy Signal | Sell Signal |
|------------|------------|------------|
| Relative Strength vs Index (e.g. SPY) | Outperforming benchmark | Underperforming benchmark |
| Relative Strength vs Sector ETF | Stronger than sector | Weaker than sector |
| Relative Rotation Graph (RRG) | Leading quadrant | Lagging quadrant |

---

# Typical Professional Trend-Following Signal Stack

A professional system may require all conditions to be met before entering a long position.

## Buy Signal

```text
Trend
------
EMA20 > EMA50 > EMA200

Momentum
---------
RSI > 55
MACD > Signal

Volume
-------
Volume > 1.5 × Average Volume

Volatility
-----------
ATR Expanding

Structure
----------
Higher High + Higher Low
```

Result:

```text
BUY
```

---

## Sell Signal

```text
EMA20 < EMA50

MACD < Signal

RSI < 45

Price < VWAP

High Volume Breakdown
```

Result:

```text
SELL
```

---

# Recommended Indicator Set for an Algo Trading Agent

If building a stock analysis platform using TimescaleDB and Python/Pandas, a balanced indicator stack would include:

## Trend

```text
EMA20
EMA50
EMA200
SuperTrend
```

## Momentum

```text
RSI(14)
MACD
ROC(20)
```

## Volume

```text
OBV
CMF
VWAP
```

## Volatility

```text
ATR(14)
Bollinger Bands
```

## Market Structure

```text
Higher High / Higher Low Detection
Support / Resistance Levels
BOS (Break of Structure)
CHoCH (Change of Character)
```

## Market Regime

```text
GARCH Volatility Model
Hidden Markov Model (HMM)
Kalman Trend Filter
```

---

# Recommended Weighting Model for an Algo Agent

A practical scoring engine might look like:

```python
score = (
    0.30 * trend_score +
    0.25 * momentum_score +
    0.20 * volume_score +
    0.15 * volatility_score +
    0.10 * regime_score
)

if score >= 0.75:
    signal = "STRONG BUY"
elif score >= 0.60:
    signal = "BUY"
elif score <= 0.25:
    signal = "STRONG SELL"
elif score <= 0.40:
    signal = "SELL"
else:
    signal = "HOLD"
```

---

# Institutional-Grade Indicator Categories

For a production-quality stock trend agent, track indicators from all six categories:

1. Trend Indicators
2. Momentum Indicators
3. Volume Indicators
4. Volatility Indicators
5. Market Structure Signals
6. Market Regime Detection Models

The strongest buy/sell signals occur when multiple categories align simultaneously rather than when a single indicator generates a signal.