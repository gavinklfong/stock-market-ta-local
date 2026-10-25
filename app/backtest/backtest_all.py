"""Batch backtest — evaluate all strategies for all tickers in ticker_list.csv."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

BACKTEST_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKTEST_DIR))

from framework.engine import BacktestEngine, DEFAULT_CUTOFF
from framework.extensions import load_custom_strategies
from framework.metrics import summarize_table
from framework.report import generate_report
from strategies.builtins import STRATEGIES, STRATEGY_LABELS, STRATEGY_GROUPS

# Module-level custom strategy cache
_custom_cache: dict[str, object] = {}


def _load_custom(custom_dir: str | Path) -> None:
    if not custom_dir or custom_dir in _custom_cache:
        return
    loaded = load_custom_strategies(custom_dir)
    _custom_cache.update(loaded)


def load_ticker_list(ticker_list_path: str | Path) -> pd.DataFrame:
    """Load the config/ticker_list.csv with Company, Ticker, Sector columns."""
    df = pd.read_csv(ticker_list_path)
    # Normalize column names to match common variants
    col_map = {}
    for col in df.columns:
        cl = col.strip().lower()
        if cl in ("ticker", "symbol"):
            col_map[col] = "Ticker"
        elif cl in ("company", "name", "name / company"):
            col_map[col] = "Company"
        elif cl in ("sector", "major industry / sector", "sector / industry"):
            col_map[col] = "Sector"
    df.rename(columns=col_map, inplace=True)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run backtests for all tickers in ticker_list.csv",
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=None,
        help="Specific tickers to run (default: all in ticker_list.csv)",
    )
    parser.add_argument(
        "--groups",
        nargs="+",
        default=None,
        help="Strategy groups to run (default: all)",
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Path to analysis-data directory",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for reports",
    )
    parser.add_argument(
        "--cutoff",
        default=None,
        help="Cutoff date YYYY-MM-DD",
    )
    parser.add_argument(
        "--trailing-pct",
        type=float,
        default=None,
        help="Trailing stop percentage",
    )
    parser.add_argument(
        "--custom-dir",
        default=None,
        help="Directory for custom strategy Python files",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip individual HTML reports",
    )
    parser.add_argument(
        "--csv-only",
        action="store_true",
        help="Only generate merged CSV, no HTML reports",
    )
    parser.add_argument(
        "--results-file",
        default=None,
        help="Path for merged results CSV (default: backtest_all_results.csv)",
    )

    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent.parent  # stock-market-ta-local
    ticker_list_path = root / "config" / "ticker_list.csv"

    if not ticker_list_path.exists():
        print(f"ERROR: Ticker list not found: {ticker_list_path}")
        sys.exit(1)

    # Determine tickers
    if args.tickers:
        tickers = args.tickers
    else:
        ticker_df = load_ticker_list(ticker_list_path)
        ticker_col = None
        for col in ["Ticker", "Symbol"]:
            if col in ticker_df.columns:
                ticker_col = col
                break
        if ticker_col is None:
            print("ERROR: Cannot find Ticker/Symbol column in ticker_list.csv")
            sys.exit(1)
        tickers = list(ticker_df[ticker_col].dropna().astype(str))

    print(f"Tickers: {len(tickers)} — {tickers}")

    # Determine strategy filter
    strategy_names = list(STRATEGIES.keys())
    if args.groups:
        group_map = {g.lower(): g for g in STRATEGY_GROUPS}
        selected_groups = []
        for g in args.groups:
            if g.lower() in group_map:
                selected_groups.append(group_map[g.lower()])
            else:
                print(f"WARNING: Unknown group '{g}' — skipping")
        if selected_groups:
            strategy_names = []
            for g in selected_groups:
                strategy_names.extend(STRATEGY_GROUPS[g])
            strategy_names = list(dict.fromkeys(strategy_names))  # unique, ordered

    strategies = {name: STRATEGIES[name] for name in strategy_names}
    labels = {name: STRATEGY_LABELS.get(name, name) for name in strategies}
    print(f"Strategies: {len(strategies)} — {list(strategies.keys())}")

    # Resolve data path
    if args.data_dir is None:
        data_dir = root / "data" / "analysis-data"
    else:
        data_dir = Path(args.data_dir)

    # Parse cutoff
    cutoff = None
    if args.cutoff:
        cutoff = pd.Timestamp(args.cutoff)

    # Run backtests per ticker
    all_results: list[dict] = []

    for i, ticker in enumerate(tickers, 1):
        data_path = data_dir / f"{ticker}.csv"
        if not data_path.exists():
            print(f"[{i}/{len(tickers)}] SKIP {ticker}: data not found")
            continue

        print(f"\n[{i}/{len(tickers)}] Running {ticker} ({len(strategies)} strategies)")

        engine = BacktestEngine(
            data_path=str(data_path),
            cutoff_date=cutoff,
            trailing_pct=args.trailing_pct,
        )
        results = engine.run_batch(strategies)

        # Add ticker and label columns
        for r in results:
            r["Ticker"] = ticker
            r["Strategy_Label"] = labels.get(r["Strategy"], r["Strategy"])

        all_results.extend(results)

        # Per-ticker report
        if not args.no_report and not args.csv_only:
            try:
                report_dir = root / "data" / "reports" / "backtest"
                report_dir.mkdir(parents=True, exist_ok=True)
                df = pd.read_csv(data_path)
                report_path = generate_report(
                    results=results,
                    df=df,
                    ticker=ticker,
                    output_dir=report_dir,
                    top_n=15,
                )
                print(f"  Report: {report_path.name}")
            except Exception as e:
                print(f"  Report failed: {e}")

        # Print top 3
        if results:
            top3 = pd.DataFrame(results).sort_values("Total Return (%)", ascending=False).head(3)
            top3.set_index("Strategy", inplace=True)
            for idx, row in top3.iterrows():
                print(f"  {labels.get(idx, idx)}: {row['Total Return (%)']:.1f}% return, "
                      f"{row['Win Rate (%)']:.0f}% WR, {row['Profit Factor']:.2f} PF")

    # Save merged results
    if all_results:
        results_df = pd.DataFrame(all_results)
        results_df.sort_values(["Ticker", "Total Return (%)"], ascending=[True, False], inplace=True)

        results_path = args.results_file
        if results_path is None:
            results_path = str(root / "data" / "reports" / "backtest" / "backtest_all_results.csv")
        Path(results_path).parent.mkdir(parents=True, exist_ok=True)
        results_df.to_csv(results_path, index=False)
        print(f"\nMerged results ({len(results_df)} rows) → {results_path}")

        # Print top overall strategies
        print(f"\n{'='*70}")
        print(f"  Top 10 Overall Strategies")
        print(f"{'='*70}")
        top_overall = results_df.sort_values("Total Return (%)", ascending=False).head(10)
        for _, row in top_overall.iterrows():
            print(f"  {row['Ticker']:8s}  {row['Strategy_Label']:<35s}  "
                  f"{row['Total Return (%)']:8.1f}%  {row['Win Rate (%)']:6.1f}%  "
                  f"{row['Profit Factor']:6.2f}")
    else:
        print("\nNo results generated — check data paths and ticker list.")


if __name__ == "__main__":
    main()
