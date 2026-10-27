"""Compute and print year-by-year returns for top strategies + B&H."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from framework.engine import BacktestEngine
from strategies.builtins import STRATEGIES
from framework.extensions import load_custom_strategies

custom = load_custom_strategies(Path(__file__).resolve().parent / "custom")

top_strategies = {
    "ema_pullback_vol": STRATEGIES["ema_pullback_vol"],
    "ema_pullback": STRATEGIES["ema_pullback"],
    "hmm_regime": STRATEGIES["hmm_regime"],
    "multiscore60": STRATEGIES["multiscore60"],
    "trend_momentum": STRATEGIES["trend_momentum"],
}

engine = BacktestEngine(
    data_path=str(Path(__file__).resolve().parent.parent.parent / "data" / "analysis-data" / "MKS.L.csv"),
    cutoff_date=pd.Timestamp("2016-10-26"),
)

bench_returns = engine.get_benchmark_returns()
bench_df = engine.df.copy()
bench_df["bench_ret"] = bench_returns

# Print header
col_width = 12
header = f"{'Year':<{col_width}}"
header += f"{'Buy & Hold':>{col_width}}"
for name in top_strategies:
    short = name.replace("_", " ").title()[:18]
    header += f" {short:>{col_width}}"
print(header)
print("-" * len(header))

for year in range(2016, 2027):
    year_mask = bench_df.index.year == year
    if not year_mask.any():
        continue
    year_close = bench_df.loc[year_mask, "Close"]
    
    bh_ret = (year_close.iloc[-1] / year_close.iloc[0] - 1) * 100 if len(year_close) > 1 else 0
    
    row = f"{year:<{col_width}}"
    row += f"{bh_ret:>{col_width}.2f}%"
    
    for name, sfn in top_strategies.items():
        strat_ret = engine.get_strategy_returns(sfn)
        year_strat = strat_ret.loc[strat_ret.index.year == year]
        if len(year_strat) > 0:
            total = (1 + year_strat).prod() - 1
            row += f" {total*100:>{col_width}.2f}%"
        else:
            row += f" {'0.00%':>{col_width}}"
    
    print(row)
