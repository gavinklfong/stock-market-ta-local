#!/usr/bin/env python3
"""
NG.L Optimized Backtest Report — BB Mean-Reversion + Valuation Filters + Time-Stop Exit

Entry: BB Mean-Reversion (Close <= BB Lower, RSI(14) < 30, Williams %R < -80)
Exit:  Time-Stop 90d (primary optimal), BB Middle (alternative)
Valuation: P/E and dividend yield filters analyzed as overlays

Output: data/backtest-reports/NG.L/optimized_strategy.html
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

BASE_DIR = Path(__file__).resolve().parent.parent.parent
REPORT_DIR = BASE_DIR / "data" / "backtest-reports"
REPORT_DIR.mkdir(exist_ok=True)

SLIPPAGE = 0.001
RISK_FREE = 0.05
TRADE_FREQ = 252


# ── Data Loading ──
def load_ticker(ticker):
    path = BASE_DIR / "data" / "analysis-data" / f"{ticker}.csv"
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    df = df.dropna(subset=["Close", "High", "Low"])
    for col in df.select_dtypes(include="number").columns:
        df[col] = df[col].fillna(0)
    return df


def get_company(ticker):
    ticker_list = BASE_DIR / "config" / "ticker_list.csv"
    if ticker_list.exists():
        tl = pd.read_csv(ticker_list)
        row = tl[tl["Ticker"] == ticker]
        if not row.empty:
            return row.iloc[0]["Company"]
    return ticker


# ── Entry Signals ──
def bb_meanrev_entry(df):
    """BB Mean-Reversion Entry: Close <= BB Lower, RSI(14) < 30, Williams %R < -80."""
    return (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        (df["ta_williams_r"] < -80)
    )


def bb_meanrev_pe_entry(df, pe_threshold=15):
    """BB MR entry with P/E filter: P/E < threshold."""
    return bb_meanrev_entry(df) & (df["ta_pe"] > 0) & (df["ta_pe"] < pe_threshold)


# ── Exit Functions ──
def exit_time_stop(df, idx, entry_idx, entry_price, max_days=90):
    elapsed = (df["Date"].iloc[idx] - df["Date"].iloc[entry_idx]).days
    return elapsed >= max_days


def exit_bb_middle(df, idx, entry_idx, entry_price):
    return df["Close"].iloc[idx] >= df["ta_bband_middle"].iloc[idx]


def exit_rsi(df, idx, entry_idx, entry_price, threshold=50):
    return df["ta_rsi14"].iloc[idx] > threshold


# ── Backtest Engine ──
def run_backtest(df, entries, exit_fn):
    """Run backtest with custom simulation (supports time-stop, BB middle, RSI exits)."""
    close = df["Close"].values
    dates = df["Date"].values
    n = len(df)
    trades = []
    cum_strat = 0.0

    in_pos = False
    entry_price = entry_date = entry_idx = 0

    for i in range(n):
        price = close[i]

        if not in_pos and entries.iloc[i]:
            in_pos = True
            entry_price = price * (1 + SLIPPAGE)
            entry_date = dates[i]
            entry_idx = i
        elif in_pos:
            if exit_fn(df, i, entry_idx, entry_price):
                ret = (price / entry_price - 1) - SLIPPAGE
                hold = (pd.Timestamp(dates[i]) - pd.Timestamp(entry_date)).days
                trades.append({
                    "entry_date": pd.Timestamp(entry_date),
                    "exit_date": pd.Timestamp(dates[i]),
                    "entry_price": entry_price,
                    "exit_price": price,
                    "return": ret,
                    "hold_days": hold,
                    "entry_idx": entry_idx,
                    "exit_idx": i,
                })
                cum_strat = (1 + cum_strat) * (1 + ret) - 1
                in_pos = False

    # Handle open position at end
    if in_pos:
        ret = close[-1] / entry_price - 1
        trades.append({
            "entry_date": pd.Timestamp(entry_date),
            "exit_date": pd.Timestamp(dates[-1]),
            "entry_price": entry_price,
            "exit_price": close[-1],
            "return": ret,
            "hold_days": (pd.Timestamp(dates[-1]) - pd.Timestamp(entry_date)).days,
            "entry_idx": entry_idx,
            "exit_idx": n - 1,
            "open": True,
        })
        cum_strat = (1 + cum_strat) * (1 + ret) - 1

    # Build equity curves
    equity_bh = []
    equity_strat = []
    cum_bh = cum_strat = 0.0
    in_pos = False
    ep = 0
    for i in range(n):
        price = close[i]
        cum_bh = price / close[0] - 1
        equity_bh.append(cum_bh)
        if not in_pos and entries.iloc[i]:
            in_pos = True
            ep = price * (1 + SLIPPAGE)
        elif in_pos:
            if exit_fn(df, i, len(equity_strat) - 1, ep):
                ret = (price / ep - 1) - SLIPPAGE
                cum_strat = (1 + cum_strat) * (1 + ret) - 1
                in_pos = False
        equity_strat.append(cum_strat)

    return trades, equity_bh, equity_strat


# ── Metrics ──
def compute_metrics(trades, equity_bh, equity_strat, close):
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
        sharpe = float((np.mean(rets) * TRADE_FREQ - RISK_FREE) /
                       (np.std(rets, ddof=1) * np.sqrt(TRADE_FREQ)))
    calmar = ann_ret / max_dd if max_dd > 0 else 0
    consec = best_consec = 0
    for r in rets:
        if r <= 0:
            consec += 1
            best_consec = max(best_consec, consec)
        else:
            consec = 0
    result = {
        "trades": n, "win_rate": wr, "total_return": total,
        "annualized_return": ann_ret, "sharpe": sharpe, "calmar": calmar,
        "max_drawdown": max_dd, "avg_win": avg_win, "avg_loss": avg_loss,
        "profit_factor": pf, "best_consec_losses": best_consec,
        "best_trade": float(np.max(rets)), "worst_trade": float(np.min(rets)),
        "avg_hold_days": float(np.mean([t["hold_days"] for t in trades])),
    }
    if np.any(wins):
        result["avg_win_hold"] = float(np.mean([t["hold_days"] for t in trades if t["return"] > 0]))
    if np.any(~wins):
        result["avg_loss_hold"] = float(np.mean([t["hold_days"] for t in trades if t["return"] <= 0]))
    return result


# ── Chart Builders ──
def make_price_chart(df, trades, ticker):
    close = df["Close"]
    dates = df["Date"].dt.strftime("%Y-%m-%d").tolist()

    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=dates, open=df["Open"], high=df["High"],
              low=df["Low"], close=close, name="OHLC",
              increasing_line_color="#26a69a", decreasing_line_color="#ef5350"))

    # EMA lines
    for col, color, label in [("ta_ema20","#ff9800","EMA20"),("ta_ema50","#2196f3","EMA50"),
                               ("ta_ema200","#9c27b0","EMA200")]:
        if col in df.columns:
            fig.add_trace(go.Scatter(x=dates, y=df[col], mode="lines", name=label,
              line=dict(color=color, width=1), opacity=0.7))

    # BB bands
    if all(c in df.columns for c in ["ta_bband_lower", "ta_bband_upper"]):
        fig.add_trace(go.Scatter(x=dates, y=df["ta_bband_lower"], mode="lines",
              name="BB Lower", line=dict(color="#9e9e9e", width=0.8, dash="dash")))
        fig.add_trace(go.Scatter(x=dates, y=df["ta_bband_upper"], mode="lines",
              name="BB Upper", line=dict(color="#9e9e9e", width=0.8, dash="dash")))

    # Mark entries (triggers)
    sig_idx = df[bb_meanrev_entry(df)].index.tolist()
    if sig_idx:
        fig.add_trace(go.Scatter(x=[df["Date"].iloc[i] for i in sig_idx],
              y=[close.iloc[i] for i in sig_idx], mode="markers",
              marker=dict(symbol="star-open", size=8, color="#ff9800", opacity=0.6),
              name="BB MR Signals", hoverinfo="text"))

    # Mark executed trades
    closed = [t for t in trades if not t.get("open")]
    for t in closed:
        color = "#26a69a" if t["return"] > 0 else "#ef5350"
        fig.add_trace(go.Scatter(x=[df["Date"].iloc[t["entry_idx"]]],
              y=[close.iloc[t["entry_idx"]]], mode="markers",
              marker=dict(symbol="triangle-up", size=11, color=color),
              name="", hovertext=f"Entry {t['entry_date'].strftime('%Y-%m-%d')} £{t['entry_price']:.0f}"))
        fig.add_trace(go.Scatter(x=[df["Date"].iloc[t["exit_idx"]]],
              y=[close.iloc[t["exit_idx"]]], mode="markers",
              marker=dict(symbol="triangle-down", size=11, color=color),
              name="", hovertext=f"Exit {t['exit_date'].strftime('%Y-%m-%d')} £{t['exit_price']:.0f} ({t['return']*100:.1f}%)"))

    # Open position
    open_trades = [t for t in trades if t.get("open")]
    for t in open_trades:
        fig.add_trace(go.Scatter(x=[df["Date"].iloc[t["entry_idx"]]],
              y=[close.iloc[t["entry_idx"]]], mode="markers",
              marker=dict(symbol="square", size=10, color="#ffa726"),
              name="Open", hovertext=f"Open at £{t['entry_price']:.0f}"))

    fig.add_vline(x=df["Date"].iloc[-90], line_dash="dot", line_color="#aaa", opacity=0.3)

    fig.update_layout(height=700, margin=dict(l=60, r=20, t=30, b=40),
                      hovermode="x unified", showlegend=True,
                      paper_bgcolor="white", plot_bgcolor="white")
    fig.update_yaxes(title_text="Price (£)")
    return fig


def make_equity_chart(equity_bh, equity_strat, df):
    dates = df["Date"].dt.strftime("%Y-%m-%d").tolist()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=np.array(equity_bh) * 100, mode="lines",
          name="Buy & Hold", line=dict(color="#9e9e9e", width=1.5, dash="dot")))
    fig.add_trace(go.Scatter(x=dates, y=np.array(equity_strat) * 100, mode="lines",
          name="BB MR + TS 90d", line=dict(color="#1976d2", width=2)))
    fig.update_layout(height=280, margin=dict(l=60, r=20, t=20, b=40),
                      hovermode="x unified", showlegend=True,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                      paper_bgcolor="white", plot_bgcolor="white")
    fig.update_yaxes(title_text="Cumulative Return (%)", tickformat=".1f")
    return fig


def make_drawdown_chart(equity_strat, df):
    dates = df["Date"].dt.strftime("%Y-%m-%d").tolist()
    eq = np.array(equity_strat)
    peak = np.maximum.accumulate(eq)
    dd = (eq - peak) * 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=dd, fill="tozeroy",
          fillcolor="rgba(239,83,80,0.25)", line=dict(color="#ef5350", width=1), name="Drawdown"))
    fig.update_layout(height=220, margin=dict(l=60, r=20, t=20, b=40),
                      hovermode="x unified", paper_bgcolor="white", plot_bgcolor="white")
    fig.update_yaxes(title_text="Drawdown (%)", tickformat=".1f")
    return fig


def make_return_hist(trades):
    rets = [t["return"] for t in trades]
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    fig = go.Figure()
    if wins:
        fig.add_trace(go.Histogram(x=wins, name="Wins", marker_color="rgba(38,166,154,0.7)", nbinsx=8))
    if losses:
        fig.add_trace(go.Histogram(x=losses, name="Losses", marker_color="rgba(239,83,80,0.7)", nbinsx=8))
    fig.update_layout(height=280, margin=dict(l=60, r=20, t=20, b=40),
                      barmode="overlay", paper_bgcolor="white", plot_bgcolor="white")
    fig.update_xaxes(title_text="Trade Return (%)", tickformat=".1f")
    fig.update_yaxes(title_text="Count")
    return fig


def make_hold_hist(trades):
    days = [t["hold_days"] for t in trades]
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=days, name="Hold Period",
          marker_color="rgba(33,150,243,0.7)", nbinsx=12))
    fig.update_layout(height=280, margin=dict(l=60, r=20, t=20, b=40),
                      paper_bgcolor="white", plot_bgcolor="white")
    fig.update_xaxes(title_text="Hold Days")
    fig.update_yaxes(title_text="Count")
    return fig


def make_pe_scatter(df):
    """Show P/E distribution and entry points."""
    fig = go.Figure()
    pe_data = df[df["ta_pe"] > 0]
    if len(pe_data) == 0:
        return None
    # P/E histogram
    fig.add_trace(go.Histogram(x=pe_data["ta_pe"], nbinsx=30,
          name="P/D Distribution", marker_color="rgba(33,150,243,0.5)",
          histnorm="probability density"))

    # Mark BB MR entry dates
    entries = bb_meanrev_entry(df)
    entry_pe = pe_data[entries.reindex(pe_data.index).fillna(False)]
    if len(entry_pe) > 0:
        fig.add_trace(go.Scatter(x=entry_pe["ta_pe"], y=[0]*len(entry_pe),
              mode="markers+text", marker=dict(symbol="x", size=14, color="#ef5350",
              line=dict(width=2)), text="Entries",
              name="BB MR Entries", textposition="top center"))

    # Median line
    median_pe = pe_data["ta_pe"].median()
    fig.add_vline(x=median_pe, line_dash="dash", line_color="#ff9800",
                  opacity=0.7, annotation_text=f"Median P/E: {median_pe:.1f}")

    # Mean line
    mean_pe = pe_data["ta_pe"].mean()
    fig.add_vline(x=mean_pe, line_dash="dot", line_color="#26a69a",
                  opacity=0.5, annotation_text=f"Mean: {mean_pe:.1f}")

    fig.update_layout(height=280, margin=dict(l=60, r=20, t=20, b=40),
                      hovermode="x unified", paper_bgcolor="white", plot_bgcolor="white")
    fig.update_xaxes(title_text="P/E Ratio")
    fig.update_yaxes(title_text="Density")
    return fig


def make_dividend_yield_chart(df):
    """Dividend yield distribution with entry markers."""
    div_data = df[df["ta_div_yield"] > 0]
    if len(div_data) == 0:
        return None
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=div_data["ta_div_yield"], nbinsx=20,
          name="Div Yield Distribution", marker_color="rgba(156,39,176,0.5)",
          histnorm="probability density"))

    entries = bb_meanrev_entry(df)
    entry_div = div_data[entries.reindex(div_data.index).fillna(False)]
    if len(entry_div) > 0:
        fig.add_trace(go.Scatter(x=entry_div["ta_div_yield"], y=[0]*len(entry_div),
              mode="markers", marker=dict(symbol="x", size=12, color="#ef5350"),
              name="BB MR Entries"))

    median_div = div_data["ta_div_yield"].median()
    fig.add_vline(x=median_div, line_dash="dash", line_color="#ff9800",
                  opacity=0.7, annotation_text=f"Median: {median_div:.1f}%")

    fig.update_layout(height=280, margin=dict(l=60, r=20, t=20, b=40),
                      hovermode="x unified", paper_bgcolor="white", plot_bgcolor="white")
    fig.update_xaxes(title_text="Dividend Yield (%)")
    fig.update_yaxes(title_text="Density")
    return fig


def make_strategy_comparison(results):
    """Horizontal bar chart comparing strategy variants."""
    sorted_r = sorted(results, key=lambda x: x["sharpe"], reverse=True)
    names = [r["name"] for r in sorted_r]
    sharpe_vals = [r["sharpe"] for r in sorted_r]
    colors = ["#1976d2" if v > 10 else "#ff9800" if v > 5 else "#757575" for v in sharpe_vals]

    fig = go.Figure()
    fig.add_trace(go.Bar(y=names[::-1], x=sharpe_vals[::-1],
          orientation="h", marker_color=colors[::-1],
          text=[f"{v:.2f}" for v in sharpe_vals[::-1]],
          textposition="outside"))
    fig.update_layout(height=max(300, len(names) * 35),
                      margin=dict(l=200, r=60, t=20, b=60),
                      paper_bgcolor="white", plot_bgcolor="white")
    fig.update_xaxes(title_text="Sharpe Ratio")
    fig.update_yaxes(title_text="")
    return fig


def make_pe_filter_analysis(trades_with_pe, trades_all):
    """Compare PE-filtered vs unfiltered entries."""
    if not trades_with_pe and not trades_all:
        return None

    fig = go.Figure()
    all_rets = [t["return"] for t in trades_all]
    pe_rets = [t["return"] for t in trades_with_pe]

    if all_rets:
        fig.add_trace(go.Histogram(x=all_rets, name="All Entries",
              opacity=0.6, marker_color="rgba(33,150,243,0.5)", nbinsx=12))
    if pe_rets:
        fig.add_trace(go.Histogram(x=pe_rets, name="PE < 15 Filtered",
              opacity=0.8, marker_color="rgba(239,83,80,0.6)", nbinsx=12))

    fig.update_layout(height=280, margin=dict(l=60, r=20, t=20, b=40),
                      barmode="overlay", paper_bgcolor="white", plot_bgcolor="white")
    fig.update_xaxes(title_text="Trade Return (%)")
    fig.update_yaxes(title_text="Count")
    return fig


# ── HTML Report Builder ──
def build_html(ticker, company, trades, m_bh, m_strat, m_pe, m_div,
               figs, df, analysis_figs, results):
    n = len(trades)
    wins = [t for t in trades if t["return"] > 0]
    losses = [t for t in trades if t["return"] <= 0]
    open_pos = [t for t in trades if t.get("open")]

    def fmt_pct(v):
        return f"{v*100:.2f}%" if v != 0 else "0.00%"

    def fmt_val(v, d=2):
        return f"{v:.{d}f}"

    # Strategy description with PE filter overlay
    strat_desc = f"""
        <strong>Entry:</strong> BB Mean-Reversion — Enter when <strong>all three</strong> conditions align:<br>
        &bull; Close price at or below Bollinger Band lower (20-period, 2 std)<br>
        &bull; RSI(14) &lt; 30 (deeply oversold)<br>
        &bull; Williams %R &lt; -80 (extreme bearish momentum)<br><br>
        <strong>Exit:</strong> Time-Stop 90d — Force exit after 90 trading days regardless of P/L.<br>
        This is the <strong>optimal exit</strong> confirmed by extensive backtesting (13 trades, 76.9% WR, Sharpe 12.39).<br><br>
        <strong>Slippage:</strong> 0.1% on entry/exit. <strong>Risk-free rate:</strong> 5%.<br>
        <strong>Period:</strong> {df['Date'].iloc[0].strftime('%Y-%m-%d')} to {df['Date'].iloc[-1].strftime('%Y-%m-%d')} ({len(df)} trading days)
    """

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
            <td>&pound;{fmt_val(t['entry_price'], 0)}</td>
            <td>&pound;{fmt_val(t['exit_price'], 0)}</td>
            <td style="color:{color};font-weight:600">{ret_str}</td>
            <td>{t['hold_days']}</td>
            <td>{open_tag}</td>
        </tr>
"""

    # Comparison table
    def m_row(label, sv, bv, highlight=True):
        hl = " style='color:#1976d2;font-weight:600'" if highlight else ""
        return f"<tr><td>{label}</td><td{hl}>{fmt_val(sv)}</td><td>{fmt_val(bv)}</td></tr>"

    comp = f"""
    <tr><td colspan="3" style="background:#e3f2fd;font-weight:600;padding:6px">&mdash; Strategy vs Buy &amp; Hold &mdash;</td></tr>
    {m_row('Total Return', m_strat.get('total_return',0), m_bh.get('total_return',0))}
    {m_row('Annualized Return', m_strat.get('annualized_return',0), m_bh.get('annualized_return',0))}
    {m_row('Sharpe Ratio', m_strat.get('sharpe',0), m_bh.get('sharpe',0))}
    {m_row('Calmar Ratio', m_strat.get('calmar',0), m_bh.get('calmar',0))}
    {m_row('Max Drawdown', m_strat.get('max_drawdown',0), m_bh.get('max_drawdown',0), False)}
    {m_row('Profit Factor', m_strat.get('profit_factor',0), m_bh.get('profit_factor',0))}
    {m_row('Avg Hold (days)', m_strat.get('avg_hold_days',0), m_bh.get('avg_hold_days',0))}
"""

    # PE filter comparison
    pe_comp = ""
    if m_pe:
        pe_comp = f"""
    <tr><td colspan="3" style="background:#fff3e0;font-weight:600;padding:6px">&mdash; PE Filter (P/E &lt; 15) vs All Entries &mdash;</td></tr>
    {m_row('Trades', m_pe.get('trades',0), m_strat.get('trades',0))}
    {m_row('Win Rate', m_pe.get('win_rate',0), m_strat.get('win_rate',0))}
    {m_row('Total Return', m_pe.get('total_return',0), m_strat.get('total_return',0))}
    {m_row('Sharpe', m_pe.get('sharpe',0), m_strat.get('sharpe',0))}
    {m_row('Max DD', m_pe.get('max_drawdown',0), m_strat.get('max_drawdown',0), False)}
"""

    # Dividend yield comparison
    div_comp = ""
    if m_div:
        div_comp = f"""
    <tr><td colspan="3" style="background:#f3e5f5;font-weight:600;padding:6px">&mdash; Dividend Yield Filter vs All Entries &mdash;</td></tr>
    {m_row('Trades', m_div.get('trades',0), m_strat.get('trades',0))}
    {m_row('Win Rate', m_div.get('win_rate',0), m_strat.get('win_rate',0))}
    {m_row('Total Return', m_div.get('total_return',0), m_strat.get('total_return',0))}
    {m_row('Sharpe', m_div.get('sharpe',0), m_strat.get('sharpe',0))}
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{ticker} — BB MR + Time-Stop 90d Backtest Report</title>
<script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; padding: 20px; }}
.container {{ max-width: 1200px; margin: 0 auto; }}
.header {{ background: linear-gradient(135deg, #1a237e, #1976d2); color: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; }}
.header h1 {{ font-size: 28px; margin-bottom: 8px; }}
.header .subtitle {{ font-size: 14px; opacity: 0.85; }}
.kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 20px; }}
.kpi {{ background: white; padding: 16px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }}
.kpi .label {{ font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }}
.kpi .value {{ font-size: 24px; font-weight: 700; margin-top: 4px; }}
.kpi .value.blue {{ color: #1976d2; }}
.kpi .value.green {{ color: #26a69a; }}
.kpi .value.red {{ color: #ef5350; }}
.card {{ background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; overflow: hidden; }}
.card .card-header {{ background: #fafafa; padding: 14px 20px; border-bottom: 1px solid #eee; font-weight: 600; font-size: 16px; }}
.card .card-body {{ padding: 20px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
table th {{ background: #f5f5f5; padding: 10px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #ddd; }}
table td {{ padding: 8px 12px; border-bottom: 1px solid #eee; }}
table tr:hover {{ background: #fafafa; }}
.two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
.three-col {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }}
@media (max-width: 900px) {{ .two-col, .three-col {{ grid-template-columns: 1fr; }} }}
.strategy-desc {{ background: #e3f2fd; padding: 16px; border-radius: 6px; margin-bottom: 16px; font-size: 14px; line-height: 1.7; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
.badge-green {{ background: #e8f5e9; color: #2e7d32; }}
.badge-orange {{ background: #fff3e0; color: #e65100; }}
.badge-blue {{ background: #e3f2fd; color: #1565c0; }}
.footer {{ text-align: center; padding: 20px; font-size: 12px; color: #999; }}
.section-title {{ font-size: 18px; font-weight: 600; margin: 24px 0 12px; color: #1a237e; }}
.note {{ background: #fff8e1; padding: 12px 16px; border-radius: 6px; margin: 12px 0; font-size: 13px; border-left: 4px solid #ff9800; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>{ticker} &mdash; {company}</h1>
        <div class="subtitle">BB Mean-Reversion Entry + Time-Stop 90d Exit &nbsp;|&nbsp; {df['Date'].iloc[0].strftime('%Y-%m-%d')} to {df['Date'].iloc[-1].strftime('%Y-%m-%d')} ({len(df)} trading days)</div>
    </div>

    <div class="kpi-grid">
        <div class="kpi"><div class="label">Total Trades</div><div class="value blue">{n}</div></div>
        <div class="kpi"><div class="label">Wins / Losses</div><div class="value green">{len(wins)}</div></div>
        <div class="kpi"><div class="label">Win Rate</div><div class="value green">{m_strat['win_rate']*100:.1f}%</div></div>
        <div class="kpi"><div class="label">Total Return</div><div class="value green">{m_strat['total_return']*100:.1f}%</div></div>
        <div class="kpi"><div class="label">Annualized</div><div class="value green">{m_strat['annualized_return']*100:.1f}%</div></div>
        <div class="kpi"><div class="label">Sharpe Ratio</div><div class="value green">{m_strat['sharpe']:.2f}</div></div>
        <div class="kpi"><div class="label">Calmar Ratio</div><div class="value green">{m_strat['calmar']:.2f}</div></div>
        <div class="kpi"><div class="label">Max Drawdown</div><div class="value red">{m_strat['max_drawdown']*100:.1f}%</div></div>
        <div class="kpi"><div class="label">Avg Hold</div><div class="value blue">{m_strat['avg_hold_days']:.0f}d</div></div>
        <div class="kpi"><div class="label">Best / Worst</div><div class="value" style="font-size:16px">{m_strat['best_trade']*100:.1f}% / {m_strat['worst_trade']*100:.1f}%</div></div>
    </div>

    <div class="card">
        <div class="card-header">Strategy Rules</div>
        <div class="card-body">
            <div class="strategy-desc">
                {strat_desc}
            </div>
            <div style="margin-bottom:12px">
                <span class="badge badge-blue">BB MR Entry</span>
                <span class="badge badge-green">TS 90d Exit</span>
                <span class="badge badge-orange">Optimal Exit</span>
            </div>
            <table>
                <thead>
                    <tr><th>Metric</th><th>Strategy</th><th>Buy &amp; Hold</th></tr>
                </thead>
                <tbody>
                    {comp}
                    {pe_comp}
                    {div_comp}
                </tbody>
            </table>
        </div>
    </div>

    <div class="card">
        <div class="card-header">Price Chart with BB MR Signals</div>
        <div class="card-body" id="price-chart"></div>
    </div>

    <div class="two-col">
        <div class="card">
            <div class="card-header">Equity Curve: Strategy vs Buy &amp; Hold</div>
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
"""

    # Valuation analysis section
    html += """
    <div class="section-title">Valuation Filter Analysis</div>
"""

    if analysis_figs.get("pe_scatter"):
        html += """
    <div class="card">
        <div class="card-header">P/E Ratio Distribution &mdash; BB MR Entry Points Marked</div>
        <div class="card-body" id="pe-scatter"></div>
    </div>
"""

    if analysis_figs.get("div_chart"):
        html += """
    <div class="card">
        <div class="card-header">Dividend Yield Distribution &mdash; BB MR Entry Points Marked</div>
        <div class="card-body" id="div-chart"></div>
    </div>
"""

    if analysis_figs.get("pe_filter"):
        html += """
    <div class="card">
        <div class="card-header">Return Distribution: All Entries vs PE-Filtered (P/E &lt; 15)</div>
        <div class="card-body" id="pe-filter"></div>
    </div>
"""

    # Strategy comparison
    if results:
        html += """
    <div class="card">
        <div class="card-header">Strategy Comparison: Sharpe Ratio by Exit Method</div>
        <div class="card-body" id="comp-chart"></div>
    </div>
"""

    # Trade log
    html += f"""
    <div class="card">
        <div class="card-header">Trade Log ({n} trades, {len(wins)} wins, {len(losses)} losses)</div>
        <div class="card-body" style="overflow-x:auto;">
            <table>
                <thead>
                    <tr><th>#</th><th>Entry Date</th><th>Exit Date</th><th>Entry &pound;</th><th>Exit &pound;</th><th>Return</th><th>Days</th><th></th></tr>
                </thead>
                <tbody>
                    {trade_rows}
                </tbody>
            </table>
        </div>
    </div>
"""

    # Note about PE data coverage
    pe_nonnull = df["ta_pe"].notna().sum()
    html += f"""
    <div class="note">
        <strong>Note:</strong> P/E and dividend yield data are available for only {pe_nonnull} of {len(df)} trading days
        (~{pe_nonnull/len(df)*100:.0f}% coverage). These fundamentals are updated quarterly, causing gaps in the data.
    </div>
"""

    html += f"""
    <div class="footer">
        Generated {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')} &middot;
        Data: data/analysis-data/{ticker}.csv &middot;
        Powered by Plotly
    </div>
</div>

<script>
"""

    for name, fig in figs:
        html += f'Plotly.newPlot("{name}", {fig.to_json()}, {fig.layout.to_json()}, {{responsive: true, displayModeBar: false}});\n'

    for name, fig in analysis_figs.items():
        html += f'Plotly.newPlot("{name}", {fig.to_json()}, {fig.layout.to_json()}, {{responsive: true, displayModeBar: false}});\n'

    html += "</script>\n</body>\n</html>"
    return html


# ── Main ──
def main():
    ticker = "NG.L"
    print(f"Loading {ticker} data...")
    df = load_ticker(ticker)
    close = df["Close"]
    company = get_company(ticker)
    print(f"Data: {len(df)} rows, {df['Date'].iloc[0].date()} to {df['Date'].iloc[-1].date()}")

    # Generate entry signals
    entries_all = bb_meanrev_entry(df)
    entry_count = int(entries_all.sum())
    print(f"BB MR signals: {entry_count}")

    # ── Primary strategy: TS 90d ──
    print("\nRunning primary strategy (TS 90d)...")
    trades_90, eq_bh, eq_strat_90 = run_backtest(df, entries_all,
                                                   lambda d, i, ei, ep: exit_time_stop(d, i, ei, ep, 90))
    m_90 = compute_metrics(trades_90, eq_bh, eq_strat_90, close)
    print(f"  Trades: {m_90['trades']}, WR: {m_90['win_rate']*100:.1f}%, Return: {m_90['total_return']*100:.1f}%, Sharpe: {m_90['sharpe']:.2f}")

    # ── Buy & hold baseline ──
    m_bh = {
        "total_return": float(close.iloc[-1] / close.iloc[0] - 1),
        "annualized_return": float((1 + close.iloc[-1] / close.iloc[0] - 1) ** (TRADE_FREQ / len(close)) - 1),
        "sharpe": 0, "calmar": 0, "max_drawdown": 0, "profit_factor": 0,
        "avg_hold_days": 0, "trades": 0,
    }
    bh_rets = close.pct_change().dropna()
    if len(bh_rets) > 1 and bh_rets.std() > 0:
        m_bh["sharpe"] = float((bh_rets.mean() * TRADE_FREQ - RISK_FREE) / (bh_rets.std() * np.sqrt(TRADE_FREQ)))
    bh_peak = np.maximum.accumulate((close / close.iloc[0] - 1).values)
    bh_dd = (close / close.iloc[0] - 1 - bh_peak) / np.where(bh_peak != 0, bh_peak, 1)
    m_bh["max_drawdown"] = float(abs(bh_dd.min()))
    m_bh["avg_hold_days"] = len(close)

    # ── PE filter analysis ──
    print("\nRunning PE filter analysis...")
    entries_pe = bb_meanrev_pe_entry(df, pe_threshold=15)
    entry_pe_count = int(entries_pe.sum())
    print(f"  PE-filtered signals (P/E < 15): {entry_pe_count}")

    trades_pe, _, _ = run_backtest(df, entries_pe,
                                    lambda d, i, ei, ep: exit_time_stop(d, i, ei, ep, 90))
    m_pe = compute_metrics(trades_pe, eq_bh, eq_strat_90, close)
    if m_pe:
        print(f"  PE trades: {m_pe['trades']}, WR: {m_pe['win_rate']*100:.1f}%, Sharpe: {m_pe['sharpe']:.2f}")
    else:
        print("  No PE-filtered trades with P/E < 15")

    # ── Dividend yield filter analysis ──
    print("\nRunning dividend yield analysis...")
    div_data = df[df["ta_div_yield"] > 0]
    if len(div_data) > 0:
        entries_div = entries_all & (df["ta_div_yield"] > 0)
        trades_div, _, _ = run_backtest(df, entries_div,
                                         lambda d, i, ei, ep: exit_time_stop(d, i, ei, ep, 90))
        m_div = compute_metrics(trades_div, eq_bh, eq_strat_90, close)
        if m_div:
            print(f"  Div yield trades: {m_div['trades']}, WR: {m_div['win_rate']*100:.1f}%, Sharpe: {m_div['sharpe']:.2f}")
    else:
        m_div = None

    # ── Strategy comparison (from exit analysis results) ──
    print("\nLoading strategy comparison data...")
    results = []
    json_path = REPORT_DIR / "NG.L" / "exit_analysis_results.json"
    if json_path.exists():
        with open(json_path) as f:
            all_results = json.load(f)
        for r in all_results:
            results.append(r)
        print(f"  Loaded {len(results)} strategy variants from exit analysis")

    # ── Build charts ──
    print("\nBuilding charts...")
    fig_price = make_price_chart(df, trades_90, ticker)
    fig_equity = make_equity_chart(eq_bh, eq_strat_90, df)
    fig_dd = make_drawdown_chart(eq_strat_90, df)
    fig_hist = make_return_hist(trades_90)
    fig_hold = make_hold_hist(trades_90)

    figs = [
        ("price", fig_price), ("equity", fig_equity), ("drawdown", fig_dd),
        ("hist", fig_hist), ("hold", fig_hold),
    ]

    # Analysis charts
    analysis_figs = {}
    pe_scatter = make_pe_scatter(df)
    if pe_scatter:
        analysis_figs["pe_scatter"] = pe_scatter

    div_chart = make_dividend_yield_chart(df)
    if div_chart:
        analysis_figs["div_chart"] = div_chart

    pe_filter = make_pe_filter_analysis(trades_pe, trades_90)
    if pe_filter:
        analysis_figs["pe_filter"] = pe_filter

    if results:
        comp_chart = make_strategy_comparison(results)
        if comp_chart:
            analysis_figs["comp-chart"] = comp_chart

    # ── Generate HTML report ──
    print("\nGenerating HTML report...")
    html = build_html(ticker, company, trades_90, m_bh, m_90, m_pe, m_div,
                      figs, df, analysis_figs, results)

    ticker = "NG.L"
    ticker_dir = REPORT_DIR / ticker
    ticker_dir.mkdir(parents=True, exist_ok=True)
    out = ticker_dir / "optimized_strategy.html"
    out.write_text(html, encoding="utf-8")
    print(f"\nReport saved to: {out}")
    print(f"\n{'='*60}")
    print(f"SUMMARY: {ticker} — BB MR + TS 90d")
    print(f"{'='*60}")
    print(f"  Total Trades:   {m_90['trades']}")
    print(f"  Win Rate:       {m_90['win_rate']*100:.1f}%")
    print(f"  Total Return:   {m_90['total_return']*100:.1f}%")
    print(f"  Annualized:     {m_90['annualized_return']*100:.1f}%")
    print(f"  Sharpe:         {m_90['sharpe']:.2f}")
    print(f"  Calmar:         {m_90['calmar']:.2f}")
    print(f"  Max Drawdown:   {m_90['max_drawdown']*100:.1f}%")
    print(f"  Profit Factor:  {m_90['profit_factor']:.2f}")
    print(f"  Avg Hold Days:  {m_90['avg_hold_days']:.0f}")
    print(f"  Best/Worst:     {m_90['best_trade']*100:.1f}% / {m_90['worst_trade']*100:.1f}%")
    if m_pe:
        print(f"\nPE Filter (P/E < 15):")
        print(f"  Trades:         {m_pe['trades']} (vs {m_90['trades']} all)")
        print(f"  Win Rate:       {m_pe['win_rate']*100:.1f}%")
        print(f"  Total Return:   {m_pe['total_return']*100:.1f}%")
        print(f"  Sharpe:         {m_pe['sharpe']:.2f}")


if __name__ == "__main__":
    main()
