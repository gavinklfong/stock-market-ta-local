#!/usr/bin/env python3
"""VUKG.L Exit Criteria Optimization"""
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

df = pd.read_csv("data/analysis-data/VUKG.L.csv")
df["Date"] = pd.to_datetime(df["Date"])
df = df.set_index("Date")
df = df.dropna(subset=["Close", "High", "Low"])
close = df["Close"]

print(f"Data range: {close.index.min().date()} to {close.index.max().date()} ({len(close)} days)")
bh_ret = (close.iloc[-1] / close.iloc[0] - 1) * 100
print(f"Buy & Hold return: {bh_ret:.1f}%")

# === Entry Strategies ===
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

def signal_goldencross(df):
    return (
        (df["ta_ema20"] > df["ta_ema50"])
        & (df["ta_ema50"] > df["ta_ema200"])
        & (df["ta_supertrend_direction"] == 1)
        & (df["ta_rsi14"] > 50)
        & (df["ta_macd_line"] > df["ta_macd_signal"])
    )

def signal_supertrend_ema(df):
    st = df["ta_supertrend_direction"]
    flip_up = (st == 1) & (st.shift(1) == -1)
    return flip_up & (df["ta_ema20"] > df["ta_ema50"]) & (df["ta_rsi14"] > 40)

def signal_adx_momentum(df):
    return (
        (df["ta_adx14"] > 25)
        & (df["ta_plus_di14"] > df["ta_minus_di14"])
        & (df["ta_rsi14"] > 50)
        & (df["ta_macd_line"] > df["ta_macd_signal"])
    )

def signal_bos_breakout(df):
    return (
        (df["ta_bos"].fillna(0).astype(int) == 1)
        & (df["Close"] > df["ta_donchian_upper"])
    )

# === Exit Strategies ===
def exit_supertrend_flip(d):
    return d["ta_supertrend_direction"] == -1

def exit_close_below_ema50(d):
    return d["Close"] < d["ta_ema50"]

def exit_close_below_ema20(d):
    return d["Close"] < d["ta_ema20"]

def exit_ema20_below_50(d):
    return d["ta_ema20"] < d["ta_ema50"]

def exit_macd_cross(d):
    return d["ta_macd_line"] < d["ta_macd_signal"]

def exit_cmf_negative(d):
    return d["ta_cmf"] < 0

def exit_bb_lower(d):
    return d["Close"] < d["ta_bband_lower"]

def exit_adx_decline(d):
    return d["ta_adx14"] < 15

def exit_combo_early(d):
    return (d["ta_supertrend_direction"] == -1) | (d["ta_rsi14"] > 75)

def exit_combo_defensive(d):
    return (d["ta_supertrend_direction"] == -1) | (d["Close"] < d["ta_ema20"]) | (d["ta_rsi14"] < 40)

def exit_combo_strict(d):
    return (d["ta_supertrend_direction"] == -1) | (d["ta_ema20"] < d["ta_ema50"]) | (d["ta_rsi14"] < 45)

# === Backtest Engine ===
def run_backtest(close, entries, exits, df=None):
    # Entry functions take the full DataFrame (need TA columns), not just close
    if callable(entries) and df is not None:
        entries = entries(df)
    entries = pd.Series(entries).reindex(close.index).fillna(False)
    
    if exits is None:
        exits = pd.Series(False, index=close.index)
    elif callable(exits):
        exits = exits(df)
    exits = pd.Series(exits).reindex(close.index).fillna(False)
    
    in_pos = False
    entry_price = 0.0
    entry_date = None
    trades = []
    
    for i in range(len(close)):
        price = close.iloc[i]
        if not in_pos and entries.iloc[i]:
            in_pos = True
            entry_price = price
            entry_date = close.index[i]
        elif in_pos and exits.iloc[i]:
            ret = price * 0.999 / entry_price - 1
            hold_days = (close.index[i] - entry_date).days
            trades.append({"return": ret, "hold_days": hold_days, "date_exit": close.index[i]})
            in_pos = False
    
    if in_pos:
        ret = close.iloc[-1] / entry_price - 1
        trades.append({"return": ret, "hold_days": (close.index[-1] - entry_date).days, "date_exit": close.index[-1]})
    
    if not trades:
        return None
    return {"trades": trades, "entry_count": int(entries.sum())}

def calc_metrics(bt, close, name=""):
    if bt is None:
        return None
    trades = bt["trades"]
    n = len(trades)
    returns = np.array([t["return"] for t in trades])
    
    wins = returns[returns > 0]
    losses = returns[returns <= 0]
    win_rate = len(wins) / n if n > 0 else 0
    
    total_return = float(np.prod(1 + returns) - 1)
    avg_win = float(np.mean(wins)) if len(wins) > 0 else 0
    avg_loss = float(np.mean(losses)) if len(losses) > 0 else 0
    
    total_win = float(np.sum(wins))
    total_loss = float(np.sum(losses))
    profit_factor = total_win / abs(total_loss) if total_loss != 0 else float("inf")
    
    cum_returns = np.cumprod(1 + returns)
    peak = np.maximum.accumulate(cum_returns)
    dd = (cum_returns - peak) / peak
    max_dd = float(abs(dd.min())) if len(dd) > 0 else 0
    
    avg_hold = float(np.mean([t["hold_days"] for t in trades]))
    
    sharpe = 0
    if len(returns) > 1:
        sharpe = float((np.mean(returns) * 252 - 0.02) / (np.std(returns, ddof=1) * np.sqrt(252)))
    
    n_days = len(close)
    ann_return = (1 + total_return) ** (252 / n_days) - 1 if n_days > 0 else 0
    calmar = ann_return / max_dd if max_dd > 0 else 0
    
    best_trade = float(np.max(returns)) if len(returns) > 0 else 0
    worst_trade = float(np.min(returns)) if len(returns) > 0 else 0
    
    max_consec = 0
    consec = 0
    for r in returns:
        if r <= 0:
            consec += 1
            max_consec = max(max_consec, consec)
        else:
            consec = 0
    
    loss_ratio = abs(avg_loss) if avg_loss != 0 else 0.001
    win_loss_ratio = avg_win / loss_ratio if avg_loss != 0 else float("inf")
    
    return {
        "name": name, "trades": n, "win_rate": win_rate,
        "total_return": total_return, "ann_return": ann_return,
        "sharpe": sharpe, "calmar": calmar, "max_dd": max_dd,
        "avg_win": avg_win, "avg_loss": avg_loss, "profit_factor": profit_factor,
        "win_loss_ratio": win_loss_ratio,
        "best_trade": best_trade, "worst_trade": worst_trade,
        "avg_hold_days": avg_hold, "max_consec_losses": max_consec,
    }

# === Main ===
print("\n" + "=" * 160)
print("VUKG.L EXIT CRITERIA OPTIMIZATION")
print(f"Period: {close.index.min().date()} to {close.index.max().date()} ({len(close)} days)")
print(f"Buy & Hold: {bh_ret:.1f}%")
print("=" * 160)

entry_names = ["Score 3+", "Score 4+", "Golden Cross", "SuperTrend+EMA", "ADX Momentum", "BOS Breakout"]
entry_fns = [
    (lambda d, ms=3: signal_score(d, ms)),
    (lambda d, ms=4: signal_score(d, ms)),
    signal_goldencross,
    signal_supertrend_ema,
    signal_adx_momentum,
    signal_bos_breakout,
]

exit_defs = [
    ("No Filter", None),
    ("ST Flip", exit_supertrend_flip),
    ("Close < EMA50", exit_close_below_ema50),
    ("Close < EMA20", exit_close_below_ema20),
    ("EMA20 < EMA50", exit_ema20_below_50),
    ("RSI > 70", lambda d: d["ta_rsi14"] > 70),
    ("RSI > 75", lambda d: d["ta_rsi14"] > 75),
    ("RSI < 40", lambda d: d["ta_rsi14"] < 40),
    ("RSI < 45", lambda d: d["ta_rsi14"] < 45),
    ("MACD Cross Down", exit_macd_cross),
    ("CMF < 0", exit_cmf_negative),
    ("ADX < 15", exit_adx_decline),
    ("BB Lower Cross", exit_bb_lower),
    ("ATR Trail 2x10d", lambda d: d["Close"] < (d["High"].rolling(10).max() - 2 * d["ta_atr14"])),
    ("ATR Trail 3x10d", lambda d: d["Close"] < (d["High"].rolling(10).max() - 3 * d["ta_atr14"])),
    ("ATR Trail 4x10d", lambda d: d["Close"] < (d["High"].rolling(10).max() - 4 * d["ta_atr14"])),
    ("ATR Trail 3x20d", lambda d: d["Close"] < (d["High"].rolling(20).max() - 3 * d["ta_atr14"])),
    ("ATR Trail 4x20d", lambda d: d["Close"] < (d["High"].rolling(20).max() - 4 * d["ta_atr14"])),
    ("Donchian 20d Break", lambda d: d["Close"] < d["Low"].rolling(20).min()),
    ("ST Flip or RSI>75", exit_combo_early),
    ("ST or EMA20 or RSI<40", exit_combo_defensive),
    ("ST or EMA20<50 or RSI<45", exit_combo_strict),
]

all_results = []

for ei, (ename, efn) in enumerate(zip(entry_names, entry_fns)):
    entry_count = int(efn(df).sum())
    print(f"\n  Entry: {ename} ({entry_count} signals)")
    
    for xname, xfn in exit_defs:
        exit_sig = xfn(df) if xfn is not None else None
        bt = run_backtest(close, efn, exit_sig, df)
        if bt is None or len(bt["trades"]) < 3:
            continue
        m = calc_metrics(bt, close, f"{ename} / {xname}")
        all_results.append(m)
        print(f"    {xname}: T={m['trades']:3d} Sharpe={m['sharpe']:7.3f} MaxDD={m['max_dd']*100:5.1f}% Ret={m['total_return']*100:7.1f}%")

print(f"\n\nTotal valid results: {len(all_results)}")

# Display
def pf_str(v):
    return f"{v:.2f}" if v != float("inf") else "inf"

print("\n" + "=" * 150)
print(f"{'Strategy':<55} {'T':>3} {'WR':>6} {'Ret':>8} {'AnnR':>8} {'Sharpe':>7} {'MaxDD':>7} {'PF':>6} {'W/L':>6} {'Best':>7} {'Worst':>7} {'AvgH':>5}")
print("─" * 150)

top_sharpe = sorted([r for r in all_results if r["trades"] >= 5], key=lambda x: x["sharpe"], reverse=True)
for r in top_sharpe[:30]:
    wlr = "N/A" if r['win_loss_ratio'] == float('inf') else f"{r['win_loss_ratio']:.2f}"
    print(f"{r['name']:<55} {r['trades']:3d} {r['win_rate']*100:5.1f}% {r['total_return']*100:7.1f}% {r['ann_return']*100:7.1f}% {r['sharpe']:7.3f} {r['max_dd']*100:6.1f}% {pf_str(r['profit_factor']):6s} {wlr:6s} {r['best_trade']*100:6.1f}% {r['worst_trade']*100:6.1f}% {r['avg_hold_days']:5.0f}d")

print("\n" + "=" * 130)
print("TOP BY CALMAR RATIO")
print("=" * 130)
top_calmar = sorted([r for r in all_results if r["trades"] >= 5 and r["max_dd"] > 0], key=lambda x: x["calmar"], reverse=True)
for r in top_calmar[:15]:
    print(f"{r['name']:<55} Sharpe={r['sharpe']:6.3f} MaxDD={r['max_dd']*100:5.1f}% Calmar={r['calmar']:6.3f} Ret={r['total_return']*100:6.1f}% PF={pf_str(r['profit_factor'])}")

print("\n" + "=" * 130)
print("LOWEST DRAWDOWN WITH POSITIVE RETURN")
print("=" * 130)
low_dd = sorted([r for r in all_results if r["trades"] >= 5 and r["total_return"] > 0], key=lambda x: x["max_dd"])
for r in low_dd[:15]:
    print(f"{r['name']:<55} Sharpe={r['sharpe']:6.3f} MaxDD={r['max_dd']*100:5.1f}% Calmar={r['calmar']:6.3f} Ret={r['total_return']*100:6.1f}% PF={pf_str(r['profit_factor'])}")

# Summary
print("\n" + "=" * 130)
print("BEST EXIT PER ENTRY (by Sharpe, min 5 trades)")
print("=" * 130)
for ename in entry_names:
    sub = [r for r in all_results if r["name"].startswith(ename) and r["trades"] >= 5]
    if sub:
        best = max(sub, key=lambda x: x["sharpe"])
        print(f"\n  {ename}:")
        print(f"    Exit: {best['name'].replace(ename + ' / ', '')}")
        print(f"    Sharpe={best['sharpe']:.3f}, Calmar={best['calmar']:.3f}, MaxDD={best['max_dd']*100:.1f}%, AnnRet={best['ann_return']*100:.1f}%, Ret={best['total_return']*100:.1f}%, T={best['trades']}, WR={best['win_rate']*100:.1f}%, PF={pf_str(best['profit_factor'])}")
