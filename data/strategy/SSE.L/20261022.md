# SSE.L Strategy Analysis

SSE plc (SSE.L) backtest analysis using multi-strategy evaluation on 5+ years of data (2021-2026).

## Data

- **Source**: `data/analysis-data/SSE.L.csv`
- **Total rows**: 5,053 daily bars (2006-2026)
- **5-year subset**: 1,465 daily bars (2021-01-01 to 2026-10-21)
- **Columns**: 105 (OHLCV + 98 TA indicators)
- **20Y Return**: +93.7%
- **5Y Return**: +66.7%
- **Close range**: 1,008.00 to 2,757.50
- **5Y Close range**: 1,301.50 to 2,757.50
- **Initial Capital**: £100,000
- **Slippage**: 0.1% per trade

## Key Findings

SSE.L is a **UK Utilities stock** (+66.7% over 5 years, +93.7% over 20 years) with **moderate drawdowns** (max -27.3%). Unlike AZN.L (pharma, -50.5% max DD) or NG.L (commodity, range-bound), SSE.L offers steady uptrends with periodic corrections - making it ideal for **pullback strategies** and **signal scoring approaches**.

- **Buy & Hold wins on return**: +66.4% over 5 years (but -27.3% max drawdown)
- **Best active strategy**: Score3+ at +20.8% with -26.3% DD
- **Best risk-adjusted**: RSI_Pullback at +19.5% with only -16.6% DD (Sharpe 0.45)
- **Most active strategies lose**: 15 of 17 strategies produced negative returns

## Top Strategies by Return (5Y, min 5 trades)

| Rank | Strategy | Return | Win Rate | Trades | Sharpe | MaxDD |
|------|----------|--------|----------|--------|--------|-------|
| 1 | **BuyAndHold** (Baseline) | **+66.4%** | **100.0%** | 1 | **0.58** | 27.3% |
| 2 | **Score3+** (Signal Score >=3) | **+20.8%** | **32.0%** | 25 | **0.31** | 26.3% |
| 3 | **RSI_Pullback** | **+19.5%** | **80.0%** | 5 | **0.45** | **16.6%** |
| 4 | **Hybrid_Volume** | **+7.3%** | **33.3%** | 21 | **0.19** | 28.2% |
| 5 | ADXMomentum | -1.3% | 36.8% | 19 | 0.06 | 33.2% |
| 6 | Hybrid_HMM | -2.3% | 36.8% | 19 | 0.04 | 28.8% |
| 7 | Pullback50 | -3.2% | 0.0% | 1 | -0.36 | 6.4% |
| 8 | Score4+ (Signal Score >=4) | -5.9% | 31.4% | 35 | 0.04 | 36.2% |
| 9 | MomentumComp | -7.3% | 29.2% | 24 | -0.02 | 34.5% |

## Top Strategies by Sharpe Ratio (5Y, min 5 trades)

| Rank | Strategy | Sharpe | Return | Win Rate | MaxDD |
|------|----------|--------|--------|----------|-------|
| 1 | **BuyAndHold** | **0.58** | +66.4% | 100% | 27.3% |
| 2 | **RSI_Pullback** | **0.45** | +19.5% | 80% | **16.6%** |
| 3 | **Score3+** | **0.31** | +20.8% | 32% | 26.3% |
| 4 | Hybrid_Volume | 0.19 | +7.3% | 33% | 28.2% |
| 5 | ADXMomentum | 0.06 | -1.3% | 37% | 33.2% |

## Recommended Strategies

### Primary Recommendation: RSI_Pullback

**Metrics (5Y):** 19.5% total return, 80% win rate (5 trades), 0.45 Sharpe, **16.6% max drawdown**

**Why it's best:** Best risk-adjusted returns among active strategies. Low drawdown (16.6%) with high win rate (80%). Buys RSI dips in uptrends - perfect for utility stocks with steady uptrends and periodic pullbacks.

#### Entry Rules

1. **Uptrend filter:**
   - `Close > EMA200` (price above 200-day EMA)
   - `MA200_slope_20d > 0` (MA200 is rising)

2. **RSI dip zone:**
   - `RSI14 >= 35` and `RSI14 <= 45` (moderate pullback, not panic)

3. **Bounce confirmation:**
   - `RSI14 > 45` and `RSI14 <= 55` (RSI recovering)
   - `MACD_line > MACD_signal` (momentum turning positive)

#### Exit Rules

- **RSI > 65**: Exit when RSI enters overbought territory (take profits early)

#### Example Trade Logic
```
# Day N: RSI is 38, price in pullback zone
# Day N+1: RSI bounces to 48, MACD crosses above signal → BUY
# Day N+20: RSI reaches 68 → SELL (profit ~8-12%)
```

---

### Conservative Alternative: Score3+ (Signal Scoring)

**Metrics (5Y):** 20.8% total return, 32% win rate (25 trades), 0.31 Sharpe, 26.3% max drawdown

**Why it's good:** Higher trade count (25 trades) provides more opportunities. Uses a simple 5-factor scoring system - buys when 3+ factors align. Lower win rate but decent returns.

#### Entry Rules

**5-Factor Score (buy when score >= 3):**
1. `EMA20 > EMA50` (short-term uptrend)
2. `RSI14 > 50` (bullish momentum)
3. `MACD_line > MACD_signal` (positive momentum)
4. `CMF20 > 0` (money flow positive)
5. `OFI > 0` (order flow indicator positive)

#### Exit Rules

- **Score drops below 1**: Exit when confluence breaks down (only 1 or fewer factors remain positive)

---

### Buy & Hold Comparison

| Metric | Buy & Hold | RSI_Pullback | Score3+ |
|--------|------------|--------------|---------|
| Total Return | **+66.4%** | 19.5% | 20.8% |
| Max Drawdown | 27.3% | **16.6%** | 26.3% |
| Sharpe Ratio | **0.58** | 0.45 | 0.31 |
| Trade Count | 1 | 5 | 25 |
| Win Rate | 100% | **80%** | 32% |
| Annualized | ~10.7% | ~3.5% | ~3.7% |

**Key insight:** Buy & Hold delivers the highest return (+66.4%) but with full market exposure (-27.3% DD). **RSI_Pullback offers the best risk-adjusted profile** (16.6% DD, 80% win rate) - ideal if you want to reduce drawdown exposure while capturing upside. Score3+ provides more frequent trading opportunities but with lower win rates.

## Strategy Groups Summary

### Group 1: Trend-Following Strategies

Pure trend-following approaches (EMA crossovers, SuperTrend, ADX momentum).

| Strategy | Return | MaxDD | Trades | Verdict |
|----------|--------|-------|--------|---------|
| GoldenCross | -33.4% | 41.2% | 66 | Too many whipsaws |
| EMAPullback | -38.3% | 44.0% | 42 | Pullback too tight |
| SuperTrendEMA | -49.1% | 61.4% | 226 | Extremely noisy (226 trades!) |
| VWAPTrend | -16.0% | 43.7% | 50 | Too many false entries |
| ADXMomentum | -1.3% | 33.2% | 19 | Close to breakeven |

**Verdict:** Pure trend-following doesn't work well on SSE.L. Utility stocks have gradual trends that cause whipsaws. SuperTrend generates 226 trades in 5 years - way too noisy.

---

### Group 2: Composite / Multi-Factor Strategies

Multi-factor scoring and momentum composites.

| Strategy | Return | MaxDD | Trades | Verdict |
|----------|--------|-------|--------|---------|
| MomentumComp | -7.3% | 34.5% | 24 | Too strict, misses entries |
| HighProbMulti | -37.9% | 37.9% | 10 | Over-fitting risk |
| **Score3+** | **+20.8%** | 26.3% | 25 | **Good flexibility** |
| Score4+ | -5.9% | 36.2% | 35 | Too strict |
| HMMBull | -73.5% | 73.8% | 261 | Disaster (too many signals) |

**Verdict:** HMM regime is too noisy (261 trades!). Score3+ is the clear winner - balances flexibility with confluence. Score4+ is too strict. Momentum composite misses too many entries.

---

### Group 3: Hybrid Trend + Momentum

Combines trend filters with momentum composite entries.

| Strategy | Return | MaxDD | Trades | Verdict |
|----------|--------|-------|--------|---------|
| Hybrid_Strong | -12.6% | 37.0% | 23 | MA200 filter too restrictive |
| Hybrid_HMM | -2.3% | 28.8% | 19 | HMM noise persists |
| **Hybrid_Volume** | **+7.3%** | 28.2% | 21 | Volume filter helps |

**Verdict:** Hybrid_Volume is positive but underperforms Score3+. Volume filter helps but isn't sufficient alone.

---

### Group 4: Pullback Strategies

Buy dips to moving averages or RSI in uptrends.

| Strategy | Return | MaxDD | Trades | Verdict |
|----------|--------|-------|--------|---------|
| Pullback20 | -10.0% | 10.0% | 8 | Too tight EMA20 pullback |
| Pullback50 | -3.2% | 6.4% | 1 | Only 1 trade (not meaningful) |
| **RSI_Pullback** | **+19.5%** | **16.6%** | 5 | **Best risk-adjusted** |
| RSI_DeepPullback | -18.3% | 24.2% | 1 | Only 1 trade (not meaningful) |

**Verdict:** RSI pullback is the best pullback strategy. Buying RSI dips (35-45) in uptrends works well for utility stocks. Deep pullbacks (25-40) are too rare.

---

### Group 5: Baselines

Buy & hold strategies for comparison.

| Strategy | Return | MaxDD | Verdict |
|----------|--------|-------|---------|
| **BuyAndHold** | **+66.4%** | 27.3% | **Best absolute return** |

## Failed Strategies (All Negative Returns)

### SuperTrend Strategies (-49.1%)
SuperTrend generates 226 trades in 5 years on SSE.L. This is **way too frequent** and results in heavy whipsaw losses. SuperTrend works for commodities (NG.L) but not for steady utility stocks.

### HMM Bull Strategy (-73.5%)
HMM regime signals generate 261 trades - the most of any strategy. The regime model is far too noisy for SSE.L. HMM works better on more volatile stocks like AZN.L where regimes shift more clearly.

### Golden Cross / EMA Cross (-33% to -38%)
Traditional EMA crossovers exit too late on corrections. By the time EMA20 crosses below EMA50, SSE.L has already dropped 15-20%.

## Why SSE.L Is Different From Other Stocks

1. **Steady uptrend with periodic corrections:** Unlike AZN.L (sharp -50% corrections), SSE.L has gradual pullbacks (-15-25%) that create buying opportunities.

2. **Utility sector characteristics:** Defensive stock with stable dividends. Lower volatility than pharma or commodities. Responds better to RSI pullbacks than trend-following.

3. **Less whipsaw-prone than commodities:** NG.L needs mean-reversion. SSE.L needs pullback entries.

4. **Buy & Hold is competitive:** +66.4% return makes passive holding a strong benchmark. Active strategies must justify their complexity.

5. **Signal scoring works:** Simple 3/5 factor confluence produces positive returns, unlike AZN.L where only hybrid filters worked.

## Implementation Notes

### Signal Dependencies

All strategies use the following TA columns from `data/analysis-data/SSE.L.csv`:
- `Close`, `Open`, `High`, `Low`, `Volume`
- `ta_ema20`, `ta_ema50`, `ta_ema200`
- `ma200_slope_20d` (20-day slope of MA200)
- `ta_rsi14` (RSI 14-period)
- `ta_macd_line`, `ta_macd_signal`
- `ta_roc20` (Rate of Change 20)
- `ta_cmf20` (Chaikin Money Flow)
- `ta_ofi` (Order Flow Indicator)
- `ta_adx14`, `ta_plus_di14`, `ta_minus_di14`
- `ta_volume_percentile`
- `ta_supertrend_direction`
- `ta_hmm_regime_prob_0/1/2`

### Code Reference

- **Backtest script**: `app/backtest/backtest_sse.py`
- **Results summary**: `data/backtest-reports/SSE_backtest_summary.csv`
- **Tearsheets**: `data/backtest-reports/SSE_*_tearsheet.html`
- **Equity curves**: `data/backtest-reports/SSE_*_equity.csv`

### Backtest Configuration

```python
INITIAL_CAPITAL = 100000
SLIPPAGE = 0.001  # 0.1% per trade
FREQ = "1D"
START_DATE = "2021-01-01"  # 5-year focus period
```

## Recommendations

### For Active Trading

1. **Use RSI_Pullback** as the primary strategy. Best risk-adjusted returns (19.5%, 16.6% DD, 80% win rate). Simple to implement and understand.

2. **Use Score3+** for more frequent trading opportunities. 25 trades over 5 years provides more action but lower win rate (32%).

3. **Avoid SuperTrend strategies** - generates 226 trades, way too noisy for utility stocks.

4. **Avoid HMM-based entries** - too many false signals (261 trades).

5. **Avoid pure trend-following** - Golden Cross, EMA pullbacks all lose money on SSE.L.

### For Long-Term Holding

- **Buy & Hold** delivers +66.4% over 5 years with minimal effort.
- Consider a **hybrid approach**: Core Buy & Hold position with tactical RSI pullback overlays when RSI dips to 35-45 in uptrends.
- The best active strategies capture ~30% of Buy & Hold returns but with 40% less drawdown.

### What NOT to Use

- SuperTrend strategies (226 trades, -49% return)
- HMM Bull / HMM hybrid (261 trades, -73.5% return)
- Golden Cross strategies (-33.4%, exits too late)
- HighProbMulti (-37.9%, over-fitted)
- VWAPTrend (-16%, too many false entries)

## Comparison with Other Stocks

| Aspect | SSE.L | AZN.L | HSBA.L | NG.L |
|--------|-------|-------|--------|------|
| Type | Utilities | Pharma | Financials | Natural Gas |
| 5Y Return | +66.7% | +70.0% | +127.7% (20Y) | Range-bound |
| Best Strategy | RSI_Pullback (+19.5%) | Hybrid_Strong+MC (61.2%) | ADX Momentum (+84.1%) | Supertrend + Mean-reversion |
| Max Drawdown | -27.3% | -50.5% | ~40-50% | Commodity cycles |
| Key Characteristic | Steady uptrends | Severe corrections | Strong trends | Range-bound |
| Optimal Entry | RSI dips (35-45) | Hybrid momentum | ADX > 25 | Mean-reversion |
| Optimal Exit | RSI > 65 | RSI > 70 | ADX flip | Mean-reversion levels |
| Trade Frequency | Low (5 trades) | Low (7-11 trades) | Low (2-3/year) | Medium (5-10/year) |

**Key insight:** Each asset class requires a completely different strategy. Utilities respond to RSI pullbacks (gradual corrections). Pharma needs hybrid momentum filters (sharp corrections). Financials respond to ADX momentum (strong trends). Commodities need mean-reversion (range-bound).

## Lessons Learned

1. **Pullbacks > Trend-following on utilities:** RSI pullback (19.5%) outperforms all pure trend strategies. Utility stocks trend steadily but pull back gradually - buy the dips.

2. **Signal scoring is simple and effective:** Score3+ (3/5 factors) produces +20.8% returns. No need for complex hybrid filters on SSE.L.

3. **Fewer trades = better on SSE.L:** RSI_Pullback has only 5 trades but 80% win rate. SuperTrend has 226 trades and -49% return. Quality over quantity.

4. **RSI exits work well:** RSI > 65 exits capture gains before corrections hit. Simple and effective.

5. **Buy & Hold is competitive:** +66.4% return makes it hard to beat actively. Active strategies provide risk reduction (16.6% vs 27.3% DD) but at a cost of ~47% lower returns.

6. **HMM is not universal:** HMM worked poorly on SSE.L (261 trades, -73.5%). Different assets need different regime models or no regime filter at all.

7. **Strategy selection matters more than execution:** The difference between +20.8% (Score3+) and -73.5% (HMM) is 94 percentage points. Choose your strategy carefully.
