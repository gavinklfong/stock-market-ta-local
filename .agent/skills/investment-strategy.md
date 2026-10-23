# Investment Strategy Skill

This skill defines a structured approach to formulating and evaluating investment strategies.

## File Naming Convention for Custom Scripts

All custom scripts must follow these rules:

1. **Naming**: `{ticker}_{function}.py` — ticker first, then a short description of the script's purpose
2. **Location**: Place in `app/backtest/custom_scripts/` (not `app/backtest/`)

### Examples

| Correct | Incorrect |
|---------|-----------|
| `LGEN.L_deep_analysis.py` | `deep_lgen_analysis.py` |
| `LGEN.L_custom_backtest.py` | `run_lgen_custom.py` |
| `NG.L_exit_analysis.py` | `ng_exit_analysis.py` |
| `AZN.L_backtest.py` | `backtest_azon.py` |
| `VUKG.L_deep_analysis.py` | `vukg_deep_analysis.py` |

### When creating a new script:

- Identify the target ticker and function
- Format: `{Ticker}_{purpose}.py` (e.g., `BP.L_backtest.py`, `HSBA.L_optimized_strategy.py`)
- Place in `app/backtest/custom_scripts/` — never in `app/backtest/` directly

## Strategy Formulation Framework

### 1. Market Analysis

- **Trend analysis**: EMA20/50/200 alignment, SuperTrend direction
- **Momentum**: RSI, MACD, ROC for entry/exit timing
- **Volume**: OBV, CMF, MFI for conviction
- **Volatility**: ATR, Bollinger Bands for position sizing

### 2. Fundamental Filters

- P/E ratio vs. industry average
- Dividend yield and payout ratio sustainability
- Revenue and earnings growth trajectory
- Debt-to-equity and current ratio

### 3. Time-Based Factors

#### Weekday Effect (day-of-week)

| Column | Description | Values |
|--------|-------------|--------|
| `weekday` | Day of week from Date index | 0=Monday … 4=Friday, 5=Saturday, 6=Sunday |

**Day-of-week considerations:**

| Day | Behaviour | Strategy action |
|-----|-----------|-----------------|
| Monday | Weekend news gaps down | Potential dip-buying if fundamentals solid |
| Tuesday | Low volatility | Ideal entry day for new positions |
| Wednesday | Mid-week profit-taking | Watch for reversals |
| Thursday | Options expiry volatility (where applicable) | Caution on wide stops |
| Friday | Pre-weekend risk | Reduce exposure or exit before weekend |
| Sat/Sun | No trading | N/A — gaps priced in Monday open |

**Rules:**
- Avoid opening new positions on Fridays (weekend gap risk)
- Monday dip buying: prefer when `weekday == 0` and price gaps below previous close
- Tuesday entries: generally lower slippage and tighter spreads
- Wednesday: monitor for mid-week reversals, tighten trailing stops
- Thursday: widen stops if weekly options expiry affects the stock

### 4. Position Sizing

- Risk no more than 2% of portfolio per trade
- Use ATR-based stop distances (e.g., 2×ATR)
- Scale into positions on confirmation signals

### 5. Exit Rules

- **Stop loss**: ATR-based (2×–3×ATR below entry for longs)
- **Take profit**: Risk-reward ratio ≥ 2:1
- **Time stop**: Exit if no progress after N trading days
- **Signal reversal**: Exit when primary indicator flips (e.g., SuperTrend change)

### 6. Backtesting Checklist

- [ ] Strategy defined with clear entry/exit rules
- [ ] Position sizing logic specified
- [ ] Weekend/day-of-week filters included if relevant
- [ ] Backtested on ≥3 years of data
- [ ] Results validated against buy-and-hold baseline
- [ ] Drawdown and Sharpe ratio meet thresholds (Sharpe ≥ 0.5, max DD ≤ 20%)

## Strategy Types

| Type | Description | Best conditions |
|------|-------------|-----------------|
| Trend following | Ride established trends | Strong trend, high ADX |
| Mean reversion | Buy dips, sell rips | Range-bound, RSI extremes |
| Momentum | Follow strong price action | High volume, breakout |
| Contrarian | Opposite of crowd | Extreme fear/greed, oversold |
| Dividend income | Income-focused | High yield, sustainable payout |
| Breakout | Enter on volume surge | Consolidation ending, high volume |

## Strategy Evaluation

After backtesting, rate strategies on:

1. **Return**: Total return vs. benchmark
2. **Sharpe ratio**: Risk-adjusted return (target ≥ 0.5)
3. **Max drawdown**: Largest peak-to-trough (target ≤ 20%)
4. **Win rate**: Percentage of profitable trades (target ≥ 45%)
5. **Profit factor**: Gross profit / gross loss (target ≥ 1.5)
6. **Calmar ratio**: Return / max drawdown (target ≥ 1.0)
