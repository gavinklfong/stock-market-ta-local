#!/usr/bin/env python
"""CLI helper for running strategy backtests — works from ANY directory.

Use this instead of writing ad-hoc Python scripts with relative imports.
Handles all path resolution internally.

Usage:
    # List available strategies without running a backtest (NEW — use this first!)
    python app/backtest/run_strategy_backtest.py NG.L --list
    python app/backtest/run_strategy_backtest.py NG.L --list --custom NG.L_custom

    # All built-in strategies
    python app/backtest/run_strategy_backtest.py NG.L

    # With custom cutoff
    python app/backtest/run_strategy_backtest.py NG.L --cutoff 2016-10-26

    # Only specific custom strategies (by module file name, not strategy name)
    python app/backtest/run_strategy_backtest.py NG.L --custom NG.L_custom

    # Only built-in strategies (skip custom)
    python app/backtest/run_strategy_backtest.py NG.L --builtins-only

    # Output as JSON (for programmatic consumption)
    python app/backtest/run_strategy_backtest.py NG.L --json

    # Combine built-ins with custom strategies
    python app/backtest/run_strategy_backtest.py NG.L --custom NG.L_custom --cutoff 2020-01-01

    # Run specific built-in strategy group only
    python app/backtest/run_strategy_backtest.py NG.L --group mean-reversion

    # Verbose per-strategy details
    python app/backtest/run_strategy_backtest.py NG.L --verbose --no-report

Exit codes: 0 = success, 1 = error
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

import pandas as pd  # noqa: E402

from framework.engine import BacktestEngine, DEFAULT_CUTOFF  # noqa: E402
from framework.extensions import load_custom_strategies  # noqa: E402
from framework.metrics import summarize_table  # noqa: E402
from strategies.builtins import STRATEGIES, STRATEGY_LABELS  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run strategy backtests for a ticker — works from any directory.",
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
        help="Custom strategy module file names (without .py), e.g. NG.L_custom",
    )
    parser.add_argument(
        "--custom-dir",
        default=None,
        help="Directory containing custom strategy files (default: app/backtest/custom)",
    )
    parser.add_argument(
        "--builtins-only",
        action="store_true",
        help="Run only built-in strategies (skip custom)",
    )
    parser.add_argument(
        "--group",
        default=None,
        help="Run only strategies in a group (e.g. mean-reversion, trend-following)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output results as JSON (for programmatic consumption)",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip HTML report generation",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available strategies WITHOUT running a backtest (use this to verify --custom module names)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output (strategy-by-strategy)",
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

    # Resolve strategies
    strategies = {}
    labels = {}

    # Built-in strategies
    if args.group:
        # Filter by group
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

    # Resolve custom directory early (needed for --list even without --custom)
    custom_dir = args.custom_dir or str(_PROJECT_ROOT / "app" / "backtest" / "custom")

    # Custom strategies
    if not args.builtins_only and args.custom:
        custom = load_custom_strategies(
            custom_dir, module_names=args.custom, ticker=args.ticker,
        )
        strategies.update(custom)
        labels.update({k: k for k in custom})
        print(f"Custom strategies loaded: {list(custom.keys())}", file=sys.stderr)

    if not strategies:
        print("ERROR: No strategies loaded", file=sys.stderr)
        sys.exit(1)

    print(f"Total strategies: {len(strategies)}", file=sys.stderr)

    # --list: show strategies and exit without running backtest
    if args.list:
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"  Available Strategies — {args.ticker}", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        if args.custom:
            print(f"\nCustom modules requested: {args.custom}", file=sys.stderr)
        if args.group:
            print(f"Group filter: {args.group}", file=sys.stderr)
        print(f"\nResolved strategies ({len(strategies)} total):", file=sys.stderr)
        for name in sorted(strategies.keys()):
            label = labels.get(name, name)
            is_custom = name not in STRATEGIES
            marker = " [CUSTOM]" if is_custom else ""
            print(f"  {label}{marker}", file=sys.stderr)

        # List custom modules grouped by ticker subdirectory
        print(f"\nCustom modules (grouped by ticker):", file=sys.stderr)
        custom_path = Path(custom_dir)
        # Walk ticker subdirectories
        for subdir in sorted(custom_path.iterdir()):
            if not subdir.is_dir():
                continue
            ticker_dir_name = subdir.name
            ticker_files = sorted(subdir.glob("*.py"))
            ticker_files = [f for f in ticker_files
                            if f.name not in ("__init__.py", "template_strategy.py")]
            for pyfile in ticker_files:
                stem = pyfile.stem
                in_requested = stem in (args.custom or [])
                prefix = "  >>> " if in_requested else "      "
                print(f"{prefix}{stem}  ({ticker_dir_name}/)", file=sys.stderr)
        # Also list top-level .py files (excluding template)
        for pyfile in sorted(custom_path.glob("*.py")):
            if pyfile.name in ("__init__.py", "template_strategy.py"):
                continue
            stem = pyfile.stem
            in_requested = stem in (args.custom or [])
            prefix = "  >>> " if in_requested else "      "
            print(f"{prefix}{stem}  (top-level)", file=sys.stderr)

        if args.custom:
            # Verify requested modules exist in the new nested structure
            for mod in args.custom:
                found = False
                # Check ticker subdirectories
                for subdir in custom_path.iterdir():
                    if subdir.is_dir() and (subdir / f"{mod}.py").exists():
                        found = True
                        break
                # Check top-level
                if not found and (custom_path / f"{mod}.py").exists():
                    found = True
                if not found:
                    print(f"  WARNING: {mod}.py NOT FOUND — check --custom module names",
                          file=sys.stderr)

        print(f"\nUse --custom {sorted(args.custom)[0] if args.custom else '<module_name>'} to run with custom strategies.", file=sys.stderr)
        return

    # Run backtest
    engine = BacktestEngine(data_path=str(data_path), cutoff_date=cutoff)
    results = engine.run_batch(signal_fns=strategies)

    # Format results
    df_results = pd.DataFrame(results).set_index("Strategy")
    df_results = df_results.sort_values("Total Return (%)", ascending=False)

    if args.as_json:
        # Output JSON for programmatic consumption
        output = {
            "ticker": args.ticker,
            "cutoff": str(cutoff.date()) if cutoff else None,
            "data_rows": len(df),
            "data_start": str(df["Date"].iloc[0].date()),
            "data_end": str(df["Date"].iloc[-1].date()),
            "strategies_run": len(results),
            "results": [],
        }
        for idx, row in df_results.iterrows():
            output["results"].append({
                "strategy": idx,
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
        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        summary_text = summarize_table(df_results)
        print(f"\n{'='*70}")
        print(f"  Backtest Results — {args.ticker}  ({len(results)} strategies)")
        if cutoff:
            print(f"  Period: {cutoff.date()} to {df['Date'].iloc[-1].date()}")
        print(f"{'='*70}")
        print(summary_text)

        # Detailed view if verbose
        if args.verbose:
            print(f"\n{'─'*70}")
            print("DETAILED VIEW:")
            for idx, row in df_results.iterrows():
                label = labels.get(idx, idx)
                print(f"\n  {label} ({idx})")
                print(f"  {'─'*50}")
                for col in ["Total Return (%)", "Sharpe Ratio", "Max Drawdown (%)",
                             "Profit Factor", "Win Rate (%)", "Total Trades"]:
                    if col in row:
                        print(f"    {col:25s}: {row[col]}")

    # Generate report
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
