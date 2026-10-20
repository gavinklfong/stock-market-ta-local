# Stock Market Technical Analysis — Complete Reference

## 1. Project Overview

**Repository:** stock-market-ta-local

A modular, parallel pipeline that downloads OHLCV market data, computes technical analysis indicators, and generates interactive HTML reports for stock/ETF tickers.

### Commands

```bash
# Download data
python app/download-market-data/download_tickers.py
python app/download-market-data/download_stock_info.py

# TA indicators (all 7 modules run in PARALLEL)
python app/calculate-ta/run_calculation.py
python app/calculate-ta/run_calculation.py trend momentum  # subset
python app/calculate-ta/run_calculation.py --dry-run       # preview

# Full Prefect pipeline (downloads + TA + merge)
python -m app.analysis_pipeline.run_pipeline

# Analyse market data and generate HTML report (one file per ticker)
python app/analyse-market-data/analyse_ticker.py              # all tickers
python app/analyse-market-data/analyse_ticker.py AAPL MSFT    # specific
python app/analyse-market-data/analyse_ticker.py --dry-run    # show data only

# Analyse sector data
python app/analyse-market-data/analyse_sector.py              # all sectors
python app/analyse-market-data/analyse_sector.py Utilities   # specific

# All-tickers overview report
python app/analyse-market-data/analyse_all.py              # all tickers
python app/analyse-market-data/analyse_all.py --dry-run    # show data only

# Backtest
python app/backtest/backtest_ng.py
python app/backtest/backtest_ng.py --strategy supertrend

# Tests
python run_test.py                              # all tests
python run_test.py calculate-ta                 # TA module tests only
```

### Architecture

- All 7 TA modules are independent — each reads raw OHLCV from `data/market-data/`
- Parallel execution via `ThreadPoolExecutor(max_workers=7)`
- Output: per-module `{ticker}_ta_{type}.csv`, merged into `{ticker}.csv`
- Full pipeline: Prefect flow downloads OHLCV + P/E → runs TA → merges into `data/analysis-data/{ticker}.csv`

### TA Module Index

| Module | Key Indicators |
|--------|---------------|
| `trend` | EMA20/50/200, SuperTrend, SMA10/20/50, MA slopes, price/MA20 ratio, price/EMA distance, Aroon, ADX/DI, Donchian, Keltner |
| `momentum` | RSI(14), MACD (line/signal/histogram), ROC(20), Williams %R(14), CCI(20), TSI(25,13), RSI Z-Score, RSI Percentile |
| `volume` | OBV, CMF(20), VWAP(20), OFI, log volume, ADL, MFI(14), EMV(14), Volume Oscillator, Volume Z-Score, Volume Percentile |
| `volatility` | ATR(14), Bollinger Bands(20,2), Band Width, %B, Historical Volatility, Parkinson Volatility, ATR Stop, ATR Position Size, Reward Risk Ratio, ATR Percentile |
| `regime` | GARCH(1,1) vol forecast, 3-state HMM regime |
| `structure` | Swing highs/lows, HH/HL/LH/LL, BOS, CHoCH, S/R levels |
| `return` | Forward returns 5d/10d/20d; Past performance 1m/3m/6m/1y; Rolling alpha20/beta20; Relative strength vs ^FTSE |

---

## 2. How an Algo Agent Determines Stock Trend

An algorithmic trading agent does not "know" the future direction of a stock. Instead, it estimates the probability that a stock is moving in an upward, downward, or sideways trend using historical and real-time market data.

### 2.1 Price Action Trend Detection

#### Moving Averages

A stock is generally considered bullish when:

```text
Current Price > 50-day MA > 200-day MA
```

#### Common Signals

**Golden Cross** — 50-day MA crosses above 200-day MA → Bullish signal

**Death Cross** — 50-day MA crosses below 200-day MA → Bearish signal

### 2.2 Market Structure Analysis

Traders analyse highs and lows recursively:

```text
Higher Highs (HH) + Higher Lows (HL) = Uptrend
Lower Highs (LH) + Lower Lows (LL) = Downtrend
```

#### Break of Structure (BOS)

A BOS occurs when price breaks a previous swing high (bullish) or swing low (bearish), confirming the trend continues.

### 2.3 Volume Analysis

```text
Volume confirms price action.
```

- Rising price + rising volume = strong trend
- Rising price + falling volume = weak trend (potential reversal)

### 2.4 Momentum Analysis

Momentum indicators (RSI, MACD, ROC) measure the speed and strength of price movement.

### 2.5 Sentiment & News

Algo agents may incorporate:

```text
Social sentiment scores
News sentiment (positive/negative)
Analyst ratings
Insider trading activity
```

### 2.6 Macro Factors

```text
Interest rates
Inflation
GDP growth
Industry trends
```

### 2.7 Combined Approach

Professional trading systems combine multiple indicators:

```text
Trend + Momentum + Volume = High-Confidence Signal
```

### 2.8 Key Takeaways

| Factor | Purpose |
|--------|---------|
| Moving Averages | Identify trend direction |
| Market Structure | Confirm trend via highs/lows |
| Volume | Confirm price moves |
| Momentum | Detect reversals early |
| Sentiment | Gauge market psychology |
| Macro | Contextual filter |

---

## 3. Trend Indicators for Buy/Sell Signals

Trend indicators help answer: **Which direction is the stock moving?**

Most commonly used:

```text
EMA20   = Short-Term Trend
EMA50   = Medium-Term Trend
EMA200  = Long-Term Trend
SuperTrend = Entry / Exit Trigger
```

Professional traders combine all four to build a high-confidence trend-following system.

### 3.1 EMA20 (20-Period Exponential Moving Average)

Tracks the average price over the last 20 periods, giving more weight to recent prices.

**Buy Signal:** Price crosses above EMA20
**Sell Signal:** Price crosses below EMA20

### 3.2 EMA50 (50-Period Exponential Moving Average)

Tracks the average price over the last 50 periods.

**Buy Signal:** Price crosses above EMA50
**Sell Signal:** Price crosses below EMA50

### 3.3 EMA200 (200-Period Exponential Moving Average)

Tracks the average price over the last 200 periods.

**Buy Signal:** Price crosses above EMA200 (major bullish signal)
**Sell Signal:** Price crosses below EMA200 (major bearish signal)

### 3.4 SuperTrend

Uses ATR to determine trend direction and generate signals.

**Buy Signal:** SuperTrend flips green (price closes above SuperTrend)
**Sell Signal:** SuperTrend flips red (price closes below SuperTrend)

### 3.5 Professional Trend-Following System

```text
STRONG BUY
----------
EMA20 > EMA50 > EMA200
SuperTrend = GREEN
Price closes above SuperTrend

SELL
----
EMA20 < EMA50
SuperTrend = RED
Price closes below SuperTrend
```

### 3.6 Key Takeaway

| Indicator | Purpose | Buy Signal | Sell Signal |
|-----------|---------|------------|-------------|
| EMA20 | Short-term trend | Price above EMA20 | Price below EMA20 |
| EMA50 | Medium-term trend | Price above EMA50 | Price below EMA50 |
| EMA200 | Long-term trend | Price above EMA200 | Price below EMA200 |
| SuperTrend | Entry/Exit trigger | SuperTrend flips green | SuperTrend flips red |

---

## 4. Momentum Indicators for Buy/Sell Signals

Momentum indicators answer: **How strong is the move?**

A stock can remain in an uptrend while momentum weakens. Momentum indicators often provide early warning signals before trend indicators react.

### 4.1 RSI(14) — Relative Strength Index

Compares the magnitude of recent gains versus recent losses.

```text
RSI > 70 = Overbought
RSI < 30 = Oversold
RSI = 50 = Neutral
```

#### Buy Signal #1 — Oversold Reversal

```text
RSI < 30 (oversold)
RSI crosses above 30
```

Interpretation: Selling pressure weakening, buyers returning.

#### Buy Signal #2 — RSI Bullish Divergence

Price makes lower lows, RSI makes higher lows.

Interpretation: Downward momentum fading.

#### Sell Signal #1 — Overbought

```text
RSI > 70
RSI crosses below 70
```

#### Sell Signal #2 — RSI Bearish Divergence

Price makes higher highs, RSI makes lower highs.

#### Strong Buy Signal

```text
RSI < 30 AND Price at Support AND Volume Spike
```

### 4.2 MACD (Moving Average Convergence Divergence)

```text
MACD Line = EMA12 - EMA26
Signal Line = EMA9 of MACD
Histogram = MACD - Signal
```

#### Buy Signal #1 — MACD Crossover

```text
MACD crosses above Signal Line
```

#### Buy Signal #2 — MACD Bullish Divergence

Price makes lower lows, MACD makes higher lows.

#### Sell Signal #1 — MACD Crossover

```text
MACD crosses below Signal Line
```

#### Sell Signal #2 — MACD Bearish Divergence

Price makes higher highs, MACD makes lower highs.

#### Strong Buy Signal

```text
MACD > 0
MACD crosses above Signal
Volume Rising
```

### 4.3 ROC (Rate of Change)

Measures percentage price change over a lookback period.

#### Buy Signal

```text
ROC > 0
ROC trending upward
```

#### Sell Signal

```text
ROC < 0
ROC trending downward
```

### 4.4 Williams %R

```text
Williams %R = -100 to 0
< -80 = Oversold
> -20 = Overbought
```

#### Buy Signal

```text
Williams %R < -80 (oversold)
Williams %R crosses above -80
```

#### Sell Signal

```text
Williams %R > -20 (overbought)
Williams %R crosses below -20
```

### 4.5 CCI (Commodity Channel Index)

```text
CCI > 100 = Overbought
CCI < -100 = Oversold
```

#### Buy Signal

```text
CCI < -100 (oversold)
CCI crosses above -100
```

#### Sell Signal

```text
CCI > 100 (overbought)
CCI crosses below 100
```

### 4.6 TSI (True Strength Index)

```text
TSI > 0 = Bullish
TSI < 0 = Bearish
```

#### Buy Signal

```text
TSI crosses above Signal Line
```

#### Sell Signal

```text
TSI crosses below Signal Line
```

### 4.7 Professional Momentum System

```text
STRONG BUY
----------
RSI > 50 AND rising
MACD > Signal
ROC > 0
CCI > 0
Williams %R > -50

STRONG SELL
-----------
RSI < 50 AND falling
MACD < Signal
ROC < 0
CCI < 0
Williams %R < -50
```

### 4.8 Key Takeaway

| Indicator | Purpose | Buy Signal | Sell Signal |
|-----------|---------|------------|-------------|
| RSI(14) | Overbought/Oversold | RSI < 30 then crosses above 30 | RSI > 70 then crosses below 70 |
| MACD | Trend + Momentum | MACD crosses above Signal | MACD crosses below Signal |
| ROC(20) | Rate of Change | ROC > 0 and rising | ROC < 0 and falling |
| Williams %R(14) | Overbought/Oversold | Crosses above -80 | Crosses below -20 |
| CCI(20) | Cyclical turns | Crosses above -100 | Crosses below 100 |
| TSI(25,13) | Momentum strength | Crosses above Signal | Crosses below Signal |

---

## 5. Volume Indicators for Buy/Sell Signals

Volume indicators answer a different question than trend or momentum indicators.

```text
Trend:   Which direction is the market moving?
Momentum: How strong is the move?
Volume:  Are institutions and large traders participating?
```

Many breakouts fail because price moves without sufficient volume support.

### 5.1 OBV (On Balance Volume)

Tracks whether volume is flowing into or out of a stock.

```text
If Close > Previous Close: OBV = Previous OBV + Volume
If Close < Previous Close: OBV = Previous OBV - Volume
```

**Bullish OBV:** Price rises and OBV rises.
**Bearish OBV:** Price falls and OBV falls.
**Divergence:** OBV rising while price falling = accumulation.

### 5.2 CMF (Chaikin Money Flow)

Measures money flow over a set period.

```text
CMF > 0 = Buying pressure
CMF < 0 = Selling pressure
```

**Buy Signal:** CMF crosses above 0
**Sell Signal:** CMF crosses below 0

### 5.3 VWAP (Volume Weighted Average Price)

```text
VWAP = Cumulative (Price × Volume) / Cumulative Volume
```

**Buy Signal:** Price is above VWAP
**Sell Signal:** Price is below VWAP

### 5.4 OFI (Order Flow Imbalance)

Measures the difference between buy and sell volume pressure.

**Buy Signal:** OFI > 0 and rising
**Sell Signal:** OFI < 0 and falling

### 5.5 Money Flow Index (MFI)

Volume-weighted RSI.

```text
MFI > 80 = Overbought
MFI < 20 = Oversold
```

**Buy Signal:** MFI < 20 then crosses above 20
**Sell Signal:** MFI > 80 then crosses below 80

### 5.6 Professional Volume System

```text
STRONG BUY
----------
Price rising
OBV rising
CMF > 0
Price > VWAP
Volume > 20-day average

STRONG SELL
-----------
Price falling
OBV falling
CMF < 0
Price < VWAP
Volume > 20-day average
```

### 5.7 Key Takeaway

| Indicator | Purpose | Buy Signal | Sell Signal |
|-----------|---------|------------|-------------|
| OBV | Volume flow direction | OBV rising with price | OBV falling with price |
| CMF(20) | Money flow | CMF > 0 | CMF < 0 |
| VWAP | Intraday average price | Price above VWAP | Price below VWAP |
| MFI(14) | Volume-weighted RSI | MFI < 20 then crosses above | MFI > 80 then crosses below |

---

## 6. Volatility Indicators for Buy/Sell Signals

Volatility indicators answer: **How aggressively is price moving?**

```text
Trend:   Which direction is price moving?
Momentum: How strong is the move?
Volatility: How aggressively is price moving?
```

A common mistake is treating volatility indicators as direct buy/sell indicators.

```text
ATR = Risk and Volatility Indicator
Bollinger Bands = Volatility + Mean Reversion + Breakout Indicator
```

### 6.1 ATR(14) — Average True Range

Measures the average price movement over the past 14 periods.

**ATR does NOT measure direction** — only volatility.

#### ATR Buy Signal

```text
EMA20 > EMA50
MACD > Signal
Price Breaks Resistance
ATR Expands
```

Interpretation: Breakout has energy behind it.

#### ATR Sell Signal

```text
Support Breaks
ATR Expands
```

Interpretation: Selling pressure is accelerating.

#### ATR Volatility Compression

```text
ATR declining: 5 → 4 → 3 → 2 → 1
```

Warning: Large breakout may be coming (not a direct signal).

#### ATR for Stop Losses

```text
Stop Loss = Entry Price - (2 × ATR)
```

ATR is used more for risk management, position sizing, and stop placement than actual buy/sell signals.

### 6.2 Bollinger Bands

Consists of:

```text
Upper Band
Middle Band (20 SMA)
Lower Band
```

Bands expand during high volatility and contract during low volatility.

#### Strategy 1: Mean Reversion

**Buy Signal:** Price touches or falls below the lower band
**Sell Signal:** Price touches or exceeds the upper band

**Strong Mean-Reversion Buy:**

```text
Price below lower band AND RSI oversold
```

#### Strategy 2: Bollinger Band Breakout

**Buy Signal:** Price closes above the upper band
**Sell Signal:** Price closes below the lower band

#### Strategy 3: Bollinger Band Squeeze

Bands become unusually narrow, followed by volatility expansion.

**Bullish Squeeze:** Bands narrow + price breaks upper band + volume increases → BUY

**Bearish Squeeze:** Bands narrow + price breaks lower band + volume increases → SELL

### 6.3 Professional Volatility Scoring

```python
volatility_score = 0

if atr_slope > 0:
    volatility_score += 30

if close > bollinger_upper:
    volatility_score += 40

if bollinger_squeeze_breakout:
    volatility_score += 30
```

```text
80-100 = Strong Bullish Expansion
60-80  = Bullish Volatility
40-60  = Neutral
20-40  = Bearish Volatility
0-20   = Strong Bearish Expansion
```

### 6.4 Key Takeaway

| Indicator | Purpose | Buy Signal | Sell Signal |
|-----------|---------|------------|-------------|
| ATR(14) | Volatility measurement | ATR expands during bullish breakout | ATR expands during bearish breakdown |
| Bollinger Bands | Volatility + Mean Reversion | Lower-band bounce, upper-band breakout, bullish squeeze | Upper-band rejection, lower-band breakdown, bearish squeeze |

### 6.5 Most Reliable Volatility Setup

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

---

## 7. Regime Indicators

Regime indicators answer: **What type of market am I trading in?**

```text
EMA        = Direction
RSI        = Momentum
OBV        = Volume Flow
ATR        = Volatility
Market Structure = Price Behaviour
Regime Models = Market Environment
```

A regime model is often used as a filter to determine whether a trading signal is trustworthy.

### 7.1 GARCH Volatility Regime

GARCH (Generalized Autoregressive Conditional Heteroskedasticity) forecasts future volatility.

**Key insight:**
- High volatility tends to cluster
- Low volatility tends to cluster

**Regime signals:**
- GARCH forecasts low volatility → range-bound strategy preferred
- GARCH forecasts high volatility → breakout strategy preferred

### 7.2 HMM (Hidden Markov Model) Regime

A 3-state HMM classifies the market into:

```text
State 1: Bullish
State 2: Bearish
State 3: Neutral / High Volatility
```

**How HMM is used in trading:**

```text
If HMM predicts Bullish regime → Use trend-following strategies
If HMM predicts Bearish regime → Use short-selling or hedging
If HMM predicts Neutral regime → Use range-bound or mean-reversion strategies
```

### 7.3 Regime as a Strategy Filter

```text
Trend Strategy in Bull Regime     → High Win Rate
Trend Strategy in Bear Regime     → Low Win Rate (avoid)
Mean-Reversion in Range Regime    → High Win Rate
Mean-Reversion in Trend Regime    → Low Win Rate (avoid)
```

### 7.4 Professional Regime-Based Approach

```text
Step 1: Determine market regime
Step 2: Select appropriate strategy for that regime
Step 3: Enter trade only if strategy signal aligns with regime
Step 4: Exit trade if regime changes
```

### 7.5 Key Takeaway

| Regime | Preferred Strategy | Avoid |
|--------|-------------------|-------|
| Bullish | Trend following, momentum | Mean-reversion, shorting |
| Bearish | Short-selling, hedging | Long trend-following |
| Range-bound | Mean-reversion, Bollinger | Breakout strategies |
| High Volatility | Breakout, wide stops | Tight stop-loss strategies |

---

## 8. Market Structure Indicators for Buy/Sell Signals

Market Structure analysis focuses on **raw price action** rather than derived indicators such as RSI, MACD, or moving averages.

Many professional traders rely primarily on:

```text
Market Structure
+
Volume Confirmation
+
Trend Confirmation
```

### 8.1 Higher High / Higher Low (HH/HL) — Bullish Structure

```text
Price forms HH = Higher High, HL = Higher Low
```

Example:

```text
100 → 110 → 105 → 120 → 115 → 130
        HH    HL    HH    HL    HH
```

### 8.2 Lower High / Lower Low (LH/LL) — Bearish Structure

```text
Price forms LH = Lower High, LL = Lower Low
```

Example:

```text
130 → 120 → 125 → 110 → 115 → 100
        LH    HL    LH    LL    LH
```

### 8.3 Break of Structure (BOS)

A BOS confirms trend continuation.

**Bullish BOS:** Price breaks above a previous swing high → trend continues upward

**Bearish BOS:** Price breaks below a previous swing low → trend continues downward

### 8.4 Change of Character (CHoCH)

A CHoCH signals potential trend reversal.

**Bullish CHoCH:** Uptrend, price breaks below last HL → potential reversal to downtrend

**Bearish CHoCH:** Downtrend, price breaks above last LH → potential reversal to uptrend

### 8.5 Support and Resistance (S/R)

**Support:** Price level where buying pressure historically exceeds selling pressure.

**Resistance:** Price level where selling pressure historically exceeds buying pressure.

#### Buy Signals

```text
Price bounces off support
Price breaks resistance with volume
```

#### Sell Signals

```text
Price rejects at resistance
Price breaks support with volume
```

### 8.6 Professional Structure-Based Trading

```text
STRONG BUY
----------
HH + HL structure
BOS confirmed above previous swing high
Volume increasing on breakout
Price above EMA20 and EMA50

STRONG SELL
-----------
LH + LL structure
BOS confirmed below previous swing low
Volume increasing on breakdown
Price below EMA20 and EMA50
```

### 8.7 Key Takeaway

| Pattern | Type | Signal |
|---------|------|--------|
| HH + HL | Bullish structure | Long positions |
| LH + LL | Bearish structure | Short positions or exits |
| BOS (bullish) | Trend continuation | Add to long |
| BOS (bearish) | Trend continuation | Add to short |
| CHoCH (bullish) | Potential reversal | Consider long entry |
| CHoCH (bearish) | Potential reversal | Consider short entry |
| Support bounce | Range-bound | Buy |
| Resistance rejection | Range-bound | Sell |

---

## 9. Technical Analysis Indicator Summary

For an algo trading agent, it is useful to group indicators by purpose. A robust trading system typically combines multiple indicator categories rather than relying on a single signal.

| Category | Indicators | Purpose |
|----------|-----------|---------|
| Trend | SMA, EMA, MACD, SuperTrend, Ichimoku | Direction |
| Momentum | RSI, MACD, ROC, Williams %R, CCI | Strength |
| Volume | OBV, CMF, VWAP, MFI | Participation |
| Volatility | ATR, Bollinger Bands | Aggressiveness |
| Market Structure | HH/HL, BOS, CHoCH, S/R | Price action |
| Regime | GARCH, HMM | Market environment |

---

## 10. Additional Technical Analysis Indicators

### 10.1 MA Slope Indicators

#### `ta_ma20_slope` and `ta_ma50_slope`

Measures the rate of change of the moving average over a 10-bar lookback.

**Interpretation:** Instead of "Is the trend up or down?" it asks "How fast is the trend accelerating or decelerating?"

**Bullish Trend Acceleration:**

```text
MA20 Slope > 0
MA50 Slope > 0
MA20 Slope Increasing
```

Example: MA20 Slope: 1% → 2% → 4% → 6% — Momentum is strengthening.

**Strong Buy:**

```text
EMA20 > EMA50 > EMA200
AND MA20 Slope > 0
AND MA50 Slope > 0
```

Suggests a strong institutional uptrend.

**Trend Weakening (Sell Signal):**

```text
MA20 Slope: +5% → +3% → +1% → -1%
```

**Strong Sell:**

```text
MA20 Slope < 0
MA50 Slope < 0
```

Both short-term and medium-term trends are declining.

### 10.2 Price vs Moving Average Ratio

#### `ta_price_to_ma20` and `ta_price_to_ma50`

Measures how far the price is from moving averages.

```text
ta_price_to_ma20 = Price / MA20
```

**Buy Signal (Mean Reversion):**

```text
Price significantly below MA20
Price < 0.95 × MA20
```

**Sell Signal (Mean Reversion):**

```text
Price significantly above MA20
Price > 1.05 × MA20
```

### 10.3 Price vs EMA Distance

#### `ta_price_to_ema20` and `ta_price_to_ema50`

Similar to price/MA ratio, but uses EMA.

### 10.4 Price vs SuperTrend

#### `ta_price_to_supertrend`

Measures distance from SuperTrend level.

**Buy Signal:** Price close to or below SuperTrend in uptrend
**Sell Signal:** Price close to or above SuperTrend in downtrend

### 10.5 SMA Ratios

#### `ta_sma10_to_sma20`, `ta_sma20_to_sma50`, `ta_sma10_to_sma50`

Short-term to medium-term SMA relationships.

**Strong Buy:**

```text
SMA10 > SMA20 > SMA50
All ratios > 1
```

### 10.6 Donchian Channel

#### `ta_donchian_channel`

Tracks the highest high and lowest low over a lookback period.

```text
Upper Band = Highest High over N periods
Lower Band = Lowest Low over N periods
Middle = (Upper + Lower) / 2
```

**Buy Signal:** Price touches lower band (mean reversion)
**Sell Signal:** Price touches upper band (mean reversion)
**Breakout Buy:** Price breaks above upper band
**Breakout Sell:** Price breaks below lower band

### 10.7 Keltner Channel

#### `ta_keltner_channel`

Similar to Bollinger Bands but uses ATR instead of standard deviation.

```text
Upper Band = EMA + (Multiplier × ATR)
Middle = EMA
Lower Band = EMA - (Multiplier × ATR)
```

**Buy Signal:** Price touches or falls below lower band
**Sell Signal:** Price touches or exceeds upper band

### 10.8 Aroon Indicator

#### `ta_aroon_up`, `ta_aroon_down`, `ta_aroon_oscillator`

Measures the strength of a trend and whether it is likely to continue.

```text
Aroon Up = 100 × (Periods since highest high within period) / Period Length
Aroon Down = 100 × (Periods since lowest low within period) / Period Length
Aroon Oscillator = Aroon Up - Aroon Down
```

**Buy Signal:**
- Aroon Up near 100 and Aroon Down near 0 → Strong uptrend
- Aroon Up crosses above Aroon Down → Bullish crossover

**Sell Signal:**
- Aroon Down near 100 and Aroon Up near 0 → Strong downtrend
- Aroon Down crosses above Aroon Up → Bearish crossover

### 10.9 ADX / DI (Average Directional Index / Directional Indicator)

#### `ta_adx`, `ta_di_plus`, `ta_di_minus`

Measures trend strength, not direction.

```text
ADX > 25 = Strong trend
ADX < 20 = Weak trend / range-bound
```

**Buy Signal:**
- DI+ > DI- (bullish direction)
- ADX rising (trend strengthening)

**Sell Signal:**
- DI- > DI+ (bearish direction)
- ADX rising (trend strengthening in downward direction)

### 10.10 EMA Cross

#### `ta_ema_cross`

Detects when short-term EMA crosses long-term EMA.

**Buy Signal:** Short-term EMA crosses above long-term EMA (Golden Cross)
**Sell Signal:** Short-term EMA crosses below long-term EMA (Death Cross)

### 10.11 Divergence Detection

#### `ta_rsi_divergence`

Detects bullish or bearish divergence between price and RSI.

**Bullish Divergence:** Price makes lower lows, RSI makes higher lows → Potential reversal up

**Bearish Divergence:** Price makes higher highs, RSI makes lower highs → Potential reversal down

### 10.12 Key Takeaway

| Indicator | Purpose | Buy Signal | Sell Signal |
|-----------|---------|------------|-------------|
| MA20/50 Slope | Trend acceleration | Slope > 0 and rising | Slope < 0 and falling |
| Price/MA20 Ratio | Deviation from average | Price < 0.95 × MA20 | Price > 1.05 × MA20 |
| SMA Ratios | Short-term vs long-term | SMA10 > SMA20 > SMA50 | SMA10 < SMA20 < SMA50 |
| Donchian Channel | Breakout / reversion | Break above upper or touch lower | Break below lower or touch upper |
| Keltner Channel | Volatility-adjusted bands | Touch lower band | Touch upper band |
| Aroon | Trend strength | Aroon Up crosses above Aroon Down | Aroon Down crosses above Aroon Up |
| ADX/DI | Trend direction & strength | DI+ > DI- with rising ADX | DI- > DI+ with rising ADX |
| EMA Cross | Golden/Death Cross | Short EMA crosses above long | Short EMA crosses below long |
| RSI Divergence | Early reversal signal | Price lower low, RSI higher low | Price higher high, RSI lower high |

---
