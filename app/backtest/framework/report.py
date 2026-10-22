"""Generate interactive Plotly HTML report from backtest results."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
]


def generate_report(
    results: list[dict],
    df: pd.DataFrame,
    ticker: str,
    output_dir: str | Path,
    top_n: int = 10,
    sort_by: str = "Total Return (%)",
    title: str | None = None,
) -> Path:
    """Generate a multi-tab HTML report.

    Tabs
    ----
    1. Summary Table — ranked strategy metrics
    2. Equity Curves — cumulative returns for top strategies
    3. Drawdowns — max drawdown overlay
    4. Trade Stats — win/loss distribution

    Parameters
    ----------
    results : list[dict]
        Each dict has at least "Strategy" and numeric metric keys.
    df : pd.DataFrame
        Full OHLCV+TA data (needed for equity curve plotting).
    ticker : str
        Ticker symbol used in titles.
    output_dir : str | Path
        Where to write the HTML file.
    top_n : int
        How many strategies to show on chart tabs.
    sort_by : str
        Metric name to rank by.
    title : str | None
        Override report title.
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Sort and slice
    ranked = sorted(results, key=lambda r: r.get(sort_by, 0) or 0, reverse=True)
    top = ranked[:top_n]
    top_names = [r.get("Strategy", "") for r in top]

    # Build Portfolio lookup for plotting
    portfolio_map: dict[str, Any] = {}
    for r in results:
        pf = r.get("Portfolio")
        if pf is not None:
            portfolio_map[r.get("Strategy", "")] = pf

    report_title = title or f"{ticker} — Optimal Strategy Report"

    # ======================================================================
    # Tab 1: Summary Table
    # ======================================================================
    table_df = pd.DataFrame(ranked)
    # Drop the raw Portfolio object (kept in results for chart tabs only)
    table_df.drop(columns=["Portfolio"], inplace=True, errors="ignore")
    table_html = table_df.to_html(index=False, classes="table", float_format="%.2f")

    # ======================================================================
    # Tab 2: Equity Curves
    # ======================================================================
    fig_eq = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3],
        subplot_titles=["Cumulative Returns", "Drawdown"],
    )

    for i, r in enumerate(top):
        sname = r.get("Strategy", f"Strategy_{i}")
        pf = portfolio_map.get(sname)
        if pf is None:
            continue
        color = COLORS[i % len(COLORS)]
        label = _short_label(sname, ticker)

        cum = pf.cumulative_returns()
        fig_eq.add_trace(
            go.Scatter(
                x=cum.index, y=cum.values,
                name=f"{label} Return",
                line=dict(width=1.5, color=color),
            ),
            row=1, col=1,
        )
        dd = pf.drawdown()
        fig_eq.add_trace(
            go.Scatter(
                x=dd.index, y=dd.values,
                name=f"{label} DD",
                line=dict(width=1, color=color),
                opacity=0.6,
                showlegend=False,
            ),
            row=2, col=1,
        )

    # Benchmark
    bench = df["Close"].pct_change().cumsum()
    bench_cum = (df["Close"] / df["Close"].iloc[0] - 1).cumsum()
    fig_eq.add_trace(
        go.Scatter(
            x=bench_cum.index, y=bench_cum.values,
            name="Buy & Hold Return",
            line=dict(width=1.5, color="black", dash="dot"),
        ),
        row=1, col=1,
    )

    fig_eq.update_layout(
        title=dict(text=report_title, x=0.5, xanchor="center"),
        width=1200,
        height=800,
        showlegend=True,
        legend=dict(
            orientation="v",
            xanchor="left",
            x=1.02,
            yanchor="top",
            y=1,
            font=dict(size=10),
            itemclick="toggleothers",
            itemdoubleclick="toggle",
        ),
        hovermode="x unified",
    )
    eq_html = fig_eq.to_html(full_html=False, include_plotlyjs="cdn")

    # ======================================================================
    # Tab 3: Bar chart of key metrics (single chart)
    # ======================================================================
    metric_cols = [
        "Total Return (%)", "Sharpe Ratio", "Profit Factor",
        "Win Rate (%)", "Max Drawdown (%)", "Total Trades",
    ]
    available_cols = [c for c in metric_cols if c in table_df.columns]

    fig_bar = go.Figure()

    for i, r in enumerate(top):
        color = COLORS[i % len(COLORS)]
        label = _short_label(r.get("Strategy", ""), ticker)
        values = [r.get(c, 0) for c in available_cols]
        fig_bar.add_trace(
            go.Bar(
                x=available_cols,
                y=values,
                name=label,
                marker_color=color,
                showlegend=(i < 3),
            ),
        )

    fig_bar.update_layout(
        title="Key Metrics Comparison",
        width=1200,
        barmode="group",
        height=600,
        showlegend=True,
        legend=dict(
            orientation="v",
            xanchor="left",
            x=1.02,
            yanchor="top",
            y=1,
            font=dict(size=10),
        ),
        xaxis_title="Metric",
        yaxis_title="Value",
    )
    bar_html = fig_bar.to_html(full_html=False, include_plotlyjs="cdn")

    # ======================================================================
    # Tab 4: Best strategy detail
    # ======================================================================
    best = ranked[0] if ranked else None
    best_html = "<p>No results to display.</p>"
    if best:
        best_name = best.get("Strategy", "Unknown")
        best_pf = portfolio_map.get(best_name)
        if best_pf:
            # Trade log
            trades = best_pf.trades
            closed = trades.closed
            if len(closed) > 0:
                pnl_df = closed.pnl
                fig_pnl = go.Figure()
                fig_pnl.add_trace(
                    go.Histogram(
                        x=pnl_df.values,
                        nbinsx=30,
                        marker_color="#1f77b4",
                        name="Trade P&L",
                    )
                )
                fig_pnl.update_layout(
                    title=f"{best_name} — Trade P&L Distribution",
                    xaxis_title="Profit/Loss (£)",
                    yaxis_title="Count",
                    height=400,
                )
                best_html = fig_pnl.to_html(full_html=False, include_plotlyjs="cdn")
            else:
                best_html = "<p>No closed trades.</p>"

    # ======================================================================
    # Assemble full HTML with tabs
    # ======================================================================
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{report_title}</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
    body {{ font-family: Arial, sans-serif; margin: 20px; background: #f9f9f9; }}
    .tab-nav {{ display: flex; border-bottom: 2px solid #ccc; margin-bottom: 16px; }}
    .tab-nav button {{
        padding: 10px 20px; border: 1px solid #ccc; background: #eee;
        cursor: pointer; border-bottom: none; border-radius: 4px 4px 0 0; margin-right: 4px;
    }}
    .tab-nav button.active {{ background: #fff; font-weight: bold; border-bottom: 2px solid #fff; margin-bottom: -2px; }}
    .tab-content {{ display: none; }}
    .tab-content.active {{ display: block; }}
    .table {{ border-collapse: collapse; width: 100%; background: #fff; }}
    .table th, .table td {{ border: 1px solid #ddd; padding: 8px; text-align: right; }}
    .table th {{ background: #f0f0f0; text-align: center; }}
    .table td:first-child {{ text-align: left; }}
    .card {{ background: #fff; padding: 16px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 12px; }}
    .card > div.plotly-graph-div {{ overflow: visible !important; }}
</style>
</head>
<body>
<h2>{report_title}</h2>

<div class="tab-nav">
    <button class="active" onclick="showTab('summary', this)">Summary</button>
    <button onclick="showTab('equity', this)">Equity Curves</button>
    <button onclick="showTab('metrics', this)">Metrics</button>
    <button onclick="showTab('detail', this)">Best Strategy</button>
</div>

<div id="summary" class="tab-content active">
    <div class="card">
        <h3>Ranked Results (sorted by {sort_by})</h3>
        {table_html}
    </div>
</div>

<div id="equity" class="tab-content">
    <div class="card">{eq_html}</div>
</div>

<div id="metrics" class="tab-content">
    <div class="card">{bar_html}</div>
</div>

<div id="detail" class="tab-content">
    <div class="card">
        <h3>Best Strategy: {best_name if best else 'N/A'}</h3>
        <p><strong>Total Return:</strong> {best.get('Total Return (%)', 'N/A')}% &nbsp;
           <strong>Sharpe:</strong> {best.get('Sharpe Ratio', 'N/A')} &nbsp;
           <strong>PF:</strong> {best.get('Profit Factor', 'N/A')} &nbsp;
           <strong>Max DD:</strong> {best.get('Max Drawdown (%)', 'N/A')}% &nbsp;
           <strong>Win Rate:</strong> {best.get('Win Rate (%)', 'N/A')}%</p>
        {best_html}
    </div>
</div>

<script>
function showTab(id, btn) {{
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-nav button').forEach(el => el.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    btn.classList.add('active');
}}
</script>
</body>
</html>"""

    out_path = out_dir / f"{ticker}_backtest_report.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path


def _short_label(name: str, ticker: str) -> str:
    """Abbreviate a strategy name for display."""
    # Strip ticker prefix if present
    clean = name.replace(f"{ticker}_", "").replace(f"{ticker}-", "")
    return clean if len(clean) <= 30 else name[:28] + "…"
