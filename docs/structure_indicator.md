# Market Structure Indicators for Buy/Sell Signals

Market Structure analysis focuses on **raw price action** rather than derived indicators such as RSI, MACD, or moving averages.

Many professional traders rely primarily on:

```text
Market Structure
+
Volume Confirmation
+
Trend Confirmation
```

The core principle is:

```text
Bullish Market
--------------
Higher Highs (HH)
Higher Lows (HL)

Bearish Market
--------------
Lower Highs (LH)
Lower Lows (LL)
```

---

# 1. Higher High / Higher Low (HH/HL)

## What It Measures

Market structure tracks how buyers and sellers are behaving.

### Bullish Structure

Price forms:

```text
HH = Higher High
HL = Higher Low
```

Example:

```text
100 → 110 → 105 → 120 → 115 → 130
       HH    HL    HH    HL    HH
```

Visual:

```text
130     HH
         ▲
120   HH
       ▲
115     HL
     /
110 HH
   ▲
105 HL
 /
100
```

Interpretation:

```text
Buyers consistently pay higher prices.

Every pullback gets bought.
```

Signal:

```text
BUY
```

---

### Bearish Structure

Price forms:

```text
LH = Lower High
LL = Lower Low
```

Example:

```text
100 → 95 → 98 → 90 → 93 → 85
       LL   LH    LL   LH   LL
```

Interpretation:

```text
Sellers dominate.

Every rebound gets sold.
```

Signal:

```text
SELL
```

---

## Algo Detection Logic

```python
if current_high > previous_high:
    higher_high = True

if current_low > previous_low:
    higher_low = True

if higher_high and higher_low:
    trend = "bullish"
```

---

## Buy Signal

Typical bullish sequence:

```text
Higher High
↓
Pullback
↓
Higher Low
↓
Buy
```

Example:

```text
100
110 HH
105 HL
```

Entry:

```text
BUY near HL
```

Reason:

```text
Bullish structure remains intact.
```

---

## Sell Signal

Example:

```text
120 HH

115 HL

Price drops to 110
```

Interpretation:

```text
Higher Low is broken.
```

Signal:

```text
SELL
```

Reason:

```text
Bullish structure invalidated.
```

---

# 2. Support and Resistance

## What It Measures

Support and resistance represent areas where buyers or sellers repeatedly enter the market.

---

## Support

Support is a price zone where buyers consistently appear.

Example:

```text
Support = 100
```

Visual:

```text
120

110

100 ← Support
------------
98
100
101
99
102
```

---

## Buy Signal

Conditions:

```text
Price reaches support

AND

Support holds
```

Example:

```text
Support = 100

Price:
101
100
99
101
104
```

Interpretation:

```text
Buyers defend support.
```

Signal:

```text
BUY
```

---

## Resistance

Resistance is a price zone where sellers consistently appear.

Example:

```text
Resistance = 150
```

Visual:

```text
150 ← Resistance
-------------
148
149
150
149
148
```

---

## Sell Signal

Conditions:

```text
Price reaches resistance

AND

Fails to break above
```

Interpretation:

```text
Selling pressure overwhelms buyers.
```

Signal:

```text
SELL
```

---

## Role Reversal

A common market behaviour:

```text
Broken Support
→ Becomes Resistance

Broken Resistance
→ Becomes Support
```

Example:

```text
100 Support

Breakdown

Price returns to 100

Fails

Rejected
```

Signal:

```text
SELL
```

---

# 3. BOS (Break of Structure)

## What It Measures

BOS confirms continuation of an existing trend.

Think:

```text
Trend already exists

BOS proves the trend continues
```

---

## Bullish BOS

Example:

```text
100
110 HH
105 HL
```

Current Structure High:

```text
110
```

Price breaks above:

```text
110
```

Visual:

```text
110 ← Previous High

Price
 ▲
 ▲
112
```

Signal:

```text
Bullish BOS

BUY
```

Interpretation:

```text
Buyers remain in control.

Uptrend continues.
```

---

## Bearish BOS

Example:

```text
100
95 LL
98 LH
```

Price breaks:

```text
95
```

Signal:

```text
Bearish BOS

SELL
```

Interpretation:

```text
Downtrend continues.
```

---

## Typical BOS Strategy

```text
HL Forms
↓
Bullish BOS
↓
Buy
```

Why?

```text
Market confirms strength before entry.
```

---

# 4. CHoCH (Change of Character)

## What It Measures

CHoCH attempts to identify a possible trend reversal.

Think:

```text
BOS = Continuation

CHoCH = Possible Reversal
```

---

## Bullish CHoCH

Starting Market Structure:

```text
100
95 LL
98 LH
90 LL
```

Expected:

```text
Another Lower Low
```

Instead:

```text
Price breaks above 98
```

Visual:

```text
98 LH
----
      ▲
      ▲
      ▲ Break
```

Interpretation:

```text
Sellers losing control.

Trend may reverse upward.
```

Signal:

```text
Bullish CHoCH

Potential BUY
```

---

## Bearish CHoCH

Starting Market Structure:

```text
100
110 HH
105 HL
120 HH
```

Expected:

```text
Another Higher High
```

Instead:

```text
Price breaks below 105
```

Interpretation:

```text
Buyers losing control.

Trend may reverse downward.
```

Signal:

```text
Bearish CHoCH

Potential SELL
```

---

# BOS vs CHoCH

## BOS (Trend Continuation)

Example:

```text
HH → HL → HH → HL → HH
```

Breaking a previous HH:

```text
Bullish BOS
```

Meaning:

```text
Trend continues.
```

Signal:

```text
BUY
```

---

## CHoCH (Trend Reversal)

Example:

```text
HH → HL → HH
```

Then:

```text
HL Breaks
```

Meaning:

```text
Bullish trend may be ending.
```

Signal:

```text
SELL
```

---

# Combined Market Structure Buy Setup

```text
Structure
---------
Higher Highs
Higher Lows

Support
--------
Price bounces from support

BOS
----
Bullish BOS

Volume
-------
OBV Rising
CMF > 0

Trend
------
EMA20 > EMA50 > EMA200
```

Result:

```text
STRONG BUY
```

---

# Combined Market Structure Sell Setup

```text
Structure
---------
Lower Highs
Lower Lows

Resistance
----------
Price rejection

BOS
----
Bearish BOS

Volume
-------
OBV Falling
CMF < 0

Trend
------
EMA20 < EMA50
```

Result:

```text
STRONG SELL
```

---

# Example Market Structure Scoring Model

```python
score = 0

if bullish_bos:
    score += 40

if higher_high:
    score += 20

if higher_low:
    score += 20

if support_bounce:
    score += 20

if bearish_choch:
    score -= 40

if lower_high:
    score -= 20

if lower_low:
    score -= 20

if resistance_rejection:
    score -= 20
```

Interpretation:

```text
Positive Score → Bullish Structure

Negative Score → Bearish Structure
```

---

# Key Takeaway

| Indicator | What It Means | Buy Signal | Sell Signal |
|------------|------------|------------|------------|
| Higher High / Higher Low | Bullish trend structure | HH + HL sequence | HL breaks |
| Support | Buyer demand zone | Bounce from support | Support fails |
| Resistance | Seller supply zone | Resistance breakout | Rejection at resistance |
| BOS (Break of Structure) | Trend continuation | Break above previous HH | Break below previous LL |
| CHoCH (Change of Character) | Potential trend reversal | Break above previous LH | Break below previous HL |

---

# Professional Interpretation

Unlike EMA, RSI, or MACD:

```text
EMA = Derived from Price
RSI = Derived from Price
MACD = Derived from Price

HH/HL
Support/Resistance
BOS
CHoCH

ARE the actual price structure itself.
```

This is why market structure often provides the **earliest buy/sell signals**, while traditional indicators are often used later for confirmation.