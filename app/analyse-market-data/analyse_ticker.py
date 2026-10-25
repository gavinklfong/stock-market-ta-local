#!/usr/bin/env python
"""Analyse market data and generate interactive HTML reports."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ANALYSIS_DIR = BASE_DIR / "data" / "analysis-data"
DEFAULT_OUTPUT_DIR = BASE_DIR / "data" / "reports" / "ticker-overview"
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


def _price_icon(chg_pct):
    """Return emoji for price change: green=up, red=down, yellow=neutral/unknown."""
    if chg_pct is None:
        return "\U0001f7e9"
    return "\u2705" if chg_pct > 0 else "\U0001f534" if chg_pct < 0 else "\U0001f7e9"


def _fmt(val, d=2):
    if val is None:
        return "N/A"
    return f"{float(val):.{d}f}" if isinstance(val, (float, int)) else str(val)


def _metric_color(val, signal):
    """Return a <span> with the value color-coded: green=buy, red=sell, black=neutral."""
    if signal is True:
        color = "#26a69a"
    elif signal is False:
        color = "#ef5350"
    else:
        color = "#1e293b"
    return f'<span style="color:{color};font-weight:600">{val}</span>'


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

def _common_analysis(df):
    """Shared analysis logic for both ticker and benchmark.

    Returns a dict with keys: date, close, trend, momentum, volume,
    volatility, regime, structure, prev_close, prev_rsi, prev_macd_hist,
    prev_ema20, prev_ema50, prev_ema200, prev_st_dir, prev_cmf, prev_atr,
    prev_norm_atr, prev_roc, prev_regime, prev_volume, price_chg,
    price_chg_pct, price_chg_periods.
    """
    df = df.sort_values("Date").reset_index(drop=True)
    L = df.iloc[-1]
    P = df.iloc[-2] if len(df) > 1 else L

    close = _v(L, "Close") or _v(L, "Adj Close")
    date_str = str(L.get("Date", "N/A"))[:10]

    # Trend
    ema20, ema50, ema200 = _v(L, "ta_ema20"), _v(L, "ta_ema50"), _v(L, "ta_ema200")
    st_dir = _v(L, "ta_supertrend_direction")
    ma20_slope = _v(L, "ta_ma20_slope")
    ma50_slope = _v(L, "ta_ma50_slope")
    donch_upper = _v(L, "ta_donchian_upper")
    donch_lower = _v(L, "ta_donchian_lower")
    kelt_upper = _v(L, "ta_keltner_upper")
    kelt_lower = _v(L, "ta_keltner_lower")
    aroon_up = _v(L, "ta_aroon_up")
    aroon_down = _v(L, "ta_aroon_down")
    price_above_ema20 = close > ema20 if close and ema20 else None
    ema_bullish = ema20 and ema50 and ema200 and ema20 > ema50 > ema200
    ema_bearish = ema20 and ema50 and ema200 and ema20 < ema50 < ema200
    st_bullish = st_dir == 1 if st_dir is not None else None
    donch_breakout = close > donch_upper if close and donch_upper else None
    donch_breakdown = close < donch_lower if close and donch_lower else None
    kelt_breakout = close > kelt_upper if close and kelt_upper else None
    kelt_breakdown = close < kelt_lower if close and kelt_lower else None
    aroon_bullish = (aroon_up and aroon_down and aroon_up > aroon_down) if aroon_up and aroon_down else None
    trend_items = [
        ("EMA20 > EMA50 > EMA200", ema_bullish, f"20:{_fmt(ema20)} > 50:{_fmt(ema50)} > 200:{_fmt(ema200)} ({'Bearish' if ema_bearish else 'Bullish' if ema_bullish else ''})"),
        ("SuperTrend", st_bullish, "Uptrend" if st_bullish == True else "Downtrend" if st_bullish == False else "N/A"),
        ("Price vs EMA20", price_above_ema20, f"Close:{_fmt(close)} vs EMA20:{_fmt(ema20)} ({'Above' if price_above_ema20 else 'Below' if price_above_ema20 is False else 'N/A'})"),
        ("MA20 Slope", ma20_slope is not None, f"{_fmt(ma20_slope,2)}% ({'Increasing' if ma20_slope > 0 else 'Decreasing' if ma20_slope is not None else 'N/A'})"),
        ("MA50 Slope", ma50_slope is not None, f"{_fmt(ma50_slope,2)}% ({'Increasing' if ma50_slope > 0 else 'Decreasing' if ma50_slope is not None else 'N/A'})"),
        ("Donchian Breakout", donch_breakout, "Yes" if donch_breakout else "No" if donch_breakout is False else "N/A"),
        ("Donchian Breakdown", donch_breakdown, "Yes" if donch_breakdown else "No" if donch_breakdown is False else "N/A"),
        ("Keltner Breakout", kelt_breakout, "Yes" if kelt_breakout else "No" if kelt_breakout is False else "N/A"),
        ("Keltner Breakdown", kelt_breakdown, "Yes" if kelt_breakdown else "No" if kelt_breakdown is False else "N/A"),
        ("Aroon", aroon_bullish, f"Up:{_fmt(aroon_up,1)} Down:{_fmt(aroon_down,1)} ({'Bullish' if aroon_bullish else 'Bearish' if (aroon_up and aroon_down and aroon_up < aroon_down) else ''})"),
    ]

    # Momentum
    rsi = _v(L, "ta_rsi14")
    macd_hist = _v(L, "ta_macd_histogram")
    macd_line = _v(L, "ta_macd_line")
    macd_signal = _v(L, "ta_macd_signal")
    roc = _v(L, "ta_roc20")
    williams_r = _v(L, "ta_williams_r")
    rsi_overbought = rsi > 70 if rsi else None
    rsi_oversold = rsi < 30 if rsi else None
    macd_bullish = macd_hist > 0 if macd_hist else None
    macd_cross = macd_line > macd_signal if macd_line and macd_signal else None
    williams_overbought = williams_r > -20 if williams_r else None
    williams_oversold = williams_r < -80 if williams_r else None
    momentum_items = [
        ("RSI(14)", None if rsi is None else (rsi_overbought or rsi_oversold), f"{_fmt(rsi,1)}{' (Overbought)' if rsi_overbought else ' (Oversold)' if rsi_oversold else ''}"),
        ("MACD Histogram", macd_bullish, f"{_fmt(macd_hist)} ({'Positive' if macd_bullish else 'Negative' if macd_bullish is False else 'N/A'})"),
        ("MACD Cross", macd_cross, "Line > Signal" if macd_cross else "Line < Signal"),
        ("ROC(20)", None if roc is None else roc > 0, f"{_fmt(roc,1)}% ({'Positive' if roc > 0 else 'Negative' if roc is not None else 'N/A'})"),
        ("Williams %R", None if williams_r is None else (williams_overbought or williams_oversold), f"{_fmt(williams_r,1)} {' (Overbought)' if williams_overbought else ' (Oversold)' if williams_oversold else '' if williams_r is not None else ''}"),
    ]

    # Volume
    obv = _v(L, "ta_obv")
    adl = _v(L, "ta_adl")
    cmf = _v(L, "ta_cmf")
    vol = _v(L, "Volume")
    obv_5 = df["ta_obv"].iloc[-5:].tolist() if "ta_obv" in df.columns else []
    obv_rising = len(obv_5) == 5 and obv_5[-1] > obv_5[0] if obv_5 else None
    adl_5 = df["ta_adl"].iloc[-5:].tolist() if "ta_adl" in df.columns else []
    adl_rising = len(adl_5) == 5 and adl_5[-1] > adl_5[0] if adl_5 else None
    cmf_pos = cmf > 0 if cmf else None
    volume_items = [
        ("OBV Trend (5-bar)", obv_rising, f"Rising" if obv_rising else "Falling" if obv_rising is False else "N/A"),
        ("ADL Trend (5-bar)", adl_rising, f"Rising" if adl_rising else "Falling" if adl_rising is False else "N/A"),
        ("CMF(20)", cmf_pos, f"{_fmt(cmf,4)} ({'Positive' if cmf_pos else 'Negative' if cmf_pos is False else 'N/A'})"),
        ("Volume", vol is not None, f"{vol:,.0f}" if vol else "N/A"),
    ]

    # Volatility
    atr = _v(L, "ta_atr14")
    norm_atr = _v(L, "ta_normalized_atr14")
    hvol20 = _v(L, "ta_hvol20")
    parkinson_vol = _v(L, "ta_parkinson_vol")
    bb_upper = _v(L, "ta_bband_upper")
    bb_lower = _v(L, "ta_bband_lower")
    bb_middle = _v(L, "ta_bband_middle")
    bb_width = _v(L, "ta_bband_width")
    bb_pctb = _v(L, "ta_bband_pctb")
    atr_pct = norm_atr if norm_atr else None
    price_in_bb = (close > bb_lower and close < bb_upper) if close and bb_upper and bb_lower else None
    price_near_upper = close > bb_upper * 0.98 if close and bb_upper else None
    volatility_items = [
        ("ATR(14) %", atr_pct is not None, f"{_fmt(atr_pct,2)}% ({'High' if atr_pct > 2 else 'Normal' if atr_pct else 'N/A'})"),
        ("Hist. Volatility(20)", hvol20 is not None, f"{_fmt(hvol20,2)}% ({'Low' if hvol20 is not None and hvol20 < 15 else 'Normal' if hvol20 is not None else 'N/A'})"),
        ("Parkinson Vol", parkinson_vol is not None, f"{_fmt(parkinson_vol,2)}%"),
        ("Price in BB", price_in_bb, f"Inside ({_fmt(close)} vs {_fmt(bb_lower)}-{_fmt(bb_upper)})"),
        ("BB Width", bb_width is not None, f"{_fmt(bb_width,2)}%"),
        ("BB %B", bb_pctb is not None, f"{_fmt(bb_pctb,3)}"),
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

    # Market Structure
    swing_high_idx = _v(L, "ta_swing_high_idx")
    swing_low_idx = _v(L, "ta_swing_low_idx")
    hh = _v(L, "ta_hh")
    hl = _v(L, "ta_hl")
    lh = _v(L, "ta_lh")
    ll = _v(L, "ta_ll")
    bos = _v(L, "ta_bos")
    choch = _v(L, "ta_choch")
    bars_since_sh = (len(df) - 1 - int(swing_high_idx)) if swing_high_idx is not None else None
    bars_since_sl = (len(df) - 1 - int(swing_low_idx)) if swing_low_idx is not None else None
    fresh_high = bars_since_sh is not None and bars_since_sh < 5
    fresh_low = bars_since_sl is not None and bars_since_sl < 5
    aging_trend = bars_since_sh is not None and bars_since_sh > 50
    structure_items = [
        ("Swing High Index", swing_high_idx is not None, f"Bar {int(swing_high_idx)} ago ({'Fresh' if fresh_high else 'Aging' if aging_trend else 'Normal'})"),
        ("Swing Low Index", swing_low_idx is not None, f"Bar {int(swing_low_idx)} ago ({'Fresh' if fresh_low else 'Normal'})"),
        ("Higher High", hh is not None and hh == 1, "Yes" if (hh is not None and hh == 1) else "No"),
        ("Higher Low", hl is not None and hl == 1, "Yes" if (hl is not None and hl == 1) else "No"),
        ("Lower High", lh is not None and lh == 1, "Yes" if (lh is not None and lh == 1) else "No"),
        ("Lower Low", ll is not None and ll == 1, "Yes" if (ll is not None and ll == 1) else "No"),
        ("BOS", bos is not None and bos == 1, "Yes" if (bos is not None and bos == 1) else "No"),
        ("CHoCH", choch is not None and choch == 1, "Yes" if (choch is not None and choch == 1) else "No"),
    ]

    # Previous day values
    L_prev = df.iloc[-2]
    prev_close = _v(L_prev, "Close") or _v(L_prev, "Adj Close")
    prev_rsi = _v(L_prev, "ta_rsi14")
    prev_macd_hist = _v(L_prev, "ta_macd_histogram")
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

    # Previous date: additional indicators for Quick Summary
    prev_pe = _v(L_prev, "ta_pe")
    prev_eps = _v(L_prev, "ta_eps_ttm")
    prev_div_yield = _v(L_prev, "ta_div_yield")
    prev_pctb = _v(L_prev, "ta_bband_pctb")
    prev_stoch_k = _v(L_prev, "ta_stoch_k")
    prev_stoch_d = _v(L_prev, "ta_stoch_d")
    prev_rsi_pct = _v(L_prev, "ta_rsi_percentile")
    prev_adx = _v(L_prev, "ta_adx14")
    prev_cci = _v(L_prev, "ta_cci")

    # Price change
    price_chg = close - prev_close if close and prev_close else None
    price_chg_pct = (price_chg / prev_close * 100) if price_chg and prev_close else None

    # Multi-period price change
    price_chg_periods = _price_change_pct(df)

    return {
        "date": date_str, "close": close, "rsi": rsi, "macd_hist": macd_hist,
        "trend": trend_items, "momentum": momentum_items, "volume": volume_items,
        "volatility": volatility_items, "regime": regime_items, "structure": structure_items,
        "prev_close": prev_close, "prev_rsi": prev_rsi, "prev_macd_hist": prev_macd_hist,
        "prev_ema20": prev_ema20, "prev_ema50": prev_ema50, "prev_ema200": prev_ema200,
        "prev_st_dir": prev_st_dir, "prev_cmf": prev_cmf, "prev_atr": prev_atr,
        "prev_norm_atr": prev_norm_atr, "prev_roc": prev_rroc, "prev_regime": prev_regime,
        "prev_volume": prev_volume, "prev_pe": prev_pe, "prev_eps": prev_eps,
        "prev_div_yield": prev_div_yield, "prev_pctb": prev_pctb,
        "prev_stoch_k": prev_stoch_k, "prev_stoch_d": prev_stoch_d,
        "prev_rsi_pct": prev_rsi_pct, "prev_adx": prev_adx, "prev_cci": prev_cci,
        "price_chg": price_chg, "price_chg_pct": price_chg_pct,
        "price_chg_periods": price_chg_periods,
        "_df": df,  # internal: popped by callers
    }


def analyse_ticker(df):
    """Analyse a ticker's latest data and return a summary dict."""
    result = _common_analysis(df)
    df = result.pop("_df")  # restore df (added by _common_analysis)

    # Changes — unique to ticker analysis (not benchmark)
    L = df.iloc[-1]
    P = df.iloc[-2] if len(df) > 1 else L
    close = _v(L, "Close") or _v(L, "Adj Close")
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
        **result,
        "changes": changes,
        "df": df,
    }


def analyse_benchmark(df):
    """Analyse the benchmark index and return a summary dict (same structure as analyse_ticker)."""
    result = _common_analysis(df)
    df = result.pop("_df")  # drop internal key, restore df
    return {
        "ticker": "",  # set by caller
        **result,
        "changes": [],  # not applicable for benchmark
        "df": df,
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
    """Build 6 Plotly figures per ticker, showing the past 3 years of data."""
    df = df.sort_values("Date").reset_index(drop=True)
    # Filter to the past 3 years for charts
    three_years_ago = df["Date"].max() - pd.DateOffset(years=3)
    df = df[df["Date"] >= three_years_ago].reset_index(drop=True)
    dates = df["Date"].dt.strftime("%Y-%m-%d").tolist()

    # 1. OHLC + EMA
    fig1 = go.Figure(data=[go.Candlestick(
        x=dates, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        name="OHLC", increasing_line_color="#26a69a", decreasing_line_color="#ef5350"
    )])
    for col, color, label in [("ta_ema20", "#ff9800", "EMA20"), ("ta_ema50", "#2196f3", "EMA50"), ("ta_ema200", "#9c27b0", "EMA200")]:
        if col in df.columns:
            fig1.add_trace(go.Scatter(x=dates, y=df[col], mode="lines", name=label, line=dict(color=color, width=1)))
    # Bollinger Bands
    if "ta_bband_upper" in df.columns and "ta_bband_lower" in df.columns:
        fig1.add_trace(go.Scatter(x=dates, y=df["ta_bband_upper"], mode="lines", name="BB Upper", line=dict(color="#06b6d4", width=1, dash="dot")))
        fig1.add_trace(go.Scatter(x=dates, y=df["ta_bband_lower"], mode="lines", name="BB Lower", line=dict(color="#06b6d4", width=1, dash="dot"), fill="tonexty", fillcolor="rgba(6,182,212,0.05)"))
    fig1.update_layout(hovermode="x unified", height=480, margin=dict(l=50, r=20, t=30, b=40), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

    # 2. Volume + OBV + CMF
    fig2 = go.Figure()
    colors = ["#26a69a" if df["Close"].iloc[i] >= df["Open"].iloc[i] else "#ef5350" for i in range(len(df))]
    fig2.add_trace(go.Bar(x=dates, y=df["Volume"], name="Volume", marker_color=colors, yaxis="y2"))
    if "ta_obv" in df.columns:
        fig2.add_trace(go.Scatter(x=dates, y=df["ta_obv"], mode="lines", name="OBV", line=dict(color="#66bb6a", width=1.5)))
    if "ta_cmf" in df.columns:
        fig2.add_trace(go.Scatter(x=dates, y=df["ta_cmf"], mode="lines", name="CMF(20)", line=dict(color="#f59e0b", width=1.5)))
    fig2.update_layout(hovermode="x unified", height=280, margin=dict(l=50, r=20, t=10, b=40), yaxis2=dict(overlaying="y", side="left"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

    # 3. MACD
    fig3 = go.Figure()
    if all(c in df.columns for c in ["ta_macd_line", "ta_macd_signal", "ta_macd_histogram"]):
        fig3.add_trace(go.Bar(x=dates, y=df["ta_macd_histogram"], name="Histogram", marker_color=df["ta_macd_histogram"].apply(lambda x: "#26a69a" if x >= 0 else "#ef5350")))
        fig3.add_trace(go.Scatter(x=dates, y=df["ta_macd_line"], mode="lines", name="MACD", line=dict(color="#1976d2", width=1.5)))
        fig3.add_trace(go.Scatter(x=dates, y=df["ta_macd_signal"], mode="lines", name="Signal", line=dict(color="#ff9800", width=1)))
    fig3.update_layout(hovermode="x unified", height=280, margin=dict(l=50, r=20, t=10, b=40), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

    # 4. RSI + Bollinger Bands
    fig4 = go.Figure()
    if "ta_rsi14" in df.columns:
        fig4.add_trace(go.Scatter(x=dates, y=df["ta_rsi14"], mode="lines", name="RSI(14)", line=dict(color="#7b1fa2", width=1.5)))
    fig4.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5)
    fig4.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5)
    fig4.update_layout(hovermode="x unified", height=280, margin=dict(l=50, r=20, t=10, b=40), yaxis=dict(range=[0, 100]), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

    return [fig1, fig2, fig3, fig4]


def build_volatility_chart(df):
    """Build a volatility analysis chart: ATR + Historical Volatility + Bollinger Width."""
    df = df.sort_values("Date").reset_index(drop=True)
    three_years_ago = df["Date"].max() - pd.DateOffset(years=3)
    df = df[df["Date"] >= three_years_ago].reset_index(drop=True)
    dates = df["Date"].dt.strftime("%Y-%m-%d").tolist()

    fig = go.Figure()

    # ATR(14) — left axis
    if "ta_atr14" in df.columns:
        fig.add_trace(go.Scatter(
            x=dates, y=df["ta_atr14"], mode="lines", name="ATR(14)",
            line=dict(color="#f59e0b", width=2), yaxis="y"
        ))

    # Historical Volatility(20) — right axis (%)
    if "ta_hvol20" in df.columns:
        fig.add_trace(go.Scatter(
            x=dates, y=df["ta_hvol20"], mode="lines", name="Hist. Vol(20)",
            line=dict(color="#8b5cf6", width=1.5, dash="dash"), yaxis="y2"
        ))

    # Bollinger Width — right axis (%)
    if "ta_bband_width" in df.columns:
        fig.add_trace(go.Scatter(
            x=dates, y=df["ta_bband_width"], mode="lines", name="BB Width",
            line=dict(color="#06b6d4", width=1, dash="dot"), yaxis="y2"
        ))

    fig.update_layout(
        hovermode="x unified",
        height=320,
        margin=dict(l=50, r=20, t=30, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        yaxis=dict(title_text="ATR", side="left", gridcolor="#f1f5f9"),
        yaxis2=dict(title_text="Volatility %", side="right", overlaying="y", gridcolor="rgba(0,0,0,0)"),
    )
    return fig


def build_pe_chart(df):
    """Build a P/E ratio chart: P/E over time with valuation zones."""
    df = df.sort_values("Date").reset_index(drop=True)
    three_years_ago = df["Date"].max() - pd.DateOffset(years=3)
    df = df[df["Date"] >= three_years_ago].reset_index(drop=True)
    dates = df["Date"].dt.strftime("%Y-%m-%d").tolist()

    fig = go.Figure()

    # P/E ratio line
    if "ta_pe" in df.columns:
        fig.add_trace(go.Scatter(
            x=dates, y=df["ta_pe"], mode="lines", name="P/E Ratio",
            line=dict(color="#1976d2", width=2), yaxis="y"
        ))

    # Earnings per share (TTM) — right axis
    if "ta_eps_ttm" in df.columns:
        fig.add_trace(go.Scatter(
            x=dates, y=df["ta_eps_ttm"], mode="lines", name="EPS (TTM)",
            line=dict(color="#e53935", width=1.5, dash="dash"), yaxis="y2"
        ))

    # Valuation reference lines on P/E axis
    fig.add_hline(y=25, line_dash="dot", line_color="#ef5350", opacity=0.4)
    fig.add_hline(y=15, line_dash="dot", line_color="#26a69a", opacity=0.4)

    # Shaded valuation zones
    # Overvalued zone (P/E > 25)
    fig.add_hrect(y0=25, y1=df["ta_pe"].max() if "ta_pe" in df.columns and df["ta_pe"].notna().any() else 30,
                  line_width=0, fillcolor="rgba(239,83,80,0.05)", opacity=0.5)
    # Fair value zone (15-25)
    fig.add_hrect(y0=15, y1=25, line_width=0, fillcolor="rgba(255,193,7,0.05)", opacity=0.5)
    # Undervalued zone (P/E < 15)
    pe_min = df["ta_pe"].min() if "ta_pe" in df.columns and df["ta_pe"].notna().any() else 0
    fig.add_hrect(y0=pe_min, y1=15, line_width=0, fillcolor="rgba(38,166,154,0.05)", opacity=0.5)

    # Current value annotation
    if "ta_pe" in df.columns and df["ta_pe"].notna().any():
        current_pe = df["ta_pe"].iloc[-1]
        pe_label = "Overvalued" if current_pe > 25 else "Fair" if current_pe > 15 else "Undervalued"
        pe_color = "#ef5350" if current_pe > 25 else "#ffc107" if current_pe > 15 else "#26a69a"
        fig.add_annotation(
            x=dates[-1], y=current_pe, xref="x", yref="y",
            text=f"P/E: {current_pe:.1f}",
            showarrow=False, font=dict(color=pe_color, size=12, family="monospace"),
            bgcolor="rgba(255,255,255,0.92)", bordercolor=pe_color, borderwidth=1.5,
            xanchor="left", yanchor="bottom", yshift=8
        )
        fig.add_annotation(
            x=dates[-1], y=current_pe - 1.5 if current_pe > 15 else current_pe + 1.5, xref="x", yref="y",
            text=pe_label,
            showarrow=False, font=dict(color=pe_color, size=10),
            bgcolor="rgba(255,255,255,0.85)", bordercolor=pe_color, borderwidth=1,
            xanchor="left", yshift=12 if current_pe > 15 else -12
        )

    fig.update_layout(
        hovermode="x unified",
        height=320,
        margin=dict(l=50, r=20, t=30, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        yaxis=dict(title_text="P/E Ratio", side="left", gridcolor="#f1f5f9", range=[
            min(0, pe_min - 1) if "ta_pe" in df.columns and df["ta_pe"].notna().any() else 0,
            max(30, (df["ta_pe"].max() if "ta_pe" in df.columns and df["ta_pe"].notna().any() else 30) + 2)
        ]),
        yaxis2=dict(title_text="EPS", side="right", overlaying="y", gridcolor="rgba(0,0,0,0)"),
    )
    return fig


def build_structure_chart(df):
    """Build a market structure chart: swing highs/lows, S/R levels, structure events on price."""
    df = df.sort_values("Date").reset_index(drop=True)
    three_years_ago = df["Date"].max() - pd.DateOffset(years=3)
    df = df[df["Date"] >= three_years_ago].reset_index(drop=True)
    dates = df["Date"].dt.strftime("%Y-%m-%d").tolist()

    fig = go.Figure()

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=dates, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        name="OHLC", increasing_line_color="#26a69a", decreasing_line_color="#ef5350"
    ))

    # Swing highs (triangles pointing up)
    if "ta_swing_high_idx" in df.columns:
        # Mark all swing highs (where ta_structure is 1 for swing high detection)
        sh_mask = df.columns.str.startswith("ta_swing")
        if sh_mask.any():
            # Use swing_high_idx column to mark the last swing high
            sh_idx_col = df.columns.get_loc("ta_swing_high_idx") if "ta_swing_high_idx" in df.columns else None
            if sh_idx_col is not None:
                last_sh = df.iloc[-1].get("ta_swing_high_idx")
                if pd.notna(last_sh):
                    idx = int(last_sh)
                    if idx < len(df):
                        fig.add_trace(go.Scatter(
                            x=[dates[idx]], y=[df["High"].iloc[idx]],
                            mode="markers", marker=dict(symbol="triangle-up", size=10, color="#ef4444"),
                            name="Swing High", hoverinfo="text",
                            hovertext=f"Swing High<br>{dates[idx]}<br>{df['High'].iloc[idx]:.2f}"
                        ))

    # Swing lows
    if "ta_swing_low_idx" in df.columns:
        last_sl = df.iloc[-1].get("ta_swing_low_idx")
        if pd.notna(last_sl):
            idx = int(last_sl)
            if idx < len(df):
                fig.add_trace(go.Scatter(
                    x=[dates[idx]], y=[df["Low"].iloc[idx]],
                    mode="markers", marker=dict(symbol="triangle-down", size=10, color="#22c55e"),
                    name="Swing Low", hoverinfo="text",
                    hovertext=f"Swing Low<br>{dates[idx]}<br>{df['Low'].iloc[idx]:.2f}"
                ))

    # Support / Resistance levels
    if "ta_sr_resistance" in df.columns:
        sr_res = df["ta_sr_resistance"].dropna()
        for _, row in sr_res.tail(3).iterrows():
            idx = int(row.name) if hasattr(row.name, "__int__") else list(sr_res.index).index(row.name)
            if idx < len(df):
                fig.add_trace(go.Scatter(
                    x=dates[idx:idx+1], y=[row["ta_sr_resistance"]],
                    mode="lines+markers", line=dict(color="#f59e0b", width=1.5, dash="dash"),
                    marker=dict(symbol="x", size=8), name="Resistance", showlegend=True
                ))

    if "ta_sr_support" in df.columns:
        sr_sup = df["ta_sr_support"].dropna()
        for _, row in sr_sup.tail(3).iterrows():
            idx = int(row.name) if hasattr(row.name, "__int__") else list(sr_sup.index).index(row.name)
            if idx < len(df):
                fig.add_trace(go.Scatter(
                    x=dates[idx:idx+1], y=[row["ta_sr_support"]],
                    mode="lines+markers", line=dict(color="#3b82f6", width=1.5, dash="dash"),
                    marker=dict(symbol="x", size=8), name="Support", showlegend=True
                ))

    # Donchian channel
    if "ta_donchian_upper" in df.columns and "ta_donchian_lower" in df.columns:
        fig.add_trace(go.Scatter(
            x=dates, y=df["ta_donchian_upper"], mode="lines",
            line=dict(color="#a855f7", width=0.8, dash="dot"), name="Donchian Upper"
        ))
        fig.add_trace(go.Scatter(
            x=dates, y=df["ta_donchian_lower"], mode="lines",
            line=dict(color="#a855f7", width=0.8, dash="dot"), fill="tonexty",
            fillcolor="rgba(168,85,247,0.05)", name="Donchian Lower"
        ))

    fig.update_layout(
        hovermode="x unified",
        height=400,
        margin=dict(l=50, r=20, t=30, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )
    return fig


def build_comparison_chart(name, df, bench_close):
    """Build a chart comparing cumulative % price change of the stock vs FTSE 100 over the past 3 years."""
    df = df.sort_values("Date").reset_index(drop=True)
    three_years_ago = df["Date"].max() - pd.DateOffset(years=3)
    df = df[df["Date"] >= three_years_ago].reset_index(drop=True)
    dates = df["Date"].dt.strftime("%Y-%m-%d").tolist()

    # Calculate cumulative % change from the first date in the window
    first_close = df["Close"].iloc[0]
    stock_pct = (df["Close"] / first_close - 1) * 100

    # Align benchmark: trim to match df's date range
    # bench_close may be longer; take the last len(df) values to align end-to-end
    if len(bench_close) >= len(df):
        bench_aligned = pd.Series(bench_close[-len(df):])
    else:
        # Fallback: pad with NaNs if benchmark is shorter
        bench_aligned = pd.Series(bench_close).reindex(range(len(df)))
    bench_first = bench_aligned.iloc[0]
    if bench_first and bench_first > 0:
        bench_pct = (bench_aligned / bench_first - 1) * 100
    else:
        bench_pct = pd.Series([0.0] * len(df), index=df.index)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=stock_pct, mode="lines", name=name,
        line=dict(color="#2563eb", width=2)
    ))
    fig.add_trace(go.Scatter(
        x=dates, y=bench_pct, mode="lines", name="FTSE 100",
        line=dict(color="#f59e0b", width=2, dash="dash")
    ))
    # Zero line
    fig.add_hline(y=0, line_dash="dot", line_color="#94a3b8", opacity=0.5)

    # Add annotations for final values
    stock_last = float(stock_pct.iloc[-1])
    bench_last = float(bench_pct.iloc[-1])
    last_date = dates[-1]
    fig.add_annotation(
        x=last_date, y=stock_last, xref="x", yref="y",
        text=f"{name}: {stock_last:+.2f}%",
        showarrow=False, font=dict(color="#2563eb", size=11),
        bgcolor="rgba(255,255,255,0.9)", bordercolor="#2563eb", borderwidth=1,
        xanchor="left", yanchor="bottom", yshift=5
    )
    fig.add_annotation(
        x=last_date, y=bench_last, xref="x", yref="y",
        text=f"FTSE 100: {bench_last:+.2f}%",
        showarrow=False, font=dict(color="#f59e0b", size=11),
        bgcolor="rgba(255,255,255,0.9)", bordercolor="#f59e0b", borderwidth=1,
        xanchor="left", yshift=5
    )

    fig.update_layout(
        hovermode="x unified",
        height=350,
        margin=dict(l=50, r=20, t=30, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1}
    )
    fig.update_yaxes(title_text="Cumulative % Change")
    return fig


# --- HTML Generation ---

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
            ticker_cells.append("<td style='text-align:center'>N/A</td>")
        else:
            icon = _price_icon(val)
            color = "#26a69a" if val > 0 else "#ef5350" if val < 0 else "#94a3b8"
            ticker_cells.append(f"<td style='text-align:center;color:{color}'><b>{icon}</b> {val:+.2f}%</td>")

        # Benchmark return
        bench_val = benchmark_periods.get(label) if benchmark_periods else None
        if bench_val is None:
            bench_cells.append("<td style='text-align:center'>N/A</td>")
        else:
            b_icon = _price_icon(bench_val)
            b_color = "#26a69a" if bench_val > 0 else "#ef5350" if bench_val < 0 else "#94a3b8"
            bench_cells.append(f"<td style='text-align:center;color:{b_color}'>{b_icon} {bench_val:+.2f}%</td>")

        # Alpha (ticker - benchmark)
        if val is not None and bench_val is not None:
            alpha_val = val - bench_val
            a_icon = _price_icon(alpha_val)
            a_color = "#26a69a" if alpha_val > 0 else "#ef5350" if alpha_val < 0 else "#94a3b8"
            alpha_cells.append(f"<td style='text-align:center;color:{a_color};font-weight:bold'>{a_icon} {alpha_val:+.2f}%</td>")
        else:
            alpha_cells.append("<td style='text-align:center'>N/A</td>")

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
    """Generate the first summary table with current vs previous values and indicators."""
    def cell(val, d=2):
        if val is None:
            return "<td>N/A</td>"
        if isinstance(val, str):
            return f"<td>{val}</td>"
        return f"<td>{val:.{d}f}</td>"

    def _change_icon(cur_val, prev_val, d=2):
        """Format value with a directional icon if different from previous."""
        if cur_val is None:
            return "N/A"
        formatted = f"{float(cur_val):.{d}f}" if isinstance(cur_val, (float, int)) else str(cur_val)
        if prev_val is None:
            return formatted
        if not isinstance(prev_val, (float, int)):
            return formatted
        try:
            c, p = float(cur_val), float(prev_val)
        except (ValueError, TypeError):
            return formatted
        if c != p:
            arrow = "<span style='color:#26a69a;margin-right:3px'>&#9650;</span>" if c > p else "<span style='color:#ef5350;margin-right:3px'>&#9660;</span>"
            return f"{arrow}{formatted}"
        return formatted

    def _icon_prefix(cur_val, prev_val):
        """Return an HTML arrow prefix if numeric values differ."""
        if cur_val is None or prev_val is None:
            return ""
        if not isinstance(prev_val, (float, int)):
            return ""
        try:
            c, p = float(cur_val), float(prev_val)
        except (ValueError, TypeError):
            return ""
        if c == p:
            return ""
        if c > p:
            return "<span style='color:#26a69a;margin-right:3px'>&#9650;</span>"
        return "<span style='color:#ef5350;margin-right:3px'>&#9660;</span>"

    close = report["close"]
    rsi = report["rsi"]
    macd_hist = report["macd_hist"]
    st_dir = report["trend"][1][1]  # st_bullish bool or None
    ema_trend = report["trend"][0][1]  # ema_bullish bool or None
    cmf = report["volume"][2][1]  # cmf_pos bool (CMF(20) is at index 2)
    roc = report["momentum"][3][1]  # roc bullish bool (ROC(20) is at index 3)
    _df = report.get("df")
    cmf_val = _v(_df.iloc[-1], "ta_cmf") if _df is not None and "ta_cmf" in _df.columns else None
    roc_val = _v(_df.iloc[-1], "ta_roc20") if _df is not None and "ta_roc20" in _df.columns else None

    # Regime
    regime_labels = {0: "Bull", 1: "Bear", 2: "Volatile"}
    regime = report["regime"][0][2].split("(")[0].strip()

    # Format price change
    pchg = report.get("price_chg")
    pchg_pct = report.get("price_chg_pct")
    if pchg is not None and pchg_pct is not None:
        price_cur = f"{_fmt(close)} ({pchg:+.2f}, {pchg_pct:+.2f}%)"
    else:
        price_cur = f"{_fmt(close)}"

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

    regime_cur = regime
    regime_prev_label = regime_labels.get(int(report.get("prev_regime", -1)), "N/A")

    # PE / Fundamental metrics
    ta_pe = report.get("ta_pe")
    ta_eps = report.get("ta_eps_ttm")
    ta_div_yield = report.get("ta_div_yield")
    if ta_pe is not None:
        if ta_pe < 10:
            pe_label = f"{_fmt(ta_pe,1)} (Deep Value)"
        elif ta_pe < 15:
            pe_label = f"{_fmt(ta_pe,1)} (Undervalued)"
        elif ta_pe < 20:
            pe_label = f"{_fmt(ta_pe,1)} (Fair)"
        elif ta_pe < 30:
            pe_label = f"{_fmt(ta_pe,1)} (Premium)"
        else:
            pe_label = f"{_fmt(ta_pe,1)} (Overvalued)"
    else:
        pe_label = "N/A"

    # ATR % context
    ta_atr_pct = report.get("ta_atr_pct")
    if ta_atr_pct is not None:
        atr_label = f"{_fmt(ta_atr_pct,2)}% ({'High' if ta_atr_pct > 2 else 'Normal' if ta_atr_pct > 1 else 'Low'})"
    else:
        atr_label = "N/A"

    # BB %B context
    ta_pctb = report.get("ta_bband_pctb")
    if ta_pctb is not None:
        bb_label = f"{_fmt(ta_pctb,3)} ({'Near Upper' if ta_pctb > 0.9 else 'Near Lower' if ta_pctb < 0.1 else 'Middle'})"
    else:
        bb_label = "N/A"

    # Stochastic context
    ta_stoch_k = report.get("ta_stoch_k")
    ta_stoch_d = report.get("ta_stoch_d")
    if ta_stoch_k is not None and ta_stoch_d is not None:
        stoch_state = ""
        if ta_stoch_k > 80:
            stoch_state = " (Overbought)"
        elif ta_stoch_k < 20:
            stoch_state = " (Oversold)"
        stoch_label = f"%K:{_fmt(ta_stoch_k,1)} / %D:{_fmt(ta_stoch_d,1)}{stoch_state}"
    else:
        stoch_label = "N/A"

    # RSI Percentile
    ta_rsi_pct = report.get("ta_rsi_percentile")
    if ta_rsi_pct is not None:
        rsi_pct_label = f"{_fmt(ta_rsi_pct,0)}% ({'Elevated' if ta_rsi_pct > 75 else 'Depressed' if ta_rsi_pct < 25 else 'Normal'})"
    else:
        rsi_pct_label = "N/A"

    # ADX context
    ta_adx = report.get("ta_adx14")
    if ta_adx is not None:
        adx_label = f"{_fmt(ta_adx,1)} ({'Strong' if ta_adx > 25 else 'Weak' if ta_adx < 20 else 'Moderate'} trend)"
    else:
        adx_label = "N/A"

    # CCI context
    ta_cci = report.get("ta_cci")
    if ta_cci is not None:
        cci_state = ""
        if ta_cci > 100:
            cci_state = " (Overbought)"
        elif ta_cci < -100:
            cci_state = " (Oversold)"
        cci_label = f"{_fmt(ta_cci,1)}{cci_state}"
    else:
        cci_label = "N/A"

    def cmp_row(label, cur_val, prev_val):
        return f"<tr><td class='label-col'>{label}</td>{cell(cur_val, 2 if not isinstance(cur_val, str) else 0)}{cell(prev_val, 2 if not isinstance(prev_val, str) else 0)}</tr>"

    # Badge helper for full rows: label + current badge + previous badge
    def badge_row(label, cur_ok, cur_label, prev_ok, prev_label, color_class):
        cur_badge = f"<span class='badge badge-bull'>{cur_label}</span>" if cur_ok else f"<span class='badge badge-bear'>{cur_label}</span>" if cur_ok is False else ""
        prev_badge = f"<span class='badge badge-bull'>{prev_label}</span>" if prev_ok else f"<span class='badge badge-bear'>{prev_label}</span>" if prev_ok is False else ""
        return f"<tr><td class='label-col'>{label}</td><td class='metric-value'>{cur_badge}</td><td class='metric-value'>{prev_badge}</td></tr>"

    # SuperTrend previous
    st_prev = "Uptrend" if report.get("prev_st_dir") == 1 else "Downtrend" if report.get("prev_st_dir") == 0 else "N/A"
    st_prev_bullish = st_prev == "Uptrend"
    st_prev_bearish = st_prev == "Downtrend"

    # EMA previous
    ema_prev = "Bullish" if report.get("prev_ema20") and report.get("prev_ema50") and report.get("prev_ema200") and report["prev_ema20"] > report["prev_ema50"] > report["prev_ema200"] else "Bearish" if report.get("prev_ema20") and report.get("prev_ema50") and report.get("prev_ema200") and report["prev_ema20"] < report["prev_ema50"] < report["prev_ema200"] else "N/A"
    ema_prev_bullish = ema_prev == "Bullish"
    ema_prev_bearish = ema_prev == "Bearish"

    # CMF previous
    prev_cmf = report.get("prev_cmf")
    cmf_prev = "Positive" if prev_cmf else "Negative" if prev_cmf is False else "N/A"
    cmf_prev_pos = prev_cmf is True

    # ROC previous
    prev_roc = report.get("prev_roc")
    roc_prev = "Positive" if prev_roc else "Negative" if prev_roc is False else "N/A"
    roc_prev_pos = prev_roc is True

    # Previous date: additional indicators formatting
    prev_pe = report.get("prev_pe")
    prev_eps = report.get("prev_eps")
    prev_div_yield = report.get("prev_div_yield")
    prev_atr_pct = report.get("prev_norm_atr")
    prev_pctb = report.get("prev_pctb")
    prev_stoch_k = report.get("prev_stoch_k")
    prev_stoch_d = report.get("prev_stoch_d")
    prev_rsi_pct = report.get("prev_rsi_pct")
    prev_adx = report.get("prev_adx")
    prev_cci = report.get("prev_cci")

    def _prev_pe_label(pe):
        if pe is None:
            return "N/A"
        if pe < 10:
            return f"{_fmt(pe,1)} (Deep Value)"
        elif pe < 15:
            return f"{_fmt(pe,1)} (Undervalued)"
        elif pe < 20:
            return f"{_fmt(pe,1)} (Fair)"
        elif pe < 30:
            return f"{_fmt(pe,1)} (Premium)"
        else:
            return f"{_fmt(pe,1)} (Overvalued)"

    def _prev_atr_label(atr):
        if atr is None:
            return "N/A"
        return f"{_fmt(atr,2)}% ({'High' if atr > 2 else 'Normal' if atr > 1 else 'Low'})"

    def _prev_bb_label(pctb):
        if pctb is None:
            return "N/A"
        return f"{_fmt(pctb,3)} ({'Near Upper' if pctb > 0.9 else 'Near Lower' if pctb < 0.1 else 'Middle'})"

    def _prev_stoch_label(k, d):
        if k is None or d is None:
            return "N/A"
        state = ""
        if k > 80:
            state = " (Overbought)"
        elif k < 20:
            state = " (Oversold)"
        return f"%K:{_fmt(k,1)} / %D:{_fmt(d,1)}{state}"

    def _prev_rsi_pct_label(pct):
        if pct is None:
            return "N/A"
        return f"{_fmt(pct,0)}% ({'Elevated' if pct > 75 else 'Depressed' if pct < 25 else 'Normal'})"

    def _prev_adx_label(adx):
        if adx is None:
            return "N/A"
        return f"{_fmt(adx,1)} ({'Strong' if adx > 25 else 'Weak' if adx < 20 else 'Moderate'} trend)"

    def _prev_cci_label(cci):
        if cci is None:
            return "N/A"
        state = ""
        if cci > 100:
            state = " (Overbought)"
        elif cci < -100:
            state = " (Oversold)"
        return f"{_fmt(cci,1)}{state}"

    def _delta_label(cur, prev, d=2):
        """Format delta from previous: (delta, delta_pct%)."""
        if cur is None or prev is None:
            return ""
        c, p = float(cur), float(prev)
        delta = c - p
        delta_pct = (delta / p * 100) if p != 0 else 0
        return f"({delta:+.{d}f}, {delta_pct:+.2f}%)"

    # Regime numeric values for comparison
    _regime_map = {"Bull": 0, "Bear": 1, "Volatile": 2}
    _regime_num = _regime_map.get(regime_cur, 0)
    _prev_regime_num = int(report.get("prev_regime", -1))

    # Tooltip descriptions for Quick Summary labels
    _tooltip = {
        "Close": "Current closing price of the stock",
        "RSI(14)": "Relative Strength Index (14-period) — measures speed and magnitude of recent price changes. >70 = overbought, <30 = oversold",
        "MACD Histogram": "MACD line minus signal line — shows momentum convergence/divergence. Positive = bullish momentum",
        "SuperTrend": "SuperTrend indicator — +1 = uptrend, −1 = downtrend. Based on ATR multipliers",
        "EMA Trend": "EMA alignment trend — Bullish when EMA20 > EMA50 > EMA200, Bearish when EMA20 < EMA50 < EMA200",
        "CMF(20)": "Chaikin Money Flow (20-period) — measures buying/selling pressure. Positive = accumulation, Negative = distribution",
        "Regime": "HMM market regime — Bull (low vol, rising), Bear (low vol, falling), Volatile (high vol, unpredictable)",
        "ROC(20)": "Rate of Change (20-period) — percentage change over 20 days. Positive = price increased",
        "P/E Ratio": "Price-to-Earnings Ratio — current price divided by earnings per share",
        "EPS (TTM)": "Earnings Per Share (Trailing Twelve Months)",
        "Div Yield": "Dividend Yield — annual dividends per share as percentage of current price",
        "ATR(14) %": "Average True Range as % of price (14-period) — measures volatility. Higher = more volatile",
        "BB %B": "Bollinger Bands %B — position within bands. >1 = above upper band, <0 = below lower band, 0.5 = middle",
        "Stoch %K/%D": "Stochastic Oscillator — %K (fast) and %D (slow) lines. >80 = overbought, <20 = oversold",
        "RSI Percentile": "RSI percentile rank over 20-day lookback — shows where current RSI falls in recent range",
        "ADX(14)": "Average Directional Index (14-period) — trend strength. >25 = strong, <20 = weak trend",
        "CCI(20)": "Commodity Channel Index (20-period) — measures current price vs statistical average. >100 = overbought, <-100 = oversold",
    }

    # Pre-compute badge HTML to avoid nested f-string issues
    st_badge_html = (f'<span class="badge-bull">{st_cur}</span>' if st_dir
                     else f'<span class="badge-bear">{st_cur}</span>' if st_dir is not None else '')
    _prev_ema_bullish = (report.get("prev_ema20") and report.get("prev_ema50") and report.get("prev_ema200")
                         and report["prev_ema20"] > report["prev_ema50"] > report["prev_ema200"])
    _prev_ema_bearish = (report.get("prev_ema20") and report.get("prev_ema50") and report.get("prev_ema200")
                         and report["prev_ema20"] < report["prev_ema50"] < report["prev_ema200"])
    ema_badge_html = (f'<span class="badge-bull">{ema_cur}</span>' if ema_trend
                      else f'<span class="badge-bear">{ema_cur}</span>' if ema_trend is not None else '')

    return f"""
<div class="summary-table" style="background:#fff;border-radius:12px;padding:20px;margin:0 0 20px;box-shadow:0 1px 4px rgba(0,0,0,0.06);border:1px solid #e5e7eb">
<h3 style="margin:0 0 16px;font-size:1.05rem;color:#1e293b;display:flex;align-items:center;gap:8px"><span>📋</span> Quick Summary</h3>
<div class="signal-bar" style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px;padding:12px;background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0">
<span style="font-weight:600;color:#64748b;font-size:0.85rem;margin-right:4px;">Signals:</span>
{_signal_badges(st_cur, macd_cur, roc, cmf)}
</div>
<table>
<thead>
<tr><th style="text-align:left;padding:8px 12px;font-weight:600;color:#64748b;border-bottom:2px solid #e2e8f0"></th><th style="text-align:center;padding:8px 12px;font-weight:600;color:#64748b;border-bottom:2px solid #e2e8f0">Current</th><th style="text-align:center;padding:8px 12px;font-weight:600;color:#64748b;border-bottom:2px solid #e2e8f0">Previous Date</th></tr>
</thead>
<tbody>
<tr><td class="label-col" title="{_tooltip['Close']}">Close</td><td>{_icon_prefix(close, report.get("prev_close"))}{price_cur}</td><td>{_fmt(report.get("prev_close"))}</td></tr>
<tr><td class="label-col" title="{_tooltip['RSI(14)']}">RSI(14)</td><td>{_icon_prefix(rsi, report.get("prev_rsi"))}{_fmt(rsi, 1)} {_delta_label(rsi, report.get("prev_rsi"), 0)}{rsi_state}</td><td>{_fmt(report.get("prev_rsi"), 1)}{prev_rsi_state}</td></tr>
<tr><td class="label-col" title="{_tooltip['MACD Histogram']}">MACD Histogram</td><td>{_icon_prefix(macd_hist, report.get("prev_macd_hist"))}{_fmt(macd_hist)} {_delta_label(macd_hist, report.get("prev_macd_hist"))} ({macd_cur})</td><td>{macd_prev}</td></tr>
<tr><td class="label-col" title="{_tooltip['SuperTrend']}">SuperTrend</td><td class="metric-value">{_icon_prefix(st_dir, report.get("prev_st_dir"))}{st_badge_html}</td><td class="metric-value">{st_prev}</td></tr>
<tr><td class="label-col" title="{_tooltip['EMA Trend']}">EMA Trend</td><td class="metric-value">{_icon_prefix(ema_trend, _prev_ema_bullish or _prev_ema_bearish or None)}{ema_badge_html}</td><td class="metric-value">{ema_prev}</td></tr>
<tr><td class="label-col" title="{_tooltip['CMF(20)']}">CMF(20)</td><td class="metric-value">{_icon_prefix(cmf_val, report.get("prev_cmf"))}{_fmt(cmf_val, 3)} {_delta_label(cmf_val, report.get("prev_cmf"), 3)} ({'Positive' if cmf else 'Negative'})</td><td class="metric-value">{_fmt(report.get("prev_cmf"), 3)} ({'Positive' if report.get("prev_cmf") else 'Negative'})</td></tr>
<tr><td class="label-col" title="{_tooltip['Regime']}">Regime</td><td class="metric-value">{_icon_prefix(_regime_num, _prev_regime_num)}{regime_cur}</td><td class="metric-value">{regime_prev_label}</td></tr>
<tr><td class="label-col" title="{_tooltip['ROC(20)']}">ROC(20)</td><td class="metric-value">{_icon_prefix(roc_val, report.get("prev_roc"))}{_fmt(roc_val, 1)} {_delta_label(roc_val, report.get("prev_roc"), 1)} ({'Positive' if roc else 'Negative'})</td><td class="metric-value">{_fmt(report.get("prev_roc"), 1)} ({'Positive' if report.get("prev_roc") else 'Negative'})</td></tr>
<tr><td class="label-col" title="{_tooltip['P/E Ratio']}">P/E Ratio</td><td>{_icon_prefix(ta_pe, prev_pe)}{f'{_fmt(ta_pe, 1)} {_delta_label(ta_pe, prev_pe)} ({pe_label})' if ta_pe else 'N/A'}</td><td>{_prev_pe_label(prev_pe)}</td></tr>
<tr><td class="label-col" title="{_tooltip['EPS (TTM)']}">EPS (TTM)</td><td>{_icon_prefix(ta_eps, prev_eps)}{f'{_fmt(ta_eps, 4)} {_delta_label(ta_eps, prev_eps, 4)}' if ta_eps else 'N/A'}</td><td>{_fmt(prev_eps, 4) if prev_eps else 'N/A'}</td></tr>
<tr><td class="label-col" title="{_tooltip['Div Yield']}">Div Yield</td><td>{_icon_prefix(ta_div_yield, prev_div_yield)}{f'{_fmt(ta_div_yield, 2)} {_delta_label(ta_div_yield, prev_div_yield, 2)}%' if ta_div_yield else 'N/A'}</td><td>{_fmt(prev_div_yield, 2) if prev_div_yield else 'N/A'}%</td></tr>
<tr><td class="label-col" title="{_tooltip['ATR(14) %']}">ATR(14) %</td><td>{_icon_prefix(ta_atr_pct, prev_atr_pct)}{_fmt(ta_atr_pct, 2)} {_delta_label(ta_atr_pct, prev_atr_pct, 2)}</td><td>{_prev_atr_label(prev_atr_pct)}</td></tr>
<tr><td class="label-col" title="{_tooltip['BB %B']}">BB %B</td><td>{_icon_prefix(ta_pctb, prev_pctb)}{_fmt(ta_pctb, 3)} {_delta_label(ta_pctb, prev_pctb, 3)}</td><td>{_prev_bb_label(prev_pctb)}</td></tr>
<tr><td class="label-col" title="{_tooltip['Stoch %K/%D']}">Stoch %K/%D</td><td>{_icon_prefix(ta_stoch_k, prev_stoch_k)}{_fmt(ta_stoch_k, 1)} {_delta_label(ta_stoch_k, prev_stoch_k, 1)} ({stoch_label})</td><td>{_prev_stoch_label(prev_stoch_k, prev_stoch_d)}</td></tr>
<tr><td class="label-col" title="{_tooltip['RSI Percentile']}">RSI Percentile</td><td>{_icon_prefix(ta_rsi_pct, prev_rsi_pct)}{_fmt(ta_rsi_pct, 0)} {_delta_label(ta_rsi_pct, prev_rsi_pct, 0)}%</td><td>{_prev_rsi_pct_label(prev_rsi_pct)}</td></tr>
<tr><td class="label-col" title="{_tooltip['ADX(14)']}">ADX(14)</td><td>{_icon_prefix(ta_adx, prev_adx)}{_fmt(ta_adx, 1)} {_delta_label(ta_adx, prev_adx, 1)}</td><td>{_prev_adx_label(prev_adx)}</td></tr>
<tr><td class="label-col" title="{_tooltip['CCI(20)']}">CCI(20)</td><td>{_icon_prefix(ta_cci, prev_cci)}{_fmt(ta_cci, 1)} {_delta_label(ta_cci, prev_cci, 1)}</td><td>{_prev_cci_label(prev_cci)}</td></tr>
</tbody>
</table>
</div>"""


def _signal_badges(st_cur, macd_cur, roc, cmf):
    """Generate signal badge HTML for current market signals."""
    badges = []
    # SuperTrend signal
    if st_cur == "Uptrend":
        badges.append('<span class="badge-bull" style="padding:3px 10px;border-radius:12px;font-size:0.82rem;font-weight:600">Uptrend</span>')
    elif st_cur == "Downtrend":
        badges.append('<span class="badge-bear" style="padding:3px 10px;border-radius:12px;font-size:0.82rem;font-weight:600">Downtrend</span>')

    # MACD signal
    if macd_cur == "Bullish":
        badges.append('<span class="badge-bull" style="padding:3px 10px;border-radius:12px;font-size:0.82rem;font-weight:600">Bullish</span>')
    elif macd_cur == "Bearish":
        badges.append('<span class="badge-bear" style="padding:3px 10px;border-radius:12px;font-size:0.82rem;font-weight:600">Bearish</span>')

    # ROC signal
    if roc is True:
        badges.append('<span class="badge-bull" style="padding:3px 10px;border-radius:12px;font-size:0.82rem;font-weight:600">Positive</span>')
    elif roc is False:
        badges.append('<span class="badge-bear" style="padding:3px 10px;border-radius:12px;font-size:0.82rem;font-weight:600">Negative</span>')

    # CMF signal
    if cmf is True:
        badges.append('<span class="badge-bull" style="padding:3px 10px;border-radius:12px;font-size:0.82rem;font-weight:600">Positive</span>')
    elif cmf is False:
        badges.append('<span class="badge-bear" style="padding:3px 10px;border-radius:12px;font-size:0.82rem;font-weight:600">Negative</span>')

    return " ".join(badges) if badges else '<span style="color:#94a3b8;font-size:0.85rem">No signals available</span>'


def _regime_bar_html(report):
    """Generate a regime probability bar visualization."""
    hmm_0 = report.get("regime")[0][2]  # e.g. "Bull (45.3/30.1/24.6)"
    if not hmm_0 or " (" not in hmm_0:
        return ""
    text_part = hmm_0.split(" (")[0]
    prob_str = hmm_0.split("(")[1].rstrip(")")
    parts = [float(x.strip()) for x in prob_str.split("/")]
    if len(parts) < 3:
        return ""
    bull_p, bear_p, vol_p = parts[0], parts[1], parts[2]
    total = bull_p + bear_p + vol_p or 1
    bull_w = bull_p / total * 100
    bear_w = bear_p / total * 100
    vol_w = vol_p / total * 100

    regime_labels = {0: "Bull", 1: "Bear", 2: "Volatile"}
    regime = report["regime"][0][2].split("(")[0].strip()
    return f"""<div class="card" style="background:#f8fafc;border-color:#e2e8f0">
<h3><span class="icon">🧭</span> Market Regime</h3>
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
    <span style="font-weight:600;color:#1e293b">{regime}</span>
    <span style="font-size:0.82rem;color:#64748b">{_fmt(bull_p,1)}% Bull / {_fmt(bear_p,1)}% Bear / {_fmt(vol_p,1)}% Vol</span>
</div>
<div class="regime-bar">
    <div class="seg seg-bull" style="width:{bull_w:.1f}%">{f'{bull_p:.0f}%' if bull_w > 12 else ''}</div>
    <div class="seg seg-bear" style="width:{bear_w:.1f}%">{f'{bear_p:.0f}%' if bear_w > 12 else ''}</div>
    <div class="seg seg-vol" style="width:{vol_w:.1f}%">{f'{vol_p:.0f}%' if vol_w > 12 else ''}</div>
</div>
<div class="regime-legend">
    <span><span class="dot" style="background:#22c55e"></span> Bull</span>
    <span><span class="dot" style="background:#ef4444"></span> Bear</span>
    <span><span class="dot" style="background:#f59e0b"></span> Volatile</span>
</div>
</div>"""



def _card_html(report):
    """Generate HTML for a single ticker summary card."""
    summary_html = _summary_table_html(report)

    def row(emoji, label, val):
        return f"<tr><td class='metric-label'>{emoji} {label}</td><td class='metric-value'>{val}</td></tr>"

    def signal_row(signal, label, val, tooltip=None):
        title_attr = f' title="{tooltip}"' if tooltip else ""
        return f"<tr><td class='metric-label'{title_attr}>{label}</td><td class='metric-value'>{signal}</td></tr>"

    # Tooltip descriptions for Trend indicators
    _trend_tooltip = {
        "EMA20 > EMA50 > EMA200": "Checks if the 20-day EMA is above the 50-day EMA, which is above the 200-day EMA — a classic bullish trend signal.",
        "SuperTrend": "A trend-following indicator based on ATR multiples. 'Uptrend' means price is above the SuperTrend line; 'Downtrend' means below.",
        "Price vs EMA20": "Whether the current close price is above or below the 20-day Exponential Moving Average.",
        "MA20 Slope": "The percentage slope of the 20-day Moving Average. Positive indicates the short-term trend is increasing; negative indicates decreasing.",
        "MA50 Slope": "The percentage slope of the 50-day Moving Average. Positive indicates the medium-term trend is increasing; negative indicates decreasing.",
        "Donchian Breakout": "Whether the price has broken above the Donchian Channel upper band (resistance breakout, often bullish).",
        "Donchian Breakdown": "Whether the price has broken below the Donchian Channel lower band (support breakdown, often bearish).",
        "Keltner Breakout": "Whether the price has broken above the Keltner Channel upper band (volatility breakout).",
        "Keltner Breakdown": "Whether the price has broken below the Keltner Channel lower band (volatility breakdown).",
        "Aroon": "The Aroon oscillator compares upward vs downward movement over the lookback period. Bullish when Aroon Up > Aroon Down.",
    }

    # Tooltip descriptions for Momentum indicators
    _momentum_tooltip = {
        "RSI(14)": "Relative Strength Index over 14 periods. Values above 70 suggest overbought conditions; below 30 suggest oversold.",
        "MACD Histogram": "MACD line minus MACD signal line. Positive indicates bullish momentum; negative indicates bearish momentum.",
        "MACD Cross": "Compares the MACD line to its signal line. 'Line > Signal' is bullish; 'Line < Signal' is bearish.",
        "ROC(20)": "Rate of Change over 20 periods — the percentage price change from 20 bars ago to the current bar.",
        "Williams %R": "Williams Percent Range. Values above -20 indicate overbought; below -80 indicate oversold conditions.",
        "CCI(20)": "Commodity Channel Index over 20 periods. Values above +100 suggest overbought; below -100 suggest oversold.",
        "TSI(25,13)": "True Strength Index using 25-period and 13-period EMA of price changes. Measures momentum with double smoothing.",
        "RSI Z-Score(14,20)": "How many standard deviations the current RSI(14) is from its 20-period average. Positive = overbought, negative = oversold.",
        "RSI Percentile(14,20)": "Where the current RSI(14) ranks within its 20-period range. 90th percentile = highest RSI in 20 bars.",
    }

    # Tooltip descriptions for Volume indicators
    _volume_tooltip = {
        "OBV Trend (5-bar)": "On-Balance Volume trend over the last 5 bars. Rising OBV suggests buying pressure; falling suggests selling pressure.",
        "ADL Trend (5-bar)": "Accumulation/Distribution Line trend over the last 5 bars. Rising suggests accumulation; falling suggests distribution.",
        "CMF(20)": "Chaikin Money Flow over 20 periods. Positive indicates buying pressure (money flowing in); negative indicates selling pressure.",
        "Volume": "Current trading volume. Compare to recent average to gauge participation level.",
        "MFI(14)": "Money Flow Index over 14 periods — volume-weighted RSI. Above 80 overbought; below 20 oversold.",
        "EMV(14)": "Ease of Movement over 14 periods. Measures how easily price moves with volume. Rising suggests easy upward movement.",
        "Volume Oscillator(14,28)": "Percentage difference between 14-period and 28-period volume EMAs. Positive = volume accelerating.",
        "Volume Z-Score(20)": "How many standard deviations current volume is from its 20-period average. High values indicate unusual volume.",
        "Volume Percentile(20)": "Where current volume ranks within its 20-period range. High percentile indicates unusually high volume.",
    }

    # Tooltip descriptions for Volatility indicators
    _volatility_tooltip = {
        "ATR(14) %": "Average True Range over 14 periods as a percentage of price. Higher values indicate greater price volatility.",
        "Hist. Volatility(20)": "Historical (realized) volatility over 20 periods — standard deviation of returns annualized. Low <15%, Normal >15%.",
        "Parkinson Vol": "Parkinson volatility estimator over 20 periods using high-low range. More efficient than close-only estimators.",
        "Price in BB": "Whether the current price is inside the Bollinger Bands (between upper and lower bands).",
        "BB Width": "Bollinger Bands width as percentage — (Upper - Lower) / Middle. Measures volatility expansion/contraction.",
        "BB %B": "Bollinger Bands %B — where price sits within the bands. 0 = at lower band, 1 = at upper band.",
        "Price near BB Upper": "Whether the current price is within 2% of the Bollinger Bands upper band.",
    }

    # Tooltip descriptions for Market Structure indicators
    _structure_tooltip = {
        "Swing High Index": "Number of bars since the most recent swing high. Under 5 = fresh high (strong trend); over 50 = aging trend.",
        "Swing Low Index": "Number of bars since the most recent swing low. Under 5 = fresh low (strong downtrend).",
        "Higher High": "Whether the latest swing high is higher than the previous swing high — a sign of an uptrend.",
        "Higher Low": "Whether the latest swing low is higher than the previous swing low — a sign of an uptrend.",
        "Lower High": "Whether the latest swing high is lower than the previous swing high — a sign of a downtrend.",
        "Lower Low": "Whether the latest swing low is lower than the previous swing low — a sign of a downtrend.",
        "BOS": "Break of Structure — confirms trend continuation when price breaks a previous swing point in the trend direction.",
        "CHoCH": "Change of Character — potential trend reversal signal when price breaks the most recent structural swing point opposite to the trend.",
    }

    trend_html = "".join(signal_row(_metric_color(item[2], item[1]), item[0], item[2], _trend_tooltip.get(item[0])) for item in report["trend"])
    mom_html = "".join(signal_row(_metric_color(item[2], item[1]), item[0], item[2], _momentum_tooltip.get(item[0])) for item in report["momentum"])
    vol_html = "".join(signal_row(_metric_color(item[2], item[1]), item[0], item[2], _volume_tooltip.get(item[0])) for item in report["volume"])
    vola_html = "".join(signal_row(_metric_color(item[2], item[1]), item[0], item[2], _volatility_tooltip.get(item[0])) for item in report["volatility"])
    reg_html = "".join(signal_row(_metric_color(item[2], item[1]), item[0], item[2], "Hidden Markov Model with 3 states: Bull, Bear, and Volatile regime probabilities.") for item in report["regime"])
    struct_html = "".join(signal_row(_metric_color(item[2], item[1]), item[0], item[2], _structure_tooltip.get(item[0])) for item in report["structure"])

    # Regime probability bar
    regime_bar_html = _regime_bar_html(report)

    changes_html = ""
    if report["changes"]:
        tags = "".join(f"<span class='tag'>{c}</span>" for c in report["changes"])
        changes_html = f'<div class="changes-banner" style="background:#fef3c7;border:1px solid #fde68a"><b>Changes Since Yesterday:</b> {tags}</div>'
    else:
        changes_html = '<div class="changes-banner" style="background:#f8fafc;border:1px solid #e2e8f0"><span class="none">No major changes since yesterday</span></div>'

    return f"""
<div class="card">
<h3>{report['ticker']} — {report['date']}</h3>
{changes_html}
{summary_html}
<div class="analysis-grid">
<div class="card">
<h3><span class="icon">📈</span> Trend</h3>
<table>{trend_html}</table>
</div>
<div class="card">
<h3><span class="icon">⚡</span> Momentum</h3>
<table>{mom_html}</table>
</div>
<div class="card">
<h3><span class="icon">📊</span> Volume</h3>
<table>{vol_html}</table>
</div>
<div class="card">
<h3><span class="icon">📉</span> Volatility</h3>
<table>{vola_html}</table>
</div>
<div class="card">
<h3><span class="icon">🏗️</span> Market Structure</h3>
<table>{struct_html}</table>
</div>
{regime_bar_html}
</div>
</div>"""


def generate_ticker_html(report):
    """Generate a single HTML report for one ticker."""
    card_html = _card_html(report)
    period_card_html = _period_returns_card_html(report)

    # Build comparison chart first (to be placed second, after OHLC)
    comp_fig = build_comparison_chart(report["ticker"], report["df"], report.get("benchmark_close", []))
    figs = build_charts(report["ticker"], report["df"])

    # Build additional charts
    vol_fig = build_volatility_chart(report["df"])
    struct_fig = build_structure_chart(report["df"])
    pe_fig = build_pe_chart(report["df"])

    # Order: OHLC, Comparison, Volume+OBV, MACD, RSI+BB, Volatility, Structure, P/E
    all_figs = [figs[0], comp_fig] + figs[1:] + [vol_fig, struct_fig, pe_fig]
    chart_titles = [
        "Price (OHLC + EMA)",
        "3Y Price Change Comparison",
        "Volume + OBV",
        "MACD",
        "RSI + Bollinger Bands",
        "Volatility (ATR + Historical Volatility)",
        "Market Structure (Swing Points, S/R, Donchian)",
        "P/E Ratio & EPS (TTM)",
    ]
    charts = ""
    for i, fig in enumerate(all_figs):
        charts += f'<div class="chart-container"><h4>{chart_titles[i]}</h4>'
        charts += fig.to_html(full_html=False, include_plotlyjs=False, config={"displayModeBar": False})
        charts += "</div>"

    display_name = f"{report.get('company_name', report['ticker'])} ({report['ticker']})"
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{display_name} Market Analysis</title>
<script src="https://cdn.plot.ly/plotly-{PLOTLY_VERSION}.min.js"></script>
<style>
/* ── Reset & Base ─────────────────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    margin: 0; padding: 0;
    background: #eef1f5;
    color: #1e293b;
    line-height: 1.5;
}}

/* ── Header ───────────────────────────────────────────────────── */
.report-header {{
    background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
    color: #fff;
    text-align: center;
    padding: 32px 20px 24px;
    margin-bottom: 24px;
}}
.report-header h1 {{ margin: 0 0 4px; font-size: 1.75rem; font-weight: 700; letter-spacing: -0.02em; }}
.report-header .meta {{ font-size: 0.95rem; opacity: 0.85; }}
.report-header .price-tag {{
    display: inline-block;
    margin-top: 10px;
    background: rgba(255,255,255,0.15);
    border-radius: 20px;
    padding: 6px 18px;
    font-size: 1.1rem;
    font-weight: 600;
}}

/* ── Container ────────────────────────────────────────────────── */
.container {{ max-width: 1100px; margin: 0 auto; padding: 0 16px 40px; }}

/* ── Cards ────────────────────────────────────────────────────── */
.card {{
    background: #fff;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    border: 1px solid #e5e7eb;
}}
.card h3 {{
    margin: 0 0 12px;
    font-size: 1.05rem;
    color: #1e293b;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.card h3 .icon {{ font-size: 1.2rem; }}

/* ── Summary Table ────────────────────────────────────────────── */
.summary-table table {{
    border-collapse: collapse;
    width: 100%;
    font-size: 0.9rem;
}}
.summary-table thead th {{
    background: #f8fafc;
    padding: 10px 12px;
    font-weight: 600;
    color: #64748b;
    text-align: center;
    border-bottom: 2px solid #e2e8f0;
}}
.summary-table tbody td {{
    padding: 10px 12px;
    text-align: center;
    border-bottom: 1px solid #f1f5f9;
}}
.summary-table tbody tr:last-child td {{ border-bottom: none; }}
.summary-table tbody tr:hover {{ background: #f8fafc; }}
.summary-table .label-col {{ text-align: left; font-weight: 600; color: #334155; cursor: help; }}
.summary-table .change-col {{ font-weight: 600; font-size: 1.05rem; min-width: 80px; }}

/* ── Badge / Status ───────────────────────────────────────────── */
.badge {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}}
.badge-bull {{ background: #dcfce7; color: #166534; }}
.badge-bear {{ background: #fee2e2; color: #991b1b; }}

/* ── Analysis Grid ────────────────────────────────────────────── */
.analysis-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 16px;
    margin-bottom: 20px;
}}
.analysis-grid .card {{ margin-bottom: 0; }}
.analysis-grid table {{ border-collapse: collapse; width: 100%; font-size: 0.88rem; }}
.analysis-grid table td {{
    padding: 7px 6px;
    border-bottom: 1px solid #f1f5f9;
    vertical-align: middle;
}}
.analysis-grid table tr:last-child td {{ border-bottom: none; }}
.analysis-grid table .metric-label {{ font-weight: 600; color: #334155; width: 40%; cursor: help; }}
.analysis-grid table .metric-value {{ color: #1e293b; text-align: right; }}

/* ── Regime Probability Bar ───────────────────────────────────── */
.regime-bar {{
    display: flex;
    height: 18px;
    border-radius: 4px;
    overflow: hidden;
    margin: 8px 0 4px;
    background: #f1f5f9;
}}
.regime-bar .seg {{
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    font-weight: 600;
    color: #fff;
    min-width: 2px;
}}
.regime-bar .seg-bull {{ background: #22c55e; }}
.regime-bar .seg-bear {{ background: #ef4444; }}
.regime-bar .seg-vol {{ background: #f59e0b; }}
.regime-legend {{ display: flex; gap: 14px; font-size: 0.78rem; color: #64748b; }}
.regime-legend span {{ display: flex; align-items: center; gap: 4px; }}
.regime-legend .dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}

/* ── Changes Banner ───────────────────────────────────────────── */
.changes-banner {{
    border-radius: 8px;
    padding: 10px 16px;
    margin-bottom: 16px;
    font-size: 0.9rem;
}}
.changes-banner .tag {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 10px;
    margin: 2px 4px 2px 0;
    font-size: 0.82rem;
    font-weight: 600;
    background: rgba(234,179,8,0.15);
    color: #92400e;
}}
.changes-banner .none {{ color: #94a3b8; font-style: italic; }}

/* ── Charts ───────────────────────────────────────────────────── */
.chart-container {{
    background: #fff;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    border: 1px solid #e5e7eb;
}}
.chart-container h4 {{
    margin: 0 0 8px;
    font-size: 0.95rem;
    color: #475569;
    font-weight: 600;
}}
.chart-container .js-plotly-plot {{ width: 100% !important; }}

/* ── Footer ───────────────────────────────────────────────────── */
.footer {{
    text-align: center;
    padding: 20px;
    font-size: 0.8rem;
    color: #94a3b8;
}}

/* ── Responsive ───────────────────────────────────────────────── */
@media (max-width: 640px) {{
    .report-header h1 {{ font-size: 1.3rem; }}
    .analysis-grid {{ grid-template-columns: 1fr; }}
    .summary-table table {{ font-size: 0.82rem; }}
}}
</style></head><body>

<div class="report-header">
    <h1>{display_name} Market Analysis</h1>
    <div class="meta">Generated automatically from market data</div>
    <div class="price-tag">{report['ticker']} — Close: {_fmt(report['close'])} ({report['date']})</div>
</div>

<div class="container">
{period_card_html}
{card_html}
{charts}

<div class="footer">Report generated on {report['date']} — Data sourced from Yahoo Finance</div>
</div>

</body></html>"""
    return html


# --- Main ---

def analyse_ticker_report(ticker_name, benchmark_periods=None, benchmark_analysis=None):
    """Analyse a single ticker and return a complete report dict.

    This is the core function used by both CLI (single ticker) and
    batch runners (e.g. run_analysis.py).
    """
    if not ANALYSIS_DIR.joinpath(f"{ticker_name}.csv").exists():
        print(f"  Error: {ticker_name}.csv not found in {ANALYSIS_DIR}")
        return None

    ticker_info = _load_ticker_info()
    df = load_ticker(ticker_name)
    r = analyse_ticker(df)
    r["ticker"] = ticker_name
    r["company_name"] = ticker_info.get(ticker_name, ticker_name)
    r["benchmark_periods"] = benchmark_periods

    # Store benchmark Close series (aligned to ticker's date range) for comparison chart
    if ticker_name == BENCHMARK_TICKER and benchmark_analysis is not None:
        r["benchmark_analysis"] = None
        r["benchmark_close"] = benchmark_analysis["df"]["Close"].values
    elif benchmark_analysis is not None:
        r["benchmark_analysis"] = benchmark_analysis
        bench_dates = benchmark_analysis["df"].set_index("Date")["Close"]
        ticker_dates = df.set_index("Date")
        aligned = bench_dates.reindex(ticker_dates.index)
        r["benchmark_close"] = aligned.values
    else:
        r["benchmark_close"] = []

    # Extract PE / fundamental data from the DataFrame
    L = df.iloc[-1]
    r["ta_pe"] = _v(L, "ta_pe")
    r["ta_eps_ttm"] = _v(L, "ta_eps_ttm")
    r["ta_div_yield"] = _v(L, "ta_div_yield")
    r["ta_div_ttm"] = _v(L, "ta_div_ttm")

    # Extract additional key metrics for the Quick Summary
    r["ta_atr_pct"] = _v(L, "ta_normalized_atr14")
    r["ta_bband_pctb"] = _v(L, "ta_bband_pctb")
    r["ta_stoch_k"] = _v(L, "ta_stoch_k")
    r["ta_stoch_d"] = _v(L, "ta_stoch_d")
    r["ta_rsi_percentile"] = _v(L, "ta_rsi_percentile")
    r["ta_adx14"] = _v(L, "ta_adx14")
    r["ta_cci"] = _v(L, "ta_cci")
    r["ta_hvol20"] = _v(L, "ta_hvol20")

    # Print quick summary
    print(f"  Close={_fmt(r['close'])}, RSI={_fmt(r['rsi'],1)}, MACD_hist={_fmt(r['macd_hist'])}")
    if r["changes"]:
        print(f"  Changes: {', '.join(r['changes'])}")

    return r


def generate_ticker_html_report(ticker_name, benchmark_periods=None, benchmark_analysis=None, output_dir=None, dry_run=False):
    """Analyse a single ticker and write its HTML report.

    Convenience wrapper that calls analyse_ticker_report and generate_ticker_html.
    """
    r = analyse_ticker_report(ticker_name, benchmark_periods, benchmark_analysis)
    if r is None:
        return False

    if dry_run:
        print(f"  Dry run: analysis for {ticker_name} shown above.")
        return True

    out = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    output_path = out / f"{r['ticker']}_analysis.html"
    html = generate_ticker_html(r)
    output_path.write_text(html, encoding="utf-8")
    print(f"Report written to {output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Analyse a single ticker and generate an HTML report")
    parser.add_argument("ticker", help="Ticker to analyse (e.g. NG.L)")
    parser.add_argument("--dry-run", action="store_true", help="Show analysis only, don't generate HTML")
    parser.add_argument("--output", default=None, help="Output directory for HTML report")
    args = parser.parse_args()

    # Load benchmark (FTSE) once
    benchmark_periods = None
    benchmark_analysis = None
    if BENCHMARK_TICKER in discover_tickers():
        print(f"Loading benchmark {BENCHMARK_TICKER}...")
        bench_df = load_ticker(BENCHMARK_TICKER)
        benchmark_periods = _price_change_pct(bench_df)
        benchmark_analysis = analyse_benchmark(bench_df)
        benchmark_analysis["ticker"] = BENCHMARK_TICKER
        benchmark_analysis["company_name"] = "FTSE 100 Index"
        print(f"  Benchmark 1Y: {benchmark_periods.get('1Y')}")
        print(f"  Benchmark Close={_fmt(benchmark_analysis['close'])}, RSI={_fmt(benchmark_analysis['rsi'],1)}, MACD_hist={_fmt(benchmark_analysis['macd_hist'])}")

    success = generate_ticker_html_report(args.ticker, benchmark_periods, benchmark_analysis, args.output, args.dry_run)
    if not success:
        parser.error(f"Failed to generate report for {args.ticker}")


if __name__ == "__main__":
    main()
