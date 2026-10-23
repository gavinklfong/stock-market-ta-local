"""Run custom LGEN.L strategies and compare with built-in top performers."""
import sys
from pathlib import Path

BACKTEST_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKTEST_DIR))

import pandas as pd
from framework.engine import BacktestEngine, DEFAULT_CUTOFF
from framework.extensions import load_custom_strategies
from framework.metrics import calculate_metrics

# Load data
df = pd.read_csv("data/analysis-data/LGEN.L.csv")
df["Date"] = pd.to_datetime(df["Date"])
df = df.sort_values("Date").reset_index(drop=True)
df = df.dropna(subset=["Close", "High", "Low"])
df.index = df["Date"]
df = df[df["Date"] >= DEFAULT_CUTOFF].reset_index(drop=True)
df.index = df["Date"]

print(f"Data: {len(df)} rows, {df['Date'].iloc[0].date()} to {df['Date'].iloc[-1].date()}")
print(f"Price range: {df['Close'].min():.2f} - {df['Close'].max():.2f}")
print(f"BH return: {(df['Close'].iloc[-1]/df['Close'].iloc[0] - 1)*100:.2f}%\n")

# Load custom strategies
custom_dir = BACKTEST_DIR / "custom"
custom_strategies = load_custom_strategies(custom_dir)
print(f"Loaded {len(custom_strategies)} custom strategies: {list(custom_strategies.keys())}\n")

# Engine with cutoff
engine = BacktestEngine(
    data_path="data/analysis-data/LGEN.L.csv",
    cutoff_date=DEFAULT_CUTOFF,
    trailing_pct=None,  # no trailing stop for fair comparison
)

# Run all custom strategies
print("=" * 70)
print("  Custom Strategies — LGEN.L Backtest Results")
print("=" * 70)

results = []
for name, sfn in custom_strategies.items():
    try:
        pf, metrics = engine.run_and_metrics(sfn)
        metrics["Strategy"] = name
        results.append(metrics)
        total_ret = metrics.get("Total Return (%)", 0)
        sharpe = metrics.get("Sharpe Ratio", 0)
        trades = metrics.get("Total Trades", 0)
        win_rate = metrics.get("Win Rate (%)", 0)
        max_dd = metrics.get("Max Drawdown (%)", 0)
        pf_val = metrics.get("Profit Factor", 0)
        print(f"  {name:30s}  Return: {total_ret:8.2f}%  Sharpe: {sharpe:6.3f}  Trades: {trades:4d}  Win: {win_rate:5.1f}%  MaxDD: {max_dd:7.2f}%  PF: {pf_val:.2f}")
    except Exception as e:
        print(f"  {name:30s}  ERROR: {e}")

# Sort and display
summary = pd.DataFrame(results).sort_values("Total Return (%)", ascending=False)
summary.set_index("Strategy", inplace=True)
print(f"\n{'='*70}")
print("  Sorted by Total Return")
print(f"{'='*70}")
for name, row in summary.iterrows():
    print(f"  {name:30s}  Return: {row['Total Return (%)']:8.2f}%  Sharpe: {row['Sharpe Ratio']:6.3f}  Trades: {int(row['Total Trades']):4d}  Win: {row['Win Rate (%)']:5.1f}%  MaxDD: {row['Max Drawdown (%)']:7.2f}%  PF: {row['Profit Factor']:.2f}")
