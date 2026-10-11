# Volume Indicators for Buy/Sell Signals

Volume indicators answer a different question than trend or momentum indicators.

```text
Trend:
Which direction is the market moving?

Momentum:
How strong is the move?

Volume:
Are institutions and large traders participating?
```

Many breakouts fail because price moves without sufficient volume support.

Volume indicators help determine whether a move is likely driven by:

```text
Real accumulation
or
Speculative price movement
```

---

# 1. OBV (On Balance Volume)

## What OBV Measures

OBV tracks whether volume is flowing into or out of a stock.

Formula:

```text
If Close > Previous Close:
    OBV = Previous OBV + Volume

If Close < Previous Close:
    OBV = Previous OBV - Volume
```

The absolute value is not important.

The trend of the OBV line is what matters.

---

## Bullish OBV Signal

Price rises and OBV rises.

Example:

```text
Day     Price    OBV
1       100      1.0M
2       102      1.5M
3       105      2.3M
4       108      3.1M
```

Interpretation:

```text
Price increasing
Volume increasing
Buyers accumulating shares
```

Signal:

```text
BUY
```

---

## Bearish OBV Signal

Price falls and OBV falls.

Example:

```text
Day     Price    OBV
1       100      3.0M
2       98       2.5M
3       95       1.9M
4       92       1.2M
```

Interpretation:

```text
Volume leaving the stock
Sellers dominate
```

Signal:

```text
SELL
```

---

## Bullish OBV Divergence

Price makes lower lows while OBV makes higher lows.

Example:

```text
Price:
100 → 95 → 90

OBV:
1000 → 1200 → 1400
```

Interpretation:

```text
Price still falling

Institutions quietly accumulating
```

Signal:

```text
BUY
```

Potentially an early reversal signal.

---

## Bearish OBV Divergence

Price rises while OBV declines.

Example:

```text
Price:
100 → 110 → 120

OBV:
5000 → 4800 → 4500
```

Interpretation:

```text
Price rising

Smart money reducing positions
```

Signal:

```text
SELL
```

Potential warning before price weakness appears.

---

# 2. CMF (Chaikin Money Flow)

## What CMF Measures

CMF measures buying and selling pressure over a period of time.

Range:

```text
-1.0 to +1.0
```

Interpretation:

```text
CMF > 0
Money flowing into stock

CMF < 0
Money flowing out of stock
```

---

## Buy Signal

Condition:

```text
CMF > 0
```

Example:

```text
CMF = +0.20
```

Interpretation:

```text
Accumulation
Buying pressure
Capital entering stock
```

Signal:

```text
BUY
```

---

## Sell Signal

Condition:

```text
CMF < 0
```

Example:

```text
CMF = -0.15
```

Interpretation:

```text
Distribution
Selling pressure
Capital leaving stock
```

Signal:

```text
SELL
```

---

## Strong Buy Example

Conditions:

```text
CMF > +0.15

Price > EMA50
```

Interpretation:

```text
Positive trend

Strong accumulation
```

Signal:

```text
STRONG BUY
```

---

## Strong Sell Example

Conditions:

```text
CMF < -0.15

Price < EMA50
```

Interpretation:

```text
Negative trend

Strong distribution
```

Signal:

```text
STRONG SELL
```

---

# 3. VWAP (Volume Weighted Average Price)

## What VWAP Measures

VWAP calculates the average traded price weighted by volume.

Formula:

```text
Average Price × Volume
```

VWAP identifies:

```text
Where most trading activity occurred.
```

Institutions commonly use VWAP for execution and trend confirmation.

---

## Buy Signal

Condition:

```text
Price > VWAP
```

Example:

```text
Price = 105

VWAP = 100
```

Interpretation:

```text
Market trading above average transaction price

Buyers control the market
```

Signal:

```text
BUY
```

---

## Sell Signal

Condition:

```text
Price < VWAP
```

Example:

```text
Price = 95

VWAP = 100
```

Interpretation:

```text
Market trading below average transaction price

Sellers control the market
``