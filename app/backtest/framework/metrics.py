"""Performance metrics extracted from vectorbt Portfolio objects."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

# Standard constants (mirrors existing scripts)
RISK_FREE = 0.05
TRADE_FREQ = 252


def _safe_float(val, default=0.0) -> float:
    """Convert to float, replacing inf/NaN with default."""
    if val is None or pd.isna(val):
        return default
    f = float(val)
    if math.isinf(f) or math.isnan(f):
        return default
    return f


def _timedelta_days(val) -> float:
    """Extract integer days from a pandas Timedelta."""
    if val is None or pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    if hasattr(val, "days"):
        return float(val.days)
    return 0.0


def calculate_metrics(pf) -> dict:
    """Extract key performance metrics from a vectorbt Portfolio object.

    Returns a flat dict suitable for DataFrame construction.
    """
    stats = pf.stats()

    # --- Percentage fields ---
    total_return_pct = _safe_float(stats.get("Total Return [%]", 0.0))
    max_dd_pct = _safe_float(stats.get("Max Drawdown [%]", 0.0))
    avg_dd_pct = _safe_float(stats.get("Average Drawdown [%]", 0.0))
    win_rate_pct = _safe_float(stats.get("Win Rate [%]", 0.0))

    # --- Ratios (may be inf) ---
    sharpe = _safe_float(stats.get("Sharpe Ratio", 0.0))
    calmar = _safe_float(stats.get("Calmar Ratio", 0.0))
    profit_factor = _safe_float(stats.get("Profit Factor", 0.0))

    # --- Trade counts ---
    total_trades = int(_safe_float(stats.get("Total Trades", 0)))

    # Calculate wins/losses from trades P&L
    trades = pf.trades
    pnl = trades.pnl
    pnl_vals = pnl.values if hasattr(pnl, "values") else np.asarray(pnl)
    total_wins = int((pnl_vals > 0).sum())
    total_losses = int((pnl_vals < 0).sum())

    # --- Trade size metrics ---
    largest_win = _safe_float(stats.get("Best Trade [%]", 0.0))
    largest_loss = _safe_float(stats.get("Worst Trade [%]", 0.0))
    avg_win = _safe_float(stats.get("Avg Winning Trade [%]", 0.0))
    avg_loss = _safe_float(stats.get("Avg Losing Trade [%]", 0.0))

    # --- Duration metrics (vectorbt returns Timedelta objects) ---
    avg_trade_duration = _safe_float(stats.get("Average Trade Duration [days]", 0.0))
    avg_win_duration = _timedelta_days(stats.get("Avg Winning Trade Duration"))
    avg_loss_duration = _timedelta_days(stats.get("Avg Losing Trade Duration"))
    avg_drawdown_duration = _timedelta_days(stats.get("Average Drawdown Duration"))
    max_drawdown_duration = _timedelta_days(stats.get("Max Drawdown Duration"))

    final_value = float(pf.final_value())

    return {
        "Total Return (%)": round(total_return_pct, 2),
        "Sharpe Ratio": round(sharpe, 2),
        "Calmar Ratio": round(calmar, 2),
        "Total Trades": total_trades,
        "Total Wins": total_wins,
        "Total Losses": total_losses,
        "Win Rate (%)": round(win_rate_pct, 1),
        "Profit Factor": round(profit_factor, 3),
        "Max Drawdown (%)": round(max_dd_pct, 2),
        "Avg Drawdown (%)": round(avg_dd_pct, 2),
        "Largest Win (%)": round(largest_win, 2),
        "Largest Loss (%)": round(largest_loss, 2),
        "Avg Win (%)": round(avg_win, 2),
        "Avg Loss (%)": round(avg_loss, 2),
        "Avg Trade Duration (d)": round(avg_trade_duration, 1),
        "Avg Win Duration (d)": round(avg_win_duration, 1),
        "Avg Loss Duration (d)": round(avg_loss_duration, 1),
        "Avg DD Duration (d)": round(avg_drawdown_duration, 1),
        "Max DD Duration (d)": round(max_drawdown_duration, 1),
        "Final Net Value": round(final_value, 0),
    }


def rank_strategies(results: list[dict], sort_by: str = "Total Return (%)") -> list[dict]:
    """Rank strategy results by a given metric (descending)."""
    return sorted(results, key=lambda r: r.get(sort_by, 0) or 0, reverse=True)


def pick_best(results: list[dict], criteria: list[str] | None = None) -> list[dict]:
    """Pick the best strategies by multiple criteria.

    Default: sort by Total Return, then break ties with Profit Factor and
    Max Drawdown (lower is better).
    """
    if criteria is None:
        criteria = ["Total Return (%)", "Profit Factor", "Max Drawdown (%)"]

    def sort_key(r):
        # Max Drawdown is inverted (lower = better)
        dd = r.get("Max Drawdown (%)", 0)
        return (
            r.get("Total Return (%)", 0) or 0,
            r.get("Profit Factor", 0) or 0,
            -dd if dd != 0 else 0,
        )

    ranked = sorted(results, key=sort_key, reverse=True)
    return ranked


def summarize_table(table: pd.DataFrame) -> str:
    """Return a human-readable summary string for a results DataFrame."""
    lines = [
        f"{'Strategy':<40} {'Return%':>10} {'Sharpe':>8} {'PF':>8} {'DD%':>8} {'WR%':>7} {'Trades':>7}",
        "─" * 90,
    ]
    for idx, row in table.iterrows():
        lines.append(
            f"{idx:<40} {row.get('Total Return (%)', 0):>10.2f} "
            f"{row.get('Sharpe Ratio', 0):>8.2f} {row.get('Profit Factor', 0):>8.3f} "
            f"{row.get('Max Drawdown (%)', 0):>8.2f} {row.get('Win Rate (%)', 0):>7.1f} "
            f"{row.get('Total Trades', 0):>7d}"
        )
    return "\n".join(lines)
