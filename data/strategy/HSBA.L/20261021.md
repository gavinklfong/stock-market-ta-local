# HSBA.L Strategy Analysis

HSBC Holdings (HSBA.L) backtest analysis using trend-following strategies on 20 years of data (2006-2026).

## Data

- **Source**: `data/analysis-data/HSBA.L.csv`
- **Rows**: 5,052 daily bars
- **Period**: 2006-10-20 to 2026-10-20 (20 years)
- **Columns**: 105 (OHLCV + 7 TA modules + P/E fundamentals)
- **20Y Return**: +127.7% (strong bull/trending stock)
- **Initial Capital**: £100,000
- **Slippage**: 0.1% per trade

## Key Findings

HSBA.L is a **strong trending/bull stock** — trend-following strategies are appropriate. Mean-reversion is NOT suitable. SuperTrend flips too frequently (85%+ of bars) and requires heavy filtering with EMA/momentum indicators.

## Top Strategies by Return

| Rank | Strategy | Return | Win Rate | Trades | Sharpe | MaxDD |
|------|----------|--------|----------|--------|--------|-------|
| 1 | **ADX Momentum** | **+84.1%** | 48.9% | 47 | 0.399 | 23.3% |
| 2 | **Momentum Composite** | **+71.9%** | 37.7% | 69 | 0.333 | 25.5% |
| 3 | **Score Adaptive** | **+48.6%** | 26.5% | 103 | 0.241 | 70.5% |
| 4 | **VWAP Trend** | +24.3% | 36.6% | 123 | 0.179 | 39.5% |
| 5 | **Score 5+** | +8.8% | 38.3% | 81 | 0.115 | 37.7% |

### 1. ADX Momentum (BEST)

**Signals:**
- Enter: `ADX > 25` AND `+DI > -DI` AND `RSI > 50` AND `MACD > Signal`
- Exit: `ADX < 20` OR `+DI < -DI` OR `RSI < 40`

**Why it works:** ADX captures strong trending momentum. The 25 threshold filters out choppy markets, while +DI/-DI direction confirms trend direction. MACD confirms momentum direction. Clean 47 trades over 20 years = ~2-3 per year.

**Best metrics:** Highest win rate (48.9%), best Sharpe (0.399), lowest max drawdown (23.3%), best profit factor (2.19).

### 2. Momentum Composite

**Signals:**
- Enter: `RSI > 55` AND `MACD > Signal` AND `ROC(20) > 0` AND `Williams %R > -50` AND `CMF > 0` AND `EMA20 > EMA50`
- Exit: (signal's default exits)

**Why it works:** Six momentum factors in agreement — strong confirmation of bullish momentum. Fewer signals than single-factor strategies but higher conviction.

### 3. Score Adaptive

**Signals:**
- Score each bar on multiple factors (EMA trend, momentum, volume, structure)
- Enter when score >= adaptive threshold (higher score = lower threshold)
- Exit based on score dropping below exit threshold

**Trade-off:** Lower win rate (26.5%) but captures large trends. Higher trade count (103) but still manageable.

## Failed Strategies

### SuperTrend+EMA (ALL FAILING, -80% to -90% return)

SuperTrend flips too frequently (1,000+ signals in 20 years = ~50/year). Even with EMA/RSI filtering, the excessive trading generates massive drag from slippage and whipsaws.

**Lesson:** SuperTrend is NOT suitable for HSBA.L without extremely aggressive signal filtering (e.g., requiring BOS confirmation + volume spike + multi-day hold minimum).

### Golden Cross (ALL FAILING, -39% to -57% return)

Golden Cross strategies don't exit frequently enough on a strong uptrend. The strategy holds through major corrections, and exits are too late. Even with ATR trailing or BB exits, returns are negative.

**Lesson:** On strongly trending stocks, entry-only signals without aggressive trend-following exits will lose money. The stock's 20Y trend means you should hold, but corrections are deep enough to wipe gains.

### HMM Bull (FAILING, -69% return)

HMM (Hidden Markov Model) generates 644 trades — way too many. Overtrading with slippage destroys returns. The regime model's signals are too noisy for this application.

## Strategy Groups Summary

### Group 1: Golden Cross + Exits (11 variants)
- All negative returns (-39% to -57%)
- Entry: EMA20>EMA50>EMA200, MA20 slope>0, SuperTrend=1, RSI>50, MACD>Signal
- Exit variants: No filter, RSI>70, BB upper, ATR trail, ST+EMA+RSI combo
- **Verdict:** Not suitable for HSBA.L

### Group 2: EMA Pullback + Exits (8 variants)
- Returns: -26% to -6%
- Entry: EMA20>EMA50>EMA200, price near EMA20, RSI 40-55, SuperTrend=1
- Exit variants: EMA50 cross, RSI>65/70, ATR trail, ST flip, EMA20 cross, ST+EMA+RSI combo, RSI weakness
- **Verdict:** Marginal — ATR trail and RSI weakness exits help but not enough

### Group 3: SuperTrend+EMA (9 variants)
- ALL failing (-79% to -88%)
- Entry: SuperTrend flip + EMA20>EMA50 + RSI>40
- Exit variants: Various (all fail)
- **Verdict:** DO NOT USE — SuperTrend noise overwhelms any filter

### Group 4: Individual Trend (4 strategies)
| Strategy | Return | WR | Trades | Verdict |
|----------|--------|-----|--------|---------|
| VWAP Trend | +24.3% | 36.6% | 123 | Good |
| Market Structure | -9.6% | 0.0% | 1 | Too few signals |
| BOS Breakout | 0% | N/A | 0 | No signals generated |
| **ADX Momentum** | **+84.1%** | **48.9%** | **47** | **BEST** |

### Group 5: Composite/Multi-Factor (7 strategies)
| Strategy | Return | WR | Trades | Verdict |
|----------|--------|-----|--------|---------|
| Momentum Composite | +71.9% | 37.7% | 69 | Good |
| High Prob Multi (5+) | -33.8% | 5.0% | 20 | Too strict |
| Score 3+ | +5.3% | 21.6% | 88 | Weak |
| Score 4+ | -26.9% | 25.5% | 110 | Declining |
| Score 5+ | +8.8% | 38.3% | 81 | Moderate |
| HMM Bull | -69.3% | 45.3% | 644 | Overtrading |
| **Score Adaptive** | **+48.6%** | **26.5%** | **103** | **Good** |

## Recommendations

### Best Overall: ADX Momentum
- Clean signals, low trade count, best risk-adjusted returns
- Consider adding a minimum holding period (e.g., 3 days) to reduce whipsaws

### Second Best: Momentum Composite
- Strong returns but lower win rate
- Could be combined with ADX Momentum as a filter

### Score Adaptive
- Interesting approach but high drawdown (70.5%)
- Consider optimizing the scoring weights

### What NOT to Use
- SuperTrend strategies (too many false signals)
- Golden Cross strategies (exits too late on corrections)
- HMM Bull (overtrading)
- Market Structure/BOS (too few or no signals on HSBA.L)

## Output Files

| File | Description |
|------|-------------|
| `data/backtest-reports/HSBC_backtest_results.csv` | All 40 strategy results |
| `data/backtest-reports/HSBC_backtest_summary.html` | Multi-strategy comparison (top 5) |
| `data/backtest-reports/HSBC_ADX_Momentum.html` | ADX Momentum tearsheet |
| `data/backtest-reports/HSBC_HMM_Bull.html` | HMM Bull tearsheet |
| `data/backtest-reports/HSBC_Golden_Cross___RSI_>_70.html` | Golden Cross + RSI>70 exits |
| `data/backtest-reports/HSBC_Golden_Cross___BB_Upper.html` | Golden Cross + BB upper exits |
| `data/backtest-reports/HSBC_Golden_Cross___ATR_Trail_(3x,10d).html` | Golden Cross + ATR trail exits |

## Comparison with NG.L

| Aspect | HSBA.L | NG.L |
|--------|--------|------|
| Type | Stock (financials) | Commodity (natural gas) |
| 20Y Return | +127.7% | Varies (range-bound) |
| Best Strategy | ADX Momentum (trend-following) | Supertrend + mean-reversion |
| SuperTrend | Fails (too many flips) | Works (commodity mean-reverts) |
| Golden Cross | Fails (doesn't exit) | Works (commodity cycles) |
| Optimal WR | ~49% (fewer, higher-quality trades) | Varies by strategy |
| Trade Frequency | 2-3 per year (ideal) | 5-10 per year |

**Key insight:** Strategy performance is highly dependent on the asset's price action characteristics. What works for commodities (NG.L) fails for stocks (HSBA.L) and vice versa.
