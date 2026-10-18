#!/usr/bin/env python
"""Analyse market data and generate interactive HTML reports."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ANALYSIS_DIR = BASE_DIR / "data" / "analysis-data"
DEFAULT_OUTPUT_DIR = BASE_DIR / "data" / "reports"
PLOTLY_VERSION = "2.35.0"


def _v(s, col):
    if col not in s.index or pd.isna(s.get(col)):
        return None
    v = s[col]
    return float(v)


def _emoji(ok):
    """Return emoji: green=good, red=bad, yellow=unknown."""
    if ok is None:
        return "\U0001f7e9"
    return "\u2705" if ok else "\U0001f534"


def _fmt(val, d=2):
    if val is None:
        return "N/A"
    return f"{float(val):.{d}f}" if isinstance(val, (float, int)) else str(val)


# --- Condition Analysis ---

def analyse_ticker(df):
    """Analyse a ticker's latest data and return a summary dict."""
    df = df.sort_values("Date").reset_index(drop=True)
    L = df.iloc[-1]
    P = df.iloc[-2] if len(df) > 1 else L

    close = _v(L, "Close") or _v(L, "Adj Close")
    date_str = str(L.get("Date", "N/A"))[:10]

    # Trend
    ema20, ema50, ema200 = _v(L, "ta_ema20"), _v(L, "ta_ema50"), _v(L, "ta_ema200")
    st_dir = _v(L, "ta_supertrend_direction")
    price_above_ema20 = close > ema20 if close and ema20 else None
    ema_bullish = ema20 and ema50 and ema200 and ema20 > ema50 > ema200
    ema_bearish = ema20 and ema50 and ema200 and ema20 < ema50 < ema200
    st_bullish = st_dir == 1 if st_dir is not None else None
    trend_items = [
        ("EMA20 > EMA50 > EMA200", ema_bullish, f"20:{_fmt(ema20)} > 50:{_fmt(ema50)} > 200:{_fmt(ema200)}"),
        ("SuperTrend", st_bullish, "Uptrend" if st_bullish == True else "Downtrend" if st_bullish == False else "N/A"),
        ("Price vs EMA20", price_above_ema20, f"Close:{_fmt(close)} vs EMA20:{_fmt(ema20)}"),
    ]

    # Momentum
    rsi = _v(L, "ta_rsi14")
    macd_hist = _v(L, "ta_macd_histogram")
    macd_line = _v(L, "ta_macd_line")
    macd_signal = _v(L, "ta_macd_signal")
    roc = _v(L, "ta_roc20")
    rsi_overbought = rsi > 70 if rsi else None
    rsi_oversold = rsi < 30 if rsi else None
    macd_bullish = macd_hist > 0 if macd_hist else None
    macd_cross = macd_line > macd_signal if macd_line and macd_signal else None
    momentum_items = [
        ("RSI(14)", None if rsi is None else (rsi_overbought or rsi_oversold), f"{_fmt(rsi,1)}{' (Overbought)' if rsi_overbought else ' (Oversold)' if rsi_oversold else ''}"),
        ("MACD Histogram", macd_bullish, f"{_fmt(macd_hist)}"),
        ("MACD Cross", macd_cross, "Line > Signal" if macd_cross else "Line < Signal"),
        ("ROC(20)", None if roc is None else roc > 0, f"{_fmt(roc,1)}%"),
    ]

    # Volume
    obv = _v(L, "ta_obv")
    cmf = _v(L, "ta_cmf")
    vol = _v(L, "Volume")
    obv_5 = df["ta_obv"].iloc[-5:].tolist() if "ta_obv" in df.columns else []
    obv_rising = len(obv_5) == 5 and obv_5[-1] > obv_5[0] if obv_5 else None
    cmf_pos = cmf > 0 if cmf else None
    volume_items = [
        ("OBV Trend (5-bar)", obv_rising, f"Rising" if obv_rising else "Falling" if obv_rising is False else "N/A"),
        ("CMF(20)", cmf_pos, f"{_fmt(cmf,4)}"),
        ("Volume", vol is not None, f"{vol:,.0f}" if vol else "N/A"),
    ]

    # Volatility
    atr = _v(L, "ta_atr14")
    norm_atr = _v(L, "ta_normalized_atr14")
    bb_upper = _v(L, "ta_bband_upper")
    bb_lower = _v(L, "ta_bband_lower")
    bb_middle = _v(L, "ta_bband_middle")
    atr_pct = norm_atr if norm_atr else None
    price_in_bb = (close > bb_lower and close < bb_upper) if close and bb_upper and bb_lower else None
    price_near_upper = close > bb_upper * 0.98 if close and bb_upper else None
    volatility_items = [
        ("ATR(14) %", atr_pct is not None, f"{_fmt(atr_pct,2)}%"),
        ("Price in BB", price_in_bb, f"Inside ({_fmt(close)} vs {_fmt(bb_lower)}-{_fmt(bb_upper)})"),
        ("Price near BB Upper", price_near_upper, "Yes" if price_near_upper else "No"),
    ]

    # Regime
    hmm_regime = _v(L, "ta_hmm_regime")
    hmm_0 = _v(L, "ta_hmm_regime_prob_0")
    hmm_1 = _v(L, "ta_hmm_regime_prob_1")
    hmm_2 = _v(L, "ta_hmm_regime_prob_2")
    regime_labels = {0: "Bull", 1: "Bear", 2: "Volatile"}
    regime = int(hmm_regime) if hmm_regime is not None else None
    regime_items = [
        ("HMM Regime", regime is not None, f"{regime_labels.get(regime, 'Unknown')} ({_fmt(hmm_0,1)}/{_fmt(hmm_1,1)}/{_fmt(hmm_2,1)})"),
    ]

    # Changes
    L2 = df.iloc[-3] if len(df) > 2 else P
    changes = []
    change_fields = [
        ("RSI", _v(L, "ta_rsi14"), _v(L2, "ta_rsi14"), lambda a, b: (a > 70) != (b > 70)),
        ("MACD Hist", _v(L, "ta_macd_histogram"), _v(L2, "ta_macd_histogram"), lambda a, b: (a > 0) != (b > 0)),
        ("SuperTrend", _v(L, "ta_supertrend_direction"), _v(L2, "ta_supertrend_direction"), lambda a, b: a != b),
        ("CMF", _v(L, "ta_cmf"), _v(L2, "ta_cmf"), lambda a, b: (a > 0) != (b > 0) if a is not None and b is not None else False),
        ("HMM Regime", _v(L, "ta_hmm_regime"), _v(L2, "ta_hmm_regime"), lambda a, b: int(a) != int(b) if a is not None and b is not None else False),
        ("Price", close, _v(L2, "Close"), lambda a, b: a > b if a and b else False),
    ]
    for name, cur, prev, changed_fn in change_fields:
        if cur is None or prev is None:
            continue
        if changed_fn(cur, prev):
            changes.append(name)

    return {
        "ticker": "",  # set by caller
        "date": date_str, "close": close, "rsi": rsi, "macd_hist": macd_hist,
        "trend": trend_items, "momentum": momentum_items, "volume": volume_items,
        "volatility": volatility_items, "regime": regime_items,
        "changes": changes, "df": df,
    }


def discover_tickers(tickers=None):
    """Discover ticker CSVs from analysis-data directory."""
    csv_files = sorted(ANALYSIS_DIR.glob("*.csv"))
    all_tickers = [f.stem for f in csv_files]
    if tickers:
        all_tickers = [t for t in tickers if t in all_tickers]
        missing = set(tickers) - set(all_tickers)
        if missing:
            print(f"Warning: tickers not found: {missing}")
    if not all_tickers:
        print(f"No CSV files found in {ANALYSIS_DIR}")
    return all_tickers


def load_ticker(name):
    """Load a ticker's analysis CSV."""
    path = ANALYSIS_DIR / f"{name}.csv"
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


# --- Chart Building ---

def build_charts(name, df):
    """Build 4 Plotly figures per ticker."""
    df = df.sort_values("Date").reset_index(drop=True)
    dates = df["Date"].dt.strftime("%Y-%m-%d")

    # 1. OHLC + EMA
    fig1 = go.Figure(data=[go.Candlestick(
        x=dates, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        name="OHLC", increasing_line_color="#26a69a", decreasing_line_color="#ef5350"
    )])
    for col, color, label in [("ta_ema20", "#ff9800", "EMA20"), ("ta_ema50", "#2196f3", "EMA50"), ("ta_ema200", "#9c27b0", "EMA200")]:
        if col in df.columns:
            fig1.add_trace(go.Scatter(x=dates, y=df[col], mode="lines", name=label, line=dict(color=color, width=1)))
    fig1.update_layout(hovermode="x unified", height=500, margin=dict(l=10, r=10, t=30, b=10))

    # 2. Volume + OBV
    fig2 = go.Figure()
    colors = ["#26a69a" if df["Close"].iloc[i] >= df["Open"].iloc[i] else "#ef5350" for i in range(len(df))]
    fig2.add_trace(go.Bar(x=dates, y=df["Volume"], name="Volume", marker_color=colors, yaxis="y2"))
    if "ta_obv" in df.columns:
        fig2.add_trace(go.Scatter(x=dates, y=df["ta_obv"], mode="lines", name="OBV", line=dict(color="#66bb6a", width=1.5)))
    fig2.update_layout(hovermode="x unified", height=300, margin=dict(l=10, r=10, t=10, b=10), yaxis2=dict(overlaying="y", side="left"))

    # 3. MACD
    fig3 = go.Figure()
    if all(c in df.columns for c in ["ta_macd_line", "ta_macd_signal", "ta_macd_histogram"]):
        fig3.add_trace(go.Bar(x=dates, y=df["ta_macd_histogram"], name="Histogram", marker_color=df["ta_macd_histogram"].apply(lambda x: "#26a69a" if x >= 0 else "#ef5350")))
        fig3.add_trace(go.Scatter(x=dates, y=df["ta_macd_line"], mode="lines", name="MACD", line=dict(color="#1976d2", width=1.5)))
        fig3.add_trace(go.Scatter(x=dates, y=df["ta_macd_signal"], mode="lines", name="Signal", line=dict(color="#ff9800", width=1)))
    fig3.update_layout(hovermode="x unified", height=300, margin=dict(l=10, r=10, t=10, b=10))

    # 4. RSI + Bollinger Bands
    fig4 = go.Figure()
    if "ta_rsi14" in df.columns:
        fig4.add_trace(go.Scatter(x=dates, y=df["ta_rsi14"], mode="lines", name="RSI(14)", line=dict(color="#7b1fa2", width=1.5)))
    if "ta_bband_upper" in df.columns:
        fig4.add_trace(go.Scatter(x=dates, y=df["ta_bband_upper"], mode="lines", name="BB Upper", line=dict(color="#aaa", width=0.5, dash="dot")))
        fig4.add_trace(go.Scatter(x=dates, y=df["ta_bband_lower"], mode="lines", name="BB Lower", line=dict(color="#aaa", width=0.5, dash="dot"), fill="tonexty", fillcolor="rgba(170,170,170,0.1)"))
    fig4.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5)
    fig4.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5)
    fig4.update_layout(hovermode="x unified", height=300, margin=dict(l=10, r=10, t=10, b=10), yaxis=dict(range=[0, 100]))

    return [fig1, fig2, fig3, fig4]


# --- HTML Generation ---

def _card_html(report):
    """Generate HTML for a single ticker summary card."""
    def row(emoji, label, val):
        return f"<tr><td>{emoji or ''}</td><td><b>{label}</b></td><td>{val}</td></tr>"

    trend_html = "".join(row(_emoji(item[1]), item[0], item[2]) for item in report["trend"])
    mom_html = "".join(row(_emoji(item[1]), item[0], item[2]) for item in report["momentum"])
    vol_html = "".join(row(_emoji(item[1]), item[0], item[2]) for item in report["volume"])
    vola_html = "".join(row(_emoji(item[1]), item[0], item[2]) for item in report["volatility"])
    reg_html = "".join(row(_emoji(item[1]), item[0], item[2]) for item in report["regime"])

    changes_html = ""
    if report["changes"]:
        changes_html = f'<div style="background:#fff3e0;padding:10px;border-radius:6px;margin-bottom:10px"><b>Changes Since Yesterday:</b> {", ".join(report["changes"])}</div>'
    else:
        changes_html = '<div style="padding:10px;margin-bottom:10px"><b>Changes Since Yesterday:</b> No major changes</div>'

    return f"""
<div class="card">
<h3>{report['ticker']} -- {report['date']} -- Close: {_fmt(report['close'])}</h3>
{changes_html}
<table>{trend_html}{mom_html}{vol_html}{vola_html}{reg_html}</table>
</div>"""


def generate_ticker_html(report):
    """Generate a single HTML report for one ticker."""
    card_html = _card_html(report)

    figs = build_charts(report["ticker"], report["df"])
    charts = ""
    for i, fig in enumerate(figs):
        charts += f'<div class="chart-container"><h4>{["Price (OHLC+EMA)", "Volume + OBV", "MACD", "RSI + Bollinger"][i]}</h4>'
        charts += fig.to_html(full_html=False, include_plotlyjs=False, config={"displayModeBar": False})
        charts += "</div>"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{report['ticker']} Market Analysis</title>
<script src="https://cdn.plot.ly/plotly-{PLOTLY_VERSION}.min.js"></script>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
h1 {{ text-align: center; color: #333; }}
table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
td {{ padding: 6px 12px; border-bottom: 1px solid #eee; }}
.card {{ background: #fff; border-radius: 8px; padding: 16px; margin: 12px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
.card h3 {{ margin-top: 0; color: #333; }}
.chart-container {{ background: #fff; border-radius: 8px; padding: 16px; margin: 16px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
.chart-container h4 {{ margin: 0 0 8px 0; color: #666; }}
</style></head><body>
<h1>{report['ticker']} Market Analysis</h1>
{card_html}
{charts}
</body></html>"""
    return html


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Analyse market data and generate per-ticker HTML reports")
    parser.add_argument("tickers", nargs="*", help="Tickers to analyse (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Show analysis only, don't generate HTML")
    parser.add_argument("--output", default=None, help="Output directory for HTML report")
    args = parser.parse_args()

    tickers = discover_tickers(args.tickers)
    reports = []
    for t in tickers:
        print(f"Analysing {t}...")
        df = load_ticker(t)
        r = analyse_ticker(df)
        r["ticker"] = t
        reports.append(r)
        # Print quick summary
        print(f"  Close={_fmt(r['close'])}, RSI={_fmt(r['rsi'],1)}, MACD_hist={_fmt(r['macd_hist'])}")
        if r["changes"]:
            print(f"  Changes: {', '.join(r['changes'])}")

    if args.dry_run:
        print("\nDry run complete. Analysis shown above.")
        return

    output_dir = Path(args.output) if args.output else DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    for r in reports:
        output_path = output_dir / f"{r['ticker']}_analysis.html"
        html = generate_ticker_html(r)
        output_path.write_text(html, encoding="utf-8")
        print(f"Report written to {output_path}")


if __name__ == "__main__":
    main()
