#!/usr/bin/env python3
"""
NG.L Exit Strategy Analysis - Optimal exit criteria for mean-reversion trades.

Tests multiple exit methods on BB Mean Reversion entries over the last
10 years (2016-10-15 onwards). Uses custom trade simulation to support
profit targets, time stops, and dual exits (not natively in vectorbt).

Exit methods tested:
  1. BB Middle (baseline)
  2. RSI > 50 / 60 / 70
  3. MACD bearish cross
  4. SuperTrend flip to -1
  5. EMA20 cross (close < EMA20)
  6. Structure break (LH or LL = 1)
  7. Time-stop forced exit: 30d / 45d / 60d / 90d / 120d
  8. Dual: BB Middle + RSI threshold (OR)
  9. Dual: BB Middle + SuperTrend flip (OR)
 10. Dual: BB Middle + MACD cross (OR)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PATH = ROOT / "data" / "analysis-data" / "NG.L.csv"
CUTOFF_DATE = pd.Timestamp("2016-10-15")
REPORT_DIR = ROOT / "data" / "backtest-reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
SLIPPAGE = 0.001
RISK_FREE = 0.05
TRADE_FREQ = 252


def load_data():
    df = pd.read_csv(DATA_PATH)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    df.index = df["Date"]
    df = df[df["Date"] >= CUTOFF_DATE].reset_index(drop=True)
    for col in df.select_dtypes(include="number").columns:
        df[col] = df[col].fillna(0)
    return df


def bb_meanrev_entry(df):
    """BB Mean Reversion Entry: Close <= BB Lower, RSI < 30, Williams %R < -80."""
    return (
        (df["Close"] <= df["ta_bband_lower"]) &
        (df["ta_rsi14"] < 30) &
        (df["ta_williams_r"] < -80)
    )


def run_backtest(df, entries, exit_fn):
    """Run backtest with custom simulation (supports PT, time stops, dual exits)."""
    close = df["Close"].values
    dates = df["Date"].values
    n = len(df)
    trades = []
    cum_strat = 0.0
    equity_strat = [0.0]

    in_pos = False
    entry_price = entry_date = entry_idx = 0

    for i in range(n):
        price = close[i]
        cum_bh = price / close[0] - 1
        equity_strat.append(cum_strat + cum_bh * (1 + cum_strat) - cum_bh)
        # Simplified equity
        equity_strat[i] = cum_strat + (price / close[0] - 1 - cum_strat) if not in_pos else equity_strat[i-1]

        if not in_pos and entries.iloc[i]:
            in_pos = True
            entry_price = price * (1 + SLIPPAGE)
            entry_date = dates[i]
            entry_idx = i
        elif in_pos:
            exit_trigger = exit_fn(df, i, entry_idx, entry_price)
            if exit_trigger:
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

    # Recompute equity curve properly
    equity_bh = []
    equity_strat2 = []
    cum_bh = cum_strat = 0.0
    trade_set = {(t["entry_idx"], t["exit_idx"]): t["return"] for t in trades if not t.get("open")}
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
            exit_trigger = exit_fn(df, i, len(equity_strat2) - 1, ep)
            if exit_trigger:
                ret = (price / ep - 1) - SLIPPAGE
                cum_strat = (1 + cum_strat) * (1 + ret) - 1
                in_pos = False
        equity_strat2.append(cum_strat)

    return trades, equity_bh, equity_strat2


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
        "avg_win_hold": float(np.mean([t["hold_days"] for t in trades if t["return"] > 0])) if np.any(wins) else 0,
        "avg_loss_hold": float(np.mean([t["hold_days"] for t in trades if t["return"] <= 0])) if np.any(~wins) else 0,
    }


# ===========================================================================
# Exit functions
# ===========================================================================
def exit_bb_middle(df, idx, entry_idx, entry_price):
    return df["Close"].iloc[idx] >= df["ta_bband_middle"].iloc[idx]


def exit_rsi(df, idx, entry_idx, entry_price, threshold=50):
    return df["ta_rsi14"].iloc[idx] > threshold


def exit_macd(df, idx, entry_idx, entry_price):
    return df["ta_macd_line"].iloc[idx] < df["ta_macd_signal"].iloc[idx]


def exit_supertrend(df, idx, entry_idx, entry_price):
    return df["ta_supertrend_direction"].iloc[idx] == -1


def exit_ema20(df, idx, entry_idx, entry_price):
    return df["Close"].iloc[idx] < df["ta_ema20"].iloc[idx]


def exit_structure(df, idx, entry_idx, entry_price):
    return (
        df["ta_lh"].fillna(0).iloc[idx] == 1 or
        df["ta_ll"].fillna(0).iloc[idx] == 1
    )


def exit_time_stop(df, idx, entry_idx, entry_price, max_days=60):
    elapsed = (df["Date"].iloc[idx] - df["Date"].iloc[entry_idx]).days
    return elapsed >= max_days


def exit_dual_or(df, idx, entry_idx, entry_price, primary_fn, secondary_fn):
    return primary_fn(df, idx, entry_idx, entry_price) or secondary_fn(df, idx, entry_idx, entry_price)


# ===========================================================================
# Build exit configs
# ===========================================================================
def build_configs():
    configs = []
    configs.append(("BB Middle (baseline)", lambda df, i, ei, ep: exit_bb_middle(df, i, ei, ep)))
    configs.append(("RSI > 50", lambda df, i, ei, ep: exit_rsi(df, i, ei, ep, 50)))
    configs.append(("RSI > 60", lambda df, i, ei, ep: exit_rsi(df, i, ei, ep, 60)))
    configs.append(("RSI > 70", lambda df, i, ei, ep: exit_rsi(df, i, ei, ep, 70)))
    configs.append(("MACD bearish cross", lambda df, i, ei, ep: exit_macd(df, i, ei, ep)))
    configs.append(("SuperTrend flip", lambda df, i, ei, ep: exit_supertrend(df, i, ei, ep)))
    configs.append(("EMA20 cross", lambda df, i, ei, ep: exit_ema20(df, i, ei, ep)))
    configs.append(("Structure break (LH/LL)", lambda df, i, ei, ep: exit_structure(df, i, ei, ep)))
    # Time stops
    for d in [30, 45, 60, 90, 120]:
        configs.append((f"Time-stop {d}d", lambda df, i, ei, ep, max_d=d: exit_time_stop(df, i, ei, ep, max_d)))
    # Dual exits (OR logic - exit on whichever comes first)
    configs.append(("BB Middle OR RSI > 50", lambda df, i, ei, ep: exit_dual_or(df, i, ei, ep, exit_bb_middle, lambda d, j, k, l: exit_rsi(d, j, k, l, 50))))
    configs.append(("BB Middle OR RSI > 60", lambda df, i, ei, ep: exit_dual_or(df, i, ei, ep, exit_bb_middle, lambda d, j, k, l: exit_rsi(d, j, k, l, 60))))
    configs.append(("BB Middle OR MACD cross", lambda df, i, ei, ep: exit_dual_or(df, i, ei, ep, exit_bb_middle, exit_macd)))
    configs.append(("BB Middle OR SuperTrend", lambda df, i, ei, ep: exit_dual_or(df, i, ei, ep, exit_bb_middle, exit_supertrend)))
    configs.append(("BB Middle OR Structure", lambda df, i, ei, ep: exit_dual_or(df, i, ei, ep, exit_bb_middle, exit_structure)))
    return configs


# ===========================================================================
# Analysis
# ===========================================================================
def run_analysis(df):
    entries = bb_meanrev_entry(df)
    configs = build_configs()
    results = []

    for name, exit_fn in configs:
        trades, eq_bh, eq_strat = run_backtest(df, entries, exit_fn)
        m = metrics(trades, eq_bh, eq_strat, df["Close"])
        if m:
            m["name"] = name
            results.append(m)

    return results, entries, df


# ===========================================================================
# Report generation
# ===========================================================================
def build_html(results, df, entries):
    n = len(results)
    entry_count = entries.sum() if hasattr(entries, 'sum') else len(entries)
    rows = ""
    for r in results:
        wr_color = "#26a69a" if r["win_rate"] > 0.8 else "#ff9800" if r["win_rate"] > 0.6 else "#ef5350"
        dd_color = "#26a69a" if r["max_drawdown"] < 0.10 else "#ff9800" if r["max_drawdown"] < 0.20 else "#ef5350"
        rows += f"""<tr>
            <td>{r['name']}</td>
            <td>{r['trades']}</td>
            <td style="color:{wr_color};font-weight:600">{r['win_rate']*100:.1f}%</td>
            <td style="color:#26a69a;font-weight:600">{r['total_return']*100:.1f}%</td>
            <td>{r['annualized_return']*100:.1f}%</td>
            <td style="color:#26a69a;font-weight:600">{r['sharpe']:.2f}</td>
            <td>{r['calmar']:.2f}</td>
            <td style="color:{dd_color};font-weight:600">{r['max_drawdown']*100:.1f}%</td>
            <td>{r['profit_factor']:.2f}</td>
            <td>{r['best_consec_losses']}</td>
            <td>{r['avg_hold_days']:.0f}</td>
            <td>{r['best_trade']*100:.1f}% / {r['worst_trade']*100:.1f}%</td>
        </tr>
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NG.L Exit Strategy Analysis</title>
<script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; padding: 20px; }}
.container {{ max-width: 1400px; margin: 0 auto; }}
.header {{ background: linear-gradient(135deg, #1a237e, #283593); color: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; }}
.header h1 {{ font-size: 26px; margin-bottom: 6px; }}
.header .subtitle {{ font-size: 14px; opacity: 0.85; }}
.kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 20px; }}
.kpi {{ background: white; padding: 16px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }}
.kpi .label {{ font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }}
.kpi .value {{ font-size: 22px; font-weight: 700; margin-top: 4px; }}
.card {{ background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; overflow: hidden; }}
.card .card-header {{ background: #fafafa; padding: 14px 20px; border-bottom: 1px solid #eee; font-weight: 600; font-size: 16px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
table th {{ background: #f5f5f5; padding: 10px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #ddd; white-space: nowrap; }}
table td {{ padding: 8px 12px; border-bottom: 1px solid #eee; white-space: nowrap; }}
table tr:hover {{ background: #fafafa; }}
.two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
@media (max-width: 800px) {{ .two-col {{ grid-template-columns: 1fr; }} }}
.footer {{ text-align: center; padding: 20px; font-size: 12px; color: #999; }}
.highlight {{ background: #e8f5e9; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>NG.L Exit Strategy Analysis</h1>
        <div class="subtitle">BB Mean Reversion entries ({entry_count} signals) - Multiple exit methods compared - Period: {df['Date'].iloc[0].strftime('%Y-%m-%d')} to {df['Date'].iloc[-1].strftime('%Y-%m-%d')} ({len(df)} trading days)</div>
    </div>

    <div class="card">
        <div class="card-header">Exit Strategy Comparison ({n} configs) - Sorted by Sharpe Ratio</div>
        <div class="card-body" style="overflow-x:auto;">
            <table>
                <thead>
                    <tr>
                        <th>Exit Method</th><th>Trades</th><th>Win Rate</th>
                        <th>Total Return</th><th>Annualized</th><th>Sharpe</th>
                        <th>Calmar</th><th>Max DD</th><th>Profit Factor</th>
                        <th>Max Consec Loss</th><th>Avg Hold</th><th>Best/Worst</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
    </div>

    <div class="two-col">
        <div class="card">
            <div class="card-header">Sharpe Ratio Comparison</div>
            <div class="card-body" id="sharpe-chart"></div>
        </div>
        <div class="card">
            <div class="card-header">Max Drawdown Comparison</div>
            <div class="card-body" id="dd-chart"></div>
        </div>
    </div>

    <div class="two-col">
        <div class="card">
            <div class="card-header">Total Return Comparison</div>
            <div class="card-body" id="return-chart"></div>
        </div>
        <div class="card">
            <div class="card-header">Sharpe vs Max Drawdown (bubble size = total return)</div>
            <div class="card-body" id="scatter-chart"></div>
        </div>
    </div>

    <div class="footer">
        Generated {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')} &middot;
        Data: data/analysis-data/NG.L.csv &middot;
        Powered by Plotly
    </div>
</div>

<script>
"""

    # Sharpe chart
    sorted_by_sharpe = sorted(results, key=lambda x: x["sharpe"], reverse=True)
    sharpe_names = [r["name"] for r in sorted_by_sharpe]
    sharpe_vals = [r["sharpe"] for r in sorted_by_sharpe]
    sharpe_colors = ["#26a69a" if v > 5 else "#ff9800" if v > 0 else "#ef5350" for v in sharpe_vals]

    html += f"""
Plotly.newPlot("sharpe-chart", [{{
    y: {json.dumps(sharpe_names[::-1])},
    x: {json.dumps(sharpe_vals[::-1])},
    type: "bar",
    orientation: "h",
    marker: {{ color: {json.dumps(sharpe_colors[::-1])} }},
    text: sharpe_vals[::-1].map(v => v.toFixed(2)),
    textposition: "outside"
}}], {{
    margin: {{ l: 200, r: 40, t: 20, b: 80 }},
    yaxis: {{ automargin: true }},
    xaxis: {{ title: "Sharpe Ratio" }},
    paper_bgcolor: "white", plot_bgcolor: "white"
}}, {{responsive: true, displayModeBar: false}});

Plotly.newPlot("dd-chart", [{{
    y: {json.dumps(sharpe_names[::-1])},
    x: {json.dumps([r['max_drawdown']*100 for r in sorted_by_sharpe][::-1])},
    type: "bar",
    orientation: "h",
    marker: {{ color: {json.dumps(sharpe_colors[::-1])} }},
    text: {json.dumps([f"{r['max_drawdown']*100:.1f}%" for r in sorted_by_sharpe][::-1])},
    textposition: "outside"
}}], {{
    margin: {{ l: 200, r: 40, t: 20, b: 80 }},
    yaxis: {{ automargin: true }},
    xaxis: {{ title: "Max Drawdown (%)" }},
    paper_bgcolor: "white", plot_bgcolor: "white"
}}, {{responsive: true, displayModeBar: false}});

Plotly.newPlot("return-chart", [{{
    y: {json.dumps(sharpe_names[::-1])},
    x: {json.dumps([r['total_return']*100 for r in sorted_by_sharpe][::-1])},
    type: "bar",
    orientation: "h",
    marker: {{ color: {json.dumps(sharpe_colors[::-1])} }},
    text: {json.dumps([f"{r['total_return']*100:.1f}%" for r in sorted_by_sharpe][::-1])},
    textposition: "outside"
}}], {{
    margin: {{ l: 200, r: 40, t: 20, b: 80 }},
    yaxis: {{ automargin: true }},
    xaxis: {{ title: "Total Return (%)" }},
    paper_bgcolor: "white", plot_bgcolor: "white"
}}, {{responsive: true, displayModeBar: false}});

Plotly.newPlot("scatter-chart", [{{
    x: {json.dumps([r['sharpe'] for r in results])},
    y: {json.dumps([r['max_drawdown']*100 for r in results])},
    mode: "markers+text",
    text: {json.dumps([r['name'] for r in results])},
    textposition: "top center",
    textfont: {{ size: 8 }},
    marker: {{
        size: {json.dumps([abs(r['total_return'])*3 for r in results])},
        color: {json.dumps([r['sharpe'] for r in results])},
        colorscale: "RdBu",
        showscale: true,
        colorbar: {{ title: "Sharpe" }},
        line: {{ width: 1 }}
    }},
    hovertemplate: "<b>%{{text}}</b><br>Sharpe: %{{x:.2f}}<br>Max DD: %{{y:.1f}}%<extra></extra>"
}}], {{
    margin: {{ l: 60, r: 20, t: 20, b: 40 }},
    xaxis: {{ title: "Sharpe Ratio" }},
    yaxis: {{ title: "Max Drawdown (%)" }},
    paper_bgcolor: "white", plot_bgcolor: "white"
}}, {{responsive: true, displayModeBar: false}});
"""

    html += "</script>\n</body>\n</html>"
    return html


def main():
    print("Loading data...")
    df = load_data()
    print(f"Data loaded: {len(df)} rows, {df['Date'].iloc[0].date()} to {df['Date'].iloc[-1].date()}")

    print("Running analysis...")
    results, entries, _ = run_analysis(df)

    # Sort by Sharpe ratio
    results_sorted = sorted(results, key=lambda x: x["sharpe"], reverse=True)

    # Console output
    print(f"\n{'Exit Method':<40} {'Trades':>7} {'WR':>6} {'Total':>9} {'AnnRet':>8} {'Sharpe':>8} {'Calmar':>8} {'MaxDD':>8} {'PF':>8} {'MaxCL':>7} {'AvgHld':>8} {'Best/Worst':>18}")
    print("-" * 145)
    for r in results_sorted:
        print(f"{r['name']:<40} {r['trades']:>7} {r['win_rate']*100:>5.1f}% {r['total_return']*100:>8.1f}% {r['annualized_return']*100:>7.1f}% {r['sharpe']:>7.2f} {r['calmar']:>7.2f} {r['max_drawdown']*100:>6.1f}% {r['profit_factor']:>7.2f} {r['best_consec_losses']:>6} {r['avg_hold_days']:>6.0f}d {r['best_trade']*100:>6.1f}%/{r['worst_trade']*100:>6.1f}%")

    # Print recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    # Best Sharpe
    best_sharpe = results_sorted[0]
    print(f"\nBest Sharpe: {best_sharpe['name']}")
    print(f"  Sharpe: {best_sharpe['sharpe']:.2f}, Return: {best_sharpe['total_return']*100:.1f}%, WR: {best_sharpe['win_rate']*100:.1f}%, Max DD: {best_sharpe['max_drawdown']*100:.1f}%")

    # Lowest drawdown
    lowest_dd = min(results_sorted, key=lambda x: x["max_drawdown"])
    print(f"\nLowest Drawdown: {lowest_dd['name']}")
    print(f"  Max DD: {lowest_dd['max_drawdown']*100:.1f}%, Sharpe: {lowest_dd['sharpe']:.2f}, Return: {lowest_dd['total_return']*100:.1f}%")

    # Best return
    best_ret = max(results_sorted, key=lambda x: x["total_return"])
    print(f"\nHighest Return: {best_ret['name']}")
    print(f"  Return: {best_ret['total_return']*100:.1f}%, Sharpe: {best_ret['sharpe']:.2f}, WR: {best_ret['win_rate']*100:.1f}%")

    # Balanced (best Calmar)
    best_calmar = max(results_sorted, key=lambda x: x["calmar"])
    print(f"\nBest Calmar (Return/DD): {best_calmar['name']}")
    print(f"  Calmar: {best_calmar['calmar']:.2f}, Return: {best_calmar['total_return']*100:.1f}%, Max DD: {best_calmar['max_drawdown']*100:.1f}%")

    # Generate HTML report
    html = build_html(results, df, entries)
    ticker = "NG.L"
    ticker_dir = REPORT_DIR / ticker
    ticker_dir.mkdir(parents=True, exist_ok=True)
    out = ticker_dir / "exit_analysis.html"
    out.write_text(html, encoding="utf-8")
    print(f"\nReport saved to: {out}")

    # Save raw results as JSON for reference
    json_path = ticker_dir / "exit_analysis_results.json"
    with open(json_path, "w") as f:
        json.dump(results_sorted, f, indent=2, default=str)
    print(f"Raw data saved to: {json_path}")


if __name__ == "__main__":
    main()
