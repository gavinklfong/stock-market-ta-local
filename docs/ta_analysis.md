# Additional Technical Analysis Indicators

## Trend

### MA Slope Indicators

#### `ta_ma20_slope`
#### `ta_ma50_slope`

Measures the rate of change of the moving average over a 10-bar lookback.

### Interpretation

Instead of asking:

> "Is the trend up or down?"

it asks:

> "How fast is the trend accelerating or decelerating?"

### Buy Signals

#### Bullish Trend Acceleration

```text
MA20 Slope > 0
MA50 Slope > 0
MA20 Slope Increasing
```

Example:

```text
MA20 Slope:
1% → 2% → 4% → 6%
```

Momentum is strengthening.

#### Strong Buy

```text
EMA20 > EMA50 > EMA200
AND
MA20 Slope > 0
AND
MA50 Slope > 0
```

Suggests a strong institutional uptrend.

### Sell Signals

#### Trend Weakening

```text
MA20 Slope:
+5% → +3% → +1% → -1%
```

The trend is losing strength.

#### Strong Sell

```text
MA20 Slope < 0
MA50 Slope < 0
```

Both short-term and medium-term trends are declining.

---

## Donchian Channel

### `ta_donchian_upper`

Highest high over the lookback period.

### `ta_donchian_lower`

Lowest low over the lookback period.

### Interpretation

Measures breakout strength.

Popularised by the Turtle Trading system.

### Buy Signals

#### Bullish Breakout

```text
Close > Donchian Upper
```

A new N-period high.

#### Strong Buy

```text
Close > Donchian Upper
AND
Volume Rising
AND
CMF > 0
```

Institutional buying likely.

### Sell Signals

#### Bearish Breakdown

```text
Close < Donchian Lower
```

New N-period low.

#### Strong Sell

```text
Close < Donchian Lower
AND
CMF < 0
```

Suggests sustained selling pressure.

---

## Keltner Channel

### `ta_keltner_upper`
### `ta_keltner_lower`

ATR-based volatility bands around an EMA.

### Interpretation

Measures whether price has moved beyond its normal ATR range.

### Buy Signals

#### Trend Expansion

```text
Close > Keltner Upper
```

Momentum and volatility expanding upward.

#### Strong Buy

```text
Close > Keltner Upper
AND
ATR Rising
AND
RSI > 60
```

A strong bullish trend is developing.

### Sell Signals

#### Downside Expansion

```text
Close < Keltner Lower
```

Bearish volatility expansion.

#### Strong Sell

```text
Close < Keltner Lower
AND
ATR Rising
```

Selling pressure is accelerating.

---

## Momentum

### Williams %R

#### `ta_williams_r`

Oscillator ranging from:

```text
0      = Overbought
-100   = Oversold
```

### Interpretation

Shows where the current close sits relative to the recent trading range.

### Buy Signals

#### Oversold Reversal

```text
Williams %R crosses above -80
```

Example:

```text
-95 → -88 → -75
```

Buyers returning.

### Strong Buy

```text
Williams %R > -80
AND
RSI Rising
```

Momentum recovery.

### Sell Signals

#### Overbought Reversal

```text
Williams %R crosses below -20
```

Example:

```text
-5 → -15 → -25
```

Momentum weakening.

### Caveat

During strong bull markets:

```text
Williams %R may stay above -20
```

for extended periods.

Do not short solely because it is overbought.

---

## Volume

### Accumulation Distribution Line (ADL)

#### `ta_adl`

Combines:

```text
Price Close Position
+
Volume
```

to identify accumulation or distribution.

### Interpretation

Tracks whether institutions are quietly buying or selling.

### Buy Signals

#### Accumulation

```text
ADL Rising
```

Money is flowing into the stock.

#### Strong Buy (Hidden Accumulation)

```text
Price Sideways
AND
ADL Rising
```

Example:

```text
Price:
100
99
100
101

ADL:
Higher Highs
```

Often precedes a breakout.

### Sell Signals

#### Distribution

```text
Price Rising
AND
ADL Falling
```

Bearish divergence.

Institutions may be selling into strength.

---

## Volatility

### Historical Volatility

#### `ta_hvol20`

Annualised standard deviation of log returns.

### Interpretation

Measures realised volatility.

### Buy Signals

Volatility itself is not directional.

Look for:

#### Volatility Compression

```text
HV20 Near Multi-Month Low
```

followed by:

```text
Donchian Breakout
```

Potential start of a trending move.

### Strong Buy Setup

```text
Low HV20
AND
BOS
AND
Volume Breakout
```

### Sell Signals

#### Volatility Spike

```text
HV20 suddenly doubles
```

Can indicate:

- Panic selling
- Blow-off tops
- Exhaustion

---

### Parkinson Volatility

#### `ta_parkinson_vol`

Uses:

```text
High
Low
```

instead of close-to-close returns.

### Interpretation

Captures intraday volatility more accurately than Historical Volatility.

### Buy Signals

#### Volatility Compression

```text
Parkinson Vol Falling
```

Trading range tightening.

#### Strong Buy

```text
Low Parkinson Vol
AND
Donchian Breakout
```

Classic volatility expansion setup.

### Sell Signals

#### Expanding Intraday Risk

```text
Parkinson Vol Rising Rapidly
```

Suggests unstable market conditions.

---

## Market Structure

### Swing High Index

#### `ta_swing_high_idx`

Index of the most recent swing high.

### Interpretation

Measures how recently the market made a meaningful high.

### Buy Signals

#### Fresh Highs

```text
Current Bar - Swing High Index < 5
```

Combined with:

```text
HH = 1
BOS = 1
```

suggests strong trend continuation.

### Sell Signals

#### Aging Trend

```text
Current Bar - Swing High Index > 50
```

No new highs for a long period.

Trend may be exhausted.

---

### Swing Low Index

#### `ta_swing_low_idx`

Index of the most recent swing low.

### Interpretation

Measures how recently the market made a meaningful low.

### Buy Signals

Recent swing lows combined with:

```text
HL = 1
```

often indicate a healthy uptrend structure.

### Sell Signals

#### Fresh Downside Structure

```text
Current Bar - Swing Low Index < 5
AND
LL = 1
AND
Bearish BOS = 1
```

Strong bearish continuation.

---

# Practical Importance Ranking

## Best Trend Quality Indicators

1. MA20 Slope
2. MA50 Slope
3. Donchian Breakout
4. Swing High/Low Structure

## Best Institutional Flow Indicators

1. ADL
2. OFI
3. CMF
4. OBV

## Best Volatility Expansion Indicators

1. Parkinson Volatility
2. Historical Volatility
3. ATR
4. Keltner Channel

## Best Breakout Detection

1. Donchian Channel
2. BOS
3. Keltner Breakout
4. SuperTrend Flip

# Quant Trading Interpretation

These indicators are most useful when viewed as factors:

```text
Trend Strength
--------------
MA20 Slope
MA50 Slope

Breakout
---------
Donchian Upper
Donchian Lower

Institutional Participation
--------------------------
ADL
OFI
CMF

Volatility Compression
----------------------
HV20
Parkinson Vol

Market Structure
---------------
Swing High Index
Swing Low Index
BOS
CHoCH
```

A high-probability long setup often looks like:

```text
EMA20 > EMA50 > EMA200
MA20 Slope > 0
Close > Donchian Upper
ADL Rising
OFI > 0
Parkinson Vol Low then Expanding
Bullish BOS
```

A high-probability short setup is the exact opposite:

```text
EMA20 < EMA50 < EMA200
MA20 Slope < 0
Close < Donchian Lower
ADL Falling
OFI < 0
Volatility Expanding Downward
Bearish BOS
```