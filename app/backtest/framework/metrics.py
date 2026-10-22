"""Performance metrics extracted from vectorbt Portfolio objects."""

from __future__ import annotations

import pandas as pd

# Standard constants (mirrors existing scripts)
RISK_FREE = 0.05
TRADE_FREQ = 252


def calculate_metrics(pf) -> dict:
    """Extract key performance metrics from a vectorbt Portfolio object.

    Returns a flat dict suitable for DataFrame construction.
    """
    stats = pf.stats()

    def _get(key: str, default=0.0):
        val = stats.get(key, default)
        if pd.isna(val):
            return default
        return float(val)

    # Convert percentage fields to consistent units
    total_return_pct = _get("Total Return [%]", 0.0)
    max_dd_pct = _get("Max Drawdown [%]", 0.0)
    avg_dd_pct = _get("Average Drawdown [%]", 0.0)
    win_rate_pct = _get("Win Rate [%]", 0.0)

    # Calculate Sharpe and Calmar if available (annualized)
    sharpe = _get("Sharpe Ratio", 0.0)
    calmar = _get("Calmar Ratio", 0.0)

    # Additional useful metrics
    total_trades = int(_get("Total Trades", 0))
    profit_factor = _get("Profit Factor", 0.0)
    final_value = float(pf.final_value())
    total_wins = int(_get("Total Wins", 0))
    total_losses = int(_get("Total Losses", 0))
    largest_win = float(_get("Largest Win [%]", 0.0))
    largest_loss = float(_get("Largest Loss [%]", 0.0))
    avg_win = float(_get("Average Win [%]", 0.0))
    avg_loss = float(_get("Average Loss [%]", 0.0))
    avg_trade_duration = _get("Average Trade Duration [days]", 0.0)
    avg_win_duration = _get("Average Win Duration [days]", 0.0)
    avg_loss_duration = _get("Average Loss Duration [days]", 0.0)
    avg_drawdown_duration = _get("Average Drawdown Duration [days]", 0.0)
    max_drawdown_duration = _get("Max Drawdown Duration [days]", 0.0)

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
