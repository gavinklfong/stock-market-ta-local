#!/usr/bin/env python3
"""
VUKG.L Deep Analysis — Trade-level detail + multi-ticker validation +
RSI threshold optimization + combo stop-loss protection.

Usage:
    python app/backtest/vukg_deep_analysis.py              # All analysis
    python app/backtest/vukg_deep_analysis.py --tickers BP.L HSBA.L  # Also test these tickers
"""
import pandas as pd
import numpy as np
import warnings
import sys

warnings.filterwarnings("ignore")

# ============================================================
# Helpers
# ============================================================

def read_ticker(ticker):
    """Read analysis-data CSV for a ticker."""
    path = f"data/analysis-data/{ticker}.csv"
    try:
        df = pd.read_csv(path)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date")
        df = df.dropna(subset=["Close", "High", "Low"])
        return df
    except FileNotFoundError:
        print(f"  WARNING: {path} not found, skipping {ticker}")
        return None


def run_backtest(close, entries, exits, df=None):
    """Run a simple position backtest. Returns dict with trade details."""
    if callable(entries) and df is not None:
        entries = entries(df)
    entries = pd.Series(entries).fillna(False)
    entries = entries.reindex(close.index)

    if exits is None:
        exits = pd.Series(False, index=close.index)
    elif callable(exits):
        exits = exits(df)
    exits = pd.Series(exits).fillna(False)
    exits = exits.reindex(close.index)

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
            ret = price * 0.999 / entry_price - 1  # 0.1% slippage on exit
            hold_days = (close.index[i] - entry_date).days
            trades.append({
                "entry_date": entry_date,
                "exit_date": close.index[i],
                "entry_price": entry_price,
                "exit_price": price,
                "return": ret,
                "hold_days": hold_days,
            })
            in_pos = False

    # Close any open position at last data point
    if in_pos:
        ret = close.iloc[-1] / entry_price - 1
        hold_days = (close.index[-1] - entry_date).days
        trades.append({
            "entry_date": entry_date,
            "exit_date": close.index[-1],
            "entry_price": entry_price,
            "exit_price": close.iloc[-1],
            "return": ret,
            "hold_days": hold_days,
            "open": True,
        })

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


def pf_str(v):
    return f"{v:.2f}" if v != float("inf") else "inf"


# ============================================================
# Entry & Exit Functions
# ============================================================

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


def signal_adx_momentum(df):
    return (
        (df["ta_adx14"] > 25)
        & (df["ta_plus_di14"] > df["ta_minus_di14"])
        & (df["ta_rsi14"] > 50)
        & (df["ta_macd_line"] > df["ta_macd_signal"])
    )


def make_rsi_exit(threshold):
    return lambda d: d["ta_rsi14"] > threshold


def make_combo_exit(rsi_threshold, use_atr=True, atr_mult=3, atr_window=10):
    """RSI > X OR ATR trailing stop."""
    def combo(d):
        rsi_exit = d["ta_rsi14"] > rsi_threshold
        if use_atr:
            atr_stop = d["Close"] < (d["High"].rolling(atr_window).max() - atr_mult * d["ta_atr14"])
            return rsi_exit | atr_stop
        return rsi_exit
    return combo


# ============================================================
# Main
# ============================================================

def main():
    args = sys.argv[1:]
    extra_tickers = [t for t in args if t.endswith(".L")]
    if "--tickers" in args:
        idx = args.index("--tickers") + 1
        extra_tickers = [a for a in args[idx:] if a.endswith(".L")]

    # Primary ticker: VUKG.L
    all_tickers = ["VUKG.L"] + extra_tickers

    entry_defs = {
        "Score 3+": lambda d: signal_score(d, 3),
        "Score 4+": lambda d: signal_score(d, 4),
        "Golden Cross": signal_goldencross,
        "ADX Momentum": signal_adx_momentum,
    }

    rsi_thresholds = [70, 72, 75, 78, 80]
    atr_combo_configs = [
        (75, True, 3, 10),
        (70, True, 3, 10),
        (75, True, 4, 10),
        (75, True, 3, 20),
    ]

    for ticker in all_tickers:
        print("=" * 120)
        print(f"  TICKER: {ticker}")
        print("=" * 120)

        df = read_ticker(ticker)
        if df is None:
            continue

        close = df["Close"]
        bh_ret = (close.iloc[-1] / close.iloc[0] - 1) * 100
        print(f"Data: {close.index.min().date()} to {close.index.max().date()} ({len(close)} days)")
        print(f"Buy & Hold: {bh_ret:.1f}%")
        print()

        # ===== Section 1: Trade-level detail for top RSI > 75 strategies =====
        print("-" * 120)
        print(f"SECTION 1: TRADE-LEVEL DETAIL — RSI > 75 Exit")
        print("-" * 120)

        for ename, efn in entry_defs.items():
            bt = run_backtest(close, efn, make_rsi_exit(75), df)
            if bt is None or len(bt["trades"]) < 3:
                continue
            m = calc_metrics(bt, close, f"{ename}")

            print(f"\n  {ename} / RSI > 75  (T={m['trades']}, WR={m['win_rate']*100:.1f}%, Sharpe={m['sharpe']:.2f}, MaxDD={m['max_dd']*100:.1f}%, Ret={m['total_return']*100:.1f}%)")
            print(f"  {'#':>3}  {'Entry Date':<12}  {'Exit Date':<12}  {'Entry $':>10}  {'Exit $':>10}  {'Ret %':>7}  {'Days':>5}")
            print(f"  {'─'*3}  {'─'*12}  {'─'*12}  {'─'*10}  {'─'*10}  {'─'*7}  {'─'*5}")

            for j, t in enumerate(bt["trades"], 1):
                open_str = " [OPEN]" if t.get("open", False) else ""
                print(f"  {j:>3}  {t['entry_date'].date()}  {t['exit_date'].date()}  {t['entry_price']:>10.2f}  {t['exit_price']:>10.2f}  {t['return']*100:6.1f}%{open_str:>7s}")

        # ===== Section 2: RSI Threshold Optimization =====
        print()
        print("-" * 120)
        print(f"SECTION 2: RSI THRESHOLD OPTIMIZATION (Score 3+ Entry)")
        print("-" * 120)

        print(f"\n  {'Threshold':>10}  {'Trades':>6}  {'WR %':>7}  {'Ret %':>8}  {'Ann %':>8}  {'Sharpe':>7}  {'Calmar':>7}  {'MaxDD %':>8}  {'PF':>6}  {'Best %':>7}  {'Worst %':>7}")
        print(f"  {'─'*10}  {'─'*6}  {'─'*7}  {'─'*8}  {'─'*8}  {'─'*7}  {'─'*7}  {'─'*8}  {'─'*6}  {'─'*7}  {'─'*7}")

        for thresh in rsi_thresholds:
            bt = run_backtest(close, lambda d: signal_score(d, 3), make_rsi_exit(thresh), df)
            if bt is None or len(bt["trades"]) < 3:
                continue
            m = calc_metrics(bt, close, f"RSI>{thresh}")
            print(f"  {thresh:>10}  {m['trades']:6d}  {m['win_rate']*100:6.1f}%  {m['total_return']*100:7.1f}%  {m['ann_return']*100:7.1f}%  {m['sharpe']:7.3f}  {m['calmar']:7.3f}  {m['max_dd']*100:7.1f}%  {pf_str(m['profit_factor']):>6s}  {m['best_trade']*100:6.1f}%  {m['worst_trade']*100:6.1f}%")

        # ===== Section 3: RSI + ATR Combo Stop-Loss =====
        print()
        print("-" * 120)
        print(f"SECTION 3: RSI + ATR COMBO STOP-LOSS (Score 3+ Entry)")
        print("-" * 120)

        print(f"\n  {'Config':<35}  {'Trades':>6}  {'WR %':>7}  {'Ret %':>8}  {'Ann %':>8}  {'Sharpe':>7}  {'Calmar':>7}  {'MaxDD %':>8}  {'PF':>6}")
        print(f"  {'─'*35}  {'─'*6}  {'─'*7}  {'─'*8}  {'─'*8}  {'─'*7}  {'─'*7}  {'─'*8}  {'─'*6}")

        for rsi_t, use_atr, a_mult, a_win in atr_combo_configs:
            xfn = make_combo_exit(rsi_t, use_atr, a_mult, a_win)
            bt = run_backtest(close, lambda d: signal_score(d, 3), xfn, df)
            if bt is None or len(bt["trades"]) < 3:
                continue
            m = calc_metrics(bt, close, f"RSI>{rsi_t}+ATR{a_mult}x{a_win}")
            label = f"RSI>{rsi_t} + ATR {a_mult}x{a_win}"
            print(f"  {label:<35}  {m['trades']:6d}  {m['win_rate']*100:6.1f}%  {m['total_return']*100:7.1f}%  {m['ann_return']*100:7.1f}%  {m['sharpe']:7.3f}  {m['calmar']:7.3f}  {m['max_dd']*100:7.1f}%  {pf_str(m['profit_factor']):>6s}")

        # Also test pure ATR trailing for comparison
        print("\n  Pure ATR Trailing (Score 3+ Entry):")
        for a_mult, a_win in [(2, 10), (3, 10), (4, 10), (2, 20), (3, 20), (4, 20)]:
            xfn = lambda d, m=a_mult, w=a_win: d["Close"] < (d["High"].rolling(w).max() - m * d["ta_atr14"])
            bt = run_backtest(close, lambda d: signal_score(d, 3), xfn, df)
            if bt is None or len(bt["trades"]) < 3:
                continue
            m = calc_metrics(bt, close, f"ATR{a_mult}x{a_win}")
            label = f"ATR {a_mult}x{a_win}"
            print(f"  {label:<35}  {m['trades']:6d}  {m['win_rate']*100:6.1f}%  {m['total_return']*100:7.1f}%  {m['ann_return']*100:7.1f}%  {m['sharpe']:7.3f}  {m['calmar']:7.3f}  {m['max_dd']*100:7.1f}%  {pf_str(m['profit_factor']):>6s}")

        # ===== Section 4: Cross-ticker comparison for RSI > 75 =====
        if len(extra_tickers) > 0:
            print()
            print("-" * 120)
            print(f"SECTION 4: MULTI-TICKER COMPARISON — RSI > 75 Exit")
            print("-" * 120)

            print(f"\n  {'Ticker':<10}  {'Period':<24}  {'B&H %':>7}  {'Entry':<15}  {'Trades':>6}  {'WR %':>7}  {'Ret %':>8}  {'Ann %':>8}  {'Sharpe':>7}  {'MaxDD %':>8}")
            print(f"  {'─'*10}  {'─'*24}  {'─'*7}  {'─'*15}  {'─'*6}  {'─'*7}  {'─'*8}  {'─'*8}  {'─'*7}  {'─'*8}")

            for ticker2 in all_tickers:
                df2 = read_ticker(ticker2)
                if df2 is None:
                    continue
                close2 = df2["Close"]
                bh2 = (close2.iloc[-1] / close2.iloc[0] - 1) * 100
                period = f"{close2.index.min().date()} - {close2.index.max().date()}"

                for ename, efn in entry_defs.items():
                    bt2 = run_backtest(close2, efn, make_rsi_exit(75), df2)
                    if bt2 is None or len(bt2["trades"]) < 3:
                        continue
                    m2 = calc_metrics(bt2, close2, f"{ename}")
                    print(f"  {ticker2:<10}  {period:<24}  {bh2:6.1f}%  {ename:<15}  {m2['trades']:6d}  {m2['win_rate']*100:6.1f}%  {m2['total_return']*100:7.1f}%  {m2['ann_return']*100:7.1f}%  {m2['sharpe']:7.3f}  {m2['max_dd']*100:7.1f}%")

    print()
    print("=" * 120)
    print("DONE")
    print("=" * 120)


if __name__ == "__main__":
    main()
