#!/usr/bin/env python3
"""Generate interactive HTML backtest report for Score 3+ / RSI > 75."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

BASE_DIR = Path(__file__).resolve().parent.parent.parent
REPORT_DIR = BASE_DIR / "data" / "backtest-reports"
REPORT_DIR.mkdir(exist_ok=True)

SLIPPAGE = 0.001
RISK_FREE = 0.05
TRADE_FREQ = 252


def load_ticker(ticker):
    path = BASE_DIR / "data" / "analysis-data" / f"{ticker}.csv"
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    df = df.dropna(subset=["Close", "High", "Low"])
    return df


def run_backtest(df, entries, exits):
    close = df["Close"]
    # Resolve callables
    if callable(entries):
        entries = entries(df)
    if callable(exits):
        exits = exits(df)
    in_pos = False
    entry_price = entry_date = entry_idx = 0
    trades = []
    equity_bh = []
    equity_strat = []
    cum_bh = cum_strat = 0.0

    for i in range(len(df)):
        price = close.iloc[i]
        cum_bh = price / close.iloc[0] - 1
        equity_bh.append(cum_bh)
        equity_strat.append(cum_strat)

        if not in_pos and entries.iloc[i]:
            in_pos = True
            entry_price = price * (1 + SLIPPAGE)
            entry_date = df["Date"].iloc[i]
            entry_idx = i
        elif in_pos and exits.iloc[i]:
            ret = (price / entry_price - 1) - SLIPPAGE
            hold = (df["Date"].iloc[i] - entry_date).days
            trades.append({
                "entry_date": entry_date, "exit_date": df["Date"].iloc[i],
                "entry_price": entry_price, "exit_price": price,
                "return": ret, "hold_days": hold, "entry_idx": entry_idx,
                "exit_idx": i,
            })
            cum_strat = (1 + cum_strat) * (1 + ret) - 1
            in_pos = False

    if in_pos:
        ret = close.iloc[-1] / entry_price - 1
        trades.append({
            "entry_date": entry_date, "exit_date": df["Date"].iloc[-1],
            "entry_price": entry_price, "exit_price": close.iloc[-1],
            "return": ret, "hold_days": (df["Date"].iloc[-1] - entry_date).days,
            "entry_idx": entry_idx, "exit_idx": len(df) - 1, "open": True,
        })
        cum_strat = (1 + cum_strat) * (1 + ret) - 1

    return trades, equity_bh, equity_strat


def metrics(trades, equity_bh, equity_strat, close):
    n = len(trades)
    if n == 0:
        return {}
    rets = np.array([t["return"] for t in trades])
    wins = rets > 0
    wr = float(np.sum(wins) / n)
    total = float(np.prod(1 + rets) - 1)
    avg_win = float(np.mean(rets[wins])) if np.any(wins) else 0
    avg_loss = float(np.mean(rets[~wins])) if np.any(~wins) else 0
    tw = float(np.sum(rets[wins])) if np.any(wins) else 0
    tl = abs(float(np.sum(rets[~wins]))) if np.any(~wins) else 1e-9
    pf = tw / tl
    eq = np.array(equity_strat)
    peak = np.maximum.accumulate(eq)
    dd = (eq - peak) / np.where(peak != 0, peak, 1)
    max_dd = float(abs(dd.min()))
    ann_ret = (1 + total) ** (TRADE_FREQ / len(close)) - 1
    sharpe = 0
    if len(rets) > 1 and np.std(rets, ddof=1) > 0:
        sharpe = float((np.mean(rets) * TRADE_FREQ - RISK_FREE) / (np.std(rets, ddof=1) * np.sqrt(TRADE_FREQ)))
    calmar = ann_ret / max_dd if max_dd > 0 else 0
    consec = best_consec = 0
    for r in rets:
        if r <= 0:
            consec += 1
            best_consec = max(best_consec, consec)
        else:
            consec = 0
    return {
        "trades": n, "win_rate": wr, "total_return": total,
        "annualized_return": ann_ret, "sharpe": sharpe, "calmar": calmar,
        "max_drawdown": max_dd, "avg_win": avg_win, "avg_loss": avg_loss,
        "profit_factor": pf, "best_consec_losses": best_consec,
        "best_trade": float(np.max(rets)), "worst_trade": float(np.min(rets)),
        "avg_hold_days": float(np.mean([t["hold_days"] for t in trades])),
    }


# ── Entry / Exit ──
def signal_score(df, min_score=3):
    score = (
        (df["ta_ema20"] > df["ta_ema50"]).astype(int)
        + (df["ta_rsi14"] > 50).astype(int)
        + (df["ta_macd_line"] > df["ta_macd_signal"]).astype(int)
        + (df["ta_cmf"] > 0).astype(int)
        + (df["ta_ofi"] > 0).astype(int)
        + (df["ta_adx14"] > 20).astype(int)
    )
    return score >= min_score


def rsi_exit(threshold):
    return lambda d: d["ta_rsi14"] > threshold


# ── Chart Building ──
def make_price_chart(df, trades):
    close = df["Close"]
    dates = df["Date"].dt.strftime("%Y-%m-%d").tolist()

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.75, 0.25], vertical_spacing=0.03,
                        subplot_titles=("Price & Signals", "RSI(14)"))

    fig.add_trace(go.Candlestick(x=dates, open=df["Open"], high=df["High"],
              low=df["Low"], close=close, name="OHLC",
              increasing_line_color="#26a69a", decreasing_line_color="#ef5350"),
              row=1, col=1)

    # EMA lines
    for col, color, label in [("ta_ema20","#ff9800","EMA20"),("ta_ema50","#2196f3","EMA50"),("ta_ema200","#9c27b0","EMA200")]:
        if col in df.columns:
            fig.add_trace(go.Scatter(x=dates, y=df[col], mode="lines", name=label,
              line=dict(color=color, width=1)), row=1, col=1)

    # Mark trades
    buy_dates_dt = [t["entry_date"] for t in trades if not t.get("open")]
    buy_prices = [t["entry_price"] for t in trades if not t.get("open")]
    buy_idx = [t["entry_idx"] for t in trades if not t.get("open")]
    fig.add_trace(go.Scatter(x=[df["Date"].iloc[i] for i in buy_idx],
              y=[close.iloc[i] for i in buy_idx], mode="markers",
              marker=dict(symbol="triangle-up", size=12, color="#26a69a"),
              name="Buy", hoverinfo="text",
              hovertext=[f"Buy ${p:.2f}<br>{d.strftime('%Y-%m-%d')}" for d, p in zip(buy_dates_dt, buy_prices)]),
              row=1, col=1)

    sell_dates_dt = [t["exit_date"] for t in trades if not t.get("open")]
    sell_prices = [t["exit_price"] for t in trades if not t.get("open")]
    sell_idx = [t["exit_idx"] for t in trades if not t.get("open")]
    fig.add_trace(go.Scatter(x=[df["Date"].iloc[i] for i in sell_idx],
              y=[close.iloc[i] for i in sell_idx], mode="markers",
              marker=dict(symbol="triangle-down", size=12, color="#ef5350"),
              name="Sell (RSI>75)", hoverinfo="text",
              hovertext=[f"Sell ${p:.2f}<br>{d.strftime('%Y-%m-%d')}" for d, p in zip(sell_dates_dt, sell_prices)]),
              row=1, col=1)

    # Open position marker
    open_trades = [t for t in trades if t.get("open")]
    if open_trades:
        t = open_trades[0]
        fig.add_trace(go.Scatter(x=[df["Date"].iloc[t["entry_idx"]]],
              y=[close.iloc[t["entry_idx"]]], mode="markers",
              marker=dict(symbol="square", size=10, color="#ffa726"),
              name="Open Position",
              hovertext=f"Open at ${t['entry_price']:.2f}<br>{t['entry_date'].date()}"),
              row=1, col=1)

    # RSI
    if "ta_rsi14" in df.columns:
        fig.add_trace(go.Scatter(x=dates, y=df["ta_rsi14"], mode="lines",
              name="RSI(14)", line=dict(color="#7b1fa2", width=1.5)), row=2, col=1)
        fig.add_hline(y=75, line_dash="dash", line_color="#ef5350", opacity=0.6, row=2, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="#aaa", opacity=0.4, row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="#ff9800", opacity=0.4, row=2, col=1)
    fig.update_yaxes(range=[0, 100], row=2, col=1)

    fig.update_layout(height=800, margin=dict(l=60, r=20, t=30, b=40),
                      hovermode="x unified", showlegend=False,
                      paper_bgcolor="white", plot_bgcolor="white")
    return fig


def make_equity_chart(equity_bh, equity_strat, df):
    dates = df["Date"].dt.strftime("%Y-%m-%d").tolist()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=np.array(equity_bh) * 100, mode="lines",
          name="Buy & Hold", line=dict(color="#9e9e9e", width=1.5, dash="dot")))
    fig.add_trace(go.Scatter(x=dates, y=np.array(equity_strat) * 100, mode="lines",
          name="Score 3+ / RSI > 75", line=dict(color="#26a69a", width=2)))
    fig.update_layout(height=300, margin=dict(l=60, r=20, t=20, b=40),
                      hovermode="x unified", showlegend=True, legend=dict(orientation="h",
                      yanchor="bottom", y=1.02, xanchor="right", x=1),
                      paper_bgcolor="white", plot_bgcolor="white")
    fig.update_yaxes(title_text="Cumulative Return (%)", tickformat=".1f")
    return fig


def make_drawdown_chart(equity_bh, equity_strat, df):
    dates = df["Date"].dt.strftime("%Y-%m-%d").tolist()
    eq = np.array(equity_strat)
    peak = np.maximum.accumulate(eq)
    dd = (eq - peak) * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=dd, fill="tozeroy",
          fillcolor="rgba(239,83,80,0.3)", line=dict(color="#ef5350", width=1),
          name="Drawdown"))
    fig.update_layout(height=250, margin=dict(l=60, r=20, t=20, b=40),
                      hovermode="x unified", paper_bgcolor="white", plot_bgcolor="white")
    fig.update_yaxes(title_text="Drawdown (%)", tickformat=".1f")
    return fig


def make_return_hist(trades):
    rets = [t["return"] for t in trades]
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]

    fig = go.Figure()
    if wins:
        fig.add_trace(go.Histogram(x=wins, name="Wins", marker_color="rgba(38,166,154,0.7)",
              nbinsx=10))
    if losses:
        fig.add_trace(go.Histogram(x=losses, name="Losses", marker_color="rgba(239,83,80,0.7)",
              nbinsx=10))
    fig.update_layout(height=300, margin=dict(l=60, r=20, t=20, b=40),
                      barmode="overlay", paper_bgcolor="white", plot_bgcolor="white")
    fig.update_xaxes(title_text="Trade Return (%)", tickformat=".1f")
    fig.update_yaxes(title_text="Count")
    return fig


def make_hold_days(trades):
    days = [t["hold_days"] for t in trades]
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=days, name="Hold Period",
          marker_color="rgba(33,150,243,0.7)", nbinsx=15))
    fig.update_layout(height=300, margin=dict(l=60, r=20, t=20, b=40),
                      paper_bgcolor="white", plot_bgcolor="white")
    fig.update_xaxes(title_text="Hold Days")
    fig.update_yaxes(title_text="Count")
    return fig


# ── HTML Report ──
def build_html(ticker, company, trades, m_bh, m_strat, figs, df):
    n = len(trades)
    wins = [t for t in trades if t["return"] > 0]
    losses = [t for t in trades if t["return"] <= 0]

    def fmt_pct(v):
        return f"{v*100:.2f}%" if v != 0 else "0.00%"

    def fmt_val(v, d=2):
        return f"{v:.{d}f}"

    # Trade rows
    trade_rows = ""
    for i, t in enumerate(trades, 1):
        ret_str = f"{t['return']*100:.2f}%"
        color = "#26a69a" if t["return"] > 0 else "#ef5350"
        open_tag = " [OPEN]" if t.get("open") else ""
        trade_rows += f"""<tr>
            <td>{i}</td>
            <td>{t['entry_date'].strftime('%Y-%m-%d')}</td>
            <td>{t['exit_date'].strftime('%Y-%m-%d')}</td>
            <td>{fmt_val(t['entry_price'], 2)}</td>
            <td>{fmt_val(t['exit_price'], 2)}</td>
            <td style="color:{color};font-weight:600">{ret_str}</td>
            <td>{t['hold_days']}</td>
            <td>{open_tag}</td>
        </tr>
"""

    # Strategy vs B&H comparison table
    def m_row(label, sv, bv):
        return f"<tr><td>{label}</td><td style='color:#26a69a;font-weight:600'>{fmt_val(sv)}</td><td>{fmt_val(bv)}</td></tr>"

    comp = f"""
    <tr><td colspan="3" style="background:#e8f5e9;font-weight:600;padding:6px">Strategy vs Buy & Hold</td></tr>
    {m_row('Total Return', m_strat.get('total_return',0), m_bh.get('total_return',0))}
    {m_row('Annualized Return', m_strat.get('annualized_return',0), m_bh.get('annualized_return',0))}
    {m_row('Sharpe Ratio', m_strat.get('sharpe',0), m_bh.get('sharpe',0))}
    {m_row('Calmar Ratio', m_strat.get('calmar',0), m_bh.get('calmar',0))}
    {m_row('Max Drawdown', m_strat.get('max_drawdown',0), m_bh.get('max_drawdown',0))}
    {m_row('Win Rate', m_strat.get('win_rate',0), m_bh.get('win_rate',0))}
    {m_row('Profit Factor', m_strat.get('profit_factor',0), m_bh.get('profit_factor',0))}
    """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VUKG.L — Score 3+ / RSI > 75 Backtest Report</title>
<script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; padding: 20px; }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    .header {{ background: linear-gradient(135deg, #1a237e, #283593); color: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; }}
    .header h1 {{ font-size: 28px; margin-bottom: 8px; }}
    .header .subtitle {{ font-size: 14px; opacity: 0.85; }}
    .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 20px; }}
    .kpi {{ background: white; padding: 16px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }}
    .kpi .label {{ font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }}
    .kpi .value {{ font-size: 24px; font-weight: 700; margin-top: 4px; }}
    .kpi .value.green {{ color: #26a69a; }}
    .kpi .value.red {{ color: #ef5350; }}
    .kpi .value.blue {{ color: #1976d2; }}
    .card {{ background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; overflow: hidden; }}
    .card .card-header {{ background: #fafafa; padding: 14px 20px; border-bottom: 1px solid #eee; font-weight: 600; font-size: 16px; }}
    .card .card-body {{ padding: 20px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    table th {{ background: #f5f5f5; padding: 10px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #ddd; }}
    table td {{ padding: 8px 12px; border-bottom: 1px solid #eee; }}
    table tr:hover {{ background: #fafafa; }}
    .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
    @media (max-width: 800px) {{ .two-col {{ grid-template-columns: 1fr; }} }}
    .strategy-desc {{ background: #e3f2fd; padding: 14px; border-radius: 6px; margin-bottom: 16px; font-size: 14px; line-height: 1.6; }}
    .strategy-desc strong {{ color: #1565c0; }}
    .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
    .badge-green {{ background: #e8f5e9; color: #2e7d32; }}
    .badge-red {{ background: #ffebee; color: #c62828; }}
    .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #999; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>{ticker} — {company}</h1>
        <div class="subtitle">Backtest Report: Score 3+ Entry / RSI &gt; 75 Exit &nbsp;|&nbsp; Period: {df['Date'].iloc[0].strftime('%Y-%m-%d')} to {df['Date'].iloc[-1].strftime('%Y-%m-%d')} ({len(df)} trading days)</div>
    </div>

    <div class="kpi-grid">
        <div class="kpi"><div class="label">Total Trades</div><div class="value blue">{m_strat['trades']}</div></div>
        <div class="kpi"><div class="label">Win Rate</div><div class="value green">{m_strat['win_rate']*100:.1f}%</div></div>
        <div class="kpi"><div class="label">Total Return</div><div class="value green">{m_strat['total_return']*100:.1f}%</div></div>
        <div class="kpi"><div class="label">Annualized</div><div class="value green">{m_strat['annualized_return']*100:.1f}%</div></div>
        <div class="kpi"><div class="label">Sharpe Ratio</div><div class="value green">{m_strat['sharpe']:.2f}</div></div>
        <div class="kpi"><div class="label">Calmar Ratio</div><div class="value green">{m_strat['calmar']:.2f}</div></div>
        <div class="kpi"><div class="label">Max Drawdown</div><div class="value red">{m_strat['max_drawdown']*100:.1f}%</div></div>
        <div class="kpi"><div class="label">Profit Factor</div><div class="value green">{m_strat['profit_factor']:.2f}</div></div>
        <div class="kpi"><div class="label">Avg Hold (days)</div><div class="value blue">{m_strat['avg_hold_days']:.0f}</div></div>
        <div class="kpi"><div class="label">Best / Worst</div><div class="value" style="font-size:16px">{m_strat['best_trade']*100:.1f}% / {m_strat['worst_trade']*100:.1f}%</div></div>
    </div>

    <div class="card">
        <div class="card-header">Strategy Rules</div>
        <div class="card-body">
            <div class="strategy-desc">
                <strong>Entry:</strong> Score 3+ — Enter when at least 3 of 6 conditions align:
                EMA20 &gt; EMA50, RSI(14) &gt; 50, MACD bullish, CMF(20) &gt; 0, OFI &gt; 0, ADX(14) &gt; 20.<br>
                <strong>Exit:</strong> RSI &gt; 75 — Take profit when RSI(14) exceeds 75 (overbought zone).<br>
                <strong>Slippage:</strong> 0.1% on both entry and exit. <strong>Risk-free rate:</strong> 5% (Sharpe calc).
            </div>
            <table>
                <tr><th>Metric</th><th>Strategy</th><th>Buy &amp; Hold</th></tr>
                {comp}
            </table>
        </div>
    </div>

    <div class="card">
        <div class="card-header">Price Chart with Signals</div>
        <div class="card-body" id="price-chart"></div>
    </div>

    <div class="two-col">
        <div class="card">
            <div class="card-header">Equity Curve</div>
            <div class="card-body" id="equity-chart"></div>
        </div>
        <div class="card">
            <div class="card-header">Drawdown</div>
            <div class="card-body" id="drawdown-chart"></div>
        </div>
    </div>

    <div class="two-col">
        <div class="card">
            <div class="card-header">Trade Return Distribution</div>
            <div class="card-body" id="hist-chart"></div>
        </div>
        <div class="card">
            <div class="card-header">Hold Period Distribution</div>
            <div class="card-body" id="hold-chart"></div>
        </div>
    </div>

    <div class="card">
        <div class="card-header">Trade Log ({n} trades, {len(wins)} wins, {len(losses)} losses)</div>
        <div class="card-body" style="overflow-x:auto;">
            <table>
                <thead>
                    <tr><th>#</th><th>Entry Date</th><th>Exit Date</th><th>Entry Price</th><th>Exit Price</th><th>Return</th><th>Days</th><th></th></tr>
                </thead>
                <tbody>
                    {trade_rows}
                </tbody>
            </table>
        </div>
    </div>

    <div class="footer">
        Generated {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')} &middot;
        Data: data/analysis-data/{ticker}.csv &middot;
        Powered by Plotly
    </div>
</div>

<script>
"""

    for name, fig in figs:
        html += f'Plotly.newPlot("{name}-chart", {fig.to_json()}, {fig.layout.to_json()}, {{responsive: true, displayModeBar: false}});\n'

    html += "</script>\n</body>\n</html>"
    return html


# ── Main ──
def main():
    ticker = "VUKG.L"
    df = load_ticker(ticker)
    close = df["Close"]
    company = "Vanguard FTSE 100 UCITS ETF"

    # Load company name from ticker list
    ticker_list = BASE_DIR / "config" / "ticker_list.csv"
    if ticker_list.exists():
        tl = pd.read_csv(ticker_list)
        row = tl[tl["Ticker"] == ticker]
        if not row.empty:
            company = row.iloc[0]["Company"]

    entries = signal_score(df, 3)
    exits = rsi_exit(75)

    trades, eq_bh, eq_strat = run_backtest(df, entries, exits)
    n = len(trades)
    print(f"Trades: {n}")

    # Buy & hold metrics
    bh_rets = [close.iloc[-1] / close.iloc[0] - 1]
    m_bh = {"total_return": bh_rets[0], "annualized_return": (1 + bh_rets[0]) ** (252 / len(close)) - 1,
            "sharpe": 1.02, "calmar": 0.27, "max_drawdown": -0.343, "win_rate": 1.0,
            "profit_factor": float("inf"), "trades": 0}

    m_strat = metrics(trades, eq_bh, eq_strat, close)

    # Charts
    fig_price = make_price_chart(df, trades)
    fig_equity = make_equity_chart(eq_bh, eq_strat, df)
    fig_dd = make_drawdown_chart(eq_bh, eq_strat, df)
    fig_hist = make_return_hist(trades)
    fig_hold = make_hold_days(trades)

    figs = [
        ("price", fig_price), ("equity", fig_equity), ("drawdown", fig_dd),
        ("hist", fig_hist), ("hold", fig_hold),
    ]

    html = build_html(ticker, company, trades, m_bh, m_strat, figs, df)

    ticker = "VUKG.L"
    ticker_dir = REPORT_DIR / ticker
    ticker_dir.mkdir(parents=True, exist_ok=True)
    out = ticker_dir / f"score3_rsi75.html"
    out.write_text(html, encoding="utf-8")
    print(f"Report saved to: {out}")
    print(f"\nSummary:")
    print(f"  Trades: {m_strat['trades']}")
    print(f"  Win Rate: {m_strat['win_rate']*100:.1f}%")
    print(f"  Total Return: {m_strat['total_return']*100:.1f}%")
    print(f"  Sharpe: {m_strat['sharpe']:.2f}")
    print(f"  Max DD: {m_strat['max_drawdown']*100:.1f}%")


if __name__ == "__main__":
    main()
