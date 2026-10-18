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


def _price_change_pct(df, close_col="Close", periods=None):
    """Calculate close price change % over the given periods from the last date.

    Returns dict like {"1Y": 12.3, "6M": -3.4, ...} or None for any missing window.
    """
    if periods is None:
        periods = {"1Y": pd.DateOffset(years=1), "6M": pd.DateOffset(months=6),
                    "3M": pd.DateOffset(months=3), "1M": pd.DateOffset(months=1)}
    latest = df[close_col].iloc[-1]
    results = {}
    for label, offset in periods.items():
        cutoff = df["Date"].max() - offset
        subset = df[df["Date"] < cutoff]
        if len(subset) == 0:
            results[label] = None
            continue
        base = subset[close_col].iloc[-1]
        if pd.isna(base) or base == 0:
            results[label] = None
        else:
            results[label] = (latest - base) / base * 100
    return results


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

    # Previous day values for comparison
    L_prev = df.iloc[-2]
    prev_close = _v(L_prev, "Close") or _v(L_prev, "Adj Close")
    prev_rsi = _v(L_prev, "ta_rsi14")
    prev_macd_hist = _v(L_prev, "ta_macd_histogram")
    prev_macd_line = _v(L_prev, "ta_macd_line")
    prev_macd_signal = _v(L_prev, "ta_macd_signal")
    prev_ema20 = _v(L_prev, "ta_ema20")
    prev_ema50 = _v(L_prev, "ta_ema50")
    prev_ema200 = _v(L_prev, "ta_ema200")
    prev_st_dir = _v(L_prev, "ta_supertrend_direction")
    prev_cmf = _v(L_prev, "ta_cmf")
    prev_atr = _v(L_prev, "ta_atr14")
    prev_norm_atr = _v(L_prev, "ta_normalized_atr14")
    prev_rroc = _v(L_prev, "ta_roc20")
    prev_regime = _v(L_prev, "ta_hmm_regime")
    prev_volume = _v(L_prev, "Volume")

    # Price change
    price_chg = close - prev_close if close and prev_close else None
    price_chg_pct = (price_chg / prev_close * 100) if price_chg and prev_close else None

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

    # Multi-period price change
    price_chg_periods = _price_change_pct(df)

    return {
        "ticker": "",  # set by caller
        "date": date_str, "close": close, "rsi": rsi, "macd_hist": macd_hist,
        "trend": trend_items, "momentum": momentum_items, "volume": volume_items,
        "volatility": volatility_items, "regime": regime_items,
        "changes": changes, "df": df,
        # Previous day comparison
        "prev_close": prev_close, "prev_rsi": prev_rsi, "prev_macd_hist": prev_macd_hist,
        "prev_ema20": prev_ema20, "prev_ema50": prev_ema50, "prev_ema200": prev_ema200,
        "prev_st_dir": prev_st_dir, "prev_cmf": prev_cmf, "prev_atr": prev_atr,
        "prev_norm_atr": prev_norm_atr, "prev_roc": prev_rroc, "prev_regime": prev_regime,
        "prev_volume": prev_volume, "price_chg": price_chg, "price_chg_pct": price_chg_pct,
        # Multi-period price change
        "price_chg_periods": price_chg_periods,
    }


BENCHMARK_TICKER = "^FTSE"
TICKER_LIST = BASE_DIR / "config" / "ticker_list.csv"

_ticker_info_cache = None


def _load_ticker_info():
    """Load ticker list and return dict mapping ticker -> company name."""
    global _ticker_info_cache
    if _ticker_info_cache is not None:
        return _ticker_info_cache
    info = {}
    if TICKER_LIST.exists():
        df = pd.read_csv(TICKER_LIST)
        for _, row in df.iterrows():
            ticker = str(row["Ticker"]).strip()
            company = str(row["Company"]).strip()
            info[ticker] = company
    _ticker_info_cache = info
    return info


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
    """Build 4 Plotly figures per ticker, showing the past 1 year of data."""
    df = df.sort_values("Date").reset_index(drop=True)
    # Filter to the past 1 year for charts
    one_year_ago = df["Date"].max() - pd.DateOffset(years=1)
    df = df[df["Date"] >= one_year_ago].reset_index(drop=True)
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

def _change_icon(cur, prev):
    """Return icon for value change: green up, red down, yellow flat."""
    if cur is None or prev is None:
        return "\U0001f7e9"
    if cur > prev:
        return "\u2705"
    elif cur < prev:
        return "\U0001f534"
    return "\U0001f7e9"


def _price_icon(chg_pct):
    if chg_pct is None:
        return "\U0001f7e9"
    return "\u2705" if chg_pct > 0 else "\U0001f534" if chg_pct < 0 else "\U0001f7e9"


def _period_returns_card_html(report):
    """Generate a standalone card for multi-period price changes."""
    periods = report.get("price_chg_periods", {})
    if not periods:
        return ""

    benchmark_periods = report.get("benchmark_periods")

    header_labels = []
    ticker_cells = []
    bench_cells = []
    alpha_cells = []
    for label in ["1Y", "6M", "3M", "1M"]:
        header_labels.append(f"<th style='text-align:center;padding:6px;color:#333'>{label}</th>")

        # Ticker return
        val = periods.get(label)
        if val is None:
            ticker_cells.append("<td style='color:#999;text-align:center'>N/A</td>")
        else:
            icon = _price_icon(val)
            color = "#26a69a" if val > 0 else "#ef5350" if val < 0 else "#999"
            ticker_cells.append(f"<td style='text-align:center;color:{color}'><b>{icon}</b> {val:+.2f}%</td>")

        # Benchmark return
        bench_val = benchmark_periods.get(label) if benchmark_periods else None
        if bench_val is None:
            bench_cells.append("<td style='color:#999;text-align:center'>N/A</td>")
        else:
            b_icon = _price_icon(bench_val)
            b_color = "#26a69a" if bench_val > 0 else "#ef5350" if bench_val < 0 else "#999"
            bench_cells.append(f"<td style='text-align:center;color:{b_color}'>{b_icon} {bench_val:+.2f}%</td>")

        # Alpha (ticker - benchmark)
        if val is not None and bench_val is not None:
            alpha_val = val - bench_val
            a_icon = _price_icon(alpha_val)
            a_color = "#26a69a" if alpha_val > 0 else "#ef5350" if alpha_val < 0 else "#999"
            alpha_cells.append(f"<td style='text-align:center;color:{a_color};font-weight:bold'>{a_icon} {alpha_val:+.2f}%</td>")
        else:
            alpha_cells.append("<td style='color:#999;text-align:center'>N/A</td>")

    header_row = "<tr style='border-bottom:2px solid #2196f3'><th></th>" + "".join(header_labels) + "</tr>"
    ticker_name = report.get("company_name", report.get("ticker", ""))
    ticker_row = f"<tr><td style='font-weight:bold;padding:6px'>{ticker_name} ({report.get('ticker','')})</td>{''.join(ticker_cells)}</tr>"
    bench_row = f"<tr><td style='font-weight:bold;padding:6px'>FTSE 100 (Market Benchmark)</td>{''.join(bench_cells)}</tr>"
    alpha_row = f"<tr><td style='font-weight:bold;padding:6px'>Alpha (vs FTSE)</td>{''.join(alpha_cells)}</tr>"

    return f"""
<div class="card" style="background:linear-gradient(135deg,#f5f7fa,#e8ecf1);border-left:4px solid #2196f3">
<h3 style="margin-top:0;color:#333">Price Performance</h3>
<table style="border-collapse:collapse;width:100%">
<caption style="text-align:left;font-size:0.85em;color:#666;padding-bottom:4px;font-weight:bold">Period Returns</caption>
{header_row}
{ticker_row}
{bench_row}
{alpha_row}
</table>
</div>"""


def _summary_table_html(report):
    """Generate the first summary table with current vs previous values and icons."""
    def cell(val, d=2):
        if val is None:
            return "<td style='color:#999'>N/A</td>"
        if isinstance(val, str):
            return f"<td>{val}</td>"
        return f"<td>{val:.{d}f}</td>"

    close = report["close"]
    rsi = report["rsi"]
    macd_hist = report["macd_hist"]
    st_dir = report["trend"][1][1]  # st_bullish bool or None
    ema_trend = report["trend"][0][1]  # ema_bullish bool or None
    cmf = report["volume"][1][1]  # cmf_pos bool
    atr_pct = report["volatility"][0][2].split("%")[0].strip() if report["volatility"][0][2] and "%" in report["volatility"][0][2] else None
    roc = report["momentum"][3][1]  # roc bullish bool
    regime = report["regime"][0][2].split("(")[0].strip()  # "Bull", "Bear", "Volatile"

    # Format price change
    pchg = report.get("price_chg")
    pchg_pct = report.get("price_chg_pct")
    if pchg is not None and pchg_pct is not None:
        price_detail = f"{pchg:+.2f} ({pchg_pct:+.2f}%)"
    else:
        price_detail = f"{_fmt(close)}"

    # Format SuperTrend direction
    st_cur = "Uptrend" if st_dir == True else "Downtrend" if st_dir == False else "N/A"
    st_prev = "Uptrend" if report.get("prev_st_dir") == 1 else "Downtrend" if report.get("prev_st_dir") == 0 else "N/A"

    # Format MACD direction
    macd_cur = "Bullish" if macd_hist and macd_hist > 0 else "Bearish" if macd_hist is not None else "N/A"
    macd_prev = "Bullish" if report.get("prev_macd_hist") and report["prev_macd_hist"] > 0 else "Bearish" if report.get("prev_macd_hist") is not None else "N/A"

    # Format RSI state
    rsi_state = ""
    if rsi is not None:
        if rsi > 70:
            rsi_state = " (Overbought)"
        elif rsi < 30:
            rsi_state = " (Oversold)"
    prev_rsi_state = ""
    if report.get("prev_rsi") is not None:
        pv = report["prev_rsi"]
        if pv > 70:
            prev_rsi_state = " (Overbought)"
        elif pv < 30:
            prev_rsi_state = " (Oversold)"

    # Format EMA trend
    ema_cur = "Bullish" if ema_trend == True else "Bearish" if ema_trend == False else "N/A"
    ema_prev = "Bullish" if report.get("prev_ema20") and report.get("prev_ema50") and report.get("prev_ema200") and report["prev_ema20"] > report["prev_ema50"] > report["prev_ema200"] else "Bearish" if report.get("prev_ema20") and report.get("prev_ema50") and report.get("prev_ema200") and report["prev_ema20"] < report["prev_ema50"] < report["prev_ema200"] else "N/A"

    # Format regime
    regime_labels = {0: "Bull", 1: "Bear", 2: "Volatile"}
    regime_cur = regime
    regime_prev_label = regime_labels.get(int(report.get("prev_regime", -1)), "N/A")

    def cmp_row(label, cur_val, prev_val, cur_icon, prev_icon):
        return f"<tr><td>{label}</td>{cell(cur_val)}<td>{cur_icon}</td>{cell(prev_val)}<td>{prev_icon}</td></tr>"

    return f"""
<div class="summary-table" style="background:#fff;border-radius:8px;padding:16px;margin:12px 0;box-shadow:0 1px 3px rgba(0,0,0,0.1)">
<h3 style="margin-top:0;color:#333">Quick Summary</h3>
<table style="border-collapse:collapse;width:100%">
<thead><tr style="border-bottom:2px solid #2196f3"><th style="text-align:left;padding:8px;color:#333">Metric</th><th style="text-align:center;padding:8px;color:#333">Today</th><th style="text-align:center;padding:8px;color:#333">📊</th><th style="text-align:center;padding:8px;color:#333">Prev</th><th style="text-align:center;padding:8px;color:#333">📊</th></tr></thead>
<tbody>
{cmp_row("Close", f"{_fmt(close)} ({pchg:+.2f} / {pchg_pct:+.2f}%)" if pchg_pct is not None else f"{_fmt(close)}", _fmt(report.get("prev_close")), _price_icon(report.get("price_chg_pct")), "\U0001f7e9")}
{cmp_row("RSI(14)", f"{_fmt(rsi,1)}{rsi_state}", _fmt(report.get("prev_rsi")) + prev_rsi_state, _change_icon(rsi, report.get("prev_rsi")), _change_icon(report.get("prev_rsi"), rsi))}
{cmp_row("MACD Hist", macd_cur, macd_prev, _emoji(macd_hist > 0 if macd_hist else None), _emoji(report.get("prev_macd_hist") and report["prev_macd_hist"] > 0 if report.get("prev_macd_hist") else None))}
{cmp_row("SuperTrend", st_cur, st_prev, _emoji(st_dir), _emoji(report.get("prev_st_dir") == 1))}
{cmp_row("EMA Trend", ema_cur, ema_prev, _emoji(ema_trend), _emoji(report.get("prev_ema20") and report.get("prev_ema50") and report.get("prev_ema200")))}
{cmp_row("CMF(20)", "Positive" if cmf else "Negative" if cmf is not None else "N/A", "Positive" if report.get("prev_cmf") else "Negative" if report.get("prev_cmf") is not None else "N/A", _emoji(cmf), _emoji(report.get("prev_cmf")))}
{cmp_row("Regime", regime_cur, regime_prev_label, "\U0001f7e9", "\U0001f7e9")}
{cmp_row("ROC(20)", "Positive" if roc else "Negative" if roc is not None else "N/A", "Positive" if report.get("prev_roc") else "Negative" if report.get("prev_roc") is not None else "N/A", _emoji(roc), _emoji(report.get("prev_roc")))}
</tbody>
</table>
</div>"""


def _card_html(report):
    """Generate HTML for a single ticker summary card."""
    summary_html = _summary_table_html(report)

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
{summary_html}
<table>{trend_html}{mom_html}{vol_html}{vola_html}{reg_html}</table>
</div>"""


def generate_ticker_html(report):
    """Generate a single HTML report for one ticker."""
    card_html = _card_html(report)
    period_card_html = _period_returns_card_html(report)

    figs = build_charts(report["ticker"], report["df"])
    charts = ""
    for i, fig in enumerate(figs):
        charts += f'<div class="chart-container"><h4>{["Price (OHLC+EMA)", "Volume + OBV", "MACD", "RSI + Bollinger"][i]}</h4>'
        charts += fig.to_html(full_html=False, include_plotlyjs=False, config={"displayModeBar": False})
        charts += "</div>"

    display_name = f"{report.get('company_name', report['ticker'])} ({report['ticker']})"
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{display_name} Market Analysis</title>
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
<h1>{display_name} Market Analysis</h1>
{period_card_html}
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

    # Load benchmark (FTSE) once
    benchmark_periods = None
    if BENCHMARK_TICKER in discover_tickers():
        print(f"Loading benchmark {BENCHMARK_TICKER}...")
        bench_df = load_ticker(BENCHMARK_TICKER)
        benchmark_periods = _price_change_pct(bench_df)
        print(f"  Benchmark 1Y: {benchmark_periods.get('1Y')}")

    ticker_info = _load_ticker_info()
    tickers = discover_tickers(args.tickers)
    reports = []
    for t in tickers:
        print(f"Analysing {t}...")
        df = load_ticker(t)
        r = analyse_ticker(df)
        r["ticker"] = t
        r["company_name"] = ticker_info.get(t, t)
        r["benchmark_periods"] = benchmark_periods
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
