#!/usr/bin/env python
"""Complete backtest analysis helper — generates all data the investment-strategy
skill needs in one JSON output.  Works from ANY directory.

This replaces the need for the AI to write ad-hoc Python for:
  1. Loading ticker metadata and indicators
  2. Getting forward returns and yearly performance
  3. Running all built-in (and optional custom) strategies
  4. Collecting metrics for the investment report

Usage:
    # Full analysis: metadata + indicators + backtest results (recommended)
    python app/backtest/run_backtest_analysis.py NG.L

    # With custom cutoff
    python app/backtest/run_backtest_analysis.py NG.L --cutoff 2016-10-26

    # Include custom strategies
    python app/backtest/run_backtest_analysis.py NG.L --custom NG.L_custom

    # Only specific built-in group
    python app/backtest/run_backtest_analysis.py NG.L --group mean-reversion

    # Skip custom strategies
    python app/backtest/run_backtest_analysis.py NG.L --builtins-only

    # With HTML report + JSON output
    python app/backtest/run_backtest_analysis.py NG.L --json --no-report

    # Verbose per-strategy details
    python app/backtest/run_backtest_analysis.py NG.L --verbose

    # Just data snapshot without backtest
    python app/backtest/run_backtest_analysis.py NG.L --no-backtest

    # Just backtest without data snapshot
    python app/backtest/run_backtest_analysis.py NG.L --no-data

    # Forward returns statistics only
    python app/backtest/run_backtest_analysis.py NG.L --forward-returns

    # Yearly performance only
    python app/backtest/run_backtest_analysis.py NG.L --yearly
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Resolve project root from THIS script's location — works from any CWD.
_SCRIPT_DIR = Path(__file__).resolve().parent  # app/backtest/
_PROJECT_ROOT = _SCRIPT_DIR.parent.parent  # stock-market-ta-local/

# Add project root to sys.path so "app.backtest" imports work from anywhere.
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


class _NumpyEncoder(json.JSONEncoder):
    """Handle numpy types for JSON serialization."""

    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

from framework.engine import BacktestEngine, DEFAULT_CUTOFF  # noqa: E402
from framework.extensions import load_custom_strategies  # noqa: E402
from framework.metrics import summarize_table  # noqa: E402
from strategies.builtins import STRATEGIES, STRATEGY_LABELS  # noqa: E402


def _get_ticker_metadata(ticker: str) -> dict:
    """Look up company name and sector from ticker_list.csv."""
    ticker_list_path = _PROJECT_ROOT / "config" / "ticker_list.csv"
    if not ticker_list_path.exists():
        return {"company_name": None, "sector": None}

    df = pd.read_csv(ticker_list_path)
    matching = df[df["Ticker"] == ticker]
    if matching.empty:
        # Try matching without suffix
        partial = df[df["Ticker"].str.split(".").str[0] == ticker.replace(".L", "").replace(".X", "")]
        if not partial.empty:
            matching = partial.head(1)
        else:
            return {"company_name": None, "sector": None}

    row = matching.iloc[0]
    return {
        "company_name": str(row["Company"]),
        "sector": str(row["Major Industry / Sector"]),
    }


def _get_data_snapshot(df: pd.DataFrame) -> dict:
    """Extract metadata, indicators, 52-week range, forward returns from DataFrame."""
    row = df.iloc[-1]
    latest = {
        "date": str(row["Date"].date()),
        "close": float(row["Close"]) if pd.notna(row["Close"]) else None,
        "open": float(row["Open"]) if pd.notna(row["Open"]) else None,
        "high": float(row["High"]) if pd.notna(row["High"]) else None,
        "low": float(row["Low"]) if pd.notna(row["Low"]) else None,
        "volume": int(row["Volume"]) if pd.notna(row["Volume"]) else None,
    }

    # Key indicators
    indicators = {}
    indicator_cols = [
        # Trend
        "ta_ema20", "ta_ema50", "ta_ema200", "ta_supertrend_direction",
        "ta_ma20_slope", "ta_ma50_slope", "ta_ma200_slope",
        "ta_adx14", "ta_donchian_upper", "ta_donchian_lower",
        "ta_keltner_upper", "ta_keltner_lower",
        # Momentum
        "ta_rsi14", "ta_macd_line", "ta_macd_signal", "ta_macd_histogram",
        "ta_roc20", "ta_williams_r", "ta_cci", "ta_tsi",
        "ta_rsi_zscore", "ta_rsi_percentile", "ta_mfi14",
        # Return
        "ta_return_5d", "ta_return_10d", "ta_return_20d",
        "ta_performance_1m", "ta_performance_3m", "ta_performance_6m", "ta_performance_1y",
        "ta_alpha20", "ta_beta20",
        # Volatility
        "ta_atr14", "ta_normalized_atr14",
        "ta_bband_upper", "ta_bband_middle", "ta_bband_lower",
        "ta_bband_width", "ta_bband_pctb",
        # Volume
        "ta_obv", "ta_cmf", "ta_vwap", "ta_ofi",
        # Regime
        "ta_hmm_regime", "ta_hmm_regime_prob_0",
        "ta_hmm_regime_prob_1", "ta_hmm_regime_prob_2", "ta_regime_label",
        # Fundamentals
        "ta_eps_ttm", "ta_pe", "ta_div_ttm", "ta_div_yield",
    ]
    for col in indicator_cols:
        if col in df.columns and pd.notna(row.get(col)):
            val = row[col]
            indicators[col] = float(val) if isinstance(val, (int, float)) else val

    # 52-week range
    if "High" in df.columns and "Low" in df.columns:
        year_start = df["Date"] >= (df["Date"].max() - pd.DateOffset(years=1))
        year_data = df.loc[year_start]
        five2week = {
            "high_52w": float(year_data["High"].max()),
            "low_52w": float(year_data["Low"].min()),
        }
    else:
        five2week = {"high_52w": None, "low_52w": None}

    # Forward returns stats
    forward_returns = {}
    for col in ["ta_return_5d", "ta_return_10d", "ta_return_20d"]:
        if col in df.columns:
            vals = df[col].dropna()
            if len(vals) > 0:
                forward_returns[col] = {
                    "mean": round(float(vals.mean()), 4),
                    "median": round(float(vals.median()), 4),
                    "std": round(float(vals.std()), 4),
                    "min": round(float(vals.min()), 4),
                    "max": round(float(vals.max()), 4),
                    "pos_pct": round(float((vals > 0).mean() * 100), 1),
                }

    # Yearly performance
    yearly = []
    if "Date" in df.columns and "Close" in df.columns:
        df_copy = df.copy()
        df_copy["Year"] = df_copy["Date"].dt.year
        for year in sorted(df_copy["Year"].unique()):
            year_data = df_copy[df_copy["Year"] == year]
            if len(year_data) < 2:
                continue
            start_close = year_data.iloc[0]["Close"]
            end_close = year_data.iloc[-1]["Close"]
            ret = (end_close - start_close) / start_close * 100 if start_close != 0 else None
            yearly.append({
                "year": int(year),
                "start_date": str(year_data.iloc[0]["Date"].date()),
                "end_date": str(year_data.iloc[-1]["Date"].date()),
                "start_close": float(start_close),
                "end_close": float(end_close),
                "return_pct": round(float(ret), 2) if ret is not None else None,
            })

    return {
        "latest": latest,
        "indicators": indicators,
        "52week": five2week,
        "forward_returns": forward_returns,
        "yearly_performance": yearly,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Complete backtest analysis — works from any directory.",
    )
    parser.add_argument("ticker", help="Ticker symbol (e.g. NG.L, HSBA.L)")
    parser.add_argument(
        "--cutoff",
        default=None,
        help="Cutoff date YYYY-MM-DD (default: ~10 years from today)",
    )
    parser.add_argument(
        "--custom",
        nargs="+",
        default=None,
        help="Custom strategy module file names (without .py)",
    )
    parser.add_argument(
        "--custom-dir",
        default=None,
        help="Directory containing custom strategy files",
    )
    parser.add_argument(
        "--builtins-only",
        action="store_true",
        help="Run only built-in strategies (skip custom)",
    )
    parser.add_argument(
        "--group",
        default=None,
        help="Run only strategies in a group (e.g. mean-reversion)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip HTML report generation",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output",
    )

    # Mode flags (mutually exclusive subsets)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--no-backtest",
        action="store_true",
        help="Only return data snapshot (no backtest)",
    )
    mode.add_argument(
        "--no-data",
        action="store_true",
        help="Only run backtest (no data snapshot)",
    )
    mode.add_argument(
        "--forward-returns",
        action="store_true",
        help="Only output forward returns statistics",
    )
    mode.add_argument(
        "--yearly",
        action="store_true",
        help="Only output year-by-year performance",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Resolve data path
    data_dir = _PROJECT_ROOT / "data" / "analysis-data"
    data_path = data_dir / f"{args.ticker}.csv"
    if not data_path.exists():
        print(f"ERROR: Data file not found: {data_path}", file=sys.stderr)
        sys.exit(1)

    # Load data
    df = pd.read_csv(data_path, parse_dates=["Date"])
    print(f"Loaded {len(df)} rows for {args.ticker} ({df['Date'].iloc[0].date()} to {df['Date'].iloc[-1].date()})", file=sys.stderr)

    # Parse cutoff
    cutoff = None
    if args.cutoff:
        cutoff = pd.Timestamp(args.cutoff)
    else:
        cutoff = DEFAULT_CUTOFF

    # Metadata
    metadata = _get_ticker_metadata(args.ticker)

    # Mode: forward-returns only
    if args.forward_returns:
        fr_stats = {}
        for col in ["ta_return_5d", "ta_return_10d", "ta_return_20d"]:
            if col in df.columns:
                vals = df[col].dropna()
                if len(vals) > 0:
                    fr_stats[col] = {
                        "mean": round(float(vals.mean()), 4),
                        "median": round(float(vals.median()), 4),
                        "std": round(float(vals.std()), 4),
                        "min": round(float(vals.min()), 4),
                        "max": round(float(vals.max()), 4),
                        "pos_pct": round(float((vals > 0).mean() * 100), 1),
                    }
        output = {
            "ticker": args.ticker,
            **metadata,
            "date_range": {
                "start": str(df["Date"].min().date()),
                "end": str(df["Date"].max().date()),
            },
            "forward_returns": fr_stats,
        }
        print(json.dumps(output, indent=2, cls=_NumpyEncoder))
        return

    # Mode: yearly only
    if args.yearly:
        yearly = []
        if "Date" in df.columns and "Close" in df.columns:
            df_copy = df.copy()
            df_copy["Year"] = df_copy["Date"].dt.year
            for year in sorted(df_copy["Year"].unique()):
                year_data = df_copy[df_copy["Year"] == year]
                if len(year_data) < 2:
                    continue
                start_close = year_data.iloc[0]["Close"]
                end_close = year_data.iloc[-1]["Close"]
                ret = (end_close - start_close) / start_close * 100 if start_close != 0 else None
                yearly.append({
                    "year": int(year),
                    "start_date": str(year_data.iloc[0]["Date"].date()),
                    "end_date": str(year_data.iloc[-1]["Date"].date()),
                    "start_close": float(start_close),
                    "end_close": float(end_close),
                    "return_pct": round(float(ret), 2) if ret is not None else None,
                })
        output = {
            "ticker": args.ticker,
            **metadata,
            "yearly_performance": yearly,
        }
        print(json.dumps(output, indent=2, cls=_NumpyEncoder))
        return

    # Mode: data snapshot only (no backtest)
    if args.no_backtest:
        snapshot = _get_data_snapshot(df)
        output = {
            "ticker": args.ticker,
            **metadata,
            "data_path": str(data_path),
            "total_rows": len(df),
            "date_range": {
                "start": str(df["Date"].min().date()),
                "end": str(df["Date"].max().date()),
            },
            **snapshot,
        }
        print(json.dumps(output, indent=2, cls=_NumpyEncoder))
        return

    # --- Default: run backtest (with or without data snapshot) ---
    result = {
        "ticker": args.ticker,
        **metadata,
        "data_path": str(data_path),
        "total_rows": len(df),
        "cutoff": str(cutoff.date()) if cutoff else None,
        "date_range": {
            "start": str(df["Date"].min().date()),
            "end": str(df["Date"].max().date()),
        },
    }

    # Data snapshot (always included unless --no-data)
    if not args.no_data:
        result["data_snapshot"] = _get_data_snapshot(df)

    # Resolve strategies
    strategies = {}
    labels = {}

    if args.group:
        for name, fn in STRATEGIES.items():
            label = STRATEGY_LABELS.get(name, name)
            if args.group.lower() in label.lower():
                strategies[name] = fn
                labels[name] = label
        print(f"Builtin strategies ({args.group} group): {list(strategies.keys())}", file=sys.stderr)
    else:
        strategies = dict(STRATEGIES)
        labels = {k: STRATEGY_LABELS.get(k, k) for k in strategies}
        print(f"Builtin strategies: {len(strategies)}", file=sys.stderr)

    # Custom strategies
    if not args.builtins_only and args.custom:
        custom_dir = args.custom_dir or str(_PROJECT_ROOT / "app" / "backtest" / "custom")
        custom = load_custom_strategies(custom_dir, module_names=args.custom)
        strategies.update(custom)
        labels.update({k: k for k in custom})
        print(f"Custom strategies loaded: {list(custom.keys())}", file=sys.stderr)

    if not strategies:
        print("ERROR: No strategies loaded", file=sys.stderr)
        sys.exit(1)

    print(f"Total strategies: {len(strategies)}", file=sys.stderr)

    # Run backtest
    engine = BacktestEngine(data_path=str(data_path), cutoff_date=cutoff)
    results = engine.run_batch(signal_fns=strategies)

    # Format results
    df_results = pd.DataFrame(results).set_index("Strategy")
    df_results = df_results.sort_values("Total Return (%)", ascending=False)

    # Build results list
    result["results"] = []
    for idx, row in df_results.iterrows():
        result["results"].append({
            "strategy": idx,
            "label": labels.get(idx, idx),
            "total_return_pct": round(float(row["Total Return (%)"]), 2),
            "sharpe_ratio": round(float(row["Sharpe Ratio"]), 4),
            "calmar_ratio": round(float(row["Calmar Ratio"]), 4),
            "max_drawdown_pct": round(float(row["Max Drawdown (%)"]), 2),
            "profit_factor": round(float(row["Profit Factor"]), 4),
            "win_rate_pct": round(float(row["Win Rate (%)"]), 1),
            "total_trades": int(row["Total Trades"]),
            "total_wins": int(row["Total Wins"]),
            "total_losses": int(row["Total Losses"]),
            "avg_trade_duration_days": round(float(row["Avg Trade Duration (d)"]), 1),
            "final_net_value": round(float(row["Final Net Value"]), 0),
        })

    if args.as_json:
        print(json.dumps(result, indent=2, cls=_NumpyEncoder))
    else:
        # Human-readable
        print(f"\n{'='*70}")
        print(f"  Backtest Analysis — {args.ticker}")
        print(f"  Company: {metadata['company_name']} ({args.ticker})")
        print(f"  Sector: {metadata['sector']}")
        print(f"  Period: {cutoff.date()} to {df['Date'].iloc[-1].date()}")
        print(f"  Data: {len(df)} rows, {len(result['results'])} strategies")
        print(f"{'='*70}\n")

        summary_text = summarize_table(df_results)
        print(summary_text)

        if args.verbose:
            print(f"\n{'─'*70}")
            print("DETAILED VIEW:")
            for entry in result["results"]:
                print(f"\n  {entry['label']} ({entry['strategy']})")
                print(f"  {'─'*50}")
                for key in ["total_return_pct", "sharpe_ratio", "max_drawdown_pct",
                             "profit_factor", "win_rate_pct", "total_trades"]:
                    label = key.replace("_", " ").title()
                    print(f"    {label:25s}: {entry[key]}")

    # Generate HTML report
    if not args.no_report:
        from framework.report import generate_report  # noqa: E402
        output_dir = _PROJECT_ROOT / "data" / "reports" / "backtest"
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = generate_report(
            results=results,
            df=df,
            ticker=args.ticker,
            output_dir=output_dir,
            top_n=15,
        )
        print(f"\nReport: {report_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
