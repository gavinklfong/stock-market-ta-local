"""
NG.L Backtest — Multi-strategy evaluation with vectorbt.

Strategies tested on data/ta-data/NG.L.csv:
  1. SuperTrend      — Entry on direction flip (-1→1), exit on (1→-1)
  2. RSI Reversal    — Buy RSI<30, sell RSI>70
  3. MACD Histogram  — Buy when histogram turns positive, sell when negative
  4. MA Crossover    — Buy MA20>MA50, sell MA20<MA50
  5. Structure       — Buy HH+HL (bullish structure), sell LL+LH (bearish)

Usage:
  python app/backtest/backtest_ng.py              # run all strategies
  python app/backtest/backtest_ng.py --strategy supertrend  # single strategy
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import vectorbt as vbt
from vectorbt.portfolio.enums import SizeType

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent.parent  # stock-market-ta-local
DATA_PATH = ROOT / "data" / "ta-data" / "NG.L.csv"

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load NG.L TA CSV and return a clean DataFrame."""
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    # df = df.set_index("Date")
    df.index = df["Date"]

    # --- Filter to last 10 years ---
    cutoff_date = pd.Timestamp("2023-10-15")
    df = df[df["Date"] >= cutoff_date].reset_index(drop=True)
    df.index = df["Date"]
    return df


# ---------------------------------------------------------------------------
# Strategy signal generators
# ---------------------------------------------------------------------------
def signal_supertrend(df: pd.DataFrame):
    """SuperTrend direction flip:  -1→1 = buy, 1→-1 = sell."""
    direction = df["ta_supertrend_direction"]
    entry = (direction == 1) & (direction.shift(1) == -1)
    exit_ = (direction == -1) & (direction.shift(1) == 1)
    return entry.astype(int), exit_.astype(int) * -1


def signal_rsi(df: pd.DataFrame):
    """RSI mean-reversion: RSI<30 = buy, RSI>70 = sell."""
    rsi = df["ta_rsi14"]
    entry = rsi < 30
    exit_ = rsi > 70
    return entry.astype(int), exit_.astype(int) * -1


def signal_macd(df: pd.DataFrame):
    """MACD histogram flip: positive = buy, negative = sell."""
    hist = df["ta_macd_histogram"]
    entry = (hist > 0) & (hist.shift(1) <= 0)
    exit_ = (hist < 0) & (hist.shift(1) >= 0)
    return entry.astype(int), exit_.astype(int) * -1


def signal_ma_crossover(df: pd.DataFrame):
    """MA20/MA50 crossover: MA20>MA50 = buy, MA20<MA50 = sell."""
    ma20 = df["ta_ma20"]
    ma50 = df["ta_ma50"]
    entry = (ma20 > ma50) & (ma20.shift(1) <= ma50.shift(1))
    exit_ = (ma20 < ma50) & (ma20.shift(1) >= ma50.shift(1))
    # Also exit at end of data if position is open
    return entry.astype(int), exit_.astype(int) * -1


def signal_structure(df: pd.DataFrame):
    """Structure-based: HH+HL = bullish (buy), LL+LH = bearish (sell)."""
    hh = df["ta_hh"].fillna(0).astype(int)
    hl = df["ta_hl"].fillna(0).astype(int)
    ll = df["ta_ll"].fillna(0).astype(int)
    lh = df["ta_lh"].fillna(0).astype(int)

    entry = (hh == 1) | (hl == 1)  # any bullish structure marker
    exit_ = (ll == 1) | (lh == 1)  # any bearish structure marker
    return entry.astype(int), exit_.astype(int) * -1


STRATEGIES = {
    "supertrend": signal_supertrend,
    "rsi": signal_rsi,
    "macd": signal_macd,
    "ma_crossover": signal_ma_crossover,
    "structure": signal_structure,
}


# ---------------------------------------------------------------------------
# Backtest runner
# ---------------------------------------------------------------------------
def run_backtest(
    df: pd.DataFrame,
    strategy_name: str,
    init_cash: float = 100_000,
    commission: float = 0.001,  # 0.1% per trade
    slippage: float = 0.0,
) -> vbt.Portfolio:
    """Run a single backtest and return a vectorbt Portfolio object."""
    signals = STRATEGIES[strategy_name](df)
    entries, exits = signals

    pf = vbt.Portfolio.from_signals(
        close=df["Close"],
        entries=entries,
        exits=exits,
        init_cash=init_cash,
        freq="1D",
        slippage=slippage,
        size=1.0,
        size_type=SizeType.Percent,
        fees=commission,
    )
    return pf


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def print_summary(pf: vbt.Portfolio, name: str):
    """Print a formatted summary for one strategy."""
    stats_df = pf.stats()
    total_return = stats_df.get("Total Return [%]", 0)
    total_trades = stats_df.get("Total Trades", 0)
    win_rate = stats_df.get("Win Rate [%]", 0)
    profit_factor = stats_df.get("Profit Factor", 0)
    max_dd = stats_df.get("Max Drawdown [%]", 0)
    final_value = pf.final_value()

    print(f"\n{'='*60}")
    print(f"  {name.upper()}")
    print(f"{'='*60}")
    print(f"  Total Return:      {total_return:7.2f}%")
    print(f"  Total Trades:      {total_trades:6d}")
    print(f"  Win Rate:          {win_rate:6.1f}%")
    print(f"  Profit Factor:     {profit_factor:7.3f}")
    print(f"  Max Drawdown:      {max_dd:7.2f}%")
    print(f"  Final Net Value:   £{final_value:,.0f}")


def compare_all(df: pd.DataFrame, strategies: list[str] | None = None):
    """Run all strategies and print a comparison table."""
    if strategies is None:
        strategies = list(STRATEGIES.keys())

    results = []
    for name in strategies:
        print(f"Running strategy: {name} ...")
        pf = run_backtest(df, name)
        print_summary(pf, name)

        stats_df = pf.stats()
        results.append({
            "Strategy": name,
            "Total Return (%)": round(stats_df.get("Total Return [%]", 0), 2),
            "Total Trades": int(stats_df.get("Total Trades", 0)),
            "Win Rate (%)": round(stats_df.get("Win Rate [%]", 0), 1),
            "Profit Factor": round(stats_df.get("Profit Factor", 0), 3),
            "Max Drawdown (%)": round(stats_df.get("Max Drawdown [%]", 0), 2),
            "Final Net Value": round(pf.final_value(), 0),
        })

    # Comparison table
    table = pd.DataFrame(results).set_index("Strategy")
    print(f"\n{'='*80}")
    print("  COMPARISON SUMMARY")
    print(f"{'='*80}")
    print(table.to_string())
    return table


# ---------------------------------------------------------------------------
# Drawdown & equity curves
# ---------------------------------------------------------------------------
def plot_comparison(df: pd.DataFrame, strategies: list[str] | None = None):
    """Plot equity curves using plotly directly."""
    if strategies is None:
        strategies = list(STRATEGIES.keys())

    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3],
        subplot_titles=["Cumulative Returns", "Drawdown"],
    )

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    for i, name in enumerate(strategies):
        pf = run_backtest(df, name)
        # Cumulative returns
        cum_ret = pf.cumulative_returns()
        fig.add_trace(
            go.Scatter(x=cum_ret.index, y=cum_ret.values, name=name,
                       line=dict(width=1.5, color=colors[i % len(colors)])),
            row=1, col=1,
        )
        # Drawdown
        dd = pf.drawdown()
        fig.add_trace(
            go.Scatter(x=dd.index, y=dd.values, name=name + " DD",
                       line=dict(width=1, color=colors[i % len(colors)]),
                       opacity=0.6),
            row=2, col=1,
        )

    fig.update_layout(
        title="NG.L Strategy Comparison",
        height=700,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified",
    )

    out_path = ROOT / "app" / "backtest" / "equity_curves.html"
    fig.write_html(str(out_path))
    print(f"\nEquity curves saved to: {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # Parse args
    args = sys.argv[1:]
    if "--strategy" in args:
        idx = args.index("--strategy")
        if idx + 1 < len(args):
            selected = [args[idx + 1]]
        else:
            print("Error: --strategy requires a value")
            sys.exit(1)
    else:
        selected = None

    # Load data
    print(f"Loading data from {DATA_PATH} ...")
    df = load_data()
    print(f"  {len(df)} rows, {df.index.min().date()} → {df.index.max().date()}")
    print(f"  Close range: £{df['Close'].min():.2f} → £{df['Close'].max():.2f}")

    # Run backtests and get comparison table
    table = compare_all(df, selected)

    # Plot (non-interactive mode — writes HTML)
    plot_comparison(df, selected)

    # Save raw results
    table_path = ROOT / "app" / "backtest" / "backtest_results.csv"
    table.to_csv(table_path)
    print(f"\nResults saved to: {table_path}")


if __name__ == "__main__":
    main()
